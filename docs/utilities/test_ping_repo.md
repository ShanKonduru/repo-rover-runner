# `test_ping_repo`

Scripts:

- `test_ping_repo.bat`
- `test_ping_repo.sh`

## Purpose

Checks whether the configured remote repository is reachable.

## What It Does

1. Resolves and loads the active env file.
2. Requires `REPO_URL`.
3. Tries `repo_rover_runner_cli.py ping --repo-url ...` without extra auth first.
4. If the ping fails and the repo URL is HTTPS, it prepares temporary `GIT_ASKPASS` credentials from the env file.
5. Retries the ping with non-interactive auth enabled.
6. Deletes the temporary askpass helper before exit.

## Expected Outcome

- Succeeds for reachable remotes with valid credentials.
- Fails with explicit messages when required tokens or usernames are missing for HTTPS auth.

## Required Config

- `REPO_URL`

## Optional Auth Config

- `REPO_PROVIDER=auto|github|bitbucket`
- `GITHUB_TOKEN`
- `GIT_USERNAME`
- `BITBUCKET_APP_PASSWORD`
- `BITBUCKET_TOKEN`
- `BITBUCKET_USERNAME`
- `REPO_CONFIG_FILE`

## Notes

- Public repos may succeed on the first ping without any credentials.
- The helper only creates temporary askpass state for the duration of the script run.