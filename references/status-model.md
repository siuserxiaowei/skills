# Seven-state model

Read this file whenever a task needs classification or a status transition.

## States

| Key | Canonical status | Use only when |
|---|---|---|
| `pending` | `📝 待派发` | The user explicitly registered work but the execution instruction has not been sent. Never infer this from an unsent composer draft. |
| `discussion` | `💬 讨论中` | The conversation is clarifying needs, comparing options, or chatting, and actual execution has not been authorized. |
| `attention` | `🟡 待确认` | Progress requires user information, approval of a high-impact action, confirmation before sending, or acceptance of a result. |
| `running` | `🔵 进行中` | Codex is actively executing, using tools, validating, or otherwise making progress. |
| `waiting` | `⏳ 等待中` | The next dependency is an external system, scheduled time, automation, another task, rate limit, or cooldown. |
| `paused` | `⏸️ 已暂停` | The user explicitly paused/cancelled, or a real blocker prevents further progress. Inactivity alone is not evidence. |
| `complete` | `✅ 已完成` | The requested deliverable exists and proportionate verification passed. |

Accepted aliases for manual marking are the keys above and these Chinese forms: `待派发`, `讨论中`, `待确认`, `进行中`, `等待中`, `已暂停`, `已完成`. The legacy `🌞` prefix means `running` only for migration.

## Decision precedence

Apply this order, stopping at the first decisive signal:

1. An explicit user state setting.
2. Current runtime or approval evidence, such as active execution or waiting on approval.
3. Waiting, pause, cancellation, or genuine blocker signals in the latest conversation.
4. Verified completion evidence: both an actual deliverable and a meaningful validation result.
5. Discussion when work authorization or stronger lifecycle evidence is absent.

Runtime `notLoaded` only means the task is not loaded in memory. It never proves pause, waiting, or completion. Likewise, an idle task or a completed assistant turn does not prove the underlying task is complete.

## Confidence

- **High (0.85–1.00):** an explicit state instruction, observable live status, approval request, explicit pause/cancel, or clear deliverable plus validation.
- **Medium (0.70–0.84):** recent conversation strongly implies one state but lacks a direct lifecycle statement.
- **Low (<0.70):** conflicting, stale, or insufficient evidence. Preserve the current title during historical organization.

Never inflate confidence based only on an existing Emoji prefix: the prefix is a prior claim, not proof.

## Transition mechanics

1. Resolve the target Codex task without changing it.
2. Inspect its current title and choose the status using the precedence above.
3. Normalize with `scripts/status_title.py transition --status <key> --title <current-title>`.
4. If `changed` is false, stop. Do not rename or sound.
5. Rename to `proposedTitle`.
6. Only if `stateChanged` is true, play the returned `soundEvent` once after the rename succeeds. Every state uses its own event and sound.

During historical batch application, suppress all sounds regardless of the target states.

## Classification examples

| Conversation evidence | Expected state | Reason |
|---|---|---|
| “先记下来，别做” | `📝 待派发` | Explicit registration without dispatch. |
| “我们先比较三个方案” | `💬 讨论中` | Deliberation, no execution authorization. |
| “需要你确认是否发布” | `🟡 待确认` | User decision is the next dependency. |
| Tools are running and verification is underway | `🔵 进行中` | Observable active work. |
| “已提交，正在等第三方导出完成” | `⏳ 等待中` | External dependency. |
| “先停一下，明天再继续” | `⏸️ 已暂停` | Explicit pause. |
| Artifact exists and tests passed | `✅ 已完成` | Delivery and verification are both present. |

Edge cases:

- A tool failure followed by viable retries is still `🔵 进行中`; a failure that creates a true no-path blocker is `⏸️ 已暂停`.
- Waiting for approval is `🟡 待确认`, not `⏳ 等待中`.
- A user cancellation is `⏸️ 已暂停`, even if partial artifacts exist.
- “Here is what I would do” without authorization is `💬 讨论中`.
- An assistant final response that lists unfinished work is not `✅ 已完成`.
- A low-confidence old task stays unchanged during historical organization.
