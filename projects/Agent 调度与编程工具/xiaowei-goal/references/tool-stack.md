# Research Tool Stack

Use this reference when a goal needs internet, platform, browser, or webpage
automation capability. Choose the smallest tool layer that can produce reliable
evidence.

## Tool Ladder

| Layer | Use first when | Tools |
|---|---|---|
| Platform discovery and reading | The task needs social, community, video, podcast, GitHub, RSS, or semantic web search | Agent Reach |
| Public webpage extraction | The task needs structured data from public pages, resilient extraction, crawling, or dynamic public pages | Scrapling |
| Interactive browser automation | The task needs clicking, typing, screenshots, stateful navigation, login-authorized browser sessions, or visual confirmation | browser-use |
| User-supervised browser assist | The user is already working in Chrome and explicitly wants Claude to inspect, navigate, or help act inside their browser | Claude for Chrome |

Default order:

1. Use Agent Reach for discovery, platform search, and readable source collection.
2. Use normal web readers/search/browser for simple public pages.
3. Use Scrapling when public pages need robust extraction, crawling, dynamic rendering, or resilient selectors.
4. Use browser-use when the task requires real browser interaction, screenshots, state, or form/navigation steps.
5. Mention Claude for Chrome only as an optional, user-authorized browser extension workflow, not as a default headless tool.

## Agent Reach

Use for:

- X/Twitter, Reddit, YouTube, GitHub, LinkedIn, Instagram
- Bilibili, 小红书, 抖音, 微博, 微信公众号, V2EX
- RSS, Exa web search, podcast transcripts, normal web pages

Generated goals should require:

- `agent-reach doctor` or equivalent channel availability check
- source records with tool/channel and access limitation
- fallback when a channel is unavailable, blocked, login-only, paid, or rate-limited

## Scrapling

Use for:

- extracting structured data from public pages
- crawling multiple public pages with repeated structure
- pages whose DOM changes often and need resilient selectors
- dynamic public pages where a browser-backed fetcher is needed
- saving reproducible extraction logic for later reruns

Do not use Scrapling to bypass paywalls, private content, login walls, CAPTCHAs,
or platform restrictions without explicit authorization. If proxies, CAPTCHA
solving, anti-bot bypass, or high-volume crawling are required, pause and ask the
user to authorize scope, rate, and legal/terms risk.

## browser-use

Use for:

- interactive research that requires clicking, typing, selecting filters, or following UI flows
- visual inspection, screenshots, and page state verification
- login-authorized workflows where the user has explicitly approved the session
- complex web tasks where a browser/computer action space is required

Do not use browser-use for background scraping at scale when a public reader,
Agent Reach, or Scrapling can produce the evidence more simply. Pause before
entering credentials, making purchases, submitting forms, changing account
settings, or sending messages.

## Claude for Chrome

Use only as an optional user-supervised path when:

- the user explicitly has Claude for Chrome available
- the task is happening inside the user's Chrome session
- the user wants Claude to ask questions, analyze visible page data, navigate, or help automate browser tasks

Do not describe Claude for Chrome as a general crawler, background scraper, or
default automation runtime. It is a browser extension with beta/safety
considerations and should be used only with user awareness and authorization.

## Tool Selection Field

Generated research goals should include a compact `工具栈` field when internet
or browser capability matters:

```text
工具栈：优先 Agent Reach 做平台搜索和来源收集；普通公开网页先用 web reader/browser；需要结构化抽取或公共网页爬取时使用 Scrapling；需要点击、截图、登录授权流程或动态 UI 验证时使用 browser-use；Claude for Chrome 仅作为用户明确授权的 Chrome 内协作/人工接管选项。
```

If a tool is unavailable, record the limitation and use the next accessible tool
instead. Never require every tool when a smaller layer is enough.
