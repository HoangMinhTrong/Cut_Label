#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote
import webbrowser
import pymupdf as fitz
from cropper import inspect, export, open_document
from label_info import read_info, validate_info
from platform_support import open_folder

SCHEMA_VERSION = 2

ROOT = Path(__file__).resolve().parent
INPUT, OUTPUT, STATE = ROOT/'input', ROOT/'output', ROOT/'.state'
for folder in (INPUT, OUTPUT, STATE):
    folder.mkdir(exist_ok=True)
LOCK = threading.RLock()  # PyMuPDF operations must never run concurrently.
DB = STATE/'jobs.json'
try:
    JOBS = json.loads(DB.read_text())
except (OSError, ValueError):
    JOBS = {}
SUPPORTED = {'.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'}


def save():
    temp = DB.with_suffix('.tmp')
    temp.write_text(json.dumps(JOBS, ensure_ascii=False, indent=2))
    os.replace(temp, DB)


def digest(path):
    h = hashlib.sha256()
    h.update(path.name.encode())
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def process(path, key):
    previous = JOBS.get(key, {})
    job = {'id': key, 'name': path.name, 'status': 'processing', 'time': time.time(),
           'version': SCHEMA_VERSION, 'outputs': previous.get('outputs', [])}
    if previous.get('output') and not previous.get('outputs'):
        job['legacy_output'] = previous['output']
    elif previous.get('legacy_output'):
        job['legacy_output'] = previous['legacy_output']
    JOBS[key] = job
    try:
        pages = inspect(path)
        with open_document(path) as doc:
            for page, details in zip(doc, pages):
                details.update(read_info(page, details['box']))
        job['pages'] = pages
        if any(p['review'] or p['info_review'] for p in pages):
            job['status'] = 'review'
        else:
            finish(job, [p['box'] for p in pages])
    except Exception as exc:
        job.update(status='error', error=str(exc))
    save()


def finish(job, boxes, infos=None):
    path = INPUT/job['name']
    if digest(path) != job['id']:
        raise ValueError('Tệp nguồn đã thay đổi; hãy dùng bản mới trong danh sách.')
    infos = job['pages'] if infos is None else infos
    if len(boxes) != len(job['pages']) or len(infos) != len(boxes):
        raise ValueError('Cần vùng cắt và Buyer/tracking cho mọi trang.')
    clean = [validate_info(info) for info in infos]
    old_names = set(job.get('outputs', []))
    names = []
    # Stage every page before publishing any file; no partial batch on crop errors.
    with tempfile.TemporaryDirectory(dir=STATE, prefix='export-') as td:
        for i, (box, info) in enumerate(zip(boxes, clean)):
            base = f"{info['buyer']}_{info['tracking']}"
            name = base + '.pdf'
            suffix = 2
            while name.casefold() in {n.casefold() for n in names} or ((OUTPUT/name).exists() and name not in old_names):
                name = f'{base}_{suffix}.pdf'
                suffix += 1
            export(path, Path(td)/name, [box], page_indices=[i])
            names.append(name)
        for name in names:
            os.replace(Path(td)/name, OUTPUT/name)
    # Retain obsolete app-generated exports in an archive, including pre-feature names.
    obsolete = old_names - set(names)
    if job.get('legacy_output'):
        obsolete.add(job['legacy_output'])
    for name in obsolete:
        old = OUTPUT/name
        if old.exists():
            archive = STATE/'previous-output'/job['id']
            archive.mkdir(parents=True, exist_ok=True)
            target = archive/name
            if target.exists():
                target = archive/f'{time.time_ns()}_{name}'
            os.replace(old, target)
    for details, info, box in zip(job['pages'], clean, boxes):
        details.update(info, box=box, info_review=False)
    job.pop('legacy_output', None)
    job.pop('error', None)
    job.update(status='done', output=names[0], outputs=names)


def watch():
    seen = {}
    while True:
        try:
            for path in INPUT.iterdir():
                if path.is_symlink() or not path.is_file() or path.suffix.lower() not in SUPPORTED:
                    continue
                stat = path.stat()
                sig = (stat.st_size, stat.st_mtime_ns)
                previous = seen.get(path)
                if previous is None or previous[0] != sig:
                    seen[path] = (sig, time.monotonic(), False)
                    continue
                if previous[2] or time.monotonic() - previous[1] < 3:
                    continue
                with LOCK:
                    key = digest(path)
                    existing = JOBS.get(key)
                    if not existing or existing.get('version') != SCHEMA_VERSION or existing['status'] == 'processing' or (existing['status'] == 'done' and any(not (OUTPUT/name).exists() for name in existing.get('outputs', [existing['output']]))):
                        process(path, key)
                seen[path] = (sig, previous[1], True)
        except Exception as exc:
            print('Theo dõi folder:', exc, flush=True)
        time.sleep(1)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, data, kind='application/json', code=200, filename=None):
        if kind == 'application/json':
            data = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if filename:
            self.send_header('Content-Disposition', "inline; filename*=UTF-8''" + quote(filename))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        try:
            route = urlparse(self.path)
            q = parse_qs(route.query)
            if route.path == '/':
                return self.reply((ROOT/'index.html').read_bytes(), 'text/html; charset=utf-8')
            with LOCK:
                if route.path == '/api/jobs':
                    return self.reply({'app': 'cut-label', 'root': str(ROOT), 'jobs': sorted(JOBS.values(), key=lambda j: j['time'], reverse=True), 'input': str(INPUT), 'output': str(OUTPUT)})
                if route.path in ('/preview', '/download'):
                    job = JOBS[q['id'][0]]
                    if route.path == '/download':
                        index = int(q.get('page', ['0'])[0])
                        names = job.get('outputs', [job['output']])
                        return self.reply((OUTPUT/names[index]).read_bytes(), 'application/pdf', filename=names[index])
                    with open_document(INPUT/job['name']) as doc:
                        page = doc[int(q.get('page', ['0'])[0])]
                        pix = page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3), alpha=False)
                        return self.reply(pix.tobytes('png'), 'image/png')
            self.reply({'error': 'Không tìm thấy'}, code=404)
        except Exception as exc:
            self.reply({'error': str(exc)}, code=400)

    def do_POST(self):
        try:
            # Only requests from this local application may mutate state.
            expected = 'http://' + self.headers.get('Host', '')
            if self.headers.get('Origin') != expected or self.headers.get('Content-Type') != 'application/json':
                return self.reply({'error': 'Request không hợp lệ'}, code=403)
            size = int(self.headers.get('Content-Length', '0'))
            if size > 1_000_000:
                raise ValueError('Request quá lớn')
            body = json.loads(self.rfile.read(size))
            with LOCK:
                if self.path == '/api/open':
                    folder = INPUT if body['folder'] == 'input' else OUTPUT
                    open_folder(folder)
                elif self.path == '/api/confirm':
                    finish(JOBS[body['id']], body['boxes'], body.get('infos'))
                    save()
                elif self.path == '/api/retry':
                    job = JOBS[body['id']]
                    path = INPUT/job['name']
                    process(path, digest(path))
                else:
                    return self.reply({'error': 'Không tìm thấy'}, code=404)
            self.reply({'ok': True})
        except Exception as exc:
            self.reply({'error': str(exc)}, code=400)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    threading.Thread(target=watch, daemon=True).start()
    url = f'http://127.0.0.1:{args.port}'
    print(f'Cut Label: {url}\nInput: {INPUT}\nOutput: {OUTPUT}', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nĐã dừng app.')
    finally:
        server.server_close()
