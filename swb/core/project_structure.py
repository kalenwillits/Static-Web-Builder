"""Project scaffolding for new swb sites."""

import os
import re
import shutil
from pathlib import Path


def slugify(name):
    """Convert 'My Site Name' to 'my-site-name'."""
    slug = name.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def is_swb_project(path):
    """Check if a directory is an swb project."""
    if not os.path.isdir(path):
        return False
    return os.path.exists(os.path.join(path, '.swb')) and os.path.exists(os.path.join(path, 'site.yaml'))


def get_author_name():
    """Try to get author name from git config, fallback to 'Author Name'."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "Author Name"


def get_template_path():
    """Get the path to the templates directory."""
    return Path(__file__).parent.parent / 'templates'


def get_resources_path():
    """Get the path to the resources directory."""
    return Path(__file__).parent.parent / 'resources'


def create_new_project(project_path):
    """
    Create a new swb project at the given path.

    Args:
        project_path: Path where the project should be created

    Raises:
        ValueError: If project_path is empty
        FileExistsError: If directory is already an swb project
    """
    if not project_path or not project_path.strip():
        raise ValueError("Project path cannot be empty")

    project_path = project_path.strip()
    path = Path(project_path).expanduser().resolve()
    project_name = path.name

    # Create directory if it doesn't exist
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # Check if already an swb project
    if (path / ".swb").exists():
        raise FileExistsError("Directory is already an swb project")

    template_dir = get_template_path()
    resources_dir = get_resources_path()
    author_name = get_author_name()

    # Template variable substitution
    template_vars = {
        '{site_title}': project_name,
        '{author_name}': author_name,
    }

    # Copy and populate site.yaml
    site_yaml_content = (template_dir / "site.yaml").read_text()
    for var, value in template_vars.items():
        site_yaml_content = site_yaml_content.replace(var, value)
    (path / "site.yaml").write_text(site_yaml_content)

    # Copy index.md
    shutil.copy2(template_dir / "index.md", path / "index.md")

    # Create templates/ directory and copy base.html
    (path / "templates").mkdir(exist_ok=True)
    shutil.copy2(template_dir / "base.html", path / "templates" / "base.html")

    # Create context/ directory and copy global.yaml
    (path / "context").mkdir(exist_ok=True)
    shutil.copy2(template_dir / "global.yaml", path / "context" / "global.yaml")

    # Create assets/css/ directory with default and custom CSS
    css_dir = path / "assets" / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(resources_dir / "default.css", css_dir / "default.css")
    (css_dir / "custom.css").write_text("/* Custom CSS for your site */\n")

    # Create .swb marker last — ensures partial failures don't leave
    # a marker file without a complete project
    (path / ".swb").write_text(f"# swb project: {project_name}\n")

    print(f"Created new swb project: {project_name}")
    print(f"  Directory: {path}")
    print()
    print("Next steps:")
    print(f"  1. cd {path.name}")
    print("  2. Edit site.yaml with your site metadata")
    print("  3. Edit index.md to add your homepage content")
    print("  4. Run 'swb build .' to build your site")
