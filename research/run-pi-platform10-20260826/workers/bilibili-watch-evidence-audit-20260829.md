# Bilibili watch-evidence demotion audit (2026-08-29)

Scope: ten previously accepted Bilibili items in `candidates.json`. This append-only audit re-read the public official `x/web-interface/view` detail API. It did not download or play media, install tools, bypass login/CAPTCHA/robots, or infer watch evidence from counters, descriptions, chapters, or search snippets.

Decision: all ten items are removed from curator-accepted `candidates.json`; nine worker IDs remain in `review_queue.json` as `worker_checked`. The seed row `seed-bilibili-38-pi` has no separate queue row because its canonical URL is represented by the existing duplicate worker row `worker-cn-001` (also `worker_checked`). None may count toward Bilibili quota until a future curator readback records actual playback observation, public transcript/subtitle, or an equivalent auditable content transcript.

| candidate_id | BVID | API HTTP/code | duration (s) | public subtitle list | evidence decision |
|---|---|---:|---:|---:|---|
| seed-bilibili-38-pi | BV139bD6gEa8 | 200/0 | 2678 | 0 | demoted_to_worker_checked |
| worker-cn-007 | BV1p68b6YEtE | 200/0 | 519 | 0 | demoted_to_worker_checked |
| worker-cn-008 | BV1CTbf6CEGu | 200/0 | 771 | 0 | demoted_to_worker_checked |
| worker-cn-011 | BV1TUM26vEAC | 200/0 | 568 | 0 | demoted_to_worker_checked |
| worker-cn-012 | BV1QwMU6yExQ | 200/0 | 1778 | 0 | demoted_to_worker_checked |
| worker-cn-013 | BV1ZnEJ6NEJ6 | 200/0 | 1916 | 0 | demoted_to_worker_checked |
| worker-cn-014 | BV1wBfvBnEkY | 200/0 | 940 | 0 | demoted_to_worker_checked |
| worker-cn-016 | BV1j5NJ6AE6B | 200/0 | 144 | 0 | demoted_to_worker_checked |
| worker-cn-018 | BV1vL3o6UE5T | 200/0 | 446 | 0 | demoted_to_worker_checked |
| worker-cn-020 | BV1WHGu6AEFp | 200/0 | 264 | 0 | demoted_to_worker_checked |

Limitations: official detail API returned metadata and descriptions; all ten records had an empty public subtitle list at audit time. Browser/OpenCLI and `bili` CLI were unavailable in this environment; no ASR provider key was configured. Per task boundary, no audio was downloaded and no package/tool was installed.
