# `run_repo_rover_runner_unit_tests`

Scripts:

- `run_repo_rover_runner_unit_tests.bat`
- `run_repo_rover_runner_unit_tests.sh`

## Purpose

Runs the Python unit test suite under coverage.

## What It Does

1. Changes to the repository root.
2. Clears previous coverage state.
3. Runs `unittest discover` for `tests/test_*.py` under coverage.
4. Prints the coverage report using `.coveragerc`.
5. Prints a success message indicating the suite passed with full coverage.

## Expected Outcome

- All unit tests pass.
- Coverage reporting completes successfully.

## Requirements

- Python available either in `.venv` on Windows or on `PATH`.
- Coverage installed in the active environment.

## Notes

- The success message says `100% coverage`, so this helper assumes the configured suite still satisfies that bar.