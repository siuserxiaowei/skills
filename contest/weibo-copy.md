# 微博投稿文案草案

#微博VibeLab# #VibeWork#

【Goal Compiler｜需求编译器】

“给我做个 AI 网站，越快越好”——问题不是 Prompt 不够长，而是没人定义：什么叫成功？什么证据会推翻它？什么时候应该停？

我把它做成了一条可运行的编译链：

1. Agent/Skill 做 Smart Router 和 Strategy Gate，产出默认假设、成功指标、反证、kill criteria、工具/证据门禁与第一步。
2. 我故意把成功指标写成“好看”，validator 真实 FAIL。
3. 人工把它改成“60 分钟 / 1 个页面 / 1 个 CTA / 假设标记”，签字后严格 PASS。
4. executor 真正生成第一个 HTML 页面和 6 项机器检查报告，不停在方案里。

边界也写清楚：Agent 负责语义判断，人负责指标和审批，CLI 只做确定性门禁与安全执行；固定 Demo 不冒充实时模型调用。启发来源、实现时间线、第三方说明和资产权利都公开保留。

Demo：https://siuserxiaowei.github.io/xiaowei-goal/
GitHub：https://github.com/siuserxiaowei/xiaowei-goal

具体实现原创，不主张“目标管理 / Prompt / 编译器比喻”的全球或类别首创。
