# Docker Hub `grogs/pi-agent` provenance audit — 2026-08-29

本次只读核验使用 Docker Hub 官方公开 API；没有登录、pull、run、push 或账号交互。

## 公开响应

- Repository detail：`https://hub.docker.com/v2/repositories/grogs/pi-agent/`，HTTP
  200，body SHA-256 `b4c20bc1962b8b239e95345a0ef63486e17d6aa3365d20d377394bcc2470eb15`。
  `description` 和 `source` 均为空；仓库公开、注册时间
  `2026-05-20T11:06:13.014359Z`。
- Tags listing：`https://hub.docker.com/v2/repositories/grogs/pi-agent/tags?page_size=100`，
  HTTP 200，body SHA-256
  `274bbd5397dac0ffa7cddd65ad5271d740daf05cd20b7a29f16b326215984164`。只有
  `latest` 和 `v1` 两个标签，二者指向同一 digest
  `sha256:b674bce3a7163419c11c8295d7c1ff1f5d81fc878f93d019cf72926bdf8779a9`。
- Latest manifest history：
  `https://hub.docker.com/v2/repositories/grogs/pi-agent/tags/latest/images`，HTTP
  200，body SHA-256
  `55613e4a5e4b9dd7316de699f5bf0b80f6611840c0e3f110ded93e03fb7b9801`。arm64
  manifest 的构建层确实显示 `@earendil-works/pi-coding-agent@0.79.1`、
  `/home/agent/.pi/agent/settings.json`、Pi welcome 文本、`/workspace`；OCI
  source label 指向 `https://github.com/grogs/pi-docker-sandbox-template`。

## 排除结论

关联 source URL 返回 HTTP 404，且 Docker Hub detail 没有 description/full
overview/source provenance。仅凭 manifest-history 构建元数据无法满足本轮“可回读原始内容”
和独立 provenance 门槛，因此不写入候选 shard、不计入 Docker Hub quota。该对象保留为
可复现的 metadata/provenance blocker；若以后 source URL 恢复公开且能读取完整原始说明，
再由主策展人显式复核。
