# ChatGPT Web Research

An Agent Skill for running a traceable research task through the official ChatGPT website in the browser profile chosen by the user.

The Skill treats browser control, account/model verification, prompt submission, generation observation, response capture, and Markdown readback as separate evidence gates. It does not replace a required ChatGPT web run with an API call or an unrelated web-search answer.

Typical request:

```text
Use $chatgpt-web-research in my signed-in Chrome profile to compare three accounting tools, preserve the raw ChatGPT response, and save a checked Markdown brief.
```

The user remains responsible for login, CAPTCHA, two-factor authentication, purchases, and account changes. The Skill never reads browser secrets to identify an account.
