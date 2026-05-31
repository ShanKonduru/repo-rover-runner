from __future__ import annotations

import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Iterable, List, Optional

from .exceptions import GitCommandError
from .interfaces import RepoOps


class BaseRepoOps(RepoOps):
    """Shared git-based implementation used by provider-specific classes."""

    provider_name = "base"

    def _resolve_git_executable(self) -> str:
        git_executable = shutil.which("git")
        if not git_executable:
            raise GitCommandError("git executable was not found on PATH")
        return git_executable

    def _normalize_git_args(self, args: List[str]) -> List[str]:
        if not args:
            raise GitCommandError("git command arguments cannot be empty")
        if any(not isinstance(arg, str) or not arg for arg in args):
            raise GitCommandError("git command arguments must be non-empty strings")
        return args

    def run_git(self, args: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        normalized_args = self._normalize_git_args(args)
        cmd = [self._resolve_git_executable(), *normalized_args]
        result = subprocess.run(  # nosec B603
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if check and result.returncode != 0:
            raise GitCommandError(
                f"Command failed: {' '.join(cmd)}\n"
                f"exit_code={result.returncode}\n"
                f"stdout={result.stdout.strip()}\n"
                f"stderr={result.stderr.strip()}"
            )
        return result

    def get_remote_url(self, repo_path: Path, remote: str = "origin") -> Optional[str]:
        result = self.run_git(["remote", "get-url", remote], cwd=repo_path, check=False)
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    def ensure_repo_path(self, repo_path: Path) -> None:
        if not repo_path.exists():
            raise GitCommandError(f"Repository path does not exist: {repo_path}")
        if not (repo_path / ".git").exists():
            raise GitCommandError(f"Not a git repository: {repo_path}")

    def ping_repo(self, repo_url: str) -> None:
        self.run_git(["ls-remote", repo_url, "HEAD"])
        print(f"OK: Remote is reachable: {repo_url}")

    def clone_repo(self, repo_url: str, dest: Path, branch: Optional[str]) -> None:
        if dest.exists() and any(dest.iterdir()):
            raise GitCommandError(f"Destination exists and is not empty: {dest}")
        dest.mkdir(parents=True, exist_ok=True)

        cmd = ["clone", repo_url, str(dest)]
        if branch:
            cmd.extend(["--branch", branch])

        self.run_git(cmd)
        print(f"OK: Cloned {repo_url} into {dest}")

    def local_branch_exists(self, repo_path: Path, branch: str) -> bool:
        result = self.run_git(["rev-parse", "--verify", branch], cwd=repo_path, check=False)
        return result.returncode == 0

    def remote_branch_exists(self, repo_path: Path, branch: str, remote: str = "origin") -> bool:
        result = self.run_git(["ls-remote", "--heads", remote, branch], cwd=repo_path, check=False)
        return result.returncode == 0 and bool(result.stdout.strip())

    def repo_has_commits(self, repo_path: Path) -> bool:
        result = self.run_git(["rev-parse", "--verify", "HEAD"], cwd=repo_path, check=False)
        return result.returncode == 0

    def checkout_branch(self, repo_path: Path, branch: str, base_branch: str = "main", remote: str = "origin") -> None:
        self.ensure_repo_path(repo_path)
        self.run_git(["fetch", remote], cwd=repo_path)

        if self.local_branch_exists(repo_path, branch):
            self.run_git(["checkout", branch], cwd=repo_path)
            print(f"OK: Switched to local branch: {branch}")
            return

        if self.remote_branch_exists(repo_path, branch, remote=remote):
            self.run_git(["checkout", "-b", branch, f"{remote}/{branch}"], cwd=repo_path)
            print(f"OK: Created local branch {branch} tracking {remote}/{branch}")
            return

        if self.remote_branch_exists(repo_path, base_branch, remote=remote):
            self.run_git(["checkout", "-b", branch, f"{remote}/{base_branch}"], cwd=repo_path)
            print(f"OK: Created new branch {branch} from {remote}/{base_branch}")
            return

        if self.local_branch_exists(repo_path, base_branch):
            self.run_git(["checkout", "-b", branch, base_branch], cwd=repo_path)
            print(f"OK: Created new branch {branch} from local {base_branch}")
            return

        if not self.repo_has_commits(repo_path):
            self.run_git(["checkout", "--orphan", branch], cwd=repo_path)
            print(f"OK: Created orphan branch {branch} for empty repository")
            return

        raise GitCommandError(
            f"Could not create branch '{branch}'. Base branch '{base_branch}' not found locally or on {remote}."
        )

    def list_branches(self, repo_path: Path, remote: str = "origin", scope: str = "all") -> None:
        self.ensure_repo_path(repo_path)
        self.run_git(["fetch", remote], cwd=repo_path)

        if scope in ("all", "local"):
            local_res = self.run_git(["branch", "--format", "%(refname:short)"], cwd=repo_path)
            print("Local branches:")
            local_lines = [line.strip() for line in local_res.stdout.splitlines() if line.strip()]
            if not local_lines:
                print("  (none)")
            else:
                for name in local_lines:
                    print(f"  {name}")

        if scope in ("all", "remote"):
            remote_res = self.run_git(["branch", "-r", "--format", "%(refname:short)"], cwd=repo_path)
            print("Remote branches:")
            remote_lines = [line.strip() for line in remote_res.stdout.splitlines() if line.strip()]
            filtered = [line for line in remote_lines if line.startswith(f"{remote}/")]
            if not filtered:
                print("  (none)")
            else:
                for name in filtered:
                    print(f"  {name}")

    def copy_sources_to_repo(self, sources: Iterable[Path], repo_path: Path, target_dir: Path) -> List[Path]:
        copied: List[Path] = []
        destination_root = repo_path / target_dir
        destination_root.mkdir(parents=True, exist_ok=True)

        for src in sources:
            if not src.exists():
                raise GitCommandError(f"Source path does not exist: {src}")

            dest = destination_root / src.name
            if src.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            copied.append(dest)

        return copied

    def has_staged_changes(self, repo_path: Path) -> bool:
        result = self.run_git(["diff", "--cached", "--name-only"], cwd=repo_path)
        return bool(result.stdout.strip())

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
        self.ensure_repo_path(repo_path)
        self.checkout_branch(repo_path, branch, base_branch=base_branch, remote=remote)

        copied = self.copy_sources_to_repo(files, repo_path, target_dir)
        add_args = ["add", "--"] + [str(path.relative_to(repo_path)) for path in copied]
        self.run_git(add_args, cwd=repo_path)

        if not self.has_staged_changes(repo_path):
            print("INFO: No staged changes to commit after copying files.")
            return

        self.run_git(["commit", "-m", commit_message], cwd=repo_path)
        self.run_git(["push", "-u", remote, branch], cwd=repo_path)
        print(f"OK: Committed and pushed files to {remote}/{branch}")


class GitOps(BaseRepoOps):
    provider_name = "github"


class BitbucketOps(BaseRepoOps):
    provider_name = "bitbucket"
