# `run_github_tests`

Scripts:

- `run_github_tests.bat`
- `run_github_tests.sh`

## Purpose

Runs the full GitHub end-to-end script sequence against the configured repository.

## What It Does

1. Sets `REPO_PROVIDER=github`.
2. Sets `REPO_CONFIG_FILE` to `repo_rover_runner.github.env`.
3. Runs these helpers in order:
   - `test_ping_repo`
   - `create_new_branch`
   - `test_list_branches`
   - `test_use_branch`
   - `list_files_in_branch`
   - `test_push_dummy`

## Expected Outcome

- Confirms remote access, branch management, branch listing, file listing, and push flow all work for the configured GitHub repo.
- Stops immediately on the first failing step.

## Required Files

- `repo_rover_runner.github.env`

## Notes

- This is the highest-level GitHub smoke test wrapper in the root scripts.
- Because it ends with `test_push_dummy`, it is expected to create and push a real commit to the target branch when successful.