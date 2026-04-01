"""Tests for project scaffolding."""

import os
import pytest
from swb.core.project_structure import slugify, create_new_project, is_swb_project


class TestSlugify:
    def test_simple_name(self):
        assert slugify("My Site") == "my-site"

    def test_already_slugified(self):
        assert slugify("my-site") == "my-site"

    def test_underscores(self):
        assert slugify("my_cool_site") == "my-cool-site"

    def test_special_characters(self):
        assert slugify("My Site! @#$%") == "my-site"

    def test_multiple_spaces(self):
        assert slugify("My   Cool   Site") == "my-cool-site"

    def test_leading_trailing_hyphens(self):
        assert slugify("-my-site-") == "my-site"

    def test_single_word(self):
        assert slugify("portfolio") == "portfolio"


class TestIsSwbProject:
    def test_valid_project(self, tmp_path):
        (tmp_path / ".swb").write_text("# swb project: test\n")
        (tmp_path / "site.yaml").write_text("metadata:\n  title: test\n")
        assert is_swb_project(str(tmp_path)) is True

    def test_missing_marker(self, tmp_path):
        (tmp_path / "site.yaml").write_text("metadata:\n  title: test\n")
        assert is_swb_project(str(tmp_path)) is False

    def test_missing_site_yaml(self, tmp_path):
        (tmp_path / ".swb").write_text("# swb project: test\n")
        assert is_swb_project(str(tmp_path)) is False

    def test_empty_directory(self, tmp_path):
        assert is_swb_project(str(tmp_path)) is False

    def test_nonexistent_directory(self):
        assert is_swb_project("/nonexistent/path") is False


class TestCreateNewProject:
    def test_creates_directory(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        assert os.path.isdir(project_dir)

    def test_creates_marker_file(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        marker = os.path.join(project_dir, ".swb")
        assert os.path.exists(marker)
        content = open(marker).read()
        assert "swb project" in content
        assert "mysite" in content

    def test_creates_site_yaml(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        site_yaml = os.path.join(project_dir, "site.yaml")
        assert os.path.exists(site_yaml)
        content = open(site_yaml).read()
        assert "mysite" in content

    def test_creates_index_md(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        assert os.path.exists(os.path.join(project_dir, "index.md"))

    def test_creates_base_html_template(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        assert os.path.exists(os.path.join(project_dir, "templates", "base.html"))

    def test_creates_global_context(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        assert os.path.exists(os.path.join(project_dir, "context", "global.yaml"))

    def test_creates_custom_css(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        assert os.path.exists(os.path.join(project_dir, "assets", "css", "custom.css"))

    def test_copies_default_css(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        assert os.path.exists(os.path.join(project_dir, "assets", "css", "default.css"))

    def test_is_valid_project_after_creation(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        assert is_swb_project(project_dir) is True

    def test_rejects_existing_project(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        with pytest.raises(FileExistsError):
            create_new_project(project_dir)

    def test_empty_name_raises(self, tmp_path):
        with pytest.raises(ValueError):
            create_new_project("")

    def test_site_yaml_has_author(self, tmp_path):
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)
        content = open(os.path.join(project_dir, "site.yaml")).read()
        assert "author:" in content
