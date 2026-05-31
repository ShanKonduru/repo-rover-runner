@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
cd /d "%SCRIPT_DIR%"

"%PYTHON_EXE%" -m coverage erase
"%PYTHON_EXE%" -m coverage run --rcfile "%SCRIPT_DIR%.coveragerc" -m unittest discover -s tests -p "test_*.py"
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -m coverage report --rcfile "%SCRIPT_DIR%.coveragerc"
if errorlevel 1 exit /b 1

echo Unit tests passed with 100%% coverage.
exit /b 0
