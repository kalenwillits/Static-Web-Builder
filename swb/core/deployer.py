"""Deployment dispatch and Firebase Hosting provider.

The deploy provider is selected via the ``provider`` key in the global swb
config (default ``firebase``). Each provider is a function with the signature
``(project_root, output_dir, config) -> None`` that raises ``RuntimeError`` on
failure.
"""

import json
import os
import subprocess

from swb.core.config_manager import load_effective_config
from swb.core.logger import get_logger

logger = get_logger("deployer")

DEPLOY_TIMEOUT = 300  # 5 minutes

DEFAULT_PROVIDER = "firebase"


def deploy_site(project_root, output_dir):
    """Deploy a built site using the configured provider.

    Reads the ``provider`` key from this project's effective config (its own
    ``swb.yaml``, falling back to the global ``~/.swb/config.yaml`` for
    anything not overridden) and dispatches to the matching deployer.
    Defaults to Firebase Hosting for backward compatibility.

    Args:
        project_root: Root directory of the swb project.
        output_dir: Directory containing built HTML files.

    Raises:
        RuntimeError: If the provider is unknown or the deploy fails.
    """
    config = load_effective_config(project_root)
    provider = config.get("provider", DEFAULT_PROVIDER)

    if provider == "firebase":
        deploy_firebase(project_root, output_dir, config)
    elif provider == "github_pages":
        # Imported lazily so the git-based provider has no import cost for
        # the default Firebase path.
        from swb.core.github_pages_deployer import deploy_github_pages
        deploy_github_pages(project_root, output_dir, config)
    else:
        raise RuntimeError(
            f"Unknown deploy provider: {provider!r}. "
            "Set 'provider' to 'firebase' or 'github_pages' (run 'swb config')."
        )


def check_firebase_cli():
    """Check if Firebase CLI is installed and working."""
    try:
        result = subprocess.run(
            ['firebase', '--version'],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def generate_firebase_json(output_dir, project_id=None):
    """Generate firebase.json and .firebaserc in the output directory.

    Does not overwrite existing files.
    """
    firebase_json_path = os.path.join(output_dir, "firebase.json")
    if not os.path.exists(firebase_json_path):
        config = {
            "hosting": {
                "public": ".",
                "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
                "headers": [
                    {
                        "source": "**/*.@(js|css)",
                        "headers": [
                            {"key": "Cache-Control", "value": "max-age=31536000"}
                        ]
                    }
                ]
            }
        }
        with open(firebase_json_path, 'w') as f:
            json.dump(config, f, indent=2)

    if project_id:
        firebaserc_path = os.path.join(output_dir, ".firebaserc")
        if not os.path.exists(firebaserc_path):
            rc = {"projects": {"default": project_id}}
            with open(firebaserc_path, 'w') as f:
                json.dump(rc, f, indent=2)


def deploy_firebase(project_root, output_dir, config):
    """Deploy built site to Firebase Hosting.

    Args:
        project_root: Root directory of the swb project
        output_dir: Directory containing built HTML files
        config: Loaded global swb config dict

    Raises:
        RuntimeError: If Firebase CLI is not installed, no project configured,
                      or the deploy command fails.
    """
    if not check_firebase_cli():
        raise RuntimeError(
            "Firebase CLI is not installed. "
            "Install it with: npm install -g firebase-tools"
        )

    project_id = config.get("firebase_project_id")
    if not project_id:
        raise RuntimeError(
            "Firebase project not configured. Run 'swb config' first."
        )

    # Generate firebase config files
    generate_firebase_json(output_dir, project_id=project_id)

    logger.info("Deploying to Firebase project: %s", project_id)
    logger.info("Source directory: %s", output_dir)

    try:
        result = subprocess.run(
            ['firebase', 'deploy', '--only', 'hosting', '--project', project_id],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=DEPLOY_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Firebase deploy timed out after {DEPLOY_TIMEOUT} seconds. "
            "Check your network connection and try again."
        )

    if result.returncode != 0:
        raise RuntimeError(f"Firebase deploy failed:\n{result.stderr}")

    logger.info(result.stdout)
    logger.info("Deploy complete!")
