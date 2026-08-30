# Lark Drive｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。来源与目标必须先解析为 canonical token；示例中的 token 和 URL 仅表示参数位置。

## 使用说明

- **何时使用：** 需要移动/传输文件、轮询 Drive 异步任务或区分位置与权限控制面时读取。
- **准备/输入：** 确认来源/目标 URL 与 token、type、父目录、profile/identity、同名策略及权限/版本基线。
- **执行方式：** 先 inspect 与 dry-run，执行一次后按 task ID 和目标 folder 清单回读同一 token。
- **验收/边界：** 以 token、父目录、任务终态和权限基线验收；move 不包含 copy、delete、公开或所有权转移。

## 正向案例

### 把一份文档移动到确定文件夹

- **用户请求：** “把这份《Q3 复盘》移动到‘项目归档/2026’，不要复制，也不要改权限。”
- **准备信息/输入：** 已提供来源文档 URL 和目标文件夹 URL；profile/identity 已固定；来源唯一且类型为 docx；目标 folder token 唯一；已记录当前父级和成员/公开权限基线。
- **处理：**

```bash
lark-cli drive +inspect --profile work --as user --url '<source_url>' --format json
lark-cli drive +inspect --profile work --as user --url '<target_folder_url>' --format json
lark-cli drive +move --profile work --as user --file-token <source_token> --folder-token <target_folder_token> --type docx --dry-run --format json
```

预览确认来源 token、标题、类型和目标 folder 后执行一次：

```bash
lark-cli drive +move --profile work --as user --file-token <source_token> --folder-token <target_folder_token> --type docx --format json
lark-cli drive files list --profile work --as user --folder-token <target_folder_token> --page-all --page-limit 10 --format json
```

若 move 返回异步 task ID，再查询同一任务：

```bash
lark-cli drive +task_result --profile work --as user --scenario task_check --task-id <task_id> --format json
```

- **预期输出：** 同一 `source_token` 出现在目标文件夹，动作是 move 而非 copy。
- **验收证据：** 目标列表包含同一 token/title/type；异步任务到达成功终态；权限基线没有被单独修改；不存在新副本 token。

## 边界案例

### 移动不授权删除、公开或所有权转移

- **用户请求：** “归档完顺便删掉旧版本并设为公开，方便大家看。”
- **边界判断：** move 改变位置，版本删除改变恢复能力，public permission 改变受众；三者不能共用一次模糊确认。
- **处理：** 把移动、版本删除和公开权限拆开。移动可以按原请求执行；版本删除和 public permission 必须先展示版本、受众、恢复能力并分别确认，不能把“方便”当授权。
- **验收证据：** 用户未确认额外动作时，文件位置变化但版本历史、成员权限、public 设置和 secure label 保持不变。

## 失败与恢复

### 移动结果未知或目标同名

- **场景：** 服务端返回 task ID 后超时，或目标目录已有同名文件。
- **处理与恢复：** 轮询原 task ID，并按目标 folder 列表核对 token；同名只作为提示，不能自动复制/改名。未知状态不再发 move。
- **验收证据：** 同一 token 位于目标即视为已移动；仍在源且任务明确失败才可重新计划；无法确定时报告 task ID、两个父目录的查询结果和残余风险。目标目录不能出现由恢复动作生成的第二个 token。
