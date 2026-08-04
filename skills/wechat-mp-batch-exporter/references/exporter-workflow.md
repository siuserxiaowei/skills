# Exporter Workflow

## 1. Downloading Bodies For Known URLs

`scripts/download_urls.py` handles article URLs the user already has. It talks to the public exporter download API and saves Markdown or JSON locally. Read counts and comments are outside its scope.

```bash
python3 {baseDir}/scripts/download_urls.py --file urls.txt --format markdown
```

When images, pixel-exact HTML preservation, DOCX, Excel, or PDF matter, switch to `wechat-article-exporter` — the lightweight URL script doesn't cover those.

## 2. History Lists Via Exporter Mode

Pick this route when the user hands over a public-account name, asks for the latest N articles, or juggles many accounts.

Public endpoint to prefer:

```text
https://down.mptext.top
```

For self-hosting or working from a local checkout, the source tree lives at:

```text
$WECHAT_ARTICLE_EXPORTER_DIR or /path/to/wechat-article-exporter
```

Upstream project page:

```text
https://github.com/wechat-article/wechat-article-exporter
```

Behind the scenes the exporter drives the WeChat Official Account backend search/list APIs through proxy endpoints of its own. Account search and article-list sync both demand a valid user-owned auth-key.

A typical run looks like:

1. Make sure the user can log into a WeChat Official Account or service account.
2. Bring up the exporter site, or the local exporter.
3. Have the user scan the QR code and pick the right public account/service account.
4. Look up the target public account.
5. Sync the article list.
6. Before quoting any totals, run `scripts/analyze_history.py` over the synced/exported history.
7. Present scoped counts, article titles, and publish dates in chat ahead of any download.
8. Let the user filter by latest count, date range, title keyword, original-only, or hand-picked rows.
9. Export the body data.

Auth-key stays out of chat. When the user supplies one manually, keep it in a local private runtime file, or in macOS Keychain where a script offers that option.

### Counting Scopes

Every account-history answer needs explicit scopes:

- `publish_groups`: distinct `msgid` values — loosely, one WeChat publish/message group apiece.
- `expanded_url_items`: the unique article URLs that multi-article messages expand into; often far above the WeChat frontend figure.
- `original_articles`: the original-article tally, i.e. rows matching `copyright_type=1`, `copyright_stat=1`, and `is_deleted=false`.

What the numbers look like in practice: one set of `publish_groups` may fan out into many more unique article URLs, of which only some pass the original-article filter. Any concrete figure is evidence from that particular run — never a lasting fact about the account.

## 3. Enhanced Data: Metrics And Comments

This mode applies when the user explicitly wants阅读量、点赞、转发、收藏、评论、评论回复.

Helper required:

```text
$WXDOWN_SERVICE_DIR or /path/to/wxdown-service
```

Upstream project page:

```text
https://github.com/wechat-article/wxdown-service
```

`wxdown-service` runs a local mitmproxy instance and exposes a WSS endpoint, typically in the shape of:

```text
wss://127.0.0.1:65001
```

Capturing user-owned article credentials requires the user to trust the mitmproxy CA certificate and to browse the relevant articles in the proper WeChat context. Credentials stay stored locally and get pushed fresh to the exporter.

Once credentials exist:

1. Point the exporter at the WSS endpoint, or follow the exporter's own credential detection flow.
2. Load or sync the target account plus the target article URLs.
3. Trigger the metadata/comment download within the exporter.
4. Export the resulting enhanced dataset.
5. Write comments and replies to JSON/CSV sidecar files; keep raw comment bodies out of chat unless the user asks for a brief excerpt or an analysis.

## 4. Self-Hosting The Exporter Locally

Fire up a local exporter only when the public site falls short or the user asks for a local/private deployment.

Upstream's stated requirements:

```bash
corepack enable
corepack prepare yarn@1.22.22 --activate
yarn
yarn dev
```

Current upstream calls for Node >= 22. A local snapshot might lag behind, so consult `package.json` prior to installing anything.

## 5. Run Validation

Check each run against:

- the output directory exists
- `history.summary.json` exists and carries `publish_groups`, `expanded_url_items`, and `original_articles`
- `index.csv` or the exporter table exists
- the number of selected URLs equals the number of downloaded bodies
- enhanced runs record credentials as fresh, missing, or expired
- failed URLs get their own separate listing
- the system proxy was put back if proxy mode saw use
