@echo off
title CAMPANA-N4 - AUTO (NIVEL 4: pasos 7..8)
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py
%PY% CAMPANA-N4.py
echo.
pause
