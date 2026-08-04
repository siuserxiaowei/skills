# ChatGPT 官网调研 (Web Research)

Run research tasks on the official ChatGPT website — inside the Chrome profile where the user is already signed in — and save verified Markdown reports.

## What It Does

- Treats the real ChatGPT web page as the single source of truth
- Reaches the page through the Chrome extension/browser-control route first
- Drops back to visible Computer Use solely when Chrome control cannot attach
- Holds out until the response has finished and carries a unique completion marker
- Pulls the answer off the page, keeping both a raw Markdown copy and a readable report

## Privacy Notes

- This public version ships without personal local paths, account names, cookies, tokens, or browser storage
- Inspecting cookies, local storage, passwords, browser profiles, or session stores is explicitly off-limits for the skill
- Report destinations are written as `<WORKSPACE>/reports/` placeholders — point them at your own workspace
- Profiles appear only as `<profile-name>` placeholders

## Requirements

- A supported Claude Code / Codex environment providing `chrome:control-chrome`
- `computer-use:computer-use` on hand for the fallback
- A Chrome profile that is already signed in to the intended ChatGPT account
- User-visible proof of paid or Pro model status whenever a task explicitly calls for it

## Typical Use

```text
Use $chatgpt-web-research to research Anthropic through the official ChatGPT web page and save a verified Markdown report.
```

Strictness is deliberate here: when the intended real ChatGPT page cannot be operated, the skill stops rather than swapping in an API call, a web search, or a different account.
