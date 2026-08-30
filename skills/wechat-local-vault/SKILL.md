---
name: wechat-local-vault
description: |
  用于用户请求在本机把微信 Mac 4.x 的数据库解密成可长期复用的数字资产库，并提供本地查询分析能力。涵盖密钥提取、全量解密、增量刷新、按联系人/群聊导出会话、关系复盘、客户跟进与内容沉淀，数据范围包括聊天记录、联系人、群聊、朋友圈、收藏夹以及语音/附件索引。触发关键词包括：微信解析、微信全量、微信增量、聊天记录、导出聊天、朋友圈解析、收藏夹解析、客户跟进、wechat-local-vault。
---

# 微信本地数字资产库

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

本 skill 做两件事：把本机微信数据沉淀成“本地数字资产库”，再在其上提供“本地查询分析台”。工作方式是读取本机数据库文件和本地进程，不模拟点击微信窗口；只有用户明确授权时才允许触碰微信 UI。处理对象固定为官方首个微信容器 `com.tencent.xinWeChat`，双开或第二个微信容器一律不管。

设计上参考了两类成熟方案的长处：

- WeChat CLI 式命令形态：单一入口、默认 JSON 输出，覆盖最近会话、历史记录、全局搜索、联系人详情、群成员、统计、导出、收藏夹、未读与增量新消息等场景。
- 一套群聊摘要工作流的组织方式：按群分目录归档、支持从上次摘要接着写、产出摘要素材包、维护群友画像目录和历史索引、预留图片说明扩展位，并沿用“消息量大时先落盘再分析”的稳妥做法。

## 隐私红线

- 回复和日志中一律不出现 key、完整 salt、wxid 和聊天库原文，除非用户主动要求展示。
- key、配置、明文库、manifest、增量状态与导出目录全部交给本机配置文件托管；skill 文档内不得出现任何真实机器的绝对路径、wxid、联系人名或聊天内容。
- 推荐把 key 与明文库收进本机私有的应用数据目录，把给人看的报告放进用户自己挑选的导出目录；文档里只用占位符或配置字段指代路径。
- 明文数据库不得拷贝进项目工作区、桌面、网盘同步目录或聊天回复；工作区里只允许存在用户点名要的导出报告。

## 按用户意图选最小动作

1. 出现“第一次用、解不开、key 没了、全部解密、全量重建”一类说法：进入全量路线。
2. 出现“继续、更新一下、增量、最近、今天、新消息”一类说法：进入增量路线。
3. 用户点名具体联系人、群聊或会话 ID：只导出该会话；如有必要先对消息库做一次增量解密。
4. 用户给出时间段：导出或分析都限定在该时间段内。
5. 用户问朋友圈或收藏夹：只读对应的已解密库；缺 key 时按需补抓，不做全量。
6. 用户明确要“群聊摘要、群聊精华、日报、复盘、从上次继续”：先跑 `vault_cli.py digest-source` 产出素材包，再基于素材写简报；注意这只是 skill 的一个用法，不要把整个 skill 当成摘要工具来介绍。
7. 用户声明不许动微信界面：只能走 `--match-only`、已保存的 key、已解密库或本地数据库文件这几条路，禁止启动 Computer Use。

## 日常查询主入口

绝大多数查询直接走 `scripts/vault_cli.py`：它只读已解密的 vault，既不抓 key 也不碰微信 UI。

```bash
python3 {{SKILL_DIR}}/scripts/vault_cli.py status --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py sessions --limit 20 --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py unread --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py new-messages --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py contacts --query "关键词" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py members "群名" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py history "联系人或群名" --start-time "2026-05-01" --end-time "2026-05-14" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py search "关键词" --chat "群名" --type link --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py stats "群名" --start-time "2026-05-01" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py export "群名" --format markdown --output ./chat.md
python3 {{SKILL_DIR}}/scripts/vault_cli.py favorites --type article --query "关键词" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py moments --name "联系人" --start "2026-05-01" --format text
```

按消息类型筛选时可选值有：`text`、`image`、`voice`、`video`、`sticker`、`location`、`link`、`file`、`call`、`system`。

### 群聊摘要素材包

当用户说“群聊精华、日报、总结群聊、看看这个群最近聊了什么、从上次继续”：

```bash
python3 {{SKILL_DIR}}/scripts/vault_cli.py digest-source "群名" --start "2026-05-01" --end "2026-05-14" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py digest-source "群名" --since-last --data-root ~/Documents/wechat-digests --format text
```

产物写入 `{data_root}/{group_id}-{group_name}/sources/`，目录结构如下：

- `profiles/`：常规风格的群友画像。
- `profiles-roast/`：毒舌风格画像，与常规版分目录存放，互不混用。
- `imgs/`：图片说明的扩展位，命名规则 `{message_id}.txt`，每个文件用一行文字描述对应图片。
- `sources/*.json`：结构化素材，含消息原文、发言统计与相关路径，供程序读取。
- `sources/*.md`：同一份素材的可读版本，方便人工浏览和动笔。

注意素材包本身不会碰 `history.json`。摘要历史只在成稿写完并经用户确认后才更新，否则半成品会污染“从上次继续”所依赖的锚点。

## 底层脚本直调场景

想看本机存在哪些库（不启动微信）：

```bash
python3 {{SKILL_DIR}}/scripts/extract_keys.py --list-dbs
```

拿已有的抓取日志离线匹配 key（不启动微信）：

```bash
python3 {{SKILL_DIR}}/scripts/extract_keys.py --match-only --targets all --reuse-log
```

第一次全量抓 key（仅在确实需要新 key 时执行；务必绕开第二微信）：

```bash
python3 {{SKILL_DIR}}/scripts/extract_keys.py --targets all --duration 240
```

把整个库全量解密进私密 vault：

```bash
python3 {{SKILL_DIR}}/scripts/decrypt_all_dbs.py --mode full
```

日常增量刷新（只处理有变化的库，不会把一切重头来过）：

```bash
python3 {{SKILL_DIR}}/scripts/decrypt_all_dbs.py --mode incremental
```

导出与某联系人的全部聊天：

```bash
python3 {{SKILL_DIR}}/scripts/export_chat.py --contact "联系人备注" --mode full
```

只导出与该联系人的新增聊天：

```bash
python3 {{SKILL_DIR}}/scripts/export_chat.py --contact "联系人备注" --mode incremental
```

按精确的会话 ID 加时间段导出：

```bash
python3 {{SKILL_DIR}}/scripts/export_chat.py --chat-id "contact_username" --since "2025-01-01"
```

这些独立脚本在窄场景下依然可用；不过用户没有点名时，一律优先 `vault_cli.py`。

## 标准工作流

### 全量路线

适用情形：首次配置、更换设备、微信升级导致 key 失效、用户明确要求全量重建。

1. 先跑 `extract_keys.py --list-dbs` 摸清本地库情况，敏感 salt 不展示。
2. 若 `~/.config/wechat-keys.json` 里已存 key，先以 `--match-only --targets all --reuse-log` 尝试复用。
3. 复用不成功、或缺关键库时，才实际执行抓 key。
4. 跑 `decrypt_all_dbs.py --mode full`，明文库统一写入私密 vault。
5. 打开 manifest 核对成功解密的数量与失败条目。

### 增量路线

适用情形：日常刷新、接着上次的进度做、只关心近期新增内容。

1. 跑 `decrypt_all_dbs.py --mode incremental`。
2. 目标若落在某个联系人/群聊上，再跑 `export_chat.py --mode incremental`。
3. 没有新增消息就如实告知用户没有新内容。
4. 增量状态只写进 vault 的 `state` 目录，不回落到 skill 文档里。

### 指定会话分析

适用情形：“分析我和某某的聊天”“导出这个会话 ID”“帮我写下一条怎么回”。

1. 用户提供备注或昵称时，用 `export_chat.py --contact`。
2. 用户提供微信 userName 或会话 ID 时，用 `export_chat.py --chat-id`。
3. 拿到导出报告后，围绕用户目标分析关系走向、语气、风险点和下一步话术。
4. 默认不整段贴原文；用户说“仔细解析”时才给出完整时间线或报告路径。

### 朋友圈/收藏夹解析

直接读已解密的 `sns/sns.db`、`favorite/favorite.db` 与 `message_resource.db`。缺 key 时只补抓相关库，不触发全量抓取。结果输出到用户配置的导出目录。

### 群聊精华/日报路线

1. 先做一次增量解密，保证明文 vault 处于最新状态。
2. 借 `vault_cli.py contacts` 或 `sessions` 解析群名，确认命中唯一群聊。
3. 用 `digest-source` 按时间段生成素材包；群大或时间跨度长时一律先落文件，不要把几百上千条原始消息直接塞进对话。
4. 读 `sources/*.md`，必要时再翻 `sources/*.json`；先搭话题骨架，再动笔写正文。
5. 成稿推荐结构：标题、消息统计、发言排行、开篇概览、群友画像、分类正文、待解决问题、固定结尾。
6. 需要毒舌版时可在同一份素材上另写一版，但严禁人身攻击，严禁推断健康、家庭、身份等属性，也严禁拿时间戳推测作息或所在地。
7. 图片内容默认不可见。只有当 `imgs/{message_id}.txt` 存在时才能把其中的描述写进摘要；否则只能表述为“图片内容不可见，根据上下文推断到这里围绕一张图片讨论”，不得凭空编造画面。
8. 摘要经确认定稿后，才更新群目录下的 `history.json` 与 `history-digests.jsonl`；“从上次继续”完全依赖这两个文件定位。

## 回复与输出约定

- 对话里先给结论、文件路径和下一步建议；大段原文放进 Markdown 文件。
- 涉及私聊时，按需引用少量原文即可，不要把整个库的内容倒进聊天窗口。
- 表述上分清三类产物：“已解密明文库”“可读导出报告”“密钥配置”。
- 每完成一次解密，都要说明结果保存在哪里、是否含有明文隐私。

## 脚本一览

- `scripts/vault_cli.py`：本地查询统一入口；沿用 WeChat CLI 的常用命令形态，额外支持朋友圈查询与摘要素材包。
- `scripts/extract_keys.py`：负责本机 key 的捕获、复用与匹配。
- `scripts/decrypt_all_dbs.py`：全量/增量解密，写入私密 vault 并产出 manifest。
- `scripts/export_chat.py`：按联系人、群聊或会话 ID 导出完整或增量的聊天记录。
- `scripts/list_contacts.py`：列出联系人与群聊。
- `scripts/wechat_digest.py`：按天生成摘要的独立脚本，仅在用户明确要摘要时启用。
- `scripts/search_sns.py`：朋友圈检索的辅助工具。
