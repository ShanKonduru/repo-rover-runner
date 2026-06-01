# `run_github_connectivity`

Scripts:

- `run_github_connectivity.bat`
- `run_github_connectivity.sh`

## Purpose

Runs the connectivity check using the GitHub-specific env file.

## What It Does

1. Sets `REPO_PROVIDER=github`.
2. Sets `REPO_CONFIG_FILE` to `repo_rover_runner.github.env` in the repo root.
3. Delegates to `test_ping_repo`.

## Expected Outcome

- Confirms the configured GitHub remote is reachable.
- Exits non-zero if the env file is missing, the repo URL is missing, or authentication fails.

## Required Files

- `repo_rover_runner.github.env`

## Notes

- This is a convenience wrapper for provider-specific smoke testing.
- For HTTPS remotes, `test_ping_repo` may use `GITHUB_TOKEN` and defaults `GIT_USERNAME` to `x-access-token` if not set.