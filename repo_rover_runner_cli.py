#!/usr/bin/env python3
"""Compatibility wrapper for the refactored repo rover runner client."""

from __future__ import annotations

from repo_rover_runner_client import main


if __name__ == "__main__":
    raise SystemExit(main())
