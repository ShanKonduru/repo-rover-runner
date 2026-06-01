# `create_new_branch`

Scripts:

- `create_new_branch.bat`
- `create_new_branch.sh`

## Purpose

Creates or reuses the configured target branch in the local working clone.

## What It Does

1. Resolves which env file to load.
2. Requires `REPO_URL`, `LOCAL_REPO_PATH`, and `TARGET_BRANCH`.
3. Defaults `BASE_BRANCH` to `main` and `REMOTE` to `origin`.
4. Clones the repository into `LOCAL_REPO_PATH` if no local git repo exists yet.
5. Runs the CLI `use-branch` command with the configured target branch and base branch.

## Expected Outcome

- A local clone exists at `LOCAL_REPO_PATH`.
- The working copy ends up on `TARGET_BRANCH`.
- If the branch already exists locally or remotely, it is reused.
- If it does not exist, it is created from `BASE_BRANCH` when possible.

## Required Config

- `REPO_URL`
- `LOCAL_REPO_PATH`
- `TARGET_BRANCH`

## Optional Config

- `BASE_BRANCH`
- `REMOTE`
- `REPO_PROVIDER`
- `REPO_CONFIG_FILE`

## Notes

- This helper is effectively a wrapper around `clone` followed by `use-branch`.
- It does not push a commit by itself.