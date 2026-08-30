# 中国平台缺口浏览器探针（2026-08-30）

本审计只记录正常 Chrome 只读页面的可复现状态，不修改主候选账本，也不把登录壳、搜索摘要或 AI 章节当作原始内容证据。

| 平台 | URL | 页面可见状态 | 结论 |
|---|---|---|---|
| 微博 | `https://s.weibo.com/weibo?q=%22pi%20coding%20agent%22` | `登录 - 微博`、`扫描二维码登录`、`验证码登录`、`账号登录`、手机号/验证码输入 | 内部搜索重定向登录；无正文，不新增 |
| 抖音 | `https://www.douyin.com/search/pi%20coding%20agent` | `登录后即可搜索更多精彩视频`、`扫码登录`、`验证码登录`、`密码登录` | 仅登录壳，无结果详情，不新增 |
| 抖音 | `https://www.douyin.com/video/7668306230381560163` | `视频数据加载中`、`请登录后继续使用`、`为保障更好的访问体验，请在登录后继续使用抖音` | 已知索引 ID 直达仍被登录门禁挡住；不计入 |
| 快手 | `https://www.kuaishou.com/search/video?searchKey=pi%20coding%20agent` | `登录即可享受`、`更懂你的优质内容`、`立即 登录`、`视频`/`用户` | 匿名搜索壳，无视频正文/字幕，不新增 |
| 微信公众号 | `https://mp.weixin.qq.com/` | 现有标签为 `小程序` 账户表面；未打开已知 Pi 文章 | 未取得正文；不猜 URL，不新增 |
| 微信视频号 | `https://channels.weixin.qq.com/platform` | `视频号助手` JS/创作者控制台壳 | 无公开视频详情/字幕，不新增 |

检查时间：`2026-08-30T10:33:00+08:00`（Chrome 页面实际操作为只读导航和 DOM 读取）。未输入密码/OTP，未解决 CAPTCHA，未点赞、关注、评论、分享、收藏、下载或播放媒体。

现有对象未重复抓取：微博 `china-weibo-pi-autoresearch-20260829`、`china-weibo-pi-minimal-philosophy-20260829`、`china-weibo-wake-session-manager`；抖音 `china-douyin-pi-sdk-part3`。恢复最小步骤：用户若愿意，在已打开的 Chrome 页面完成平台正常扫码/登录后告知“只读会话已准备好”；再仅回读可见 canonical detail/正文/字幕。
