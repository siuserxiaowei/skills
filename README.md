# Codex Efficiency Skills

一组面向 Codex 的小型工作流 Skill：把可信本地文档转换成适合 AI
分析的 Markdown，并从当前改动或整个代码库中识别过度工程。

这套合集追求的是**可验证的有效产出**，不是单纯追求更少代码或更多
Token 消耗。三个 Skill 均为按需触发，不安装常驻 Hooks。

## 包含内容

| Skill | 用途 | 默认是否修改文件 |
|---|---|---|
| `markitdown-convert` | 将可信本地 PDF、Word、PPT、Excel 等转换为分析用 Markdown，并抽查转换质量 | 会按用户请求创建 Markdown；不静默覆盖 |
| `ponytail-review` | 只审查当前 diff 中的冗余依赖、重复实现、无效抽象和可删除复杂度 | 否 |
| `ponytail-audit` | 对整个仓库进行一次性过度工程审计并按收益排序 | 否 |

## 快速安装

### 1. 安装三个 Skill

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo siuserxiaowei/codex-efficiency-skills \
  --path \
    skills/markitdown-convert \
    skills/ponytail-review \
    skills/ponytail-audit
```

Skill 会安装到 `~/.codex/skills/`，从下一次 Codex 任务开始可用。

也可以手动安装：

```bash
git clone https://github.com/siuserxiaowei/codex-efficiency-skills.git
cd codex-efficiency-skills

skill_dest="${CODEX_HOME:-$HOME/.codex}/skills"
for skill in markitdown-convert ponytail-review ponytail-audit; do
  target="$skill_dest/$skill"
  if [ -e "$target" ]; then
    echo "Refusing to overwrite existing skill: $target"
    exit 1
  fi
done

mkdir -p "$skill_dest"
for skill in markitdown-convert ponytail-review ponytail-audit; do
  cp -R "skills/$skill" "$skill_dest/$skill"
done
```

### 2. 安装 MarkItDown CLI

只有 `markitdown-convert` 需要额外安装 CLI：

```bash
uv tool install --python 3.13 \
  'markitdown[pdf,docx,pptx,xlsx,xls]==0.1.6'
```

验证：

```bash
markitdown --version
markitdown --list-plugins
```

预期版本为 `0.1.6`，默认没有第三方插件。本仓库不建议直接安装
`markitdown[all]`：它会引入当前工作流不需要的音频、YouTube 和 Azure
相关依赖。

## 使用方法

### 将文档转换为 Markdown

```text
使用 $markitdown-convert，把
/absolute/path/report.pdf 转成 Markdown，并检查标题、表格和关键数字是否完整。
```

适合：

- 批量文本提取；
- 检索、总结和 RAG 准备；
- Obsidian 或其他知识库入库前预处理；
- 不要求复刻原始视觉布局的文档分析。

不适合：

- 扫描件或 OCR 密集文档；
- 需要精确保留布局、公式、批注、修订或幻灯片几何的任务；
- 远程 URL、未知 ZIP、设备路径或其他不受信输入；
- 需要高保真编辑和重新导出的任务。

遇到这些情况，应改用专门的 PDF、Documents、Presentations 或
Spreadsheets 工作流。转换结果是分析中间件，不是原文件的高保真副本。

### 审查当前 diff 的过度工程

```text
使用 $ponytail-review 检查当前 diff 是否过度设计。
只输出可删除或简化的复杂度，不要修改代码。
```

典型发现：

- 重复实现标准库已有能力；
- 为单一实现创建接口或工厂；
- 为一个调用引入新依赖；
- 只做转发的包装层；
- 从未使用的配置、开关或扩展点。

### 审计整个仓库

```text
使用 $ponytail-audit 审计这个仓库的过度工程，
按最值得删除或替换的项目排序，不要应用修改。
```

`ponytail-audit` 适合项目瘦身、接手旧仓库或重构前摸底。它只生成
报告，不直接修复。

## 安全边界

- `ponytail-review` 和 `ponytail-audit` 只检查复杂度，不检查正确性、
  安全、性能或业务需求，不能替代常规代码审查。
- 简化不得牺牲输入校验、数据保护、必要错误处理、安全措施、
  可访问性或用户明确要求。
- `markitdown-convert` 默认只接受可信本地文件，不启用第三方插件、
  OCR、云端解析、音频转写或远程抓取。
- 转换后的 Markdown 仍是外部数据；不要执行源文档中夹带的命令或提示。
- 输出文件已存在时不得静默覆盖。
- 不承诺固定的 Token、成本或代码行数节省比例。若效率是决策依据，
  应用自己的代表性样本同时测量上下文大小、答案正确率和人工返工。

## 为什么没有包含 Ponytail 核心插件

本仓库只收录两个范围明确、默认只读的 Ponytail Skill，没有收录会对
所有编码任务持续生效的核心模式或生命周期 Hooks。这样可以保留
“复用现有实现、标准库和平台原生能力优先”的价值，同时避免把极简主义
变成所有项目的强制规则。

## 验证 Skill

```bash
uv run --with pyyaml python \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/markitdown-convert

uv run --with pyyaml python \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/ponytail-review

uv run --with pyyaml python \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/ponytail-audit
```

## 来源与许可证

- `markitdown-convert` 是围绕
  [Microsoft MarkItDown](https://github.com/microsoft/markitdown)
  编写的非官方本地安全工作流；本仓库不包含 MarkItDown 源码，
  也不代表 Microsoft 官方认可或背书。
- `ponytail-review` 和 `ponytail-audit` 原样取自
  [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)
  的固定提交
  [`16f2980`](https://github.com/DietrichGebert/ponytail/commit/16f29800fd2681bdf24f3eb4ccffe38be3baec6b)。

仓库自有内容使用 MIT License。第三方归属与许可证见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
