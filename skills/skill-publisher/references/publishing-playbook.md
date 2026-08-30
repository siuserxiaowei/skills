# Publishing Playbook

Use the path that matches the current repository and installed tooling.

## Preflight Record

Before mutation, record:

```text
Source root:
Discovered Skills:
Release files or commit:
Current branch:
Current origin:
Target OWNER/REPO:
Visibility:
License and notices:
Release tag:
Validation commands:
Installation verification client:
```

The record is a release plan, not authorization by itself.

## Current Official Path

When `gh skill --help` succeeds:

1. run `gh skill publish <repo> --dry-run`;
2. review any suggested fix before using `--fix` because it changes files;
3. commit only the intended reviewed changes;
4. run `gh skill publish <repo>` interactively, or provide an explicitly chosen tag with `--tag`;
5. use `gh skill preview OWNER/REPO SKILL` and an isolated `gh skill install` to verify the release.

The official publisher discovers Skill entrypoints using documented repository layouts, validates the Agent Skills specification, can inspect relevant GitHub security settings, adds the `agent-skills` topic, and creates a GitHub release. It does not choose the user's license or decide which unrelated working-tree changes belong in a commit.

## Older GitHub CLI

If `gh skill` is unavailable:

- prefer an authorized GitHub CLI upgrade when the user wants the official path;
- otherwise run the local preflight plus an available Agent Skills reference validator;
- create or update the GitHub repository with ordinary `gh repo`/`git` operations only after target, visibility, branch, commit, and remote are exact;
- create a release with `gh release create` only when a versioned release was requested;
- verify discovery and isolated installation with another client the user already trusts, such as `npx skills`, and label this as client-specific rather than universal conformance.

Do not silently install a new publisher or package manager just to complete verification.

## New Repository

For a new repository:

1. decide whether the source is one Skill or a multi-Skill repository;
2. ensure the repository root contains the intended license/notice and user-facing documentation;
3. initialize Git only inside the exact new repository directory;
4. inspect the first commit file list and diff;
5. create `OWNER/REPO` with explicit visibility;
6. add the remote and push the reviewed commit;
7. validate and release separately.

Do not initialize Git inside a Skill subdirectory that already belongs to a larger repository unless the user explicitly chose to split it.

## Existing Repository

For an update:

- verify that `origin` resolves to the intended owner/repository;
- inspect whether the local branch is ahead, behind, diverged, or has no upstream;
- identify staged, unstaged, and untracked files separately;
- avoid committing unrelated user work;
- respect protected branches and the project's PR/release process;
- confirm that the remote commit matches the intended local commit after push.

## Documentation and Claims

Include what a new user needs to decide and operate safely:

- what the Skill does and when it activates;
- supported clients that were actually tested;
- installation examples for those clients;
- required tools, credentials, network access, or costs;
- external-write, privacy, and destructive-operation boundaries;
- provenance and license information;
- one realistic invocation and expected artifact when useful.

Avoid mandatory growth tactics. Badges, screenshots, demos, translations, and extensive troubleshooting earn their place only when they help the target audience and can be maintained.

## Verification Matrix

| Claim | Strong evidence |
|---|---|
| Repository published | `gh repo view` plus remote URL and visibility |
| Commit pushed | local commit SHA equals the remote ref SHA |
| Skill conforms | current official/reference validator output |
| Release exists | `gh release view <tag>` and remote tag SHA |
| Skill discoverable | preview/list output names the intended Skill |
| Skill installable | isolated install creates the expected file tree |
| Installed version exact | tag/commit provenance and selected file hashes match |

Never use a successful push alone to claim that discovery, conformance, release, or installation succeeded.
