#!/bin/zsh
cd "${0:A:h}"
if /usr/bin/curl -fsS --max-time 2 http://127.0.0.1:8765/api/jobs 2>/dev/null | /usr/bin/grep -q '"input".*Cut_Label/input'; then
  /usr/bin/open http://127.0.0.1:8765
  exit 0
fi
if [[ ! -x .venv/bin/python ]]; then
  /usr/bin/python3 -m venv .venv || exit 1
fi
if ! .venv/bin/python -c 'import pymupdf, cv2, numpy' 2>/dev/null; then
  .venv/bin/python -m pip install -r requirements.txt || { read '?Không cài được thư viện. Nhấn Enter để đóng.'; exit 1; }
fi
.venv/bin/python app.py
read '?App đã dừng. Nhấn Enter để đóng.'
