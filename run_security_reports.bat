@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

python scripts\generate_security_reports.py
exit /b %errorlevel%
