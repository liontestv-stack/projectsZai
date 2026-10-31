@echo off
title CAMPANA-N4 - estado (solo foto)
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py
%PY% CAMPANA-N4.py estado
echo.
pause
