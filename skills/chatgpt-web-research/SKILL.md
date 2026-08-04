---
name: chatgpt-web-research
description: Drive the user's already logged-in ChatGPT 官网 / ChatGPT 网页版 account — especially GPT-5.5 Pro / ChatGPT Pro — to carry out 产品调研, 市场调研, competitor research, or second-opinion analysis, and for any request mentioning ChatGPT 官网, ChatGPT 网页版, GPT-5.5 Pro, 5.5 Pro, 用官网调研, 产品调研, 市场调研, or wanting to avoid API cost. The Chrome plugin/extension route comes first; when it is missing or cannot attach, fall back to Computer Use on the real, visible Chrome window/profile. This skill operates only the genuine ChatGPT web page inside the intended Chrome account/profile — never a separate free-account window, never the OpenAI API, never web search alone, never generic Playwright, and never the deprecated chatgpt-web MCP.
---

# ChatGPT 官网调研 (Web Research)

## The One Rule That Matters

Everything must go through the official ChatGPT web page open in the Chrome account/profile where the user is already logged in — that page is the single source of truth.

Never bring up or fall back to some other free ChatGPT window/account. When the intended Pro / GPT-5.5 Pro account cannot be seen through either the plugin-driven page or the Computer Use visible Chrome page, halt and ask the user to bring up (or switch Chrome to) that logged-in ChatGPT account.

Answers must not be sourced from the OpenAI API, a local model, plain web search, the deprecated `chatgpt-web` MCP, stale task files, or memory. Should the Chrome plugin route be unusable in the current thread, fall back to Computer Use as long as it can drive the user's real visible ChatGPT page. Should neither route be able to reach that page, stop and state plainly that the required ChatGPT website route is unavailable.

For product or market research, the job counts as done only once the ChatGPT web response has visibly finished, has been pulled off the page, has been written out as Markdown, and has passed verification.

## Skills to Load First

Browser-plugin work requires loading and following `chrome:control-chrome`; Computer Use fallback work requires loading and following `computer-use:computer-use`.

- Pull `chrome:control-chrome` from the current environment's skill registry; never hard-code user-specific local plugin paths.
- Pull `computer-use:computer-use` from the current environment's skill registry ahead of any Computer Use fallback; never hard-code user-specific local plugin paths.
- When the full Chrome skill body already appears verbatim in the current user message, re-reading it is unnecessary.
- The Chrome skill's `node_repl` / browser-client route is the preferred option whenever it exists.
- With several Chrome extension instances/profiles around, do not blindly grab `agent.browsers.get("extension")`. Call `agent.browsers.list()` first, look only at the returned metadata (profile name, last-used flag, and similar), and pick the Chrome extension instance that lines up with the account/profile the user named.
- The opening move is to list tabs through the chosen browser's `browser.user.openTabs()` and claim a genuine ChatGPT tab out of the user's existing Chrome session whenever one exists — this is the safest way to remain inside the logged-in ChatGPT account the user intends.
- Privacy boundary: never look at cookies, local storage, passwords, browser profiles, or session stores.
- When `node_repl` does not show up, run tool discovery for `node_repl js`; when it is still unavailable after that, move on to the Computer Use fallback.
- Count `Browser is not available: extension`, `Browser is not available: iab`, an empty `agent.browsers.list()`, or being unable to claim the visible ChatGPT tab as Chrome-plugin failure. Skip diagnostics unless the user requests them, and carry on with the Computer Use fallback.

## Fallback via Computer Use

Take this path only once the Chrome plugin route is unavailable or cannot attach, or when the user explicitly asks for `@电脑`.

- Drive the Chrome window/profile the user already has open. Choose the window whose title, profile button, and tab strip line up with the intended account/profile, for example `Chrome - <profile-name>`.
- Opening a fresh ChatGPT tab inside the same verified Chrome window/profile is acceptable when the user approves or the current verified tab is unsuitable. Opening another Chrome profile or a separate account window is not.
- Base account/model checks solely on what the page visibly shows. Never open or inspect session/status endpoints, cookies, local storage, passwords, browser profiles, or session stores.
- When a sensitive session/API tab happens to be open, leave it alone — do not quote or extract its contents.
- Verify GPT-5.5 / Pro by opening the visible model/menu as needed and looking for labels such as `GPT-5.5`, `Pro`, `Pro 扩展`, or an equivalent paid-route indicator. When Pro cannot be confirmed yet the user explicitly asked for Pro, stop before sending anything.
- Type or paste the prompt into the visible ChatGPT composer, and confirm the unique completion marker shows up in the composer before sending.
- Apply the same completion criteria as the Chrome route: hold on until generation has stopped and the marker is present in the visible response.
- Extraction should prefer the page's `复制回复` button, but confirm the system clipboard actually holds non-empty assistant text containing the marker. When the page reports `Failed to copy to clipboard`, the clipboard comes back empty, or it holds the wrong text, extract through the Computer Use accessibility tree, rebuild readable Markdown, and explicitly record that extraction method in the saved report header.
- Should Computer Use focus drift onto unrelated tabs, return by exact ChatGPT tab title/URL and do not read any unrelated private content.

## Workflow

1. Give the browser session a name, for example `🔎 ChatGPT 调研`.
2. Find the intended ChatGPT account via the Chrome plugin:
   - Call `agent.browsers.list()` and enumerate every Chrome extension instance. When the user names an account/profile such as `<profile-name>`, match that name before opening or claiming any ChatGPT page.
   - When several Chrome instances are visible and none of them matches the user's named account/profile, do not settle for the last-used or default Chrome profile.
   - When the user says the named Chrome profile/window is already open, use `computer-use` purely to inspect the visible Chrome window title, profile button, tab strip, and Codex extension presence. When that visible window title/profile identifies the intended profile while the Chrome plugin metadata shows a generic name such as `您的 Chrome`, map the plugin instance by lining up its open tab list against the visible tab strip before going further.
   - Call `browser.user.openTabs()` on the selected Chrome instance and scan for existing `chatgpt.com` tabs.
   - Favor a tab whose visible title/account/model points to the user's paid ChatGPT account.
   - Claim the precise tab object handed back by `openTabs()` using `browser.user.claimTab(...)`.
   - Reaching for `browser.tabs.new()` as the default first move is forbidden — a freshly opened tab may land in the wrong/free account.
   - When no suitable ChatGPT tab exists, ask the user to open `https://chatgpt.com/` in the already logged-in Chrome account/profile, then carry on by claiming that tab.
   - When the Chrome plugin route is unavailable or cannot claim a real tab, switch to the Computer Use fallback and locate the visible Chrome tab/window instead.
3. Make sure the page is the intended signed-in account and that the composer is usable.
   - When login, CAPTCHA, 2FA, or account selection blocks progress, ask the user to complete that step.
   - When a ChatGPT modal blocks the composer, close it provided it is a normal informational modal. Never accept permission prompts or account changes without explicit user approval.
   - When the user explicitly requested GPT-5.5 Pro, 5.5 Pro, ChatGPT Pro, or a paid ChatGPT website route, inspect only the visible page/account/model labels.
   - When the visible page shows `免费版`, a free account, a non-Pro account, or no usable Pro model route, stop and ask the user to switch/open the intended logged-in ChatGPT account in Chrome — do not push ahead inside the free account.
   - When Pro status is not visible yet the user explicitly requires it, stop and ask the user to make the correct Pro account/model visible. An unconfirmed route must never be treated as Pro.
4. Only when needed, start a new chat inside the verified account:
   - Favor the ChatGPT UI's `新聊天` control, or `https://chatgpt.com/` inside the already claimed/verified tab.
   - Do not open a new browser window or a new tab that could switch profiles/accounts.
5. Assemble a self-contained prompt containing:
   - The current date.
   - The exact research target plus common confusion terms.
   - The required report sections.
   - Requirements covering sources and uncertainty.
   - A unique completion marker placed on the final line, for example `[[CHATGPT_WEB_RESEARCH_DONE_<uuid>]]`.
6. Put the prompt into the page.
   - The visible textbox is the first choice.
   - When a direct `fill` does not stick, paste through the tab clipboard, then confirm the marker shows up in the textbox before sending.
7. Submit the prompt from the real page.
8. While generation runs, poll every 3 minutes.
   - Regard `Pro 思考中`, `正在思考`, `正在整理答案`, a visible stop button, or an active generation status as still running.
   - An hour of thinking is fine — keep waiting as long as answer text has started appearing.
   - When more than an hour passes with no assistant answer text whatsoever, report the stall rather than giving up early.
   - When the page immediately shows `Something went wrong`, click Retry once within the same chat. When it happens again, open a fresh ChatGPT tab and resubmit once.
   - When the user closes the window or the tab vanishes, open a fresh ChatGPT tab and resubmit, unless the user told you to stop.
9. Completion demands all of the following:
   - The stop button is gone, or the page otherwise no longer shows a running status.
   - The assistant response carries the unique completion marker.
   - The visible response covers the requested report sections, or explicitly explains information that is unavailable.
10. Pull the answer off the real page.
   - The ChatGPT `复制回复` button plus reading the browser clipboard text is the preferred route.
   - Confirm the copied text is the assistant answer rather than the user prompt. When the copied text lacks the answer sections, begins with the submitted prompt, or is far shorter than the visible response, throw it away and use DOM extraction.
   - When no reliable copy button exists, extract from the visible DOM/accessibility tree. Favor `[data-message-author-role="assistant"]` whenever the ChatGPT DOM exposes it. Under Computer Use, rely on the accessibility tree text nodes for the assistant response and rebuild Markdown where needed.
   - Confirm the copied/extracted text carries the unique completion marker and matches the visible beginning/end. When only an accessibility-tree reconstruction is achievable, keep the key sections, tables, examples, and links intact, and state this extraction method in the report header.
11. Persist the output before wrapping up.
    - Write long raw page output to `<WORKSPACE>/reports/YYYY-MM-DD-<topic>-chatgpt-web-raw.md`.
    - Write the readable final Markdown report to `<WORKSPACE>/reports/YYYY-MM-DD-<topic>.md`.
    - Strip the marker out of the readable report unless the user asked to preserve raw evidence.
    - Place the ChatGPT conversation URL, save time, extraction method, and verification status near the top.
12. Before ending browser work, call Chrome finalization, keeping the completed ChatGPT tab around as a deliverable only when it helps user review.
    - Under the Computer Use fallback, leave the completed ChatGPT tab open unless the user asks for it to be closed.

## Prompt Template for Product Research

For product research, start from this template and swap in the bracketed values.

```text
今天是 <YYYY-MM-DD>。请联网调研产品 <产品名>（注意不要和 <易混淆对象> 混淆），输出中文 Markdown 产品调研报告。

请包含：
1. 一句话结论
2. 产品定位与核心价值
3. 核心功能
4. 目标用户与典型使用场景
5. 工作流/使用方式
6. 价格、套餐与限制
7. 平台支持与下载渠道
8. 竞品对比（至少 4 个）
9. 用户评价/口碑线索
10. 商业化与增长判断
11. 风险、限制与不确定性
12. 适合/不适合推荐给谁
13. 推广或选题角度建议
14. 参考来源链接

要求：
- 结论先行。
- 区分已核验事实、公开资料推断和你的判断。
- 价格、版本、政策、平台支持等易变信息标注核验日期。
- 无法确认的信息直接写“未确认”。
- 给出可追溯来源名称或链接。
- 回答最后单独一行输出：[[CHATGPT_WEB_RESEARCH_DONE_<uuid>]]
```

## Success Checklist

Ahead of claiming success, confirm and report each item:

- No old/deprecated routes were touched.
- The answer came from a real ChatGPT website URL, driven either by Chrome plugin control or by the Computer Use fallback.
- The page sat inside the user's intended, already logged-in ChatGPT account/profile — it was not some newly opened different/free-account window.
- When the Chrome plugin route failed, the reason for falling back was written down.
- Visible account/model status was inspected. When Pro was requested, visible evidence must establish Pro, otherwise the run stops before submission.
- The final visible response carried the unique marker.
- The copied/extracted text carried that same marker.
- The Markdown was saved and then read back from disk.
- The saved report path is handed back to the user.

## When Things Go Wrong

- When Chrome plugin control tools are unavailable, take the Computer Use fallback provided it can drive the real visible ChatGPT page. Never manufacture a substitute research answer out of non-ChatGPT sources.
- When ChatGPT is signed out, blocked by CAPTCHA, or stuck on 2FA, ask the user to finish that browser step.
- When only a free ChatGPT account/window is visible even though Pro was requested, stop and ask the user to open or switch to the already logged-in Pro account in Chrome.
- When the page produces an incomplete answer without the marker, keep waiting for as long as it is still running; when it halts without the marker, retry once.
- When extraction feels uncertain, attempt the copy button, then DOM extraction, then accessibility-tree extraction, in that order. When uncertainty remains, ask the user to copy the response out of ChatGPT and compare it before treating it as the final source.
- When the user explicitly says to wait, that wait policy overrides the default timing.
