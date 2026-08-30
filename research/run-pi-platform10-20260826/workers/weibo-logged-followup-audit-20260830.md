# Weibo logged-in follow-up audit — 2026-08-30

## Scope and route

- User reported a logged-in Weibo session. I used the native Weibo search page only to discover objects, then opened the corresponding mobile canonical detail routes (`m.weibo.cn/detail/<mid>`) in the same Chrome session.
- Each of the eight rows below was freshly read from the native detail page: title/body, account, visible month-day/time, canonical object ID and visible engagement controls were checked. Search cards, Weibo AI-generated “智搜” answers and comments were not used as final evidence.
- No like, repost, comment, follow, collection, message, download, or creator-side action was performed. The desktop `/weibo/<uid>/<mid>` route redirected to the visitor system during this pass; the mobile canonical route was the successful readback surface.

## New worker-checked rows

`weibo-logged-followup-candidates-20260830.jsonl` contains 8 unique Weibo object IDs and canonical URLs; `weibo-logged-followup-readbacks-20260830.jsonl` contains one narrow readback per row. All rows remain `evidence_status=worker_checked`; no curator acceptance is asserted.

| object | account | Pi identity anchor | visible date |
| --- | --- | --- | --- |
| `RcqOGfo8f` | 蚁工厂 | `π-agent book`, `Pi agent` source-reading book | 8-8 13:18 |
| `Rc6SojaAG` | 张岱樾 | `Pi-Agent` source tutorial and `dg-ai-notes` | 8-6 10:33 |
| `RdoPH7Evz` | 斌叔OKmath | GooeyPi supports Pi / Oh-My-Pi / Prime Agent | 8-14 22:06 |
| `ResXSiAcs` | AI星踪岛 | Pi Coding Agent, Extensions / Skills / Packages | 8-21 22:27 |
| `R9WYfDIiz` | agentzh | Pi Coding Agent internal Coding Evals comparison | 7-23 05:39 |
| `Rc7imbU1q` | _阿楠_ | explicit switch to `pi coding agent` | 8-6 11:36 |
| `QvKULtfwI` | 挨踢牛魔王 | OpenClaw based on `pi-mono-agent` | 3-12 16:40 |
| `QvHAIchU0` | RAyH4c | explicit `oh-my-pi` code-agent / Pi-core route | 3-12 08:12 |

## Deduplication and acceptance boundaries

- Before writing, I searched the current `review_queue.json`, `candidates.json`, and all worker artifacts for each mid and canonical URL; none of the eight object IDs or URLs was present. Existing Weibo queue objects remain the three older `/2/detail/` rows and were not duplicated.
- Body fingerprints were computed from the visible article text used for these rows and are distinct within this shard. This is an object-level uniqueness check, not a claim that every linked project or referenced article is independent; `limitations` records secondary/short-post constraints.
- `Rc7imbU1q` is intentionally retained as a thin, one-sentence practitioner record for curator decision, not silently promoted. `QvKULtfwI` and `QvHAIchU0` are marked `independent_candidate_pi_secondary` because Pi is an implementation/ecosystem reference rather than the sole topic.
- Dates show only month/day in the native page; the candidate rows use 2026 because the run date is 2026-08-30 and explicitly record this basis. A curator may downgrade to `unknown` if the acceptance policy requires no year inference.

## Field and evidence checks

- Every candidate row has the queue compiler's required 19 fields, a stable `platform_object_id`, a canonical HTTPS URL, a non-empty summary/why-useful, and a native detail readback description.
- Every readback row has the required 12 readback fields and points to the matching object ID.
- No row claims `accepted`; all are ready for the main curator's independent review and any content-cluster decisions.
