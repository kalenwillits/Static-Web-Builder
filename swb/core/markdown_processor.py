"""Markdown processing: page discovery, routing, and frontmatter parsing."""

import os
import re
import markdown

from swb.core.logger import get_logger

logger = get_logger("markdown")


def parse_frontmatter(md_content):
    """
    Extract YAML frontmatter metadata from markdown content.

    Returns:
        tuple: (original_content, metadata_dict)
    """
    md = markdown.Markdown(extensions=['meta'])
    md.convert(md_content)

    metadata = {}
    if hasattr(md, 'Meta'):
        for key, value in md.Meta.items():
            if isinstance(value, list) and len(value) > 0:
                metadata[key] = value[0]
            else:
                metadata[key] = value

    return md_content, metadata


def discover_pages(project_root, exclude_dirs=None):
    """
    Recursively discover markdown pages in a project directory.

    Args:
        project_root: Root directory to search
        exclude_dirs: List of directory names to exclude

    Returns:
        list: Page dictionaries with path, relative_path, name, metadata keys
    """
    if exclude_dirs is None:
        exclude_dirs = [
            '.git', '.venv', 'venv', 'node_modules', '__pycache__',
            'build', 'dist', 'context', 'templates', 'assets',
        ]

    if not os.path.exists(project_root):
        return []

    pages = []

    def scan_directory(path):
        if _should_exclude(path, exclude_dirs, project_root):
            return

        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            return

        for item in items:
            full_path = os.path.join(path, item)

            if _should_exclude(full_path, exclude_dirs, project_root):
                continue

            if os.path.isfile(full_path) and item.endswith('.md'):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    _, metadata = parse_frontmatter(content)
                except (OSError, UnicodeDecodeError) as e:
                    logger.warning("Could not read %s: %s", full_path, e)
                    metadata = {}

                relative_path = os.path.relpath(full_path, project_root)

                pages.append({
                    'path': full_path,
                    'relative_path': relative_path,
                    'name': item,
                    'metadata': metadata,
                })

            elif os.path.isdir(full_path):
                scan_directory(full_path)

    scan_directory(project_root)
    return sorted(pages, key=lambda p: p['relative_path'])


def _should_exclude(path, exclude_dirs, search_root):
    """Check if path should be excluded based on directory name patterns."""
    if not exclude_dirs:
        return False
    try:
        rel_path = os.path.relpath(path, search_root)
    except ValueError:
        return False
    for part in rel_path.split(os.sep):
        if part in exclude_dirs:
            return True
    return False


def get_page_route(md_path, project_root):
    """
    Map a markdown file path to its output HTML route.

    Args:
        md_path: Full path to the markdown file
        project_root: Root directory of the project

    Returns:
        str: Relative HTML path (e.g., 'contact/aboutus.html')
    """
    rel_path = os.path.relpath(md_path, project_root)
    # Replace .md extension with .html
    return re.sub(r'\.md$', '.html', rel_path)


def get_page_title(page):
    """
    Extract page title from metadata or first heading.

    Args:
        page: Page dictionary with 'path', 'metadata', 'name' keys

    Returns:
        str: Page title
    """
    if 'title' in page.get('metadata', {}):
        return page['metadata']['title']

    try:
        with open(page['path'], 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
    except OSError:
        pass

    # Fallback to filename
    name = page['name']
    if name.endswith('.md'):
        name = name[:-3]
    name = name.replace('-', ' ').replace('_', ' ')
    return name.title()
