import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import fs, { readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import test from "node:test";

const ROOT = new URL("../", import.meta.url);
const ROOT_PATH = fileURLToPath(ROOT);
const INJECTOR = path.join(ROOT_PATH, "scripts", "injector.mjs");
const BUNDLED_BACKGROUND = path.join(ROOT_PATH, "assets", "portal-hero.png");
const execFileAsync = promisify(execFile);
const [
  injector,
  common,
  packageSource,
  versionSource,
  renderer,
  clientDeliveryReadme,
  buildClientRelease,
] = await Promise.all([
  readFile(new URL("scripts/injector.mjs", ROOT), "utf8"),
  readFile(new URL("scripts/common-macos.sh", ROOT), "utf8"),
  readFile(new URL("package.json", ROOT), "utf8"),
  readFile(new URL("VERSION", ROOT), "utf8"),
  readFile(new URL("assets/renderer-inject.js", ROOT), "utf8"),
  readFile(new URL("client-delivery/使用说明.txt", ROOT), "utf8"),
  readFile(new URL("scripts/build-client-release.sh", ROOT), "utf8"),
]);

test("BUGFIRE uses one CDP runtime binding and no extra network listener", () => {
  assert.match(injector, /Runtime\.addBinding/);
  assert.match(injector, /Runtime\.bindingCalled/);
  assert.match(injector, /__bugfireSync/);
  assert.doesNotMatch(injector, /createServer\s*\(/);
  assert.doesNotMatch(injector, /\.listen\s*\(/);
});

test("progress lives under Dream Skin Application Support and is embedded on injection", () => {
  assert.match(injector, /CodexDreamSkinStudio/);
  assert.match(injector, /bugfire-progress\.json/);
  assert.match(injector, /loadProgress/);
  assert.match(injector, /saveProgress/);
  assert.match(injector, /__BUGFIRE_PROGRESS_JSON__/);
  assert.match(renderer, /__BUGFIRE_PROGRESS_JSON__/);
});

test("pack assets are validated, embedded, and exposed to the renderer without remote pet URLs", () => {
  assert.match(injector, /MAX_THEME_BYTES/);
  assert.match(injector, /MAX_PET_ART_BYTES/);
  assert.match(injector, /realpath/);
  assert.match(injector, /isSymbolicLink/);
  assert.match(injector, /__BUGFIRE_ASSETS_JSON__/);
  assert.match(injector, /petAssets/);
  assert.match(injector, /\{\s*ref:\s*existingState\s*\}/);
  assert.doesNotMatch(injector, /https?:\/\/[^`"']+pet/i);
});

async function makeCompiledTheme() {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-injector-theme-"));
  await fs.copyFile(BUNDLED_BACKGROUND, path.join(directory, "background.png"));
  const source = await fs.readFile(BUNDLED_BACKGROUND);
  const targetBytes = 3 * 1024 * 1024;
  const idle = source.length >= targetBytes
    ? source.subarray(0, targetBytes)
    : Buffer.concat([source, Buffer.alloc(targetBytes - source.length)]);
  await fs.writeFile(path.join(directory, "pet-idle.png"), idle);
  const art = Object.fromEntries(
    ["idle", "building", "bug", "fire", "success", "levelUp"].map((state) => [state, "pet-idle.png"]),
  );
  await fs.writeFile(path.join(directory, "theme.json"), JSON.stringify({
    schemaVersion: 1,
    id: "idle-only-test-pack",
    name: "Idle-only Test Pack",
    image: "background.png",
    pet: {
      id: "idle-only-test-pet",
      name: "Idle-only Pet",
      season: "test-season",
      art,
    },
  }));
  return directory;
}

test("a 3 MiB idle-only pet is counted and embedded once across all six state aliases", async () => {
  const directory = await makeCompiledTheme();
  const { stdout } = await execFileAsync(process.execPath, [
    INJECTOR, "--check-payload", "--theme-dir", directory,
  ], { maxBuffer: 12 * 1024 * 1024 });
  const report = JSON.parse(stdout);
  assert.equal(report.pass, true);
  assert.equal(report.petArtBytes, 3 * 1024 * 1024);
  assert.ok(report.petAssetPayloadBytes > 4 * 1024 * 1024);
  assert.ok(report.petAssetPayloadBytes < 4.1 * 1024 * 1024);
  assert.ok(report.payloadBytes < 10 * 1024 * 1024);
});

test("runtime theme loading caps theme.json and rejects symlinked art", async () => {
  const oversized = await makeCompiledTheme();
  await fs.writeFile(path.join(oversized, "theme.json"), Buffer.alloc(128 * 1024 + 1, 0x20));
  await assert.rejects(
    execFileAsync(process.execPath, [INJECTOR, "--check-payload", "--theme-dir", oversized]),
    /Theme config.*128|regular file/i,
  );

  const linked = await makeCompiledTheme();
  await fs.rm(path.join(linked, "pet-idle.png"));
  await fs.symlink(path.join(linked, "background.png"), path.join(linked, "pet-idle.png"));
  await assert.rejects(
    execFileAsync(process.execPath, [INJECTOR, "--check-payload", "--theme-dir", linked]),
    /symlink|regular/i,
  );
});

test("binding payloads are validated and settled by the tested state model", () => {
  assert.match(injector, /bugfire-state\.mjs/);
  assert.match(injector, /validateProgress/);
  assert.match(injector, /settleBuild/);
  assert.match(injector, /resetProgress/);
  assert.match(injector, /JSON\.parse/);
});

test("all user-visible runtime versions use the BUGFIRE prerelease", () => {
  const expected = "1.3.0-bugfire.1";
  assert.equal(JSON.parse(packageSource).version, expected);
  assert.equal(versionSource.trim(), expected);
  assert.match(common, new RegExp(`SKIN_VERSION=["']${expected.replaceAll(".", "\\.")}["']`));
  assert.match(injector, new RegExp(`SKIN_VERSION = ["']${expected.replaceAll(".", "\\.")}["']`));
  assert.equal(clientDeliveryReadme.split("\n", 1)[0], `Codex BUGFIRE 补丁兽 ${expected}`);
  assert.match(buildClientRelease, /VERSION="\$\(\/usr\/bin\/tr -d '\[:space:\]' < "\$ROOT\/VERSION"\)"/);
  assert.match(buildClientRelease, /"Codex BUGFIRE 补丁兽 \$VERSION"/);
});
