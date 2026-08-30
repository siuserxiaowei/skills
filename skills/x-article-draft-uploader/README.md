# x-article-draft-uploader

一个把 Obsidian 笔记或本地 Markdown 文章送进 X Articles 草稿箱的 Codex Skill。

自动化覆盖的环节：

- 取文章第一张图作为 X Article 封面
- 文章开头不是图片时默认中断，并提示先补封面图
- 把 Markdown 转成 rich text 正文
- 正文图片各自落回原文对应的位置
- 自动化跑在独立 Playwright 浏览器里，不占用用户当前的 Chrome
- X cookies 从本机 Chrome 临时导出，Skill 内部不固化任何 cookies
- 全程只保存草稿，绝不替你点击最终 `发布`

## 什么时候用它

- 想把 Obsidian 长文搬到 X Articles
- Markdown 中夹带大量本地图片
- 封面有硬性要求：必须是文章最上方的第一张图
- 缺封面时希望先被提醒，而不是让脚本擅自拿正文第一张图顶上
- 旧脚本留下过缺图、图片错位、`MPH_MARKER` 残留之类的问题
- 已经在 Chrome 里登录了 X，又不希望自动化抢走当前浏览器窗口

## 安装

把整个目录拷进 Codex 或 Claude Code 的 skills 目录即可：

```bash
cp -R x-article-draft-uploader ~/.codex/skills/
```

几个常见的 skills 目录位置：

- Codex: `~/.codex/skills/`
- Claude Code: `~/.claude/skills/`
- Agents: `~/.agents/skills/`

## 环境依赖

需要 Python 3.9+，并装好 Playwright 与 pycryptodome：

```bash
pip3 install playwright pycryptodome
python3 -m playwright install chromium
```

macOS 上还需本机装有 Chrome，且这个 Chrome 里已经登录了 X。

## 使用流程

### 1. 先导出 X cookies

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/export_x_cookies_from_chrome.py \
  --output /tmp/x_current_cookies.json
```

导出过程只会打印 cookie 的名字，值不会出现在终端里。

### 2. dry-run 预检

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/upload_markdown_to_x_article.py \
  "/absolute/path/to/article.md" \
  --cookies-json /tmp/x_current_cookies.json \
  --dry-run
```

dry-run 阶段会核对这些信息：

- 文章标题
- 封面候选图（第一张图）
- 首个有效内容是不是图片
- 正文图片总数
- 每张正文图对应的插入锚点

一旦发现文章首个有效内容不是图片，脚本会直接中断并提示先加封面图——这个阶段不会打开 X，更不会创建草稿。

如果用户明确表示不要封面、仍想上传无封面草稿，再运行：

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/upload_markdown_to_x_article.py \
  "/absolute/path/to/article.md" \
  --cookies-json /tmp/x_current_cookies.json \
  --allow-no-cover
```

带上 `--allow-no-cover` 后，封面环节被跳过，文章里所有图片一律按正文图插入。

### 3. 正式上传为新草稿

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/upload_markdown_to_x_article.py \
  "/absolute/path/to/article.md" \
  --cookies-json /tmp/x_current_cookies.json
```

跑完后查看这三个产物文件：

- `/tmp/x_article_upload_url.txt`：草稿 URL
- `/tmp/x_article_upload_result.json`：校验结果
- `/tmp/x_article_final_uploaded.png`：最终截图

## 背后做了什么

1. 解析 Markdown，拆出标题、封面候选图和正文图片。
2. 检查文章首个有效内容是否为图片；不是则默认中断上传，并提醒补封面。
3. 每张图拿它前一行的文字当 anchor，用来确定插图落点。
4. 起一个独立的 Playwright Chromium 会话，注入临时 cookies。
5. 在 X Articles 里新建草稿。
6. 上传封面并点击 X 的 `应用`（`--allow-no-cover` 模式下此步跳过）。
7. 把 rich HTML 正文粘贴进编辑器。
8. 正文图片倒序插入，这样前面的插入不会打乱后面的定位。
9. 等待 X autosave 完成。
10. 收尾校验：标题、正文开头/结尾、无 `MPH_MARKER`，媒体总数等于 `封面数 + 正文图数量`。

## 隐私与安全

- 本 Skill 不含任何真实 cookies、token、账号密码或 API key。
- cookies 仅存在于运行时导出的 `/tmp/x_current_cookies.json`。
- 用完想清理的话：

```bash
rm -f /tmp/x_current_cookies.json
```

- `/tmp/x_current_cookies.json` 以及任何真实 cookies 都不要提交进 Git。
- 脚本的默认产物只是草稿，不会把文章公开出去。

## 常见问题

### 跳到了 X 登录页

说明 cookies 已过期，重新导一次：

```bash
python3 ~/.codex/skills/x-article-draft-uploader/scripts/export_x_cookies_from_chrome.py \
  --output /tmp/x_current_cookies.json
```

还不行的话，先手动在 Chrome 里登录 X。

### 封面传完页面像被蒙住了

那是 X 弹出的媒体编辑层。必须点击 `应用`，否则 mask 会一直挡着编辑器，封面也不会真正保存。脚本已内置这一步。

### 文章开头不是图片

默认会先停下来，提醒用户加封面图。除非用户明确讲“不加封面也继续”，才会动用 `--allow-no-cover`。此时 X Article 没有封面，文中图片全部按正文图处理。

### 正文图片为什么要倒序插

X 编辑器的内容是动态重排的：先插前面的图会让后面内容的坐标全部位移，倒序插入稳定性更好。

### 会抢走我的 Chrome 吗

不会。脚本只是读取本机 Chrome 保存的 X 登录态，真正的上传发生在独立的 Playwright 浏览器里。

## 文件结构

```text
x-article-draft-uploader/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   └── examples.md
├── scripts/
│   ├── export_x_cookies_from_chrome.py
│   ├── parse_markdown.py
│   └── upload_markdown_to_x_article.py
└── tests/
    └── test_x_article_tools.py
```

## License 与归属

本目录的说明、脚本、测试和案例均为本仓库独立实现，使用仓库顶层 MIT License。X、Chrome、Playwright 与 Python 依赖是外部产品或运行环境，不属于本仓库原创内容，也不随本 Skill 分发。
