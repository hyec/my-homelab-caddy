# Caddy Cloudflare Docker 仓库设计笔记

目标：构建一个带 `github.com/caddy-dns/cloudflare` DNS challenge 插件的 Caddy Docker 镜像，并通过 GitHub Actions 定时检查上游 Caddy 版本；发现新版本后先构建并发布镜像，再更新仓库中的版本元数据。

默认策略：
- 镜像基于 `docker.io/caddy:<version>-builder` + `docker.io/caddy:<version>` 多阶段构建
- 通过 `xcaddy build --with github.com/caddy-dns/cloudflare@<plugin_version>` 编译包含固定版本 Cloudflare DNS 插件的自定义 caddy 二进制
- 通过 GitHub Actions `schedule` + `workflow_dispatch` 触发
- 通过 GitHub Releases API 获取 `caddyserver/caddy` 最新稳定版本
- 发布目标默认使用 GHCR（可改）
- 维护 `versions.json` 作为当前已发布上游版本状态与 plugin_version pin
- 若检测到新版本：先构建/推送新镜像 tag，成功后再自动提交版本更新，并同步更新 Dockerfile 中默认的 `ARG CADDY_VERSION`
- 自动提交仅修改元数据文件（`versions.json` / `Dockerfile`）时，应通过 workflow `paths-ignore` 避免再次触发发布循环

可选增强：
- 支持 tag `latest` 与精确版本 tag
- 支持 semver tag 和 major.minor tag
- 如需更实时，可后续增加外部 webhook / repository_dispatch 桥接，但默认先用定时轮询，可靠且最少外部依赖
