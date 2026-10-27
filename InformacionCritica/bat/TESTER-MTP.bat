@echo off
title TESTER-MTP - Qwen APEX-I-MINI (LAIA)
cd /d "%~dp0"
set SCRIPT=tester-mtp.py
if exist "..\scripts\tester-mtp.py" set SCRIPT=..\scripts\tester-mtp.py
where py >nul 2>nul
if %errorlevel%==0 (py %SCRIPT% %* & goto fin)
where python >nul 2>nul
if %errorlevel%==0 (python %SCRIPT% %* & goto fin)
echo  [ERROR] Python no encontrado en este PC.
echo          Instala Python 3 desde python.org y marca
echo          "Add python.exe to PATH" durante la instalacion.
:fin
echo.
pause
