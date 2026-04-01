"""Tests for Jinja2 template engine and context loading."""

import os
import pytest
from swb.core.template_engine import (
    load_context,
    render_template,
    render_page,
    load_yaml_context,
)


class TestLoadYamlContext:
    def test_loads_yaml_file(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("name: Alice\nage: 30\n")
        result = load_yaml_context(str(yaml_file))
        assert result == {'name': 'Alice', 'age': 30}

    def test_missing_file_returns_empty(self):
        result = load_yaml_context("/nonexistent/file.yaml")
        assert result == {}

    def test_empty_file_returns_empty(self, tmp_path):
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")
        result = load_yaml_context(str(yaml_file))
        assert result == {}


class TestLoadContext:
    def _make_project(self, tmp_path, global_yaml=None, page_yaml=None, site_config=None):
        """Helper to create a minimal project structure for context testing."""
        if global_yaml:
            context_dir = tmp_path / "context"
            context_dir.mkdir(exist_ok=True)
            (context_dir / "global.yaml").write_text(global_yaml)
        if page_yaml:
            context_dir = tmp_path / "context"
            context_dir.mkdir(exist_ok=True)
            (context_dir / "index.yaml").write_text(page_yaml)
        if site_config is None:
            site_config = {'metadata': {'title': 'Test Site', 'author': 'Tester'}}
        return site_config

    def test_includes_builtin_context(self, tmp_path):
        config = self._make_project(tmp_path)
        page_path = str(tmp_path / "index.md")
        ctx = load_context(str(tmp_path), page_path, config)
        assert 'swb_version' in ctx
        assert 'build_date' in ctx

    def test_includes_site_metadata(self, tmp_path):
        config = self._make_project(tmp_path)
        page_path = str(tmp_path / "index.md")
        ctx = load_context(str(tmp_path), page_path, config)
        assert ctx['site']['title'] == 'Test Site'
        assert ctx['site']['author'] == 'Tester'

    def test_loads_global_context(self, tmp_path):
        config = self._make_project(tmp_path, global_yaml="company: Acme\n")
        page_path = str(tmp_path / "index.md")
        ctx = load_context(str(tmp_path), page_path, config)
        assert ctx['company'] == 'Acme'

    def test_loads_per_page_context(self, tmp_path):
        config = self._make_project(tmp_path, page_yaml="hero_text: Welcome!\n")
        page_path = str(tmp_path / "index.md")
        ctx = load_context(str(tmp_path), page_path, config)
        assert ctx['hero_text'] == 'Welcome!'

    def test_page_context_overrides_global(self, tmp_path):
        config = self._make_project(
            tmp_path,
            global_yaml="greeting: Hello\n",
            page_yaml="greeting: Welcome\n",
        )
        page_path = str(tmp_path / "index.md")
        ctx = load_context(str(tmp_path), page_path, config)
        assert ctx['greeting'] == 'Welcome'

    def test_no_context_files_still_works(self, tmp_path):
        config = self._make_project(tmp_path)
        page_path = str(tmp_path / "index.md")
        ctx = load_context(str(tmp_path), page_path, config)
        assert 'site' in ctx
        assert 'build_date' in ctx


class TestRenderTemplate:
    def test_renders_variable(self):
        result = render_template("Hello {{ name }}!", {'name': 'World'})
        assert result == "Hello World!"

    def test_renders_conditional(self):
        template = "{% if show %}Visible{% endif %}"
        assert render_template(template, {'show': True}) == "Visible"
        assert render_template(template, {'show': False}) == ""

    def test_renders_loop(self):
        template = "{% for item in items %}{{ item }} {% endfor %}"
        result = render_template(template, {'items': ['a', 'b', 'c']})
        assert result == "a b c "

    def test_no_jinja_passthrough(self):
        result = render_template("Plain text", {})
        assert result == "Plain text"

    def test_nested_variable(self):
        result = render_template("{{ site.title }}", {'site': {'title': 'My Site'}})
        assert result == "My Site"


class TestRenderPage:
    def test_renders_page_with_context(self, tmp_path):
        (tmp_path / "index.md").write_text("# {{ site.title }}\n\nWelcome!")
        site_config = {'metadata': {'title': 'Test Site'}}
        result = render_page(str(tmp_path / "index.md"), str(tmp_path), site_config)
        assert "# Test Site" in result
        assert "Welcome!" in result

    def test_renders_page_with_global_context(self, tmp_path):
        (tmp_path / "index.md").write_text("Company: {{ company }}")
        (tmp_path / "context").mkdir()
        (tmp_path / "context" / "global.yaml").write_text("company: Acme Corp\n")
        site_config = {'metadata': {'title': 'Test'}}
        result = render_page(str(tmp_path / "index.md"), str(tmp_path), site_config)
        assert "Company: Acme Corp" in result
