---
name: chatgpt-web-research
description: Conduct a user-requested research run through the official ChatGPT website in the user's intended signed-in browser profile, then capture and verify the result as Markdown. Use when the user explicitly asks to use ChatGPT web, a particular visible ChatGPT plan/model, or their web subscription instead of an API. Do not substitute ordinary web search or an API when that route is required.
---

# ChatGPT Web Research

This Skill controls a visible ChatGPT session as a research instrument. The deliverable is a traceable report, not merely a submitted prompt.

Read [references/examples.md](references/examples.md) before starting.

## Result contract

Agree or infer a concrete contract containing:

- research question and decision it should support;
- required coverage and comparison candidates;
- freshness date and geography, if relevant;
- requested ChatGPT account, plan, or model evidence;
- output location and format;
- whether the user wants the ChatGPT conversation left open.

If the account or model choice materially affects the request and cannot be verified from the visible page, stop before submission. Never inspect cookies, local storage, password stores, browser-profile files, or session endpoints to prove identity.

## Choose an authorized browser route

Use capabilities available in the current environment rather than hard-coded local paths.

1. Prefer a browser-control capability that exposes the user's existing Chrome tabs.
2. Enumerate browser instances and tabs before claiming one.
3. Match the user-named profile and a visible `chatgpt.com` page.
4. If extension control cannot reach that page, use a visible computer-control capability on the same browser profile.
5. If neither route reaches the intended signed-in page, report the missing prerequisite.

Do not open a different browser profile, choose a convenient free account, or silently replace ChatGPT web with an API or your own synthesis.

When a supporting browser/computer Skill is available, read and follow it before controlling the page.

## Create a research packet

Draft a fresh prompt for this run. Include:

- today's date and the exact subject;
- confusing names or exclusions;
- the decisions and sections the answer must cover;
- primary-source and citation expectations;
- instructions to label verified facts, inference, and uncertainty;
- a run-specific completion token such as `[[WEB_RUN:<random-id>:COMPLETE]]`.

Do not reuse a cached answer as the new run. Keep the prompt proportional to the question; a fixed fourteen-section template is not appropriate for every task.

## Operate as a state machine

Track one of these states and gather visible evidence before moving forward:

| State | Required evidence | Next action |
|---|---|---|
| `SESSION_READY` | intended ChatGPT origin, usable composer, account/model condition satisfied | insert prompt |
| `PROMPT_READY` | complete packet and completion token visible in composer | submit once |
| `GENERATING` | active generation indicator or changing assistant content | wait and re-observe |
| `RESPONSE_READY` | generation ended and completion token appears in assistant response | extract |
| `CAPTURED` | extracted beginning, end, and token match the page | save and verify |
| `FAILED` | a concrete terminal condition or exhausted bounded recovery | preserve evidence and report |

Elapsed time alone does not prove completion. While the page is still generating, continue with bounded observation rather than resubmitting the same prompt.

## Submission procedure

1. Inspect the visible origin, page state, and requested account/model label.
2. Start a new conversation only if the selected existing conversation is unsuitable.
3. Insert the complete research packet and verify its ending token before sending.
4. Submit once.
5. Observe until the page reaches `RESPONSE_READY` or a specific failure occurs.

Login, CAPTCHA, two-factor authentication, account selection, payment, and permission dialogs require the user. Normal informational dialogs may be dismissed when that does not grant new authority.

## Capture without confusing prompt and answer

Prefer the page's response-copy control. If it is unavailable or incomplete, use the accessible page structure or the assistant-message DOM exposed by the authorized browser tool.

Reject a capture when:

- it contains only the submitted prompt;
- the visible response has sections missing from the captured text;
- the run token is absent;
- the beginning or ending disagrees with the page;
- generation is still active.

Keep raw capture and edited report separate when substantial cleanup is needed. The readable report may remove the completion token, but the raw evidence should retain it.

## Save and verify

Use a workspace path agreed with the user. A practical default is:

```text
reports/<YYYY-MM-DD>-<topic>/
  request.md
  response.raw.md
  report.md
  run.json
```

`run.json` should record the ChatGPT conversation URL when available, date, visible route, requested/observed model condition, capture method, and completion status. Do not store account secrets or browser state.

After saving:

1. read the files back;
2. compare the raw response's beginning and end with the page;
3. check the report against the required coverage;
4. inspect citations and mark unverified claims;
5. report exact paths and any residual limitation.

## Bounded recovery

| Failure | Recovery |
|---|---|
| Browser extension cannot attach | try visible computer control on the same intended profile |
| Intended account is not visible | ask the user to expose or switch to it |
| Login/CAPTCHA/2FA blocks the page | wait for the user to complete it |
| Immediate transient page error | use the page's retry once, then one fresh conversation attempt |
| Generation stops without the run token | preserve partial output and retry once with the missing contract |
| Copy output is incomplete | compare copy, accessible tree, and assistant DOM; keep uncertainty explicit |
| User closes the page | report the interruption; do not switch accounts to continue |

Do not loop indefinitely, create parallel duplicate research conversations, or claim completion from a partial capture.

## Delivery

Lead with the research result and link the saved report. Then state:

- which visible ChatGPT route was used;
- whether the requested account/model condition was proven;
- how the response was captured;
- whether the completion token and required sections were verified;
- what remains uncertain.

Leave the completed conversation open when it is useful for user review, unless the user asks to close it.
