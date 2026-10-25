@echo off
title LAIA - BARRIDO 37 configs - Qwen t/s
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py barrido-qwen-30.py %*
) else (
    python barrido-qwen-30.py %*
)
echo.
pause
