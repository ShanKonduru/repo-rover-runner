from __future__ import annotations

from typing import Optional

from .auth import resolve_auth_from_env
from .exceptions import GitCommandError
from .interfaces import RepoOps
from .operations import BitbucketOps, GitOps


class RepoOpsFactory:
    """Creates provider-specific repository operation handlers."""

    @staticmethod
    def create(provider: Optional[str] = None) -> RepoOps:
        selected = (provider or "auto").strip().lower()

        if selected in {"", "auto"}:
            auth_user, auth_token = resolve_auth_from_env("auto")
            if not auth_token:
                return GitOps()
            if auth_user == "x-access-token":
                return GitOps()
            return BitbucketOps()

        if selected == "github":
            return GitOps()

        if selected == "bitbucket":
            return BitbucketOps()

        raise GitCommandError("REPO_PROVIDER must be one of: auto, github, bitbucket")
