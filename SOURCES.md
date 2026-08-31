# Sources and evidence index

## Primary implementation sources

- [Pinned Codex Dream Skin upstream commit](https://github.com/Fei-Away/Codex-Dream-Skin/commit/2f038b5322702cfb248d9c7564b56470a389abc2): inherited base and Git provenance.
- [Node.js `fetch` documentation](https://nodejs.org/api/globals.html#fetch): built-in HTTP client used by `bugfire-director.mjs`; no added network dependency.
- [OpenAI Chat Completions API reference](https://platform.openai.com/docs/api-reference/chat): supported live request shape.
- [OpenAI Responses API reference](https://platform.openai.com/docs/api-reference/responses): optional live request shape selected with `--api-mode responses`.
- [MIT License](LICENSE): repository software license.

## Repository evidence

- [`macos/scripts/bugfire-director.mjs`](macos/scripts/bugfire-director.mjs): AI request, fixture verification, human gate, and materialization implementation.
- [`macos/scripts/bugfire-pack.mjs`](macos/scripts/bugfire-pack.mjs): deterministic pack schema, image, path, rights, and build checks.
- [`macos/tests/bugfire-director.test.mjs`](macos/tests/bugfire-director.test.mjs): real loopback HTTP request tests, credential non-persistence, strict UTF-8 and no-clobber regressions, rejection gate, and end-to-end build test.
- [`contest/bugfire/run-demo.sh`](contest/bugfire/run-demo.sh): one-command offline replay and optional explicitly authorized live install/verify/restore cycle.
- [`contest/bugfire/demo`](contest/bugfire/demo): original brief, checksum-locked AI draft, scripted review input, reviewed plan, SVG sources, and exported PNGs.
- [`macos/references/asset-provenance.md`](macos/references/asset-provenance.md): existing hero and screenshot provenance.
- [`docs/RESEARCH.md`](docs/RESEARCH.md): prior product-mechanic research and consciously excluded third-party assets.

## Evidence limits

- API documentation establishes request contracts; it does not prove a particular inference occurred. Live inference requires the CLI output and endpoint response from that run.
- A SHA-256 file proves fixture integrity, not authorship identity.
- A scripted review file proves workflow behavior, not personal approval.
- Existing V2 video footage proves older BUGFIRE engineering behavior only. Record the separate Character Director storyboard before claiming the new AI workflow was shown on video.
