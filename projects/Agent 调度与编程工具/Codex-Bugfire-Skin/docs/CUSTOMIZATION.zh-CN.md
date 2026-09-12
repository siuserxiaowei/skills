# 制作自己的 BUGFIRE 桌宠包

## 最少上传什么？

只需要两张图和几行文字；`init` 只创建清单与 `assets/` 目录，不会生成、下载或上传图片：

1. `background.png`：Codex 首页横幅和任务背景，建议横向、宽度 2000 px 以上、左侧留出安静区域。
2. `pet-idle.png`：你的宠物主形象，推荐正方形透明 PNG、角色完整、轮廓清楚。
3. 包名称、宠物名称，以及你确认拥有素材使用权。

可选再上传五张透明宠物图：

| 文件 | 状态 | 画面建议 |
|---|---|---|
| `pet-building.png` | 构建中 | 敲键盘、扫描、蓄力 |
| `pet-bug.png` | 发现 Bug | 惊讶、警报、错误姿势 |
| `pet-fire.png` | 修复动作 | 喷火、攻击、施法、打补丁 |
| `pet-success.png` | Build 成功 | 庆祝、跳跃、亮灯 |
| `pet-level-up.png` | 升级 | 进化、发光、穿戴新装备 |

没有提供的状态会复用 `pet-idle.png`，因此两张图就能跑完整系统。

## 生成与验证

```bash
cd skills/codex-bugfire-customizer
node scripts/create-pack.mjs init /绝对路径/我的桌宠素材

# 把图片放入“我的桌宠素材/assets/”，编辑 bugfire-pack.json 后：
node scripts/create-pack.mjs validate /绝对路径/我的桌宠素材
node scripts/create-pack.mjs build /绝对路径/我的桌宠素材 /绝对路径/我的桌宠成品
node scripts/create-pack.mjs preview /绝对路径/我的桌宠成品 /绝对路径/preview.html
```

`validate` 会检查图片真实性、大小、路径穿越、字段、颜色、任务规则和素材权利声明。`build` 只复制清单声明的本地素材，并输出 `pack-report.json`。

素材限制：

| 内容 | 格式与限制 |
|---|---|
| `bugfire-pack.json` | 最大 128 KiB，`schemaVersion: 1`，拒绝未声明字段 |
| 背景 | PNG/JPEG/WebP，最大 16 MiB、8192 px 单边、32 Mi 像素 |
| 单张宠物图 | PNG/JPEG/WebP，最大 4 MiB、4096 px 单边、8 Mi 像素 |
| 宠物图合计 | 最大 16 MiB |

APNG、动画 WebP、SVG、GIF、扩展名与内容不符、作为清单/素材文件的符号链接、越出素材包的父目录链接和远程素材都会被拒绝。编译器使用同一文件句柄完成校验与读取，Build 直接写入已经验证的字节，不会在校验后重新打开源素材。

## 可定制内容

- 工作台背景与九色主题令牌
- 宠物名称、赛季名称、1–12 条互动台词
- 六种宠物状态图
- 1–5 条本地任务，指标限于 XP、等级、失败次数、成功次数和修复次数
- 每次修复成功的 XP（1–100）
- 成长纪念卡标题

五级 XP 阈值和技能表固定，宠物包不能把本地娱乐进度改写成能力评分。

等级阈值目前保持统一，以保证存档校验、升级卡和跨包行为可预测。切换到不同 `id` 或 `seasonId` 时，会把旧存档归档为 `.previous...` 文件并创建新的 Lv2 体验存档；不同宠物包的进度不会自动合并。

## 安装

从仓库根目录执行：

```bash
macos/scripts/install-bugfire-pack-macos.sh \
  --pack /绝对路径/我的桌宠素材 \
  --no-apply
```

去掉 `--no-apply` 会尝试热应用；若 Codex 没有打开已验证的调试会话，激活流程可能正常关闭并重新打开 Codex 一次。安装与恢复都不会修改官方 `.app` 或 `app.asar`。

`--no-apply` 只把包放进本地主题库，不改活动主题或进度。正式激活会先停止身份匹配的旧 watcher，把完整主题复制到同一文件系统的临时目录并再次校验，再用原子重命名切换；失败时恢复旧主题。

直接使用编译器的 `build <source> <output> --replace` 时，`--replace` 会清空已有输出目录。源码包和编译输出必须使用不同且互不嵌套的目录；编译器会拒绝重叠路径。

## 分享

分享编译后的成品目录或 ZIP。不要分享原始工作区、进度 JSON、日志、认证文件、私人任务截图或本机绝对路径。使用他人角色/IP/照片前，请确认许可、肖像权与商标边界。
