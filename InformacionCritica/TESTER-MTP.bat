@echo off
title TESTER-MTP - Qwen APEX-I-MINI (LAIA)
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py tester-mtp.py %*) else (python tester-mtp.py %*)
echo.
pause
