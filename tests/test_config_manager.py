"""Tests for configuration management."""

import os
import pytest
import yaml
from swb.core.config_manager import (
    load_config,
    save_config,
    get_config_path,
    get_project_config_path,
    load_project_config,
    load_effective_config,
)


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


class TestGetProjectConfigPath:
    def test_returns_swb_yaml_in_project_root(self, tmp_path):
        path = get_project_config_path(str(tmp_path))
        assert path == os.path.join(str(tmp_path), "swb.yaml")


class TestLoadProjectConfig:
    def test_returns_empty_dict_when_no_project_config(self, tmp_path):
        assert load_project_config(str(tmp_path)) == {}

    def test_loads_existing_project_config(self, tmp_path):
        with open(tmp_path / "swb.yaml", "w") as f:
            yaml.dump({"firebase_project_id": "project-specific"}, f)
        loaded = load_project_config(str(tmp_path))
        assert loaded == {"firebase_project_id": "project-specific"}

    def test_returns_empty_dict_on_malformed_yaml(self, tmp_path):
        with open(tmp_path / "swb.yaml", "w") as f:
            f.write("not: valid: yaml: [")
        assert load_project_config(str(tmp_path)) == {}


class TestLoadEffectiveConfig:
    def test_falls_back_to_global_when_no_project_config(self, tmp_path):
        global_dir = tmp_path / "global"
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        save_config({"provider": "github_pages", "github_remote": "origin"}, config_dir=str(global_dir))

        effective = load_effective_config(str(project_dir), config_dir=str(global_dir))

        assert effective == {"provider": "github_pages", "github_remote": "origin"}

    def test_project_config_overrides_global(self, tmp_path):
        global_dir = tmp_path / "global"
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        save_config(
            {"provider": "github_pages", "github_remote": "other-project"},
            config_dir=str(global_dir),
        )
        with open(project_dir / "swb.yaml", "w") as f:
            yaml.dump({"provider": "firebase", "firebase_project_id": "this-project"}, f)

        effective = load_effective_config(str(project_dir), config_dir=str(global_dir))

        assert effective["provider"] == "firebase"
        assert effective["firebase_project_id"] == "this-project"

    def test_project_config_only_overrides_keys_it_sets(self, tmp_path):
        global_dir = tmp_path / "global"
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        save_config({"domain": "shared-default.com"}, config_dir=str(global_dir))
        with open(project_dir / "swb.yaml", "w") as f:
            yaml.dump({"provider": "firebase", "firebase_project_id": "this-project"}, f)

        effective = load_effective_config(str(project_dir), config_dir=str(global_dir))

        # domain wasn't set at the project level, so the global value survives
        assert effective["domain"] == "shared-default.com"
        assert effective["provider"] == "firebase"

    def test_no_config_anywhere_returns_empty_dict(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        assert load_effective_config(str(project_dir), config_dir=str(tmp_path / "global")) == {}
