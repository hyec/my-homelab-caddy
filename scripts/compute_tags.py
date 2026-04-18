#!/usr/bin/env python3
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("version", help="Caddy version, e.g. 2.11.2")
parser.add_argument("image", help="Image name without tag, e.g. ghcr.io/org/caddy-cloudflare-docker")
args = parser.parse_args()

parts = args.version.split('.')
if len(parts) != 3 or not all(part.isdigit() for part in parts):
    raise SystemExit(f"Invalid semantic version: {args.version}")

major, minor, patch = parts
result = {
    "version": args.version,
    "major_minor": f"{major}.{minor}",
    "tags": [
        f"{args.image}:{args.version}",
        f"{args.image}:{major}.{minor}",
        f"{args.image}:latest",
    ],
}
print(json.dumps(result))
