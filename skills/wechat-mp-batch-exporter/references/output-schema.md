# Output Schema

## URL Download (Lightweight Path)

`scripts/download_urls.py` produces:

```text
<output-dir>/
|-- index.csv
|-- errors.json
`-- articles/
    |-- 001-title.md
    `-- 002-title.md
```

Columns of `index.csv`:

```text
seq,title,source_url,format,path,status,error,downloaded_at
```

`errors.json` holds an array of the items that failed:

```json
[
  {
    "seq": "002",
    "source_url": "https://mp.weixin.qq.com/s/...",
    "error": "..."
  }
]
```

## Enhanced Archive

Merging bodies, metrics, and comments out of the exporter means one row per article:

```text
account_name
fakeid
title
url
publish_time
author
digest
cover_url
body_markdown_path
html_path
image_dir
read_count
like_count
share_count
favorite_count
comment_count
comments_path
comment_replies_path
fetch_mode
credential_status
exported_at
error
```

Sidecar layout worth following:

```text
comments/<article-id>.json
comment-replies/<article-id>.json
raw-exporter/
logs/
```

Raw cookies, auth-key, pass_ticket, key, token, uin, and credentials JSON stay out of the output archive — the sole exception is a private debugging bundle the user explicitly requests after acknowledging the risk.

## History Count Breakdown

Once a public-account history is synced or imported, run `scripts/analyze_history.py`. Its outputs:

```text
history.summary.json
history.summary.md
history.dedup.json
history.dedup.csv
urls.all.txt
history.original.json
history.original.csv
urls.original.txt
```

The count fields to work with:

```text
raw_records
expanded_url_items
unique_urls
publish_groups
headline_items
original_articles
not_deleted_items
deleted_items
duplicate_records_removed
first_publish_time
last_publish_time
itemidx_counts
copyright_type_counts
copyright_stat_counts
```

What they mean:

- `expanded_url_items`: all unique article URLs that come out of expanding multi-article messages.
- `publish_groups`: distinct `msgid` values — loosely one WeChat publish/message group each.
- `headline_items`: the rows carrying `itemidx=1`.
- `original_articles`: rows matching `copyright_type=1`, `copyright_stat=1`, and `is_deleted=false`.

If the user puts WeChat frontend figures like “原创文章” next to these numbers, the right comparison target is `original_articles`, never `expanded_url_items`.
