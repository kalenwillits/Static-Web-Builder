# SWB Decision Log

This document records key design and implementation decisions made during development.

## 2026-04-01: Project Architecture

**Decision:** Mirror ebk's project architecture with `core/` modules, `resources/`, `templates/`.

**Rationale:** ebk is a proven, well-structured reference. Following its patterns reduces design risk and provides consistency for the developer (who maintains both projects).

## 2026-04-01: Firebase Hosting for Deployment

**Decision:** Use Firebase Hosting instead of Cloud Storage + Load Balancer or Cloud Run.

**Rationale:** Firebase Hosting is $0/month for small sites, provides automatic HTTPS, global CDN, and custom domain support. Cloud Storage + LB costs ~$18/month minimum. Cloud Run requires container management for static files, which is architecturally wasteful.

## 2026-06-28: Pluggable Deploy Providers (Firebase + GitHub Pages)

**Decision:** Make the deploy step pluggable via a `provider` config key (`firebase` | `github_pages`), defaulting to Firebase. `deployer.deploy_site` is now a dispatcher; Firebase logic moved to `deploy_firebase`, and a new `github_pages_deployer` module publishes via git.

**Rationale:** GitHub Pages offers ~10× the free monthly bandwidth (100 GB soft limit vs Firebase Spark's 10 GB enforced limit) and degrades gracefully instead of disabling the site, and it removes the Node.js/`firebase-tools` dependency for users already on GitHub. It is added as an *alternative* rather than a replacement because it couples hosting to a GitHub repo (one site per repo) and lacks Firebase's atomic deploy/instant rollback. Keeping both behind a provider key preserves the decoupled-deploy property for users who want it.

**Implementation notes:**
1. GitHub Pages deploy force-pushes the built dir to a branch (default `gh-pages`) from a throwaway orphan history created inside the output dir, so the source repo is untouched and remote history stays shallow.
2. A `.nojekyll` marker is always written so GitHub Pages serves swb's file-system routing (including `_`-prefixed paths) verbatim instead of running Jekyll.
3. A `CNAME` file is written when a custom `domain` is configured.
4. Backward compatible: existing configs without a `provider` key continue to deploy to Firebase unchanged.

## 2026-04-01: File System Routing

**Decision:** Map file system paths directly to URL routes (`contact/aboutus.md` → `/contact/aboutus`).

**Rationale:** User requirement. Intuitive mental model — the directory structure IS the site structure. No routing configuration needed.

## 2026-04-01: Jinja2 Base HTML Template

**Decision:** Wrap all pages in a customizable `base.html` Jinja2 template.

**Rationale:** Allows users to customize page structure (nav, footer, head tags) without modifying the build tool. Template is copied into each new project and can be edited freely.

## 2026-04-01: Jinja2 Before Markdown

**Decision:** Apply Jinja2 template rendering before markdown conversion (same as ebk).

**Rationale:** Enables Jinja2 logic (conditionals, loops, variables) within markdown source files. The rendered Jinja2 output is still valid markdown that then gets converted to HTML.

## 2026-04-01: Pre-commit Git Hook for Tests

**Decision:** Install a pre-commit hook that runs pytest and blocks commits with failing tests.

**Rationale:** User requirement for TDD enforcement. Prevents broken code from being committed.

## 2026-04-01: Structured Logging Over Print Statements

**Decision:** Use Python's `logging` module with a centralized `swb.core.logger` module instead of bare `print()` for diagnostics.

**Rationale:** Bare `print()` statements mixed with `except Exception: return {}` make it impossible for users to diagnose build/deploy failures. The logging system provides: (1) severity levels (DEBUG, INFO, WARNING, ERROR), (2) module-level loggers for targeted debugging, (3) a `--verbose` flag for detailed output, and (4) consistent formatting to stderr.

## 2026-04-01: Specific Exception Types

**Decision:** Replace bare `except Exception` with specific types (e.g., `yaml.YAMLError`, `OSError`, `UnicodeDecodeError`).

**Rationale:** Catching `Exception` broadly silences bugs. Specific types ensure only expected failures are handled gracefully while unexpected errors propagate with full tracebacks for debugging.

## 2026-04-01: Manual CLI Routing Over argparse Subparsers

**Decision:** Use manual `sys.argv` inspection instead of argparse subparsers for CLI routing.

**Rationale:** argparse subparsers reject unknown positional args (like `swb mysite`), making it impossible to have both subcommands (`build`, `deploy`, `config`) and a bare positional arg for project creation. Manual routing is simpler and more flexible for this use case.

## 2026-04-01: Peer Review Fixes

**Decision:** Address critical findings from agent-based peer review.

**Changes made:**
1. Config wizard now merges into existing config (prevents data loss of unknown keys)
2. Config wizard warns on empty Firebase project ID instead of silently saving
3. `deploy_site` raises `RuntimeError` instead of `sys.exit(1)` — keeps it testable/composable
4. `deploy_site` now has 5-minute timeout on `firebase deploy` subprocess
5. `.swb` marker file created last in scaffolding — prevents unrecoverable partial state
6. CLI catches `TemplateError` from build pipeline for clean error messages
7. CLI guards against `None` from empty `site.yaml` files
8. `.firebaserc` is no longer overwritten if it already exists
9. `save_config` now has error handling for write failures
10. Added 5 integration tests covering create-then-build pipeline
