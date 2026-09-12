import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execFileAsync = promisify(execFile);
const ENGINE = path.resolve(fileURLToPath(new URL("../", import.meta.url)));
const BUILD_RELEASE = path.join(ENGINE, "scripts", "build-release.sh");

async function walk(directory) {
  const files = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await walk(absolute));
    else if (entry.isFile()) files.push(absolute);
  }
  return files;
}

async function extract(archive, directory) {
  await fs.mkdir(directory, { recursive: true });
  await execFileAsync("/usr/bin/ditto", ["-x", "-k", archive, directory]);
}

async function assertLocalMarkdownLinks(root) {
  const missing = [];
  for (const file of (await walk(root)).filter((candidate) => candidate.endsWith(".md"))) {
    const markdown = await fs.readFile(file, "utf8");
    const links = markdown.matchAll(/\[[^\]]*\]\(([^)]+)\)/g);
    for (const match of links) {
      let target = match[1].trim().replace(/^<|>$/g, "");
      if (!target || target.startsWith("#") || /^[a-z][a-z0-9+.-]*:/i.test(target)) continue;
      target = target.split("#", 1)[0].split("?", 1)[0];
      const absolute = path.resolve(path.dirname(file), decodeURIComponent(target));
      if (!await fs.access(absolute).then(() => true, () => false)) {
        missing.push(`${path.relative(root, file)} -> ${match[1]}`);
      }
    }
  }
  assert.deepEqual(missing, []);
}

async function assertEnginePackage(root) {
  for (const required of [
    "LICENSE",
    "NOTICE.md",
    "PROVENANCE.md",
    "SOURCES.md",
    "THIRD_PARTY_NOTICES.md",
    "ASSET_RIGHTS.csv",
    "SECURITY.md",
    "scripts/bugfire-director.mjs",
    "skills/codex-bugfire-customizer/SKILL.md",
    "contest/bugfire/run-demo.sh",
  ]) {
    await fs.access(path.join(root, required));
  }
  await assertLocalMarkdownLinks(root);

  const packageDocs = (await Promise.all([
    "README.md",
    "SOURCES.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/USAGE.zh-CN.md",
    "docs/SECURITY-ARCHITECTURE.zh-CN.md",
    "docs/CUSTOMIZATION.zh-CN.md",
    "contest/bugfire/README.md",
  ].map((file) => fs.readFile(path.join(root, file), "utf8")))).join("\n");
  assert.doesNotMatch(packageDocs, /\.\.\/(?:docs|skills|contest|windows)\//);
  assert.doesNotMatch(packageDocs, /(?:node\s+)?macos\/scripts\//);
  assert.doesNotMatch(packageDocs, /^cd macos$/m);

  const rights = await fs.readFile(path.join(root, "ASSET_RIGHTS.csv"), "utf8");
  assert.match(rights, /^repository_path,main_package_path,asset_type,/);
  for (const line of rights.trim().split("\n").slice(1)) {
    const [, packagePath] = line.split(",", 3);
    await fs.access(path.join(root, packagePath));
  }
  for (const image of (await fs.readdir(path.join(root, "docs", "images")))
    .filter((file) => /^bugfire-.*\.png$/.test(file))) {
    const relative = `docs/images/${image}`;
    const bytes = await fs.readFile(path.join(root, relative));
    const digest = crypto.createHash("sha256").update(bytes).digest("hex");
    assert.match(rights, new RegExp(`^${relative.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")},${relative.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")},[^\\n]+,${digest},`, "m"));
  }
}

test("release builders work from repository and flattened layouts with resolvable evidence", async (t) => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-release-layout-"));
  t.after(() => fs.rm(workspace, { recursive: true, force: true }));

  const repositoryArchive = path.join(workspace, "repository-layout.zip");
  await execFileAsync("/bin/bash", [BUILD_RELEASE, "--skip-tests", repositoryArchive]);
  const repositoryExtract = path.join(workspace, "repository-extract");
  await extract(repositoryArchive, repositoryExtract);
  const flattenedEngine = path.join(repositoryExtract, "codex-dream-skin-studio");
  await assertEnginePackage(flattenedEngine);

  const flattenedSkill = path.join(workspace, "flattened.skill.zip");
  await execFileAsync("/bin/bash", [
    path.join(flattenedEngine, "scripts", "build-skill-release.sh"), flattenedSkill,
  ], { env: { ...process.env, SKILL_VALIDATOR: "/nonexistent/quick_validate.py" } });
  await execFileAsync("/usr/bin/unzip", ["-t", flattenedSkill]);
  const flattenedSkillExtract = path.join(workspace, "flattened-skill-extract");
  await extract(flattenedSkill, flattenedSkillExtract);
  const flattenedSkillRoot = path.join(flattenedSkillExtract, "codex-bugfire-customizer");
  await assertLocalMarkdownLinks(flattenedSkillRoot);
  const flattenedSkillEvidence = (await Promise.all([
    "PROVENANCE.md", "SOURCES.md", "THIRD_PARTY_NOTICES.md", "ASSET_RIGHTS.csv",
  ].map((file) => fs.readFile(path.join(flattenedSkillRoot, file), "utf8")))).join("\n");
  assert.doesNotMatch(
    flattenedSkillEvidence,
    /\]\((?:macos|scripts|tests|references|contest|docs)\//,
  );
  assert.doesNotMatch(flattenedSkillEvidence, /documented in (?:macos\/)?references\//);
  assert.match(
    flattenedSkillEvidence,
    /https:\/\/github\.com\/siuserxiaowei\/Codex-Bugfire-Skin\/blob\/v1\.3\.0-bugfire\.1\/macos\//,
  );

  const nestedArchive = path.join(workspace, "flattened-layout.zip");
  await execFileAsync("/bin/bash", [
    path.join(flattenedEngine, "scripts", "build-release.sh"), "--skip-tests", nestedArchive,
  ]);
  const nestedExtract = path.join(workspace, "flattened-extract");
  await extract(nestedArchive, nestedExtract);
  await assertEnginePackage(path.join(nestedExtract, "codex-dream-skin-studio"));

  const clientArchive = path.join(workspace, "Codex 主题编辑器.zip");
  await execFileAsync("/bin/bash", [
    path.join(flattenedEngine, "scripts", "build-client-release.sh"), "--skip-tests", clientArchive,
  ]);
  const clientExtract = path.join(workspace, "client-extract");
  await extract(clientArchive, clientExtract);
  const clientRoot = path.join(clientExtract, "Codex 主题编辑器");
  assert.equal(
    (await fs.readFile(path.join(clientRoot, "使用说明.txt"), "utf8")).split("\n", 1)[0],
    "Codex BUGFIRE 补丁兽 1.3.0-bugfire.1",
  );
  await fs.access(path.join(clientRoot, "安装 Codex 主题编辑器.command"));
  await assertEnginePackage(path.join(clientRoot, ".codex-dream-skin-studio"));
});
