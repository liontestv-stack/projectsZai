@echo off
title CAMPANA - MODO AUTO (hace solo los pasos en orden)
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py
echo ==================================================
echo  CAMPANA - MODO AUTO
echo  doble click = trabaja SOLO los pasos 1..6 en orden
echo  (mide, promueve, juzga, descarga, verifica y mide N1;
echo   puede tardar ~2-4 h; todo queda en campana-INFORME.md)
echo  solo mirar: CAMPANA-ESTADO.bat   paso manual: CAMPANA.bat pN
echo ==================================================
%PY% campana-10-pasos.py %*
echo.
pause
