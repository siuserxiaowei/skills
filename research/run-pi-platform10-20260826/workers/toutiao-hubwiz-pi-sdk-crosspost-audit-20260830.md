# Toutiao ↔ Hubwiz Pi SDK cross-post comparison (2026-08-30)

本报告是只读比较证据，不修改 `candidates.json`、`review_queue.json`、任何
ledger 或候选分片。比较对象：

- Toutiao canonical：<https://www.toutiao.com/article/7673696349073818147/>
- Hubwiz canonical：<https://www.hubwiz.com/blog/agent-engineering-pi-sdk/>

## 访问与可见元数据

两页均在普通匿名浏览器中成功渲染完整正文（未登录、未互动、未下载、未绕过
安全检查）。Toutiao 页面显示标题 **智能体工程：Pi SDK**、作者 **新缸中之脑**、
时间 **2026-08-14 09:41**；页面 `og:url` 为 Toutiao URL，文章末尾有指向 Hubwiz
canonical 的链接，文字为 **原文链接：智能体工程：Pi SDK - 汇智网**。Hubwiz 页面
显示同标题、站点作者 **admin**、**Aug 13, 2026**、3 min read；`article:published_time`
为 **2026-08-13T13:52:11.000Z**，canonical/`og:url` 为 Hubwiz URL，文章末尾明确写
**原文链接：Agent engineering: Pi SDK**、**汇智网翻译整理，转载请标明出处**，
并链接原始作者页 `https://roman.pt/posts/pi-sdk-version/`。这组来源标注直接证明
Hubwiz 是翻译/整理页，而 Toutiao 是转载入口。

## 正文哈希与长度

为避免把站点导航、评论和推荐内容混入正文，分别取 Toutiao `article.innerText` 与
Hubwiz `.gh-content.innerText`：

| page | raw body chars | normalized body chars | raw SHA-256 | normalized SHA-256 |
|---|---:|---:|---|---|
| Toutiao article | 3210 | 2832 | `7e331c9664119c99b01a920625a4d05eb34437566ba974d55678e6cb9b906d6f` | `c6a85fd16abd0cff266028dac36ecaf1b577b9d3f0f8d9ec019c236bb2c3fa67` |
| Hubwiz `.gh-content` | 3267 (content section) | 2995 | `3bb5e9729967b6b21abc15e36efb041e09020b056562eb2269766587c60bedea` | `1b10ffd2e3cde2588722013c22ff8f241337eb288ff9a95d30d672efd9576f17` |

另取页面中去除 Hubwiz 顶部站点推广 blockquote 后的正文，Hubwiz 仍保留同一篇原文的
3267 字符主内容；Toutiao 与 Hubwiz 的两段 TypeScript code block 分别为 924 和
903 字符，且各自 SHA-256 完全相同：

- block 1：`d08458c6559570fa801944b031ab23867eabd0d5fbdb2f82abeecd7832866b19`
- block 2：`5b7cb03b310478e1166df4d2872d26cd57a272b3caa5865533722edf1c395cab`

## 正文级重叠结果

NFKC、大小写、标点和空白规范化后，Toutiao 422 token、Hubwiz 452 token；共享
连续 shingle 数及覆盖率如下（A=Toutiao，B=Hubwiz）：

| shingle | A total | B total | shared | A coverage | B coverage |
|---:|---:|---:|---:|---:|---:|
| 5-token | 418 | 448 | 413 | 98.80% | 92.19% |
| 8-token | 415 | 445 | 410 | 98.80% | 92.13% |
| 12-token | 411 | 441 | 406 | 98.78% | 92.06% |
| 20-token | 403 | 433 | 398 | 98.76% | 91.92% |

逐段比较（去除站点推广和页首元数据）得到 Toutiao 14 个正文段、Hubwiz 11 个长
正文段，其中 10 个段落规范化后完全相等，且两页的 924/903 字符代码块逐字哈希
一致。共享内容从开场“上一篇文章…Pi 的 CLI…”、`defineTool()` 示例、
`DefaultResourceLoader`/`createAgentSession`/`session.subscribe` 代码，到 SDK 对照
表和“什么时候用 SDK 而不是 CLI”结尾，顺序和措辞均一致。差异主要是：Hubwiz
增加站点推广/导航、英文原文署名与翻译声明；Toutiao 去掉这些并以自己的标题栏、
作者和发布时间包装。规范化字符位置同序前缀只有 4.7%（因 Toutiao 页首直接从正文
开始、Hubwiz 有不同包装），但 shingle/段落结果说明这不是独立改写。

## 判定

**判定：exact/trivial cross-post（同一原文的转载/翻译整理），不是独立改写。**

推荐内容簇处理：将 Toutiao 7673696349073818147 与 Hubwiz
`agent-engineering-pi-sdk`、以及其明确指向的原始作者页
`roman.pt/posts/pi-sdk-version/` 归入同一内容簇；保留最接近原始作者的代表（若
原始作者页可审计），不要把 Toutiao 与 Hubwiz 当作两个独立 quota 对象。现有
Toutiao 规则已将该页标为“明确归因的 Pi SDK syndication”，本次正文级比较支持
这一既有排除结论。无需新增 candidate，也不应因 Toutiao 的不同作者/日期包装而晋级。

## 可复现命令/方法说明

正文通过浏览器可见 DOM 读取；规范化为 Unicode NFKC、去除标点、折叠空白后按
5/8/12/20-token 连续 shingle 计算集合交集和双向覆盖率。原始哈希采用 UTF-8
`SHA-256(innerText)`。本报告只保存结果和定位信息，不保存任何登录态、Cookie 或
页面外部敏感数据。
