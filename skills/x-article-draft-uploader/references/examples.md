# X Article Draft Uploader｜使用说明与案例

## 使用说明

本 Skill 只创建新的 X Article 草稿，不发布、删除或覆盖线上内容。开始前需要用户确认 Markdown 绝对路径、精确 Chrome profile、临时 storage-state 路径和运行输出目录；Markdown 中的本地图片必须存在。Cookie 与 storage state 等同登录凭据，不能打印值、提交 Git 或长期保留。

执行顺序固定为两道预览/执行门：先预览并带 `--apply` 导出限定于 `x.com`/`twitter.com` 的 storage state；再不带 `--apply` 预览文章标题、封面和正文图片锚点。用户核对计划后才带 `--apply` 新建草稿。交付必须证明 `published=false`，并核验标题、正文首尾和每张图片的媒体计数增长。

## 正向案例

**用户请求：** “把 `/absolute/path/launch.md` 保存成 X Article 草稿；首图做封面，正文两张图保持原位置，不要发布。”

**准备信息：** 用户指明 Chrome profile `/absolute/path/Chrome/Profile 1`、临时凭据 `/private/tmp/x-storage.json` 和输出目录 `/absolute/path/x-run`；Markdown 首个有效内容为封面图，正文图片路径均可读取，当前账号有 X Articles 编辑权限。

**处理：** 先运行 cookie 导出器预览，核对 profile、输出路径和域名范围，再加 `--apply` 写出权限为 `0600` 的 storage state。运行上传器预览 `launch.md`，检查标题、封面、正文文本块及两张图的前后候选锚点；确认无误后使用相同参数加 `--apply`，让独立 Chromium context 新建草稿并逐项验证。

**预期输出：** `/absolute/path/x-run` 中包含草稿 URL、结果 JSON、运行日志和验证截图；结果记录 `cover_uploaded=true`、两张正文图的命中锚点，以及 `publishes=false` / `published=false`。

**验收证据：** 草稿页面标题和正文首尾与 Markdown 一致，封面可见，两次正文媒体计数各增长 1；脚本没有点击发布控件。storage state 未出现在终端或 Git，任务完成后按用户选择安全清理。

## 边界案例

**场景：** Markdown 以标题开头，第一张图片本应留在正文；用户明确表示草稿不需要封面。

**边界判断：** 默认规则会要求首个有效内容为封面；只有用户明确接受无封面时才能使用 `--no-cover`，而且预览和实际执行参数必须一致。

**处理：** 先用 `--no-cover` 预览文章计划，确认 `cover` 为 `null`、第一张图片出现在正文图片列表且锚点正确；向用户展示计划后，创建草稿时继续使用同一 flag。不能先按有封面预览、再在执行阶段临时改变布局。

**验收证据：** 最终结果为 `cover_uploaded=false`，原首图在预期正文段落出现且媒体计数增长；草稿仍为未发布状态，没有把图片丢弃或随意移动到文末。

## 失败与恢复

**失败场景：** 第二张图片前没有稳定文字锚点，编辑器找不到候选段落；或打开编辑器后跳回登录页面。

**处理与恢复：** 锚点失败时立即停止，不把图片插到文末，也不把半成品报告为成功；在 Markdown 中补一段唯一且稳定的相邻文字，重新预览后新建一篇干净草稿。登录失效时关闭独立浏览器，重新确认正确 Chrome profile 并导出新的 storage state；不得打印或手工复制 Cookie 值。对可能已创建的草稿先只读确认，未知状态下不盲目重跑。

**验收证据：** 失败运行保留错误、候选锚点和已完成步骤；恢复后的结果能记录实际可见段落与媒体计数增长，新的凭据文件权限为 `0600`。如果旧草稿状态无法确认，报告明确标记 unknown，不自动删除或发布任何草稿。
