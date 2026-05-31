from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from repo_rover_runner.exceptions import GitCommandError
from repo_rover_runner.operations import BaseRepoOps


class FakeResult:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class ScriptedOps(BaseRepoOps):
    def __init__(self, responses: list[FakeResult]) -> None:
        self.responses = responses
        self.calls: list[list[str]] = []

    def run_git(self, args, cwd=None, check=True):  # type: ignore[override]
        self.calls.append(args)
        if not self.responses:
            return FakeResult(0, "")
        result = self.responses.pop(0)
        if check and result.returncode != 0:
            raise GitCommandError("command failed")
        return result


class TestBaseRepoOps(unittest.TestCase):
    def test_run_git_success(self) -> None:
        ops = BaseRepoOps()
        with patch("repo_rover_runner.operations.shutil.which", return_value="/usr/bin/git"), patch(
            "repo_rover_runner.operations.subprocess.run", return_value=FakeResult(0, "ok", "")
        ):
            result = ops.run_git(["status"])
            self.assertEqual(result.stdout, "ok")

    def test_run_git_failure(self) -> None:
        ops = BaseRepoOps()
        with patch("repo_rover_runner.operations.shutil.which", return_value="/usr/bin/git"), patch(
            "repo_rover_runner.operations.subprocess.run", return_value=FakeResult(1, "o", "e")
        ):
            with self.assertRaises(GitCommandError):
                ops.run_git(["status"])

    def test_run_git_requires_non_empty_args(self) -> None:
        with self.assertRaises(GitCommandError):
            BaseRepoOps().run_git([])

    def test_run_git_rejects_empty_arg(self) -> None:
        with self.assertRaises(GitCommandError):
            BaseRepoOps().run_git([""])

    def test_run_git_requires_git_on_path(self) -> None:
        ops = BaseRepoOps()
        with patch("repo_rover_runner.operations.shutil.which", return_value=None):
            with self.assertRaises(GitCommandError):
                ops.run_git(["status"])

    def test_get_remote_url_none(self) -> None:
        ops = ScriptedOps([FakeResult(1, "", "")])
        self.assertIsNone(ops.get_remote_url(Path(".")))

    def test_get_remote_url_value(self) -> None:
        ops = ScriptedOps([FakeResult(0, "https://x\n", "")])
        self.assertEqual(ops.get_remote_url(Path(".")), "https://x")

    def test_ensure_repo_path_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ops = BaseRepoOps()
            with self.assertRaises(GitCommandError):
                ops.ensure_repo_path(Path(td) / "missing")

    def test_ensure_repo_path_not_git(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ops = BaseRepoOps()
            with self.assertRaises(GitCommandError):
                ops.ensure_repo_path(Path(td))

    def test_ensure_repo_path_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".git").mkdir()
            BaseRepoOps().ensure_repo_path(repo)

    def test_ping_repo(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", "")])
        ops.ping_repo("https://example/repo")
        self.assertEqual(ops.calls[0][0], "ls-remote")

    def test_clone_repo_dest_not_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "dest"
            dest.mkdir()
            (dest / "x.txt").write_text("x", encoding="utf-8")
            with self.assertRaises(GitCommandError):
                BaseRepoOps().clone_repo("https://x", dest, None)

    def test_clone_repo_success_with_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "dest"
            ops = ScriptedOps([FakeResult(0, "", "")])
            ops.clone_repo("https://x", dest, "main")
            self.assertIn("--branch", ops.calls[0])

    def test_local_branch_exists_true(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", "")])
        self.assertTrue(ops.local_branch_exists(Path("."), "b"))

    def test_remote_branch_exists_false(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", "")])
        self.assertFalse(ops.remote_branch_exists(Path("."), "b"))

    def test_repo_has_commits_false(self) -> None:
        ops = ScriptedOps([FakeResult(1, "", "")])
        self.assertFalse(ops.repo_has_commits(Path(".")))

    def test_checkout_branch_local_exists(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", ""), FakeResult(0, "", "")])
        with patch.object(ops, "ensure_repo_path"), patch.object(ops, "local_branch_exists", return_value=True):
            ops.checkout_branch(Path("."), "feature")
            self.assertIn(["checkout", "feature"], ops.calls)

    def test_checkout_branch_remote_exists(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", ""), FakeResult(0, "", "")])
        with patch.object(ops, "ensure_repo_path"), patch.object(ops, "local_branch_exists", return_value=False), patch.object(
            ops, "remote_branch_exists", side_effect=[True]
        ):
            ops.checkout_branch(Path("."), "feature")
            self.assertIn(["checkout", "-b", "feature", "origin/feature"], ops.calls)

    def test_checkout_branch_remote_base_exists(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", ""), FakeResult(0, "", "")])
        with patch.object(ops, "ensure_repo_path"), patch.object(ops, "local_branch_exists", return_value=False), patch.object(
            ops, "remote_branch_exists", side_effect=[False, True]
        ):
            ops.checkout_branch(Path("."), "feature")
            self.assertIn(["checkout", "-b", "feature", "origin/main"], ops.calls)

    def test_checkout_branch_local_base_exists(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", ""), FakeResult(0, "", "")])
        with patch.object(ops, "ensure_repo_path"), patch.object(ops, "local_branch_exists", side_effect=[False, True]), patch.object(
            ops, "remote_branch_exists", side_effect=[False, False]
        ):
            ops.checkout_branch(Path("."), "feature")
            self.assertIn(["checkout", "-b", "feature", "main"], ops.calls)

    def test_checkout_branch_orphan(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", ""), FakeResult(0, "", "")])
        with patch.object(ops, "ensure_repo_path"), patch.object(ops, "local_branch_exists", side_effect=[False, False]), patch.object(
            ops, "remote_branch_exists", side_effect=[False, False]
        ), patch.object(ops, "repo_has_commits", return_value=False):
            ops.checkout_branch(Path("."), "feature")
            self.assertIn(["checkout", "--orphan", "feature"], ops.calls)

    def test_checkout_branch_error(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", "")])
        with patch.object(ops, "ensure_repo_path"), patch.object(ops, "local_branch_exists", side_effect=[False, False]), patch.object(
            ops, "remote_branch_exists", side_effect=[False, False]
        ), patch.object(ops, "repo_has_commits", return_value=True):
            with self.assertRaises(GitCommandError):
                ops.checkout_branch(Path("."), "feature")

    def test_list_branches_all(self) -> None:
        ops = ScriptedOps([
            FakeResult(0, "", ""),
            FakeResult(0, "main\nfeature\n", ""),
            FakeResult(0, "origin/main\nupstream/dev\n", ""),
        ])
        with patch.object(ops, "ensure_repo_path"):
            ops.list_branches(Path("."), remote="origin", scope="all")
        self.assertEqual(ops.calls[0], ["fetch", "origin"])

    def test_list_branches_remote_none(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", ""), FakeResult(0, "", "")])
        with patch.object(ops, "ensure_repo_path"):
            ops.list_branches(Path("."), remote="origin", scope="remote")

    def test_list_branches_local_none(self) -> None:
        ops = ScriptedOps([FakeResult(0, "", ""), FakeResult(0, "", "")])
        with patch.object(ops, "ensure_repo_path"):
            ops.list_branches(Path("."), remote="origin", scope="local")

    def test_copy_sources_to_repo_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".git").mkdir()
            with self.assertRaises(GitCommandError):
                BaseRepoOps().copy_sources_to_repo([repo / "missing.txt"], repo, Path("dest"))

    def test_copy_sources_to_repo_file_and_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = base / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            src_file = base / "a.txt"
            src_file.write_text("a", encoding="utf-8")
            src_dir = base / "d"
            src_dir.mkdir()
            (src_dir / "x.txt").write_text("x", encoding="utf-8")

            copied = BaseRepoOps().copy_sources_to_repo([src_file, src_dir], repo, Path("target"))
            self.assertEqual(len(copied), 2)

            # Re-copy directory to exercise overwrite path.
            copied_again = BaseRepoOps().copy_sources_to_repo([src_dir], repo, Path("target"))
            self.assertEqual(len(copied_again), 1)

    def test_has_staged_changes_true(self) -> None:
        ops = ScriptedOps([FakeResult(0, "file.txt\n", "")])
        self.assertTrue(ops.has_staged_changes(Path(".")))

    def test_push_files_no_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = base / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            src = base / "a.txt"
            src.write_text("a", encoding="utf-8")

            ops = ScriptedOps([FakeResult(0, "", "")])
            with patch.object(ops, "ensure_repo_path"), patch.object(ops, "checkout_branch"), patch.object(
                ops, "has_staged_changes", return_value=False
            ):
                ops.push_files(repo, "b", [src], "msg", Path("."), "main", "origin")
            self.assertEqual(ops.calls[0][0], "add")

    def test_push_files_with_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = base / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            src = base / "a.txt"
            src.write_text("a", encoding="utf-8")

            ops = ScriptedOps([FakeResult(0, "", ""), FakeResult(0, "", ""), FakeResult(0, "", "")])
            with patch.object(ops, "ensure_repo_path"), patch.object(ops, "checkout_branch"), patch.object(
                ops, "has_staged_changes", return_value=True
            ):
                ops.push_files(repo, "b", [src], "msg", Path("."), "main", "origin")
            self.assertIn(["commit", "-m", "msg"], ops.calls)
            self.assertIn(["push", "-u", "origin", "b"], ops.calls)
