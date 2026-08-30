# 中文公开平台补缺记录（2026-08-29）

本轮使用连接的普通未登录浏览器，以 360 Search（so.com）执行有界 `site:`/精确别名发现，再逐页打开 OSCHINA、今日头条和 36Kr 的公开 canonical 原页。没有使用搜索摘要作为最终证据，没有登录、互动、下载、验证码或风控绕过；`agent-reach` CLI 在本机不可直接调用，因此没有把本轮发现冒充 Google/Bing/Exa。

## 写入的 worker 候选

- OSCHINA：`china-followup-oschina-19743916-pi-dsh`、`china-followup-oschina-19743056-pi-guide`
- 今日头条：`china-followup-toutiao-7661897902360363535-pi-four-tools`、`china-followup-toutiao-7665256119266181684-pigo`、`china-followup-toutiao-7645841313899807284-pi-mono`
- 36Kr：`china-followup-36kr-3884083529658374-harness-pi`

上述条目均为 `worker_checked`，并有独立 readback JSONL；尚未声称 curator `accepted`。

## 内容簇/限制提示

- OSCHINA 19743916 与 19743056 都出自七牛云行业应用；前者与 SegmentFault 的 Pi/DSH 对照题材、后者与其他中文 Pi 指南可能有跨站内容簇，主审应逐段比对。
- Toutiao 7661897902360363535 是 Mario/Armin 访谈的个人二次解读，可能与已收录 36Kr 访谈摘要重叠。
- Toutiao 7645841313899807284 与同站另一篇 pi-mono 综述及 OSCHINA 指南主题相近，最多保留最可审计代表。
- 36Kr 3884083529658374 把 Pi 作为五个 harness 的一个 benchmark subject，而非全文唯一主题；45.4% pooled score 未独立重跑。
- `https://www.oschina.net/p/Huiyu-Pi`、OSCHINA 19724759 等既有对象未重复提交；19724759 与 SegmentFault CN-056 同标题/作者/日期内容簇已排除。

## InfoQ 有界调查结果

本轮以 InfoQ 原生搜索和 exact-site 关键词进行有界尝试，没有找到新的、可独立回读且不与现有三对象重复的 canonical 页面。现有 InfoQ 对象（`worker-cn-063`、`worker-cn-064`、`worker-cn-065`）保持不变；不从摘要或转载标题臆造新候选。若继续补齐，下一步应由主线程记录这一可复现的 no-new-result 状态，或在用户提供登录/访问协助后再按规则复查。
