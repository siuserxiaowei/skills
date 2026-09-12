import assert from "node:assert/strict";
import { execFile, spawn } from "node:child_process";
import { once } from "node:events";
import { mkdir, mkdtemp, readFile, readdir, rm, stat, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import test from "node:test";

const execFileAsync = promisify(execFile);
const ROOT = new URL("../", import.meta.url);
const COMMON_PATH = fileURLToPath(new URL("scripts/common-macos.sh", ROOT));
const injector = await readFile(new URL("scripts/injector.mjs", ROOT), "utf8");
const common = await readFile(new URL("scripts/common-macos.sh", ROOT), "utf8");
const restore = await readFile(new URL("scripts/restore-dream-skin-macos.sh", ROOT), "utf8");
const startScript = await readFile(new URL("scripts/start-dream-skin-macos.sh", ROOT), "utf8");
const switchTheme = await readFile(new URL("scripts/switch-theme-macos.sh", ROOT), "utf8");
const installPack = await readFile(new URL("scripts/install-bugfire-pack-macos.sh", ROOT), "utf8");

function sourceBetween(start, end) {
  const startIndex = injector.indexOf(start);
  assert.notEqual(startIndex, -1, `missing source marker: ${start}`);
  const endIndex = injector.indexOf(end, startIndex + start.length);
  assert.notEqual(endIndex, -1, `missing source marker: ${end}`);
  return injector.slice(startIndex, endIndex);
}

test("binding settlement reloads persisted progress and commits memory only after atomic save", () => {
  const binding = sourceBetween(
    "async function installBugfireBinding",
    "async function removeFromSession",
  );
  const transaction = binding.slice(binding.indexOf("runtime.queue = runtime.queue.then"));
  const reloadIndex = transaction.indexOf("loadProgress(");
  const resetIndex = transaction.indexOf("resetProgress(");
  const settleIndex = transaction.indexOf("settleBuild(");
  const guardIndex = transaction.indexOf("assertLockHeld()", settleIndex);
  const saveIndex = transaction.indexOf("await saveProgress(");
  const postSaveGuardIndex = transaction.indexOf("assertLockHeld()", saveIndex);
  const memoryCommitIndex = transaction.indexOf("runtime.progress =");

  assert.notEqual(reloadIndex, -1, "each queued transaction must reload the persisted state");
  assert.notEqual(resetIndex, -1, "reset must be settled inside the transaction");
  assert.notEqual(settleIndex, -1, "Build outcomes must be settled inside the transaction");
  assert.notEqual(saveIndex, -1, "the transaction must await its atomic save");
  assert.notEqual(guardIndex, -1, "the transaction must verify the kernel lock before saving");
  assert.notEqual(postSaveGuardIndex, -1, "the transaction must verify the kernel lock after saving");
  assert.notEqual(memoryCommitIndex, -1, "the saved state must then become runtime.progress");
  assert.ok(reloadIndex < resetIndex, "reload must happen before reset settlement");
  assert.ok(reloadIndex < settleIndex, "reload must happen before Build settlement");
  assert.ok(resetIndex < saveIndex, "reset settlement must happen before save");
  assert.ok(settleIndex < saveIndex, "Build settlement must happen before save");
  assert.ok(guardIndex < saveIndex, "the holder must still own the kernel lock before save");
  assert.ok(saveIndex < memoryCommitIndex, "runtime.progress must not change until save succeeds");
  assert.ok(postSaveGuardIndex < memoryCommitIndex,
    "memory must not commit after an unexpectedly lost kernel lock");
});

test("authoritative settlement broadcasts preserve the renderer event identity", () => {
  const binding = sourceBetween(
    "async function installBugfireBinding",
    "async function removeFromSession",
  );

  assert.match(binding, /result\s*=\s*\{[\s\S]*?\.\.\.settlement,[\s\S]*?eventId\s*:\s*event\.eventId,[\s\S]*?outcome\s*:\s*event\.outcome,[\s\S]*?\}/);
  assert.match(binding, /await\s+broadcast\([^)]*result[^)]*\)/);
});

test("watch shutdown drains pending writes, removes bindings, then closes sessions", () => {
  const watch = sourceBetween("async function runWatch", "\ntry {");
  const shutdown = watch.slice(watch.lastIndexOf("while (!stopping)"));
  const drainIndex = shutdown.indexOf("await runtime.queue");
  const removeIndex = Math.max(
    shutdown.indexOf("Runtime.removeBinding"),
    shutdown.indexOf("removeBugfireBinding"),
  );
  const closeIndex = shutdown.lastIndexOf("session.close()");

  assert.notEqual(drainIndex, -1, "shutdown must await the serialized persistence queue");
  assert.notEqual(removeIndex, -1, "shutdown must remove the Runtime binding");
  assert.notEqual(closeIndex, -1, "shutdown must close each CDP session");
  assert.ok(drainIndex < removeIndex, "pending saves must finish before bindings are removed");
  assert.ok(removeIndex < closeIndex, "Runtime.removeBinding must happen before session.close");
  assert.match(injector, /Runtime\.removeBinding/);
});

test("remove and verification both cover the renderer binding global", () => {
  const remove = sourceBetween("async function removeFromSession", "async function verifyRemovedSession");
  const verify = sourceBetween("async function verifyRemovedSession", "async function verifySession");

  assert.match(remove, /delete\s+window(?:\.__bugfireSync|\[['"]__bugfireSync['"]\])/);
  assert.match(verify, /window(?:\.__bugfireSync|\[['"]__bugfireSync['"]\])/);
  assert.match(verify, /(?:!|typeof)[^\n;]*window(?:\.__bugfireSync|\[['"]__bugfireSync['"]\])/);
});

test("reload reinjection failures evict and close the session so watch can reconnect", () => {
  const watch = sourceBetween("async function runWatch", "\ntry {");
  const handlerStart = watch.indexOf("session.on(\"Page.loadEventFired\"");
  assert.notEqual(handlerStart, -1, "runWatch must register a reload handler");
  const initialApply = watch.indexOf("await applyCurrent(session)", handlerStart);
  assert.notEqual(initialApply, -1, "missing initial injection marker after reload handler");
  const handler = watch.slice(handlerStart, initialApply);

  assert.match(handler, /catch\s*\([^)]*\)\s*(?:=>)?\s*\{/);
  assert.match(handler, /sessions\.delete\(target\.id\)/);
  assert.match(handler, /session\.close\(\)/);
});

test("Restore stops known injectors even when state.json is missing", () => {
  const recordedStop = restore.indexOf("stop_recorded_injector");
  const knownStop = restore.indexOf("stop_known_injectors");
  const rendererCleanup = restore.indexOf("CODEX_RUNNING=");
  assert.notEqual(recordedStop, -1, "Restore should still use a valid state record when present");
  assert.notEqual(knownStop, -1, "Restore must have an unconditional fallback cleanup");
  assert.notEqual(rendererCleanup, -1);
  assert.ok(knownStop > recordedStop && knownStop < rendererCleanup);
  assert.doesNotMatch(
    restore.slice(restore.lastIndexOf("\n", knownStop - 1) + 1, restore.indexOf("\n", knownStop)),
    /\[\s+-f\s+"?\$STATE_PATH/,
    "known injector cleanup must not depend on state.json",
  );

  const start = common.indexOf("stop_known_injectors() {");
  const end = common.indexOf("\nlaunch_injector_daemon()", start);
  assert.notEqual(start, -1, "common-macos must define stop_known_injectors");
  assert.notEqual(end, -1);
  const cleanup = common.slice(start, end);
  const matcherStart = common.indexOf("known_injector_command() {");
  const snapshotStart = common.indexOf("known_injector_snapshot() {");
  const stopperStart = common.indexOf("stop_process_snapshot() {");
  const recordedStart = common.indexOf("stop_recorded_injector() {");
  assert.notEqual(matcherStart, -1);
  assert.notEqual(snapshotStart, -1);
  assert.notEqual(stopperStart, -1);
  assert.notEqual(recordedStart, -1);
  const matcher = common.slice(matcherStart, snapshotStart);
  const snapshot = common.slice(snapshotStart, stopperStart);
  const stopper = common.slice(stopperStart, recordedStart);
  assert.match(cleanup, /remove_injector_launchd_job/);
  assert.match(common, /launchctl\s+remove[^\n]*INJECTOR_JOB_LABEL/);
  assert.match(cleanup, /ps\s+-axo\s+pid=,command=/);
  assert.match(matcher, /INJECTOR/);
  assert.match(matcher, /NODE/);
  assert.match(matcher, /--watch\s+--port/);
  assert.match(stopper, /kill\s+-TERM/);
  assert.match(stopper, /kill\s+-KILL/);
  assert.doesNotMatch(cleanup, /local\s+-a\b|\$\{[^}]*\[@\]\}/,
    "Restore cleanup must remain compatible with macOS Bash 3.2 + set -u");
  assert.match(stopper, /process_matches_snapshot/g,
    "each signal path must revalidate the exact process identity");
  assert.match(cleanup, /known_injector_snapshot/,
    "candidate discovery must retain command and start-time identity");
  assert.match(snapshot, /process_started_at[\s\S]*command=[\s\S]*process_started_at/,
    "snapshot discovery must bracket the command read with start-time reads");
});

test("Restore fallback is safe under stock macOS Bash 3.2 with no matching process", async () => {
  const script = [
    'source "$1"',
    'NODE="/tmp/bugfire-no-such-node"',
    'INJECTOR="/tmp/bugfire-no-such-injector.mjs"',
    'THEME_DIR="/tmp/bugfire-no-such-theme"',
    'remove_injector_launchd_job() { :; }',
    "stop_known_injectors",
  ].join("\n");
  const result = await execFileAsync("/bin/bash", ["-uc", script, "bugfire-test", COMMON_PATH], {
    encoding: "utf8",
    timeout: 5_000,
  });
  assert.equal(result.stderr, "");
});

test("injector matching requires the exact production argv and process identity", async () => {
  const script = [
    'source "$1"',
    'NODE="/tmp/bugfire node"',
    'INJECTOR="/tmp/bugfire injector.mjs"',
    'THEME_DIR="/tmp/bugfire theme"',
    'known_injector_command "$NODE $INJECTOR --watch --port 9341 --theme-dir $THEME_DIR"',
    '! known_injector_command "$NODE $INJECTOR --watchdog --port 9341 --theme-dir $THEME_DIR"',
    '! known_injector_command "$NODE $INJECTOR --watch --port 9341 --theme-dir $THEME_DIR extra"',
    'pid="$$"',
    'started="$(process_started_at "$pid")"',
    'command_line="$(/bin/ps -p "$pid" -o command=)"',
    'process_matches_snapshot "$pid" "$started" "$command_line"',
    '! process_matches_snapshot "$pid" "Mon Jan 1 00:00:00 1990" "$command_line"',
  ].join("\n");
  await execFileAsync("/bin/bash", ["-uc", script, "bugfire-test", COMMON_PATH], {
    encoding: "utf8",
    timeout: 5_000,
  });
});

test("a TERM-triggered exec cannot be mistaken for the original injector at KILL time", {
  skip: process.platform !== "darwin",
}, async (context) => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "bugfire-pid-identity-"));
  const fixturePath = path.join(directory, "injector-fixture.sh");
  const themeDir = path.join(directory, "theme");
  await writeFile(fixturePath, [
    "#!/bin/bash",
    "trap 'exec /bin/sleep 30' TERM",
    "printf 'READY\\n'",
    "while :; do read -t 1 _ || true; done",
    "",
  ].join("\n"), { mode: 0o700 });

  const fixture = spawn("/bin/bash", [
    fixturePath, "--watch", "--port", "9341", "--theme-dir", themeDir,
  ], { stdio: ["pipe", "pipe", "pipe"] });
  context.after(async () => {
    if (fixture.exitCode === null && fixture.signalCode === null) fixture.kill("SIGKILL");
    if (fixture.exitCode === null && fixture.signalCode === null) await once(fixture, "exit");
    await rm(directory, { recursive: true, force: true });
  });
  fixture.stdout.setEncoding("utf8");
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("identity fixture did not start")), 2_000);
    fixture.stdout.on("data", (chunk) => {
      if (!chunk.includes("READY\n")) return;
      clearTimeout(timer);
      resolve();
    });
    fixture.once("exit", (code, signal) => reject(new Error(`fixture exited (${code ?? signal})`)));
  });

  const startedAt = (await execFileAsync("/bin/ps", [
    "-p", String(fixture.pid), "-o", "lstart=",
  ], { encoding: "utf8" })).stdout.trim().replace(/\s+/g, " ");
  const expectedCommand = [
    "/bin/bash", fixturePath, "--watch", "--port", "9341", "--theme-dir", themeDir,
  ].join(" ");
  const stopScript = [
    'source "$1"',
    'stop_process_snapshot "$2" "$3" "$4"',
  ].join("\n");
  await execFileAsync("/bin/bash", [
    "-uc", stopScript, "bugfire-test", COMMON_PATH,
    String(fixture.pid), startedAt, expectedCommand,
  ], { encoding: "utf8", timeout: 5_000 });

  const commandAfterTerm = (await execFileAsync("/bin/ps", [
    "-p", String(fixture.pid), "-o", "command=",
  ], { encoding: "utf8" })).stdout.trim();
  assert.equal(commandAfterTerm, "/bin/sleep 30",
    "identity changes must stop cleanup before the KILL fallback");
});

test("every watcher replacement uses the identity-safe fallback cleanup", () => {
  const hotStart = common.indexOf("hot_reapply_theme() {");
  const hotEnd = common.indexOf("\nrelease_codex_launchd_job()", hotStart);
  assert.notEqual(hotStart, -1);
  assert.notEqual(hotEnd, -1);
  const hotReapply = common.slice(hotStart, hotEnd);
  const recorded = hotReapply.indexOf("stop_recorded_injector");
  const known = hotReapply.indexOf("stop_known_injectors");
  const launch = hotReapply.indexOf("launch_injector_daemon");
  assert.ok(recorded !== -1 && known > recorded && launch > known,
    "hot reapply must stop recorded and orphan injectors before replacement");
  assert.doesNotMatch(hotReapply, /ps\s+-axo|awk\s+-v\s+inj|kill\s+-TERM/,
    "hot reapply must not bypass the exact identity helpers");

  const startRecorded = startScript.indexOf("stop_recorded_injector");
  const startKnown = startScript.indexOf("stop_known_injectors");
  const startLaunch = startScript.indexOf("launch_injector_daemon");
  assert.ok(startRecorded !== -1 && startKnown > startRecorded && startLaunch > startKnown,
    "cold start must clean orphan watchers even when state.json is absent");
  const knownLine = startScript.slice(
    startScript.lastIndexOf("\n", startKnown - 1) + 1,
    startScript.indexOf("\n", startKnown),
  );
  assert.doesNotMatch(knownLine, /\[\s+-f\s+"?\$STATE_PATH/,
    "orphan cleanup must be unconditional");
});

test("theme switching stops identity-checked watchers before atomic activation", () => {
  const sourceValidation = switchTheme.indexOf("--check-payload --theme-dir \"$SRC\"");
  const noApply = switchTheme.indexOf('if [ "$APPLY_NOW" != "true" ]');
  const recordedStop = switchTheme.indexOf("stop_recorded_injector", noApply);
  const knownStop = switchTheme.indexOf("stop_known_injectors", noApply);
  const activation = switchTheme.indexOf('activate_theme_from_directory "$SRC"', noApply);

  assert.ok(sourceValidation !== -1 && noApply > sourceValidation,
    "library payload must validate before the no-apply decision");
  assert.ok(recordedStop > noApply && knownStop > recordedStop && activation > knownStop,
    "watchers must stop through identity-safe helpers immediately before active mutation");
  assert.doesNotMatch(switchTheme, /find\s+"\$THEME_DIR"[^\n]*-delete|cp\s+-f[^\n]*\$THEME_DIR/,
    "switching must not clear or copy directly into the live directory");
  assert.match(switchTheme.slice(noApply, recordedStop), /exit\s+0/,
    "--no-apply must exit before watcher cleanup or active mutation");
});

test("theme notifications pass untrusted names as data, never AppleScript source", () => {
  assert.match(switchTheme, /system attribute ["']DREAM_SKIN_NOTIFICATION["']/);
  assert.match(switchTheme, /DREAM_SKIN_NOTIFICATION="\$\*"/);
  assert.doesNotMatch(switchTheme, /osascript\s+-e\s+"[^"]*\$\*/,
    "pack-controlled theme names must never be interpolated into AppleScript source");
});

test("theme activation stages, validates, atomically renames, and has rollback", () => {
  const start = common.indexOf("activate_theme_from_directory() {");
  const end = common.indexOf("\nhot_reapply_theme() {", start);
  assert.notEqual(start, -1);
  assert.notEqual(end, -1);
  const activation = common.slice(start, end);

  assert.match(activation, /mktemp\s+-d\s+"\$STATE_ROOT\/\.theme-swap\.XXXXXX"/);
  assert.match(activation, /cp\s+-R\s+"\$source_dir\/\."\s+"\$staged_dir\/"/);
  assert.match(activation, /--check-payload\s+--theme-dir\s+"\$staged_dir"/,
    "the exact staged bytes must validate before any active rename");
  const preserve = activation.indexOf('mv "$THEME_DIR" "$previous_dir"');
  const swap = activation.indexOf('mv "$staged_dir" "$THEME_DIR"');
  const rollback = activation.indexOf('mv "$previous_dir" "$THEME_DIR"', swap);
  assert.ok(preserve !== -1 && swap > preserve && rollback > swap,
    "the previous directory must be retained until the staged rename succeeds");
});

test("atomic activation changes only complete themes and leaves no transaction", async (context) => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "bugfire-theme-swap-"));
  const stateRoot = path.join(directory, "state");
  const source = path.join(directory, "source");
  const badSource = path.join(directory, "bad-source");
  const validator = path.join(directory, "validate-theme.sh");
  await mkdir(path.join(stateRoot, "theme"), { recursive: true });
  await mkdir(source, { recursive: true });
  await mkdir(badSource, { recursive: true });
  await writeFile(path.join(stateRoot, "theme", "old.txt"), "old\n");
  await writeFile(path.join(source, "theme.json"), "{\"name\":\"new\"}\n");
  await writeFile(path.join(source, "payload.ok"), "ok\n");
  await writeFile(path.join(badSource, "theme.json"), "{\"name\":\"bad\"}\n");
  await writeFile(validator, [
    "#!/bin/bash",
    "set -eu",
    '[ "$1" = "--check-payload" ]',
    '[ "$2" = "--theme-dir" ]',
    '[ -s "$3/theme.json" ]',
    '[ -s "$3/payload.ok" ]',
    "",
  ].join("\n"));
  context.after(() => rm(directory, { recursive: true, force: true }));

  const activationScript = [
    'source "$1"',
    'STATE_ROOT="$2"',
    'THEME_DIR="$STATE_ROOT/theme"',
    'START_ERROR_LOG="$STATE_ROOT/start-error.log"',
    'NODE="/bin/bash"',
    'INJECTOR="$3"',
    'activate_theme_from_directory "$4"',
  ].join("\n");
  await execFileAsync("/bin/bash", [
    "-uc", activationScript, "bugfire-test", COMMON_PATH, stateRoot, validator, source,
  ], { encoding: "utf8", timeout: 5_000 });

  assert.equal(await readFile(path.join(stateRoot, "theme", "theme.json"), "utf8"),
    "{\"name\":\"new\"}\n");
  await assert.rejects(readFile(path.join(stateRoot, "theme", "old.txt")));
  assert.equal((await stat(path.join(stateRoot, "theme"))).mode & 0o777, 0o700);
  assert.equal((await stat(path.join(stateRoot, "theme", "theme.json"))).mode & 0o777, 0o600);
  assert.deepEqual((await readdir(stateRoot)).filter((entry) => entry.startsWith(".theme-swap.")), []);

  await assert.rejects(execFileAsync("/bin/bash", [
    "-uc", activationScript, "bugfire-test", COMMON_PATH, stateRoot, validator, badSource,
  ], { encoding: "utf8", timeout: 5_000 }));
  assert.equal(await readFile(path.join(stateRoot, "theme", "theme.json"), "utf8"),
    "{\"name\":\"new\"}\n", "failed staged validation must preserve the active theme");
  assert.deepEqual((await readdir(stateRoot)).filter((entry) => entry.startsWith(".theme-swap.")), []);
});

test("pack installation mutates only its library until switch delegates activation", () => {
  const build = installPack.indexOf("bugfire-pack.mjs\" build");
  const applyBranch = installPack.indexOf('if [ "$APPLY_NOW" = "true" ]', build);
  const delegate = installPack.indexOf('switch-theme-macos.sh\" --id "$PACK_ID"', applyBranch);
  assert.ok(build !== -1 && applyBranch > build && delegate > applyBranch,
    "a validated library build must finish before switch-theme performs activation");
  assert.match(installPack.slice(applyBranch, delegate), /APPLY_NOW/,
    "--no-apply must skip the activation delegate");
  assert.doesNotMatch(installPack, /THEME_DIR|bugfire-progress|KEEP_PROGRESS|--keep-progress/,
    "the installer must neither touch active files nor make progress-retention assumptions");
  assert.doesNotMatch(installPack, /hot_reapply_theme|start-dream-skin-macos/,
    "all activation behavior belongs to switch-theme-macos.sh");
});
