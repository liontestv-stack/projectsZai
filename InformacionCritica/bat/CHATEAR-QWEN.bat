@echo off
title LAIA - Chat Qwen APEX-I-MINI
cd /d "%~dp0"
set SCRIPT=chatear-qwen.py
if exist "..\scripts\chatear-qwen.py" set SCRIPT=..\scripts\chatear-qwen.py
where py >nul 2>nul
if %errorlevel%==0 (
    py %SCRIPT% %*
) else (
    python %SCRIPT% %*
)
echo.
pause
