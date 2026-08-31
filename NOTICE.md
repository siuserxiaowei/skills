# BUGFIRE notices

BUGFIRE「补丁兽」is an **unofficial independent extension**. It is not affiliated with, endorsed by, or sponsored by OpenAI.

## Upstream

BUGFIRE is based on Codex Dream Skin v1.1.2 at pinned commit [`2f038b5322702cfb248d9c7564b56470a389abc2`](https://github.com/Fei-Away/Codex-Dream-Skin/commit/2f038b5322702cfb248d9c7564b56470a389abc2). The original Patch Dragon, pet state machine, XP levels, growth cards, and certificate experience are additions in this independent extension.

## License scope

The MIT License in [`LICENSE`](LICENSE) applies to project source code and documentation. It does not grant rights to:

- OpenAI or Codex trademarks, product names, logos, or trade dress;
- official Codex / ChatGPT application binaries, `.app` bundles, or `app.asar`;
- user-supplied images or third-party artwork;
- character likenesses, franchise artwork, or other third-party intellectual property.

## Runtime and data

BUGFIRE does not redistribute Node.js. The macOS runtime validates and uses the signed Node.js executable bundled with the user's official Codex Desktop application.

Themes are injected through a verified Chromium DevTools Protocol endpoint on the loopback interface. BUGFIRE does not modify the official application bundle or code signature, and its desktop-pet runtime does not execute a real Build command or read task text, source code, API keys, or secrets in `1.3.0-bugfire.1`. The separately invoked Character Director reads an environment API key only for an explicitly requested live call and never persists it. The local progress file contains only gameplay state described in the README.

CDP is powerful even on loopback. Do not expose its port to the network or run untrusted local software while a themed session is active. Use Pause or Restore when the extension is not needed.

## Keepsake disclaimer

Every season certificate must retain this statement:

> 个人成长纪念卡，由本地活动生成；非官方认证，不代表专业资格。
