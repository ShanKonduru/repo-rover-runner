from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class RepoOps(ABC):
    """Contract for provider-specific repository operations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def ping_repo(self, repo_url: str) -> None:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def clone_repo(self, repo_url: str, dest: Path, branch: Optional[str]) -> None:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def checkout_branch(self, repo_path: Path, branch: str, base_branch: str = "main", remote: str = "origin") -> None:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def list_branches(self, repo_path: Path, remote: str = "origin", scope: str = "all") -> None:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def push_files(
        self,
        repo_path: Path,
        branch: str,
        files: List[Path],
        commit_message: str,
        target_dir: Path,
        base_branch: str,
        remote: str,
    ) -> None:
        raise NotImplementedError  # pragma: no cover
