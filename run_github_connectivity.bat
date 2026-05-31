@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "REPO_PROVIDER=github"
set "REPO_CONFIG_FILE=%SCRIPT_DIR%repo_rover_runner.github.env"

echo Running GitHub connectivity check using %REPO_CONFIG_FILE%
call "%SCRIPT_DIR%test_ping_repo.bat"
if errorlevel 1 exit /b 1

echo GitHub connectivity check passed.
exit /b 0
