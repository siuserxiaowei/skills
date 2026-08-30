# 微信公众号批量导出｜验收案例

先区分公开 URL、账号历史和增强指标三条路线。高权限路线不能因为“更完整”而成为默认。

## 使用说明

- **何时使用：** 归档有限公开 URL，或在账号所有者授权下规范化历史和增强指标。
- **准备/输入：** 明确路线、有限输入、全新私有输出、用途；高权限路线还需用户亲自登录和经核验的外部 exporter。
- **执行方式：** doctor 与 preview 先行，只有确认后添加 `--apply`；正文、原始 history 与 normalized records 分层保存。
- **验收/边界：** URL/文章/发布组/原创口径分开对账，失败和 unknown 明示；不控制客户端、不收凭证、不改代理/证书、不授予转载权。

## 正向案例

### 归档已知公开 URL

- **用户请求：** “把 `urls.txt` 里的 40 篇公开文章保存为 Markdown，供本地分析。”
- **准备信息/输入：** 输入是有限、已知的公开文章 URL；用户给出全新的私有输出目录；不需要账号历史、阅读量或评论。
- **处理：** 运行 `python3 <skill-dir>/scripts/doctor.py`；随后用 `python3 <skill-dir>/scripts/download_urls.py --file /absolute/path/urls.txt --format markdown` 预览去重后的 URL 数、API base 和格式；核对后才运行同一命令并添加 `--output /absolute/path/archive-run --apply`。完成后检查 `index.csv`、`failures.json` 与代表性正文。
- **预期输出：** 每个成功 URL 对应可追溯正文；失败项单列；输出目录不含凭证。
- **验收证据：** 输入/去重/成功/失败计数、源 URL、retrieval time、`index.csv` 对账、样本文档和输出目录敏感信息扫描。

## 边界案例

### 要求后台指标和公开再分发

- **用户请求：** “顺便抓阅读量和评论，登录你自己处理，然后把归档公开发布。”
- **边界判断：** 指标需要账号所有者授权；登录、证书/代理选择与公开再分发均未获授权。
- **处理：** 保持公开 URL 路线；说明增强字段需要用户亲自完成官方/外部 exporter 的 QR 登录、账号选择和可能的证书/代理决定。`start_wxdown_service.py` 先不带 `--apply` 展示项目、解释器、入口、端口和代理环境；公开发布是独立版权/隐私决策，不作为导出副作用。
- **预期输出：** 不控制微信客户端、不保存凭证、不改变系统代理、不公开分发。
- **验收证据：** 只读 doctor/preview 输出、未使用 `--apply` 的 helper 计划、无 cookie/auth-key/token 文件和无发布动作。

## 失败与恢复

### 增强字段缺失或批次部分失败

- **场景：** 100 篇历史中正文成功 94 篇，6 篇失败；阅读/评论字段只覆盖部分记录。
- **处理与恢复：** 保留成功正文与原始 exporter 结果；在 normalized record 中把缺失字段记为 `unknown` 并附错误，不填 0。按 URL/文章标识记录失败，只有明确瞬时且幂等的下载可有限重试；凭证过期则停在人工重新登录门，不重复启动多个 helper。
- **预期输出：** 部分归档可用但不宣称完整，统计不把 unknown 当零。
- **验收证据：** `failures.json`、字段 availability、94/6 对账、publish group/expanded article/marked-original 各自口径和下一次安全重试条件。
