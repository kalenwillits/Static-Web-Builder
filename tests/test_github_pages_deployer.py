"""Tests for GitHub Pages deployment."""

import os
import pytest
from unittest.mock import patch, MagicMock
from swb.core.github_pages_deployer import (
    check_git_cli,
    generate_pages_files,
    deploy_github_pages,
)


class TestCheckGitCli:
    @patch("subprocess.run")
    def test_returns_true_when_installed(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="git version 2.45\n")
        assert check_git_cli() is True

    @patch("subprocess.run")
    def test_returns_false_when_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        assert check_git_cli() is False

    @patch("subprocess.run")
    def test_returns_false_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert check_git_cli() is False


class TestGeneratePagesFiles:
    def test_creates_nojekyll(self, tmp_path):
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        generate_pages_files(output_dir)
        assert os.path.exists(os.path.join(output_dir, ".nojekyll"))

    def test_does_not_create_cname_without_domain(self, tmp_path):
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        generate_pages_files(output_dir)
        assert not os.path.exists(os.path.join(output_dir, "CNAME"))

    def test_creates_cname_with_domain(self, tmp_path):
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        generate_pages_files(output_dir, domain="example.com")
        cname_path = os.path.join(output_dir, "CNAME")
        assert os.path.exists(cname_path)
        with open(cname_path) as f:
            assert f.read().strip() == "example.com"

    def test_does_not_overwrite_existing_nojekyll(self, tmp_path):
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        marker = os.path.join(output_dir, ".nojekyll")
        with open(marker, "w") as f:
            f.write("keep")
        generate_pages_files(output_dir)
        with open(marker) as f:
            assert f.read() == "keep"


class TestDeployGithubPages:
    @patch("swb.core.github_pages_deployer.check_git_cli")
    def test_raises_when_git_not_installed(self, mock_check, tmp_path):
        mock_check.return_value = False
        with pytest.raises(RuntimeError, match="git is not installed"):
            deploy_github_pages(str(tmp_path), str(tmp_path / "build"), {})

    @patch("swb.core.github_pages_deployer.check_git_cli")
    def test_raises_when_no_remote_configured(self, mock_check, tmp_path):
        mock_check.return_value = True
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        with pytest.raises(RuntimeError, match="GitHub remote"):
            deploy_github_pages(str(tmp_path), output_dir, {})

    @patch("subprocess.run")
    @patch("swb.core.github_pages_deployer.check_git_cli")
    def test_pushes_to_configured_remote_and_branch(self, mock_check, mock_run, tmp_path):
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)

        deploy_github_pages(
            str(tmp_path),
            output_dir,
            {"github_remote": "git@github.com:me/site.git", "github_branch": "gh-pages"},
        )

        push_calls = [
            c for c in mock_run.call_args_list
            if "push" in c[0][0]
        ]
        assert len(push_calls) == 1
        push_cmd = push_calls[0][0][0]
        assert "git@github.com:me/site.git" in push_cmd
        assert "HEAD:gh-pages" in push_cmd
        assert "--force" in push_cmd

    @patch("subprocess.run")
    @patch("swb.core.github_pages_deployer.check_git_cli")
    def test_writes_nojekyll_before_deploy(self, mock_check, mock_run, tmp_path):
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)

        deploy_github_pages(
            str(tmp_path), output_dir, {"github_remote": "origin"}
        )
        assert os.path.exists(os.path.join(output_dir, ".nojekyll"))

    @patch("subprocess.run")
    @patch("swb.core.github_pages_deployer.check_git_cli")
    def test_raises_when_git_step_fails(self, mock_check, mock_run, tmp_path):
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="fatal: boom")
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)

        with pytest.raises(RuntimeError, match="git .* failed"):
            deploy_github_pages(
                str(tmp_path), output_dir, {"github_remote": "origin"}
            )
