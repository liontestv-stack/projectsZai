@echo off
title LAIA - BARRIDO 25 configs - Qwen t/s
cd /d "%~dp0"
set SCRIPT=barrido-qwen-25.py
if exist "..\scripts\barrido-qwen-25.py" set SCRIPT=..\scripts\barrido-qwen-25.py
where py >nul 2>nul
if %errorlevel%==0 (
    py %SCRIPT% %*
) else (
    python %SCRIPT% %*
)
echo.
pause
