# Research Basis

Last reviewed: 2026-08-30.

## Primary Sources

- Tencent WeChatReading repository and versioned Skill: <https://github.com/Tencent/WeChatReading>
- Tencent setup page for the official Skill/API key: <https://weread.qq.com/r/weread-skills>
- Current upstream commit inspected locally and through GitHub: `315698a8da1810fab0bbf24a52b38a6960e54cdc` (`v1.0.4`, 2026-07-01).
- Open issues documenting unavailable shelf writes/uploads/groups and current response limitations: <https://github.com/Tencent/WeChatReading/issues>
- RFC 9110 HTTP Semantics, including security considerations for forwarding caller-supplied `Authorization`/`Cookie` headers across redirects: <https://www.rfc-editor.org/rfc/rfc9110>
- OWASP Secrets Management Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html>
- NIST Privacy Framework: <https://www.nist.gov/privacy-framework>

## Cross-Checks

Community implementations and issue reports were used to identify failure cases, not as the authority for endpoint semantics:

- gateway clients confirm practical problems around redirects, key exposure, fallback behavior, and fixed-version drift;
- issue reports showed that `/book/similar` requires explicit `count` and `maxIdx`, `/review/list/mine` has conditional `abstract`/`range`, `/book/info` may omit `wordCount`, and selected images may be placeholders;
- multiple projects market the API as “bookshelf management,” while Tencent's open issues confirm the current Gateway remains read-only.

## Design Conclusions

1. Keep compatibility with Tencent's official Gateway and endpoint names, but independently implement the transport, validation, privacy, statistics, and completion logic.
2. Make read-only scope explicit. Do not promise or emulate unavailable writes.
3. Replace copy-pasted `curl` with a client that never accepts a key on argv, refuses redirects, bounds responses/retries, and validates the known surface.
4. Treat `upgrade_info` as untrusted remote data. Verify official source/diff before changing local code.
5. Minimize account data and separate public social data, personal history, authored notes, and credentials.
6. Compute totals deterministically and surface unknown/mismatched values instead of forcing them into a convenient category.

## Rejected Legacy Behaviors

- describing a read-only shelf sync as write-capable management;
- following an `upgrade_info.message` as executable instructions;
- hand-building authenticated `curl` commands for every request;
- treating missing fields as zero or relying on unstable annual-report modules;
- counting article collections as “books” without explaining components;
- treating absent privacy flags as public;
- exporting raw identities and account data by default;
- silently falling back to cookies, scraping, reverse-engineered writes, or arbitrary gateways.
