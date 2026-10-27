@echo off
title LAIA - FASE D NIVEL 1 - expertos (EXP) + MEC
cd /d "%~dp0"
set SCRIPT=barrido-n1-expertos.py
if exist "..\scripts\barrido-n1-expertos.py" set SCRIPT=..\scripts\barrido-n1-expertos.py
where py >nul 2>nul
if %errorlevel%==0 (
    py %SCRIPT% %*
) else (
    python %SCRIPT% %*
)
echo.
pause
