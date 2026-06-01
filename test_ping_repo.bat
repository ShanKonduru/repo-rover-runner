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
  echo ERROR: REPO_URL is empty in selected config file
  exit /b 1
)

set "ASKPASS_FILE="
"%PYTHON_EXE%" "%SCRIPT_DIR%repo_rover_runner_cli.py" ping --repo-url "%REPO_URL%"
if %ERRORLEVEL%==0 exit /b 0

if /I "%REPO_URL:~0,8%"=="https://" (
  if "%REPO_PROVIDER%"=="" set "REPO_PROVIDER=auto"

  if /I "%REPO_PROVIDER%"=="github" (
    if "%GITHUB_TOKEN%"=="" (
      echo ERROR: REPO_PROVIDER=github requires GITHUB_TOKEN
      exit /b 1
    )
    if "%GIT_USERNAME%"=="" set "GIT_USERNAME=x-access-token"
    set "RB_AUTH_USER=%GIT_USERNAME%"
    set "RB_AUTH_TOKEN=%GITHUB_TOKEN%"
  ) else (
    if /I "%REPO_PROVIDER%"=="bitbucket" (
      if "%BITBUCKET_APP_PASSWORD%"=="" if "%BITBUCKET_TOKEN%"=="" (
        echo ERROR: REPO_PROVIDER=bitbucket requires BITBUCKET_APP_PASSWORD ^(or BITBUCKET_TOKEN^)
        exit /b 1
      )
      if "%BITBUCKET_USERNAME%"=="" if "%GIT_USERNAME%"=="" (
        echo ERROR: BITBUCKET_USERNAME ^(or GIT_USERNAME^) is required for Bitbucket HTTPS auth
        exit /b 1
      )
      if "%BITBUCKET_USERNAME%"=="" (
        set "RB_AUTH_USER=%GIT_USERNAME%"
      ) else (
        set "RB_AUTH_USER=%BITBUCKET_USERNAME%"
      )
      if not "%BITBUCKET_APP_PASSWORD%"=="" (
        set "RB_AUTH_TOKEN=%BITBUCKET_APP_PASSWORD%"
      ) else (
        set "RB_AUTH_TOKEN=%BITBUCKET_TOKEN%"
      )
    ) else (
      if /I "%REPO_PROVIDER%"=="auto" (
        if not "%GITHUB_TOKEN%"=="" (
          if "%GIT_USERNAME%"=="" set "GIT_USERNAME=x-access-token"
          set "RB_AUTH_USER=%GIT_USERNAME%"
          set "RB_AUTH_TOKEN=%GITHUB_TOKEN%"
        ) else (
          if not "%BITBUCKET_APP_PASSWORD%"=="" (
            if "%BITBUCKET_USERNAME%"=="" if "%GIT_USERNAME%"=="" (
              echo ERROR: BITBUCKET_USERNAME ^(or GIT_USERNAME^) is required for Bitbucket HTTPS auth
              exit /b 1
            )
            if "%BITBUCKET_USERNAME%"=="" (
              set "RB_AUTH_USER=%GIT_USERNAME%"
            ) else (
              set "RB_AUTH_USER=%BITBUCKET_USERNAME%"
            )
            set "RB_AUTH_TOKEN=%BITBUCKET_APP_PASSWORD%"
          ) else (
            if not "%BITBUCKET_TOKEN%"=="" (
              if "%BITBUCKET_USERNAME%"=="" if "%GIT_USERNAME%"=="" (
                echo ERROR: BITBUCKET_USERNAME ^(or GIT_USERNAME^) is required for Bitbucket HTTPS auth
                exit /b 1
              )
              if "%BITBUCKET_USERNAME%"=="" (
                set "RB_AUTH_USER=%GIT_USERNAME%"
              ) else (
                set "RB_AUTH_USER=%BITBUCKET_USERNAME%"
              )
              set "RB_AUTH_TOKEN=%BITBUCKET_TOKEN%"
            ) else (
              echo ERROR: HTTPS remote detected but no token provided ^(GITHUB_TOKEN, BITBUCKET_APP_PASSWORD, or BITBUCKET_TOKEN^)
              exit /b 1
            )
          )
        )
      ) else (
        echo ERROR: REPO_PROVIDER must be auto, github, or bitbucket
        exit /b 1
      )
    )
  )

  if "%RB_AUTH_TOKEN%"=="" (
    echo ERROR: HTTPS remote detected but no token provided ^(GITHUB_TOKEN or BITBUCKET_APP_PASSWORD^)
    exit /b 1
  )

  set "ASKPASS_FILE=%TEMP%\repo_rover_runner_askpass_%RANDOM%%RANDOM%.cmd"
  > "%ASKPASS_FILE%" (
    echo @echo off
    echo echo %%~1 ^| findstr /I "username" ^>nul ^&^& ^(echo %%RB_AUTH_USER%% ^& exit /b 0^)
    echo echo %%~1 ^| findstr /I "password" ^>nul ^&^& ^(echo %%RB_AUTH_TOKEN%% ^& exit /b 0^)
    echo exit /b 0
  )
  set "GIT_ASKPASS=%ASKPASS_FILE%"
  set "GIT_TERMINAL_PROMPT=0"
)

  "%PYTHON_EXE%" "%SCRIPT_DIR%repo_rover_runner_cli.py" ping --repo-url "%REPO_URL%"
set "RC=%ERRORLEVEL%"
if defined ASKPASS_FILE if exist "%ASKPASS_FILE%" del /q "%ASKPASS_FILE%" >nul 2>&1
exit /b %RC%
