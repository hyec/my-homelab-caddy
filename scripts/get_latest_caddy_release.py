#!/usr/bin/env python3
import json
import re
import sys
import urllib.request

API_URL = "https://api.github.com/repos/caddyserver/caddy/releases/latest"
SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def fetch_latest_release() -> str:
    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "caddy-cloudflare-docker-updater"
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    tag_name = payload.get("tag_name", "")
    if not SEMVER_RE.match(tag_name):
        raise SystemExit(f"Unexpected tag_name from GitHub API: {tag_name!r}")
    return tag_name.lstrip("v")


if __name__ == "__main__":
    sys.stdout.write(fetch_latest_release())
