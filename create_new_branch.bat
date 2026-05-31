@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
if not "%REPO_CONFIG_FILE%"=="" (
  set "ENV_FILE=%REPO_CONFIG_FILE%"
) else if /I "%REPO_PROVIDER%"=="github" (
  set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.github.env"
) else if /I "%REPO_PROVIDER%"=="bitbucket" (
  set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.bitbucket.env"
) else if exist "%SCRIPT_DIR%repo_rover_runner.bitbucket.env" (
  set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.bitbucket.env"
) else if exist "%SCRIPT_DIR%repo_rover_runner.github.env" (
  set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.github.env"
) else (
  set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.env"
)

if not exist "%ENV_FILE%" (
  echo ERROR: Missing %ENV_FILE%. Provide REPO_CONFIG_FILE or create repo_rover_runner.github.env/repo_rover_runner.bitbucket.env.
  exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
  if not "%%A"=="" if /I not "%%A:~0,1"=="#" set "%%A=%%B"
)

if "%REPO_URL%"=="" (
  echo ERROR: REPO_URL missing in selected config file
  exit /b 1
)
if "%LOCAL_REPO_PATH%"=="" (
  echo ERROR: LOCAL_REPO_PATH missing in selected config file
  exit /b 1
)
if "%TARGET_BRANCH%"=="" (
  echo ERROR: TARGET_BRANCH missing in selected config file
  exit /b 1
)

if "%BASE_BRANCH%"=="" set "BASE_BRANCH=main"
if "%REMOTE%"=="" set "REMOTE=origin"
set "REPO_PATH_ABS=%SCRIPT_DIR%%LOCAL_REPO_PATH%"

if not exist "%REPO_PATH_ABS%\.git" (
  python "%SCRIPT_DIR%repo_rover_runner_cli.py" clone --repo-url "%REPO_URL%" --dest "%REPO_PATH_ABS%"
  if errorlevel 1 exit /b 1
)

python "%SCRIPT_DIR%repo_rover_runner_cli.py" use-branch --repo-path "%REPO_PATH_ABS%" --branch "%TARGET_BRANCH%" --base-branch "%BASE_BRANCH%" --remote "%REMOTE%"
exit /b %ERRORLEVEL%
