from __future__ import annotations

import unittest
from unittest.mock import patch

from repo_rover_runner.exceptions import GitCommandError
from repo_rover_runner.factory import RepoOpsFactory
from repo_rover_runner.operations import BitbucketOps, GitOps


class TestRepoOpsFactory(unittest.TestCase):
    def test_create_github(self) -> None:
        self.assertIsInstance(RepoOpsFactory.create("github"), GitOps)

    def test_create_bitbucket(self) -> None:
        self.assertIsInstance(RepoOpsFactory.create("bitbucket"), BitbucketOps)

    def test_create_auto_no_token_defaults_github(self) -> None:
        with patch("repo_rover_runner.factory.resolve_auth_from_env", return_value=("", "")):
            self.assertIsInstance(RepoOpsFactory.create("auto"), GitOps)

    def test_create_auto_github_signature(self) -> None:
        with patch("repo_rover_runner.factory.resolve_auth_from_env", return_value=("x-access-token", "gh")):
            self.assertIsInstance(RepoOpsFactory.create("auto"), GitOps)

    def test_create_auto_bitbucket_signature(self) -> None:
        with patch("repo_rover_runner.factory.resolve_auth_from_env", return_value=("bb-user", "bb")):
            self.assertIsInstance(RepoOpsFactory.create("auto"), BitbucketOps)

    def test_invalid_provider(self) -> None:
        with self.assertRaises(GitCommandError):
            RepoOpsFactory.create("bad")
