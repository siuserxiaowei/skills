# Skill Publisher｜使用说明与案例

## 使用说明

发布前先解析五个对象：要发布的 Skill 集合、确切 Git 工作树/commit、目标 `OWNER/REPO`、可见性与授权动作。检查许可证、秘密、符号链接、子模块、二进制、生成物、当前分支、未提交改动和远端差异；预检只读，不会因为用户说“检查一下”就自动创建仓库、提交、推送或发布 Release。

可从仓库根目录运行：

```bash
python3 skills/skill-publisher/scripts/preflight.py . \
  --visibility public \
  --target OWNER/REPO \
  --fail-on blocker
```

只有 blocker 清零、warning 已逐条判定、用户授权目标与可见性后才能发布。交付必须用远端 commit、标签/Release（如有）、干净克隆安装和目标 Agent 实际发现结果证明成功。

## 正向案例

**用户请求：** “把 `/absolute/path/my-skill` 发布到新的私有仓库 `acme/my-skill`，提交后帮我验证能安装。”

**准备信息：** 用户确认仓库名、私有可见性、默认分支和本轮允许创建仓库/提交/推送；本地 Skill 是精确目标，当前 GitHub 身份对 `acme` 有权限。尚未授权公开发布或创建 Release。

**处理：** 先以 `--visibility private --target acme/my-skill` 运行预检，展示文件/哈希/许可证/秘密和 Git 边界；解决 blocker 并解释 warning。确认暂存集合后创建一次聚焦提交，创建或绑定目标远端并推送。随后在全新临时目录克隆目标 commit，按实际 Agent 安装路径复制，运行 `quick_validate.py` 并检查 Skill 能被发现。

**预期输出：** 私有仓库包含已审定的文件和单一明确 commit；发布说明列出远端 URL、branch、SHA、预检结果和隔离安装结果，不包含未授权的 Release 或 public visibility。

**验收证据：** `git ls-remote` 与干净克隆的 HEAD 等于报告 SHA；克隆目录无额外本地文件，结构校验通过，目标 Agent 能读取名称和 description；本地无关改动没有被提交。

## 边界案例

**场景：** 用户只说“看看这个 Skill 能不能公开”，工作树里同时有 `.env`、用户私有案例和未提交的其他项目改动。

**边界判断：** 这是只读评估，不是公开发布授权；`.gitignore` 不能证明秘密未进入历史，工作树中的无关改动也不属于候选发布集合。

**处理：** 精确列出 blocker、候选文件和目标可见性风险，检查 Git 历史/暂存集合与敏感模式，提供删除私密材料、改用合成案例或保持私有的方案。停止在发布计划，不执行 `gh repo create`、commit、push 或 Release。

**验收证据：** 远端状态没有变化；报告能指出每个敏感文件的位置及建议处置，清楚写明“可整改后复检”而不是“已发布”。

## 失败与恢复

**失败场景：** 本地 push 返回网络错误，但远端可能已经接收 commit，重跑有造成重复标签或错误 Release 的风险。

**处理与恢复：** 不立即重复发布。先用 `git ls-remote`、目标分支和 Release/标签只读查询确认远端真实状态：若 SHA 已存在，继续做干净克隆验证；若未存在，保留本地 commit 并给出精确重试命令；若状态仍未知，明确标记 blocked/unknown，等待网络恢复后再查。

**验收证据：** 最终报告包含本地 SHA、远端观察值和查询时间；没有因为命令退出非零就误报失败，也没有在未知状态下创建第二个标签、覆盖分支或宣布成功。
