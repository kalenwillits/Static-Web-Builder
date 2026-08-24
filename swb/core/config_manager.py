"""Configuration management and CLI config wizard."""

import os
import sys
import yaml

from swb.core.logger import get_logger

logger = get_logger("config")


DEFAULT_CONFIG_DIR = os.path.expanduser("~/.swb")


def get_config_path(config_dir=None):
    """Get the path to the swb config file."""
    if config_dir is None:
        config_dir = DEFAULT_CONFIG_DIR
    return os.path.join(config_dir, "config.yaml")


def load_config(config_dir=None):
    """Load global swb config. Returns empty dict if no config exists."""
    config_path = get_config_path(config_dir)
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Could not load config from %s: %s", config_path, e)
        return {}


def save_config(config, config_dir=None):
    """Save global swb config."""
    if config_dir is None:
        config_dir = DEFAULT_CONFIG_DIR
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.yaml")
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
    except OSError as e:
        logger.error("Could not save config to %s: %s", config_path, e)
        raise


def get_project_config_path(project_root):
    """Get the path to a project's own swb config file (deploy overrides)."""
    return os.path.join(project_root, "swb.yaml")


def load_project_config(project_root):
    """Load a project's own swb config. Returns empty dict if none exists.

    This is separate from ``site.yaml`` (build/content config) — it holds
    deploy overrides (``provider``, ``firebase_project_id``, etc.) scoped to
    this one project, in the same shape as the global config.
    """
    config_path = get_project_config_path(project_root)
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Could not load project config from %s: %s", config_path, e)
        return {}


def load_effective_config(project_root, config_dir=None):
    """Load the config that applies to one project.

    Starts from the global config (``~/.swb/config.yaml``) and layers the
    project's own ``swb.yaml`` on top, key by key — so a project without its
    own ``swb.yaml`` (or one that only sets some keys) still falls back to
    the global config for anything it doesn't override. This is what
    deployment should use; a bare global config is shared across every swb
    project on the machine and has no idea which one you're deploying.
    """
    global_config = load_config(config_dir=config_dir)
    project_config = load_project_config(project_root)
    merged = dict(global_config)
    merged.update(project_config)
    return merged


def run_config_wizard(config_dir=None):
    """Interactive CLI config wizard for swb settings."""
    print("swb Configuration Wizard")
    print("=" * 40)
    print()

    existing = load_config(config_dir)

    # Deploy provider
    current_provider = existing.get("provider", "firebase")
    provider = input(
        f"Deploy provider (firebase/github_pages) [{current_provider}]: "
    ).strip() or current_provider
    if provider not in ("firebase", "github_pages"):
        print(f"  Warning: unknown provider '{provider}', keeping '{current_provider}'.")
        provider = current_provider
    existing["provider"] = provider

    if provider == "firebase":
        # Firebase Project ID
        current_project = existing.get("firebase_project_id", "")
        prompt = f"Firebase Project ID [{current_project}]: " if current_project else "Firebase Project ID: "
        firebase_project_id = input(prompt).strip()
        if not firebase_project_id and current_project:
            firebase_project_id = current_project
        if firebase_project_id:
            existing["firebase_project_id"] = firebase_project_id
    else:
        # GitHub Pages remote and branch
        current_remote = existing.get("github_remote", "")
        prompt = f"GitHub remote (URL or name) [{current_remote}]: " if current_remote else "GitHub remote (URL or name): "
        github_remote = input(prompt).strip()
        if not github_remote and current_remote:
            github_remote = current_remote
        if github_remote:
            existing["github_remote"] = github_remote

        current_branch = existing.get("github_branch", "gh-pages")
        github_branch = input(f"GitHub Pages branch [{current_branch}]: ").strip() or current_branch
        existing["github_branch"] = github_branch

    # Custom domain (applies to both providers)
    current_domain = existing.get("domain", "")
    prompt = f"Custom domain [{current_domain}]: " if current_domain else "Custom domain (optional): "
    domain = input(prompt).strip()
    if not domain and current_domain:
        domain = current_domain
    if domain:
        existing["domain"] = domain

    save_config(existing, config_dir)

    print()
    print("Configuration saved!")
    print(f"  Provider: {provider}")
    if provider == "firebase":
        if existing.get("firebase_project_id"):
            print(f"  Firebase Project: {existing['firebase_project_id']}")
        else:
            print("  Warning: No Firebase Project ID set. Run 'swb config' again before deploying.")
    else:
        if existing.get("github_remote"):
            print(f"  GitHub remote: {existing['github_remote']}")
            print(f"  Branch: {existing.get('github_branch', 'gh-pages')}")
        else:
            print("  Warning: No GitHub remote set. Run 'swb config' again before deploying.")
    if domain:
        print(f"  Domain: {domain}")
