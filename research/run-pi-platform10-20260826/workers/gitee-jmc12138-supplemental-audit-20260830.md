# Gitee jmc12138 supplemental audit (2026-08-30)

This append-only audit records three public Gitee repository-root readbacks. It does not promote rows or edit `candidates.json`, `review_queue.json`, or derived ledgers.

## Discovery and duplicate boundary

One bounded Google exact-site query (`site:gitee.com "pi-coding-agent" -github`) exposed the jmc12138 project list. Existing candidate IDs and normalized canonical URLs were checked before each direct read; none of the three roots was present in the frozen queue/candidates snapshot. Only ordinary anonymous public Gitee pages were used. No API/raw/blob/commit automation, login, star, issue, fork, download, install, or credential access occurred.

The three roots share owner `jmc12138` and a roughly one-month creation/update window, and `my-pi` documents the other two packages. They are therefore a same-author suite for cluster review. Their canonical objects and complete README bodies are nevertheless materially different:

* `my-pi` (`zhangph12138/my-pi`, 8,381 Unicode chars) is an installer/workstation composition with Pi 0.81.1 pinning, provider ownership, models.json and `.pi/settings.json` guidance.
* `ccswitch-pi` (`zhangph12138/ccswitch-pi`, 2,322 Unicode chars) is a provider bridge with dynamic Claude/Codex routes and bounded pre-SSE retries.
* `pi-hide-tools` (`zhangph12138/pi-hide-tools`, 977 Unicode chars) is a renderer extension that hides seven built-in tool rows while preserving execution/results/context.

No same-body or canonical collision was observed. Because the suite is cross-linked and same-author, the primary curator should conservatively keep at most one or two as independent quota objects according to the global content-cluster policy; `my-pi` and `ccswitch-pi` have the strongest Pi-primary evidence, while `pi-hide-tools` is optional if a third suite item is allowed.

## Reproducible readback evidence

The companion `gitee-jmc12138-supplemental-readbacks-20260830.jsonl` contains only the curator helper's readback allowlist fields. SHA-256 values are hashes of the rendered `.file_content.markdown-body` text:

* `my-pi`: `9530bd86deee9538204fcc543567ff703b0cda9f0e333b3737b49187baccf734`.
* `ccswitch-pi`: `718e1fcdfa9638241276d2e2f128ec1e8f9a566cb0a3315f7dc5167def840ddd`.
* `pi-hide-tools`: `772a4a412ef9be0eccc7b0510fcf01ed190b6c454d00179189c23cdc5496268d`.

All three remain `curator_review_ready` worker evidence until the primary curator explicitly selects IDs and runs the fail-closed promotion helper.
