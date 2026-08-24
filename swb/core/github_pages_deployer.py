"""GitHub Pages deployment provider.

Publishes the built site by force-pushing the contents of ``output_dir`` to a
branch (default ``gh-pages``) on a configured git remote. GitHub serves that
branch as the site.

The build output is published from a throwaway orphan history created inside
``output_dir`` so the source repository is never touched and remote history
stays shallow (each deploy replaces the branch). A ``.nojekyll`` marker is
always written so GitHub Pages serves files and directories whose names start
with an underscore instead of running them through Jekyll. A ``CNAME`` file is
written when a custom ``domain`` is configured.
"""

import os
import shutil
import subprocess

from swb.core.logger import get_logger

logger = get_logger("github_pages")

DEPLOY_TIMEOUT = 300  # 5 minutes


def check_git_cli():
    """Check if git is installed and working."""
    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def generate_pages_files(output_dir, domain=None):
    """Write GitHub Pages control files into the output directory.

    Always writes ``.nojekyll`` (without overwriting an existing one). Writes
    ``CNAME`` when a custom domain is provided.
    """
    nojekyll_path = os.path.join(output_dir, ".nojekyll")
    if not os.path.exists(nojekyll_path):
        with open(nojekyll_path, 'w') as f:
            f.write("")

    if domain:
        cname_path = os.path.join(output_dir, "CNAME")
        with open(cname_path, 'w') as f:
            f.write(domain.strip() + "\n")


def _run_git(args, cwd):
    """Run a git command in ``cwd``, raising RuntimeError on failure."""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=DEPLOY_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"git {args[0]} timed out after {DEPLOY_TIMEOUT} seconds. "
            "Check your network connection and try again."
        )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result


def deploy_github_pages(project_root, output_dir, config):
    """Deploy built site to GitHub Pages.

    Config keys:
        github_remote: Git remote URL or name to push to (required).
        github_branch: Branch to publish (default 'gh-pages').
        domain: Optional custom domain, written to CNAME.

    Raises:
        RuntimeError: If git is not installed, no remote is configured, or any
                      git step fails.
    """
    if not check_git_cli():
        raise RuntimeError(
            "git is not installed. Install git to deploy to GitHub Pages."
        )

    remote = config.get("github_remote")
    if not remote:
        raise RuntimeError(
            "GitHub remote not configured. Run 'swb config' first."
        )

    branch = config.get("github_branch", "gh-pages")
    domain = config.get("domain")

    generate_pages_files(output_dir, domain=domain)

    logger.info("Publishing to GitHub Pages branch '%s' on %s", branch, remote)
    logger.info("Source directory: %s", output_dir)

    # Build a throwaway orphan history in the output dir and force-push it.
    git_dir = os.path.join(output_dir, ".git")
    if os.path.isdir(git_dir):
        shutil.rmtree(git_dir)
    try:
        _run_git(["init", "-q"], cwd=output_dir)
        _run_git(["checkout", "-q", "--orphan", branch], cwd=output_dir)
        _run_git(["add", "-A"], cwd=output_dir)
        _run_git(
            ["-c", "user.email=swb@localhost", "-c", "user.name=swb",
             "commit", "-q", "-m", "Deploy via swb"],
            cwd=output_dir,
        )
        _run_git(
            ["push", "-q", "--force", remote, f"HEAD:{branch}"],
            cwd=output_dir,
        )
    finally:
        if os.path.isdir(git_dir):
            shutil.rmtree(git_dir)

    logger.info("Deploy complete!")
