# caddy-cloudflare-docker

Build and publish a custom Caddy Docker image with the Cloudflare DNS challenge plugin (`github.com/caddy-dns/cloudflare`).

The repository tracks upstream stable Caddy releases and the pinned Cloudflare plugin version in a single metadata file, `versions.json`, and uses GitHub Actions to automatically:

- check the latest stable release from `caddyserver/caddy`
- build and push the image for the new Caddy release first
- only then commit tracked metadata back to `main`
- build and push image tags to **GHCR** by default

## What gets published

For Caddy `2.11.2`, the workflow publishes:

- `ghcr.io/<owner>/caddy-cloudflare-docker:2.11.2`
- `ghcr.io/<owner>/caddy-cloudflare-docker:2.11`
- `ghcr.io/<owner>/caddy-cloudflare-docker:latest`

## Repository layout

- `Dockerfile` - multi-stage build using `xcaddy` with an explicitly pinned Cloudflare plugin version
- `versions.json` - tracked upstream Caddy version and plugin_version metadata that must stay synchronized with Dockerfile defaults
- `.github/workflows/release.yml` - scheduled/manual/push automation for update + publish, with metadata committed only after a successful publish
- `.github/workflows/validate.yml` - lightweight repository validation workflow
- `scripts/get_latest_caddy_release.py` - fetch latest stable Caddy version from GitHub API
- `scripts/compute_tags.py` - generate exact / major.minor / latest tags
- `scripts/validate_repo.py` - local self-test without requiring Docker

## How it works

1. `release.yml` runs on `schedule`, `workflow_dispatch`, and `push` to `main`.
2. It reads the tracked version from `versions.json`.
3. It fetches the latest stable upstream version from `https://api.github.com/repos/caddyserver/caddy/releases/latest`.
4. When a build is needed, it builds the Docker image with `CADDY_VERSION=<version>` and a pinned `plugin_version` from `versions.json`, then pushes versioned tags.
5. If the upstream Caddy version was newer and the publish succeeded, it updates both `versions.json` and the Dockerfile default `ARG CADDY_VERSION`, commits the metadata change, and pushes it back to the repository.
6. If nothing changed, the scheduled/manual run exits cleanly as a no-op unless `workflow_dispatch` is forced.

The post-publish metadata commit is ignored by the release workflow `push.paths-ignore` rules for `versions.json` and `Dockerfile`, so the bookkeeping commit does not trigger a second build.

## GitHub setup

### Required repository settings

1. Enable GitHub Actions for the repository.
2. Ensure the workflow token can write packages and repository contents.
3. If your organization restricts package publishing, allow this repository to publish to GHCR.

`release.yml` already declares:

- `contents: write`
- `packages: write`

It uses the built-in `GITHUB_TOKEN` for GHCR login and for committing synchronized `versions.json` + `Dockerfile` metadata updates after a successful publish.

### Secrets

No secret is required to build the image itself when publishing to GHCR with `GITHUB_TOKEN`.

At runtime, if you use DNS challenge with Cloudflare, provide a **runtime** secret such as `CLOUDFLARE_API_TOKEN`. This token is **not** needed during image build.

Example runtime environment:

```yaml
environment:
  CLOUDFLARE_API_TOKEN: your-token
```

### Changing the target registry

The default registry is GHCR.

To publish elsewhere, update the workflow environment in `.github/workflows/release.yml`:

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.event.repository.name }}
```

Examples:

- Docker Hub: set `REGISTRY: docker.io` and adjust login credentials accordingly.
- Private registry: set `REGISTRY: registry.example.com` and replace the login step with the required credentials.

If you change registries away from GHCR, you will likely need repository secrets for registry authentication.

## Usage

Example pull:

```bash
docker pull ghcr.io/<owner>/caddy-cloudflare-docker:latest
```

Example `docker run`:

```bash
docker run --rm \
  -e CLOUDFLARE_API_TOKEN=your-token \
  -p 80:80 -p 443:443 \
  -v "$PWD/Caddyfile:/etc/caddy/Caddyfile:ro" \
  -v caddy_data:/data \
  -v caddy_config:/config \
  ghcr.io/<owner>/caddy-cloudflare-docker:latest
```

Example Caddyfile snippet for DNS challenge:

```caddyfile
example.com {
  tls {
    dns cloudflare {env.CLOUDFLARE_API_TOKEN}
  }

  respond "hello from custom caddy"
}
```

## Manual workflow usage

You can trigger `workflow_dispatch` from GitHub Actions.

Optional input:

- `force_build=true` - rebuild and republish using the tracked version even if `versions.json` already matches upstream

`versions.json` also carries the pinned Cloudflare `plugin_version`, which the Dockerfile consumes via build args so plugin upgrades remain explicit and reviewable.

## Local validation / self-test

No Docker daemon is required for the local self-test.

Run:

```bash
python3 scripts/validate_repo.py
python3 scripts/compute_tags.py 2.11.2 ghcr.io/example/caddy-cloudflare-docker
```

The validation script checks the expected repository structure, pinned plugin metadata, and key workflow semantics.

## Notes

- `versions.json` remains the reviewable metadata record, and the workflow keeps the Dockerfile default `ARG CADDY_VERSION` synchronized with it after each successful upstream bump.
- Release workflow `push.paths-ignore` excludes metadata-only bot commits (`versions.json` and `Dockerfile`) so automated bookkeeping does not recurse into another publish run.
- The Dockerfile accepts `--build-arg CADDY_VERSION=<version>` and uses a multi-stage build with `xcaddy` plus a pinned `github.com/caddy-dns/cloudflare@<plugin_version>`.
- The workflow currently follows the latest stable GitHub release from `caddyserver/caddy`.

## License

MIT
