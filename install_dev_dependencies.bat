@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

if not exist "%VENV_PYTHON%" (
    echo [INFO] Workspace virtual environment not found. Creating .venv...
    call :create_venv
    if errorlevel 1 exit /b 1
)

if not exist "%VENV_ACTIVATE%" (
    echo [ERROR] Could not find virtual environment activation script: "%VENV_ACTIVATE%"
    exit /b 1
)

call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    exit /b 1
)

python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

python -m pip install -r "%SCRIPT_DIR%requirements-dev.txt"
if errorlevel 1 exit /b 1

if exist "%SCRIPT_DIR%bin\gitleaks.exe" goto :gitleaks_ok
where gitleaks >nul 2>&1
if errorlevel 1 (
    echo [WARN] gitleaks CLI was not found on PATH.
    echo [WARN] Place gitleaks.exe in "%SCRIPT_DIR%bin" or install it with winget.
)
:gitleaks_ok

echo Dev dependencies installed successfully in .venv.
call deactivate >nul 2>&1
exit /b 0

:create_venv
where python >nul 2>&1
if not errorlevel 1 (
    python -m venv "%VENV_DIR%"
    if not errorlevel 1 exit /b 0
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3.12 -m venv "%VENV_DIR%"
    if not errorlevel 1 exit /b 0

    py -3.11 -m venv "%VENV_DIR%"
    if not errorlevel 1 exit /b 0

    py -3.10 -m venv "%VENV_DIR%"
    if not errorlevel 1 exit /b 0

    py -3 -m venv "%VENV_DIR%"
    if not errorlevel 1 exit /b 0
)

echo [ERROR] Failed to create .venv. Ensure a working Python 3 installation is on PATH.
exit /b 1
