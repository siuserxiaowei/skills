---
name: mac-wechat-dual-open
description: Inspect, create, repair, launch, or visually distinguish a second local WeChat app bundle on macOS by copying the official app, assigning the copy a separate bundle identifier, and ad-hoc signing only the copy. Use when the user explicitly asks for two WeChat instances or a duplicate-app diagnosis. Do not use injection tools or modify the original app.
---

# macOS WeChat second instance

This is an unofficial, reversible local workaround. It may stop working after a macOS or WeChat update, and notification behavior is not guaranteed.

Read [references/examples.md](references/examples.md) and [references/reliability-and-risks.md](references/reliability-and-risks.md) before changing an app bundle.

## Non-negotiable boundary

- The source app is read-only.
- The target must be a different `.app` path under the user's control.
- Never overwrite an existing target.
- Never install an injector, patch executable code, disable Gatekeeper, or ask for administrator access merely to create the copy.
- Creating, signing, changing preferences, recoloring, and launching are separate mutations. Use the helper's `plan` output before `--apply`.

## Locate the helper

Resolve this Skill's installed directory through the active skill registry, then use:

```bash
python3 <skill-directory>/scripts/wechat_dual_open.py --help
```

Do not search the user's entire home directory for the script when the registry already gives its location.

## Preflight

Run the read-only plan first:

```bash
python3 <script> plan
```

The default source is `/Applications/WeChat.app`; the default target is `~/Applications/WeChat-Second.app`. Review the resolved paths, source version/identifier, target existence, requested identifier, languages, and mutation list.

If a previous duplicate exists, use `status` and decide whether repair is sufficient. Removing or replacing it requires separate approval and a recoverable backup plan.

## Create

After the user approves the plan:

```bash
python3 <script> create --apply
```

The helper stages a complete copy, renames it into place only after copying succeeds, changes the duplicate's identifier, writes language preferences for that identifier, clears extended metadata on the copy, ad-hoc signs it, verifies the signature, and refreshes Launch Services.

Use `--source`, `--target`, `--identifier`, and `--languages` to override defaults. Show the resolved values before applying them.

## Launch and verify

```bash
python3 <script> launch --apply
python3 <script> status
```

Completion requires visible evidence of two independently running windows plus a status readback showing different bundle identifiers. A new login window is expected; never enter account credentials for the user.

## Repair after an update

The copied bundle does not update with the source. Compare versions first. If the duplicate files are intact but identity/signature metadata is wrong:

```bash
python3 <script> repair --apply
```

If the source app has a newer version, propose creating a fresh target at a new path, verifying it, and only then archiving the old duplicate. Do not silently merge application bundles.

## Language preference

```bash
python3 <script> --languages zh-Hans en set-language --apply
```

Quit and relaunch the duplicate before judging the result. The preference is scoped to the duplicate identifier; verify the identifier in status output.

## Distinct icon

Icon recoloring is optional and requires Pillow plus the macOS `iconutil` command:

```bash
python3 <script> recolor-icon --color '#2878d0' --apply
```

The helper decodes the official icon locally, remaps green pixels to the selected hue, replaces icon resources only inside the duplicate, signs it again, and writes a preview PNG next to the target. Review the preview and the visible Finder/Dock result. Cached icons may require quitting the duplicate or revisiting the folder.

The original icon is not redistributed by this repository; it is read from the user's installed application at runtime.

## Verification checklist

- Source path, identifier, version, and signature remain unchanged.
- Target path exists and has the requested different identifier.
- `codesign --verify --deep --strict <target>` succeeds.
- Both processes can be distinguished by executable path.
- The user can tell which window is the duplicate before entering credentials.
- No injector, modified source executable, privileged installer, or third-party binary was introduced.

Report notification uncertainty and the fact that a future application update may invalidate the copy.
