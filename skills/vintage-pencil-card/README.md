# Vintage Pencil Card｜复古彩铅卡片

把人物、宠物、风景、建筑或静物照片转换成**构图保真**的复古彩铅卡片：先锁定“必须像”的内容，再叠加米白手工纸、莫兰迪彩铅、蜡笔和 Risograph 颗粒。

## 它解决什么问题

普通的“改成彩铅风”很容易得到漂亮但不相像的人、另一处风景或变形的建筑。这个 Skill 会先判断照片类型，再选择不同的保真规则：

- 人物：锁定身份、真实五官、年龄、发型、体态和姿势；
- 宠物：锁定脸部比例、耳朵、毛色花纹和动作；
- 风景：锁定地平线、山体、河湖或道路走向、前中后景与光线；
- 建筑：锁定视角、透视、体块、楼层和门窗；
- 静物：锁定数量、轮廓、比例、遮挡关系和功能结构。

它支持全画面彩铅、人物纸张肖像、完整风景卡和上下严格 50/50 的“实拍 + 手绘”卡片。

## 安装

一行安装：

```bash
npx skills add siuserxiaowei/skills --skill vintage-pencil-card
```

或手动复制：

```bash
git clone https://github.com/siuserxiaowei/skills.git
cp -R skills/skills/vintage-pencil-card ~/.codex/skills/
```

## 怎么使用

上传至少一张照片，然后直接说目标。图片较多时，按下面分工最稳定：

1. 图1：主体照片，决定人物、姿势、场景和构图。
2. 图2（可选）：五官、毛色或产品细节近景，只锁定细节。
3. 图3（可选）：只参考纸张、笔触、颜色和留白，不复制其中的人物和动作。

### 人像

```text
用 $vintage-pencil-card 把这张人像做成横向复古彩铅卡片。
必须还是同一个人，保留脸型、五官、发型、年龄、神态和前倾坐姿；
背景换成米白手工纸，外围加少量低饱和蜡笔色块，不要文字。
```

### 风景

```text
用 $vintage-pencil-card 把这张山湖照片转成横向莫兰迪彩铅风景卡。
保留湖湾形状、右侧道路、前景深色树林和远处雾层；
不要增加房屋、船、人物或太阳。
```

### 上下对半卡片

```text
用 $vintage-pencil-card 做成竖版上下对半卡片：
上半保留原始实拍照片，下半是米白手工纸和彩铅轮廓，严格各占 50%。
```

当上半照片必须像素级不变时，Skill 会建议单独生成下半部分，再做确定性拼接；单次生成式改图无法保证原照片每个像素不变。

## 案例与验收

仓库不再捆绑第三方照片或由其生成的衍生图。可复现的人像、风景、建筑与严格 50/50 案例见 [references/examples.md](references/examples.md)：每个案例都列出用户请求、处理决策、保留项和验收标准。运行案例时使用用户自己的图片或已确认可使用的素材。

## 需要什么

- 能读取参考图片并支持图片编辑的 Agent 或图像模型；
- 至少一张清晰的主体照片；
- 人像高度保真时，建议补一张清晰五官近景作为图2；
- 精确文字排版建议在生成图片后单独完成。

## 常见问题

| 问题 | 处理方式 |
|---|---|
| 人物变成“通用漂亮脸” | 补五官近景，并明确眼型、眼距、下颌、发际线、鼻口位置和年龄；强调身份优先于风格。 |
| 风景很好看但像另一个地方 | 明确地平线高度、水体或道路路径、主要地形相对位置和前景锚点；禁止反转和新增景物。 |
| 建筑门窗或透视变形 | 写清楼层数、开口数量和对齐关系；要求只简化纹理，不改变几何。 |
| 风格参考把人物和姿势带进来了 | 把图3限定为“只参考纸张、笔触、配色和留白”，禁止复制主体与构图。 |
| 文字拼错 | 默认不在生成阶段写字；后期排版，或只使用一条很短的精确文案。 |

## 限制

- 生成式模型无法保证像素级身份、手部、文字或建筑几何完全一致；Skill 通过保真清单和单点迭代降低偏差，但不会把概率生成伪装成确定性复制。
- 低清、严重遮挡或极端透视的人像，最好补充细节参考图。
- 严格 50/50 和“上半照片完全不改”应使用确定性合成工具完成最后拼接。
- 不要使用无权公开或无权改编的照片制作公开案例。

---

## English

Vintage Pencil Card turns portrait, pet, landscape, architecture, and still-life photos into composition-faithful colored-pencil stationery art. It assigns explicit roles to multiple references, applies subject-specific preservation rules, and verifies identity or scene topology before accepting the style transfer.

Install:

```bash
npx skills add siuserxiaowei/skills --skill vintage-pencil-card
```

Example:

```text
Use $vintage-pencil-card to turn this mountain-lake photo into a horizontal vintage colored-pencil card. Preserve the shoreline, road, foreground trees, fog layers, and light direction. Do not add buildings, boats, people, or a sun.
```

See [SKILL.md](SKILL.md) for the workflow, [references/prompt-template.md](references/prompt-template.md) for the prompt scaffold, and [references/preservation-rules.md](references/preservation-rules.md) for subject-specific invariants.
