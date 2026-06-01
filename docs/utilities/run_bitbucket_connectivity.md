# `run_bitbucket_connectivity`

Scripts:

- `run_bitbucket_connectivity.bat`
- `run_bitbucket_connectivity.sh`

## Purpose

Runs the connectivity check using the Bitbucket-specific env file.

## What It Does

1. Sets `REPO_PROVIDER=bitbucket`.
2. Sets `REPO_CONFIG_FILE` to `repo_rover_runner.bitbucket.env` in the repo root.
3. Delegates to `test_ping_repo`.

## Expected Outcome

- Confirms the configured Bitbucket remote is reachable.
- Exits non-zero if the env file is missing, the repo URL is missing, or authentication fails.

## Required Files

- `repo_rover_runner.bitbucket.env`

## Notes

- This is a convenience wrapper for provider-specific smoke testing.
- For HTTPS remotes, `test_ping_repo` may use `BITBUCKET_APP_PASSWORD` or `BITBUCKET_TOKEN` plus `BITBUCKET_USERNAME` or `GIT_USERNAME`.