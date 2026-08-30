# Docker Hub provenance/digest audit (read-only, 2026-08-29)

审计范围：本轮新增的五个 Docker Hub candidate。未重新抓取、未改核心账本；仅比较已有 candidate/readback 文件和当前 `candidates.json`。

## 结论

- 5 个新 candidate 的 `candidate_id` 与 canonical URL 在各自新增 shard 内唯一。
- 与任务基线的旧 Docker Hub 对象（`stck/pi`、`dbellkoff/pi-harness`、`hoax859/pi-coding-agent`、`jarvisquilter/pi-coding-agent`、`stefan2904/pi-coding-agent`）不重合。
- 运行时共享工作树显示主策展流程已将 4 个可计数对象写入 `candidates.json`：`michaelwadman/pi-agent`、`cactixxx/pi-agent`、`freecoderhub/sbx-pi-rust`、`sbx/pi-image`；`sbx/pi-kit` 未进入 accepted（其 `latest/images` 返回空数组，属于 OCI kit artifact）。本文件不执行或建议额外提升。
- 五个对象的窄 curator readback 均与 candidate 的 title、creator、canonical locator 一致；HTTP 细节/overview、tag、manifest readback 均为公开匿名读取。

## Provenance 与 digest 交叉核对

| 对象 | provenance 事实 | digest/manifest 核对 |
|---|---|---|
| `michaelwadman/pi-agent` | Hub overview 明确“containerised version of the Pi coding agent”，并链接 `github.com/mwadman/pi-agent`；构建层安装 `@earendil-works/pi-coding-agent` | latest digest `sha256:6c1d00c42718630b33d88ebb01abfe30d27cacbe28536c07d3eaa137fbe89e76` 在 candidate、窄 readback、完整接口 readback 三处一致；amd64，PI_VERSION=0.84.4，`/app`，`pi` entrypoint |
| `cactixxx/pi-agent` | Hub description/overview 明确 pi.dev Dockerized coding agent；overview 给出挂载、`/login` 和 provider 配置 | latest digest `sha256:814f7ca5c1e954e43ad56bd5403e6234525ae30bbf9e9130e480b804556c4fbb` 三处一致；amd64 manifest 安装 legacy `@mariozechner/pi-coding-agent`，`/workspace`，`pi` entrypoint |
| `freecoderhub/sbx-pi-rust` | Hub overview 含完整 Dockerfile/Sandbox Kit/Windows script，明确安装 `@earendil-works/pi-coding-agent` | latest amd64 digest `sha256:3a570d1d8207f6e23f2792644c6ea6acbd97b10bab014a6efc8ad6769b90f860` 三处一致；Pi 安装层和 `pi` entrypoint 可见 |
| `sbx/pi-kit` | Hub overview 明确 `@earendil-works/pi-coding-agent`、proxy-managed credential、network allowlist、PI_VERSION 可复现参数 | `tags/latest` HTTP 200 但 `images=[]`；没有 image digest 可核对，因此不把它当普通 image quota 项 |
| `sbx/pi-image` | Hub overview 明确 Pi kit base image、Node 22.22.1、fd-find、非 root agent、`CMD ["pi"]` 与 `sbx/pi-kit` 关系 | amd64 `sha256:a78f2b2fd4263664914ec709d0ff33105b6f08a1ab3237254ba51ba351c1e927`、arm64 `sha256:3b3967e945d9f427c56107a9334df4c58d94f780f4ca2156450aa1f308ec9e5b` 在 candidate 与 readback 一致；manifest 含 Pi 安装层 |

## 保留的限制

Digest 只固定本次读取的 mutable tag 状态，不是内容安全审计。manifest history 是 Hub 构建元数据，不替代源码/Dockerfile 审计；本轮没有拉取或运行任何镜像。`cactixxx/pi-agent` 的 legacy 包名与当前 Earendil 包的迁移关系需保持保守表述。`sbx/pi-kit` 是 kit artifact，不能因 overview 中的 Pi 文本自动当作 image。
