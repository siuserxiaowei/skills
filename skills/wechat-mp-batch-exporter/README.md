# WeChat MP Batch Exporter Overview

An agent workflow built around bulk archiving of WeChat Official Account articles.

What it helps with:

- Turning known `mp.weixin.qq.com` article URLs into Markdown, JSON, text, or HTML files.
- Pulling a public account's history list through `wechat-article-exporter`.
- Keeping `publish_groups`, `expanded_url_items`, and `original_articles` apart as separate counting scopes.
- Assembling enhanced archives — read counts, likes, shares, comments, and replies — whenever fresh user-owned credentials are on hand.

## Privacy Stance

Nothing sensitive ships with this public skill: no credentials, cookies, QR secrets, article archives, downloaded bodies, local account data, or private paths.

The scripts stay conservative on purpose:

- `doctor.py` only reads; it changes nothing.
- `download_urls.py` fetches solely known public article URLs through the configured exporter API.
- `start_wxdown_service.py` launches a local helper solely on explicit request and leaves system proxy settings untouched.
- QR login, certificate trust, proxy changes, and any WeChat desktop action all happen only after user confirmation, carried out by the user.

Output archives, `credentials.json`, cookies, auth-key values, `pass_ticket`, `uin`, tokens, QR login secrets, and private account data must never be committed.

## Setup

Downloading bodies for known URLs works out of the box — no upstream checkout needed:

```bash
python3 scripts/download_urls.py "https://mp.weixin.qq.com/s/..."
```

Account history needs an installed or self-hosted `wechat-article/wechat-article-exporter`; point the skill at it like this:

```bash
export WECHAT_ARTICLE_EXPORTER_DIR=/path/to/wechat-article-exporter
python3 scripts/doctor.py --exporter-path "$WECHAT_ARTICLE_EXPORTER_DIR" --check-network
```

Read counts and comments need `wechat-article/wxdown-service`; start it only once the user has signed off on the credential-capture workflow:

```bash
export WXDOWN_SERVICE_DIR=/path/to/wxdown-service
python3 scripts/start_wxdown_service.py --wxdown-dir "$WXDOWN_SERVICE_DIR" --dry-run
```

## Output

History analysis produces:

- `history.summary.json`
- `history.summary.md`
- `history.dedup.json`
- `history.dedup.csv`
- `urls.all.txt`
- `history.original.json`
- `history.original.csv`
- `urls.original.txt`

Known URL downloads produce:

- `index.csv`
- `errors.json`
- `articles/*`

## Safety Rules

- The agent never touches WeChat UI.
- Login walls, paywalls, deleted articles, private content, and platform permission checks are never bypassed.
- Article content remains the property of its original authors or rights holders — no republishing or redistribution without permission.
- Read/comment metrics are only as good as fresh user-owned credentials; never guarantee them otherwise.
- System proxy settings must be back to their prior state once a credential-capture run ends.
