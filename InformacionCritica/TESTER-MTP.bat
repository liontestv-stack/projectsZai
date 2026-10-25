@echo off
title TESTER-MTP - Qwen APEX-I-MINI (LAIA)
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py tester-mtp.py %* & goto fin)
where python >nul 2>nul
if %errorlevel%==0 (python tester-mtp.py %* & goto fin)
echo  [ERROR] Python no encontrado en este PC.
echo          Instala Python 3 desde python.org y marca
echo          "Add python.exe to PATH" durante la instalacion.
:fin
echo.
pause
