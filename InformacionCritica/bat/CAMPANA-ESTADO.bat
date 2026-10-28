@echo off
title CAMPANA - estado (solo foto)
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py
%PY% campana-10-pasos.py estado
echo.
pause
