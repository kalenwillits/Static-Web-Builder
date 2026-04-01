"""Tests for CLI routing."""

import os
import sys
import pytest
import yaml
from unittest.mock import patch, MagicMock
from swb.cli import main


class TestCliCreate:
    def test_creates_project(self, tmp_path, monkeypatch):
        project_dir = str(tmp_path / "testsite")
        monkeypatch.setattr(sys, 'argv', ['swb', project_dir])
        main()
        assert os.path.exists(os.path.join(project_dir, ".swb"))
        assert os.path.exists(os.path.join(project_dir, "site.yaml"))

    def test_rejects_existing_project(self, tmp_path, monkeypatch):
        project_dir = str(tmp_path / "testsite")
        monkeypatch.setattr(sys, 'argv', ['swb', project_dir])
        main()
        with pytest.raises(SystemExit):
            main()


class TestCliBuild:
    def _make_project(self, tmp_path):
        """Create a minimal swb project for build testing."""
        (tmp_path / ".swb").write_text("# swb project: test\n")
        site_config = {
            'metadata': {'title': 'Test', 'author': 'Tester', 'language': 'en-US'},
            'default_css': ['default.css'],
            'discovery': {
                'root': '.',
                'exclude': ['.git', 'build', 'context', 'templates', 'assets'],
            },
            'output': {'dir': 'build'},
        }
        (tmp_path / "site.yaml").write_text(yaml.dump(site_config))
        (tmp_path / "index.md").write_text("# Home\n\nWelcome!")
        (tmp_path / "templates").mkdir()
        (tmp_path / "templates" / "base.html").write_text(
            '<!DOCTYPE html><html><head><title>{{ page_title }}</title></head>'
            '<body>{{ content }}</body></html>'
        )
        (tmp_path / "assets" / "css").mkdir(parents=True)
        (tmp_path / "assets" / "css" / "default.css").write_text("body{}")
        return tmp_path

    def test_builds_project(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        monkeypatch.setattr(sys, 'argv', ['swb', 'build', str(project)])
        main()
        assert os.path.exists(os.path.join(str(project), "build", "index.html"))

    def test_build_nonexistent_dir_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['swb', 'build', str(tmp_path / "nope")])
        with pytest.raises(SystemExit):
            main()

    def test_build_non_swb_dir_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['swb', 'build', str(tmp_path)])
        with pytest.raises(SystemExit):
            main()


class TestCliConfig:
    @patch("swb.cli.run_config_wizard")
    def test_config_calls_wizard(self, mock_wizard, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['swb', 'config'])
        main()
        mock_wizard.assert_called_once()


class TestCliDeploy:
    @patch("swb.cli.deploy_site")
    def test_deploy_calls_deployer(self, mock_deploy, tmp_path, monkeypatch):
        (tmp_path / ".swb").write_text("# swb\n")
        (tmp_path / "site.yaml").write_text("metadata:\n  title: Test\n")
        (tmp_path / "build").mkdir()
        monkeypatch.setattr(sys, 'argv', ['swb', 'deploy', str(tmp_path)])
        main()
        mock_deploy.assert_called_once()

    def test_deploy_non_swb_dir_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['swb', 'deploy', str(tmp_path)])
        with pytest.raises(SystemExit):
            main()


class TestCliVersion:
    def test_version_flag(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, 'argv', ['swb', '--version'])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "0.1.0" in captured.out
