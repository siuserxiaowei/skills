# BUGFIRE Character Director · 72-second recording script

This is a new director-flow video. The older V2 release video may appear for at most a few seconds as labelled engineering context; it must not be presented as proof of the new AI workflow.

## Capture setup

- Use a clean terminal with repository root visible and no secrets, usernames, private paths, chats, or account UI.
- Run the offline demo once before recording so the flow is familiar. For a live provider, hide all environment setup and never show the key.
- Open `brief.json`, `ai-draft-plan.json`, `human-review.json`, and the generated `preview.html` in advance.
- Put the three 1920×1080 boards in the editor timeline; regenerate them offline with `./contest/bugfire/render-boards.sh` if needed.
- The operator must personally type or verbally confirm the palette rejection before the public post says “人工否决”.

## Timeline

| Time | Screen | Voice / caption |
|---:|---|---|
| 0–6 s | Product title + original Patchling Zero brief | “一句‘帮我设计角色’，不应该直接变成可安装资产。” |
| 6–14 s | Show brief rights + constraints | “先锁定原创 brief、禁止已知 IP、素材权利和验证边界。” |
| 14–23 s | Run `verify-fixture`; zoom `recorded-agent-fixture` and checksum | “这是 Codex agent 实际产出的离线 AI 草案；重放不冒充实时 API。” |
| 23–31 s | Show AI decision `alert-first-palette`, orange `#ff7a1a` | “AI 选告警橙当主色，但待机界面会一直像故障。” |
| 31–40 s | Operator edits/confirms `human-review.json`, cyan `#35d9d1` | “我否决这项，改成电路青，橙色只留给真正警报。” |
| 40–47 s | Run `review` with the same brief; show `human-approved` and decision ID | “review 会重新绑定 brief；跳过 fixture 校验也不能换掉 rights。” |
| 47–57 s | Run `materialize` with the brief again, then `bugfire-pack validate` | “materialize 再核一次 brief；人工改完也不能绕过字段、路径、图片和权利校验。” |
| 57–65 s | Run build; open `preview.html`; click idle / bug / fire / success | “同一份 plan 生成本地包和六态离线预览。” |
| 65–69 s | Show renderer payload `pass: true` | “只有 verifier 返回 pass，才叫可运行证据。” |
| 69–72 s | Restore command / offline no-change notice + GitHub URL | “离线模式不改 Codex；live 录制结束立即 restore。” |

Suggested board placement: `01-ai-draft.png` at 14–31 s, `02-human-rejection.png` at 31–47 s, and `03-pack-preview.png` at 57–69 s. Cut back to live terminal output whenever a claim needs executable evidence.

## Terminal commands

For the compact offline recording:

```bash
./contest/bugfire/run-demo.sh
```

To show each checkpoint slowly, run the same commands printed in `DEMO_TRANSCRIPT.txt` one by one.

For an explicitly authorized live install / verify / restore recording:

```bash
BUGFIRE_CONFIRM_LIVE_CYCLE=YES \
  ./contest/bugfire/run-demo.sh --output /tmp/bugfire-live-demo --live-cycle
```

The live flag may restart Codex. Do not run it silently. Publish a live claim only if verify returns `pass: true` and the restore command completes.

## Final on-screen evidence

Keep these visible together for the last frame:

- `humanDecisionChanged: "alert-first-palette"`
- `beforeAccent: "#ff7a1a"`
- `afterAccent: "#35d9d1"`
- `deterministicValidation: true`
- public repository URL
