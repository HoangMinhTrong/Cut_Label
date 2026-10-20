"""Read the explicit Buyer field and tracking; never substitute sender/recipient."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata
import pymupdf as fitz

ROOT = Path(__file__).resolve().parent


def safe_buyer(value):
    value = unicodedata.normalize('NFKC', value).strip().lstrip('@')
    value = re.sub(r'[^\w. -]', '_', value, flags=re.UNICODE)
    value = re.sub(r'\s+', ' ', value).strip(' ._-')
    return value[:80].encode('utf-8')[:180].decode('utf-8', errors='ignore')


def normalize_tracking(value):
    value = re.sub(r'[\s-]', '', unicodedata.normalize('NFKC', value)).upper()
    if re.fullmatch(r'9[0-9]{19}(?:[0-9]{2})?|1Z[A-Z0-9]{16}', value):
        return value
    return ''


def parse_lines(lines):
    buyers, tracking = {}, {}
    for line in lines:
        text, confidence = line['text'].strip(), line.get('confidence', 1)
        match = re.search(r'\bBuyer(?:\s+name)?\s*[:：]?\s*@?\s*([\w][\w. -]*)', text, re.I)
        if match:
            name = safe_buyer(match.group(1))
            if name:
                buyers[name] = max(buyers.get(name, 0), confidence)
        # Restrict to tracking-shaped lines, not arbitrary numbers embedded in addresses/order IDs.
        raw = re.sub(r'^(?:USPS\s+)?TRACKING(?:\s+NUMBER|\s+NO\.?)?[\s:#-]*', '', text, flags=re.I)
        number = normalize_tracking(raw)
        if number:
            tracking[number] = max(tracking.get(number, 0), confidence)
    buyer = next(iter(buyers)) if len(buyers) == 1 else ''
    number = next(iter(tracking)) if len(tracking) == 1 else ''
    return {'buyer': buyer, 'tracking': number,
            'info_review': not (buyer and number and buyers[buyer] >= .8 and tracking[number] >= .8)}


def ocr_lines(page, box):
    binary = ROOT/'.state/label-ocr'
    source = ROOT/'ocr.swift'
    if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
        cache = ROOT/'.state/swift-cache'
        cache.mkdir(parents=True, exist_ok=True)
        subprocess.run(['xcrun', 'swiftc', '-module-cache-path', str(cache), str(source), '-o', str(binary)],
                       capture_output=True, check=True, timeout=180)
    r = page.rect
    clip = fitz.Rect(box[0]*r.width, box[1]*r.height, box[2]*r.width, box[3]*r.height)
    scale = min(4, 4000/max(clip.width, clip.height))
    with tempfile.TemporaryDirectory(prefix='cut-label-ocr-') as td:
        image = Path(td)/'label.png'
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
        pix.save(image)
        result = subprocess.run([str(binary), str(image)], capture_output=True, check=True, timeout=90)
        return json.loads(result.stdout)


def read_info(page, box):
    r = page.rect
    clip = fitz.Rect(box[0]*r.width, box[1]*r.height, box[2]*r.width, box[3]*r.height)
    lines = [{'text': text, 'confidence': 1} for text in page.get_text(clip=clip, sort=True).splitlines()]
    info = parse_lines(lines)
    info['info_source'] = 'PDF text'
    if not info['info_review']:
        return info
    try:
        info = parse_lines(ocr_lines(page, box))
        info['info_source'] = 'OCR'
        if info['info_review']:
            info['info_note'] = 'Chưa đọc chắc Buyer/tracking. Kiểm tra và nhập lại trước khi xuất.'
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        info.update(info_review=True, info_note='Không chạy được OCR; hãy nhập Buyer và tracking.', info_source='Nhập tay')
    return info


def validate_info(info):
    buyer = safe_buyer(str(info.get('buyer', '')))
    tracking = normalize_tracking(str(info.get('tracking', '')))
    if not buyer or not tracking:
        raise ValueError('Cần Buyer name và tracking hợp lệ (USPS 20/22 số hoặc UPS 1Z).')
    return {'buyer': buyer, 'tracking': tracking}
