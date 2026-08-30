# x-article-draft-uploader

一个面向 X Articles 的 Markdown 草稿工具。它把首图作为封面、按原文位置安排正文图片，并把自动化限制在独立 Playwright 会话中。

## 安全模型

- 两个有副作用的阶段都要求显式 `--apply`。
- cookie 导出必须指定 Chrome profile，只读取 `x.com` / `twitter.com` 范围。
- cookie 值不会写到终端，输出 JSON 使用 `0600` 权限。
- 上传器只新建草稿，没有公开发布逻辑。
- 默认要求文章首个有效内容是图片；`--no-cover` 只能用于用户明确接受无封面时。

## 依赖

```bash
python3 -m pip install playwright pycryptodome
python3 -m playwright install chromium
```

cookie 解密目前面向 macOS Chrome 与 Keychain。

## 快速使用

先确认将要读取的 profile 与输出路径：

```bash
python3 scripts/export_x_cookies_from_chrome.py \
  --profile "/absolute/path/to/Chrome/Profile 1" \
  --output /tmp/x-storage-state.json
```

确认后导出：

```bash
python3 scripts/export_x_cookies_from_chrome.py \
  --profile "/absolute/path/to/Chrome/Profile 1" \
  --output /tmp/x-storage-state.json \
  --apply
```

文章计划预览不会读取 cookie 内容或打开浏览器：

```bash
python3 scripts/upload_markdown_to_x_article.py article.md \
  --cookies /tmp/x-storage-state.json
```

检查标题、封面、正文图片和锚点后，再创建草稿：

```bash
python3 scripts/upload_markdown_to_x_article.py article.md \
  --cookies /tmp/x-storage-state.json \
  --output ./x-article-run \
  --apply
```

成功运行会生成 `draft-url.txt`、`result.json` 和 `draft.png`。任何登录、锚点、媒体计数或正文首尾校验失败都会中止；修复后应创建新草稿重试。

完整决策规则见 [SKILL.md](SKILL.md)，示例见 [references/examples.md](references/examples.md)。
