# skill-publisher

> 你已经把一个工作流沉淀成 skill，下一步最容易卡住的不是代码，而是发布：README 太像内部说明、YAML 一点点写错、仓库名发错、最后还没人验证能不能安装。
> skill-publisher turns a local agent skill into a public GitHub repo with a product-style README and real `npx skills add` verification.

**中文** | [English](#english)

## 为什么值得用

一个 skill 真正可复用，不是本地能跑就结束。

它还需要：

- GitHub 仓库能被别人找到
- README 第一眼让人想装
- `SKILL.md` frontmatter 能被严格 YAML 解析
- 安装命令一行可用
- 发布后真的能通过 `npx skills add` 发现和安装
- 本地 `.agents`、`.codex`、`.claude` 入口别互相打架

skill-publisher 把这些发布步骤打包成一个可验证流程。

## 它会做什么

- 验证 `SKILL.md` 的 `name` 和 `description`
- 用 PyYAML 做严格 frontmatter 检查
- 创建 MIT LICENSE
- 生成不带 TODO 占位符的 README 发布页
- 检查已有 README 是否还残留占位内容
- 区分 `skill name` 和 GitHub `repo name`
- 优先使用当前 git `origin` 仓库名，避免推错 repo
- 创建或更新 GitHub 公开仓库
- 跑 `npx skills add <user>/<repo> --list`
- 在临时目录真实安装一次，确认 `SKILL.md` 落盘
- 可把 skill 同步到 `~/.agents/skills/<name>` 实体目录

## 快速开始

发布一个 skill：

```bash
python3 ~/.agents/skills/skill-publisher/scripts/publish_skill.py ~/.agents/skills/my-skill
```

先检查，不发布：

```bash
python3 ~/.agents/skills/skill-publisher/scripts/publish_skill.py ~/.agents/skills/my-skill --dry-run
```

skill name 和仓库名不一致时，明确仓库名：

```bash
python3 ~/.agents/skills/skill-publisher/scripts/publish_skill.py ~/.agents/skills/my-skill --repo-name my-skill-repo --no-symlink
```

发布后用户安装：

```bash
npx skills add <user>/my-skill
```

## 你可以这样说

- “把这个 skill 发布到 GitHub。”
- “先检查这个 skill 能不能发布。”
- “重写 README，让它更吸引人，然后发布。”
- “更新 my-skill 到 GitHub，并验证可安装。”
- “这个 skill name 和 repo name 不一样，发布到 my-skill-repo。”

## 发布流程

```mermaid
flowchart LR
  A["本地 skill 目录"] --> B["验证 SKILL.md"]
  B --> C["检查 README 质量"]
  C --> D["识别 repo name"]
  D --> E["提交并推送 GitHub"]
  E --> F["npx --list 发现验证"]
  F --> G["临时目录真实安装"]
  G --> H["输出仓库和安装命令"]
```

## README 发布页标准

这个 publisher 的 README 标准来自多次真实 skill 发布与重写。

好 README 不只是“说明功能”。

它要让陌生人愿意安装。

推荐首屏：

1. 痛点：用户现在为什么难受
2. 翻转：用了这个 skill 之后有什么不同
3. 一行安装命令
4. 真实输出样例或工作流片段
5. 3-6 个具体能力点
6. 前置要求和 Troubleshooting
7. 作者、版权、风险边界

脚本会拦截这些坏味道：

- `TODO`
- `特性 1`
- `[问题 1]`
- `[解决方案]`
- `your-org`
- `your-repo`
- 未替换的 `product-screenshot.png`

## 参数

| 参数 | 说明 |
|---|---|
| `--github-user USER` | 指定 GitHub 用户名；默认优先使用当前 origin owner，否则使用 `gh api user` |
| `--repo-name NAME` | 指定 GitHub 仓库名；默认优先使用当前 origin repo，否则使用 skill name |
| `--private` | 创建私有仓库，默认公开 |
| `--dry-run` | 只检查，不发布 |
| `--skip-verify` | 跳过 `npx skills` 验证 |
| `--no-symlink` | 跳过同步 `~/.agents/skills` 实体目录 |

## 前置要求

- [ ] 已安装 GitHub CLI：`brew install gh`
- [ ] 已登录 GitHub CLI：`gh auth status`
- [ ] 已安装 Python 3.9+
- [ ] 已安装 Node.js 和 `npx`
- [ ] skill 目录包含有效 `SKILL.md`
- [ ] 发布前已检查 README 中没有密钥、私有路径、账号信息或未替换占位符

## 关键细节

### repo name 和 skill name 可以不同

例如仓库名是 `my-skill-repo`，但 `SKILL.md` 里的 name 是 `my-skill`。

脚本会优先读取当前 git `origin`，避免把更新误推到 `<user>/skill-publisher`。

必要时使用：

```bash
--repo-name my-skill-repo
```

### 验证不是只看 --list

脚本会先跑：

```bash
npx skills add <user>/<repo> --list
```

然后在临时目录真实安装：

```bash
npx skills add <user>/<repo> --skill <skill-name>
```

确认 `.agents/skills/<skill-name>/SKILL.md` 真实落盘后才算过。

### 本地同步不会自删

如果发布源目录已经是 `~/.agents/skills/<name>`，脚本会跳过同步，避免删除自己的源目录。

如果你从一个仓库名和 skill name 不一致的目录发布，并且不想产生本地副本，用：

```bash
--no-symlink
```

## Troubleshooting

| 问题 | 原因 | 解决方法 |
|---|---|---|
| `gh: command not found` | 没装 GitHub CLI | 运行 `brew install gh && gh auth login` |
| `No valid skills found` | `SKILL.md` frontmatter 不是严格 YAML | 用 `description: |` 块标量，重新发布 |
| 发布到了错误仓库 | skill name 和 repo name 混用 | 检查 `git remote -v`，或传 `--repo-name` |
| README 质量检查失败 | 还残留 TODO 或占位符 | 把 README 改成真实痛点、样例和安装说明 |
| npx 真实安装失败 | repo 可见但 skill 未正确解析或路径不对 | 先跑 `--list` 看 skill name，再检查 `SKILL.md` |
| 本地出现重复 skill | 自动同步创建了实体副本 | 下次发布用 `--no-symlink`，或清理不需要的副本 |

## License

MIT

<a name="english"></a>
## English

skill-publisher publishes a local agent skill to GitHub and verifies that it can be discovered and installed through `npx skills add`.

It focuses on:

- strict `SKILL.md` YAML validation
- attractive product-page README generation
- README placeholder checks
- repo-name and skill-name separation
- GitHub repo creation or update
- `npx skills add --list` discovery verification
- real install verification in a temporary directory
- safe local `~/.agents/skills` sync

