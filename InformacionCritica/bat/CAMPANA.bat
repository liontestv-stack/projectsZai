@echo off
title CAMPANA 10 PASOS - piloto de la campana (LAIA)
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py
echo ==================================================
echo  CAMPANA 10 PASOS  -  piloto de la campana
echo  doble click = foto del estado (p1..p10 con puertas)
echo  paso concreto: CAMPANA.bat p1   (o p2, p3, ...)
echo ==================================================
%PY% campana-10-pasos.py %*
echo.
pause
