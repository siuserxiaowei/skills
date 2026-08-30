# macOS 微信双开｜验收案例

这是可逆但非官方的本地副本方案。原应用始终只读；复制、改语言、改图标、签名与启动是不同变更。

## 使用说明

- **何时使用：** 用户明确要在 macOS 上创建、检查、修复、启动或区分第二个本地 WeChat app bundle。
- **准备/输入：** 官方 source、全新 target、不同 bundle ID、语言/图标选择及每类变更的单独授权。
- **执行方式：** `plan`/`status` 先行，确认后才对副本 create/repair/recolor/launch，并重新签名和状态验证。
- **验收/边界：** source 不变、target identifier/signature/进程路径不同且双窗口可见；不覆盖、不注入、不降系统安全、不替用户登录。

## 正向案例

### 创建蓝色图标的第二实例

- **用户请求：** “给我做一个蓝色图标的 WeChat-2，原微信不能受影响。”
- **准备信息/输入：** macOS 上存在官方 `/Applications/WeChat.app`；用户确认新的 target、bundle identifier 和语言；target 当前不存在；改色还需要 Pillow 与 `iconutil`。
- **处理：** 运行 `python3 <script> plan`，记录 source/target、版本、原 identifier、签名和 mutation list；用户确认后执行 `python3 <script> create --apply`；再单独预览/确认并执行 `python3 <script> recolor-icon --color '#2878d0' --apply`；最后运行 `python3 <script> launch --apply` 与 `python3 <script> status`。
- **预期输出：** 原应用不变；副本使用不同 identifier、蓝色图标和独立可辨认窗口，两个实例可并存。
- **验收证据：** source 前后版本/identifier/签名不变，target 的不同 identifier，`codesign --verify --deep --strict <target>` 成功，预览 PNG、两个进程的不同 executable path 和可见双窗口。

## 边界案例

### 目标已存在或要求安装注入器

- **用户请求：** “原来的 WeChat-Second.app 直接覆盖；不行就装个注入插件。”
- **边界判断：** target 已存在，覆盖会丢失可回退副本；注入器不在允许路线。
- **处理：** 只运行 `status`/`plan` 检查现有副本；让用户在修复、使用新目标名或可恢复归档之间选择。未经单独批准不移动旧副本；绝不覆盖、不装 injector、不修改原可执行文件、不关闭 Gatekeeper、不索取管理员权限。
- **预期输出：** 现有 target 与 source 都保持不变，给出精确可选路线。
- **验收证据：** `target_exists`、状态/签名报告、零 create/repair/recolor/launch mutation 和无第三方二进制。

## 失败与恢复

### 更新后副本无法启动

- **场景：** 官方 WeChat 已升级，旧副本版本落后或签名/identifier 元数据损坏。
- **处理与恢复：** 先比较 source/target 版本和 `status`。文件完整但元数据错误时，展示 `repair` 计划后由用户确认 `python3 <script> repair --apply`；版本落后时，在新 target 路径从当前官方应用创建新副本，验证双开后再让用户决定是否归档旧副本，不合并 app bundle。
- **预期输出：** 恢复以新副本或最小修复完成，原应用和旧回退副本不被破坏。
- **验收证据：** 版本/签名对比、repair/create 计划、最终 status/codesign/双窗口结果，以及仍存在的通知与未来更新不确定性。
