# Agent Memory examples

## 正向案例

**用户请求：** “给两个编码 Agent 建一个共用记忆库，但不要把聊天记录自动存进去。”

**处理：** Define a Markdown record contract, one canonical private root, separate host adapters, and rebuildable indexes. Enable writes only for user-approved distilled records.

**验收证据：** Each host resolves the same root and retrieves a synthetic record by ID and text; raw chat content and secrets are absent from the repository and index export.

## 失败与恢复

**场景：** “文件已经改了，但搜索还返回旧内容。”

**处理：** Compare the source record hash with catalog and index hashes. Rebuild derived state in a disposable location before replacing the stale index.

**验收证据：** The new query returns the current record, the old phrase no longer matches, and the Markdown source has the same hash before and after repair.

## 边界案例

**场景：** “把这个记忆目录直接推到公开 GitHub。”

**处理：** Stop before pushing. Show the exact target, staged files, sensitive-data findings, attachment rights, and a sanitized-template option. Public visibility requires separate authorization.

**验收证据：** No remote mutation occurs until confirmed; the proposed public package contains only fake examples and excludes private records, databases, logs, caches, and credentials.

### Recover from competing writers

**Request:** “两个 Agent 同时写完后，一部分内容丢了。”

**Decision:** Freeze new writes, identify active claims and the last common record hashes, then reconcile only the affected records. Do not rebuild indexes until canonical Markdown is resolved.

**Evidence:** Conflicts remain visible until decided, every reconciled record has a source and status, and a concurrent synthetic test no longer merges unrelated writes.
