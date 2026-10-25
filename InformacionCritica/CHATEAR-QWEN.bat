@echo off
title LAIA - Chat Qwen APEX-I-MINI
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py chatear-qwen.py %*
) else (
    python chatear-qwen.py %*
)
echo.
pause
