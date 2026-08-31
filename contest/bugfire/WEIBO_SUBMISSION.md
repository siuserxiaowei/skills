# Weibo submission copy

## Main post

#微博VibeLab# #VibeVision#

【BUGFIRE｜补丁兽】

我把“让 AI 帮我设计一个角色”拆成了一条可验收的证据链：原创角色 brief → AI 结构化草案 → 人工明确否决一个选择 → deterministic validator → build / preview → 可选 install / verify / restore。

真实 Demo 输入是原创像素电路蝾螈 Patchling Zero。AI 草案把告警橙定成主色；操作员否决它，因为待机界面也会一直像故障态，改成电路青 + 通过绿，橙色只留给警报。AI 草案不能直接生成可安装包；review 和 materialize 都必须重新核对同一份人工 brief 的摘要与 rights，之后仍要通过图片真实性、路径、大小和字段校验。

无 Key 时演示使用本项目 Codex agent 实际产出并经 SHA-256 锁定的 fixture，明确不冒充实时 API。代码也提供真实 OpenAI-compatible live 路径，并用 loopback mock 测试证明会发请求、不会把 Key 写进产物。

仓库：https://github.com/siuserxiaowei/Codex-Bugfire-Skin
复现：`./contest/bugfire/run-demo.sh`
证据：`contest/bugfire/README.md`

人工负责方向与权利确认；AI 负责结构化提案；deterministic validator 负责判断能不能构建。旧 75 秒 V2 只证明既有桌宠工程，新导演流程使用单独录屏，不混作 AI 证据。

## Short version

#微博VibeLab# #VibeVision#

BUGFIRE｜补丁兽：原创 brief → AI 角色导演草案 → 人工否决/替换一项选择 → deterministic validator → build / preview / restore。

Demo 中 AI 选了告警橙主色，操作员改成电路青 + 通过绿；AI 草案不能直接 materialize，review / materialize 会重复绑定人工 brief，不能跳过 rights、图片、路径与字段校验。离线 AI fixture 有 SHA-256 完整性摘要且不冒充实时调用；live API 路径有真实 loopback HTTP 测试，Key 不落盘。

https://github.com/siuserxiaowei/Codex-Bugfire-Skin

## Required attachments

1. New 60–75 second Character Director recording made from [`RECORDING_SCRIPT.md`](RECORDING_SCRIPT.md).
2. `boards/01-ai-draft.png`: AI draft with truthful recorded-fixture label.
3. `boards/02-human-rejection.png`: `#ff7a1a → #35d9d1` rejection/replacement proof.
4. `boards/03-pack-preview.png`: real offline preview captured from generated `preview.html`.
5. Optional old real-Codex screenshot/video only as a separately labelled engineering appendix.

Do not say “实时 AI” unless `draft-live` was actually run against a named endpoint for that recording. Do not say “人工否决” unless the recording operator explicitly confirmed the choice.
