"""HTML output builder."""

import os
import shutil
import markdown as md_lib
import yaml
from jinja2 import Environment, FileSystemLoader, BaseLoader

from swb.core.markdown_processor import discover_pages, get_page_route, get_page_title
from swb.core.template_engine import render_page


MARKDOWN_EXTENSIONS = [
    'meta',
    'codehilite',
    'tables',
    'fenced_code',
    'footnotes',
    'md_in_html',
]


def convert_markdown_to_html(md_content):
    """Convert markdown string to HTML body."""
    md = md_lib.Markdown(extensions=MARKDOWN_EXTENSIONS)
    return md.convert(md_content)


def _compute_site_root(page_route):
    """Compute relative path back to site root for a given page route.
    'index.html' -> ''
    'blog/post.html' -> '../'
    'docs/api/ref.html' -> '../../'
    """
    depth = page_route.count(os.sep)
    if depth == 0:
        return ''
    return '../' * depth


def _discover_css_files(project_root, discovery_config):
    """Find all CSS files in assets directory."""
    css_files = {}
    assets_css = os.path.join(project_root, 'assets', 'css')
    if os.path.isdir(assets_css):
        for f in sorted(os.listdir(assets_css)):
            if f.endswith('.css'):
                css_files[f] = os.path.join(assets_css, f)
    return css_files


def _discover_image_files(project_root, discovery_config):
    """Find all image files in assets directory."""
    image_files = {}
    image_extensions = discovery_config.get('image_extensions', ['.jpg', '.jpeg', '.png', '.gif', '.svg'])
    assets_dir = os.path.join(project_root, 'assets')
    if not os.path.isdir(assets_dir):
        return image_files

    for root, dirs, files in os.walk(assets_dir):
        for f in sorted(files):
            if any(f.lower().endswith(ext) for ext in image_extensions):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, assets_dir)
                image_files[rel_path] = full_path
    return image_files


def build_site(project_root, output_dir):
    """
    Build static HTML site from an swb project.

    Args:
        project_root: Root directory of the swb project
        output_dir: Directory to write built HTML into
    """
    # Load site config
    site_yaml_path = os.path.join(project_root, 'site.yaml')
    if not os.path.exists(site_yaml_path):
        raise FileNotFoundError("site.yaml not found")

    with open(site_yaml_path, 'r') as f:
        site_config = yaml.safe_load(f)

    discovery_config = site_config.get('discovery', {})
    exclude_dirs = discovery_config.get('exclude', [
        '.git', '.venv', 'venv', 'node_modules', '__pycache__',
        'build', 'dist', 'context', 'templates', 'assets',
    ])

    # Discover pages
    pages = discover_pages(project_root, exclude_dirs)
    if not pages:
        raise ValueError(f"No markdown files found in {project_root}")

    # Discover CSS
    css_files_map = _discover_css_files(project_root, discovery_config)
    css_filenames = list(css_files_map.keys())

    # Discover images
    image_files_map = _discover_image_files(project_root, discovery_config)

    # Load base template
    template_dir = os.path.join(project_root, 'templates')
    base_template_path = os.path.join(template_dir, 'base.html')
    if os.path.exists(base_template_path):
        with open(base_template_path, 'r') as f:
            base_template_str = f.read()
    else:
        # Fallback: minimal HTML wrapper
        base_template_str = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{{ page_title }}</title></head>
<body>{{ content }}</body>
</html>"""

    # Prepare output directory
    os.makedirs(output_dir, exist_ok=True)
    css_out = os.path.join(output_dir, 'css')
    os.makedirs(css_out, exist_ok=True)

    # Build each page
    env = Environment(loader=BaseLoader())

    for page in pages:
        route = get_page_route(page['path'], project_root)
        title = get_page_title(page)
        site_root = _compute_site_root(route)

        # Render markdown through Jinja2 context
        rendered_md = render_page(page['path'], project_root, site_config)

        # Convert markdown to HTML body
        html_body = convert_markdown_to_html(rendered_md)

        # Wrap in base template
        template = env.from_string(base_template_str)
        full_html = template.render(
            content=html_body,
            page_title=title,
            site=site_config.get('metadata', {}),
            css_files=css_filenames,
            site_root=site_root,
        )

        # Write output file
        output_path = os.path.join(output_dir, route)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

    # Copy CSS files
    for css_name, css_path in css_files_map.items():
        shutil.copy2(css_path, os.path.join(css_out, css_name))

    # Copy image files
    if image_files_map:
        assets_out = os.path.join(output_dir, 'assets')
        for rel_path, src_path in image_files_map.items():
            dest = os.path.join(assets_out, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src_path, dest)
