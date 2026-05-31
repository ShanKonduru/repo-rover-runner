#!/usr/bin/env python3
"""MCP server wrapper for Repo Rover Runner operations."""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path
from typing import Callable, Iterable, Literal, Optional

from repo_rover_runner import GitAuthSession, GitCommandError, RepoOpsFactory

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[assignment]

Provider = Literal["auto", "github", "bitbucket"]
Scope = Literal["all", "local", "remote"]

mcp = FastMCP("repo-rover-runner") if FastMCP else None


def _capture_output(callable_op: Callable[[], None]) -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        callable_op()
    return buffer.getvalue().strip()


def _resolve_repo_url(command: str, repo_url: Optional[str], repo_path: Optional[Path], remote: str, provider_ops: object) -> Optional[str]:
    if command in {"ping", "clone"}:
        return repo_url

    if repo_path and hasattr(provider_ops, "get_remote_url"):
        return provider_ops.get_remote_url(repo_path, remote=remote)  # type: ignore[attr-defined]

    return None


def _execute_with_auth(
    provider: Provider,
    command: str,
    operation: Callable[[object], str],
    repo_url: Optional[str] = None,
    repo_path: Optional[Path] = None,
    remote: str = "origin",
) -> str:
    provider_ops = RepoOpsFactory.create(provider)
    resolved_repo_url = _resolve_repo_url(command, repo_url, repo_path, remote, provider_ops)

    try:
        with GitAuthSession(resolved_repo_url, provider=provider_ops.provider_name):
            return operation(provider_ops)
    except GitCommandError as exc:
        raise RuntimeError(str(exc)) from exc


def ping_repo(repo_url: str, provider: Provider = "auto") -> str:
    return _execute_with_auth(
        provider=provider,
        command="ping",
        repo_url=repo_url,
        operation=lambda ops: _capture_output(lambda: ops.ping_repo(repo_url)),
    )


def clone_repo(repo_url: str, dest: str, branch: Optional[str] = None, provider: Provider = "auto") -> str:
    dest_path = Path(dest)
    return _execute_with_auth(
        provider=provider,
        command="clone",
        repo_url=repo_url,
        operation=lambda ops: _capture_output(lambda: ops.clone_repo(repo_url, dest_path, branch)),
    )


def use_branch(repo_path: str, branch: str, base_branch: str = "main", remote: str = "origin", provider: Provider = "auto") -> str:
    path = Path(repo_path)
    return _execute_with_auth(
        provider=provider,
        command="use-branch",
        repo_path=path,
        remote=remote,
        operation=lambda ops: _capture_output(lambda: ops.checkout_branch(path, branch, base_branch=base_branch, remote=remote)),
    )


def list_branches(repo_path: str, scope: Scope = "all", remote: str = "origin", provider: Provider = "auto") -> str:
    path = Path(repo_path)
    return _execute_with_auth(
        provider=provider,
        command="list-branches",
        repo_path=path,
        remote=remote,
        operation=lambda ops: _capture_output(lambda: ops.list_branches(path, remote=remote, scope=scope)),
    )


def push_files(
    repo_path: str,
    branch: str,
    files: Iterable[str],
    commit_message: str,
    target_dir: str = ".",
    base_branch: str = "main",
    remote: str = "origin",
    provider: Provider = "auto",
) -> str:
    path = Path(repo_path)
    file_paths = [Path(item) for item in files]
    return _execute_with_auth(
        provider=provider,
        command="push-files",
        repo_path=path,
        remote=remote,
        operation=lambda ops: _capture_output(
            lambda: ops.push_files(
                repo_path=path,
                branch=branch,
                files=file_paths,
                commit_message=commit_message,
                target_dir=Path(target_dir),
                base_branch=base_branch,
                remote=remote,
            )
        ),
    )


if mcp:

    @mcp.tool(name="ping_repo")
    def mcp_ping_repo(repo_url: str, provider: Provider = "auto") -> str:
        """Verify remote repository connectivity and auth."""

        return ping_repo(repo_url=repo_url, provider=provider)


    @mcp.tool(name="clone_repo")
    def mcp_clone_repo(repo_url: str, dest: str, branch: Optional[str] = None, provider: Provider = "auto") -> str:
        """Clone a remote repository to a local path."""

        return clone_repo(repo_url=repo_url, dest=dest, branch=branch, provider=provider)


    @mcp.tool(name="use_branch")
    def mcp_use_branch(
        repo_path: str,
        branch: str,
        base_branch: str = "main",
        remote: str = "origin",
        provider: Provider = "auto",
    ) -> str:
        """Create or switch to a branch, with base branch fallback logic."""

        return use_branch(repo_path=repo_path, branch=branch, base_branch=base_branch, remote=remote, provider=provider)


    @mcp.tool(name="list_branches")
    def mcp_list_branches(repo_path: str, scope: Scope = "all", remote: str = "origin", provider: Provider = "auto") -> str:
        """List local and remote branches."""

        return list_branches(repo_path=repo_path, scope=scope, remote=remote, provider=provider)


    @mcp.tool(name="push_files")
    def mcp_push_files(
        repo_path: str,
        branch: str,
        files: list[str],
        commit_message: str,
        target_dir: str = ".",
        base_branch: str = "main",
        remote: str = "origin",
        provider: Provider = "auto",
    ) -> str:
        """Copy files into a repo, commit, and push."""

        return push_files(
            repo_path=repo_path,
            branch=branch,
            files=files,
            commit_message=commit_message,
            target_dir=target_dir,
            base_branch=base_branch,
            remote=remote,
            provider=provider,
        )


def main() -> int:
    if not mcp:
        raise RuntimeError("mcp package is required. Install with: pip install .[dev]")

    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
