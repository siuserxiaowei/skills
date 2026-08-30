---
name: x-article-draft-uploader
description: 把本地 Markdown 转为经核验的 X Articles 新草稿。适用于需要保留首图封面、正文图片相对位置，并在独立 Playwright 会话中复用用户已授权 Chrome 登录态的任务；不负责公开发布。
---

# X Article Draft Uploader

这个 Skill 只创建草稿。公开发布、删除旧草稿或替换线上内容都需要用户另行明确授权。

先阅读 [references/examples.md](references/examples.md)，再按下面的安全门执行。

## 运行约束

- 只接受用户明确选择的 Markdown、Chrome profile 和输出目录。
- cookie 导出前先预览；只有带 `--apply` 才读取浏览器数据库并写出登录态。
- 上传脚本默认也只是预览；只有带 `--apply` 才访问 X 并创建草稿。
- cookie 文件可能等同于登录凭据：不得打印值、提交 Git、写进 Skill 或长期留存。
- 自动化使用独立 Chromium context，不接管用户当前 Chrome 窗口。
- 脚本没有发布动作，结果中的 `publishes` / `published` 必须始终为 `false`。

## 1. 选择并预览 cookie 导出

`--profile` 必须是 Chrome profile 的精确路径，不要自动猜测账号。

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/export_x_cookies_from_chrome.py \
  --profile "/absolute/path/to/Chrome/Profile 1" \
  --output /tmp/x-storage-state.json
```

预览应只显示路径、域名范围以及是否读取 cookie 值。确认无误后再执行：

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/export_x_cookies_from_chrome.py \
  --profile "/absolute/path/to/Chrome/Profile 1" \
  --output /tmp/x-storage-state.json \
  --apply
```

导出器只保留 `x.com` 与 `twitter.com` DNS 边界内的 cookie，并把 JSON 以 `0600` 权限原子写入。终端仅返回数量、路径和权限。

## 2. 本地预览文章计划

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/upload_markdown_to_x_article.py \
  "/absolute/path/to/article.md" \
  --cookies /tmp/x-storage-state.json
```

未加 `--apply` 时不会读取 cookie 文件、启动浏览器或创建草稿。检查 JSON 中的：

- `title`：最终标题；
- `first_content`：正文首个有效内容及其行号；
- `cover`：准备上传的封面绝对路径；
- `body_images`：正文图片顺序、源行号与锚点候选；
- `creates_draft: false`、`publishes: false`。

默认要求 Markdown 的首个有效内容是图片。用户明确接受无封面草稿时才加 `--no-cover`；该模式会把原封面候选按正文图片处理。

## 3. 创建并核验新草稿

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/upload_markdown_to_x_article.py \
  "/absolute/path/to/article.md" \
  --cookies /tmp/x-storage-state.json \
  --output "/absolute/path/to/run-output" \
  --apply
```

脚本会新建草稿、上传封面、粘贴正文、倒序插入正文图片，并验证标题、正文首尾和每次媒体计数增长。成功输出目录包含：

- `draft-url.txt`：新草稿地址；
- `result.json`：验证结果与实际锚点；
- `draft.png`：结束状态截图。

若省略 `--output`，脚本会在当前目录的 `x-article-runs/` 下生成唯一运行目录。需要后台浏览器时可加 `--headless`。

## 停止条件

遇到以下任一情况应停止并报告证据，不要在残缺草稿上继续补写：

- 登录后仍跳到 `/login`；
- 新建文章按钮或编辑器不可见；
- 封面裁剪层无法确认；
- 某张图片没有可靠锚点，或粘贴后媒体数量未增加；
- 正文开头、结尾或标题最终校验失败。

修正输入或登录态后，新建一篇干净草稿重试。完成后提醒用户妥善删除临时 storage-state 文件。

## 依赖与边界

需要 Python 3、Playwright、Chromium 和 `pycryptodome`。Chrome cookie 解密流程面向 macOS Keychain。X 页面结构可能变化；选择器失效时应先更新并测试脚本，而不是绕过验证。

本目录不包含 X、Chrome、Playwright 的代码或真实账号数据；这些名称只用于说明互操作对象。
