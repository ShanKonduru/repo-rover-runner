# `run_bitbucket_tests`

Scripts:

- `run_bitbucket_tests.bat`
- `run_bitbucket_tests.sh`

## Purpose

Runs the full Bitbucket end-to-end script sequence against the configured repository.

## What It Does

1. Sets `REPO_PROVIDER=bitbucket`.
2. Sets `REPO_CONFIG_FILE` to `repo_rover_runner.bitbucket.env`.
3. Runs these helpers in order:
   - `test_ping_repo`
   - `create_new_branch`
   - `test_list_branches`
   - `test_use_branch`
   - `list_files_in_branch`
   - `test_push_dummy`

## Expected Outcome

- Confirms remote access, branch management, branch listing, file listing, and push flow all work for the configured Bitbucket repo.
- Stops immediately on the first failing step.

## Required Files

- `repo_rover_runner.bitbucket.env`

## Notes

- This is the highest-level Bitbucket smoke test wrapper in the root scripts.
- Because it ends with `test_push_dummy`, it is expected to create and push a real commit to the target branch when successful.