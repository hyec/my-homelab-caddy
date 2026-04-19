# syntax=docker/dockerfile:1.7
ARG CADDY_VERSION=2.11.2

FROM docker.io/caddy:${CADDY_VERSION}-builder AS builder
ARG CADDY_VERSION
ARG CLOUDFLARE_PLUGIN
ARG CLOUDFLARE_PLUGIN_VERSION
RUN xcaddy build v${CADDY_VERSION} \
    --with github.com/caddy-dns/cloudflare

FROM docker.io/caddy:${CADDY_VERSION}
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
