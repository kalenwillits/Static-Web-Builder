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


def run_config_wizard(config_dir=None):
    """Interactive CLI config wizard for swb settings."""
    print("swb Configuration Wizard")
    print("=" * 40)
    print()

    existing = load_config(config_dir)

    # Firebase Project ID
    current_project = existing.get("firebase_project_id", "")
    prompt = f"Firebase Project ID [{current_project}]: " if current_project else "Firebase Project ID: "
    firebase_project_id = input(prompt).strip()
    if not firebase_project_id and current_project:
        firebase_project_id = current_project

    # Custom domain
    current_domain = existing.get("domain", "")
    prompt = f"Custom domain [{current_domain}]: " if current_domain else "Custom domain (optional): "
    domain = input(prompt).strip()
    if not domain and current_domain:
        domain = current_domain

    # Merge into existing config to preserve other keys
    if firebase_project_id:
        existing["firebase_project_id"] = firebase_project_id
    if domain:
        existing["domain"] = domain

    save_config(existing, config_dir)

    print()
    print("Configuration saved!")
    if firebase_project_id:
        print(f"  Firebase Project: {firebase_project_id}")
    if domain:
        print(f"  Domain: {domain}")
    if not firebase_project_id:
        print("  Warning: No Firebase Project ID set. Run 'swb config' again before deploying.")
