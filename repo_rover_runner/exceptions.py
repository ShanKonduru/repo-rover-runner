from __future__ import annotations


class GitCommandError(RuntimeError):
    """Raised when a git command or repository operation fails."""
