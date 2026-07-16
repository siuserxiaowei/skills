import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const ROOT = new URL("../", import.meta.url);
const [themeSource, renderer, css, injector] = await Promise.all([
  readFile(new URL("assets/theme.json", ROOT), "utf8"),
  readFile(new URL("assets/renderer-inject.js", ROOT), "utf8"),
  readFile(new URL("assets/dream-skin.css", ROOT), "utf8"),
  readFile(new URL("scripts/injector.mjs", ROOT), "utf8"),
]);
const theme = JSON.parse(themeSource);
const STATES = ["idle", "building", "bug", "fire", "success", "level-up"];

const section = (source, start, end) => {
  const startIndex = source.indexOf(start);
  assert.notEqual(startIndex, -1, `missing section start: ${start}`);
  const endIndex = source.indexOf(end, startIndex + start.length);
  assert.notEqual(endIndex, -1, `missing section end: ${end}`);
  return source.slice(startIndex, endIndex);
};

const cssRule = (source, selector) => {
  const start = source.indexOf(selector);
  assert.notEqual(start, -1, `missing CSS selector: ${selector}`);
  const open = source.indexOf("{", start + selector.length);
  assert.notEqual(open, -1, `missing opening brace for: ${selector}`);
  let depth = 0;
  for (let index = open; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") depth -= 1;
    if (depth === 0) return source.slice(open + 1, index);
  }
  assert.fail(`missing closing brace for: ${selector}`);
};

const atRule = (source, header) => {
  const start = source.indexOf(header);
  assert.notEqual(start, -1, `missing CSS at-rule: ${header}`);
  const open = source.indexOf("{", start + header.length);
  assert.notEqual(open, -1, `missing opening brace for: ${header}`);
  let depth = 0;
  for (let index = open; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") depth -= 1;
    if (depth === 0) return source.slice(open + 1, index);
  }
  assert.fail(`missing closing brace for: ${header}`);
};

test("theme.json exposes the schema-v1 BUGFIRE pet contract", () => {
  assert.equal(theme.schemaVersion, 1);
  assert.equal(typeof theme.pet, "object");
  assert.match(theme.pet.id, /\S/);
  assert.match(theme.pet.name, /\S/);
  assert.match(theme.pet.season, /\S/);
  assert.equal(theme.pet.demoReward, 35);
  assert.deepEqual(
    theme.pet.levels.map(({ level, minXp, stage, skill }) => ({ level, minXp, stage, skill })),
    [
      { level: 1, minXp: 0, stage: "会描述", skill: "灵感火星" },
      { level: 2, minXp: 100, stage: "会搭建", skill: "结构嗅探" },
      { level: 3, minXp: 240, stage: "会除虫", skill: "BUGFIRE" },
      { level: 4, minXp: 450, stage: "会验收", skill: "测试结界" },
      { level: 5, minXp: 750, stage: "会交付", skill: "发布跃迁" },
    ],
  );
});

test("renderer supports custom six-state pet art, interaction sayings, and derived quests", () => {
  assert.match(renderer, /__BUGFIRE_ASSETS_JSON__/);
  assert.match(renderer, /PET_ASSETS/);
  assert.match(renderer, /data-bugfire-custom-art/);
  assert.match(renderer, /data-bugfire-action=["']pet["']/);
  assert.match(renderer, /data-bugfire-quests/);
  assert.match(renderer, /repairedBuilds/);
  assert.match(renderer, /successfulBuilds/);
  assert.match(renderer, /data-bugfire-quest-complete/);
});

test("custom art aliases resolve once and propagate to the pet, growth card, and certificate", () => {
  const resolver = section(renderer, "const resolvePetAsset", "const setPetState");
  assert.match(resolver, /asset\.ref/);
  assert.match(resolver, /visited/);
  assert.match(resolver, /data:image\\?\//);
  assert.match(resolver, /const applyPetAsset/);

  const state = section(renderer, "const setPetState", "const setPetLog");
  assert.match(state, /applyPetAsset\(root, resolved\)/);
  const certificate = section(renderer, "const showCertificate", "const showGrowthCard");
  assert.match(certificate, /applyPetAsset\(modal, ["']success["']\)/);
  const growth = section(renderer, "const showGrowthCard", "const fallbackSettle");
  assert.match(growth, /applyPetAsset\(modal, ["']level-up["']\)/);
});

test("renderer mounts one marked pet root and cleanup removes every BUGFIRE marker", () => {
  assert.match(renderer, /const\s+PET_ID\s*=\s*["']codex-bugfire-pet["']/);
  assert.match(renderer, /const\s+GROWTH_CARD_ID\s*=\s*["']codex-bugfire-growth-card["']/);
  assert.match(renderer, /const\s+CERTIFICATE_ID\s*=\s*["']codex-bugfire-certificate["']/);
  assert.match(renderer, /getElementById\(PET_ID\)/);
  assert.match(renderer, /\.id\s*=\s*PET_ID/);
  assert.match(renderer, /data-bugfire-mounted/);

  const cleanup = section(renderer, "const cleanup =", "const scheduler =");
  for (const id of ["PET_ID", "GROWTH_CARD_ID", "CERTIFICATE_ID"]) {
    assert.match(cleanup, new RegExp(`getElementById\\(${id}\\)\\?\\.remove\\(\\)`));
  }
  assert.match(cleanup, /removeAttribute\(["']data-bugfire-mounted["']\)/);
});

test("pet interaction is opt-in while its root and decoration never intercept Codex", () => {
  assert.match(renderer, /data-bugfire-interactive/);
  assert.match(renderer, /data-bugfire-decoration/);
  assert.match(cssRule(css, "#codex-bugfire-pet"), /pointer-events\s*:\s*none/);
  assert.match(
    cssRule(css, "#codex-bugfire-pet [data-bugfire-interactive]"),
    /pointer-events\s*:\s*auto/,
  );
  assert.match(
    cssRule(css, "#codex-bugfire-pet [data-bugfire-decoration]"),
    /pointer-events\s*:\s*none/,
  );
});

test("renderer and CSS expose the six canonical pet states", () => {
  assert.match(renderer, /BUGFIRE_STATES/);
  assert.match(renderer, /setPetState/);
  assert.match(renderer, /data-bugfire-state/);
  for (const state of STATES) {
    assert.match(renderer, new RegExp(`["']${state}["']`), `renderer lacks ${state} state`);
    assert.match(css, new RegExp(`data-bugfire-state=["']${state}["']`), `CSS lacks ${state} state`);
  }
});

test("growth card and certificate use 4:5 surfaces and certificate exports PNG", () => {
  assert.match(renderer, /codex-bugfire-growth-card/);
  assert.match(renderer, /codex-bugfire-certificate/);
  assert.match(renderer, /个人成长纪念卡，由本地活动生成；非官方认证，不代表专业资格。/);
  assert.match(renderer, /(?:toBlob|toDataURL)\s*\(/);
  assert.match(renderer, /image\/png/);
  assert.match(renderer, /\.png["'`]/);
  assert.match(renderer, /\.download\s*=/);
  assert.match(css, /(?:codex-bugfire-growth-card|codex-bugfire-certificate)[\s\S]{0,600}aspect-ratio\s*:\s*4\s*\/\s*5/);
});

test("certificate export asynchronously draws custom success art with a default-pet fallback", () => {
  const draw = section(renderer, "const drawDefaultCertificatePet", "const showCertificate");
  assert.match(draw, /const drawCertificatePet\s*=\s*async/);
  assert.match(draw, /resolvePetAsset\(["']success["']\)/);
  assert.match(draw, /new Image\(\)/);
  assert.match(draw, /drawImage\s*\(/);
  assert.match(draw, /drawDefaultCertificatePet\(context\)/);
  assert.match(draw, /const renderCertificateDataUrl\s*=\s*async/);
  assert.match(draw, /await drawCertificatePet\(context\)/);
  assert.match(draw, /const exportCertificate\s*=\s*async/);
  assert.match(draw, /await renderCertificateDataUrl\(card\)/);
});

test("Escape and task routes collapse the pet and cleanup unregisters its keyboard listener", () => {
  assert.match(renderer, /addEventListener\(["']keydown["']/);
  assert.match(renderer, /(?:event|evt|e)\.key\s*===\s*["']Escape["']/);
  assert.match(renderer, /data-bugfire-open/);
  assert.match(renderer, /data-bugfire-route/);
  assert.match(renderer, /["']home["']/);
  assert.match(renderer, /["']task["']/);
  const cleanup = section(renderer, "const cleanup =", "const scheduler =");
  assert.match(cleanup, /removeEventListener\(["']keydown["']/);
});

test("task routes move the 72px nest clear of the native composer", () => {
  const route = section(renderer, "const updatePetRoute", "const destroyPet");
  assert.match(route, /composer-surface-chrome/);
  assert.match(route, /getBoundingClientRect\s*\(/);
  assert.match(route, /--bugfire-task-bottom/);
  assert.match(css, /data-bugfire-route=["']task["'][^\{]*\{[^}]*bottom\s*:\s*var\(--bugfire-task-bottom/s);
});

test("route detection ignores retained but hidden home DOM", () => {
  const ensure = section(renderer, "const ensure =", "const cleanup =");
  assert.match(ensure, /getClientRects\s*\(\)/);
  assert.match(ensure, /aria-hidden/);
});

test("route detection supports current Codex home pages without role=main", () => {
  const ensure = section(renderer, "const ensure =", "const cleanup =");
  assert.match(ensure, /data-feature=["']game-source["']/);
  assert.match(ensure, /group\/home-suggestions/);
  assert.match(ensure, /closest\([^)]*home-main-content/);
  assert.match(ensure, /isHomeRoute/);
  assert.doesNotMatch(ensure, /closest\([^)]*main\.main-surface/);
  assert.match(ensure, /querySelectorAll\(["']\.dream-skin-home["']\)/);
});

test("BUGFIRE forces readable foregrounds on its dark home and composer surfaces", () => {
  const bugfire = css.slice(css.indexOf("BUGFIRE / 补丁兽"));
  assert.match(bugfire, /game-source[^\{]*\{[^}]*color\s*:\s*#f4efd8[^}]*text-shadow/s);
  assert.match(bugfire, /game-source[^\{]*::after[^\{]*\{[^}]*color\s*:\s*#d7dfcf/s);
  assert.match(bugfire, /home-suggestions[^\{]*button[^\{]*span:last-child[^\{]*\{[^}]*color\s*:\s*#e9ead7/s);
  assert.doesNotMatch(bugfire, /home-suggestions[^,\{]*button\s+\*/s);
  assert.match(bugfire, /project-selector[^\{]*\*[^\{]*\{[^}]*color\s*:\s*#f4efd8/s);
  assert.match(bugfire, /dream-skin-home[^\{]*\[role=["']group["']\][^\{]*\{[^}]*color\s*:\s*#c7d2c0/s);
  assert.match(bugfire, /composer-surface-chrome[^\{]*:where\([^)]*\)[^\{]*\{[^}]*color\s*:\s*#e9ead7/s);
  assert.match(bugfire, /(?:ProseMirror|contenteditable)[^\{]*\{[^}]*color\s*:\s*#fffdf1[^}]*font-weight\s*:\s*5\d\d/s);
  assert.match(bugfire, /is-editor-empty[^\{]*::before[^\{]*\{[^}]*color\s*:\s*#b9c4b2/s);
  assert.match(bugfire, /\[data-placeholder\]::after[^\{]*\{[^}]*color\s*:\s*#b9c4b2[^}]*opacity\s*:\s*1/s);
});

test("BUGFIRE keeps task transcript text readable without recoloring side panels", () => {
  const bugfire = css.slice(css.indexOf("BUGFIRE / 补丁兽"));
  assert.match(bugfire, /thread-scroll-container[^\{]*markdownContent_[^\{]*\{[^}]*color\s*:\s*#e9ead7/s);
  assert.match(bugfire, /thread-scroll-container[^\{]*markdownText_[^\{]*\{[^}]*color\s*:\s*inherit/s);
  assert.match(bugfire, /thread-scroll-container[^\{]*text-token-conversation-body[^\{]*\{[^}]*color\s*:\s*#e9ead7/s);
  assert.match(bugfire, /thread-scroll-container[^\{]*text-token-conversation-body[^\{]*\*\s*:\s*not\(button\)[^\{]*\{[^}]*color\s*:\s*#b9c4b2/s);
  assert.match(bugfire, /thread-scroll-container[^\{]*text-token-text-tertiary[^\{]*\{[^}]*color\s*:\s*#aeb9a8/s);
});

test("reduced-motion disables BUGFIRE animation and transition effects", () => {
  const reducedMotion = atRule(css, "@media (prefers-reduced-motion: reduce)");
  assert.match(reducedMotion, /(?:codex-bugfire-pet|bugfire)/);
  assert.match(reducedMotion, /animation\s*:\s*none\s*!important/);
  assert.match(reducedMotion, /transition(?:-duration)?\s*:\s*(?:none|0s)\s*!important/);
});

test("live verification requires the pet plus the native sidebar and composer", () => {
  const verify = section(injector, "async function verifySession", "async function waitForVerifiedSession");
  assert.match(verify, /getElementById\(["']codex-bugfire-pet["']\)/);
  assert.match(verify, /petPresent\s*:\s*Boolean\(/);
  assert.match(verify, /petInteractive/);
  assert.match(verify, /petPointerEvents/);

  const basePass = section(verify, "const basePass", "const homePass");
  assert.match(basePass, /result\.petPresent/);
  assert.match(basePass, /result\.petInteractive/);
  assert.match(basePass, /result\.composer\?\.visible/);
  assert.match(basePass, /result\.sidebar\?\.visible/);

  const remove = section(injector, "async function removeFromSession", "async function verifyRemovedSession");
  const verifyRemoved = section(injector, "async function verifyRemovedSession", "async function verifySession");
  for (const id of ["codex-bugfire-pet", "codex-bugfire-growth-card", "codex-bugfire-certificate"]) {
    assert.match(remove, new RegExp(id));
    assert.match(verifyRemoved, new RegExp(id));
  }
});
