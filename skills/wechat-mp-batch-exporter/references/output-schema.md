# Archive records and reconciliation outputs

## Public URL capture

Each run writes article bodies under `articles/`, plus:

- `index.csv`: one row per requested URL;
- `failures.json`: only unsuccessful rows.

`index.csv` fields are:

```text
position,source_url,status,title,relative_path,retrieved_at,error
```

Paths are relative to the run directory so the archive can be moved without rewriting the index.

## Normalized history

`analyze_history.py` writes the complete and platform-marked-original subsets as JSON, CSV, and URL lists. It also writes duplicate evidence and JSON/Markdown summaries.

The summary fields are:

```text
input_objects
expanded_articles
unique_article_urls
publish_groups
headline_articles
marked_original_articles
active_articles
deleted_articles
duplicates_removed
newest_published_at
oldest_published_at
item_position_counts
copyright_type_counts
```

These are reconciliation scopes, not interchangeable totals.

## Enhanced article record

When external tools provide metrics or comments, normalize them into one article record while keeping the unmodified upstream response in a separate private raw directory. Recommended groups:

- identity: account, article ID, canonical URL, title;
- publication: author, platform publication time, digest, cover URL;
- local artifacts: body path, HTML path, image directory;
- metrics: value, availability, retrieval time, and credential status for each field;
- comments: comment file, reply file, visibility/availability state;
- provenance: external tool/version, access route, exported time, and error.

Unknown or unauthorized fields remain `null` with an explanation. Do not encode “not fetched” as zero.

## Exclusions

Credentials, cookies, QR payloads, authorization headers, signed query parameters, `pass_ticket`, `auth-key`, tokens, and private proxy/certificate material are never part of a normal archive.
