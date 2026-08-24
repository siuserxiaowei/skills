# Wigolo 可选外部适配合同

本适配器只把用户已经独立安装的 Wigolo 原生单文件发行镜像当作 Python 控制面的可选外部进程。它不是第四套引擎，不进入 `engine_mode`，也不复制、链接、修改或自动安装 Wigolo 源码与二进制。

审计基线为 `KnockOutEZ/wigolo` commit `c6ad4479da7706945b479786df0121e3cce1ece6`、package `0.2.1`、`AGPL-3.0-only`。版本门禁只允许 `0.2.x`，但这不是可执行兼容性声明：Adapter 只接受兼容当前主机、通过 ELF、Mach-O/FAT 或 PE magic 白名单，且 SHA-256 已经源码冻结在 `AUDITED_NATIVE_RELEASE_SHA256` 的原生单文件镜像；调用方、环境和请求都不能扩展该集合。JavaScript、Node/npm CLI、`.js/.mjs/.cjs`、所有 shebang/解释型脚本、无后缀包装器，以及任意未审计或重命名的原生程序都在外部 probe 前失败关闭。当前白名单为空；标准 npm `wigolo@0.2.1` 是 Node/npm 发行物，因此明确 No-go，当前没有生产执行路线。未来只有上游提供兼容的原生单文件发行镜像，并重新通过来源、发行摘要、入口完整性、真实 probe、CLI 合同、能力与许可证审计后，才能由代码更新加入白名单。

## v2/v3 四份合同

- [wigolo-request.schema.json](../assets/engine-contracts/wigolo-request.schema.json)：显式、typed、只读请求。
- [wigolo-probe.schema.json](../assets/engine-contracts/wigolo-probe.schema.json)：带 SHA-256 完整性摘要的 dispatch-only 探针；摘要本身不是认证签名，只有被 HMAC 计划绑定后才具有认证链路，不声称实时网络路线已可用。
- [wigolo-plan.schema.json](../assets/engine-contracts/wigolo-plan.schema.json)：绑定 request、probe、可执行文件 SHA-256、固定 argv 与权限策略，并由 HMAC-SHA256 认证的不可变计划。
- [wigolo-result.schema.json](../assets/engine-contracts/wigolo-result.schema.json)：强制 HMAC-SHA256 认证、严格归一化且没有证据/curator 权限的结果。

正确流程是 `probe → plan → execute HMAC-authenticated plan`：

```bash
python3 scripts/wigolo_adapter.py probe --command /absolute/path/to/wigolo
umask 077
openssl rand 32 > /path/wigolo-auth.key
python3 scripts/wigolo_adapter.py plan --input /path/request.json --command /absolute/path/to/wigolo --auth-key-file /path/wigolo-auth.key > /path/plan.json
python3 scripts/wigolo_adapter.py execute --plan /path/plan.json --auth-key-file /path/wigolo-auth.key
```

跨进程 CLI 的 `plan` 与 `execute` 必须使用同一 owner-only 密钥文件：当前用户持有、权限不宽于 `0600`、32–4096 bytes。密钥只由 Adapter 读取，不写入 plan/result、不进入 Wigolo argv 或子进程环境；计划保存非秘密 key ID 与 HMAC，执行用 `compare_digest` 验证。因此攻击者即使替换 executable、重算公开 SHA-256 和固定 argv，也不能在没有密钥时重新认证计划。

`probe`、`plan` 和 `execute` 都先绑定最终入口；命令定位符可以是 symlink，但计划只保存解析后的最终目标。Adapter 安全打开该目标后，从同一文件描述符执行 `fstat`、原生 magic/主机兼容性校验、SHA-256 计算与 owner-only 私有快照复制，再只运行验证后的快照，不回退到原路径。这样封闭“按路径校验后、打开前被替换”的竞态，也阻止脚本从入口路径继续加载任意外部源码。

`execute` 不接受 request 或 `--command`，不重新 probe、不重新规划。它先重验 plan HMAC、plan/request digest、probe identity、argv、authority policy 与绑定入口 SHA-256；再从新打开的同一 FD 重验类型、magic、主机兼容性与摘要，复制并执行新的私有快照。特殊文件、脚本、非原生镜像、入口漂移或权限异常都在启动子进程前失败。库内同进程兼容 API 使用进程随机临时密钥；需要跨进程、落盘或跨信任边界时必须显式使用 key file。

这是入口文件完整性边界，不是“完全静态/自包含”证明：Mach-O/ELF/PE 仍可能由系统动态加载器装载共享库、框架或系统组件；这些属于受信主机平台边界。本 Adapter 不解析、复制或声称验证任意原生程序的完整运行时依赖图。

## 启用与探针边界

- 默认 `enabled=false`；只有 `enabled=true` 且 `selection_mode=explicit` 才可能规划，`auto` 永远拒绝。
- 不执行 `node/npx/npm/pnpm/bun/bunx/yarn` 或任何脚本解释器，不提供 install、upgrade、init、doctor `--fix`、serve、research、agent、crawl 或任意 shell 路线。
- `probe` 先完成原生单文件 FD 校验、SHA-256 发行白名单与私有快照，门禁失败时不得调用外部 runner。通过后才在临时隔离目录对快照运行 `doctor --json` 与四个 dispatch 探针。search/fetch 用无必需参数的 typed error 验证命令分派但不发网；cache/watch 只走本地 `stats/list`。
- `dispatch_ready=true` 只证明经审计 CLI 面存在；`live_route_ready` 固定为 `false`。实际路线仍需当前请求执行结果、来源 outcome 与后续证据门禁。
- 标准 npm `wigolo@0.2.1` 必须在 probe 前返回 `backend_not_ready`；原生测试 fixture 只通过测试内注入的临时摘要运行，其 dispatch 绿灯不能证明 Wigolo 生产兼容。生产白名单为空，因此 `wigolo_mode=external` 没有执行路线；添加未来摘要属于代码与供应链审计变更，不是运行时配置。

## 固定只读面

适配器不接受自由 argv、headers、身份、认证参数或任意 flag：

| operation | 固定关键 argv | 语义 |
|---|---|---|
| `discovery` | `search QUERY ... --no-content --no-cache --json` | 只发现候选；最多 50；输出固定 `discovery_only` |
| `fetch` | `fetch URL --render-js=never --force-refresh ... --json` | 仅公开 HTTP(S)，不复用 cache/浏览器/登录态；正文仍不是 accepted evidence |
| `cache` | `cache stats` 或 `cache search QUERY --mode=fts ... --json` | 只读统计/词法检索；禁止 clear、embedding、change check |
| `watch` | `watch list --json` | 仅列出；禁止 add/delete/pause/resume/check/run 与 webhook |

查询或自由文本不能以 `-` 开头。URL 预检拒绝凭据、localhost、本地域名和显式私网/loopback/link-local/reserved IP；这是词法第一层，不替代解析后 SSRF 防护，因此高敏感或不受信目标不交给本适配器。

CJK 默认拒绝；只有请求显式 `allow_experimental_cjk=true` 才计划，并始终保留 `experimental_cjk_enabled` 警告。它不能替代中文平台原生适配器或登录接力。

## 进程与输出隔离

所有子进程使用 argv 数组、`shell=False`、有界超时。环境从 allowlist 重建，只透传必要 locale/TLS/path 项；未知环境变量、token 与代理配置不会继承。每次 probe/execute 都使用独立临时 `HOME` 和 `WIGOLO_DATA_DIR`，并固定透明自有 UA `TopFiftyWigoloAdapter/2.1 (+https://github.com/siuserxiaowei/skills)`、`RESPECT_ROBOTS_TXT=true`。

环境强制关闭 hardcore、TLS impersonation、stealth、humanize、CDP、浏览器 profile/auth state、challenge/CAPTCHA solver、hosted reader/browser、proxy bypass、private target、cloud/local LLM、keyed search providers、遥测、browser prewarm 与 reranker 懒加载。

外部 JSON 被当作不可信数据并按 operation 严格白名单归一化；所有 v3 结果（包括失败诊断）都必须携带 HMAC，删除认证字段后重算公开摘要仍会失败：

- discovery 必须有非空结果、查询守恒、结果数不超过 HMAC 认证计划所绑定请求的 `max_results`、公开 URL、有限分数与无重复 URL；所有候选固定 `evidence_status=discovery_only`、`curator_accepted=false`。
- fetch 必须声明 `fetch_method=http`、`cached=false`、非空正文与公开 URL；输出固定 `evidence_status=discovery_only`、`render_js=never`。
- cache/watch 只保留合同字段，不把未知字段透传。
- 空白/未知对象、非 JSON、非零退出、重复或越权字段、任意嵌套层级出现的 `solve_method`、challenge、browser/TLS fetch、`escalated=true`、第三方 crawler UA 等均失败关闭并丢弃数据。

Wigolo 的搜索结果、正文或 cache 记录都不是事实真值。进入榜单前仍须经过本 Skill 的来源合同、日期核验、提取、去重、证据卡与独立 curator；适配器自身的 authority 固定为 `none`。

## 许可证与升级

本项目只通过公开 CLI JSON 与用户独立安装的进程交互，并记录 `license=AGPL-3.0-only`、`integration_boundary=separate_process`。这不是法律意见；分发、修改、嵌入或网络化提供 Wigolo 时需单独履行 AGPL 与商标义务。

升级前重新核对版本/JSON 合同、许可证、安装副作用、持久化状态、重定向/SSRF/robots/UA、challenge ladder、cache/watch 副作用与 CJK 质量；任一门禁未关闭就保持 disabled。
