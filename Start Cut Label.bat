@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
for %%V in (3.12 3.11 3.10 3.9) do (
  py -%%V -c "import sys" >nul 2>&1
  if not errorlevel 1 (
    py -%%V bootstrap.py
    if errorlevel 1 pause
    exit /b
  )
)
python -c "import sys; sys.exit(not ((3,9) <= sys.version_info[:2] <= (3,12)))" >nul 2>&1
if not errorlevel 1 (
  python bootstrap.py
  if errorlevel 1 pause
  exit /b
)
echo Hay cai Python 3.12 64-bit tu https://www.python.org/downloads/windows/
echo Chon "Add python.exe to PATH", sau do mo lai file nay.
pause
exit /b 1
