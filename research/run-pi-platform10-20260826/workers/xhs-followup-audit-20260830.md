# Xiaohongshu follow-up audit — 2026-08-30

## Scope and method

- Used the user's already signed-in Chrome session and Xiaohongshu's native `Pi Agent` search.
- Opened each selected `/explore/<note-id>` canonical detail and read the visible title, creator, date line, body and public attachment metadata where shown.
- Search cards, snippets and comments were used only to locate details; they are not final evidence.
- No likes, follows, comments, collections, shares, messages, downloads or creator-side actions were performed.

## Worker-checked candidates

Five independent, Pi-specific detail objects were initially recorded in `xhs-followup-candidates-20260830.jsonl` and corresponding narrow readbacks in `xhs-followup-readbacks-20260830.jsonl`. A sixth replacement-quality object (`6a87dff9`) was appended after a body-vs-comment audit; all rows remain `worker_checked`; no curator acceptance is asserted here.

## Explicit exclusion

The search result `6a808415000000002500446e` (`我的 Pi Agent配置清单：6 个插件，够用`, creator 咕叽, 08-15 江苏) opened to a detail page whose visible body was image-only/no readable note text. It was not added as a candidate and must not be accepted from title, comments or card metadata alone.

The original `6a8172030000000008013d7b` detail page was also re-audited: its author `note-content` exposed only title, hashtags and edited date; the long Pi tutorial text previously observed belonged to a generated/comment reply, not the author's body. Treat `china-followup-xhs-6a817203-pi-guide-20260830` as rejected (`reject_author_body_not_visible`) and do not promote it. The appended `6a87dff9` row is the body-visible replacement.

## Access caveat

The normal logged-in detail route was available in this session. Relative dates are retained as `unknown` publication dates rather than inferred calendar dates. The platform's robots/risk boundaries remain in force; future work should continue through normal user-assisted browser access only.

## Correction record (2026-08-30)

- `6a8172030000000008013d7b` is explicitly **rejected**: the author's visible `note-content` contains only the title, hashtags and edit date. The long Pi tutorial text visible below was an AI-generated comment/reply, not the author's note body; it cannot satisfy the original-content gate. The corresponding worker row is retained only as an append-only audit trail and must not be promoted.
- `6a87dff9000000002500fc2a` is the body-visible replacement candidate appended to the worker/readback shards. It remains `worker_checked` pending explicit curator review.
