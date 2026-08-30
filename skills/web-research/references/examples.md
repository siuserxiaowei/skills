# Web Research Router examples

## 正向案例

**用户请求：** “找出近六个月中国市场的五个同类产品，核对融资和定价，再把主要来源保存下来。”

**处理：** Define the market and date boundary; discover candidates; verify product identity, financing source, and current pricing; ask the user to approve the final capture set if it expands beyond the original scope; archive those sources; synthesize with dated citations.

**验收证据：** The candidate and verified sets are separate, every financing/price claim maps to a preserved source, and failed or stale candidates remain visible.

## 边界案例

**场景：** “保存这篇公开文章。”

**处理：** Use the known-URL archival specialist directly. Do not launch discovery, private bookmark export, or media transcription.

**验收证据：** The saved artifact opens, its source URL and retrieval time are recorded, and no unrelated account data was accessed.

### Private collection boundary

**Request:** “研究我收藏里的内容”，without naming a platform or range.

**Route:** Ask for the platform and bounded collection scope before accessing it. Explain that exporting links is distinct from opening or downloading their contents.

**Evidence:** No private collection is read before authorization; later stages receive only the approved link set.

## 失败与恢复

**场景：** One platform rate-limits the discovery query and only three of the requested ten candidates are verified.

**处理：** Preserve the query/error, try a lawful public alternative, and deliver a partial result if coverage remains insufficient.

**验收证据：** The report states 3/10 verified rather than claiming a complete ranking, and lists the smallest action that could close the gap.
