# Usage examples

These examples show what a user can say. The Skill expands each request with source-specific preservation facts after inspecting the image.

## Portrait

> 把这张人像做成横向复古彩铅卡片。必须还是同一个人，保留脸型、五官、发型、年龄、神态和前倾坐姿；背景换成米白手工纸，外围加少量低饱和蜡笔色块，不要文字。

Expected routing: `person` + `paper portrait` + horizontal crop. Identity and pose outrank the decorative crayon marks.

## Pet

> 把这只猫画成米白纸张上的复古彩铅卡片，保留耳朵形状、脸部花纹、白色前爪和蜷卧姿势，不要画成通用萌猫。

Expected routing: `pet` + `paper portrait`. Coat patches and anatomy are invariants.

## Mountain lake

> 把这张山湖照片转成横向莫兰迪彩铅风景卡，保留湖湾形状、右侧道路、前景深色树林和远处雾层，不增加房屋、船或太阳。

Expected routing: `landscape` + `whole-scene card`. The scene is redrawn, not removed.

## Architecture

> 把这栋老房子转换成复古彩铅卡片，锁定拍摄视角、屋顶轮廓、楼层数和门窗位置，只简化墙面纹理。

Expected routing: `architecture` + `whole-scene card`. Geometry outranks texture.

## Strict 50/50 split

> 做成竖版上下对半卡片：上半必须保留原始实拍照片，下半是米白手工纸和彩铅轮廓，两部分严格各占 50%。

Expected routing: `50/50 split card`. Generate the lower panel and composite it with the untouched source crop when pixel fidelity matters.

## Iteration language

When a result is close, correct one failure at a time:

> 保持其他内容完全不变，只修正人物眼距和下颌弧度，使其匹配图1；不要改变发型、姿势、服装、纸张和配色。

> 保持其他内容完全不变，只把湖岸恢复成图1的 S 形走向，并让右侧道路回到山坡中部；不要增加新景物。
