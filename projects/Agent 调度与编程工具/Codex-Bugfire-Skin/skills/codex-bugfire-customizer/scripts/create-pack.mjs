import fs from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const here = path.dirname(fileURLToPath(import.meta.url));
const findEngine = path.join(here, "find-engine.sh");

async function engineLayout() {
  const { stdout } = await execFileAsync(findEngine, [], { encoding: "utf8" });
  const root = stdout.trim();
  const candidates = [path.join(root, "macos", "scripts"), path.join(root, "scripts")];
  for (const scripts of candidates) {
    try {
      const stat = await fs.stat(path.join(scripts, "bugfire-pack.mjs"));
      if (stat.isFile()) return { root, scripts };
    } catch {}
  }
  throw new Error(`Codex BUGFIRE compiler not found under ${root}`);
}

async function runCompiler(args) {
  const { scripts } = await engineLayout();
  const compiler = path.join(scripts, "bugfire-pack.mjs");
  const { stdout } = await execFileAsync(process.execPath, [compiler, ...args], {
    encoding: "utf8", maxBuffer: 1024 * 1024,
  });
  process.stdout.write(stdout);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function safeJson(value) {
  return JSON.stringify(value)
    .replace(/</g, "\\u003c")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}

async function preview(packDirectory, outputFile) {
  const pack = path.resolve(packDirectory);
  const output = path.resolve(outputFile);
  const { scripts } = await engineLayout();
  await execFileAsync(process.execPath, [
    path.join(scripts, "injector.mjs"),
    "--check-payload", "--theme-dir", pack,
  ], { encoding: "utf8", maxBuffer: 32 * 1024 * 1024 });
  const theme = JSON.parse(await fs.readFile(path.join(pack, "theme.json"), "utf8"));
  const asset = async (filename) => {
    if (path.basename(filename) !== filename) throw new Error("Preview asset must stay inside the compiled pack");
    const assetPath = path.join(pack, filename);
    const stat = await fs.lstat(assetPath);
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 16 * 1024 * 1024) {
      throw new Error("Preview asset is not a safe local image");
    }
    const file = await fs.readFile(assetPath);
    const extension = path.extname(filename).toLowerCase();
    const mime = extension === ".jpg" || extension === ".jpeg" ? "image/jpeg"
      : extension === ".webp" ? "image/webp" : "image/png";
    return `data:${mime};base64,${file.toString("base64")}`;
  };
  const background = await asset(theme.image);
  const states = ["idle", "building", "bug", "fire", "success", "levelUp"];
  const stateLabels = {
    idle: "待机", building: "构建", bug: "发现 Bug", fire: "修复", success: "成功", levelUp: "升级",
  };
  const stateArt = {};
  for (const state of states) stateArt[state] = await asset(theme.pet.art[state]);
  const quests = theme.pet.quests.map((quest) => `<li>○ ${escapeHtml(quest.title)} · 0/${quest.target}</li>`).join("");
  const stateButtons = states.map((state) => (
    `<button type="button" data-state="${state}">${stateLabels[state]}</button>`
  )).join("");
  const sayings = safeJson(theme.pet.sayings);
  const html = `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${escapeHtml(theme.name)} · Bugfire Pack Preview</title><style>
  :root{color-scheme:dark;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:${theme.colors.background};color:${theme.colors.text}}*{box-sizing:border-box}body{min-height:100vh;margin:0;display:grid;place-items:center;background:linear-gradient(90deg,rgba(0,0,0,.82),rgba(0,0,0,.2)),url('${background}') center/cover fixed}button{font:inherit}main{width:min(980px,92vw);display:grid;grid-template-columns:1fr 340px;gap:30px;align-items:end}.intro{padding:36px;border-left:5px solid ${theme.colors.accent};background:rgba(4,7,4,.68);backdrop-filter:blur(14px)}h1{margin:0;color:${theme.colors.accent};font-size:clamp(32px,7vw,74px)}p{color:${theme.colors.muted}}.cabin{padding:16px;border:1px solid ${theme.colors.accent};border-radius:18px;background:rgba(5,8,5,.96);box-shadow:0 30px 80px #000}.pet{width:100%;height:150px;border:0;display:grid;place-items:center;cursor:pointer;color:${theme.colors.text};background:radial-gradient(circle at 50% 80%,${theme.colors.secondary}33,transparent 48%)}.pet img{width:140px;height:130px;object-fit:contain;image-rendering:pixelated;filter:drop-shadow(0 12px 18px #0008)}.saying{min-height:38px;margin:8px 0;padding:8px 10px;border-left:2px solid ${theme.colors.accent};color:${theme.colors.accentAlt};background:${theme.colors.panelAlt}}.states{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin:10px 0}.states button{padding:7px 4px;border:1px solid ${theme.colors.accent}55;color:${theme.colors.muted};background:${theme.colors.panelAlt};cursor:pointer}.states button[aria-pressed="true"]{border-color:${theme.colors.accent};color:${theme.colors.background};background:${theme.colors.accent}}.bar{height:8px;background:#020302}.bar i{display:block;width:58%;height:100%;background:${theme.colors.accent}}ul{padding:10px;list-style:none;color:${theme.colors.muted};font-size:11px}.button{width:100%;padding:11px;border:0;text-align:center;background:${theme.colors.secondary};color:#120701;font-weight:900;cursor:pointer}@media(max-width:720px){main{grid-template-columns:1fr}.intro{display:none}}
  </style><main><section class="intro"><small>${escapeHtml(theme.brandSubtitle)}</small><h1>${escapeHtml(theme.name)}</h1><p>${escapeHtml(theme.tagline)}</p><strong>${escapeHtml(theme.quote)}</strong></section><section class="cabin"><header><small>${escapeHtml(theme.pet.seasonLabel)}</small><h2>${escapeHtml(theme.pet.name)}</h2></header><button class="pet" type="button" aria-label="点击 ${escapeHtml(theme.pet.name)} 听一句话" data-sayings="${escapeHtml(sayings)}"><img id="pet-art" src="${stateArt.idle}" alt="${escapeHtml(theme.pet.name)} · 待机"></button><p class="saying" id="pet-saying" aria-live="polite">点击伙伴听一句话，或切换状态检查素材。</p><div class="states" aria-label="宠物状态预览">${stateButtons}</div><p>Lv2 · ${escapeHtml(theme.pet.levels[1].stage)} · ${escapeHtml(theme.pet.levels[1].skill)}</p><div class="bar"><i></i></div><ul>${quests}</ul><button class="button" id="build-demo" type="button">BUILD · 六态演示</button></section></main><script>
  const stateArt = ${safeJson(stateArt)};
  const stateLabels = ${safeJson(stateLabels)};
  const states = ${safeJson(states)};
  const sayings = ${sayings};
  const pet = document.getElementById("pet-art");
  const saying = document.getElementById("pet-saying");
  const buttons = [...document.querySelectorAll("[data-state]")];
  let stateIndex = 0;
  function showState(state) {
    stateIndex = states.indexOf(state);
    pet.src = stateArt[state];
    pet.alt = "${escapeHtml(theme.pet.name)} · " + stateLabels[state];
    buttons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.state === state)));
  }
  buttons.forEach((button) => button.addEventListener("click", () => showState(button.dataset.state)));
  document.querySelector(".pet").addEventListener("click", () => {
    saying.textContent = sayings[Math.floor(Math.random() * sayings.length)];
  });
  document.getElementById("build-demo").addEventListener("click", () => showState(states[(stateIndex + 1) % states.length]));
  showState("idle");
  </script></html>`;
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, html, { mode: 0o600 });
  process.stdout.write(`${JSON.stringify({ pass: true, output }, null, 2)}\n`);
}

const [command, ...args] = process.argv.slice(2);
try {
  if (["init", "validate", "build"].includes(command)) await runCompiler([command, ...args]);
  else if (command === "preview" && args.length === 2) await preview(args[0], args[1]);
  else throw new Error("Usage: create-pack.mjs init|validate|build ... | preview <compiled-pack> <preview.html>");
} catch (error) {
  process.stderr.write(`[codex-bugfire-customizer] ${error.message}\n`);
  process.exitCode = 1;
}
