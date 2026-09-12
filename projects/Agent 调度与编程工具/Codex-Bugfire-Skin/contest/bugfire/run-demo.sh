#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
if [ -d "$PROJECT_ROOT/macos/scripts" ]; then
  ENGINE_ROOT="$PROJECT_ROOT/macos"
elif [ -d "$PROJECT_ROOT/scripts" ]; then
  ENGINE_ROOT="$PROJECT_ROOT"
else
  printf 'Could not locate BUGFIRE engine from %s\n' "$PROJECT_ROOT" >&2
  exit 1
fi
DEMO_ROOT="$PROJECT_ROOT/contest/bugfire/demo"
DIRECTOR="$ENGINE_ROOT/scripts/bugfire-director.mjs"
COMPILER="$ENGINE_ROOT/scripts/bugfire-pack.mjs"
CUSTOMIZER="$PROJECT_ROOT/skills/codex-bugfire-customizer/scripts/create-pack.mjs"
INJECTOR="$ENGINE_ROOT/scripts/injector.mjs"
OUTPUT=""
LIVE_CYCLE="false"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output) OUTPUT="${2:-}"; shift 2 ;;
    --live-cycle) LIVE_CYCLE="true"; shift ;;
    *) printf 'Unknown demo argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

if [ -z "$OUTPUT" ]; then
  DEMO_TEMP_ROOT="${TMPDIR:-/private/tmp}"
  DEMO_TEMP_ROOT="$(cd "$DEMO_TEMP_ROOT" && pwd -P)"
  OUTPUT="$(/usr/bin/mktemp -d "$DEMO_TEMP_ROOT/bugfire-vibelab-demo.XXXXXX")"
else
  OUTPUT="$(cd "$(dirname "$OUTPUT")" && pwd -P)/$(basename "$OUTPUT")"
  if [ -d "$OUTPUT" ] && [ -n "$(/bin/ls -A "$OUTPUT")" ]; then
    printf 'Demo output must be absent or empty: %s\n' "$OUTPUT" >&2
    exit 1
  fi
  /bin/mkdir -p "$OUTPUT"
fi

TRANSCRIPT="$OUTPUT/DEMO_TRANSCRIPT.txt"
exec > >(/usr/bin/tee "$TRANSCRIPT") 2>&1

run() {
  printf '\n$'
  printf ' %q' "$@"
  printf '\n'
  "$@"
}

printf 'BUGFIRE Character Director · reproducible contest demo\n'
printf 'Boundary: AI proposes -> operator rejects/changes -> deterministic validator -> builder -> preview.\n'
printf 'Output: %s\n' "$OUTPUT"

run node "$DIRECTOR" verify-fixture \
  "$DEMO_ROOT/ai-draft-plan.json" "$DEMO_ROOT/ai-draft-plan.sha256" "$DEMO_ROOT/brief.json"
run node "$DIRECTOR" review \
  "$DEMO_ROOT/ai-draft-plan.json" "$DEMO_ROOT/human-review.json" \
  "$DEMO_ROOT/brief.json" "$OUTPUT/reviewed-plan.json"
run /usr/bin/cmp "$OUTPUT/reviewed-plan.json" "$DEMO_ROOT/reviewed-plan.json"

/bin/mkdir -p "$OUTPUT/pack-source/assets"
run /bin/cp "$DEMO_ROOT/assets/background.png" "$OUTPUT/pack-source/assets/background.png"
run /bin/cp "$DEMO_ROOT/assets/pet-idle.png" "$OUTPUT/pack-source/assets/pet-idle.png"
run node "$DIRECTOR" materialize \
  "$OUTPUT/reviewed-plan.json" "$DEMO_ROOT/brief.json" "$OUTPUT/pack-source"
run node "$COMPILER" validate "$OUTPUT/pack-source"
run node "$COMPILER" build "$OUTPUT/pack-source" "$OUTPUT/compiled-pack"
run node "$CUSTOMIZER" preview "$OUTPUT/compiled-pack" "$OUTPUT/preview.html"
run node "$INJECTOR" --check-payload --theme-dir "$OUTPUT/compiled-pack"

if [ "$LIVE_CYCLE" = "true" ]; then
  if [ "${BUGFIRE_CONFIRM_LIVE_CYCLE:-}" != "YES" ]; then
    printf 'Live cycle requires BUGFIRE_CONFIRM_LIVE_CYCLE=YES because it may restart Codex.\n' >&2
    exit 1
  fi
  run "$ENGINE_ROOT/scripts/install-bugfire-pack-macos.sh" --pack "$OUTPUT/pack-source"
  run "$ENGINE_ROOT/scripts/verify-dream-skin-macos.sh" --reload
  run "$ENGINE_ROOT/scripts/restore-dream-skin-macos.sh" --restore-base-theme --restart-codex
else
  printf '\nLIVE CYCLE: not run. Offline mode never changes Codex or user configuration, so no restore is needed.\n'
  printf 'For an explicitly authorized recording only:\n'
  printf '  BUGFIRE_CONFIRM_LIVE_CYCLE=YES %q --output %q --live-cycle\n' "$0" "${OUTPUT}-live"
fi

run node -e '
  const fs = require("node:fs");
  const path = require("node:path");
  const output = process.argv[1];
  const plan = JSON.parse(fs.readFileSync(path.join(output, "reviewed-plan.json"), "utf8"));
  const report = JSON.parse(fs.readFileSync(path.join(output, "compiled-pack", "pack-report.json"), "utf8"));
  const result = {
    pass: true,
    generationMode: plan.provenance.mode,
    liveAiClaimed: false,
    humanDecisionChanged: plan.humanReview.rejectedDecisionId,
    beforeAccent: plan.humanReview.originalDecision.manifestPatch["/theme/colors/accent"],
    afterAccent: plan.manifestProposal.theme.colors.accent,
    deterministicValidation: report.pass,
    preview: path.join(output, "preview.html"),
    liveCycle: process.argv[2] === "true" ? "completed" : "not-run-offline",
  };
  fs.writeFileSync(path.join(output, "demo-result.json"), `${JSON.stringify(result, null, 2)}\n`, { mode: 0o600 });
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
' "$OUTPUT" "$LIVE_CYCLE"

printf '\nPASS: reproducible director fixture, rejection, materialization, validation, build and preview.\n'
printf 'Open preview: %s/preview.html\n' "$OUTPUT"
