# Third-party research references

This Skill is independently implemented and remains under the repository's
MIT License.  The following projects were inspected as design references on
2026-08-24.  No source code, bundled executable, credential, cookie, or model
output from those projects is included here.

## last30days-skill

- Project: `mvanhorn/last30days-skill`
- Inspected revision: `d05389d39b2ce09a13f71b01e68562f077c766df`
- Upstream license at that revision: MIT, Copyright (c) 2026 Matt Van Horn
- Ideas evaluated: source-specific health diagnosis, separate discovery and
  ranking intent, bounded recovery, source diversity, first-party lanes,
  durable handoff state, and recent-social-source routing.
- Local treatment: independently implemented contracts and tests.  Engagement
  remains a discovery/ranking signal and never upgrades evidence.

## last30days-skill-cn

- Project: `Jesseovo/last30days-skill-cn`
- Inspected revision: `1a8a04c3c347defbcdbb8da26d7cf1a531426b1f`
- Upstream license at that revision: MIT, with notices for Matt Van Horn and
  Jesse.
- Ideas evaluated: Chinese-platform adapters, CJK bigram tokenization with
  optional jieba, platform-native payload-shape recognition, Beijing-time
  date boundaries, route diagnosis, and public-search fallback disclosure.
- Local treatment: independently implemented generic contracts.  Browser or
  API access never imports cookies or bypasses login, CAPTCHA, signatures, or
  access controls.

## yichen-skills / yichen-web-research

- Project: `mcncarl/yichen-skills`, component `yichen-web-research`
- Inspected revision: `28066c9f91cecd819784fc70bf882473a4fd29fa`
- Upstream license at that revision: personal learning and non-commercial
  personal workflow use only; it expressly excludes commercial services,
  client delivery, paid products, and internal company toolkits without
  written permission.
- Ideas evaluated at an abstract workflow level: horizontal/vertical research
  decomposition, explicit dated context, bounded geography × language search,
  claim/source lineage, contradiction handling, scenario triggers and
  invalidators, opportunity mapping, and retained-gap disclosure.
- Local treatment: clean, independent specification and implementation.  No
  upstream prose, code, templates, or package assets are copied or adapted.

## ego-lite

- Project: `citrolabs/ego-lite`
- Inspected revision: `689f71a7bad8b78e22664ca8708a41ceaf263e93`
- Upstream repository license at that revision: MIT, Copyright (c) 2026
  CitroLabs.  The upstream README describes the ego lite browser application
  as a separate free download; the repository license is not treated here as
  proof of browser-binary redistribution rights.
- Ideas evaluated: dynamic DOM snapshots, isolated task spaces, explicit
  browser handoff, and reuse of an already authenticated user session.
- Local treatment: assessment and a disabled-by-default adapter slot only.
  No ego-lite source, Skill files, installer, browser binary, profile, cookie,
  or session data is included.  Admission requires separate supply-chain,
  data-flow, binary-license, and session-isolation evidence plus task-specific
  user opt-in.

## wigolo

- Project: `KnockOutEZ/wigolo`
- Inspected revision: `c6ad4479da7706945b479786df0121e3cce1ece6`
- Inspected package: `wigolo@0.2.1`
- Upstream license at that revision: GNU AGPL-3.0-only; `wigolo` is identified
  by its maintainer as a trademark.
- Ideas evaluated: external local-first search/fetch/cache/watch capabilities,
  machine-readable probing, caching, and bounded multi-query discovery.
- Local treatment: optional, disabled-by-default external CLI adapter only.
  No Wigolo source or binary is vendored.  The adapter invokes a separately
  installed unmodified executable through a strict argv allowlist and does not
  imply endorsement, affiliation, or an official integration.  Users remain
  responsible for the upstream license and trademark terms of their installed
  Wigolo distribution.  The adapter accepts only a host-compatible native
  single-file executable image whose SHA-256 has been source-frozen after a
  release review; callers cannot add digests at run time.  JavaScript,
  Node/npm CLIs, shebang scripts, extensionless interpreter wrappers, and
  unaudited or renamed native programs are rejected before probing.  The
  production digest allowlist is currently empty.  Therefore the standard npm
  0.2.1 package is an explicit No-go and the current integration has no
  production execution route.  No Wigolo source or binary, including a native
  build, is distributed by this Skill.

These references do not expand this Skill's authorization.  In particular,
the Skill does not impersonate third-party crawler identities, solve CAPTCHA,
enable stealth evasion, auto-install or auto-upgrade external tools, import
browser cookies, or turn search summaries and repeated wording into accepted
facts.
