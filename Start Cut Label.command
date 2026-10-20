#!/bin/zsh
cd "${0:A:h}" || exit 1
for candidate in python3.12 python3.11 python3.10 python3.9 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(not ((3,9) <= sys.version_info[:2] <= (3,12)))' 2>/dev/null; then
    "$candidate" bootstrap.py
    result=$?
    if [[ $result -ne 0 ]]; then
      read '?Khong khoi dong duoc app. Nhan Enter de dong.'
    fi
    exit $result
  fi
done
print 'Hay cai Python 3.12 tu https://www.python.org/downloads/ roi mo lai.'
read '?Nhan Enter de dong.'
exit 1
