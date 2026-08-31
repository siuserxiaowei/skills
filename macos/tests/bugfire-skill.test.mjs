import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execFileAsync = promisify(execFile);
const ENGINE = path.resolve(fileURLToPath(new URL("../", import.meta.url)));
const PROJECT_ROOT = path.basename(ENGINE) === "macos" ? path.dirname(ENGINE) : ENGINE;
const SKILL = path.join(PROJECT_ROOT, "skills", "codex-bugfire-customizer");
const CREATE = path.join(SKILL, "scripts", "create-pack.mjs");
const FIND_ENGINE = path.join(SKILL, "scripts", "find-engine.sh");
const INSTALLER = await fs.readFile(path.join(ENGINE, "scripts", "install-dream-skin-macos.sh"), "utf8");
const VALIDATOR = process.env.SKILL_VALIDATOR || path.join(
  os.homedir(),
  ".codex",
  "skills",
  ".system",
  "skill-creator",
  "scripts",
  "quick_validate.py",
);

test("skill metadata and UI prompt validate", async () => {
  const validatorExists = await fs.access(VALIDATOR).then(() => true, () => false);
  if (validatorExists) {
    const { stdout } = await execFileAsync("/usr/bin/python3", [VALIDATOR, SKILL]);
    assert.match(stdout, /valid/i);
  } else {
    const markdown = await fs.readFile(path.join(SKILL, "SKILL.md"), "utf8");
    assert.match(markdown, /^---\nname: codex-bugfire-customizer\ndescription: .+\n---/);
  }
  const yaml = await fs.readFile(path.join(SKILL, "agents", "openai.yaml"), "utf8");
  assert.match(yaml, /\$codex-bugfire-customizer/);
  assert.doesNotMatch(await fs.readFile(path.join(SKILL, "SKILL.md"), "utf8"), /\[TODO/);
  assert.match(INSTALLER, /skills\/codex-bugfire-customizer/,
    "repository installs must bundle the customizer alongside the engine");
});

test("skill wrapper finds this repository and completes a fresh pack journey", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-skill-test-"));
  const source = path.join(workspace, "source");
  const output = path.join(workspace, "output");
  const preview = path.join(workspace, "preview.html");
  await execFileAsync(process.execPath, [CREATE, "init", source]);
  const art = path.join(ENGINE, "assets", "portal-hero.png");
  await fs.copyFile(art, path.join(source, "assets", "background.png"));
  await fs.copyFile(art, path.join(source, "assets", "pet-idle.png"));
  await execFileAsync(process.execPath, [CREATE, "validate", source]);
  await execFileAsync(process.execPath, [CREATE, "build", source, output]);
  await execFileAsync(process.execPath, [CREATE, "preview", output, preview]);
  const html = await fs.readFile(preview, "utf8");
  assert.match(html, /我的 Codex 伙伴/);
  assert.match(html, /data:image\/png;base64/);
  for (const state of ["idle", "building", "bug", "fire", "success", "levelUp"]) {
    assert.match(html, new RegExp(`data-state="${state}"`));
  }
  assert.match(html, /data-sayings="/);
  assert.match(html, /addEventListener\("click"/);
  assert.match(html, /pet\.src = stateArt\[state\]/);
  assert.match(html, /saying\.textContent/);
});

test("skill wrapper resolves the flattened installed-engine layout", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-skill-installed-"));
  const engine = path.join(workspace, "engine");
  const source = path.join(workspace, "source");
  await fs.mkdir(path.join(engine, "scripts"), { recursive: true });
  await fs.copyFile(
    path.join(ENGINE, "scripts", "bugfire-pack.mjs"),
    path.join(engine, "scripts", "bugfire-pack.mjs"),
  );
  const env = { ...process.env, CODEX_BUGFIRE_ROOT: engine };
  const located = await execFileAsync("/bin/bash", [FIND_ENGINE], { env, encoding: "utf8" });
  assert.equal(located.stdout.trim(), engine);
  await execFileAsync(process.execPath, [CREATE, "init", source], { env, encoding: "utf8" });
  await fs.access(path.join(source, "bugfire-pack.json"));
});
