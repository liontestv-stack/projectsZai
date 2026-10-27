@echo off
title LAIA - BARRIDO 37 configs - Qwen t/s
cd /d "%~dp0"
set SCRIPT=barrido-qwen-30.py
if exist "..\scripts\barrido-qwen-30.py" set SCRIPT=..\scripts\barrido-qwen-30.py
where py >nul 2>nul
if %errorlevel%==0 (
    py %SCRIPT% %*
) else (
    python %SCRIPT% %*
)
echo.
pause
