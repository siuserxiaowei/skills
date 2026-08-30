# 50-Agent 原创性与归属复核

审计日期：2026-08-30

固定基线：`aadbe9cc380cbbd9301b750bf40b404a63f86946`

首轮重建提交：`44cd6179f0c7a0071d410523e6517fa19d48eba3`

## 结论范围

本轮复核回答的是：当前仓库随包提供的 Skill 入口、参考资料、自有脚本、测试与案例，是否仍保留已知上游的实质文字、代码或受保护资产。它不声称外部产品、API、协议、运行时依赖、研究事实或用户输入由本仓库创造，也不把字符串扫描等同于法律意见。

首轮重建提交中有 48 个 Skill 未发现已知上游的实质内容残留；9 个此前归类为“仓库原始基线”的 Skill 经复核后确认来自 Yichen Skills 的旧实现或改写，不能继续依赖原分类。它们随后全部进入独立重写与回归验证：

- `agent-memory`
- `chatgpt-web-research`
- `mac-wechat-dual-open`
- `web-research`
- `wechat-local-vault`
- `wechat-mp-batch-exporter`
- `wecom-local-vault`
- `wecom-operations`
- `x-article-draft-uploader`

## 方法

每个审计单元至少核对固定提交的完整文件清单、Git 沿革、旧版/本地已知来源、目录级许可证与随包资产。文本与代码先做 Unicode NFKC、大小写折叠和空白归一化，再检查较长完整行及 12/16-token 连续窗口。结果同时区分通用命令/API 名称、仓库内部家族合同与可保护的实质表达。部分 Agent 还做了独特短语精确外搜；未完成的外搜或语义级全网核验均保留为限制，不被包装成“绝对原创证明”。

发现 `FIX` 时，修复门槛不是换同义词，而是重新设计职责边界、数据流、状态模型与代码组织，并用离线测试、结构校验、编译和再次重合扫描验证。

## 50 个独立审计单元

| Agent | 审计范围 |
|---:|---|
| 01 | `agent-memory`；`chatgpt-web-research` |
| 02 | `beautiful-html-templates` |
| 03 | `goal-meta-skill` |
| 04 | `imagegen-frontend-web` |
| 05 | `impeccable` |
| 06 | `kami` |
| 07 | `lark-approval` |
| 08 | `lark-apps` |
| 09 | `lark-attendance` |
| 10 | `lark-base` |
| 11 | `lark-calendar` |
| 12 | `lark-contact` |
| 13 | `lark-doc` |
| 14 | `lark-drive` |
| 15 | `lark-event` |
| 16 | `lark-im` |
| 17 | `lark-mail` |
| 18 | `lark-markdown` |
| 19 | `lark-minutes` |
| 20 | `lark-note` |
| 21 | `lark-okr` |
| 22 | `lark-openapi-explorer` |
| 23 | `lark-shared` |
| 24 | `lark-sheets` |
| 25 | `lark-skill-maker` |
| 26 | `lark-slides` |
| 27 | `lark-task` |
| 28 | `lark-vc`；`lark-vc-agent` |
| 29 | `lark-whiteboard` |
| 30 | `lark-wiki` |
| 31 | `lark-workflow-meeting-summary`；`lark-workflow-standup-report` |
| 32 | `mac-wechat-dual-open` |
| 33 | `pua`；`pua-ding` |
| 34 | `pua-en` |
| 35 | `pua-ja` |
| 36 | `pua-loop` |
| 37 | `pua-mama` |
| 38 | `pua-p10` |
| 39 | `pua-p7` |
| 40 | `pua-p9` |
| 41 | `pua-pro` |
| 42 | `pua-shot` |
| 43 | `pua-yes` |
| 44 | `skill-publisher` |
| 45 | `skill-vetter` |
| 46 | `vintage-pencil-card` |
| 47 | `web-research`；`wechat-local-vault` |
| 48 | `wechat-mp-batch-exporter`；`wechat-reading` |
| 49 | `wecom-local-vault`；`wecom-operations` |
| 50 | `x-article-draft-uploader` |

以上 50 个单元覆盖 57 个 Skill；双人交叉项用于复核首轮分类或高风险本地数据工具，并非重复计算覆盖数量。

## 主要发现与处置

1. `agent-memory` 与 `chatgpt-web-research` 对 Yichen 对应目录存在高覆盖连续重合。两者的工作流、文档、案例和 Agent 元数据均已从空白设计重新实现。
2. `mac-wechat-dual-open` 的旧脚本与非商业、禁止公开打包的来源高度重合。现实现改为预览/执行双门、暂存副本、路径校验、plist 修改、签名、图标处理和状态回读的新组织，并加入离线测试。
3. `web-research` 的旧诊断器沿用来源实现。新版本只做隐私友好的结构检查，不读取账号状态，并加入回归测试。
4. `wechat-mp-batch-exporter` 的服务启动、下载、诊断和历史分析脚本曾大量重合。四个脚本、文档、输出合同与测试均已重建。
5. `wecom-operations` 的两个辅助脚本和多份操作文档来自旧来源。现实现使用预览/执行门、运行时 help/schema、私密回执和独立文档合同。
6. `x-article-draft-uploader` 的 cookie 导出与浏览器自动化仍保留来源结构。现版本要求精确 profile、域名边界、`0600` 原子 storage state、显式 `--apply`，且只创建并核验草稿。
7. `wechat-local-vault` 与 `wecom-local-vault` 是重合度最高的两项；其查询、快照、解密、密钥与授权模块全部重新组织和实现，并把无法在无真实账号/进程环境验证的部分降为明确限制。
8. `goal-meta-skill` 没有文字/代码重合，但旧测试案例沿用了上游的结账/优惠券情境；案例已换成静态站点导航重复标识问题。

## 自动证据与限制

最终工作树通过：57/57 `quick_validate.py`、57 个 provenance 条目与 57 份案例的集合审计（0 findings）、全量 Python 编译、16 组共 161 个离线单元测试、`git diff --check`，以及公开目标 `siuserxiaowei/skills` 的发布预检（0 blocker）。

九个纠错 Skill 对本地 Yichen 来源的最终 16-token 结果为：六项 0 命中；`wechat-local-vault` 23 个窗口全部来自连续 CLI 示例和消息类型编号；`wechat-mp-batch-exporter` 1 个窗口为 Python `json/main` 样板；`wecom-operations` 1 个窗口为标准库 import 样板。对应 12-token 覆盖均不超过 0.36%，人工查看未发现实质表达或实现重合。旧基线中的其他重建 Skill 也没有高覆盖窗口；唯一保留大段旧文本的是此前已由本仓库新增的 `vintage-pencil-card`，其第三方 Pexels 原图及衍生示例已删除，不把外部图片说成自有资产。

公开预检仍会把脚本可执行位、凭据路径引用、当前脏工作树和本机 `gh` 尚无 `gh skill` 列为人工 review warning；这些不是 blocker。凭据相关高风险提示集中在 X cookie 的显式导出/注入能力，已人工核对为精确 profile、域名限定、值不落终端、`0600` 原子输出和默认不执行。

本审计不能证明全互联网不存在语义相近的独立表达，也不能替代律师对思想/表达边界、商标、API 条款或未知历史授权的意见。真实微信、企业微信、飞书、ChatGPT、X 和浏览器会话未在审计环境中做破坏性或对外写入前向测试；这些能力仍需在用户授权、私密数据和当前产品版本下单独验证。
