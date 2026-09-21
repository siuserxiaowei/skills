# 质量闸门

按阶段保存结果。error 阻止进入下一阶段；warning 必须记录并在交付时提示；pass 只表示该项检查已完成，不代表语义和审美已经自动证明。

## 源文件与任务身份

| 检查 | 级别 | 证据 |
|---|---|---|
| 路径、大小、修改时间、SHA-256 与任务记录一致 | error | source.json |
| 视频轨道、音轨、时长可读取 | error | FFprobe/doctor 输出 |
| 已有字幕、封面、旧任务与当前源文件同源 | error | 文件指纹或明确人工确认 |
| 任务目录没有把个人凭据、个人词库或视频提交进公共仓库 | error | 路径检查/版本控制检查 |
| 能力快照记录 FFmpeg、编码器、字体、OCR/转录 provider 和磁盘状态 | error | task.json capabilities |
| 屏幕录制或画面语义任务有 transcript 与带时间戳的抽帧证据 | warning | evidence/ 索引 |

## 转录与字幕

| 检查 | 级别 | 证据 |
|---|---|---|
| text 非空，时间轴单调且在视频时长内 | error | captions.json 质检 |
| 相邻字幕不重叠，块数和顺序稳定 | error | 结构检查 |
| 每处 Agent 改词有证据索引 | error | review-evidence.json |
| 低置信度、专有名词、数字和命令已回听或标记 | warning | 复核清单 |
| 显示少于 0.65 秒 | warning | duration check |
| 每秒视觉字宽过高 | warning | CJK=1、拉丁字符=0.5 的经验计数 |
| 横屏单行超过 28、竖屏超过 16 个视觉字宽 | warning | layout check |
| 字幕遮住脸、关键界面或平台水印 | error | 开头/中段/结尾截图检查 |
| caption profile 与实际内容一致；captions profile 的说话人/关键音效标记完整 | error | captionProfile 与抽样截图 |
| 字幕文件为 UTF-8，cue 编号、空行和时间码可被目标播放器读取 | error | 编码检查/播放器 |
| ASR 低置信度、否定词、专有名词和说话人已抽样回听 | warning | review-evidence.json |

## 导出视频

| 检查 | 级别 | 证据 |
|---|---|---|
| MP4 可被播放器打开，视频和音频轨道存在 | error | 播放器或 FFprobe |
| 输出时长与源视频一致，允许仅由编码造成的极小误差 | error | verification.json |
| 开头、中段、结尾音画同步 | error | 实际试听/观看 |
| ASS 字体、字号、描边、底边距与任务选项一致 | warning | 截图和配置 |
| 章节只在满足时长条件时出现，关闭选项没有残留章节 | error | 视频检查 |
| 启用音频 profile 时记录 integrated loudness、LRA 和 maximum true peak | error | audio-measurement.json |
| 最终导出音频没有削波，声音在音乐下仍可懂 | error | 试听与测量 |
| 启用 YouTube profile 时验证 fast start、codec、48 kHz、帧率、逐行和 BT.709 | error | ffprobe/format check |

## 封面

| 检查 | 级别 | 证据 |
|---|---|---|
| 3:4、4:3、16:9 文件存在且尺寸正确 | error | 图片尺寸 |
| 主标题来自当前素材，逐字无错 | error | 标题对照 |
| 真实参考帧和产品标识来自当前视频/用户素材 | error | cover/analysis.json |
| 文字在目标显示尺寸可读，未被裁切 | error | 原尺寸和缩略图检查 |
| prompt、分析、生成响应和成品有 sidecar | warning | cover/ 目录 |

## 平台草稿

| 检查 | 级别 | 证据 |
|---|---|---|
| 草稿身份与任务、源视频和目标平台绑定 | error | 平台 task-space/receipt |
| 标题、简介、话题/标签读回值与交付清单一致 | error | 独立 verify |
| 封面 receipt 与画幅、文件指纹一致 | error | receipt |
| 浏览器输入通道可用且没有并发写入 | error | runner 状态 |
| 最终发布控件未点击且仍受 final guard 保护 | error | 安全检查 |
| 平台 profile 有版本、来源和检查日期 | error | platformProfiles/ 与 delivery.json |
| B-roll、音乐、Logo 和字体有来源/授权备注 | warning | asset manifest |

## 复核抽样

至少看三段：开头 10–20 秒、中间一个完整语义段、结尾 10–20 秒。长视频再抽查每个章节的第一条和最后一条字幕。若自动质检与试听结论冲突，以真实试听和画面为准，并把差异记录到 quality.json。

屏幕录制或多语义镜头再看章节起止帧和所有 OCR 命中帧；抽帧只证明画面当时出现过文字，不能单独证明口播读法。
