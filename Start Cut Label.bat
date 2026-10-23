@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch.ps1"
if errorlevel 1 pause
exit /b
