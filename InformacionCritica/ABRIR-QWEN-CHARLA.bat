@echo off
title LAIA - Qwen APEX-I-MINI (b11856) - CHARLA (4 expertos)
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py abrir-qwen-apex.py charla %*
) else (
    python abrir-qwen-apex.py charla %*
)
echo.
pause
