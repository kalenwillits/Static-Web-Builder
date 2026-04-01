"""Tests for markdown processing: page discovery, routing, and frontmatter."""

import os
import pytest
from swb.core.markdown_processor import (
    discover_pages,
    get_page_route,
    get_page_title,
    parse_frontmatter,
)


class TestParseFrontmatter:
    def test_extracts_title(self):
        content = "title: Hello World\n\n# Content"
        _, metadata = parse_frontmatter(content)
        assert metadata['title'] == 'Hello World'

    def test_extracts_multiple_fields(self):
        content = "title: Test\nauthor: Bob\n\n# Content"
        _, metadata = parse_frontmatter(content)
        assert metadata['title'] == 'Test'
        assert metadata['author'] == 'Bob'

    def test_no_frontmatter(self):
        content = "# Just a heading\n\nSome text."
        _, metadata = parse_frontmatter(content)
        assert metadata == {}

    def test_returns_content(self):
        content = "title: Test\n\n# Hello"
        returned_content, _ = parse_frontmatter(content)
        assert "# Hello" in returned_content


class TestDiscoverPages:
    def test_finds_md_files(self, tmp_path):
        (tmp_path / "index.md").write_text("# Home")
        (tmp_path / "about.md").write_text("# About")
        pages = discover_pages(str(tmp_path))
        assert len(pages) == 2

    def test_finds_nested_files(self, tmp_path):
        (tmp_path / "index.md").write_text("# Home")
        (tmp_path / "contact").mkdir()
        (tmp_path / "contact" / "aboutus.md").write_text("# About Us")
        pages = discover_pages(str(tmp_path))
        assert len(pages) == 2

    def test_excludes_directories(self, tmp_path):
        (tmp_path / "index.md").write_text("# Home")
        (tmp_path / "build").mkdir()
        (tmp_path / "build" / "output.md").write_text("# Built")
        pages = discover_pages(str(tmp_path), exclude_dirs=["build"])
        assert len(pages) == 1

    def test_empty_directory(self, tmp_path):
        pages = discover_pages(str(tmp_path))
        assert pages == []

    def test_ignores_non_md_files(self, tmp_path):
        (tmp_path / "index.md").write_text("# Home")
        (tmp_path / "style.css").write_text("body {}")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        pages = discover_pages(str(tmp_path))
        assert len(pages) == 1

    def test_deeply_nested(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "page.md").write_text("# Deep")
        pages = discover_pages(str(tmp_path))
        assert len(pages) == 1

    def test_page_has_path_key(self, tmp_path):
        (tmp_path / "index.md").write_text("# Home")
        pages = discover_pages(str(tmp_path))
        assert 'path' in pages[0]
        assert pages[0]['path'].endswith("index.md")

    def test_page_has_relative_path(self, tmp_path):
        (tmp_path / "contact").mkdir()
        (tmp_path / "contact" / "form.md").write_text("# Form")
        pages = discover_pages(str(tmp_path))
        assert pages[0]['relative_path'] == os.path.join("contact", "form.md")


class TestGetPageRoute:
    def test_index_at_root(self, tmp_path):
        md_path = str(tmp_path / "index.md")
        route = get_page_route(md_path, str(tmp_path))
        assert route == "index.html"

    def test_nested_page(self, tmp_path):
        md_path = str(tmp_path / "contact" / "aboutus.md")
        route = get_page_route(md_path, str(tmp_path))
        assert route == os.path.join("contact", "aboutus.html")

    def test_deeply_nested_page(self, tmp_path):
        md_path = str(tmp_path / "blog" / "2024" / "post.md")
        route = get_page_route(md_path, str(tmp_path))
        assert route == os.path.join("blog", "2024", "post.html")

    def test_simple_page(self, tmp_path):
        md_path = str(tmp_path / "about.md")
        route = get_page_route(md_path, str(tmp_path))
        assert route == "about.html"


class TestGetPageTitle:
    def test_from_frontmatter(self, tmp_path):
        page_file = tmp_path / "page.md"
        page_file.write_text("title: My Page\n\n# Heading")
        page = {
            'path': str(page_file),
            'metadata': {'title': 'My Page'},
            'name': 'page.md',
        }
        assert get_page_title(page) == "My Page"

    def test_from_heading(self, tmp_path):
        page_file = tmp_path / "page.md"
        page_file.write_text("# Great Page\n\nContent here.")
        page = {
            'path': str(page_file),
            'metadata': {},
            'name': 'page.md',
        }
        assert get_page_title(page) == "Great Page"

    def test_fallback_to_filename(self, tmp_path):
        page_file = tmp_path / "my-page.md"
        page_file.write_text("No heading here, just text.")
        page = {
            'path': str(page_file),
            'metadata': {},
            'name': 'my-page.md',
        }
        assert get_page_title(page) == "My Page"
