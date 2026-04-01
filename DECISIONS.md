# SWB Decision Log

This document records key design and implementation decisions made during development.

## 2026-04-01: Project Architecture

**Decision:** Mirror ebk's project architecture with `core/` modules, `resources/`, `templates/`.

**Rationale:** ebk is a proven, well-structured reference. Following its patterns reduces design risk and provides consistency for the developer (who maintains both projects).

## 2026-04-01: Firebase Hosting for Deployment

**Decision:** Use Firebase Hosting instead of Cloud Storage + Load Balancer or Cloud Run.

**Rationale:** Firebase Hosting is $0/month for small sites, provides automatic HTTPS, global CDN, and custom domain support. Cloud Storage + LB costs ~$18/month minimum. Cloud Run requires container management for static files, which is architecturally wasteful.

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
