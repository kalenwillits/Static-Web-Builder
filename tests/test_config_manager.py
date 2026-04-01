"""Tests for configuration management."""

import os
import pytest
import yaml
from swb.core.config_manager import load_config, save_config, get_config_path


class TestGetConfigPath:
    def test_returns_path_in_home_dir(self):
        path = get_config_path()
        assert ".swb" in path
        assert path.endswith("config.yaml")

    def test_respects_override(self, tmp_path):
        custom = str(tmp_path / "custom_config.yaml")
        path = get_config_path(config_dir=str(tmp_path))
        assert str(tmp_path) in path


class TestSaveConfig:
    def test_creates_config_file(self, tmp_path):
        config = {"firebase_project_id": "my-project"}
        save_config(config, config_dir=str(tmp_path))
        config_path = os.path.join(str(tmp_path), "config.yaml")
        assert os.path.exists(config_path)

    def test_saves_correct_data(self, tmp_path):
        config = {"firebase_project_id": "my-project", "domain": "example.com"}
        save_config(config, config_dir=str(tmp_path))
        config_path = os.path.join(str(tmp_path), "config.yaml")
        loaded = yaml.safe_load(open(config_path).read())
        assert loaded["firebase_project_id"] == "my-project"
        assert loaded["domain"] == "example.com"

    def test_creates_parent_directory(self, tmp_path):
        config_dir = str(tmp_path / "new_dir")
        config = {"firebase_project_id": "test"}
        save_config(config, config_dir=config_dir)
        assert os.path.exists(os.path.join(config_dir, "config.yaml"))


class TestLoadConfig:
    def test_loads_existing_config(self, tmp_path):
        config = {"firebase_project_id": "my-project", "domain": "example.com"}
        save_config(config, config_dir=str(tmp_path))
        loaded = load_config(config_dir=str(tmp_path))
        assert loaded["firebase_project_id"] == "my-project"
        assert loaded["domain"] == "example.com"

    def test_returns_empty_dict_when_no_config(self, tmp_path):
        loaded = load_config(config_dir=str(tmp_path))
        assert loaded == {}

    def test_roundtrip(self, tmp_path):
        config = {
            "firebase_project_id": "test-123",
            "domain": "test.example.com",
        }
        save_config(config, config_dir=str(tmp_path))
        loaded = load_config(config_dir=str(tmp_path))
        assert loaded == config
