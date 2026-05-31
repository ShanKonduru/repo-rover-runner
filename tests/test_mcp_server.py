from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import repo_rover_runner_mcp_server as mcp_server


class TestMcpServer(unittest.TestCase):
    def test_ping_repo_calls_provider(self) -> None:
        mock_ops = MagicMock()
        mock_ops.provider_name = "github"
        mock_ops.ping_repo.side_effect = lambda _repo_url: print("OK: Remote is reachable")

        with patch("repo_rover_runner_mcp_server.RepoOpsFactory.create", return_value=mock_ops), patch(
            "repo_rover_runner_mcp_server.GitAuthSession"
        ):
            output = mcp_server.ping_repo("https://example/repo.git", provider="github")

        self.assertIn("OK: Remote is reachable", output)
        mock_ops.ping_repo.assert_called_once_with("https://example/repo.git")

    def test_list_branches_uses_remote_url_resolution(self) -> None:
        mock_ops = MagicMock()
        mock_ops.provider_name = "github"
        mock_ops.get_remote_url.return_value = "https://example/repo.git"

        with patch("repo_rover_runner_mcp_server.RepoOpsFactory.create", return_value=mock_ops), patch(
            "repo_rover_runner_mcp_server.GitAuthSession"
        ):
            _ = mcp_server.list_branches(repo_path=".", provider="github")

        mock_ops.get_remote_url.assert_called_once_with(Path("."), remote="origin")
        mock_ops.list_branches.assert_called_once()

    def test_push_files_maps_input_to_paths(self) -> None:
        mock_ops = MagicMock()
        mock_ops.provider_name = "github"
        mock_ops.get_remote_url.return_value = "https://example/repo.git"

        with patch("repo_rover_runner_mcp_server.RepoOpsFactory.create", return_value=mock_ops), patch(
            "repo_rover_runner_mcp_server.GitAuthSession"
        ):
            _ = mcp_server.push_files(
                repo_path=".",
                branch="feature/a",
                files=["dummy_payload.txt"],
                commit_message="test commit",
                provider="github",
            )

        _, kwargs = mock_ops.push_files.call_args
        self.assertEqual(kwargs["repo_path"], Path("."))
        self.assertEqual(kwargs["files"], [Path("dummy_payload.txt")])
        self.assertEqual(kwargs["target_dir"], Path("."))

    def test_main_raises_if_mcp_missing(self) -> None:
        with patch.object(mcp_server, "mcp", None):
            with self.assertRaises(RuntimeError):
                mcp_server.main()


if __name__ == "__main__":
    unittest.main()
