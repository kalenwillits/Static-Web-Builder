"""Firebase Hosting deployment."""

import json
import os
import subprocess

from swb.core.config_manager import load_config
from swb.core.logger import get_logger

logger = get_logger("deployer")

DEPLOY_TIMEOUT = 300  # 5 minutes


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


def deploy_site(project_root, output_dir):
    """Deploy built site to Firebase Hosting.

    Args:
        project_root: Root directory of the swb project
        output_dir: Directory containing built HTML files

    Raises:
        RuntimeError: If Firebase CLI is not installed, no project configured,
                      or the deploy command fails.
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
