---
name: skill-publisher
description: Prepare, validate, publish, or update Agent Skills in a GitHub repository with explicit target, visibility, license, attribution, commit, and release boundaries. Use when the user asks to publish or share a Skill, create its GitHub repository, cut a Skill release, or verify that a published Skill can be discovered and installed.
---

# Skill Publisher

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

Publish a reviewable repository state, not an inferred collection of local files.

## 1. Resolve the Release Object

Inspect the source before changing local or remote state:

- find the repository root and all Skill entrypoints that the chosen publish command will discover;
- distinguish the Skill name, local directory, repository name, and release tag;
- inspect the current branch, origin, staged and unstaged changes, and repository visibility;
- identify the exact commit or exact files intended for the release;
- preserve existing licenses, notices, copyright, and provenance.

If the source sits inside a larger repository, do not pretend the subdirectory can be pushed independently. Decide whether the user wants the whole repository published or a separately prepared repository.

## 2. Establish Authority

Publishing is an external write. Before the first create, push, visibility change, topic change, or release action, resolve:

- exact `OWNER/REPO`;
- public, private, or internal visibility;
- whether this is a new repository or an update;
- the files/commit and branch to publish;
- license choice and required attribution;
- release tag, if a GitHub release will be created.

A direct request to publish can authorize the resolved operation, but it does not answer missing high-impact choices. Ask when target, audience, license, ownership, or included changes remain materially ambiguous.

Never add MIT or any other license on the user's behalf. Without a license, default copyright applies; public visibility is not an open-source license.

## 3. Run Read-Only Preflight

Run the bundled checker from this Skill directory:

```bash
python3 scripts/preflight.py /absolute/path/to/repository --visibility public --target OWNER/REPO
```

The checker does not execute candidate scripts, stage files, create licenses, initialize Git, or contact GitHub. Use `--format json` for a machine-readable manifest.

Then use the current official validator when available:

```bash
gh skill publish /absolute/path/to/repository --dry-run
```

`gh skill` requires GitHub CLI 2.90.0 or later as of the research date and remains a preview feature. Detect support with `gh skill --help`; do not assume it exists and do not upgrade tools without authorization. Read [references/publishing-playbook.md](references/publishing-playbook.md) for fallback and release details.

Do not publish while any of these remain unresolved:

- secrets, private keys, environment files, or private user paths in the release set;
- invalid Skill metadata or a Skill name/directory mismatch;
- symlinks or archives whose target/content was not reviewed;
- unknown public-license status or missing third-party attribution;
- unrelated staged changes, an unexpected remote, or an ambiguous repository boundary;
- placeholders or claims in public documentation that were not verified.

## 4. Publish the Reviewed State

Use the least surprising official operation for the resolved repository state:

- create a repository only after the owner and visibility are explicit;
- stage exact paths rather than `git add .` in a dirty worktree;
- do not rewrite history, bypass branch protection, bypass secret protection, force-push, or change visibility unless separately authorized;
- do not create a generic commit if the user did not ask you to commit;
- prefer `gh skill publish` for validation and a versioned Skill release when supported;
- if the preview command is unavailable, explain the fallback and keep repository creation, push, release creation, and installation verification as distinct observable steps.

README content should help the intended audience evaluate and install the Skill, but screenshots, badges, bilingual duplication, Star History, and marketing copy are optional—not universal gates. Never fabricate adoption metrics, compatibility, screenshots, or security claims.

## 5. Verify the Remote Result

Read back authoritative remote state after each external mutation:

1. confirm the repository URL, visibility, default branch, and pushed commit;
2. confirm the release tag and assets if a release was requested;
3. preview the discovered Skill and file tree;
4. install the intended Skill/version into an isolated temporary directory using a supported client;
5. verify the installed `SKILL.md` name and important file hashes against the reviewed release;
6. report the exact install command, verified commit/tag, and any client-specific limitation.

Do not copy the published Skill over a user's personal Skill directory as a side effect. Installation or local synchronization is a separate action.

Read [references/research-basis.md](references/research-basis.md) when updating assumptions about the Agent Skills specification, GitHub CLI, security checks, or licensing.
