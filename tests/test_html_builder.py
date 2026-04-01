"""Tests for the HTML build pipeline."""

import os
import pytest
import yaml
from swb.core.html_builder import build_site, convert_markdown_to_html


def _make_project(tmp_path, pages=None, site_config=None, base_html=None, global_ctx=None):
    """Helper to create a minimal swb project for testing."""
    # Marker
    (tmp_path / ".swb").write_text("# swb project: test\n")

    # site.yaml
    if site_config is None:
        site_config = {
            'metadata': {
                'title': 'Test Site',
                'author': 'Tester',
                'description': 'A test site',
                'language': 'en-US',
            },
            'default_css': ['default.css'],
            'discovery': {
                'root': '.',
                'exclude': ['.git', 'build', 'context', 'templates', 'assets'],
                'content_extensions': ['.md'],
                'image_extensions': ['.jpg', '.png', '.gif', '.svg'],
                'css_extensions': ['.css'],
            },
            'output': {'dir': 'build'},
        }
    (tmp_path / "site.yaml").write_text(yaml.dump(site_config))

    # templates/base.html
    (tmp_path / "templates").mkdir(exist_ok=True)
    if base_html is None:
        base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% if page_title %}{{ page_title }} - {% endif %}{{ site.title }}</title>
    {% for css in css_files %}
    <link rel="stylesheet" href="{{ site_root }}css/{{ css }}">
    {% endfor %}
</head>
<body>
    <main>{{ content }}</main>
</body>
</html>"""
    (tmp_path / "templates" / "base.html").write_text(base_html)

    # context/
    (tmp_path / "context").mkdir(exist_ok=True)
    if global_ctx:
        (tmp_path / "context" / "global.yaml").write_text(yaml.dump(global_ctx))

    # assets/css/
    css_dir = tmp_path / "assets" / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    (css_dir / "default.css").write_text("body { margin: 0; }\n")

    # Pages
    if pages is None:
        pages = {"index.md": "# Home\n\nWelcome to the site."}
    for path, content in pages.items():
        page_file = tmp_path / path
        page_file.parent.mkdir(parents=True, exist_ok=True)
        page_file.write_text(content)

    return tmp_path


class TestConvertMarkdownToHtml:
    def test_heading(self):
        html = convert_markdown_to_html("# Hello")
        assert "<h1>Hello</h1>" in html

    def test_paragraph(self):
        html = convert_markdown_to_html("Some text here.")
        assert "<p>Some text here.</p>" in html

    def test_code_block(self):
        html = convert_markdown_to_html("```python\nprint('hi')\n```")
        assert "print" in html

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = convert_markdown_to_html(md)
        assert "<table>" in html

    def test_inline_html(self):
        html = convert_markdown_to_html('<div class="custom">Content</div>')
        assert '<div class="custom">' in html


class TestBuildSite:
    def test_creates_output_directory(self, tmp_path):
        project = _make_project(tmp_path)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        assert os.path.isdir(output_dir)

    def test_builds_index_html(self, tmp_path):
        project = _make_project(tmp_path)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        assert os.path.exists(os.path.join(output_dir, "index.html"))

    def test_index_html_contains_content(self, tmp_path):
        project = _make_project(tmp_path)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        html = open(os.path.join(output_dir, "index.html")).read()
        assert "Welcome to the site" in html

    def test_wraps_in_base_template(self, tmp_path):
        project = _make_project(tmp_path)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        html = open(os.path.join(output_dir, "index.html")).read()
        assert "<!DOCTYPE html>" in html
        assert "<title>" in html
        assert "Test Site" in html

    def test_builds_nested_page(self, tmp_path):
        pages = {
            "index.md": "# Home",
            "contact/aboutus.md": "# About Us\n\nWe are great.",
        }
        project = _make_project(tmp_path, pages=pages)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        about_path = os.path.join(output_dir, "contact", "aboutus.html")
        assert os.path.exists(about_path)
        html = open(about_path).read()
        assert "About Us" in html

    def test_copies_css_files(self, tmp_path):
        project = _make_project(tmp_path)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        css_path = os.path.join(output_dir, "css", "default.css")
        assert os.path.exists(css_path)

    def test_css_linked_in_html(self, tmp_path):
        project = _make_project(tmp_path)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        html = open(os.path.join(output_dir, "index.html")).read()
        assert "css/default.css" in html

    def test_jinja_variables_rendered(self, tmp_path):
        pages = {"index.md": "# {{ site.title }}\n\nBy {{ site.author }}"}
        project = _make_project(tmp_path, pages=pages)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        html = open(os.path.join(output_dir, "index.html")).read()
        assert "Test Site" in html
        assert "Tester" in html

    def test_nested_page_css_relative_path(self, tmp_path):
        pages = {
            "index.md": "# Home",
            "blog/post.md": "# Post",
        }
        project = _make_project(tmp_path, pages=pages)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        html = open(os.path.join(output_dir, "blog", "post.html")).read()
        assert "../css/default.css" in html

    def test_no_pages_raises(self, tmp_path):
        project = _make_project(tmp_path, pages={})
        # Remove the index.md that _make_project creates by default
        # Actually pages={} means no pages at all
        output_dir = str(tmp_path / "build")
        with pytest.raises(ValueError, match="No markdown"):
            build_site(str(project), output_dir)

    def test_deeply_nested_routing(self, tmp_path):
        pages = {
            "index.md": "# Home",
            "docs/api/reference.md": "# API Reference",
        }
        project = _make_project(tmp_path, pages=pages)
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        ref_path = os.path.join(output_dir, "docs", "api", "reference.html")
        assert os.path.exists(ref_path)

    def test_global_context_in_pages(self, tmp_path):
        pages = {"index.md": "# Home\n\nCompany: {{ company }}"}
        project = _make_project(tmp_path, pages=pages, global_ctx={"company": "Acme"})
        output_dir = str(tmp_path / "build")
        build_site(str(project), output_dir)
        html = open(os.path.join(output_dir, "index.html")).read()
        assert "Company: Acme" in html
