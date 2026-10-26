@echo off
title LAIA - FASE D NIVEL 1 - expertos (EXP) + MEC
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py barrido-n1-expertos.py %*
) else (
    python barrido-n1-expertos.py %*
)
echo.
pause
