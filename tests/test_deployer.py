"""Tests for Firebase deployment."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from swb.core.deployer import (
    check_firebase_cli,
    generate_firebase_json,
    deploy_site,
)


class TestCheckFirebaseCli:
    @patch("subprocess.run")
    def test_returns_true_when_installed(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="13.0.0\n")
        assert check_firebase_cli() is True

    @patch("subprocess.run")
    def test_returns_false_when_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        assert check_firebase_cli() is False

    @patch("subprocess.run")
    def test_returns_false_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert check_firebase_cli() is False


class TestGenerateFirebaseJson:
    def test_creates_firebase_json(self, tmp_path):
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        generate_firebase_json(output_dir)
        assert os.path.exists(os.path.join(output_dir, "firebase.json"))

    def test_firebase_json_has_hosting_config(self, tmp_path):
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        generate_firebase_json(output_dir)
        with open(os.path.join(output_dir, "firebase.json")) as f:
            config = json.load(f)
        assert "hosting" in config
        assert config["hosting"]["public"] == "."

    def test_does_not_overwrite_existing(self, tmp_path):
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        existing = '{"custom": true}'
        with open(os.path.join(output_dir, "firebase.json"), "w") as f:
            f.write(existing)
        generate_firebase_json(output_dir)
        with open(os.path.join(output_dir, "firebase.json")) as f:
            content = f.read()
        assert '"custom": true' in content

    def test_creates_firebaserc(self, tmp_path):
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        generate_firebase_json(output_dir, project_id="my-project")
        rc_path = os.path.join(output_dir, ".firebaserc")
        assert os.path.exists(rc_path)
        with open(rc_path) as f:
            rc = json.load(f)
        assert rc["projects"]["default"] == "my-project"


class TestDeploySite:
    @patch("swb.core.deployer.check_firebase_cli")
    def test_raises_when_firebase_not_installed(self, mock_check, tmp_path):
        mock_check.return_value = False
        with pytest.raises(RuntimeError, match="Firebase CLI"):
            deploy_site(str(tmp_path), str(tmp_path / "build"))

    @patch("subprocess.run")
    @patch("swb.core.deployer.check_firebase_cli")
    @patch("swb.core.deployer.load_config")
    def test_calls_firebase_deploy(self, mock_config, mock_check, mock_run, tmp_path):
        mock_check.return_value = True
        mock_config.return_value = {"firebase_project_id": "test-project"}
        mock_run.return_value = MagicMock(returncode=0, stdout="Deploy complete!")
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        deploy_site(str(tmp_path), output_dir)
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "firebase" in cmd[0]
        assert "deploy" in cmd

    @patch("subprocess.run")
    @patch("swb.core.deployer.check_firebase_cli")
    @patch("swb.core.deployer.load_config")
    def test_raises_when_no_project_configured(self, mock_config, mock_check, mock_run, tmp_path):
        mock_check.return_value = True
        mock_config.return_value = {}
        output_dir = str(tmp_path / "build")
        os.makedirs(output_dir)
        with pytest.raises(RuntimeError, match="Firebase project"):
            deploy_site(str(tmp_path), output_dir)
