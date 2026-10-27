@echo off
title LAIA - Qwen APEX-I-MINI (b11856) - TRABAJO
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py abrir-qwen-apex.py trabajo %*
) else (
    python abrir-qwen-apex.py trabajo %*
)
echo.
pause
