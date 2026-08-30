# Research Basis

Last reviewed: 2026-08-30.

## Primary Sources

- Agent Skills specification: <https://agentskills.io/specification>
- Agent Skills reference repository: <https://github.com/agentskills/agentskills>
- GitHub CLI `gh skill publish`: <https://cli.github.com/manual/gh_skill_publish>
- GitHub documentation for adding and publishing Agent Skills: <https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills>
- GitHub CLI repository creation: <https://cli.github.com/manual/gh_repo_create>
- GitHub secret scanning and push protection: <https://docs.github.com/en/code-security/concepts/secret-security/push-protection>
- GitHub repository licensing: <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository>
- SPDX license identifiers: <https://spdx.dev/learn/handling-license-info/>

## Verified Current Facts

- The open specification requires a Skill directory with `SKILL.md`, a valid lowercase/hyphenated name matching its parent directory, and a non-empty description explaining capability and activation. Scripts, references, and assets are optional.
- GitHub CLI 2.90.0+ exposes `gh skill` in public preview. `gh skill publish --dry-run` validates documented Skill layouts without publishing; the publish flow can add the `agent-skills` topic, choose a tag, and create a release.
- GitHub warns that shared Skills are not verified merely because they are hosted on GitHub and may contain prompt injection or malicious scripts.
- Push protection reduces supported secret leaks but is not a substitute for a local release-set review.
- GitHub states that missing a license leaves default copyright in effect. A publisher therefore cannot safely invent MIT or another license.
- The repository used during development had GitHub CLI 2.87.0, so current local testing proved the need for feature detection and a documented fallback; it did not test the live `gh skill publish` path.

## Design Conclusions

1. Separate read-only preflight from create, commit, push, release, and install operations.
2. Treat repository identity, visibility, release content, license, and tag as independent decisions.
3. Prefer the current official validator/publisher when installed, while preserving a safe older-client fallback.
4. Verify remote state and an isolated installation; do not infer installability from a successful push.
5. Keep local personal-Skill synchronization out of the publishing side effect.

## Rejected Legacy Behaviors

- automatically creating an MIT license;
- defaulting every new repository to public;
- staging every file and committing generic messages without reviewing the release set;
- attempting multiple pushes while ignoring failures;
- deleting or replacing `~/.agents/skills/<name>` after publication;
- making badges, screenshots, bilingual duplication, Star History, or a fixed FAQ count universal publication requirements;
- treating `npx skills` output as proof of conformance for every Agent Skills client.
