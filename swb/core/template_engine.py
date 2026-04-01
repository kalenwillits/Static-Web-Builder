"""Jinja2 template engine for markdown rendering."""

import os
from datetime import datetime
from jinja2 import Environment, BaseLoader, TemplateError
import yaml

from swb.core.logger import get_logger

logger = get_logger("template")


def load_yaml_context(yaml_path):
    """Load a YAML context file. Returns empty dict if missing or empty."""
    if not os.path.exists(yaml_path):
        return {}
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Could not load context from %s: %s", yaml_path, e)
        return {}


def _get_page_name_from_path(page_path):
    """Extract page name from path for context file lookup.
    'pages/index.md' -> 'index'
    """
    filename = os.path.basename(page_path)
    if filename.endswith('.md'):
        return filename[:-3]
    return filename


def load_context(project_root, page_path, site_config):
    """
    Build merged context for a page.

    Context merge order (later overrides earlier):
    1. Built-in context (swb_version, build_date)
    2. Global context (context/global.yaml)
    3. Per-page context (context/{page-name}.yaml)
    4. Site metadata (site.title, site.author, etc.)
    """
    from swb import __version__

    context = {
        'swb_version': __version__,
        'build_date': datetime.now().strftime('%Y-%m-%d'),
    }

    context_dir = os.path.join(project_root, 'context')

    # Global context
    global_yaml = os.path.join(context_dir, 'global.yaml')
    if os.path.exists(global_yaml):
        context.update(load_yaml_context(global_yaml))

    # Per-page context
    page_name = _get_page_name_from_path(page_path)
    page_yaml = os.path.join(context_dir, f'{page_name}.yaml')
    if os.path.exists(page_yaml):
        context.update(load_yaml_context(page_yaml))

    # Site metadata
    if 'metadata' in site_config:
        context['site'] = site_config['metadata']

    return context


def render_template(md_content, context):
    """Render markdown content through Jinja2 before markdown conversion."""
    try:
        env = Environment(loader=BaseLoader())
        template = env.from_string(md_content)
        return template.render(**context)
    except TemplateError as e:
        raise TemplateError(f"Jinja2 template error: {e}") from e


def render_page(page_path, project_root, site_config):
    """
    Load and render a page with Jinja2 context.

    Returns rendered markdown content (after Jinja2, before markdown->HTML).
    """
    with open(page_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    context = load_context(project_root, page_path, site_config)

    try:
        return render_template(md_content, context)
    except TemplateError as e:
        raise TemplateError(f"Error rendering {page_path}: {e}") from e
