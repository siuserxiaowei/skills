import fs from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  LEVELS,
  createSeedProgress,
  loadProgress,
  resetProgress,
  saveProgress,
  settleBuild,
  validateProgress,
  withProgressLock,
} from "./bugfire-state.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const SKIN_VERSION = "1.2.0-bugfire.1";
const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);
const MAX_THEME_BYTES = 128 * 1024;
const MAX_ART_BYTES = 16 * 1024 * 1024;
const MAX_PET_ART_BYTES = 4 * 1024 * 1024;
const BUGFIRE_BINDING = "__bugfireSync";
const BUGFIRE_STATE_PATH = process.env.BUGFIRE_PROGRESS_PATH || path.join(
  os.homedir(),
  "Library",
  "Application Support",
  "CodexDreamSkinStudio",
  "bugfire-progress.json",
);
const DEFAULT_PET = Object.freeze({
  id: "bugfire-patch-dragon",
  name: "补丁兽",
  season: "season-1",
  seasonLabel: "BUGFIRE · Season 01",
  demoReward: 35,
  levels: LEVELS,
  art: Object.freeze({}),
  sayings: Object.freeze([
    "今天也一起把 Bug 烧掉。",
    "先描述清楚，再动手构建。",
    "修复不是倒退，是进化素材。",
  ]),
  quests: Object.freeze([
    Object.freeze({ id: "first-fix", title: "完成第一次修复重建", metric: "repairedBuilds", target: 1 }),
    Object.freeze({ id: "build-streak", title: "累计完成 3 次 Build", metric: "successfulBuilds", target: 3 }),
    Object.freeze({ id: "level-three", title: "成长到 Lv3", metric: "level", target: 3 }),
  ]),
  certificateTitle: "BUGFIRE 赛季证书",
});

const PET_ART_STATES = Object.freeze(["idle", "building", "bug", "fire", "success", "levelUp"]);
const QUEST_METRICS = new Set(["repairedBuilds", "successfulBuilds", "failedBuilds", "xp", "level"]);

function parseArgs(argv) {
  const options = {
    port: 9341,
    mode: "watch",
    timeoutMs: 30000,
    screenshot: null,
    reload: false,
    themeDir: null,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--port") options.port = Number(argv[++i]);
    else if (arg === "--once") options.mode = "once";
    else if (arg === "--watch") options.mode = "watch";
    else if (arg === "--verify") options.mode = "verify";
    else if (arg === "--remove") options.mode = "remove";
    else if (arg === "--check-payload") options.mode = "check";
    else if (arg === "--timeout-ms") options.timeoutMs = Number(argv[++i]);
    else if (arg === "--screenshot") options.screenshot = path.resolve(argv[++i]);
    else if (arg === "--theme-dir") options.themeDir = path.resolve(argv[++i]);
    else if (arg === "--reload") options.reload = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if (!Number.isInteger(options.port) || options.port < 1024 || options.port > 65535) {
    throw new Error(`Invalid port: ${options.port}`);
  }
  if (!Number.isFinite(options.timeoutMs) || options.timeoutMs < 250 || options.timeoutMs > 120000) {
    throw new Error(`Invalid timeout: ${options.timeoutMs}`);
  }
  return options;
}

function validatedDebuggerUrl(target, port) {
  const url = new URL(target.webSocketDebuggerUrl);
  if (url.protocol !== "ws:" || !LOOPBACK_HOSTS.has(url.hostname) || Number(url.port) !== port) {
    throw new Error(`Rejected non-loopback CDP WebSocket URL: ${url.href}`);
  }
  return url.href;
}

class CdpSession {
  constructor(target, port) {
    this.target = target;
    this.ws = new WebSocket(validatedDebuggerUrl(target, port));
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
    this.closed = false;
  }

  async open() {
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("CDP WebSocket open timed out")), 5000);
      this.ws.addEventListener("open", () => { clearTimeout(timeout); resolve(); }, { once: true });
      this.ws.addEventListener("error", () => { clearTimeout(timeout); reject(new Error("CDP WebSocket open failed")); }, { once: true });
    });
    this.ws.addEventListener("message", (event) => this.onMessage(event));
    this.ws.addEventListener("close", () => {
      this.closed = true;
      for (const waiter of this.pending.values()) {
        clearTimeout(waiter.timeout);
        waiter.reject(new Error("CDP socket closed"));
      }
      this.pending.clear();
    });
    await this.send("Runtime.enable");
    await this.send("Page.enable");
    return this;
  }

  onMessage(event) {
    const message = JSON.parse(String(event.data));
    if (message.id) {
      const waiter = this.pending.get(message.id);
      if (!waiter) return;
      clearTimeout(waiter.timeout);
      this.pending.delete(message.id);
      if (message.error) waiter.reject(new Error(`${message.error.message} (${message.error.code})`));
      else waiter.resolve(message.result);
      return;
    }
    for (const listener of this.listeners.get(message.method) ?? []) listener(message.params ?? {});
  }

  on(method, listener) {
    const listeners = this.listeners.get(method) ?? [];
    listeners.push(listener);
    this.listeners.set(method, listeners);
  }

  send(method, params = {}) {
    if (this.closed) return Promise.reject(new Error("CDP session is closed"));
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      const timeout = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP command timed out: ${method}`));
      }, 10000);
      this.pending.set(id, { resolve, reject, timeout });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async evaluate(expression) {
    const result = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
      userGesture: false,
    });
    if (result.exceptionDetails) {
      const detail = result.exceptionDetails.exception?.description ?? result.exceptionDetails.text;
      throw new Error(`Renderer evaluation failed: ${detail}`);
    }
    return result.result?.value;
  }

  close() {
    if (!this.closed) this.ws.close();
    this.closed = true;
  }
}

async function listAppTargets(port) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2000);
  try {
    const response = await fetch(`http://127.0.0.1:${port}/json/list`, { signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const targets = await response.json();
    return targets.filter((item) => {
      if (item.type !== "page" || !item.url?.startsWith("app://") || !item.webSocketDebuggerUrl) return false;
      try {
        validatedDebuggerUrl(item, port);
        return true;
      } catch {
        return false;
      }
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function probeSession(session) {
  return session.evaluate(`(() => {
    const markers = {
      shell: Boolean(document.querySelector('main.main-surface')),
      sidebar: Boolean(document.querySelector('aside.app-shell-left-panel')),
      composer: Boolean(document.querySelector('.composer-surface-chrome')),
      main: Boolean(document.querySelector('[role="main"]')),
    };
    return {
      title: document.title,
      href: location.href,
      markers,
      codex: markers.shell && markers.sidebar && (markers.composer || markers.main),
    };
  })()`);
}

async function connectTarget(target, port) {
  return new CdpSession(target, port).open();
}

async function connectCodexTargets(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const targets = await listAppTargets(port);
      const connected = [];
      for (const target of targets) {
        let session;
        try {
          session = await connectTarget(target, port);
          const probe = await probeSession(session);
          if (probe?.codex) connected.push({ target, session, probe });
          else session.close();
        } catch (error) {
          session?.close();
          lastError = error;
        }
      }
      if (connected.length) return connected;
      lastError = new Error("No page matched the expected Codex shell markers");
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 350));
  }
  throw new Error(`No verified Codex renderer on 127.0.0.1:${port}: ${lastError?.message ?? "timed out"}`);
}

function pathStaysInside(rootPath, candidatePath) {
  const relative = path.relative(rootPath, candidatePath);
  return relative !== "" && relative !== ".." && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}

async function validatedThemeAsset(assetsRoot, filename, label, maximumBytes) {
  const candidate = path.resolve(assetsRoot, filename);
  if (!pathStaysInside(assetsRoot, candidate)) {
    throw new Error(`${label} must stay inside its theme directory`);
  }
  const entry = await fs.lstat(candidate);
  if (entry.isSymbolicLink() || !entry.isFile()) {
    throw new Error(`${label} must be a regular, non-symlink file`);
  }
  const canonical = await fs.realpath(candidate);
  if (!pathStaysInside(assetsRoot, canonical)) {
    throw new Error(`${label} resolves outside its theme directory`);
  }
  const handle = await fs.open(canonical, fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW);
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size < 1 || stat.size > maximumBytes) {
      throw new Error(`${label} must be a non-empty file no larger than ${maximumBytes} bytes`);
    }
    const content = await handle.readFile();
    if (content.length !== stat.size) throw new Error(`${label} changed while it was being read`);
    return { content, identity: `${stat.dev}:${stat.ino}`, path: canonical, stat };
  } finally {
    await handle.close();
  }
}

async function loadTheme(themeDir) {
  const defaultAssetsRoot = path.join(root, "assets");
  let assetsRoot = defaultAssetsRoot;
  if (themeDir) {
    try {
      await fs.access(path.join(themeDir, "theme.json"));
      assetsRoot = themeDir;
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
  }

  assetsRoot = await fs.realpath(assetsRoot);
  const configPath = path.join(assetsRoot, "theme.json");
  const configStat = await fs.lstat(configPath);
  if (configStat.isSymbolicLink() || !configStat.isFile() || configStat.size < 2 || configStat.size > MAX_THEME_BYTES) {
    throw new Error(`Theme config must be a regular file between 2 and ${MAX_THEME_BYTES} bytes`);
  }
  const raw = JSON.parse(await fs.readFile(configPath, "utf8"));
  if (raw.schemaVersion !== 1 || typeof raw.image !== "string" || !raw.image) {
    throw new Error(`${configPath} has an unsupported schema or image field`);
  }
  if (path.basename(raw.image) !== raw.image) throw new Error("Theme image must stay inside its theme directory");
  const themePetId = typeof raw.pet?.id === "string" && raw.pet.id.trim()
    ? raw.pet.id.trim() : DEFAULT_PET.id;
  const text = (value, fallback, max) => typeof value === "string" && value.trim()
    ? value.trim().slice(0, max) : fallback;
  const color = (value, fallback) => {
    if (typeof value !== "string") return fallback;
    const normalized = value.trim();
    return /^#[0-9a-f]{6}$/i.test(normalized) || /^rgba?\([0-9., %]+\)$/i.test(normalized)
      ? normalized
      : fallback;
  };
  const rawReward = Number(raw.pet?.demoReward);
  const arrayText = (values, fallback, maximumItems, maximumLength) => {
    if (!Array.isArray(values) || values.length < 1 || values.length > maximumItems) return [...fallback];
    const normalized = values.map((value) => text(value, "", maximumLength)).filter(Boolean);
    return normalized.length === values.length ? normalized : [...fallback];
  };
  const petArt = {};
  if (raw.pet?.art && typeof raw.pet.art === "object" && !Array.isArray(raw.pet.art)) {
    for (const state of PET_ART_STATES) {
      const filename = raw.pet.art[state];
      if (typeof filename !== "string" || !filename) continue;
      if (path.basename(filename) !== filename || !/\.(?:png|jpe?g|webp)$/i.test(filename)) {
        throw new Error(`Invalid pet art path for ${state}`);
      }
      petArt[state] = filename;
    }
  }
  const quests = Array.isArray(raw.pet?.quests) ? raw.pet.quests.map((quest, index) => {
    const metric = typeof quest?.metric === "string" ? quest.metric : "";
    const target = Number(quest?.target);
    if (!QUEST_METRICS.has(metric) || !Number.isSafeInteger(target) || target < 1 || target > 100_000) {
      throw new Error(`Invalid pet quest at index ${index}`);
    }
    return {
      id: text(quest?.id, `quest-${index + 1}`, 64),
      title: text(quest?.title, `Quest ${index + 1}`, 80),
      metric,
      target,
    };
  }).slice(0, 5) : DEFAULT_PET.quests.map((quest) => ({ ...quest }));
  const pet = {
    id: text(raw.pet?.id, DEFAULT_PET.id, 80),
    name: text(raw.pet?.name, DEFAULT_PET.name, 80),
    season: text(raw.pet?.season, DEFAULT_PET.season, 80),
    seasonLabel: text(raw.pet?.seasonLabel, DEFAULT_PET.seasonLabel, 80),
    demoReward: Number.isSafeInteger(rawReward) && rawReward > 0 && rawReward <= 100
      ? rawReward
      : DEFAULT_PET.demoReward,
    // Progress validation is deliberately tied to one auditable level table.
    levels: LEVELS.map((entry) => ({ ...entry })),
    art: petArt,
    sayings: arrayText(raw.pet?.sayings, DEFAULT_PET.sayings, 12, 80),
    quests: quests.length ? quests : DEFAULT_PET.quests.map((quest) => ({ ...quest })),
    certificateTitle: text(raw.pet?.certificateTitle, DEFAULT_PET.certificateTitle, 80),
  };
  const theme = {
    schemaVersion: 1,
    id: text(raw.id, "custom", 80),
    name: text(raw.name, "Codex Dream Skin", 80),
    brandSubtitle: text(raw.brandSubtitle, "CODEX DREAM SKIN", 80),
    tagline: text(raw.tagline, "Make something wonderful.", 160),
    projectPrefix: text(raw.projectPrefix, "选择项目 · ", 80),
    projectLabel: text(raw.projectLabel, "◉  选择项目", 80),
    statusText: text(raw.statusText, "DREAM SKIN ONLINE", 80),
    quote: text(raw.quote, "MAKE SOMETHING WONDERFUL", 80),
    image: raw.image,
    pet,
    colors: {
      background: color(raw.colors?.background, "#071116"),
      panel: color(raw.colors?.panel, "#0b1a20"),
      panelAlt: color(raw.colors?.panelAlt, "#10272c"),
      accent: color(raw.colors?.accent, "#7cff46"),
      accentAlt: color(raw.colors?.accentAlt, "#b8ff3d"),
      secondary: color(raw.colors?.secondary, "#36d7e8"),
      highlight: color(raw.colors?.highlight, "#642a8c"),
      text: color(raw.colors?.text, "#e9fff1"),
      muted: color(raw.colors?.muted, "#9ebdb3"),
      line: color(raw.colors?.line, "rgba(124, 255, 70, .28)"),
    },
  };
  const extension = path.extname(theme.image).toLowerCase();
  if (![".png", ".jpg", ".jpeg", ".webp"].includes(extension)) {
    throw new Error(`Unsupported theme image format: ${extension || "missing"}`);
  }
  const image = await validatedThemeAsset(assetsRoot, theme.image, "Theme image", MAX_ART_BYTES);
  const imagePath = image.path;
  const imageStat = image.stat;
  const petArtFiles = {};
  let totalPetArtBytes = 0;
  const uniquePetArtFiles = new Set();
  const petArtByFilename = new Map();
  for (const [state, filename] of Object.entries(theme.pet.art)) {
    let petArt = petArtByFilename.get(filename);
    if (!petArt) {
      petArt = await validatedThemeAsset(assetsRoot, filename, `Pet art ${state}`, MAX_PET_ART_BYTES);
      petArtByFilename.set(filename, petArt);
    }
    if (!uniquePetArtFiles.has(petArt.identity)) {
      uniquePetArtFiles.add(petArt.identity);
      totalPetArtBytes += petArt.stat.size;
    }
    petArtFiles[state] = petArt;
  }
  if (totalPetArtBytes > MAX_ART_BYTES) throw new Error("Total pet art exceeds the 16 MB limit");
  return { assetsRoot, imageContent: image.content, imagePath, imageStat, petArtFiles, theme, themePetId };
}

async function loadPetAssets(petArtFiles) {
  const petAssets = {};
  const stateByFile = new Map();
  let petArtBytes = 0;
  for (const [state, asset] of Object.entries(petArtFiles)) {
    const existingState = stateByFile.get(asset.identity);
    if (existingState) {
      petAssets[state] = { ref: existingState };
      continue;
    }
    const extension = path.extname(asset.path).toLowerCase();
    const mime = extension === ".jpg" || extension === ".jpeg" ? "image/jpeg"
      : extension === ".webp" ? "image/webp" : "image/png";
    const { content } = asset;
    petAssets[state] = `data:${mime};base64,${content.toString("base64")}`;
    stateByFile.set(asset.identity, state);
    petArtBytes += content.length;
  }
  return {
    petAssets,
    petArtBytes,
    petAssetPayloadBytes: Buffer.byteLength(JSON.stringify(petAssets)),
  };
}

async function loadPayload(themeDir, progressOverride = null) {
  const [css, template, loaded] = await Promise.all([
    fs.readFile(path.join(root, "assets", "dream-skin.css"), "utf8"),
    fs.readFile(path.join(root, "assets", "renderer-inject.js"), "utf8"),
    loadTheme(themeDir),
  ]);
  const { imageContent, imagePath, petArtFiles, theme, themePetId } = loaded;
  const progress = progressOverride
    ? validateProgress(progressOverride)
    : createSeedProgress({ petId: themePetId, seasonId: theme.pet.season });
  const art = imageContent;
  const extension = path.extname(imagePath).toLowerCase();
  const mime = extension === ".jpg" || extension === ".jpeg" ? "image/jpeg"
    : extension === ".webp" ? "image/webp" : "image/png";
  const artDataUrl = `data:${mime};base64,${art.toString("base64")}`;
  const { petAssets, petArtBytes, petAssetPayloadBytes } = await loadPetAssets(petArtFiles);
  const payload = template
    .replace("__DREAM_SKIN_CSS_JSON__", JSON.stringify(css))
    .replace("__DREAM_SKIN_ART_JSON__", JSON.stringify(artDataUrl))
    .replace("__DREAM_SKIN_THEME_JSON__", JSON.stringify(theme))
    .replace("__BUGFIRE_PROGRESS_JSON__", JSON.stringify(progress))
    .replace("__BUGFIRE_ASSETS_JSON__", JSON.stringify(petAssets))
    .replace("__DREAM_SKIN_VERSION_JSON__", JSON.stringify(SKIN_VERSION));
  return { imageBytes: art.length, payload, petArtBytes, petAssetPayloadBytes, petAssets, progress, theme };
}

async function loadLivePayload(themeDir) {
  const seed = await loadPayload(themeDir);
  const options = {
    petId: seed.theme.pet.id,
    seasonId: seed.theme.pet.season,
  };
  const progress = await loadProgress(BUGFIRE_STATE_PATH, options);
  return loadPayload(themeDir, progress);
}

async function applyToSession(session, payload) {
  return session.evaluate(payload);
}

function parseBugfireEvent(payload) {
  if (typeof payload !== "string" || payload.length < 2 || payload.length > 4096) {
    throw new Error("Rejected invalid BUGFIRE binding payload size");
  }
  const event = JSON.parse(payload);
  if (!event || typeof event !== "object" || Array.isArray(event)) {
    throw new Error("Rejected invalid BUGFIRE binding payload");
  }
  if (event.type === "reset") return { type: "reset" };
  if (event.type !== "settle-build") throw new Error("Rejected unknown BUGFIRE event type");
  if (typeof event.eventId !== "string" || !event.eventId.trim() || event.eventId.length > 120) {
    throw new Error("Rejected invalid BUGFIRE event id");
  }
  if (!new Set(["failed", "repair-success"]).has(event.outcome)) {
    throw new Error("Rejected invalid BUGFIRE Build outcome");
  }
  return { type: event.type, eventId: event.eventId, outcome: event.outcome };
}

async function hydrateBugfireSession(session, progress, result) {
  if (session.closed) return;
  await session.evaluate(`(() => {
    const pet = window.__CODEX_DREAM_SKIN_STATE__?.pet;
    return pet?.hydrate?.(${JSON.stringify(progress)}, ${JSON.stringify(result)}) ?? false;
  })()`);
}

async function installBugfireBinding(session, runtime, broadcast) {
  await session.send("Runtime.addBinding", { name: BUGFIRE_BINDING });
  session.on("Runtime.bindingCalled", ({ name, payload }) => {
    if (name !== BUGFIRE_BINDING) return;
    runtime.queue = runtime.queue.then(async () => {
      let event;
      try {
        event = parseBugfireEvent(payload);
        const now = new Date().toISOString();
        let result;
        await withProgressLock(BUGFIRE_STATE_PATH, async (assertLockHeld) => {
          // Always reload while holding the cross-process lock. A stale or
          // duplicate watcher can therefore never overwrite a newer event.
          const persisted = await loadProgress(BUGFIRE_STATE_PATH, {
            petId: runtime.theme.pet.id,
            seasonId: runtime.theme.pet.season,
          });
          if (event.type === "reset") {
            const progress = resetProgress({
              petId: runtime.theme.pet.id,
              seasonId: runtime.theme.pet.season,
              now,
            });
            result = {
              progress,
              awardedXp: 0,
              duplicate: false,
              levelUp: null,
              card: null,
              reset: true,
            };
          } else {
            const settlement = settleBuild(persisted, {
              eventId: event.eventId,
              outcome: event.outcome,
              rewardXp: runtime.theme.pet.demoReward,
              now,
            });
            // Preserve the renderer-originated identity so only the initiating
            // window animates; other verified renderers only refresh progress.
            result = {
              ...settlement,
              eventId: event.eventId,
              outcome: event.outcome,
            };
          }
          const nextProgress = validateProgress(result.progress);
          assertLockHeld();
          await saveProgress(BUGFIRE_STATE_PATH, nextProgress);
          assertLockHeld();
          runtime.progress = nextProgress;
          result = { ...result, progress: nextProgress };
        });
        await broadcast(runtime.progress, result);
      } catch (error) {
        if (event?.eventId) {
          await hydrateBugfireSession(session, runtime.progress, {
            error: true,
            eventId: event.eventId,
            message: "本地进度保存失败，未结算 XP。",
          }).catch(() => {});
        }
        throw error;
      }
    }).catch((error) => {
      console.error(`[bugfire] ${new Date().toISOString()} ${error.message}`);
    });
  });
}

async function removeBugfireBinding(session) {
  if (session.closed) return;
  try {
    await session.send("Runtime.removeBinding", { name: BUGFIRE_BINDING });
  } catch (error) {
    // Removing an already absent binding is idempotent. Other CDP failures are
    // surfaced by the DOM/global cleanup verification below.
    console.error(`[bugfire] remove binding: ${error.message}`);
  }
}

async function removeFromSession(session) {
  return session.evaluate(`(() => {
    window.__CODEX_DREAM_SKIN_DISABLED__ = true;
    try {
      window.__bugfireSync = undefined;
      delete window.__bugfireSync;
    } catch {}
    const state = window.__CODEX_DREAM_SKIN_STATE__;
    if (state?.cleanup) return state.cleanup();
    document.documentElement?.classList.remove('codex-dream-skin');
    document.documentElement?.style.removeProperty('--dream-skin-art');
    document.documentElement?.removeAttribute('data-bugfire-mounted');
    document.getElementById('codex-dream-skin-style')?.remove();
    document.getElementById('codex-dream-skin-chrome')?.remove();
    document.getElementById('codex-bugfire-pet')?.remove();
    document.getElementById('codex-bugfire-growth-card')?.remove();
    document.getElementById('codex-bugfire-certificate')?.remove();
    delete window.__CODEX_DREAM_SKIN_STATE__;
    return true;
  })()`);
}

async function verifyRemovedSession(session) {
  return session.evaluate(`(() =>
    !document.documentElement.classList.contains('codex-dream-skin') &&
    !document.getElementById('codex-dream-skin-style') &&
    !document.getElementById('codex-dream-skin-chrome') &&
    !document.getElementById('codex-bugfire-pet') &&
    !document.getElementById('codex-bugfire-growth-card') &&
    !document.getElementById('codex-bugfire-certificate') &&
    !document.documentElement.hasAttribute('data-bugfire-mounted') &&
    typeof window.__bugfireSync !== 'function' &&
    !window.__CODEX_DREAM_SKIN_STATE__
  )()`);
}

async function verifySession(session) {
  return session.evaluate(`(() => {
    const box = (node) => {
      if (!node) return null;
      const r = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return {
        x: Math.round(r.x), y: Math.round(r.y),
        width: Math.round(r.width), height: Math.round(r.height),
        visible: r.width > 0 && r.height > 0 && style.display !== 'none' && style.visibility !== 'hidden',
      };
    };
    const homeIndicator = document.querySelector('[data-testid="home-icon"]');
    const homeSignal = homeIndicator ?? document.querySelector('[data-feature="game-source"]') ??
      document.querySelector('.group\\\\/home-suggestions');
    const homeRoute = homeSignal?.closest('[role="main"]') ?? null;
    const home = document.querySelector('[role="main"].dream-skin-home');
    const suggestions = home?.querySelector('.group\\\\/home-suggestions') ?? null;
    const cardBoxes = suggestions ? [...suggestions.querySelectorAll('button')].map(box) : [];
    const visibleCards = cardBoxes.filter((item) => item?.visible);
    const hero = box(home?.firstElementChild?.firstElementChild?.firstElementChild);
    const projectButton = box(home?.querySelector('.group\\\\/project-selector > button'));
    const composer = box(document.querySelector('.composer-surface-chrome'));
    const sidebar = box(document.querySelector('aside.app-shell-left-panel'));
    const chrome = document.getElementById('codex-dream-skin-chrome');
    const pet = document.getElementById('codex-bugfire-pet');
    const petInteractive = Boolean(pet?.querySelector('[data-bugfire-interactive]'));
    const petPointerEvents = getComputedStyle(pet || document.body).pointerEvents;
    const result = {
      installed: document.documentElement.classList.contains('codex-dream-skin'),
      version: window.__CODEX_DREAM_SKIN_STATE__?.version ?? null,
      stylePresent: Boolean(document.getElementById('codex-dream-skin-style')),
      chromePresent: Boolean(chrome),
      chromePointerEvents: getComputedStyle(chrome || document.body).pointerEvents,
      petPresent: Boolean(pet),
      petInteractive,
      petPointerEvents,
      homeRoute: Boolean(homeRoute),
      homePresent: Boolean(home),
      hero,
      cards: cardBoxes,
      visibleCardCount: visibleCards.length,
      projectButton,
      composer,
      sidebar,
      viewport: { width: innerWidth, height: innerHeight },
      documentOverflow: {
        x: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        y: document.documentElement.scrollHeight > document.documentElement.clientHeight,
      },
    };
    const basePass = result.installed && result.version === ${JSON.stringify(SKIN_VERSION)} &&
      result.stylePresent && result.chromePresent && result.chromePointerEvents === 'none' &&
      result.petPresent && result.petInteractive && result.petPointerEvents === 'none' &&
      Boolean(result.composer?.visible) && Boolean(result.sidebar?.visible) && !result.documentOverflow.x;
    // Project selector markup varies across Codex builds — soft requirement.
    const homePass = !result.homeRoute || (
      result.homePresent && result.hero?.visible && result.hero.width >= 280 && result.hero.height >= 120 &&
      result.visibleCardCount >= 1 && result.visibleCardCount <= 6
    );
    result.pass = Boolean(basePass && homePass);
    result.softNotes = {
      projectButtonOptional: !result.projectButton?.visible,
    };
    return result;
  })()`);
}

async function waitForVerifiedSession(session, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let lastResult;
  while (Date.now() < deadline) {
    lastResult = await verifySession(session);
    if (lastResult.pass) return lastResult;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return lastResult;
}

async function capture(session, outputPath) {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await session.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await session.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  const viewport = await session.evaluate("({ width: innerWidth, height: innerHeight })");
  await session.send("Input.dispatchMouseEvent", {
    type: "mouseMoved",
    x: Math.round(viewport.width * 0.64),
    y: Math.round(viewport.height * 0.62),
    button: "none",
  });
  await new Promise((resolve) => setTimeout(resolve, 300));
  const result = await session.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  });
  await fs.writeFile(outputPath, Buffer.from(result.data, "base64"));
}

async function runOneShot(options) {
  const connected = await connectCodexTargets(options.port, options.timeoutMs);
  const loaded = (options.mode === "once" || options.reload) ? await loadLivePayload(options.themeDir) : null;
  const payload = loaded?.payload ?? null;
  const results = [];
  let screenshotCaptured = false;

  for (const { target, session, probe } of connected) {
    try {
      if (options.mode === "remove") {
        await removeBugfireBinding(session);
        await removeFromSession(session);
      }
      else if (options.mode === "once") await applyToSession(session, payload);

      if (options.reload) {
        await session.send("Page.reload", { ignoreCache: true });
        await new Promise((resolve) => setTimeout(resolve, 1600));
        if (options.mode !== "remove") await applyToSession(session, payload);
      }

      const result = options.mode === "remove"
        ? await verifyRemovedSession(session)
        : await waitForVerifiedSession(session, options.timeoutMs);
      results.push({ targetId: target.id, title: target.title, url: target.url, probe, result });

      if (options.screenshot && !screenshotCaptured) {
        await capture(session, options.screenshot);
        screenshotCaptured = true;
      }
    } finally {
      session.close();
    }
  }

  console.log(JSON.stringify({ mode: options.mode, version: SKIN_VERSION, port: options.port, targets: results }, null, 2));
  const failed = results.length === 0 || results.some((item) => options.mode === "remove" ? item.result !== true : !item.result?.pass);
  if (failed) process.exitCode = 2;
}

async function runWatch(options) {
  const loaded = await loadLivePayload(options.themeDir);
  const runtime = {
    progress: validateProgress(loaded.progress),
    theme: loaded.theme,
    queue: Promise.resolve(),
  };
  await withProgressLock(BUGFIRE_STATE_PATH, async (assertLockHeld) => {
    const persisted = await loadProgress(BUGFIRE_STATE_PATH, {
      petId: runtime.theme.pet.id,
      seasonId: runtime.theme.pet.season,
    });
    assertLockHeld();
    await saveProgress(BUGFIRE_STATE_PATH, persisted);
    assertLockHeld();
    runtime.progress = persisted;
  });
  const sessions = new Map();
  const rejected = new Set();
  let stopping = false;
  const broadcast = async (progress, result) => {
    const updates = [...sessions.values()].map((active) =>
      hydrateBugfireSession(active, progress, result));
    const settled = await Promise.allSettled(updates);
    for (const update of settled) {
      if (update.status === "rejected") {
        console.error(`[bugfire] hydrate failed: ${update.reason?.message ?? update.reason}`);
      }
    }
  };
  const applyCurrent = async (session) => {
    const current = await loadPayload(options.themeDir, runtime.progress);
    return applyToSession(session, current.payload);
  };
  const stop = () => { stopping = true; };
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);

  while (!stopping) {
    let targets = [];
    try {
      targets = await listAppTargets(options.port);
    } catch (error) {
      console.error(`[dream-skin] ${new Date().toISOString()} ${error.message}`);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      continue;
    }

    const activeIds = new Set(targets.map((target) => target.id));
    for (const [id, session] of sessions) {
      if (!activeIds.has(id) || session.closed) {
        session.close();
        sessions.delete(id);
      }
    }

    for (const target of targets) {
      if (sessions.has(target.id)) continue;
      let session;
      try {
        session = await connectTarget(target, options.port);
        const probe = await probeSession(session);
        if (!probe?.codex) {
          session.close();
          if (!rejected.has(target.id)) {
            console.error(`[dream-skin] rejected non-Codex app target ${target.id}`);
            rejected.add(target.id);
          }
          continue;
        }
        rejected.delete(target.id);
        await installBugfireBinding(session, runtime, broadcast);
        session.on("Page.loadEventFired", () => {
          setTimeout(() => applyCurrent(session).catch((error) => {
            console.error(`[dream-skin] reinject failed: ${error.message}`);
            if (sessions.get(target.id) === session) sessions.delete(target.id);
            session.close();
          }), 250);
        });
        await applyCurrent(session);
        sessions.set(target.id, session);
        console.log(`[dream-skin] injected verified Codex target ${target.id} (${target.title || target.url})`);
      } catch (error) {
        session?.close();
        console.error(`[dream-skin] inject failed for ${target.id}: ${error.message}`);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 900));
  }

  // SIGTERM is a graceful boundary: finish any in-flight atomic save before
  // detaching the renderer binding, then close the CDP sessions.
  await runtime.queue;
  for (const session of sessions.values()) {
    await removeBugfireBinding(session);
    session.close();
  }
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.mode === "check") {
    const loaded = await loadPayload(options.themeDir);
    console.log(JSON.stringify({
      pass: true,
      version: SKIN_VERSION,
      themeId: loaded.theme.id,
      themeName: loaded.theme.name,
      imageBytes: loaded.imageBytes,
      petArtBytes: loaded.petArtBytes,
      petAssetPayloadBytes: loaded.petAssetPayloadBytes,
      payloadBytes: Buffer.byteLength(loaded.payload),
    }, null, 2));
  } else if (options.mode === "watch") await runWatch(options);
  else await runOneShot(options);
} catch (error) {
  console.error(`[dream-skin] ${error.stack || error.message}`);
  process.exitCode = 1;
}
