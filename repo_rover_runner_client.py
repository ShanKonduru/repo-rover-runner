#!/usr/bin/env python3
"""Client CLI for provider-specific repo operations via factory."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from repo_rover_runner import GitAuthSession, GitCommandError, RepoOpsFactory

BANNER = r"""+----------------------------+
|      REPO ROVER RUNNER     |
+----------------------------+"""
GRADIENT_START = (56, 189, 248)
GRADIENT_END = (244, 63, 94)


def _interpolate_channel(start: int, end: int, index: int, total: int) -> int:
    if total <= 1:
        return start
    return round(start + (end - start) * (index / (total - 1)))


def _render_banner() -> str:
    try:
        from pyfiglet import Figlet
    except ImportError:
        return BANNER

    for font_name in ("double_blocky", "blocky", "big", "slant", "standard"):
        try:
            return Figlet(font=font_name).renderText("REPO-ROVER-RUNNER")
        except Exception:
            continue

    return BANNER


def _print_banner() -> None:
    banner_text = _render_banner().rstrip("\n")

    try:
        from rich.console import Console
    except ImportError:
        print(banner_text)
        return

    console = Console()
    lines = banner_text.splitlines()
    total = max(len(lines), 1)

    for index, line in enumerate(lines):
        red = _interpolate_channel(GRADIENT_START[0], GRADIENT_END[0], index, total)
        green = _interpolate_channel(GRADIENT_START[1], GRADIENT_END[1], index, total)
        blue = _interpolate_channel(GRADIENT_START[2], GRADIENT_END[2], index, total)
        console.print(line, style=f"bold rgb({red},{green},{blue})")

    console.print("REPO ROVER RUNNER", style="bold")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-rover-runner-client",
        description="GitHub/Bitbucket branch and file push helper using git CLI.",
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "github", "bitbucket"],
        default=os.environ.get("REPO_PROVIDER", "auto"),
        help="Provider selection strategy (default: REPO_PROVIDER or auto)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    ping = sub.add_parser("ping", help="Ping remote repository")
    ping.add_argument("--repo-url", required=True, help="Remote repository URL")

    clone = sub.add_parser("clone", help="Clone remote repository")
    clone.add_argument("--repo-url", required=True, help="Remote repository URL")
    clone.add_argument("--dest", required=True, type=Path, help="Destination folder")
    clone.add_argument("--branch", default=None, help="Optional branch to clone")

    use_branch = sub.add_parser("use-branch", help="Create or connect to a branch")
    use_branch.add_argument("--repo-path", required=True, type=Path, help="Local repository path")
    use_branch.add_argument("--branch", required=True, help="Branch to use")
    use_branch.add_argument("--base-branch", default="main", help="Base branch if creating new branch")
    use_branch.add_argument("--remote", default="origin", help="Remote name (default: origin)")

    list_cmd = sub.add_parser("list-branches", help="List local and/or remote branches")
    list_cmd.add_argument("--repo-path", required=True, type=Path, help="Local repository path")
    list_cmd.add_argument("--remote", default="origin", help="Remote name (default: origin)")
    list_cmd.add_argument(
        "--scope",
        choices=["all", "local", "remote"],
        default="all",
        help="Branch scope to list (default: all)",
    )

    push = sub.add_parser("push-files", help="Copy files, commit, and push to a branch")
    push.add_argument("--repo-path", required=True, type=Path, help="Local repository path")
    push.add_argument("--branch", required=True, help="Target branch")
    push.add_argument("--files", required=True, nargs="+", type=Path, help="Files or folders to copy")
    push.add_argument("--target-dir", default=".", type=Path, help="Target folder inside repo")
    push.add_argument("--commit-message", required=True, help="Commit message")
    push.add_argument("--base-branch", default="main", help="Base branch if target does not exist")
    push.add_argument("--remote", default="origin", help="Remote name (default: origin)")

    return parser


def _get_repo_url_for_auth(command: str, args: argparse.Namespace, provider_ops: object) -> Optional[str]:
    if command in {"ping", "clone"}:
        return args.repo_url

    if command in {"use-branch", "list-branches", "push-files"}:
        repo_path = args.repo_path
        remote = getattr(args, "remote", "origin")
        if isinstance(repo_path, Path) and hasattr(provider_ops, "get_remote_url"):
            return provider_ops.get_remote_url(repo_path, remote=remote)  # type: ignore[attr-defined]

    return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    _print_banner()

    try:
        provider_ops = RepoOpsFactory.create(args.provider)
        repo_url = _get_repo_url_for_auth(args.command, args, provider_ops)

        with GitAuthSession(repo_url, provider=provider_ops.provider_name):
            if args.command == "ping":
                provider_ops.ping_repo(args.repo_url)
            elif args.command == "clone":
                provider_ops.clone_repo(args.repo_url, args.dest, args.branch)
            elif args.command == "use-branch":
                provider_ops.checkout_branch(args.repo_path, args.branch, base_branch=args.base_branch, remote=args.remote)
            elif args.command == "list-branches":
                provider_ops.list_branches(args.repo_path, remote=args.remote, scope=args.scope)
            elif args.command == "push-files":
                provider_ops.push_files(
                    repo_path=args.repo_path,
                    branch=args.branch,
                    files=args.files,
                    commit_message=args.commit_message,
                    target_dir=args.target_dir,
                    base_branch=args.base_branch,
                    remote=args.remote,
                )
            else:  # pragma: no cover
                parser.error(f"Unknown command: {args.command}")
    except GitCommandError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    from repo_rover_runner_client import main as client_main

    raise SystemExit(client_main())
