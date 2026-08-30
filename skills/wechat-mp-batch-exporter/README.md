# WeChat Official Account archive Skill

This directory contains an independently implemented Agent Skill and three local utilities:

- `download_urls.py` previews and, with `--apply`, captures a finite set of known public article URLs through a configured API;
- `analyze_history.py` deduplicates a supplied history export and reports non-equivalent counting scopes;
- `doctor.py` inventories tools/checkouts without reading credentials or controlling WeChat;
- `start_wxdown_service.py` previews and optionally starts an owner-provided external helper checkout without changing system proxy settings.

External projects such as `wechat-article-exporter` and `wxdown-service` are not vendored. Their licenses, releases, and operating instructions must be checked at use time.

Private archives and all login/credential artifacts belong outside this repository. Article rights remain with their authors or rights holders.
