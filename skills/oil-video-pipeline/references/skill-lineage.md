# 来源审计与取舍

本文件记录创建 `oil-video-pipeline` 时实际检查过的本地 Skill。它不是把所有 Skill 的文字复制进来，而是把能跨工具复用的规则抽成主流程，把只适用于某个主机或品牌的规则放到条件分支。

## 通用视频与字幕

| 来源 | 纳入的规则 |
|---|---|
| `oil-subtitle` | 源指纹、阶段状态、证据校对、预览保存、glossary 边界、章节开关、SRT/ASS/烧录验证 |
| `oil-tone` | 事实边界、朗读自然、不要虚构评价和细节 |
| `oil-cover` | 真实帧筛选、多画幅、sidecar、逐字检查、避免历史任务污染 |
| `oil-visual` | 完整解释图与透明插画分支、短标签、原尺寸检查、精确重试 |
| `ffmpeg` / `ffmpeg-usage` | 先 ffprobe、显式 map、尽量 stream copy、编码与比例/音画同步检查 |
| `video-creator` | 固定字幕安全区、比例明确、时长总和、输出命名和片尾约束 |
| `verification-before-completion` | 完成声明必须有本次刷新验证证据 |

## ChatCut 分支

| 来源 | 只在对应主机启用的规则 |
|---|---|
| `asset-import` | 先检查已有资产，使用主机导入器，不能手写替代上传协议 |
| `transcription` | ready/error/no_audio 终态、不要忙轮询、源 transcript 修复优先于可见字幕改写 |
| `talking-head-guide` | 先决定处理类型；A-roll 先于 MG/B-roll/音乐/字幕；完整语义单元；阶段间确认 |
| `music` | 纯音乐/歌曲先分流；生成后再做剪辑和 ducking；不承诺精确节拍同步 |
| `voice` | 先查可用音色；provider/voiceId 成对使用；已有正确录音只改 transcript，不用 TTS 替换 |
| `export` | 确认 timeline/range/resolution/codec/format；记录 renderId；只在 render 完成后交付 |
| `multicam-sync` | 先发现轨道结构，再对齐、标注、验证墙钟不变量；不凭 utterance 数量判断麦克风归属 |
| `video-translation` | 区分口型同步、只译声音、只译字幕；需要付费任务时先确认处理类型和源稿 |
| `verification` | 结构证据与合成画面像素都要检查，渲染成功本身不是视觉证明 |

## Remotion 分支

| 来源 | 纳入的规则 |
|---|---|
| `remotion-best-practices` | 按任务加载 create/markup/captions/multimedia/render/studio reference，不预加载无关分支 |
| `remotion-captions` | Caption JSON、SRT 导入、毫秒时间轴、逐字高亮和空格保留 |
| `remotion-multimedia` | 在浏览器/Remotion 中读取时长、尺寸和媒体元数据 |
| `remotion-render` | 用 render/still，保存 composition 和渲染状态；透明视频单独走对应规则 |

## Xiaowei 个人品牌分支

`xiaowei-cover-system` 只在用户要求个人品牌封面时启用：本人形象、官方产品 Logo、多种用途变体、品牌色和来源记录。这些规则不强行套到普通视频封面；普通封面仍遵循 `oil-cover` 的当前素材证据边界。

## 没有纳入的内容

- 仅适用于具体 ChatCut MCP 工具的参数、Widget 标签和平台内部错误，不写进通用本地视频路径。
- 只针对生成新音乐、克隆音色或付费翻译的交互确认，不在用户未选择这些处理时触发。
- 平台发布适配器的具体选择器和浏览器实现，继续由 `video-publisher` 自己维护。

## 公开互联网审计

以下公开项目和官方文档在两轮公开网络审计中实际查看过。链接用于复核来源，不表示把第三方实现原样复制进本地 Skill。

| 公开来源 | 观察到的可复用实践 |
|---|---|
| [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) | 固定 `probe → 尽量无损编辑 → check → verify`；能力探测、结构化工具契约和交付检查 |
| [alwaysmavs/agent-skills/video-subtitle-translator](https://github.com/alwaysmavs/agent-skills/tree/main/skills/video-subtitle-translator) | 词级时间戳、保留原始转录、显示字幕重排、烧录 MP4/软字幕/sidecar 的输出分流、可恢复翻译批次 |
| [nopefallacy/vertical-video-editing-skills](https://github.com/nopefallacy/vertical-video-editing-skills) | `init → preview → lint → render → verify`、资产 manifest、每拍编辑报告、ffprobe 与抽帧验收 |
| [lainshao/video-editor](https://github.com/lainshao/video-editor) | 路由优先、不强迫全流程；渲染前的 cue plan、spec review、pre-render 三道闸门 |
| [Remotion captions reference](https://github.com/remotion-dev/skills/blob/main/skills/remotion-best-practices/remotion-captions/REFERENCE.md) | 字幕内部统一 JSON/Caption 模型：文本、毫秒起止、时间戳、置信度和可选分页 |
| [ChatCut transcription skill](https://github.com/ChatCut-Inc/agent-plugin/blob/main/claude/skills/transcription/SKILL.md) | 先确认资产和转录状态；ready/error/no_audio 终态；禁止从单个 pending 状态忙轮询 |
| [FFmpeg documentation](https://www.ffmpeg.org/ffmpeg.html) | 不使用 `-map` 时存在自动选流行为；多输入、多音轨和字幕输出需要显式选择并验证 |

## 第二轮公开互联网审计：证据、字幕规范、平台交付与音频

| 公开来源 | 实际纳入的规则或边界 |
|---|---|
| [Newuxtreme/watch-video-skill](https://github.com/Newuxtreme/watch-video-skill) | 视频理解可把 transcript 与带时间戳的 still frames 配对；本地流程只在画面时间匹配时使用它佐证字幕或镜头判断 |
| [Lum1104/video-to-skill](https://github.com/Lum1104/video-to-skill) | 视频转知识需要保留 transcript/OCR/证据与 manifest，并检查来源、链接、密钥和可分享性；本 Skill 抽成 evidence bundle 与能力快照 |
| [natyang1234/auto-edit-video-skill](https://github.com/natyang1234/auto-edit-video-skill) | 自动剪辑应有显式阶段和输出边界；只采纳“阶段化、可恢复”的流程思想，未采纳其具体命令或默认风格 |
| [W3C WAI captions](https://www.w3.org/WAI/media/av/captions/) | captions 不只转写对白，还要提供理解内容所需的说话人、音效等信息；ASR 结果必须复核，漏掉否定词可能改变含义 |
| [Section 508 captioning](https://www.section508.gov/create/captions/) | 说话人、画外声音和关键音效要有一致标记；字幕样式、对比度和可读性是独立检查项 |
| [YouTube automatic captions](https://support.google.com/youtube/answer/6373554) | 机器字幕会受噪声、重叠说话人、长静音和多语言影响；发布前必须编辑和抽样核对 |
| [YouTube subtitle file formats](https://support.google.com/youtube/answer/2734698) | SRT 适合基础文本和时间码；UTF-8、cue 分隔和音效标记应在导出检查中验证，样式/定位需求走支持相应能力的格式 |
| [YouTube recommended upload encoding](https://support.google.com/youtube/answer/1722171) | YouTube profile 核对 MP4/fast start、H.264、AAC/Opus、48 kHz、逐行、原始帧率和 BT.709；这些只属于版本化平台 profile，不当作所有平台的通用硬规则 |
| [TikTok for Business video specs](https://ads.tiktok.com/help/article/video-ads-specifications) | 广告 profile 需要单独记录 9:16、清晰度、时长/大小等限制；不把广告规格无条件套到普通自然流量视频 |
| [Meta Reels creative guidance](https://www.facebook.com/business/ads-guide/update/video/instagram-reels) | 9:16、声音和 safe zone 会影响 Reels 创意表现；本 Skill 只将其作为发布前 profile 检查，不声称一个固定算法收益 |
| [EBU R 128](https://www.ebu.ch/activities/technical/ebu-r128) | 广播型 profile 记录 -23 LUFS、LRA 和 maximum true peak；不把该目标强行套到未选择的社交平台 profile |
| [FFmpeg loudnorm filter](https://ffmpeg.org/ffmpeg-filters.html#loudnorm) | 用 `loudnorm` 做 EBU R128 单遍/双遍测量或处理，并把 integrated loudness、LRA、true peak 绑定到最终文件 |

第三方 skill 的具体默认值、脚本和平台数值可能随时间改变；本地 Skill 只固定证据链和检查结构，具体工具参数与平台限制仍需在任务当天按官方文档复核。

网络来源只用来提炼流程模式和检查边界；具体命令、版本、平台限制仍以当前本机工具和任务现场的验证结果为准。
