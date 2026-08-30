---
name: wechat-mp-batch-exporter
description: 批量下载微信公众号文章正文、历史文章列表、原创文章筛选、历史计数口径、阅读量、点赞/转发等指标、评论和评论回复。Use when the user asks to batch fetch mp.weixin.qq.com articles, export WeChat public-account history, tell apart publish groups vs expanded article URLs vs original articles, work with wechat-article-exporter, set up wxdown-service credentials, gather read/comment metrics, or build an archive for Obsidian/Feishu/local analysis. Skip it for plain one-off article summarization when no batch or enhanced data is involved.
---

# WeChat MP Batch Exporter Skill

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

## Hard Rules

Hands off the user's WeChat client entirely. Publishing, deleting, mass-sending, following, unfollowing, messaging, or any clicking inside WeChat is off limits. Whenever a workflow depends on WeChat desktop, spell out the exact steps for the user and pause until they confirm.

Raw cookies, auth-key, token, pass_ticket, key, uin, credentials JSON, and QR login secrets must never show up in chat or in any saved report.

Copyright of downloaded articles stays with the original authors or rights holders. Keep exports inside the user's lawful, private-use scope unless the user explicitly confirms permission to republish or redistribute.

## Start Here

Before picking any workflow, run the local doctor:

```bash
python3 {baseDir}/scripts/doctor.py
```

Add `--check-network` only if the task actually calls the public exporter API or the online download endpoint.

## Picking A Workflow

- Known article URLs and only正文/Markdown needed → `scripts/download_urls.py`; no login, no WeChat action.
- A public account's历史文章列表 or the latest N articles → exporter mode via `wechat-article-exporter`, which demands a user-owned WeChat Official Account backend login/auth-key.
- 阅读量、点赞、转发、评论、评论回复 → complete the `wxdown-service` credentials flow first, then export the enhanced fields through `wechat-article-exporter`.
- “不登录”“代理模式” requests, or a failing exporter mode → fall back to proxy/history capture only after the user explicitly agrees; read `references/manual-gates.md` beforehand.

For plain single-URL extraction with no batch or enhanced requirement, the existing `$wechat-article` skill is the better fit.

## Counting Rules

A public-account total must never be stated as a bare “N 篇文章” before the counting scope is pinned down.

Once a history sync finishes or a history JSON gets imported, run:

```bash
python3 {baseDir}/scripts/analyze_history.py --history-json /path/to/history.dedup.json
python3 {baseDir}/scripts/analyze_history.py --chunk-dir /path/to/chunks --output-dir /path/to/output
```

Stick to these labels when answering the user:

- `publish_groups`: distinct `msgid` values, i.e. roughly one WeChat publish/message group each.
- `expanded_url_items`: all unique article URLs produced by expanding multi-article messages.
- `original_articles`: the frontend-style original count — `copyright_type=1`, `copyright_stat=1`, plus `is_deleted=false`.

When the numbers don't match what the user sees inside WeChat, lead with the scope explanation and reference the generated `history.summary.json` / `history.summary.md`.

## Downloading Known URLs

Pasted URLs or `.txt` / `.csv` / `.json` URL lists go through:

```bash
python3 {baseDir}/scripts/download_urls.py --file /path/to/urls.txt --format markdown
python3 {baseDir}/scripts/download_urls.py "https://mp.weixin.qq.com/s/..."
```

Report back only the success count, failure count, failed URLs, output directory, and `index.csv`.

Default layout:

```text
~/Downloads/wechat-mp-batch/<run-id>/
|-- index.csv
|-- errors.json
`-- articles/
    `-- 001-<safe-title>.md
```

## History Sync And Enhanced Export

Always read `references/exporter-workflow.md` ahead of exporter, history, or enhanced-data work.

Launch the local credential helper via:

```bash
python3 {baseDir}/scripts/start_wxdown_service.py
```

Build on the mature upstream stack:

- `wechat-article/wechat-article-exporter` covers account search, article history, body download, and multi-format export.
- `wechat-article/wxdown-service` captures the user-owned credentials that read/comment metrics depend on.

Local checkout locations vary per machine, so take them from environment variables or explicit flags:

```bash
export WECHAT_ARTICLE_EXPORTER_DIR=/path/to/wechat-article-exporter
export WXDOWN_SERVICE_DIR=/path/to/wxdown-service
python3 {baseDir}/scripts/doctor.py --exporter-path "$WECHAT_ARTICLE_EXPORTER_DIR" --wxdown-path "$WXDOWN_SERVICE_DIR"
python3 {baseDir}/scripts/start_wxdown_service.py --wxdown-dir "$WXDOWN_SERVICE_DIR"
```

The public exporter's default base URL:

```text
https://down.mptext.top
```

## Human Checkpoints

Whenever login, credentials, comments, read counts, proxy, certificate trust, or WeChat desktop enters the picture, read `references/manual-gates.md`.

Each of the following demands explicit user confirmation every time:

- Scanning the QR code and picking the user's Official Account or service account.
- Installing a mitmproxy certificate or marking it as trusted.
- Turning on or modifying macOS system proxy settings.
- Having the user open an article/history page in WeChat desktop and scroll it.
- Consuming a pasted auth-key or credentials file.

## Output Layout

When assembling an archive or feeding exporter results into another system, read `references/output-schema.md`.

Preferred field set for the enhanced archive:

```text
account_name, fakeid, title, url, publish_time, author, digest, cover_url,
body_markdown_path, html_path, image_dir,
read_count, like_count, share_count, favorite_count, comment_count,
comments_path, comment_replies_path, fetch_mode, credential_status, exported_at
```

History analysis should produce:

```text
history.summary.json, history.summary.md,
history.dedup.json, history.dedup.csv, urls.all.txt,
history.original.json, history.original.csv, urls.original.txt
```

## Automation Limits

- No bypassing login, deleted content, paywalls, private articles, or platform permission checks.
- Read/comment metrics can't be guaranteed unless fresh user-owned credentials exist.
- The user's own WeChat desktop actions can't be performed or substituted by the agent.
- Comments can't be promised for articles where commenting is disabled or hidden.
- Never silently install system certificates, flip proxy settings, or leave a proxy enabled afterwards.
