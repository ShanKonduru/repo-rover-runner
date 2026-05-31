from __future__ import annotations

import runpy
import sys
import unittest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import repo_rover_runner_client


class TestCliClient(unittest.TestCase):
    def test_get_repo_url_for_auth_with_ping(self) -> None:
        parser = repo_rover_runner_client.build_parser()
        args = parser.parse_args(["ping", "--repo-url", "https://x"])
        url = repo_rover_runner_client._get_repo_url_for_auth(args.command, args, object())
        self.assertEqual(url, "https://x")

    def test_get_repo_url_for_auth_with_repo_path(self) -> None:
        parser = repo_rover_runner_client.build_parser()
        args = parser.parse_args(["list-branches", "--repo-path", "."])
        mock_ops = MagicMock()
        mock_ops.get_remote_url.return_value = "https://remote"
        url = repo_rover_runner_client._get_repo_url_for_auth(args.command, args, mock_ops)
        self.assertEqual(url, "https://remote")

    def test_get_repo_url_for_auth_returns_none(self) -> None:
        parser = repo_rover_runner_client.build_parser()
        args = parser.parse_args(["list-branches", "--repo-path", "."])
        url = repo_rover_runner_client._get_repo_url_for_auth(args.command, args, object())
        self.assertIsNone(url)

    def test_main_ping(self) -> None:
        mock_ops = MagicMock()
        mock_ops.provider_name = "github"
        with patch("repo_rover_runner_client.RepoOpsFactory.create", return_value=mock_ops), patch("repo_rover_runner_client.GitAuthSession"):
            rc = repo_rover_runner_client.main(["ping", "--repo-url", "https://x"])
        self.assertEqual(rc, 0)
        mock_ops.ping_repo.assert_called_once_with("https://x")

    def test_main_clone(self) -> None:
        mock_ops = MagicMock()
        mock_ops.provider_name = "github"
        with patch("repo_rover_runner_client.RepoOpsFactory.create", return_value=mock_ops), patch("repo_rover_runner_client.GitAuthSession"):
            rc = repo_rover_runner_client.main(["clone", "--repo-url", "https://x", "--dest", "tmp"])
        self.assertEqual(rc, 0)
        mock_ops.clone_repo.assert_called_once_with("https://x", Path("tmp"), None)

    def test_main_use_branch(self) -> None:
        mock_ops = MagicMock()
        mock_ops.provider_name = "github"
        with patch("repo_rover_runner_client.RepoOpsFactory.create", return_value=mock_ops), patch("repo_rover_runner_client.GitAuthSession"):
            rc = repo_rover_runner_client.main(["use-branch", "--repo-path", ".", "--branch", "feature"])
        self.assertEqual(rc, 0)
        mock_ops.checkout_branch.assert_called_once()

    def test_main_list_branches(self) -> None:
        mock_ops = MagicMock()
        mock_ops.provider_name = "github"
        with patch("repo_rover_runner_client.RepoOpsFactory.create", return_value=mock_ops), patch("repo_rover_runner_client.GitAuthSession"):
            rc = repo_rover_runner_client.main(["list-branches", "--repo-path", ".", "--scope", "remote"])
        self.assertEqual(rc, 0)
        mock_ops.list_branches.assert_called_once()

    def test_main_push_files(self) -> None:
        mock_ops = MagicMock()
        mock_ops.provider_name = "github"
        with patch("repo_rover_runner_client.RepoOpsFactory.create", return_value=mock_ops), patch("repo_rover_runner_client.GitAuthSession"):
            rc = repo_rover_runner_client.main(
                [
                    "push-files",
                    "--repo-path",
                    ".",
                    "--branch",
                    "feature",
                    "--files",
                    "repo_rover_runner_client.py",
                    "--commit-message",
                    "m",
                ]
            )
        self.assertEqual(rc, 0)
        mock_ops.push_files.assert_called_once()

    def test_main_handles_git_error(self) -> None:
        with patch("repo_rover_runner_client.RepoOpsFactory.create", side_effect=repo_rover_runner_client.GitCommandError("x")):
            rc = repo_rover_runner_client.main(["ping", "--repo-url", "https://x"])
        self.assertEqual(rc, 1)

    def test_legacy_wrapper_executes(self) -> None:
        with patch("repo_rover_runner_client.main", return_value=0):
            with self.assertRaises(SystemExit) as ctx:
                runpy.run_path("repo_rover_runner_cli.py", run_name="__main__")
        self.assertEqual(ctx.exception.code, 0)

    def test_client_main_dunder_executes(self) -> None:
        with patch.object(sys, "argv", ["repo_rover_runner_client.py", "ping", "--repo-url", "https://x"]), patch(
            "repo_rover_runner_client.RepoOpsFactory.create"
        ) as create_mock, patch("repo_rover_runner_client.GitAuthSession"):
            mock_ops = MagicMock()
            mock_ops.provider_name = "github"
            create_mock.return_value = mock_ops
            with self.assertRaises(SystemExit) as ctx:
                runpy.run_path("repo_rover_runner_client.py", run_name="__main__")
        self.assertEqual(ctx.exception.code, 0)

    def test_client_main_dunder_executes_with_github_provider_env(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "github"}, clear=False), patch.object(
            sys, "argv", ["repo_rover_runner_client.py", "ping", "--repo-url", "https://x"]
        ), patch("repo_rover_runner_client.RepoOpsFactory.create") as create_mock, patch(
            "repo_rover_runner_client.GitAuthSession"
        ):
            mock_ops = MagicMock()
            mock_ops.provider_name = "github"
            create_mock.return_value = mock_ops
            with self.assertRaises(SystemExit) as ctx:
                runpy.run_path("repo_rover_runner_client.py", run_name="__main__")
        self.assertEqual(ctx.exception.code, 0)
