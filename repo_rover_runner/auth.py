from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Optional

from .exceptions import GitCommandError


def resolve_auth_from_env(provider: Optional[str] = None) -> tuple[str, str]:
    selected = (provider or os.environ.get("REPO_PROVIDER", "auto")).strip().lower()

    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    github_user = os.environ.get("GIT_USERNAME", "").strip() or "x-access-token"

    bitbucket_token = os.environ.get("BITBUCKET_APP_PASSWORD", "").strip() or os.environ.get("BITBUCKET_TOKEN", "").strip()
    bitbucket_user = os.environ.get("BITBUCKET_USERNAME", "").strip() or os.environ.get("GIT_USERNAME", "").strip()

    if selected == "github":
        if not github_token:
            raise GitCommandError("REPO_PROVIDER=github requires GITHUB_TOKEN for HTTPS auth")
        return github_user, github_token

    if selected == "bitbucket":
        if not bitbucket_token:
            raise GitCommandError("REPO_PROVIDER=bitbucket requires BITBUCKET_APP_PASSWORD (or BITBUCKET_TOKEN)")
        if not bitbucket_user:
            raise GitCommandError("BITBUCKET_USERNAME (or GIT_USERNAME) is required for Bitbucket HTTPS auth")
        return bitbucket_user, bitbucket_token

    if selected not in {"", "auto"}:
        raise GitCommandError("REPO_PROVIDER must be one of: auto, github, bitbucket")

    if github_token:
        return github_user, github_token

    if bitbucket_token:
        if not bitbucket_user:
            raise GitCommandError("BITBUCKET_USERNAME (or GIT_USERNAME) is required for Bitbucket HTTPS auth")
        return bitbucket_user, bitbucket_token

    return "", ""


class GitAuthSession:
    """Configures temporary GIT_ASKPASS credentials for HTTPS remotes."""

    def __init__(self, repo_url: Optional[str], provider: Optional[str] = None):
        self.repo_url = repo_url or ""
        self.provider = provider
        self.askpass_file: Optional[Path] = None
        self._prev_env: dict[str, Optional[str]] = {}

    def __enter__(self) -> "GitAuthSession":
        self._enable_if_needed()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()

    def _enable_if_needed(self) -> None:
        if not self.repo_url.lower().startswith("https://"):
            return

        if os.environ.get("GIT_ASKPASS"):
            return

        auth_user, auth_token = resolve_auth_from_env(self.provider)
        if not auth_token:
            return

        self._set_env("RB_AUTH_USER", auth_user)
        self._set_env("RB_AUTH_TOKEN", auth_token)
        self._set_env("GIT_TERMINAL_PROMPT", "0")

        if os.name == "nt":
            askpass_path = Path(tempfile.gettempdir()) / f"repo_rover_runner_askpass_{os.getpid()}.cmd"
            askpass_path.write_text(
                "@echo off\n"
                "echo %~1 | findstr /I \"username\" >nul && (echo %RB_AUTH_USER% & exit /b 0)\n"
                "echo %~1 | findstr /I \"password\" >nul && (echo %RB_AUTH_TOKEN% & exit /b 0)\n"
                "exit /b 0\n",
                encoding="utf-8",
            )
        else:  # pragma: no cover
            askpass_path = Path(tempfile.gettempdir()) / f"repo_rover_runner_askpass_{os.getpid()}.sh"
            askpass_path.write_text(
                "#!/usr/bin/env bash\n"
                "prompt=\"$1\"\n"
                "case \"$prompt\" in\n"
                "  *sername*|*Username*) printf '%s\\n' \"${RB_AUTH_USER}\" ;;\n"
                "  *assword*|*Password*) printf '%s\\n' \"${RB_AUTH_TOKEN}\" ;;\n"
                "  *) printf '\\n' ;;\n"
                "esac\n",
                encoding="utf-8",
            )
            askpass_path.chmod(askpass_path.stat().st_mode | stat.S_IXUSR)

        self.askpass_file = askpass_path
        self._set_env("GIT_ASKPASS", str(askpass_path))

    def _set_env(self, key: str, value: str) -> None:
        if key not in self._prev_env:
            self._prev_env[key] = os.environ.get(key)
        os.environ[key] = value

    def cleanup(self) -> None:
        if self.askpass_file and self.askpass_file.exists():
            try:
                self.askpass_file.unlink()
            except OSError:
                pass

        for key, prev in self._prev_env.items():
            if prev is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prev
