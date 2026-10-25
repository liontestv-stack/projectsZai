@echo off
title LAIA - BARRIDO 25 configs - Qwen t/s
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py barrido-qwen-25.py %*
) else (
    python barrido-qwen-25.py %*
)
echo.
pause
