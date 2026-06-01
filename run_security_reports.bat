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

if exist "%SCRIPT_DIR%bin" set "PATH=%SCRIPT_DIR%bin;%PATH%"

python scripts\generate_security_reports.py
set "EXIT_CODE=%errorlevel%"

call deactivate >nul 2>&1
exit /b %EXIT_CODE%

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
