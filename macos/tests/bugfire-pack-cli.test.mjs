import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execFileAsync = promisify(execFile);
const ROOT = path.resolve(fileURLToPath(new URL("../", import.meta.url)));
const CLI = path.join(ROOT, "scripts", "bugfire-pack.mjs");

test("CLI initializes, validates, builds, and emits a machine-readable report", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-cli-"));
  const source = path.join(workspace, "source");
  const output = path.join(workspace, "output");

  await execFileAsync(process.execPath, [CLI, "init", source]);
  await fs.copyFile(path.join(ROOT, "assets", "portal-hero.png"), path.join(source, "assets", "background.png"));
  await fs.copyFile(path.join(ROOT, "assets", "portal-hero.png"), path.join(source, "assets", "pet-idle.png"));
  const validation = JSON.parse((await execFileAsync(process.execPath, [CLI, "validate", source])).stdout);
  assert.equal(validation.pass, true);

  const built = JSON.parse((await execFileAsync(process.execPath, [CLI, "build", source, output])).stdout);
  assert.equal(built.pass, true);
  await fs.access(path.join(output, "theme.json"));
  await fs.access(path.join(output, "pack-report.json"));
});

test("CLI reports missing uploads without creating fake user art", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-cli-missing-"));
  await execFileAsync(process.execPath, [CLI, "init", workspace]);
  await assert.rejects(
    execFileAsync(process.execPath, [CLI, "validate", workspace]),
    /background\.png|pet-idle\.png/i,
  );
});
