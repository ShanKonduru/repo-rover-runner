@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "REPO_PROVIDER=bitbucket"
set "REPO_CONFIG_FILE=%SCRIPT_DIR%repo_rover_runner.bitbucket.env"

echo Running Bitbucket test sequence using %REPO_CONFIG_FILE%

call "%SCRIPT_DIR%test_ping_repo.bat"
if errorlevel 1 exit /b 1

call "%SCRIPT_DIR%create_new_branch.bat"
if errorlevel 1 exit /b 1

call "%SCRIPT_DIR%test_list_branches.bat"
if errorlevel 1 exit /b 1

call "%SCRIPT_DIR%test_use_branch.bat"
if errorlevel 1 exit /b 1

call "%SCRIPT_DIR%list_files_in_branch.bat"
if errorlevel 1 exit /b 1

call "%SCRIPT_DIR%test_push_dummy.bat"
if errorlevel 1 exit /b 1

echo Bitbucket test sequence completed successfully.
exit /b 0
