"""Detect shipping label boundaries and preserve PDF vector content."""
from pathlib import Path
import os
import uuid
import cv2
import numpy as np
import pymupdf as fitz


def open_document(path):
    doc = fitz.open(path)
    if doc.needs_pass:
        doc.close()
        raise ValueError('PDF có mật khẩu. Hãy xuất bản không có mật khẩu trước.')
    if not doc.is_pdf:
        data = doc.convert_to_pdf()
        doc.close()
        doc = fitz.open('pdf', data)
    doc.bake()
    for page in doc:
        page.remove_rotation()
    return doc


def detect(page):
    scale = min(2.5, 1800 / max(page.rect.width, page.rect.height))
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY, alpha=False)
    gray = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    mask = (gray < 210).astype(np.uint8) * 255
    h, w = mask.shape
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        ratio = min(cw, ch) / max(cw, ch)
        if cw * ch < w * h * .12 or abs(ratio / (2/3) - 1) > .08:
            continue
        # Require all four sides; internal barcode blocks must not count as frames.
        strip = max(2, round(min(cw, ch) * .008))
        region = mask[y:y+ch, x:x+cw] > 0
        sides = [region[:strip].any(axis=0).mean(), region[-strip:].any(axis=0).mean(),
                 region[:, :strip].any(axis=1).mean(), region[:, -strip:].any(axis=1).mean()]
        if min(sides) > .8:
            candidates.append((cw * ch, (x, y, x+cw, y+ch)))
    reason = 'Khung viền'
    if candidates:
        candidates.sort(reverse=True)
        box = candidates[0][1]
        # Multiple disjoint label-sized frames require review.
        ambiguous = any(b[0] >= box[2] or b[2] <= box[0] or b[1] >= box[3] or b[3] <= box[1]
                        for _, b in candidates[1:])
    else:
        points = cv2.findNonZero(mask)
        if points is None:
            return {'box': [0, 0, 1, 1], 'review': True, 'reason': 'Trang trống'}
        x, y, cw, ch = cv2.boundingRect(points)
        box = (x, y, x+cw, y+ch)
        reason = 'Biên nội dung (không có khung kín)'
        ambiguous = cw * ch < w * h * .2
    x0, y0, x1, y1 = box
    ratio = min(x1-x0, y1-y0) / max(x1-x0, y1-y0)
    mismatch = abs(ratio / (2/3) - 1)
    review = ambiguous or mismatch > .025
    if mismatch > .025:
        reason += ' · tỷ lệ khác 4×6'
    return {'box': [x0/w, y0/h, x1/w, y1/h], 'review': review, 'reason': reason}


def inspect(path):
    with open_document(path) as doc:
        if not len(doc):
            raise ValueError('Tệp không có trang.')
        return [detect(page) for page in doc]


def export(path, target, boxes, page_indices=None):
    with open_document(path) as source, fitz.open() as dest:
        indices = list(range(len(source))) if page_indices is None else page_indices
        if len(boxes) != len(indices):
            raise ValueError('Số vùng cắt phải khớp số trang.')
        for index, box in zip(indices, boxes):
            page = source[index]
            if len(box) != 4 or not all(isinstance(v, (int, float)) and np.isfinite(v) and 0 <= v <= 1 for v in box):
                raise ValueError('Vùng cắt không hợp lệ.')
            x0, y0, x1, y1 = box
            if x1-x0 < .01 or y1-y0 < .01:
                raise ValueError('Vùng cắt quá nhỏ.')
            r = page.rect
            clip = fitz.Rect(x0*r.width, y0*r.height, x1*r.width, y1*r.height)
            new = dest.new_page(width=288, height=432)
            new.show_pdf_page(new.rect, source, page.number, clip=clip,
                              rotate=90 if clip.width > clip.height else 0, keep_proportion=False)
        temp = Path(target).with_name('.' + uuid.uuid4().hex + '.tmp')
        try:
            dest.save(temp, garbage=4, deflate=True)
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
