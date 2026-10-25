@echo off
title LAIA - Qwen APEX-I-MINI (b11856)
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py abrir-qwen-apex.py %*
) else (
    python abrir-qwen-apex.py %*
)
echo.
pause
