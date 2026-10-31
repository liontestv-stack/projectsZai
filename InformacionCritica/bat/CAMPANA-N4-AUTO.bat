@echo off
title CAMPANA-N4 - NIVEL 4 (doble click y ya)
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py
%PY% CAMPANA-N4.py p7 --fuerza
if errorlevel 1 goto fin
%PY% CAMPANA-N4.py p8 --fuerza
:fin
echo.
pause
