# `run_security_reports`

Scripts:

- `run_security_reports.bat`
- `run_security_reports.sh`

## Purpose

Generates the repository's security report artifacts.

## What It Does

1. Changes to the repository root.
2. Runs `scripts/generate_security_reports.py`.

## Expected Outcome

- The report generator completes successfully and writes whatever outputs `generate_security_reports.py` is designed to emit.

## Requirements

- Python available either in `.venv` on Windows or on `PATH`.
- Any dependencies required by `scripts/generate_security_reports.py` installed in the current environment.

## Notes

- This helper does not add wrapper logic beyond choosing the Python executable and launching the report generator.