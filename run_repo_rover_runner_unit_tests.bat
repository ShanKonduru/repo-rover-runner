@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

python -m coverage erase
python -m coverage run --rcfile "%SCRIPT_DIR%.coveragerc" -m unittest discover -s tests -p "test_*.py"
if errorlevel 1 exit /b 1

python -m coverage report --rcfile "%SCRIPT_DIR%.coveragerc"
if errorlevel 1 exit /b 1

echo Unit tests passed with 100%% coverage.
exit /b 0
