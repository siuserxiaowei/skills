# rust-processor

Rust 1.95 的离线候选处理后端。它不访问网络，也不承担采集或最终排名。

```bash
cargo run --quiet --manifest-path Cargo.toml -- probe --json
cargo run --quiet --manifest-path Cargo.toml -- process \
  --input input.json \
  --expected-input-sha256 <sha256-of-input.json> \
  --output output.json
```

输入合同是 `top50-processor/v1`，输出合同是
`top50-processor-result/v1`。输入候选可以携带额外元数据以保持前向兼容；处理器不会把
这些未知字段透传到输出。调用方应保留原始候选作为事实源，并用 `candidate_id` 关联处理结果。

生产 CLI 强制接收小写 `--expected-input-sha256`。处理器只打开输入一次，从同一字节快照
校验摘要并解析；摘要不符时在写输出前失败，避免控制面校验后同路径内容被替换。

`candidate_id` 是跨阶段稳定业务 ID。`cluster_id` 与 `review_id` 是本处理器为单次结果生成的
本地定位符；跨实现双跑比较以候选成员、代表项、证据、相似度、处置与 counts 为准，不要求
其它实现复现相同定位符。集合顺序也不承载业务语义。

处理器离线拒绝明显不安全的 URL。DNS 名称只做语法和明显本地后缀门禁，每个 DNS
候选都会输出 `requires_fetch_time_dns_validation=true`。实际 fetch 必须再次解析 DNS，
逐个拒绝非公网地址，并在重定向每一跳重复验证，不能把离线通过当成网络安全证明。

`tests/fixtures/canonical-url-v1.json` 固化与 Python ranker 对齐的 canonical identity：
HTTP/HTTPS 合一、去 `www.`、重复路径斜杠折叠、非根尾斜杠除去、fragment 清除、
query 排序和共享 tracking 参数清除。
