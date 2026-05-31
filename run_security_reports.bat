@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
cd /d "%SCRIPT_DIR%"

"%PYTHON_EXE%" scripts\generate_security_reports.py
exit /b %errorlevel%
