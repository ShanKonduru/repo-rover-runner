@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
for %%I in ("%ROOT%..\..") do set "REPO_ROOT=%%~fI"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"
set "PYTHON_BIN=%REPO_ROOT%\.venv\Scripts\python.exe"
set "BACKEND_PORT=4070"
set "FRONTEND_PORT=5173"

if not defined REPO_PROVIDER set "REPO_PROVIDER=github"
if /I "%REPO_PROVIDER%"=="bitbucket" (
  set "ENV_FILE=%REPO_ROOT%\repo_rover_runner.bitbucket.env"
) else (
  set "ENV_FILE=%REPO_ROOT%\repo_rover_runner.github.env"
)

if not exist "%PYTHON_BIN%" (
  echo ERROR: Python not found at "%PYTHON_BIN%"
  exit /b 1
)

if exist "%ENV_FILE%" (
  call :load_env_file "%ENV_FILE%"
)

if not defined WORKTOP_REPO_URL set "WORKTOP_REPO_URL=%REPO_URL%"
if not defined WORKTOP_BASE_BRANCH set "WORKTOP_BASE_BRANCH=%BASE_BRANCH%"
if not defined WORKTOP_GENERATED_PATH (
  for %%I in ("%REPO_ROOT%\dummy_payload.txt") do set "WORKTOP_GENERATED_PATH=%%~fI"
)
if not defined WORKTOP_TARGET_DIR set "WORKTOP_TARGET_DIR=%TARGET_DIR%"
if not defined WORKTOP_COMMIT_MESSAGE set "WORKTOP_COMMIT_MESSAGE=%COMMIT_MESSAGE%"
if "%REPO_PROVIDER%"=="" set "REPO_PROVIDER=auto"

if not defined WORKTOP_REPO_URL (
  echo ERROR: WORKTOP_REPO_URL or REPO_URL was not found.
  exit /b 1
)

if defined LOCAL_REPO_PATH (
  for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$repoRoot = [System.IO.Path]::GetFullPath('%REPO_ROOT%'); $p = '%LOCAL_REPO_PATH%'; if ([System.IO.Path]::IsPathRooted($p)) { [System.IO.Path]::GetFullPath($p) } else { [System.IO.Path]::GetFullPath((Join-Path $repoRoot $p)) }"`) do set "WORKTOP_REPO_DIR=%%I"
)

if not defined WORKTOP_REPO_DIR set "WORKTOP_REPO_DIR=%ROOT%_tmp-repo"
if not defined WORKTOP_TARGET_DIR set "WORKTOP_TARGET_DIR=tests/generated"
if not defined WORKTOP_COMMIT_MESSAGE set "WORKTOP_COMMIT_MESSAGE=Worktop smoke test: add generated test script"
if not defined WORKTOP_BASE_BRANCH set "WORKTOP_BASE_BRANCH=main"

if not exist "%BACKEND_DIR%\node_modules" (
  echo Installing backend dependencies...
  pushd "%BACKEND_DIR%"
  call npm install
  if errorlevel 1 exit /b 1
  popd
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo Installing frontend dependencies...
  pushd "%FRONTEND_DIR%"
  call npm install
  if errorlevel 1 exit /b 1
  popd
)

set "WORKTOP_JOB_DIR=%ROOT%_tmp-job"
if exist "%WORKTOP_JOB_DIR%" rmdir /s /q "%WORKTOP_JOB_DIR%"
if exist "%WORKTOP_REPO_DIR%" rmdir /s /q "%WORKTOP_REPO_DIR%"
mkdir "%WORKTOP_JOB_DIR%" >nul 2>&1

if "%ALLOWED_REPO_PREFIXES%"=="" (
  echo WARNING: ALLOWED_REPO_PREFIXES is not set. The backend sample allows any repo URL.
)

pushd "%BACKEND_DIR%"
start "worktop-sample-backend" /B cmd /c "set PORT=%BACKEND_PORT%&& set PYTHON_BIN=%PYTHON_BIN%&& npm start"
popd

pushd "%FRONTEND_DIR%"
start "worktop-sample-frontend" /B cmd /c "npm run dev -- --host 127.0.0.1 --port %FRONTEND_PORT%"
popd

call :wait_for_http "http://127.0.0.1:%BACKEND_PORT%/api/health" 30
if errorlevel 1 exit /b 1

echo Submitting smoke-test publish job...
set "JOB_FILE=%WORKTOP_JOB_DIR%\job-response.json"
if not defined WORKTOP_REPO_URL (
  echo ERROR: Set WORKTOP_REPO_URL before running the smoke test.
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$payload = @{ provider = if ($env:REPO_PROVIDER) { $env:REPO_PROVIDER } else { 'auto' }; repoUrl = $env:WORKTOP_REPO_URL; localRepoPath = $env:WORKTOP_REPO_DIR; generatedPath = $env:WORKTOP_GENERATED_PATH; targetDir = if ($env:WORKTOP_TARGET_DIR) { $env:WORKTOP_TARGET_DIR } else { 'tests/generated' }; baseBranch = if ($env:WORKTOP_BASE_BRANCH) { $env:WORKTOP_BASE_BRANCH } else { 'main' }; remote = 'origin'; branchHint = 'worktop-smoke'; commitMessage = if ($env:WORKTOP_COMMIT_MESSAGE) { $env:WORKTOP_COMMIT_MESSAGE } else { 'Worktop smoke test: add generated test script' } } | ConvertTo-Json -Depth 5;" ^
  "$response = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:%BACKEND_PORT%/api/jobs/publish-generated-scripts' -ContentType 'application/json' -Body $payload;" ^
  "$response | ConvertTo-Json -Depth 5 | Set-Content -Path '%JOB_FILE%' -Encoding UTF8"
if errorlevel 1 exit /b 1

echo Polling job status...
for /f "usebackq delims=" %%J in (`powershell -NoProfile -Command "(Get-Content '%JOB_FILE%' | ConvertFrom-Json).jobId"`) do set "JOB_ID=%%J"
for /l %%i in (1,1,60) do (
  powershell -NoProfile -Command "$job = Invoke-RestMethod -Uri ('http://127.0.0.1:%BACKEND_PORT%/api/jobs/%JOB_ID%'); $job | ConvertTo-Json -Depth 6" > "%JOB_FILE%"
  findstr /c:"\"status\":\"succeeded\"" "%JOB_FILE%" >nul
  if not errorlevel 1 goto :job_done
  findstr /c:"\"status\":\"failed\"" "%JOB_FILE%" >nul
  if not errorlevel 1 goto :job_failed
  timeout /t 2 /nobreak >nul
)

echo ERROR: Job did not finish in time.
exit /b 1

:job_done
echo Smoke test succeeded.
type "%JOB_FILE%"
exit /b 0

:job_failed
echo ERROR: Smoke test job failed.
type "%JOB_FILE%"
exit /b 1

:wait_for_http
set "URL=%~1"
set "MAX_ATTEMPTS=%~2"
for /l %%i in (1,1,%MAX_ATTEMPTS%) do (
  powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri '%URL%' | Out-Null; exit 0 } catch { exit 1 }"
  if not errorlevel 1 exit /b 0
  timeout /t 1 /nobreak >nul
)
echo ERROR: Service did not become ready: %URL%
exit /b 1

:load_env_file
set "ENV_PATH=%~1"
for /f "usebackq tokens=1,* delims==" %%A in (`powershell -NoProfile -Command ^
  "$lines = Get-Content -LiteralPath '%ENV_PATH%';" ^
  "foreach ($line in $lines) {" ^
  "  if ([string]::IsNullOrWhiteSpace($line)) { continue }" ^
  "  if ($line.TrimStart().StartsWith('#')) { continue }" ^
  "  $parts = $line -split '=', 2;" ^
  "  if ($parts.Count -lt 2) { continue }" ^
  "  $key = $parts[0].Trim();" ^
  "  $value = $parts[1];" ^
  "  if ($key) { [Console]::WriteLine(($key + '=' + $value)) }" ^
  "}"`) do (
  set "%%A=%%B"
)
exit /b 0
