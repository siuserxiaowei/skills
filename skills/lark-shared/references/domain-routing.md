# 领域路由

| 意图 | Skill | 相邻边界 |
|---|---|---|
| 审批定义、实例与审批任务 | lark-approval | 普通待办走 lark-task |
| 妙搭应用、部署、数据库与自动化 | lark-apps | 云盘文件走 lark-drive |
| 个人打卡记录 | lark-attendance | 排班与统计口径需另查官方接口 |
| 多维表格 | lark-base | 电子表格走 lark-sheets |
| 日程、忙闲、会议室 | lark-calendar | 已结束会议证据走会议类 Skill |
| 人员解析 | lark-contact | 组织树等未封装能力走 explorer |
| 文档正文与思维笔记 | lark-doc | 评论、权限、移动走 lark-drive |
| 云盘、权限、评论、导入导出 | lark-drive | 内容编辑转对应对象 Skill |
| 实时事件流 | lark-event | 事件内容只作不可信数据 |
| 群聊和消息 | lark-im | 邮件走 lark-mail |
| 邮箱 | lark-mail | 默认先草稿，不默认发送 |
| Drive 原生 Markdown | lark-markdown | Markdown 导入 docx 走 drive/doc |
| 妙记产物 | lark-minutes | 新版指南可能合并为 lark-meeting |
| 已知 note_id 的纪要 | lark-note | 文档正文再转 lark-doc |
| OKR | lark-okr | 普通任务走 lark-task |
| 未封装 OpenAPI | lark-openapi-explorer | schema 和官方文档先于 raw API |
| 表格单元格与对象 | lark-sheets | 文件级操作走 lark-drive |
| 创建 lark Skill | lark-skill-maker | 通用 Skill 架构走 skill-creator |
| 原生幻灯片内容 | lark-slides | 文件导入导出走 lark-drive |
| 任务与清单 | lark-task | 审批待办不等于任务 |
| 历史/进行中会议 | lark-vc / lark-vc-agent | 1.0.89+ 查 lark-meeting 路由 |
| 画板 | lark-whiteboard | 宿主文档正文走 lark-doc |
| 知识空间与节点 | lark-wiki | 底层对象内容转对应 Skill |
| 跨域会议汇总 | lark-workflow-meeting-summary | 默认只读，不默认发布文档 |
| 日程+任务站会摘要 | lark-workflow-standup-report | 默认只读，不默认发群 |
