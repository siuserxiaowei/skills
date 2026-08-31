# Security policy

BUGFIRE is an unofficial local extension for Codex Desktop on macOS. The currently supported release line is `1.3.0-bugfire.x`.

## Report a security issue

Do not post API keys, task text, source code, account details, unredacted logs, or a full Application Support directory in a public Issue. After the user-owned canonical repository is published, use its private vulnerability-reporting channel when available. Until then, keep a minimal local reproduction and share only redacted diagnostics with the repository owner.

Include:

- BUGFIRE and Codex Desktop versions;
- macOS version and CPU architecture;
- the smallest reproducible steps;
- redacted output from `doctor-macos.sh` or `verify-dream-skin-macos.sh`;
- whether the official application bundle or CDP flags were changed outside this project.

## Security boundary

- The injector accepts only a verified Codex renderer on a loopback CDP endpoint.
- It does not modify the official `.app`, `app.asar`, or code signature.
- The first release does not run a real Build or Shell command.
- The pet does not read task text, prompts, source code, API keys, or secrets.
- Local progress is schema-validated, size-bounded, atomically written, and stored with mode `0600`.
- The optional Character Director reads its API key only from the environment, requires HTTPS for remote endpoints, persists no credentials, rejects malformed UTF-8, refuses to overwrite existing outputs, and cannot bypass the human-review or deterministic pack-validation gates.

CDP is powerful even on loopback. Never expose the debugging port on `0.0.0.0` or a LAN address, and avoid untrusted local software while the extension is active.

## Immediate containment

Pause without closing Codex:

```bash
~/.codex/codex-dream-skin-studio/scripts/pause-dream-skin-macos.sh
```

Remove injection and restore the saved base theme:

```bash
~/.codex/codex-dream-skin-studio/scripts/restore-dream-skin-macos.sh \
  --restore-base-theme --restart-codex
```
