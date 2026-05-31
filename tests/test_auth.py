from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from repo_rover_runner.auth import GitAuthSession, resolve_auth_from_env
from repo_rover_runner.exceptions import GitCommandError


class TestResolveAuthFromEnv(unittest.TestCase):
    def test_provider_github_requires_token(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "github"}, clear=True):
            with self.assertRaises(GitCommandError):
                resolve_auth_from_env()

    def test_provider_github_success(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "github", "GITHUB_TOKEN": "gh", "GIT_USERNAME": "u"}, clear=True):
            self.assertEqual(resolve_auth_from_env(), ("u", "gh"))

    def test_provider_bitbucket_success(self) -> None:
        env = {
            "REPO_PROVIDER": "bitbucket",
            "BITBUCKET_USERNAME": "bb-user",
            "BITBUCKET_APP_PASSWORD": "bb-token",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(resolve_auth_from_env(), ("bb-user", "bb-token"))

    def test_provider_bitbucket_requires_token(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "bitbucket", "BITBUCKET_USERNAME": "bb-user"}, clear=True):
            with self.assertRaises(GitCommandError):
                resolve_auth_from_env()

    def test_provider_bitbucket_requires_user(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "bitbucket", "BITBUCKET_APP_PASSWORD": "x"}, clear=True):
            with self.assertRaises(GitCommandError):
                resolve_auth_from_env()

    def test_auto_prefers_github(self) -> None:
        env = {
            "REPO_PROVIDER": "auto",
            "GITHUB_TOKEN": "gh",
            "BITBUCKET_APP_PASSWORD": "bb",
            "BITBUCKET_USERNAME": "bb-user",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(resolve_auth_from_env(), ("x-access-token", "gh"))

    def test_auto_returns_bitbucket_credentials(self) -> None:
        env = {
            "REPO_PROVIDER": "auto",
            "BITBUCKET_APP_PASSWORD": "bb",
            "BITBUCKET_USERNAME": "bb-user",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(resolve_auth_from_env(), ("bb-user", "bb"))

    def test_auto_bitbucket_requires_user(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "auto", "BITBUCKET_TOKEN": "bb"}, clear=True):
            with self.assertRaises(GitCommandError):
                resolve_auth_from_env()

    def test_invalid_provider(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "invalid"}, clear=True):
            with self.assertRaises(GitCommandError):
                resolve_auth_from_env()

    def test_auto_no_credentials(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "auto"}, clear=True):
            self.assertEqual(resolve_auth_from_env(), ("", ""))


class TestGitAuthSession(unittest.TestCase):
    def test_no_https_remote_skips_setup(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with GitAuthSession("ssh://host/repo") as session:
                self.assertIsNone(session.askpass_file)

    def test_respects_existing_askpass(self) -> None:
        with patch.dict(os.environ, {"GIT_ASKPASS": "already"}, clear=True):
            with GitAuthSession("https://host/repo") as session:
                self.assertIsNone(session.askpass_file)

    def test_windows_askpass_lifecycle(self) -> None:
        env = {
            "REPO_PROVIDER": "github",
            "GITHUB_TOKEN": "gh-token",
            "GIT_USERNAME": "x-access-token",
        }
        with patch.dict(os.environ, env, clear=True), patch("repo_rover_runner.auth.os.name", "nt"):
            with GitAuthSession("https://host/repo") as session:
                self.assertIsNotNone(session.askpass_file)
                assert session.askpass_file is not None
                self.assertTrue(session.askpass_file.exists())
                self.assertEqual(os.environ.get("GIT_TERMINAL_PROMPT"), "0")
                self.assertIn("RB_AUTH_USER", os.environ)

            self.assertNotIn("GIT_ASKPASS", os.environ)
            self.assertNotIn("RB_AUTH_TOKEN", os.environ)

    def test_https_without_credentials_does_not_set_askpass(self) -> None:
        with patch.dict(os.environ, {"REPO_PROVIDER": "auto"}, clear=True):
            with GitAuthSession("https://host/repo") as session:
                self.assertIsNone(session.askpass_file)

    def test_cleanup_handles_unlink_failure(self) -> None:
        session = GitAuthSession("https://host/repo")
        temp_file = Path(tempfile.gettempdir()) / "repo_rover_runner_fake_cleanup.cmd"
        temp_file.write_text("x", encoding="utf-8")
        session.askpass_file = temp_file
        session._prev_env = {"RB_AUTH_USER": None}

        with patch.object(Path, "unlink", side_effect=OSError):
            session.cleanup()

        self.assertNotIn("RB_AUTH_USER", os.environ)

    def test_cleanup_restores_previous_value(self) -> None:
        session = GitAuthSession("https://host/repo")
        with patch.dict(os.environ, {"RB_AUTH_USER": "before"}, clear=True):
            session._prev_env = {"RB_AUTH_USER": "before"}
            os.environ["RB_AUTH_USER"] = "changed"
            session.cleanup()
            self.assertEqual(os.environ["RB_AUTH_USER"], "before")
