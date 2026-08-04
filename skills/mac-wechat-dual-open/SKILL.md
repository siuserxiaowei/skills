---
name: mac-wechat-dual-open
description: |
  Build, check, fix, and refine a second WeChat app on macOS. Duplicate the
  WeChat bundle, swap its bundle identifier, ad-hoc re-sign it, start the
  extra instance, apply Chinese language preferences, and tint only the
  duplicate's icon from WeChat green to blue. Use when the user asks whether
  Mac WeChat dual-open methods are reliable, wants to double-open WeChat,
  needs WeChat-2 language/icon/cache issues fixed, or wants the second
  WeChat visually distinct without installing third-party injection tools.
---

# Running Two WeChat Instances on macOS

Run two WeChat accounts side by side on macOS by giving the system a second,
separately identified copy of the app.

## How It Works

macOS tells applications apart through the bundle identifier, so the whole
trick comes down to handing the system a clone whose identity differs from
the original. Once the clone has its own bundle ID and a fresh local
signature, it runs as an independent app next to the real WeChat:

1. Duplicate `/Applications/WeChat.app` into `~/Applications/WeChat-2.app`.
2. Rewrite the duplicate's `CFBundleIdentifier` (for example `com.tencent.xin2`).
3. Sign the duplicate again using `codesign --force --deep --sign -`.
4. Start the duplicate by invoking its executable directly.

Everything stays local: no third-party injection tools and no patched
binaries are involved.

## Prerequisites

- macOS 12 or later, with WeChat present at `/Applications/WeChat.app`
- Python 3.10 or newer (the system interpreter is fine)
- Pillow (`pip3 install Pillow`) — used solely by `recolor-icon`
- Xcode Command Line Tools (`xcode-select --install`) — provides `codesign`, `iconutil`, `sips`

## Finding the Helper Script

Relative to this skill's folder, the helper sits at
`scripts/wechat_dual_open.py`. Since each agent drops skills into its own
location, work out the absolute path on the fly instead of hardcoding it:

```bash
# Auto-detect skill directory
SKILL_DIR="$(dirname "$(find ~ -path '*/mac-wechat-dual-open/SKILL.md' -maxdepth 4 2>/dev/null | head -1)")"
SCRIPT="$SKILL_DIR/scripts/wechat_dual_open.py"
```

## Quick Commands

```bash
python3 "$SCRIPT" status          # Check current state
python3 "$SCRIPT" create          # Create the second WeChat
python3 "$SCRIPT" set-language --languages zh-Hans en   # Set Chinese
python3 "$SCRIPT" recolor-icon --blue "#1296db"         # Blue icon
python3 "$SCRIPT" launch          # Start the second instance
python3 "$SCRIPT" repair          # Fix bundle id, signing, language, caches
```

Built-in defaults (change them via `--source-app`, `--target-app`, `--bundle-id`):

- Source: `/Applications/WeChat.app`
- Target: `~/Applications/WeChat-2.app`
- Bundle ID: `com.tencent.xin2`

## Recommended Sequence

1. **Inspect the state first.** `status` shows what is already in place.
2. **Build the copy.** When no second app exists yet, run `create`. It
   duplicates the app, rewrites the bundle ID, applies the Chinese language
   preference, strips `CFBundleIconName`, re-signs, and registers the result
   with Launch Services.
3. **Fix the language.** When the second instance comes up in English, run
   `set-language` and then restart that instance.
4. **Tint the icon.** `recolor-icon` turns the WeChat green into a blue of
   the user's choice. Both the outer `AppIcon.icns` and the embedded
   `WeChatAppEx.app/.../app.icns` are covered; `CFBundleIconName` is removed
   so stale `Assets.car` entries cannot shadow the new icon; and when the
   Carbon-era tools (`DeRez`, `Rez`, `SetFile`) happen to be installed, a
   Finder custom icon is set as well.
5. **Start it.** Run `launch`. A second WeChat window with its own login
   prompt should appear; pin it to the Dock as a separate entry from the
   original.

## How Reliable Is It

Treat this as an unofficial technique, roughly 6.5–7 out of 10 on the
reliability scale:

- Succeeds across many macOS and WeChat version pairings.
- Nothing is injected and no tweaks are installed, so it is easy to audit
  and to reverse.
- **A WeChat update breaks the copy.** After the original app updates, run
  `create` again (or `repair`).
- Push notifications can be flaky because APNs stays bound to the original
  app identity.
- Login state and Keychain entries are kept apart per bundle ID.
- Ad-hoc signing can stop working if WeChat ever enforces stricter
  signature validation.

The deeper write-up lives in `references/reliability-and-risks.md`.

## Icon Pitfalls

WeChat keeps its icon in several spots, and every one of them is handled by
the script:

| Where it lives | What it controls |
|----------------|------------------|
| `Contents/Resources/AppIcon.icns` | Main app icon |
| `Contents/MacOS/WeChatAppEx.app/Contents/Resources/app.icns` | Icon used by the embedded runtime |
| `Contents/Resources/Assets.car` | Asset catalog (neutralized by deleting `CFBundleIconName`) |
| `Icon\r` plus the Finder custom-icon attribute | How Finder shows the app under "Applications" |

When the user says the icon is still green:

- Maybe they opened `/Applications/WeChat.app` (the original) instead of
  `~/Applications/WeChat-2.app`. Confirm with `open -R ~/Applications/WeChat-2.app`.
- The Dock remembers icons per process. Fully quit WeChat-2 and start it again.
- Setting a Finder custom icon depends on `DeRez`/`Rez`/`SetFile`, which are
  often absent on macOS 13 and later; the script moves on without them, and
  swapping the icns file alone is normally enough.

## Safety

- **Never touch `/Applications/WeChat.app`** — every change stays confined
  to the copy.
- Get the user's consent before removing an existing second app; reach for
  `repair` instead of delete-and-recreate.
- Signing has to happen **before** a Finder custom icon is attached; doing it
  the other way around makes macOS refuse the bundle with "resource fork,
  Finder information, or similar detritus not allowed".

## Technical Notes

- Icon recoloring rotates hue in HSV/HLS space through Pillow.
- The Finder custom icon step relies on the classic Carbon resource tools
  (`DeRez`/`Rez`).
