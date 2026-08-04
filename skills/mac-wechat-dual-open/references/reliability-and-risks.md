# Reliability and Risk Notes

Read this before judging a public Mac WeChat dual-open tutorial, or when a
user needs the tradeoffs spelled out.

## What Most Tutorials Actually Do

The posts that look trustworthy almost all boil down to the same handful of
commands:

```bash
cp -R /Applications/WeChat.app ~/Applications/WeChat-2.app
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.tencent.xin2" \
  ~/Applications/WeChat-2.app/Contents/Info.plist
codesign --force --deep --sign - ~/Applications/WeChat-2.app
nohup ~/Applications/WeChat-2.app/Contents/MacOS/WeChat >/dev/null 2>&1 &
```

Placing the clone under `~/Applications` means no `sudo` is needed and the
duplicate stays owned by the user. Invoking the executable itself beats
`open -n` here, since WeChat notices and refuses the normal multi-instance
launch route.

## Verdict

Score the approach at roughly **6.5/10 to 7/10**:

- It genuinely works across many macOS and WeChat version pairings.
- No code gets injected and no third-party tweaks get installed.
- Auditing it or undoing it is straightforward.
- There is **no guarantee** it survives WeChat or macOS updates.

## Known Tradeoffs

- **An update invalidates the clone.** Once the original WeChat updates,
  redo the create/repair routine: duplicate again, reapply the bundle ID,
  re-sign, relaunch.
- **Push delivery can be flaky** since APNs and the entitlements remain
  bound to the original app's identity.
- **Login state and Keychain entries stay separate**, partitioned by bundle
  ID.
- **`codesign --force --deep --sign -`** swaps the vendor signature for an
  ad-hoc one. Fine for local use, but it can break the moment WeChat
  enforces stricter signature validation.
- **Pinning to one version is brittle.** Guides that tell you to downgrade
  or freeze a particular WeChat build also cut you off from security fixes
  and age poorly.
- **Third-party tweak/injection tools** carry more risk than this
  copy-and-sign approach.
- **"Comment to receive the script" posts** add nothing — everything below
  is a few plain shell commands.

## How To Answer

When a user asks whether a social media tutorial can be trusted:

1. The mechanism itself is genuine: bundle IDs are how macOS and the app
   data containers tell applications apart.
2. It is unofficial and it will not last forever.
3. Favor running the steps by hand, or through a local script you have read.
4. Only consider downgrading if the current version stops working.
5. Only reach for third-party injection tools when the user has explicitly
   accepted that risk.

## Troubleshooting

| Problem | Why it happens | Remedy |
|---------|----------------|--------|
| The clone launches in English | A fresh bundle ID carries no language setting | Run `defaults write com.tencent.xin2 AppleLanguages -array zh-Hans en` and restart the app |
| "已损坏/无法打开" | Gatekeeper refuses the unsigned bundle | System Settings → Privacy & Security → choose Still Open |
| "应用程序版本过低" | The account was first signed into the wrong instance | Quit both → sign into the original first → then start the copy |
| Finder/Dock still shows green icon | Stale icon caches | See the SKILL.md Icon Pitfalls section |
| WeChat-2 vanishes after an update | The original WeChat updated and the copy is outdated | Run `create` or `repair` again |
