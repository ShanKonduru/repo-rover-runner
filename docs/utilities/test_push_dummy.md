# `test_push_dummy`

Scripts:

- `test_push_dummy.bat`
- `test_push_dummy.sh`

## Purpose

Validates the file-copy, commit, and push workflow by pushing `dummy_payload.txt` into the configured branch.

## What It Does

1. Resolves and loads the active env file.
2. Requires `REPO_URL`, `LOCAL_REPO_PATH`, and `TARGET_BRANCH`.
3. Defaults `BASE_BRANCH` to `main`, `REMOTE` to `origin`, `TARGET_DIR` to `integration-tests`, and `COMMIT_MESSAGE` to a predefined test message.
4. Prepares temporary HTTPS auth when required.
5. Clones the repo if needed.
6. Runs the CLI `push-files` command using `dummy_payload.txt` as the source payload.

## Expected Outcome

- The target branch exists or is created as needed.
- `dummy_payload.txt` is copied into `TARGET_DIR` inside the repo.
- A commit is created with `COMMIT_MESSAGE` and pushed to the remote branch.

## Required Config

- `REPO_URL`
- `LOCAL_REPO_PATH`
- `TARGET_BRANCH`

## Optional Config

- `BASE_BRANCH`
- `REMOTE`
- `TARGET_DIR`
- `COMMIT_MESSAGE`
- `REPO_PROVIDER`
- `REPO_CONFIG_FILE`
- HTTPS auth variables used by `test_ping_repo`

## Notes

- This helper performs a real write operation against the remote repository.
- Use a disposable test branch if you do not want the pushed dummy file to affect an existing workflow.