# Changelog

## 1.3.0-bugfire.1 — 2026-08-31

### 新增

- 加入真实 `OpenAI-compatible` 角色导演 CLI：从原创 brief 生成结构化创意草案，支持 Chat Completions 与 Responses 两种 API 形态
- 加入 checksum 锁定的离线 AI fixture；明确标注它不是实时 API 调用，也不是人工审批证明
- 加入强制人工拒绝/替换门：至少实质修改一项创意决定，且替换字段必须与被拒决定一致
- 加入 `materialize` 边界报告：AI 只提案，人工改动后，仍必须由既有 deterministic pack validator 决定是否可构建
- 加入原创 `Patchling Zero｜零号补丁兽` 演示 brief、矢量源素材、可复现终端 Demo、离线预览与 VibeLab 投稿包

### 安全与证据

- API Key 只从环境变量读取，不接受命令行 secret，也不会写入 plan、日志或产物
- 远程模型端点必须使用 HTTPS；仅本机 `127.0.0.1` / `localhost` / `::1` 测试或本地模型允许 HTTP
- brief、review、fixture 与 AI response 采用 fatal UTF-8 解码，拒绝非法字节而不是静默替换
- draft、review 与 materialize 输出使用随机 `wx` 暂存文件和原子 no-clobber 提交，已有目标会原样保留并拒绝覆盖
- 自动化测试会启动 loopback mock endpoint，证明 live 路径确实发起 HTTP 请求，并校验凭据没有进入输出
- 对 AI 响应与最终 plan 做递归精确凭据扫描；恶意端点回显 API Key 时在落盘前拒绝，错误信息也不回显 Key
- `manifestProposal.rights` 强制从已校验的人工 brief 派生，AI 不能覆盖素材权利声明
- `materialize` 会重建 canonical AI draft 并严格校验 `humanReview.draftSha256`，同时拒绝调用方可控输出路径中的 symlink 祖先
- Character Director 纳入 lines / branches / functions 均 80% 的独立覆盖率门禁；测试路径改用 `fileURLToPath`，支持含空格与中文的 Client ZIP 解包目录
- 保持既有 loopback-only CDP、官方应用不修改、Build 仅演示与一键恢复边界

## 1.2.0-bugfire.1 — 2026-07-16

### 新增

- 加入 `Bugfire Pack v1` 编译与校验工具：最小背景 + 宠物两图即可生成可移植桌宠包
- 支持六状态宠物素材、点击台词、本地任务板、自定义主题色和成长纪念卡标题
- 加入 `codex-bugfire-customizer` Skill、离线预览、安装脚本与端到端测试

### 安全

- 拒绝目录穿越、symlink、伪图片、远程素材、非法字段和超大素材
- 校验 PNG/JPEG/WebP 的真实帧尺寸与像素上限，拒绝 APNG、动画 WebP、画布尺寸伪装和多帧 WebP
- 同一宠物图被多个状态复用时只计数并编码一次，避免 6 倍 payload
- 宠物包名称以数据而非 AppleScript 源码传给系统通知，阻止元数据注入
- 主题先完整暂存并校验，再原子切换；失败自动恢复旧主题
- 任务仅从现有本地聚合数派生，不读取任务正文、源码、文件名、项目名或 Shell 输出

### 桌宠体验

- 加入 BUGFIRE「补丁兽」桌宠舱，保留 Codex 原生侧栏、任务区和输入框交互
- 加入 Build 失败 → 修复重建 → 喷火升级的本地演示流程与五级 Vibe 成长体系
- 加入成长卡、赛季纪念证书与 PNG 导出；所有证书均明确标注为非官方个人纪念卡
- 通过已验证的 CDP Runtime binding 将进度原子保存到 Application Support，不新增网络端口

### 安全与可用性

- 支持 Escape 收起、任务页自动收起、窄窗口和 `prefers-reduced-motion`
- Restore 会移除全部 BUGFIRE DOM、样式和监听器，不修改官方 `.app`、`app.asar` 或代码签名

## 1.1.2 — 2026-07-16

### 修复

- 修正内置主题引用了未随仓库发布的背景文件，恢复使用 bundled abstract demo 素材
- 更新主题配置往返测试：安装只备份外观键，不再错误断言强制切换深色模式
- 恢复原本没有 `[desktop]` 配置段的用户设置时，不再额外写入空段

---

## 1.1.1 — 2026-07-16

### 修复

- 不再用 `launchctl submit` 托管带调试口的 Codex：退出 SwiftBar / 关掉 Codex 后不应再被 launchd 自动拉起
- 暂停与完全恢复时清理 `com.openai.codex-dream-skin-studio.app` 作业

---

## 1.1.0 — 2026-07-16

### 新增

- SwiftBar 菜单栏入口（`Install Menu Bar.command`）：应用 / 暂停 / 换图 / 切换已保存主题 / 从图片文件夹加载 / 完全恢复
- 主题库（`themes/`）与图片投放目录（`images/`）动态加载，不再把 README 图库合成图当背景素材
- 按 Codex 应用浅色 / 深色自动切换皮肤壳（`data-dream-shell`）

### 改进

- CDP 已就绪时热切换主题（重启 injector + 短时注入），换图更快
- 注入校验放宽（项目选择器等可选），避免误杀已生效皮肤
- 注入守护优先 `nohup`；暂停状态与路径大小写下停止逻辑更稳
- 安装时不再强制 `appearanceTheme=dark`，只备份桌面外观相关键，便于恢复与自动适配

### 视觉

- 以原版暗色 portal CSS 为结构底，叠加 light 壳与更薄横幅遮罩，减轻「换图看不清」
- 历史上游曾附带人物示例横幅；BUGFIRE 独立扩展不再保留或宣传该素材

### 说明

- 历史上游图库仅作记录；BUGFIRE 对外素材统一使用原创补丁龙与脱敏截图

---

## 1.0.0 — 2026-07-15

- 发布 macOS 通用主题制作器，而不是固定角色皮肤。
- 加入 Finder 选图、自动 JPEG 转换、主题命名和高级配色参数。
- 主页使用独立横幅，任务页使用背景与磨砂层，完整保留原生交互。
- 改为复用并验证 Codex 官方签名 Node.js，不再附带大型运行时或依赖全局 Node。
- 增加独立安装目录、桌面启动/定制/验证/恢复入口。
- 增加官方签名、CDP 端口归属、PID 身份、刷新重注入和真实 DOM 自检。
- 增加原子配置备份、精确恢复、静态测试、安装恢复循环和发布打包脚本。
- 清理固定角色内部命名；传送门主题仅作为可替换示例素材。
- 开源树：示例横幅改为无角色抽象几何图；验收截图不入库；补充 NOTICE / README 商标与安全边界说明。
