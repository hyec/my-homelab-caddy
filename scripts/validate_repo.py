#!/usr/bin/env python3
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
errors = []

versions = json.loads((ROOT / "versions.json").read_text())
version = versions.get("caddy_version")
plugin = versions.get("plugin")
plugin_version = versions.get("plugin_version")
if not re.fullmatch(r"\d+\.\d+\.\d+", version or ""):
    errors.append(f"versions.json caddy_version is invalid: {version!r}")
if plugin != "github.com/caddy-dns/cloudflare":
    errors.append(f"versions.json plugin is invalid: {plugin!r}")
if not re.fullmatch(r"v\d+\.\d+\.\d+", plugin_version or ""):
    errors.append(f"versions.json plugin_version is invalid: {plugin_version!r}")

dockerfile = (ROOT / "Dockerfile").read_text()
match = re.search(r"^ARG CADDY_VERSION=(\d+\.\d+\.\d+)$", dockerfile, re.MULTILINE)
if not match:
    errors.append("Dockerfile does not define default CADDY_VERSION arg")
else:
    dockerfile_default_version = match.group(1)
    if dockerfile_default_version != version:
        errors.append(
            f"Dockerfile default version {dockerfile_default_version!r} does not match versions.json {version!r}"
        )
plugin_match = re.search(r"^ARG CLOUDFLARE_PLUGIN=(.+)$", dockerfile, re.MULTILINE)
if not plugin_match:
    errors.append("Dockerfile does not define default CLOUDFLARE_PLUGIN arg")
elif plugin_match.group(1) != plugin:
    errors.append(
        f"Dockerfile default Cloudflare plugin {plugin_match.group(1)!r} does not match versions.json {plugin!r}"
    )
plugin_version_match = re.search(r"^ARG CLOUDFLARE_PLUGIN_VERSION=(v\d+\.\d+\.\d+)$", dockerfile, re.MULTILINE)
if not plugin_version_match:
    errors.append("Dockerfile does not define default CLOUDFLARE_PLUGIN_VERSION arg")
elif plugin_version_match.group(1) != plugin_version:
    errors.append(
        "Dockerfile default Cloudflare plugin version "
        f"{plugin_version_match.group(1)!r} does not match versions.json {plugin_version!r}"
    )
if "FROM docker.io/caddy:${CADDY_VERSION}-builder AS builder" not in dockerfile:
    errors.append("Dockerfile missing builder stage based on docker.io/caddy:${CADDY_VERSION}-builder")
if "--with ${CLOUDFLARE_PLUGIN}@${CLOUDFLARE_PLUGIN_VERSION}" not in dockerfile:
    errors.append("Dockerfile missing pinned Cloudflare plugin build flag")
if "FROM docker.io/caddy:${CADDY_VERSION}" not in dockerfile:
    errors.append("Dockerfile missing runtime stage based on docker.io/caddy:${CADDY_VERSION}")

workflow = (ROOT / ".github/workflows/release.yml").read_text()
for snippet in [
    "schedule:",
    "workflow_dispatch:",
    "push:",
    "packages: write",
    "contents: write",
    "- Dockerfile",
    "versions.json",
    "ghcr.io",
    "docker/build-push-action",
    "scripts/get_latest_caddy_release.py",
    "plugin_version",
    "Update tracked metadata after successful publish",
    "Commit updated version metadata after successful publish",
    "git add Dockerfile versions.json",
]:
    if snippet not in workflow:
        errors.append(f"release workflow missing expected snippet: {snippet}")

if "ARG CADDY_VERSION=" not in workflow:
    errors.append("release workflow does not appear to synchronize Dockerfile CADDY_VERSION")

release_script = (ROOT / "scripts/get_latest_caddy_release.py").read_text()
if "https://api.github.com/repos/caddyserver/caddy/releases/latest" not in release_script:
    errors.append("get_latest_caddy_release.py missing expected GitHub API URL")

validate_workflow = (ROOT / ".github/workflows/validate.yml").read_text()
for snippet in ["push:", "workflow_dispatch:", "scripts/validate_repo.py"]:
    if snippet not in validate_workflow:
        errors.append(f"validate workflow missing expected snippet: {snippet}")

readme = (ROOT / "README.md").read_text()
for snippet in [
    "GHCR",
    "CLOUDFLARE_API_TOKEN",
    "versions.json",
    "plugin_version",
    "workflow_dispatch",
    "python3 scripts/validate_repo.py",
]:
    if snippet not in readme:
        errors.append(f"README missing expected snippet: {snippet}")

if errors:
    print("VALIDATION FAILED", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print("Validation passed.")
