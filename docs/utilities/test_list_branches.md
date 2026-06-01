# `test_list_branches`

Scripts:

- `test_list_branches.bat`
- `test_list_branches.sh`

## Purpose

Exercises the CLI branch-listing behavior against the configured repo.

## What It Does

1. Resolves and loads the active env file.
2. Requires `REPO_URL` and `LOCAL_REPO_PATH`.
3. Defaults `REMOTE` to `origin`.
4. Clones the repo if the target local repo does not exist yet.
5. Runs `repo_rover_runner_cli.py list-branches --scope all`.

## Expected Outcome

- Prints both local and remote branches for the working clone.
- Exits non-zero if the env file is missing, the required variables are missing, clone fails, or the CLI list operation fails.

## Required Config

- `REPO_URL`
- `LOCAL_REPO_PATH`

## Optional Config

- `REMOTE`
- `REPO_PROVIDER`
- `REPO_CONFIG_FILE`

## Notes

- This is a direct wrapper over the CLI `list-branches` subcommand.