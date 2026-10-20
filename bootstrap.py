"""Shared double-click launcher. Requires Python 3.9–3.12, standard library only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:8765'


def running_here():
    try:
        with urllib.request.urlopen(URL + '/api/jobs', timeout=3) as response:
            info = json.load(response)
    except urllib.error.URLError:
        return False
    except (ValueError, OSError) as exc:
        raise RuntimeError('Port 8765 dang duoc su dung. Hay dong app cu roi mo lai.') from exc
    # Also recognize the earlier app response during upgrade.
    root = Path(info.get('root', str(Path(info.get('input', '/unknown')).parent)))
    if root.resolve() != ROOT or 'jobs' not in info:
        raise RuntimeError('Port 8765 thuoc mot app/folder khac. Hay dong app do truoc.')
    return True


def main():
    if running_here():
        webbrowser.open(URL)
        print('App dang chay. Neu vua cap nhat code, dong Terminal cu va mo lai app.')
        return 0
    if not (3, 9) <= sys.version_info[:2] <= (3, 12):
        raise RuntimeError('Hay cai Python 3.12 (64-bit), roi mo lai file Start Cut Label.')
    environment = ROOT/'.venv'
    python = environment/('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('Dang tao moi truong Python...', flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    requirements = ROOT/'requirements.txt'
    stamp = environment/'.cut-label-requirements'
    signature = hashlib.sha256(requirements.read_bytes()).hexdigest()
    check = subprocess.run([str(python), '-c', 'import pymupdf, cv2, numpy, rapidocr_onnxruntime, onnxruntime'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if check.returncode or not stamp.exists() or stamp.read_text() != signature:
        print('Dang cai/cap nhat thu vien OCR. Lan dau can Internet...', flush=True)
        # Both OpenCV distributions share cv2; remove the old headless package first.
        headless = subprocess.run([str(python), '-m', 'pip', 'show', 'opencv-python-headless'],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if headless.returncode == 0:
            subprocess.run([str(python), '-m', 'pip', 'uninstall', '-y', 'opencv-python-headless'], check=True)
            subprocess.run([str(python), '-m', 'pip', 'install', '--force-reinstall', '--no-deps',
                            'opencv-python==4.11.0.86'], check=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(requirements)], check=True)
        subprocess.run([str(python), '-c', 'import pymupdf, cv2, numpy, rapidocr_onnxruntime, onnxruntime'], check=True)
        stamp.write_text(signature)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONUNBUFFERED='1')
    return subprocess.call([str(python), str(ROOT/'app.py')], cwd=ROOT, env=env)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        print(f'Khong khoi dong duoc app: {exc}', file=sys.stderr)
        sys.exit(1)
