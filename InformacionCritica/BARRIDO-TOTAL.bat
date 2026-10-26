@echo off
title BARRIDO-TOTAL - instrumento de t/s (LAIA)
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py
echo ================================================
echo  BARRIDO-TOTAL: escalera A-G automatizada
echo  completo: ~1.5-2.5 h | quick: --quick ~35-50 min
echo ================================================
%PY% barrido-total.py %*
echo.
pause
