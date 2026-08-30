# Lark Docs｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。`docs` 命令要求先读取与当前 CLI 同版本的内置指南；示例刻意把这一步写进流程。

## 使用说明

- **何时使用：** 需要块级编辑、选择 XML/Markdown、处理 Wiki token 或 revision 冲突时读取。
- **准备/输入：** 确认 canonical doc token、目标 block/唯一选择器、revision、内容格式、本地相对文件和不变区域。
- **执行方式：** 先用 CLI 内置指南与 fetch 获取块树/基线，再 dry-run 最小修改，写后重新 fetch 并按需视觉检查。
- **验收/边界：** 用 revision、block ID、局部 diff 和相邻块验收；选择器不唯一时停止，局部编辑不自动升级为 overwrite。

## 正向案例

### 只替换一个确定的结论段落

- **用户请求：** “把这份文档‘结论’标题下的第一段替换成 `changes/conclusion.md`，其他块不要动。”
- **准备信息/输入：** 已提供 docx/wiki URL；解析后得到 canonical doc token；目标段落只有一个 block；本地文件位于工作区；当前 revision 和相邻 block 已读取。
- **处理：**

```bash
lark-cli skills read lark-doc references/lark-doc-fetch.md
lark-cli docs +fetch --profile work --as user --doc '<doc_url>' --scope outline --detail with-ids --doc-format markdown --format json
lark-cli docs +fetch --profile work --as user --doc '<doc_url>' --scope section --start-block-id <heading_block_id> --detail with-ids --doc-format markdown --format json
lark-cli skills read lark-doc references/lark-doc-update.md
lark-cli skills read lark-doc references/lark-doc-md.md
lark-cli docs +update --profile work --as user --doc '<doc_url>' --command block_replace --block-id <paragraph_block_id> --content @changes/conclusion.md --doc-format markdown --revision-id <revision_id> --dry-run --format json
```

核对只替换目标 block、内容和 revision 后执行一次，再回读目标及相邻结构：

```bash
lark-cli docs +update --profile work --as user --doc '<doc_url>' --command block_replace --block-id <paragraph_block_id> --content @changes/conclusion.md --doc-format markdown --revision-id <revision_id> --format json
lark-cli docs +fetch --profile work --as user --doc '<doc_url>' --scope section --start-block-id <heading_block_id> --detail with-ids --doc-format markdown --format json
```

- **预期输出：** 目标段落变为本地内容，文档 revision 前进；标题、相邻块和其他章节保留。
- **验收证据：** 写前/写后 revision、目标 block ID、内容 diff 和相邻 block ID 可对账；必要的视觉打开检查通过；权限与媒体资源未改变。

## 边界案例

### 不能把“改一段”升级为全文覆盖

- **用户请求：** “结论标题有两处，你看着改，实在不行就覆盖全文。”
- **边界判断：** 两个标题使选择器不唯一；全文 overwrite 会覆盖所有块、引用和嵌入对象，远超局部段落修改的影响范围。
- **处理：** 两处命中时停止并给出标题路径、块 ID 与上下文；全文 overwrite 是不同影响范围，不能作为自动降级。共享权限、评论和 Wiki 移动也不由正文编辑授权。
- **验收证据：** 未选择唯一目标前 revision 不变；没有执行 overwrite、delete 或 Drive 权限写操作。

## 失败与恢复

### revision 冲突

- **场景：** dry-run 后他人编辑了文档，写操作返回 revision 冲突。
- **处理与恢复：** 用 `+fetch` 重新读取当前 section 和新 revision，制作“旧基线 / 用户期望 / 当前远端”三方差异；若仍可无冲突局部应用，再向用户展示新预览。禁止把 `--revision-id` 改为 `-1` 强行覆盖。
- **验收证据：** 冲突期间无额外写入；新计划明确保留他人改动，或交付无法安全自动合并的具体块和文本。
