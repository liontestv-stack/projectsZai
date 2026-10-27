@echo off
title LAIA - Qwen APEX-I-MINI (b11856) - TRABAJO
cd /d "%~dp0"
set SCRIPT=abrir-qwen-apex.py
if exist "..\scripts\abrir-qwen-apex.py" set SCRIPT=..\scripts\abrir-qwen-apex.py
where py >nul 2>nul
if %errorlevel%==0 (
    py %SCRIPT% trabajo %*
) else (
    python %SCRIPT% trabajo %*
)
echo.
pause
