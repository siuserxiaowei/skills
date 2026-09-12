# Source Map

Use this reference to choose where to search and what to ask.

## Channel Routing

Prefer Agent Reach when it is installed and the channel is available. Use `agent-reach doctor` or the current tool list to confirm availability before relying on a channel.

| Need | Preferred Agent Reach route | Fallback sources |
|---|---|
| Competitor positioning | Exa web search, normal web pages, GitHub, LinkedIn | official sites, pricing pages, onboarding, product docs, Product Hunt, directories |
| User pain | Reddit, X/Twitter, YouTube, V2EX, 小红书, 微博 | App Store/Google Play reviews, public forums, search results |
| Chinese consumer signal | 小红书, 抖音, B站, 微信公众号, 微博, V2EX | public search results, platform pages reachable by browser |
| Technical examples | GitHub, Exa code/context, normal web pages | GitHub repos, GitHub issues, official docs, code search, engineering blogs |
| SEO/content | Exa web search, RSS, normal web pages | search results, competitor blogs, comparison pages, template/checklist pages |
| Founder/operator insight | podcasts, YouTube, X/Twitter, LinkedIn, RSS | interviews, newsletters, public talks, founder blogs |

If a channel needs login, cookies, proxy, paid access, or bypassing platform restrictions, record the limitation and use accessible sources instead unless the user explicitly authorizes that channel.

## Tool Routing

Use `references/tool-stack.md` for capability selection:

| Need | Tool route |
|---|---|
| Platform/social/video/community search | Agent Reach |
| Simple public webpage reading | web reader, browser, or Agent Reach web page route |
| Structured extraction from public pages | Scrapling |
| Repeated public crawling with stable output | Scrapling |
| Dynamic UI inspection, clicks, filters, screenshots | browser-use |
| Login-authorized browsing with explicit user approval | browser-use or user-supervised Claude for Chrome |
| User wants help inside their own Chrome browser | Claude for Chrome as optional user-supervised path |

If Scrapling, browser-use, or Claude for Chrome would require credentials,
private content, CAPTCHA solving, payment, account changes, message sending,
or bypassing platform restrictions, pause and ask for explicit authorization.

## Agent Reach Platform Map

When available, route platform-specific research through Agent Reach before generic web search:

| Platform group | Channels |
|---|---|
| Overseas social/content | X/Twitter, Reddit, YouTube, GitHub, LinkedIn, Instagram |
| Chinese social/content | Bilibili, 小红书, 抖音, 微博, 微信公众号, V2EX |
| General discovery | RSS, Exa web search, podcast transcripts, normal web pages |

Do not claim full internet coverage. Phrase scope as "current run's collected, deduplicated, relevant, source-backed material." Agent Reach expands the accessible source surface, but actual coverage depends on installation, cookies, proxies, rate limits, platform blocks, and user authorization.

## Query Patterns

Search in both Chinese and English when the market could include both.

Competitors:

```text
"{idea}" app
"{idea}" SaaS
"{idea}" alternative
"best {category} tools"
"{competitor}" pricing
"{competitor}" reviews
```

User pain:

```text
"{category}" complaints
"{category}" reviews
"{category}" reddit
"{category}" feature request
"{category}" too expensive
"{category}" not working
```

Chinese market:

```text
"{品类}" "小红书"
"{品类}" "抖音"
"{品类}" "B站"
"{品类}" "公众号"
"{品类}" "避坑"
"{品类}" "推荐"
"{品类}" "痛点"
```

Landing page:

```text
"{category}" landing page
"{category}" pricing page
"{category}" onboarding
"{category}" demo
site:{competitor_domain} pricing
site:{competitor_domain} blog "{topic}"
```

SEO:

```text
"{topic}" guide
"{topic}" template
"{topic}" checklist
"{topic}" alternatives
"{topic}" vs
"how to {job}"
```

Technical build:

```text
site:github.com "{feature}" "{framework}"
"{feature}" "{framework}" example
"{library}" docs
"{error}" "{framework}"
```

## Standard Research Pack

For a normal app or website task, ask for:

- 5-8 competitor or adjacent product sources
- 3-5 user pain sources
- 3-5 page, onboarding, UX, or implementation references
- 2-4 growth, SEO, or acquisition references
- 1-3 risk references if the domain touches privacy, payments, minors, health, finance, or education claims
