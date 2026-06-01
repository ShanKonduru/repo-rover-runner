# `list_files_in_branch`

Scripts:

- `list_files_in_branch.bat`
- `list_files_in_branch.sh`

## Purpose

Lists every file path reachable from a selected branch or branch ref.

## What It Does

1. Resolves the env file and loads repository settings.
2. Requires `REPO_URL` and `LOCAL_REPO_PATH`.
3. Defaults `REMOTE` to `origin`.
4. Chooses `BRANCH_TO_LIST`, falling back to `TARGET_BRANCH`, then `main`.
5. Clones the repo if needed.
6. Fetches from the configured remote.
7. Resolves the requested branch locally first, then as `REMOTE/BRANCH_TO_LIST`.
8. Runs `git ls-tree -r --name-only` against the resolved ref.

## Expected Outcome

- The script prints a flat list of files in the chosen branch.
- It fails if the branch cannot be found either locally or on the configured remote.

## Required Config

- `REPO_URL`
- `LOCAL_REPO_PATH`

## Optional Config

- `BRANCH_TO_LIST`
- `TARGET_BRANCH`
- `REMOTE`
- `REPO_PROVIDER`
- `REPO_CONFIG_FILE`

## Notes

- This helper is read-only after the optional clone step.
- It uses direct git commands rather than a dedicated CLI subcommand for file listing.