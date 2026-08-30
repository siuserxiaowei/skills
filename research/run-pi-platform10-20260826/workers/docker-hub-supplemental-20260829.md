# Docker Hub supplemental pass — 2026-08-29

路线：使用 agent-reach doctor 确认公开 Web 可用后，匿名读取 Docker Hub public search、repository detail/overview、`tags/latest` 和 `tags/latest/images`；没有登录、pull、run、push 或账号交互。

本轮新增候选（canonical URL 与现有全库去重）：

- `michaelwadman/pi-agent`：overview 明确是 Pi coding agent 容器并链接 `github.com/mwadman/pi-agent`；manifest history 显示 `@earendil-works/pi-coding-agent` 0.84.4、`/app`、`pi` entrypoint。
- `cactixxx/pi-agent`：完整公开 overview 明确 pi.dev、挂载和 provider 配置；manifest history 显示旧名 `@mariozechner/pi-coding-agent`、`/workspace`、`pi` entrypoint。旧包名关系仍需保守表述。
- `freecoderhub/sbx-pi-rust`：公开 overview 含完整 Dockerfile、Sandbox Kit 和 Windows script，明确安装 `@earendil-works/pi-coding-agent`，并记录 Rust/uv/CodeGraph 工具链。
- `sbx/pi-kit`：公开 overview 明确 `@earendil-works/pi-coding-agent`、proxy-managed 凭据、network allowlist 和 `PI_VERSION` 可复现构建；该 tag 是 OCI kit artifact，`latest/images` 为空。
- `sbx/pi-image`：公开 overview 明确 Pi kit 基础镜像、Node 22.22.1、fd-find、非 root `agent` 和 `CMD ["pi"]`；latest 提供 amd64/arm64 manifests。

证据：

- 候选行：`docker-hub-supplemental-candidates-20260829.jsonl`、`docker-hub-sbx-supplemental-candidates-20260829.jsonl`
- 独立原页/接口 readback：`docker-hub-supplemental-readbacks-20260829.jsonl`
- 可直接供显式 curator promotion 的窄字段 readback：`docker-hub-supplemental-curator-readbacks-20260829.jsonl`

未提升对象：没有 overview/source provenance 的 exact-name 镜像（如 `hambn/pi-agent`、`technigmaai/pi-agent`、`markusalbrecht/pi-agent`、`nairvarun/pi` 等）保留 metadata-only；不因 manifest 中出现 Pi 包名而自动接受。
