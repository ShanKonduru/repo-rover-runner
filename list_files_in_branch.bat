@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
if not "%REPO_CONFIG_FILE%"=="" (
  set "ENV_FILE=%REPO_CONFIG_FILE%"
) else (
  if /I "%REPO_PROVIDER%"=="github" (
    set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.github.env"
  ) else (
    if /I "%REPO_PROVIDER%"=="bitbucket" (
      set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.bitbucket.env"
    ) else (
      if exist "%SCRIPT_DIR%repo_rover_runner.bitbucket.env" (
        set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.bitbucket.env"
      ) else (
        if exist "%SCRIPT_DIR%repo_rover_runner.github.env" (
          set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.github.env"
        ) else (
          set "ENV_FILE=%SCRIPT_DIR%repo_rover_runner.env"
        )
      )
    )
  )
)

if not exist "%ENV_FILE%" (
  echo ERROR: Missing %ENV_FILE%. Provide REPO_CONFIG_FILE or create repo_rover_runner.github.env/repo_rover_runner.bitbucket.env.
  exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R "^[A-Za-z_][A-Za-z0-9_]*=.*" "%ENV_FILE%"`) do (
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

if "%REMOTE%"=="" set "REMOTE=origin"
if "%BRANCH_TO_LIST%"=="" (
  if "%TARGET_BRANCH%"=="" (
    set "BRANCH_TO_LIST=main"
  ) else (
    set "BRANCH_TO_LIST=%TARGET_BRANCH%"
  )
)

set "REPO_PATH_ABS=%SCRIPT_DIR%%LOCAL_REPO_PATH%"

if not exist "%REPO_PATH_ABS%\.git" (
  "%PYTHON_EXE%" "%SCRIPT_DIR%repo_rover_runner_cli.py" clone --repo-url "%REPO_URL%" --dest "%REPO_PATH_ABS%"
  if errorlevel 1 exit /b 1
)

pushd "%REPO_PATH_ABS%" >nul
git fetch "%REMOTE%" >nul 2>&1

git rev-parse --verify "%BRANCH_TO_LIST%" >nul 2>&1
if not errorlevel 1 (
  set "REF=%BRANCH_TO_LIST%"
  goto :list
)

git rev-parse --verify "%REMOTE%/%BRANCH_TO_LIST%" >nul 2>&1
if not errorlevel 1 (
  set "REF=%REMOTE%/%BRANCH_TO_LIST%"
  goto :list
)

echo ERROR: Branch not found locally or remotely: %BRANCH_TO_LIST%
popd >nul
exit /b 1

:list
echo Listing files in branch ref: %REF%
git ls-tree -r --name-only "%REF%"
set "RC=%ERRORLEVEL%"
popd >nul
exit /b %RC%
