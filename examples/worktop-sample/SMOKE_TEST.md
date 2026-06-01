# Smoke Test Usage

These scripts install dependencies, start the sample backend, and submit one publish job.

## Windows

```bat
set WORKTOP_REPO_URL=https://github.com/your-org/your-repo.git
set WORKTOP_BASE_BRANCH=main
set REPO_PROVIDER=auto
set GITHUB_TOKEN=... or BITBUCKET_APP_PASSWORD=...
examples\worktop-sample\run-worktop-sample.bat
```

## macOS/Linux

```bash
export WORKTOP_REPO_URL=https://github.com/your-org/your-repo.git
export WORKTOP_BASE_BRANCH=main
export REPO_PROVIDER=auto
export GITHUB_TOKEN=... # or BITBUCKET_APP_PASSWORD=...
chmod +x examples/worktop-sample/run-worktop-sample.sh
examples/worktop-sample/run-worktop-sample.sh
```

## What the smoke test does

1. Installs backend and frontend dependencies if `node_modules` is missing.
2. Starts the sample backend.
3. Creates a temporary generated script file from `dummy_payload.txt`.
4. Posts a publish job to the backend.
5. Polls until the job succeeds or fails.

## Expected inputs

- `WORKTOP_REPO_URL`: allowed Git or Bitbucket repository URL
- `WORKTOP_BASE_BRANCH`: usually `main` or `master`
- `REPO_PROVIDER`: `auto`, `github`, or `bitbucket`
- Auth env vars required by the selected provider
