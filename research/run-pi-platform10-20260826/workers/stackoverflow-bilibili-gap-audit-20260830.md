# Stack Overflow / Bilibili gap audit (2026-08-30)

This append-only audit adds no candidate or accepted row. It records a fresh bounded public probe after loading all existing IDs and canonical URLs from the run queue, candidates, and worker evidence. No shared ledger, `candidates.json`, or `review_queue.json` was modified.

## Stack Overflow

The official anonymous Stack Exchange API was queried sequentially with three-second spacing, `site=stackoverflow`, `filter=withbody`, and seven new exact/quoted aliases not previously present in the run's probe files:

```text
"@earendil-works/pi-ai"
"@earendil-works/pi-coding-agent"
"@earendil-works/pi-tui"
"pi-session" + "earendil"
"pi-forge" + coding
"pi-web" + "earendil-works"
"badlogic/pi-mono" + agent
```

All seven returned HTTP 200 with `items: []`. Remaining anonymous quota decreased from 244 to 229; each response was 67 bytes with an individual SHA-256 recorded in the probe log. A supplementary unquoted check for `earendil-works`, `pi-coding-agent`, `pi-agent-core`, `pi-tui`, and `oh-my-pi` returned only unrelated Raspberry Pi, Mono, Bluetooth, or generic agent questions; none named the specified coding-agent project and no candidate was created. No HTML scraping, CAPTCHA solving, login, vote, comment, answer, edit, or account action occurred.

**Decision:** zero new Stack Overflow objects. Keep the platform at its reproducible zero-result/partial state; retry only when a new exact-alias API result is indexed.

## Bilibili

A bounded Google discovery query (`site:bilibili.com/video "Pi Agent" "pi-coding-agent"`) exposed public canonical details not present in the local queue. Five distinct Pi-focused BVIDs were checked through the official anonymous endpoints, with ordinary Chrome page confirmation:

| BVID | Visible title / uploader | Duration | `view` subtitle list | `player/v2` state | Decision |
|---|---|---:|---:|---|---|
| `BV1aW3V6WEsT` | 一口气学会Pi Agent极简Harness系统设计 / 肖恩君Sean | 22:30 | 0 | `need_login_subtitle=true`; paid full-video preview | not promotable |
| `BV1ZcVJ6nEJd` | pi与oh-my-pi比较 / 原周率加1 | 00:58 | 0 | `need_login_subtitle=true`; paid full-video preview | not promotable |
| `BV1zagQ6BEry` | Pi Agent 源码系统课：从真实运行到自己组装 Agent / 幻想家阿星403 | 54:32 | 0 | `need_login_subtitle=true`; paid full-video preview | not promotable |
| `BV1FtgK6yEhY` | 01-Pi Agent 架构详解 loop extention TUI / AI_Julie | 42:02 | 0 | `need_login_subtitle=true`; paid full-video preview | not promotable |
| `BV1mAEh6jEYU` | Alejandro AO｜Pi Agent 极简入门 / 63号炼金工坊 | 26:34 | 0 | no public subtitle; paid full-video preview | not promotable |

The official `x/web-interface/view` and `x/player/v2` response hashes, CIDs, timestamps, title/owner fields, subtitle counts, and preview messages are in `bilibili-public-gap-probes-20260830.jsonl` (artifact SHA-256 `d66145e92d906732cbd85838bee727034ce363c6a0f57b213ddd8b8b5499a3ae`). The first Chrome readback visibly exposed a rich chapter/description list (four tools, TUI/CLI/JSON/RPC, sessions, skills/extensions/packages) but also `登录 免费享高清视频` and `试看30秒`; chapters/descriptions are metadata and do not substitute for a watched transcript. The other pages similarly showed the login/trial boundary and no transcript. No media stream, subtitle URL, download, ASR workaround, CAPTCHA, purchase, or login was attempted.

**Decision:** zero new Bilibili candidates. All five remain discovery negatives; they must not count toward the ten-item quota. The existing `worker-cn-021` remains separately blocked by its login/purchase/subtitle boundary. Safe resume requires a normal user-assisted login with read-only full playback/subtitle inspection or a creator-provided public transcript.
