# 微博投稿文案草案

#微博VibeLab# #VibeWork#

【Goal Compiler｜需求编译器】

“给我做个 AI 网站，越快越好”——难点不是 Prompt 不够长，而是没人定义：什么叫成功？什么证据会推翻它？什么时候应该停？

我把它做成了一条可运行、但不伪造完成的链：

1. Agent/Skill 产出完整语义：Smart Router、Strategy Gate、可测量指标、反证、kill criteria、工具/证据门禁与领域专属第一步。
2. 研究型任务没有来源就真实 FAIL；“看起来够好”和“主观感受”也真实 FAIL。
3. 精确指标、来源确认和执行范围留给真人；没有真签字，Demo 就停在 HUMAN PENDING，不写假 PASS。
4. 真人批准时，CLI 保存 semantic snapshot、执行 workspace 和 `approved_payload_sha256`；审批记录保留不变时，请求、指标、证据、动作或落点发生漂移会被一致性检查拒绝。

边界很明确：Agent 负责语义，人负责决定，CLI 负责确定性验证与白名单执行。固定 fixture 是 `liveAiClaimed:false`，不冒充实时 AI。

这个 SHA-256 是无密钥一致性摘要，不是数字签名，也不负责对抗能同时改写合同与摘要的人。

Demo：https://siuserxiaowei.github.io/xiaowei-goal/

GitHub：https://github.com/siuserxiaowei/xiaowei-goal

主张具体实现与组合机制的原创，不主张“目标管理 / Prompt / 编译器比喻”的全球或类别首创。
