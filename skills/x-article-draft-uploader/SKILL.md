---
name: x-article-draft-uploader
description: 将 Obsidian 或本地 Markdown 文章上传为 X/Twitter Articles 草稿：自动以第一张图作为封面，正文图片全部按原文位置插入。适用于用户要求上传、发布、保存 Markdown 到 X Article 时，特别是需要复用 Chrome 登录态、使用独立 Playwright 浏览器而不接管用户当前浏览器、封面必须是最上方图片，或旧脚本出现缺图、错位、MPH_MARKER 等残留的情况。
---

# X Article Draft Uploader

## 两条不可违反的原则

- 本 Skill 的产物只有草稿。在没有得到用户明确同意公开发布之前，绝不能替用户点下 X 上最终的 `发布` 按钮。
- 自动化全程运行在一个独立的 Playwright 浏览器会话中，不得抢占用户正在操作的 Chrome 窗口。Chrome 的登录态可以复用，但唯一合法的方式是先临时导出成 Playwright cookie JSON，再注入到这个独立会话里。

## 三步上手

### 第 1 步：导出 X 的登录 cookies

当 `/tmp/x_current_cookies.json` 不存在，或登录态已经失效时，先重新导出一份：

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/export_x_cookies_from_chrome.py --output /tmp/x_current_cookies.json
```

### 第 2 步：dry-run 预检

真正访问 X 之前，先用 dry-run 模式解析文章，核对封面、正文图片数量和每一处插入锚点：

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/upload_markdown_to_x_article.py \
  "/absolute/path/to/article.md" \
  --cookies-json /tmp/x_current_cookies.json \
  --dry-run
```

一旦 dry-run 提示“文章第一个有效内容不是图片”，必须中止流程并告知用户：最好在文章开头补一张封面图，此时不要继续上传。仅当用户明确表示不加封面、仍坚持上传无封面草稿时，才追加 `--allow-no-cover`：

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/upload_markdown_to_x_article.py \
  "/absolute/path/to/article.md" \
  --cookies-json /tmp/x_current_cookies.json \
  --allow-no-cover
```

### 第 3 步：创建全新草稿并上传

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/upload_markdown_to_x_article.py \
  "/absolute/path/to/article.md" \
  --cookies-json /tmp/x_current_cookies.json
```

上传完成后，可以在这些位置找到产物：

- 草稿 URL 写在 `/tmp/x_article_upload_url.txt`
- 校验数据（JSON）写在 `/tmp/x_article_upload_result.json`
- 上传后的整页截图存在 `/tmp/x_article_final_uploaded.png`

## 完整执行链路

1. 调用本 Skill 内置的 `scripts/parse_markdown.py` 完成 Markdown 解析。
2. 确认文章首个有效内容是图片；若不是，默认直接中断，并建议用户先补封面。只有用户明确放弃封面且要求继续时，才用 `--allow-no-cover` 跳过封面环节。
3. 位于文章最上方的第一张图即封面。一旦启用 `--allow-no-cover`，则不再上传封面，文中全部图片一律视为正文图。
4. 每张正文图的插入锚点取它在原始 Markdown 中的上一行。遇到列表要格外小心：锚点要用真实的那一行，例如 `Git 变化。`，而不是把前面若干列表项拼接出来的更长 fallback。
5. 新开一个干净的 Playwright Chromium context，注入 X cookies。
6. 访问 `https://x.com/compose/articles`，点击 `create`，记下跳转后新生成的 `/compose/articles/edit/...` 地址。
7. 经由封面区域的 file input 上传封面，随后必须点击 X 的 `应用`。漏掉这一步，X 会残留 media-edit mask 盖住编辑器，封面也不会真正保存下来。
8. 写入标题，再把 rich HTML 正文粘贴进 `[data-testid="composer"]`。
9. 正文图按从后往前的顺序插入，每张图固定走这套动作：
   - 在当前编辑器里定位优先级最高的 anchor；
   - 点击该段落的结尾处；
   - 依次按下 `End`、`Enter`；
   - 通过 clipboard paste event 把图片文件贴进去；
   - 等到页面中检测到的 media count 确实增加，再处理下一张。
10. 等待 X autosave 落盘，随后做整体校验：标题一致、正文开头/结尾完整、不存在 `MPH_MARKER`，且媒体总数等于 `封面数 + expected_image_count`。

## 排障速查

- 页面跳到 `/login`：登录态已失效，重新导出 cookies 即可。
- 文章开头不是图片：默认不会继续上传，先提醒用户补封面；用户明确拒绝后，再带 `--allow-no-cover` 重跑。
- 封面传完编辑器被一层遮罩盖住：说明 `应用` 没点，找到该按钮并点击。
- 正文图片千万不要走隐藏的 file input 上传——那个 input 可能连着封面上传器，会把封面顶掉。
- 媒体数量达标不代表万事大吉。紧跟在列表后面的图片尤其要核对 anchor 是否命中；结果 JSON 里的 `anchor_used` 与 `expected_anchor` 就是用来对账的。
- 某次运行只成功了一半、图片位置又不对：另起一篇干净草稿重跑，别在失败的旧草稿上缝缝补补。

## 关于脚本的几个事实

- `upload_markdown_to_x_article.py --dry-run` 纯粹是预检，全程不会打开 X。
- `--allow-no-cover` 的启用前提只有一个：用户明确说不要封面。它的行为是跳过封面上传，并把文章里所有图片都按正文图插入。
- 上传脚本依赖 Python Playwright，以及一份有效的 X cookie JSON。
- Markdown 解析器已经随本 Skill 自带，不再需要旧的 `x-article-publisher` Skill。
- cookie 导出脚本只读取本机 Chrome 里的 cookies，并写入你指定的临时 Playwright cookie 文件；Skill 自身不留存任何 cookie。
