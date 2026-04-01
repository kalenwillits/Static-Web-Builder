"""Firebase Hosting deployment."""

import json
import os
import subprocess
import sys

from swb.core.config_manager import load_config
from swb.core.logger import get_logger

logger = get_logger("deployer")


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

    Does not overwrite existing firebase.json.
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
        rc = {"projects": {"default": project_id}}
        with open(firebaserc_path, 'w') as f:
            json.dump(rc, f, indent=2)


def deploy_site(project_root, output_dir):
    """Deploy built site to Firebase Hosting.

    Args:
        project_root: Root directory of the swb project
        output_dir: Directory containing built HTML files

    Raises:
        RuntimeError: If Firebase CLI is not installed or no project configured
    """
    if not check_firebase_cli():
        raise RuntimeError(
            "Firebase CLI is not installed. "
            "Install it with: npm install -g firebase-tools"
        )

    config = load_config()
    project_id = config.get("firebase_project_id")
    if not project_id:
        raise RuntimeError(
            "Firebase project not configured. Run 'swb config' first."
        )

    # Generate firebase config files
    generate_firebase_json(output_dir, project_id=project_id)

    logger.info("Deploying to Firebase project: %s", project_id)
    logger.info("Source directory: %s", output_dir)

    result = subprocess.run(
        ['firebase', 'deploy', '--only', 'hosting', '--project', project_id],
        cwd=output_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Deploy failed:\n%s", result.stderr)
        sys.exit(1)

    logger.info(result.stdout)
    logger.info("Deploy complete!")
