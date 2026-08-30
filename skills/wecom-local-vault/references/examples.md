# 验收案例

## 正向案例

**用户请求：** Export one project room for a stated week.

**处理：** Record the selected dataset label, create a new snapshot, resolve the room unambiguously, apply both time bounds, and export to a new private file.

**验收证据：** The run has a manifest and message count, all outputs are owner-only, and source database metadata is unchanged.

## 边界案例

**场景：** The user asks whether local data is discoverable but has not authorized process attachment.

**处理：** Run discovery, status, and doctor only. A capture command without its confirmation flag must stop before importing Frida or touching a process.

**验收证据：** No process was attached, spawned, signed, or read; the report names the missing permission precisely.

### Multiple accounts

If discovery returns several opaque labels, ask the user to choose or provide an exact `--data-dir`. Do not guess based on contact contents. Capture and decrypt must bind the verified key record to the same dataset label.

## 失败与恢复

**场景：** Headers, schema, or the known memory layout no longer match.

**处理：** Preserve the read-only inspection result and stop. Update fixtures and compatibility logic before handling the live data; do not reinterpret unknown columns as people or message bodies.

**验收证据：** The failure identifies the unsupported boundary, no plaintext claim is made, and a fixture-based compatibility test is required before retry.
