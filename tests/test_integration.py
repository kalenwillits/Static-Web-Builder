"""Integration tests for the full swb pipeline."""

import os
import pytest
from swb.core.project_structure import create_new_project
from swb.core.html_builder import build_site


class TestCreateThenBuild:
    def test_scaffolded_project_builds_successfully(self, tmp_path):
        """A freshly created project should build without errors."""
        project_dir = str(tmp_path / "testsite")
        create_new_project(project_dir)

        output_dir = os.path.join(project_dir, "build")
        build_site(project_dir, output_dir)

        assert os.path.exists(os.path.join(output_dir, "index.html"))
        assert os.path.exists(os.path.join(output_dir, "css", "default.css"))
        assert os.path.exists(os.path.join(output_dir, "css", "custom.css"))

    def test_scaffolded_project_index_has_site_title(self, tmp_path):
        """The built index.html should contain the site title from context."""
        project_dir = str(tmp_path / "mysite")
        create_new_project(project_dir)

        output_dir = os.path.join(project_dir, "build")
        build_site(project_dir, output_dir)

        with open(os.path.join(output_dir, "index.html")) as f:
            html = f.read()
        assert "mysite" in html

    def test_nested_page_routing(self, tmp_path):
        """Adding a nested page should produce correct file-system routing."""
        project_dir = str(tmp_path / "testsite")
        create_new_project(project_dir)

        # Add a nested page
        contact_dir = os.path.join(project_dir, "contact")
        os.makedirs(contact_dir)
        with open(os.path.join(contact_dir, "aboutus.md"), 'w') as f:
            f.write("# About Us\n\nWe are a team.")

        output_dir = os.path.join(project_dir, "build")
        build_site(project_dir, output_dir)

        # Verify routing
        assert os.path.exists(os.path.join(output_dir, "index.html"))
        about_path = os.path.join(output_dir, "contact", "aboutus.html")
        assert os.path.exists(about_path)

        with open(about_path) as f:
            html = f.read()
        assert "About Us" in html
        # Verify CSS relative path goes up one directory
        assert "../css/" in html

    def test_build_with_global_context(self, tmp_path):
        """Global context variables should appear in built pages."""
        project_dir = str(tmp_path / "testsite")
        create_new_project(project_dir)

        # Write global context
        with open(os.path.join(project_dir, "context", "global.yaml"), 'w') as f:
            f.write("company: Acme Corp\n")

        # Write a page using the variable
        with open(os.path.join(project_dir, "index.md"), 'w') as f:
            f.write("# Home\n\nCompany: {{ company }}")

        output_dir = os.path.join(project_dir, "build")
        build_site(project_dir, output_dir)

        with open(os.path.join(output_dir, "index.html")) as f:
            html = f.read()
        assert "Acme Corp" in html

    def test_build_with_per_page_context(self, tmp_path):
        """Per-page context variables should appear in the correct page."""
        project_dir = str(tmp_path / "testsite")
        create_new_project(project_dir)

        # Write per-page context for index
        with open(os.path.join(project_dir, "context", "index.yaml"), 'w') as f:
            f.write("hero_text: Welcome Home\n")

        with open(os.path.join(project_dir, "index.md"), 'w') as f:
            f.write("# Home\n\n{{ hero_text }}")

        output_dir = os.path.join(project_dir, "build")
        build_site(project_dir, output_dir)

        with open(os.path.join(output_dir, "index.html")) as f:
            html = f.read()
        assert "Welcome Home" in html
