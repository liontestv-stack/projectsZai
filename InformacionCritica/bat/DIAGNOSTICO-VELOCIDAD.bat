@echo off
title LAIA - DIAGNOSTICO DE VELOCIDAD - Qwen APEX-I-MINI (b11856)
cd /d "%~dp0"
set SCRIPT=diagnostico-velocidad.py
if exist "..\scripts\diagnostico-velocidad.py" set SCRIPT=..\scripts\diagnostico-velocidad.py
where py >nul 2>nul
if %errorlevel%==0 (
    py %SCRIPT% %*
) else (
    python %SCRIPT% %*
)
echo.
pause
