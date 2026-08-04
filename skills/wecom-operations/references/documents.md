# 企微文档与智能文档

## 命令与 URL 对照

| URL | 类型 | 命令 |
|---|---|---|
| `/doc/*` | 普通文档 | `wecom-cli doc create_doc/get_doc_content/edit_doc_content` |
| `/smartpage/*` | 智能文档 | `wecom-cli doc +smartpage_create/smartpage_export_task` |
| `/sheet/*` | 在线表格 | `wecom-cli doc sheet_*` |
| `/smartsheet/*` | 智能表格 | `wecom-cli doc smartsheet_*` |

动手前先跑 `wecom-cli doc --help`，实际可用的工具以本次动态输出为准。

## 由 Markdown 生成智能文档

首选入口是 `scripts/create_smartpage.py`：默认 dry-run 预检，只有附加 `--execute` 才真正写入企微。

### 纯文本 Markdown

脚本内部直接调用：

```bash
wecom-cli doc +smartpage_create '{"title":"标题","pages":[{"page_title":"正文","content_type":1,"page_filepath":"/absolute/report.md"}]}'
```

单个 Markdown 文件的大小上限为 10MB。

### 带本地图片的流程

官方 `+smartpage_create` 只读取 Markdown 文本本身，相对路径的本地图片不会被上传，`data:` 内联图片也会被企微侧过滤。正确顺序固定为：

1. 先建一个与最终文档同名的“图片资源”普通文档；
2. 借助本机 `+doc_upload_image` helper 把本地图片逐一传到该文档；
3. 把 Markdown 里的图片引用替换为返回的企微 `https://wdcdn.qpic.cn/...` 链接；
4. 基于改写后的私密上传副本生成最终智能文档；
5. 回执以 `0600` 权限落盘，最终文档与图片资源文档都要向用户披露。

证据图片不允许公开托管，也不要回头再试 `data:` 方案。

## 覆写普通文档正文

`edit_doc_content` 属于整篇替换。执行前必须先 `get_doc_content` 回读现有内容并核实目标无误；回读都因权限失败时，覆写同样禁止。

## 回读校验智能文档

1. 用 `smartpage_export_task` 提交导出任务；
2. 用 `smartpage_get_export_result` 轮询，直到 `task_done=true`；
3. 只有回读跑通之后，才能宣称正文已验证。

返回 `851008 partial no authorization` 说明机器人缺少“获取成员文档内容”的授权：按接口要求的帮助文字原样展示后停止回读，不要改用浏览器或客户端去补看。

## 隐私要点

- 文档 URL 可以当作本次交付链接给用户，但不许沉淀进共享记忆。
- docid、图片 CDN 映射、上传副本只能落在私密本机目录。
- 源 Markdown 保持原样不动；一切路径替换只作用于上传副本。
