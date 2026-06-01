# `test_use_branch`

Scripts:

- `test_use_branch.bat`
- `test_use_branch.sh`

## Purpose

Exercises the CLI branch-selection logic against the configured repository.

## What It Does

1. Resolves and loads the active env file.
2. Requires `REPO_URL`, `LOCAL_REPO_PATH`, and `TARGET_BRANCH`.
3. Defaults `BASE_BRANCH` to `main` and `REMOTE` to `origin`.
4. Clones the repo if needed.
5. Runs the CLI `use-branch` command.

## Expected Outcome

- The working clone is left checked out on `TARGET_BRANCH`.
- If the branch exists locally or remotely, it is attached to.
- If it does not exist, it is created from the configured base branch when possible.

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

- This helper overlaps heavily with `create_new_branch`; both currently invoke the same CLI flow.
- The practical difference is naming: this one reads as a validation step in the scripted test sequence.