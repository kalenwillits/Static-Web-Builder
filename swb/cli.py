#!/usr/bin/env python3
"""CLI router for swb commands."""

import os
import sys

from jinja2 import TemplateError

from swb import __version__
from swb.core.logger import setup_logger, get_logger
from swb.core.project_structure import create_new_project, is_swb_project
from swb.core.html_builder import build_site
from swb.core.deployer import deploy_site
from swb.core.config_manager import run_config_wizard
from swb.core.server import run_dev_server

logger = get_logger("cli")


def _cmd_create(project_path):
    """Handle project creation."""
    try:
        create_new_project(project_path)
    except (FileExistsError, ValueError, OSError) as e:
        logger.error("%s", e)
        sys.exit(1)


def _cmd_build(project_dir):
    """Handle site build."""
    if not os.path.isdir(project_dir):
        logger.error("Directory not found: %s", project_dir)
        sys.exit(1)

    if not is_swb_project(project_dir):
        logger.error("Not an swb project: %s", project_dir)
        logger.info("Run 'swb <name>' to create a new project.")
        sys.exit(1)

    import yaml
    with open(os.path.join(project_dir, 'site.yaml'), 'r') as f:
        site_config = yaml.safe_load(f) or {}

    output_dir = os.path.join(
        project_dir,
        site_config.get('output', {}).get('dir', 'build')
    )

    try:
        build_site(project_dir, output_dir)
        logger.info("Build complete: %s/", output_dir)
    except (FileNotFoundError, ValueError, TemplateError) as e:
        logger.error("Build failed: %s", e)
        sys.exit(1)


def _cmd_deploy(project_dir):
    """Handle site deployment."""
    if not os.path.isdir(project_dir):
        logger.error("Directory not found: %s", project_dir)
        sys.exit(1)

    if not is_swb_project(project_dir):
        logger.error("Not an swb project: %s", project_dir)
        sys.exit(1)

    import yaml
    with open(os.path.join(project_dir, 'site.yaml'), 'r') as f:
        site_config = yaml.safe_load(f) or {}

    output_dir = os.path.join(
        project_dir,
        site_config.get('output', {}).get('dir', 'build')
    )

    if not os.path.isdir(output_dir):
        logger.error("Build directory not found: %s", output_dir)
        logger.info("Run 'swb build' first.")
        sys.exit(1)

    try:
        deploy_site(project_dir, output_dir)
    except RuntimeError as e:
        logger.error("%s", e)
        sys.exit(1)


def _cmd_run(project_dir, port=8080):
    """Handle local dev server."""
    if not os.path.isdir(project_dir):
        logger.error("Directory not found: %s", project_dir)
        sys.exit(1)

    if not is_swb_project(project_dir):
        logger.error("Not an swb project: %s", project_dir)
        sys.exit(1)

    import yaml
    with open(os.path.join(project_dir, 'site.yaml'), 'r') as f:
        site_config = yaml.safe_load(f) or {}

    output_dir = os.path.join(
        project_dir,
        site_config.get('output', {}).get('dir', 'build')
    )

    # Auto-build if build directory is missing or empty
    if not os.path.isdir(output_dir) or not os.listdir(output_dir):
        logger.info("Build directory not found, building first...")
        try:
            build_site(project_dir, output_dir)
            logger.info("Build complete: %s/", output_dir)
        except (FileNotFoundError, ValueError, TemplateError) as e:
            logger.error("Build failed: %s", e)
            sys.exit(1)

    run_dev_server(output_dir, port)


def main():
    """Main CLI entry point.

    Routing:
        swb <name>           → create new project
        swb build <dir>      → build site
        swb run <dir>        → local dev server
        swb deploy <dir>     → deploy to Firebase
        swb config           → config wizard
        swb --version        → show version
    """
    # Handle --version early
    if '--version' in sys.argv:
        print(f"swb {__version__}")
        sys.exit(0)

    # Handle --verbose flag
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    setup_logger(verbose=verbose)

    args = [a for a in sys.argv[1:] if a not in ('--verbose', '-v')]

    if not args or args[0] in ('-h', '--help'):
        print(f"swb {__version__} - Static Web Builder")
        print()
        print("Usage:")
        print("  swb <project-name>        Create a new swb project")
        print("  swb build <project-dir>   Build the static site")
        print("  swb run <project-dir>     Serve locally (--port N)")
        print("  swb deploy <project-dir>  Deploy via configured provider")
        print("  swb config                Configure swb settings")
        print("  swb --version             Show version")
        print("  swb --verbose (-v)        Enable debug logging")
        print("  swb --help                Show this help")
        return

    command = args[0]

    if command == 'build':
        if len(args) < 2:
            print("Usage: swb build <project-dir>", file=sys.stderr)
            sys.exit(1)
        _cmd_build(args[1])

    elif command == 'run':
        if len(args) < 2:
            print("Usage: swb run <project-dir> [--port N]", file=sys.stderr)
            sys.exit(1)
        port = 8080
        if '--port' in args:
            port_idx = args.index('--port')
            if port_idx + 1 < len(args):
                try:
                    port = int(args[port_idx + 1])
                except ValueError:
                    logger.error("Invalid port number: %s", args[port_idx + 1])
                    sys.exit(1)
        _cmd_run(args[1], port=port)

    elif command == 'deploy':
        if len(args) < 2:
            print("Usage: swb deploy <project-dir>", file=sys.stderr)
            sys.exit(1)
        _cmd_deploy(args[1])

    elif command == 'config':
        run_config_wizard()

    else:
        # Treat as project creation
        _cmd_create(command)


if __name__ == "__main__":
    main()
