((cssText, artDataUrl, themeConfig, initialProgress, petAssetData) => {
  const STATE_KEY = "__CODEX_DREAM_SKIN_STATE__";
  const DISABLED_KEY = "__CODEX_DREAM_SKIN_DISABLED__";
  const STYLE_ID = "codex-dream-skin-style";
  const CHROME_ID = "codex-dream-skin-chrome";
  const PET_ID = "codex-bugfire-pet";
  const GROWTH_CARD_ID = "codex-bugfire-growth-card";
  const CERTIFICATE_ID = "codex-bugfire-certificate";
  const SHELL_ATTR = "data-dream-shell";
  const VERSION = __DREAM_SKIN_VERSION_JSON__;
  const THEME = themeConfig && typeof themeConfig === "object" ? themeConfig : {};
  const PET_ASSETS = petAssetData && typeof petAssetData === "object" ? petAssetData : {};
  const BUGFIRE_STATES = Object.freeze([
    "idle", "building", "bug", "fire", "success", "level-up",
  ]);
  const BUGFIRE_DISCLAIMER = "个人成长纪念卡，由本地活动生成；非官方认证，不代表专业资格。";
  const DEFAULT_LEVELS = Object.freeze([
    { level: 1, minXp: 0, stage: "会描述", skill: "灵感火星" },
    { level: 2, minXp: 100, stage: "会搭建", skill: "结构嗅探" },
    { level: 3, minXp: 240, stage: "会除虫", skill: "BUGFIRE" },
    { level: 4, minXp: 450, stage: "会验收", skill: "测试结界" },
    { level: 5, minXp: 750, stage: "会交付", skill: "发布跃迁" },
  ]);
  const THEME_VARIABLES = [
    "--ds-bg", "--ds-panel", "--ds-panel-2", "--ds-green", "--ds-lime",
    "--ds-cyan", "--ds-purple", "--ds-text", "--ds-muted", "--ds-line",
    "--dream-skin-name", "--dream-skin-tagline", "--dream-skin-project-prefix",
    "--dream-skin-project-label",
  ];
  window[DISABLED_KEY] = false;

  const previous = window[STATE_KEY];
  try { previous?.pet?.cleanup?.(); } catch {}
  if (previous?.observer) previous.observer.disconnect();
  if (previous?.timer) clearInterval(previous.timer);
  if (previous?.scheduler?.timeout) clearTimeout(previous.scheduler.timeout);
  if (previous?.resizeHandler) window.removeEventListener("resize", previous.resizeHandler);
  if (previous?.mediaHandler && previous?.mediaQuery) {
    try { previous.mediaQuery.removeEventListener("change", previous.mediaHandler); } catch {}
  }
  if (previous?.artUrl) URL.revokeObjectURL(previous.artUrl);

  const artUrl = (() => {
    const comma = artDataUrl.indexOf(",");
    const mime = /^data:([^;,]+)/.exec(artDataUrl)?.[1] || "image/png";
    const binary = atob(artDataUrl.slice(comma + 1));
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
    return URL.createObjectURL(new Blob([bytes], { type: mime }));
  })();

  const cssString = (value) => JSON.stringify(String(value ?? ""));

  const parseRgb = (value) => {
    if (!value || value === "transparent") return null;
    const m = String(value).match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i);
    if (!m) return null;
    return { r: Number(m[1]), g: Number(m[2]), b: Number(m[3]) };
  };

  const luminance = ({ r, g, b }) => {
    const lin = [r, g, b].map((c) => {
      const x = c / 255;
      return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
  };

  /** Detect Codex app light/dark shell for CSS branching. */
  const detectShellMode = () => {
    const root = document.documentElement;
    const body = document.body;
    const cls = `${root.className || ""} ${body?.className || ""}`.toLowerCase();

    if (/\b(dark|theme-dark|appearance-dark)\b/.test(cls)) return "dark";
    if (/\b(light|theme-light|appearance-light)\b/.test(cls)) return "light";

    const dataTheme = (
      root.getAttribute("data-theme") ||
      root.getAttribute("data-appearance") ||
      root.getAttribute("data-color-mode") ||
      body?.getAttribute("data-theme") ||
      body?.getAttribute("data-appearance") ||
      ""
    ).toLowerCase();
    if (dataTheme.includes("dark")) return "dark";
    if (dataTheme.includes("light")) return "light";

    // Radios in profile menu (if present in DOM)
    const checked = document.querySelector('input[name="appearance-theme"]:checked');
    if (checked) {
      const label = (checked.getAttribute("aria-label") || checked.value || "").toLowerCase();
      if (label.includes("暗") || label.includes("dark")) return "dark";
      if (label.includes("浅") || label.includes("light")) return "light";
      if (label.includes("系统") || label.includes("system")) {
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      }
    }

    try {
      const cs = getComputedStyle(root).colorScheme || "";
      if (cs.includes("dark") && !cs.includes("light")) return "dark";
      if (cs.includes("light") && !cs.includes("dark")) return "light";
    } catch {}

    // Background luminance of main surfaces
    const samples = [
      body,
      document.querySelector("main.main-surface"),
      document.querySelector("aside.app-shell-left-panel"),
    ].filter(Boolean);
    let votesLight = 0;
    let votesDark = 0;
    for (const el of samples) {
      try {
        const rgb = parseRgb(getComputedStyle(el).backgroundColor);
        if (!rgb) continue;
        const L = luminance(rgb);
        if (L >= 0.55) votesLight += 1;
        else if (L <= 0.25) votesDark += 1;
      } catch {}
    }
    if (votesLight > votesDark) return "light";
    if (votesDark > votesLight) return "dark";

    try {
      if (window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
    } catch {}
    return "light";
  };

  const applyTheme = (root, shell) => {
    const colors = THEME.colors || {};
    const accent = colors.accent || (shell === "light" ? "#e25563" : "#7cff46");
    const accentAlt = colors.accentAlt || accent;
    const secondary = colors.secondary || (shell === "light" ? "#f3a8af" : "#36d7e8");
    const highlight = colors.highlight || (shell === "light" ? "#c93d4c" : "#642a8c");

    let variables;
    if (shell === "light") {
      // Structural tokens stay light so banners stay readable; accents follow theme.
      variables = {
        "--ds-bg": "#f6f2f3",
        "--ds-panel": "#ffffff",
        "--ds-panel-2": "#fff7f8",
        "--ds-green": accent,
        "--ds-lime": accentAlt,
        "--ds-cyan": secondary,
        "--ds-purple": highlight,
        "--ds-text": "#1f1a1b",
        "--ds-muted": "#6b5f62",
        "--ds-line": colors.line || "rgba(196, 120, 128, .22)",
      };
    } else {
      variables = {
        "--ds-bg": colors.background || "#071116",
        "--ds-panel": colors.panel || "#0b1a20",
        "--ds-panel-2": colors.panelAlt || "#10272c",
        "--ds-green": accent,
        "--ds-lime": accentAlt,
        "--ds-cyan": secondary,
        "--ds-purple": highlight,
        "--ds-text": colors.text || "#e9fff1",
        "--ds-muted": colors.muted || "#9ebdb3",
        "--ds-line": colors.line || "rgba(124, 255, 70, .28)",
      };
    }

    for (const [name, value] of Object.entries(variables)) {
      if (typeof value === "string" && value) root.style.setProperty(name, value);
    }
    root.style.setProperty("--dream-skin-name", cssString(THEME.name || "Codex Dream Skin"));
    root.style.setProperty("--dream-skin-tagline", cssString(THEME.tagline || "Make something wonderful."));
    root.style.setProperty("--dream-skin-project-prefix", cssString(THEME.projectPrefix || "选择项目 · "));
    root.style.setProperty("--dream-skin-project-label", cssString(THEME.projectLabel || "◉  选择项目"));
  };

  const configuredPet = THEME.pet && typeof THEME.pet === "object" ? THEME.pet : {};
  const configuredLevels = Array.isArray(configuredPet.levels) && configuredPet.levels.length === 5
    ? configuredPet.levels : DEFAULT_LEVELS;
  const PET_LEVELS = configuredLevels.map((entry, index) => ({
    level: Number.isSafeInteger(entry?.level) ? entry.level : DEFAULT_LEVELS[index].level,
    minXp: Number.isSafeInteger(entry?.minXp) ? entry.minXp : DEFAULT_LEVELS[index].minXp,
    stage: String(entry?.stage || DEFAULT_LEVELS[index].stage),
    skill: String(entry?.skill || DEFAULT_LEVELS[index].skill),
  })).sort((left, right) => left.minXp - right.minXp);
  const PET_META = Object.freeze({
    id: String(configuredPet.id || "bugfire-patch-dragon"),
    name: String(configuredPet.name || "补丁兽"),
    seasonId: String(configuredPet.season || "season-1"),
    season: String(configuredPet.seasonLabel || configuredPet.season || "BUGFIRE · SEASON 1"),
    demoReward: Number.isSafeInteger(configuredPet.demoReward) && configuredPet.demoReward >= 0
      ? configuredPet.demoReward : 35,
    sayings: Array.isArray(configuredPet.sayings) && configuredPet.sayings.length
      ? configuredPet.sayings.map(String) : ["今天也一起把 Bug 烧掉。"],
    quests: Array.isArray(configuredPet.quests) ? configuredPet.quests : [],
    certificateTitle: String(configuredPet.certificateTitle || "BUGFIRE 赛季证书"),
  });

  const fallbackProgress = () => ({
    schemaVersion: 1,
    petId: PET_META.id,
    seasonId: PET_META.seasonId,
    xp: 220,
    failedBuilds: 0,
    successfulBuilds: 0,
    repairedBuilds: 0,
    unlockedSkills: PET_LEVELS.filter((entry) => entry.minXp <= 220).map((entry) => entry.skill),
    cards: [],
    settledEventIds: [],
    updatedAt: new Date().toISOString(),
  });

  const normalizeProgress = (value) => {
    let candidate = value;
    if (typeof candidate === "string") {
      try { candidate = JSON.parse(candidate); } catch { candidate = null; }
    }
    if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
      return fallbackProgress();
    }
    const base = fallbackProgress();
    const integer = (input, fallback) => Number.isSafeInteger(input) && input >= 0 ? input : fallback;
    return {
      ...base,
      petId: typeof candidate.petId === "string" && candidate.petId ? candidate.petId : base.petId,
      seasonId: typeof candidate.seasonId === "string" && candidate.seasonId
        ? candidate.seasonId : base.seasonId,
      xp: integer(candidate.xp, base.xp),
      failedBuilds: integer(candidate.failedBuilds, base.failedBuilds),
      successfulBuilds: integer(candidate.successfulBuilds, base.successfulBuilds),
      repairedBuilds: integer(candidate.repairedBuilds, base.repairedBuilds),
      unlockedSkills: Array.isArray(candidate.unlockedSkills)
        ? candidate.unlockedSkills.filter((skill) => typeof skill === "string")
        : base.unlockedSkills,
      cards: Array.isArray(candidate.cards)
        ? candidate.cards.filter((card) => card && typeof card === "object")
        : [],
      settledEventIds: Array.isArray(candidate.settledEventIds)
        ? candidate.settledEventIds.filter((eventId) => typeof eventId === "string")
        : [],
      updatedAt: typeof candidate.updatedAt === "string" ? candidate.updatedAt : base.updatedAt,
    };
  };

  const levelForProgress = (value) => {
    let current = PET_LEVELS[0];
    for (const entry of PET_LEVELS) {
      if (value.xp >= entry.minXp) current = entry;
    }
    return current;
  };

  const nextLevelForProgress = (value) => {
    const current = levelForProgress(value);
    return PET_LEVELS.find((entry) => entry.level > current.level) || null;
  };

  const dragonSvg = () => `
    <svg class="bugfire-dragon" viewBox="0 0 96 96" role="img" aria-label="像素补丁龙补丁兽">
      <g class="bugfire-tail">
        <path d="M25 62H13V56H7V44H13V50H25Z" fill="#ff7a2f"/>
        <path d="M13 56H7V50H1V44H7V50H13Z" fill="#ffd15c"/>
      </g>
      <g class="bugfire-wing">
        <path d="M41 39V15H47V9H53V27H59V39Z" fill="#55ed84"/>
        <path d="M47 27V15H53V33H59V39H47Z" fill="#167b50"/>
      </g>
      <g class="bugfire-body">
        <path d="M25 39H31V27H37V21H55V27H67V33H73V45H79V63H73V69H67V75H43V69H31V63H25Z" fill="#31c875"/>
        <path d="M31 45H37V33H61V39H67V51H73V63H67V69H43V63H31Z" fill="#178953"/>
        <path d="M61 33H73V39H79V51H73V57H61Z" fill="#48e18a"/>
        <path d="M43 63H67V69H43Z" fill="#ffad3d"/>
        <path d="M37 69H49V81H43V87H31V81H37Z" fill="#116a46"/>
        <path d="M61 69H73V81H79V87H61Z" fill="#116a46"/>
        <path d="M37 21H43V15H49V21M55 27V15H61V21H67V27" fill="#ff7a2f"/>
        <rect class="bugfire-eye" x="65" y="39" width="6" height="6" fill="#071116"/>
        <rect x="67" y="39" width="2" height="2" fill="#e9fff1"/>
        <path d="M79 51H91V57H79Z" fill="#10272c"/>
      </g>
      <g class="bugfire-flame">
        <path d="M78 51H84V45H90V39H96V57H90V63H84V57H78Z" fill="#ff6a2a"/>
        <path d="M84 51H90V45H96V57H84Z" fill="#ffd15c"/>
      </g>
      <g class="bugfire-bug">
        <rect x="76" y="66" width="12" height="12" rx="2" fill="#ff5364"/>
        <path d="M73 68H76M88 68H91M73 76H76M88 76H91M79 63V66M85 63V66" stroke="#ff8d99" stroke-width="3"/>
        <rect x="79" y="69" width="3" height="3" fill="#071116"/>
        <rect x="84" y="69" width="3" height="3" fill="#071116"/>
      </g>
      <g class="bugfire-spark" fill="#b8ff3d">
        <rect x="17" y="24" width="4" height="4"/><rect x="83" y="23" width="4" height="4"/>
        <rect x="9" y="34" width="3" height="3"/><rect x="73" y="13" width="3" height="3"/>
      </g>
    </svg>`;

  const petVisual = () => `
    <span class="bugfire-custom-art" data-bugfire-custom-art aria-hidden="true"></span>
    <span class="bugfire-default-art">${dragonSvg()}</span>`;

  let progress = normalizeProgress(initialProgress);
  let petState = "idle";
  let demoNeedsRepair = progress.failedBuilds > progress.repairedBuilds;
  let pendingOutcome = null;
  let pendingEventId = null;
  let keyboardAttached = false;
  let animationToken = 0;
  const petTimers = new Set();

  const petAfter = (callback, delay) => {
    const timerId = setTimeout(() => {
      petTimers.delete(timerId);
      callback();
    }, delay);
    petTimers.add(timerId);
    return timerId;
  };

  const petRoot = () => document.getElementById(PET_ID);
  const petNode = (selector) => petRoot()?.querySelector(selector) || null;

  const resolvePetAsset = (requestedState) => {
    const normalizedState = requestedState === "level-up" ? "levelUp" : requestedState;
    const candidates = normalizedState === "idle" ? ["idle"] : [normalizedState, "idle"];
    for (const candidate of candidates) {
      let state = candidate;
      const visited = new Set();
      while (typeof state === "string" && !visited.has(state)) {
        visited.add(state);
        const asset = Object.hasOwn(PET_ASSETS, state) ? PET_ASSETS[state] : null;
        if (typeof asset === "string") {
          if (/^data:image\/(?:png|jpeg|webp);base64,/i.test(asset)) return asset;
          break;
        }
        if (!asset || typeof asset !== "object" || Array.isArray(asset) || typeof asset.ref !== "string") break;
        state = asset.ref;
      }
    }
    return "";
  };

  const applyPetAsset = (scope, state) => {
    if (!scope) return false;
    const asset = resolvePetAsset(state);
    const nodes = [
      ...(scope.matches?.("[data-bugfire-custom-art]") ? [scope] : []),
      ...scope.querySelectorAll("[data-bugfire-custom-art]"),
    ];
    for (const node of nodes) {
      node.style.backgroundImage = asset ? `url(${JSON.stringify(asset)})` : "";
      node.toggleAttribute("data-bugfire-custom-art-active", Boolean(asset));
    }
    return Boolean(asset);
  };

  const setPetState = (nextState) => {
    const resolved = BUGFIRE_STATES.includes(nextState) ? nextState : "idle";
    petState = resolved;
    const root = petRoot();
    if (!root) return;
    root.setAttribute("data-bugfire-state", resolved);
    applyPetAsset(root, resolved);
    const labels = {
      idle: "READY", building: "BUILDING", bug: "BUG FOUND",
      fire: "BUGFIRE", success: "BUILD PASS", "level-up": "LEVEL UP",
    };
    const badge = root.querySelector("[data-bugfire-status]");
    if (badge) badge.textContent = labels[resolved];
  };

  const setPetLog = (message, tone = "neutral") => {
    const log = petNode("[data-bugfire-log]");
    if (!log) return;
    log.textContent = message;
    log.setAttribute("data-bugfire-tone", tone);
  };

  const setBuildPending = (pending) => {
    const button = petNode('[data-bugfire-action="build"]');
    if (!button) return;
    button.disabled = pending;
    button.setAttribute("aria-busy", pending ? "true" : "false");
  };

  const renderProgress = () => {
    const root = petRoot();
    if (!root) return;
    const level = levelForProgress(progress);
    const next = nextLevelForProgress(progress);
    const startXp = level.minXp;
    const endXp = next?.minXp ?? Math.max(startXp, progress.xp);
    const range = Math.max(1, endXp - startXp);
    const percent = next ? Math.max(0, Math.min(100, ((progress.xp - startXp) / range) * 100)) : 100;
    const setText = (selector, value) => {
      const node = root.querySelector(selector);
      if (node) node.textContent = String(value);
    };
    setText("[data-bugfire-name]", PET_META.name);
    setText("[data-bugfire-season]", PET_META.season);
    setText("[data-bugfire-level]", level.level);
    setText("[data-bugfire-level-label]", `Lv${level.level}`);
    setText("[data-bugfire-stage]", level.stage);
    setText("[data-bugfire-skill]", level.skill);
    setText("[data-bugfire-xp]", next ? `${progress.xp} / ${next.minXp} XP` : `${progress.xp} XP · MAX`);
    setText(
      "[data-bugfire-counts]",
      `成功 ${progress.successfulBuilds} · 修复 ${progress.repairedBuilds} · 失败 ${progress.failedBuilds}`,
    );
    const fill = root.querySelector("[data-bugfire-xp-fill]");
    if (fill) fill.style.width = `${percent.toFixed(1)}%`;
    const build = root.querySelector('[data-bugfire-action="build"]');
    if (build && !pendingOutcome) {
      build.textContent = demoNeedsRepair ? "已修复，重新 Build" : "BUILD · 演示";
      build.disabled = false;
      build.setAttribute("aria-busy", "false");
    }
    const skills = root.querySelector("[data-bugfire-skills]");
    if (skills) {
      skills.replaceChildren();
      for (const skill of progress.unlockedSkills) {
        const chip = document.createElement("span");
        chip.textContent = skill;
        skills.appendChild(chip);
      }
    }
    const certificate = progress.cards.find((card) => card.kind === "season") || null;
    const certificateButton = root.querySelector('[data-bugfire-action="certificate"]');
    if (certificateButton) certificateButton.hidden = !certificate;
    const questList = root.querySelector("[data-bugfire-quests]");
    if (questList) {
      questList.replaceChildren();
      for (const quest of PET_META.quests) {
        const metricValue = quest.metric === "level" ? level.level : Number(progress[quest.metric] || 0);
        const complete = metricValue >= Number(quest.target || 1);
        const item = document.createElement("li");
        item.toggleAttribute("data-bugfire-quest-complete", complete);
        item.textContent = `${complete ? "✓" : "○"} ${quest.title} · ${Math.min(metricValue, quest.target)}/${quest.target}`;
        questList.appendChild(item);
      }
    }
  };

  const closePet = () => {
    const root = petRoot();
    if (!root) return false;
    const wasOpen = root.getAttribute("data-bugfire-open") === "true";
    root.setAttribute("data-bugfire-open", "false");
    const toggle = root.querySelector('[data-bugfire-action="toggle"]');
    const cabin = root.querySelector(".bugfire-cabin");
    toggle?.setAttribute("aria-expanded", "false");
    if (cabin) {
      cabin.setAttribute("aria-hidden", "true");
      cabin.inert = true;
    }
    return wasOpen;
  };

  const openPet = () => {
    const root = petRoot();
    if (!root || root.getAttribute("data-bugfire-route") === "task") return false;
    root.setAttribute("data-bugfire-open", "true");
    const toggle = root.querySelector('[data-bugfire-action="toggle"]');
    const cabin = root.querySelector(".bugfire-cabin");
    toggle?.setAttribute("aria-expanded", "true");
    if (cabin) {
      cabin.setAttribute("aria-hidden", "false");
      cabin.inert = false;
    }
    return true;
  };

  const closeGrowthCard = () => {
    document.getElementById(GROWTH_CARD_ID)?.remove();
    if (petState === "level-up") setPetState("idle");
  };

  const closeCertificate = () => document.getElementById(CERTIFICATE_ID)?.remove();

  const drawDefaultCertificatePet = (context) => {
    context.fillStyle = "#31c875";
    context.fillRect(390, 575, 420, 190);
    context.fillStyle = "#ff7a2f";
    context.fillRect(760, 620, 120, 42);
    context.fillStyle = "#071116";
    context.fillRect(690, 620, 42, 42);
    context.fillStyle = "#b8ff3d";
    context.fillRect(455, 535, 52, 52);
    context.fillRect(625, 535, 52, 52);
  };

  const drawCertificatePet = async (context) => {
    const asset = resolvePetAsset("success");
    if (!asset) {
      drawDefaultCertificatePet(context);
      return false;
    }
    try {
      const image = await new Promise((resolve, reject) => {
        const candidate = new Image();
        candidate.onload = () => resolve(candidate);
        candidate.onerror = () => reject(new Error("Custom pet art could not be decoded"));
        candidate.src = asset;
      });
      const sourceWidth = image.naturalWidth || image.width;
      const sourceHeight = image.naturalHeight || image.height;
      if (!sourceWidth || !sourceHeight) throw new Error("Custom pet art has no drawable dimensions");
      const scale = Math.min(640 / sourceWidth, 330 / sourceHeight);
      const width = Math.max(1, Math.round(sourceWidth * scale));
      const height = Math.max(1, Math.round(sourceHeight * scale));
      const x = Math.round(600 - width / 2);
      const y = Math.round(493 + (360 - height) / 2);
      context.imageSmoothingEnabled = false;
      context.drawImage(image, x, y, width, height);
      return true;
    } catch {
      drawDefaultCertificatePet(context);
      return false;
    }
  };

  const renderCertificateDataUrl = async (requestedCard) => {
    const card = requestedCard || progress.cards.find((entry) => entry.kind === "season") || {};
    const canvas = document.createElement("canvas");
    canvas.width = 1200;
    canvas.height = 1500;
    const context = canvas.getContext("2d");
    if (!context) return "data:image/png;base64,";

    context.fillStyle = "#f4ecd7";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#071116";
    context.fillRect(54, 54, 1092, 1392);
    context.strokeStyle = "#ff6a2a";
    context.lineWidth = 8;
    context.strokeRect(82, 82, 1036, 1336);
    context.strokeStyle = "#7cff46";
    context.lineWidth = 3;
    context.strokeRect(104, 104, 992, 1292);

    context.fillStyle = "#7cff46";
    context.font = "700 35px ui-monospace, Menlo, monospace";
    context.textAlign = "center";
    context.fillText("CODEX · BUGFIRE", 600, 182);
    context.fillStyle = "#f4ecd7";
    context.font = "900 86px system-ui, sans-serif";
    context.fillText(PET_META.certificateTitle, 600, 315);
    context.fillStyle = "#ff8a3d";
    context.font = "700 28px ui-monospace, Menlo, monospace";
    context.fillText(PET_META.season, 600, 380);

    context.fillStyle = "#10272c";
    context.fillRect(220, 468, 760, 430);
    context.strokeStyle = "#36d7e8";
    context.lineWidth = 4;
    context.strokeRect(220, 468, 760, 430);
    await drawCertificatePet(context);
    context.fillStyle = "#f4ecd7";
    context.font = "800 42px system-ui, sans-serif";
    context.fillText(PET_META.name, 600, 846);

    const currentLevel = levelForProgress(progress);
    context.fillStyle = "#f4ecd7";
    context.font = "700 43px system-ui, sans-serif";
    context.fillText(`Lv${currentLevel.level} · ${currentLevel.stage} · ${currentLevel.skill}`, 600, 1000);
    context.fillStyle = "#9ebdb3";
    context.font = "500 26px system-ui, sans-serif";
    const earned = typeof card.earnedAt === "string" ? card.earnedAt.slice(0, 10) : "LOCAL SEASON";
    context.fillText(`SUCCESS ${progress.successfulBuilds}  /  REPAIR ${progress.repairedBuilds}  /  ${earned}`, 600, 1070);
    context.fillStyle = "#f4ecd7";
    context.font = "500 27px system-ui, sans-serif";
    context.fillText("个人成长纪念卡，由本地活动生成；", 600, 1212);
    context.fillText("非官方认证，不代表专业资格。", 600, 1257);
    context.fillStyle = "#7cff46";
    context.font = "700 23px ui-monospace, Menlo, monospace";
    context.fillText("BUILD · FIX · LEARN · SHIP", 600, 1362);
    return canvas.toDataURL("image/png");
  };

  const exportCertificate = async (card) => {
    const link = document.createElement("a");
    link.href = await renderCertificateDataUrl(card);
    const safeSeason = String(progress.seasonId || "season-1").replace(/[^a-z0-9_-]+/gi, "-");
    link.download = `BUGFIRE-${safeSeason}.png`;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const showCertificate = (requestedCard) => {
    const card = requestedCard || progress.cards.find((entry) => entry.kind === "season");
    if (!card || !document.body) return false;
    closeCertificate();
    const modal = document.createElement("div");
    modal.id = CERTIFICATE_ID;
    modal.className = "bugfire-modal";
    modal.setAttribute("data-bugfire-interactive", "");
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", PET_META.certificateTitle);
    modal.innerHTML = `
      <div class="bugfire-surface bugfire-certificate">
        <button class="bugfire-close" type="button" data-bugfire-close aria-label="关闭证书">×</button>
        <div class="bugfire-certificate-mark" data-bugfire-decoration>${petVisual()}</div>
        <small>CODEX · BUGFIRE</small>
        <h2 data-bugfire-certificate-title></h2>
        <p data-bugfire-certificate-season></p>
        <strong data-bugfire-certificate-level></strong>
        <div class="bugfire-certificate-stats" data-bugfire-certificate-stats></div>
        <p class="bugfire-disclaimer">个人成长纪念卡，由本地活动生成；非官方认证，不代表专业资格。</p>
        <div class="bugfire-card-actions">
          <button type="button" data-bugfire-export>导出 PNG</button>
        </div>
      </div>`;
    const level = levelForProgress(progress);
    modal.querySelector("[data-bugfire-certificate-title]").textContent = PET_META.certificateTitle;
    modal.querySelector("[data-bugfire-certificate-season]").textContent = PET_META.season;
    modal.querySelector("[data-bugfire-certificate-level]").textContent =
      `Lv${level.level} · ${level.stage} · ${level.skill}`;
    modal.querySelector("[data-bugfire-certificate-stats]").textContent =
      `成功 Build ${progress.successfulBuilds} 次 · 修复重建 ${progress.repairedBuilds} 次`;
    modal.querySelector("[data-bugfire-close]").addEventListener("click", closeCertificate);
    modal.querySelector("[data-bugfire-export]").addEventListener("click", () => {
      void exportCertificate(card);
    });
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeCertificate();
    });
    document.body.appendChild(modal);
    applyPetAsset(modal, "success");
    modal.querySelector("[data-bugfire-close]")?.focus({ preventScroll: true });
    return true;
  };

  const showGrowthCard = (card, seasonCard = null) => {
    if (!card || !document.body) return false;
    closeGrowthCard();
    setPetState("level-up");
    const modal = document.createElement("div");
    modal.id = GROWTH_CARD_ID;
    modal.className = "bugfire-modal";
    modal.setAttribute("data-bugfire-interactive", "");
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", "补丁兽成长卡");
    modal.innerHTML = `
      <div class="bugfire-surface bugfire-card">
        <button class="bugfire-close" type="button" data-bugfire-close aria-label="关闭成长卡">×</button>
        <small>VIBE CODING · LEVEL UP</small>
        <div class="bugfire-card-dragon" data-bugfire-decoration>${petVisual()}</div>
        <p>PATCH DRAGON UPGRADED</p>
        <h2 data-bugfire-card-level></h2>
        <strong data-bugfire-card-stage></strong>
        <span>新技能</span>
        <b data-bugfire-card-skill></b>
        <div class="bugfire-card-actions">
          <button type="button" data-bugfire-card-certificate hidden>查看赛季证书</button>
        </div>
      </div>`;
    modal.querySelector("[data-bugfire-card-level]").textContent = `Lv${card.level}`;
    modal.querySelector("[data-bugfire-card-stage]").textContent = card.stage || "新阶段";
    modal.querySelector("[data-bugfire-card-skill]").textContent = card.skill || "新技能";
    const certificateButton = modal.querySelector("[data-bugfire-card-certificate]");
    if (seasonCard) {
      certificateButton.hidden = false;
      certificateButton.addEventListener("click", () => {
        closeGrowthCard();
        showCertificate(seasonCard);
      });
    }
    modal.querySelector("[data-bugfire-close]").addEventListener("click", closeGrowthCard);
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeGrowthCard();
    });
    document.body.appendChild(modal);
    applyPetAsset(modal, "level-up");
    modal.querySelector("[data-bugfire-close]")?.focus({ preventScroll: true });
    return true;
  };

  const fallbackSettle = (outcome, eventId) => {
    const before = levelForProgress(progress);
    const next = normalizeProgress(progress);
    const awardedXp = outcome === "failed" ? 0 : PET_META.demoReward;
    next.xp += awardedXp;
    next.failedBuilds += outcome === "failed" ? 1 : 0;
    next.successfulBuilds += outcome === "failed" ? 0 : 1;
    next.repairedBuilds += outcome === "repair-success" ? 1 : 0;
    next.settledEventIds = [...next.settledEventIds, eventId];
    next.updatedAt = new Date().toISOString();
    next.unlockedSkills = PET_LEVELS.filter((entry) => entry.minXp <= next.xp).map((entry) => entry.skill);
    const after = levelForProgress(next);
    let card = null;
    if (after.level > before.level) {
      card = {
        id: `level-${after.level}-${eventId}`,
        kind: "level",
        level: after.level,
        stage: after.stage,
        skill: after.skill,
        earnedAt: next.updatedAt,
      };
      next.cards = [...next.cards, card];
    }
    hydrateProgress(next, {
      awardedXp,
      duplicate: false,
      levelUp: card ? { from: before.level, to: after.level } : null,
      card,
      eventId,
      outcome,
    });
  };

  const emitSettlement = (outcome, eventId) => {
    if (typeof window.__bugfireSync === "function") {
      try {
        window.__bugfireSync(JSON.stringify({
          type: "settle-build",
          outcome,
          eventId,
          rewardXp: PET_META.demoReward,
        }));
        return true;
      } catch {}
    }
    fallbackSettle(outcome, eventId);
    return false;
  };

  const newEventId = (outcome) => {
    let suffix;
    try { suffix = crypto.randomUUID(); } catch { suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`; }
    return `bugfire-demo-${outcome}-${suffix}`;
  };

  const runDemoBuild = () => {
    if (pendingOutcome) return;
    const outcome = demoNeedsRepair ? "repair-success" : "failed";
    const eventId = newEventId(outcome);
    pendingOutcome = outcome;
    pendingEventId = eventId;
    const token = ++animationToken;
    setPetState("building");
    setBuildPending(true);
    setPetLog(
      outcome === "repair-success" ? "> rebuild --patched\n正在验证补丁…" : "> build --demo\n正在扫描火花与 Bug…",
      "active",
    );
    petAfter(() => {
      if (token !== animationToken || pendingEventId !== eventId) return;
      if (outcome === "failed") {
        demoNeedsRepair = true;
        setPetState("bug");
        setPetLog("✗ BUILD FAILED · 捕获 1 只 Bug\n失败不奖励 XP", "error");
      } else {
        setPetState("fire");
        setPetLog("BUGFIRE 已点燃 · 正在烧掉 Bug…", "fire");
      }
      emitSettlement(outcome, eventId);
    }, outcome === "failed" ? 800 : 620);
    petAfter(() => {
      if (pendingEventId !== eventId) return;
      pendingOutcome = null;
      pendingEventId = null;
      setBuildPending(false);
      renderProgress();
      setPetLog("本地进度同步超时，可再次演示。", "error");
    }, 5000);
  };

  function hydrateProgress(nextProgress, result = null) {
    const previousCardIds = new Set(progress.cards.map((card) => card.id));
    progress = normalizeProgress(nextProgress);
    const settlement = result?.result && typeof result.result === "object"
      ? {
          ...result.result,
          eventId: result.eventId ?? result.result.eventId,
          outcome: result.outcome ?? result.result.outcome,
        }
      : (result || {});
    demoNeedsRepair = progress.failedBuilds > progress.repairedBuilds;
    const eventMatchesPending = Boolean(
      pendingEventId && settlement.eventId === pendingEventId,
    );
    const outcome = eventMatchesPending ? (settlement.outcome || pendingOutcome) : null;
    const newCards = progress.cards.filter((card) => !previousCardIds.has(card.id));
    const growthCard = settlement.card || newCards.find((card) => card.kind === "level") || null;
    const seasonCard = newCards.find((card) => card.kind === "season") || null;

    if (settlement.reset) {
      pendingOutcome = null;
      pendingEventId = null;
      animationToken += 1;
      closeGrowthCard();
      closeCertificate();
      setPetState("idle");
      setPetLog("体验进度已重置 · 从 Lv1 重新出发", "success");
    } else if (!eventMatchesPending) {
      renderProgress();
      return { progress, result: settlement, state: petState };
    } else if (settlement.error) {
      pendingOutcome = null;
      pendingEventId = null;
      animationToken += 1;
      setPetState("bug");
      setPetLog(settlement.message || "本地进度保存失败，未结算 XP。", "error");
    } else if (settlement.duplicate) {
      pendingOutcome = null;
      pendingEventId = null;
      animationToken += 1;
      setPetState("idle");
      setPetLog("这个 Build 已结算，不会重复奖励 XP。", "neutral");
    } else if (outcome === "failed") {
      pendingOutcome = null;
      pendingEventId = null;
      animationToken += 1;
      setPetState("bug");
      setPetLog("✗ BUILD FAILED · Bug 已入笼\n失败不奖励 XP", "error");
    } else if (outcome === "repair-success" || outcome === "success") {
      pendingOutcome = null;
      pendingEventId = null;
      const token = ++animationToken;
      setPetState(outcome === "repair-success" ? "fire" : "success");
      setPetLog(
        outcome === "repair-success"
          ? `BUGFIRE 命中 · +${settlement.awardedXp ?? PET_META.demoReward} XP`
          : `✓ BUILD PASS · +${settlement.awardedXp ?? PET_META.demoReward} XP`,
        "success",
      );
      petAfter(() => {
        if (token !== animationToken) return;
        setPetState("success");
        setPetLog(`✓ BUILD PASS · +${settlement.awardedXp ?? PET_META.demoReward} XP`, "success");
      }, outcome === "repair-success" ? 680 : 0);
      petAfter(() => {
        if (token !== animationToken) return;
        if (growthCard) showGrowthCard(growthCard, seasonCard);
        else if (seasonCard) showCertificate(seasonCard);
        else setPetState("idle");
      }, growthCard || seasonCard ? 1250 : 1450);
    }
    renderProgress();
    setBuildPending(false);
    return { progress, result: settlement, state: petState };
  }

  const resetDemo = () => {
    pendingOutcome = null;
    pendingEventId = null;
    animationToken += 1;
    if (typeof window.__bugfireSync === "function") {
      try {
        window.__bugfireSync(JSON.stringify({ type: "reset" }));
        setPetLog("正在重置本地体验进度…", "active");
        setBuildPending(true);
        return;
      } catch {}
    }
    const reset = fallbackProgress();
    reset.xp = 0;
    reset.unlockedSkills = [PET_LEVELS[0].skill];
    hydrateProgress(reset, { reset: true });
  };

  const petClickHandler = (event) => {
    const actionNode = event.target.closest?.("[data-bugfire-action]");
    if (!actionNode || !petRoot()?.contains(actionNode)) return;
    const action = actionNode.getAttribute("data-bugfire-action");
    if (action === "toggle") {
      if (petRoot()?.getAttribute("data-bugfire-open") === "true") closePet();
      else openPet();
    } else if (action === "close") closePet();
    else if (action === "pet") {
      const saying = PET_META.sayings[Math.floor(Math.random() * PET_META.sayings.length)];
      setPetLog(`> ${PET_META.name}\n${saying}`, "success");
    }
    else if (action === "build") runDemoBuild();
    else if (action === "reset") resetDemo();
    else if (action === "certificate") showCertificate();
  };

  const keyboardHandler = (event) => {
    if (event.key === "Escape") {
      const hadOverlay = Boolean(
        document.getElementById(GROWTH_CARD_ID) || document.getElementById(CERTIFICATE_ID),
      );
      closeGrowthCard();
      closeCertificate();
      if (closePet() || hadOverlay) event.stopPropagation();
    }
  };

  const mountPet = () => {
    if (!document.body) return null;
    let root = document.getElementById(PET_ID);
    if (root) return root;
    root = document.createElement("div");
    root.id = PET_ID;
    root.setAttribute("data-bugfire-mounted", "true");
    root.setAttribute("data-bugfire-state", "idle");
    root.setAttribute("data-bugfire-open", "false");
    root.setAttribute("data-bugfire-route", "home");
    root.setAttribute("aria-label", "BUGFIRE 补丁兽");
    root.innerHTML = `
      <button class="bugfire-nest-toggle" type="button" data-bugfire-interactive
        data-bugfire-action="toggle" aria-expanded="false" aria-controls="bugfire-cabin">
        <span class="bugfire-dragon-wrap" data-bugfire-decoration>${petVisual()}</span>
        <span class="bugfire-status-badge">LV<span data-bugfire-level>2</span></span>
        <span class="bugfire-sr-only">打开补丁兽宠物舱</span>
      </button>
      <section id="bugfire-cabin" class="bugfire-cabin" data-bugfire-interactive
        aria-label="BUGFIRE 补丁兽宠物舱" aria-hidden="true">
        <header class="bugfire-header">
          <div><small data-bugfire-season></small><h2 data-bugfire-name></h2></div>
          <button type="button" data-bugfire-action="close" aria-label="收起宠物舱">×</button>
        </header>
        <button class="bugfire-hero" type="button" data-bugfire-action="pet" aria-label="和宠物互动">
          <span class="bugfire-dragon-wrap" data-bugfire-decoration>${petVisual()}</span>
          <span class="bugfire-terminal-status" data-bugfire-status>READY</span>
        </button>
        <div class="bugfire-stats">
          <div><strong data-bugfire-level-label>Lv2</strong><span data-bugfire-stage>会搭建</span></div>
          <div><small>当前技能</small><b data-bugfire-skill>结构嗅探</b></div>
        </div>
        <div class="bugfire-xp">
          <div><span>VIBE XP</span><strong data-bugfire-xp>220 / 240 XP</strong></div>
          <div class="bugfire-xp-track"><i data-bugfire-xp-fill></i></div>
        </div>
        <div class="bugfire-skills" data-bugfire-skills aria-label="已解锁技能"></div>
        <ul class="bugfire-quests" data-bugfire-quests aria-label="本地任务板"></ul>
        <pre class="bugfire-log" data-bugfire-log role="status" aria-live="polite">&gt; demo ready\n体验存档 · 不执行真实 Shell</pre>
        <button class="bugfire-build-button" type="button" data-bugfire-action="build">BUILD · 演示</button>
        <div class="bugfire-cabin-footer">
          <small data-bugfire-counts></small>
          <span>
            <button type="button" data-bugfire-action="certificate" hidden>证书</button>
            <button type="button" data-bugfire-action="reset">重置体验</button>
          </span>
        </div>
      </section>`;
    root.querySelector(".bugfire-cabin").inert = true;
    root.addEventListener("click", petClickHandler);
    document.body.appendChild(root);
    document.documentElement?.setAttribute("data-bugfire-mounted", "true");
    if (!keyboardAttached) {
      window.addEventListener("keydown", keyboardHandler);
      keyboardAttached = true;
    }
    renderProgress();
    setPetState(petState);
    return root;
  };

  const updatePetRoute = (route) => {
    const root = mountPet();
    if (!root) return;
    const resolved = route === "home" ? "home" : "task";
    root.setAttribute("data-bugfire-route", resolved);
    if (resolved === "task") {
      closePet();
      const composer = document.querySelector(".composer-surface-chrome");
      const composerBox = composer?.getBoundingClientRect();
      const fallbackBottom = Math.max(96, Math.min(innerHeight - 84, 112));
      const taskBottom = composerBox && composerBox.width > 0 && composerBox.height > 0
        ? Math.max(96, Math.min(innerHeight - 84, innerHeight - composerBox.top + 12))
        : fallbackBottom;
      root.style.setProperty("--bugfire-task-bottom", `${Math.round(taskBottom)}px`);
    } else {
      root.style.removeProperty("--bugfire-task-bottom");
    }
  };

  const destroyPet = () => {
    animationToken += 1;
    for (const timerId of petTimers) clearTimeout(timerId);
    petTimers.clear();
    window.removeEventListener("keydown", keyboardHandler);
    keyboardAttached = false;
    document.getElementById(PET_ID)?.remove();
    document.getElementById(GROWTH_CARD_ID)?.remove();
    document.getElementById(CERTIFICATE_ID)?.remove();
    document.documentElement?.removeAttribute("data-bugfire-mounted");
  };

  const petApi = {
    hydrate: hydrateProgress,
    open: openPet,
    close: closePet,
    renderCertificateDataUrl,
    cleanup: destroyPet,
  };

  const existingStyle = document.getElementById(STYLE_ID);
  if (existingStyle) {
    existingStyle.textContent = cssText;
    existingStyle.dataset.dreamSkinVersion = VERSION;
  }

  const ensure = () => {
    if (window[DISABLED_KEY]) return;
    const root = document.documentElement;
    if (!root) return;
    const shell = detectShellMode();
    root.classList.add("codex-dream-skin");
    root.setAttribute(SHELL_ATTR, shell);
    root.style.setProperty("--dream-skin-art", `url("${artUrl}")`);
    applyTheme(root, shell);

    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement("style");
      style.id = STYLE_ID;
      (document.head || root).appendChild(style);
    }
    if (style.dataset.dreamSkinVersion !== VERSION) {
      style.textContent = cssText;
      style.dataset.dreamSkinVersion = VERSION;
    }

    const shellMain = document.querySelector("main.main-surface") || document.querySelector("main");
    const isVisibleRouteNode = (candidate) => {
      if (!candidate || candidate.getAttribute("aria-hidden") === "true" ||
          candidate.closest('[aria-hidden="true"]')) return false;
      const style = getComputedStyle(candidate);
      return style.display !== "none" && style.visibility !== "hidden" &&
        candidate.getClientRects().length > 0;
    };
    const visibleGameSource = [...document.querySelectorAll('[data-feature="game-source"]')]
      .find(isVisibleRouteNode) || null;
    const visibleSuggestions = [...document.querySelectorAll('[class~="group/home-suggestions"]')]
      .find(isVisibleRouteNode) || null;
    const visibleHomeIcon = [...document.querySelectorAll('[data-testid="home-icon"]')]
      .find(isVisibleRouteNode) || null;
    const visibleHomeSignal = visibleGameSource || visibleSuggestions || visibleHomeIcon;
    const isHomeRoute = Boolean(visibleGameSource || visibleSuggestions || visibleHomeIcon);
    const indicatedHome = visibleHomeSignal?.closest('[role="main"], [class*="home-main-content"]') || null;
    const home = isHomeRoute && isVisibleRouteNode(indicatedHome) ? indicatedHome : null;
    for (const candidate of document.querySelectorAll('.dream-skin-home')) {
      if (candidate !== home) candidate.classList.remove("dream-skin-home");
    }
    if (home) home.classList.add("dream-skin-home");
    updatePetRoute(isHomeRoute ? "home" : "task");

    if (!shellMain || !document.body) return;
    shellMain.classList.toggle("dream-skin-home-shell", isHomeRoute);
    let chrome = document.getElementById(CHROME_ID);
    if (!chrome || chrome.parentElement !== document.body) {
      chrome?.remove();
      chrome = document.createElement("div");
      chrome.id = CHROME_ID;
      chrome.setAttribute("aria-hidden", "true");
      chrome.innerHTML = `
        <div class="dream-skin-brand">
          <span class="dream-skin-portal-mark">◉</span>
          <span><b></b><small></small></span>
        </div>
        <div class="dream-skin-status"><i></i><span></span></div>
        <div class="dream-skin-quote"></div>
        <div class="dream-skin-particles"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
        <div class="dream-skin-orbit"></div>`;
      document.body.appendChild(chrome);
    }
    chrome.querySelector(".dream-skin-brand b").textContent = THEME.name || "Codex Dream Skin";
    chrome.querySelector(".dream-skin-brand small").textContent = THEME.brandSubtitle || "CODEX DREAM SKIN";
    chrome.querySelector(".dream-skin-status span").textContent = THEME.statusText || "DREAM SKIN ONLINE";
    chrome.querySelector(".dream-skin-quote").textContent = THEME.quote || "MAKE SOMETHING WONDERFUL";
    const shellBox = shellMain.getBoundingClientRect();
    chrome.style.left = `${Math.round(shellBox.left)}px`;
    chrome.style.top = `${Math.round(shellBox.top)}px`;
    chrome.style.width = `${Math.round(shellBox.width)}px`;
    chrome.style.height = `${Math.round(shellBox.height)}px`;
    chrome.classList.toggle("dream-skin-home-shell", isHomeRoute);
    chrome.dataset.dreamShell = shell;
  };

  const cleanup = () => {
    window[DISABLED_KEY] = true;
    document.documentElement?.classList.remove("codex-dream-skin");
    document.documentElement?.removeAttribute(SHELL_ATTR);
    document.documentElement?.style.removeProperty("--dream-skin-art");
    for (const name of THEME_VARIABLES) document.documentElement?.style.removeProperty(name);
    document.querySelectorAll(".dream-skin-home").forEach((node) => node.classList.remove("dream-skin-home"));
    document.querySelectorAll(".dream-skin-home-shell").forEach((node) => node.classList.remove("dream-skin-home-shell"));
    document.getElementById(STYLE_ID)?.remove();
    document.getElementById(CHROME_ID)?.remove();
    animationToken += 1;
    for (const timerId of petTimers) clearTimeout(timerId);
    petTimers.clear();
    window.removeEventListener("keydown", keyboardHandler);
    keyboardAttached = false;
    document.getElementById(PET_ID)?.remove();
    document.getElementById(GROWTH_CARD_ID)?.remove();
    document.getElementById(CERTIFICATE_ID)?.remove();
    document.documentElement?.removeAttribute("data-bugfire-mounted");
    const state = window[STATE_KEY];
    state?.observer?.disconnect();
    if (state?.timer) clearInterval(state.timer);
    if (state?.scheduler?.timeout) clearTimeout(state.scheduler.timeout);
    if (state?.resizeHandler) window.removeEventListener("resize", state.resizeHandler);
    if (state?.mediaHandler && state?.mediaQuery) {
      try { state.mediaQuery.removeEventListener("change", state.mediaHandler); } catch {}
    }
    if (state?.artUrl) URL.revokeObjectURL(state.artUrl);
    delete window[STATE_KEY];
    return true;
  };

  const scheduler = { timeout: null };
  const scheduleEnsure = () => {
    if (scheduler.timeout) clearTimeout(scheduler.timeout);
    scheduler.timeout = setTimeout(() => {
      scheduler.timeout = null;
      ensure();
    }, 180);
  };
  const observer = new MutationObserver(scheduleEnsure);
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["class", "data-theme", "data-appearance", "data-color-mode", "style"],
  });
  const timer = setInterval(ensure, 4000);
  const resizeHandler = scheduleEnsure;
  window.addEventListener("resize", resizeHandler, { passive: true });

  let mediaQuery = null;
  let mediaHandler = null;
  try {
    mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaHandler = () => scheduleEnsure();
    mediaQuery.addEventListener("change", mediaHandler);
  } catch {}

  window[STATE_KEY] = {
    ensure,
    cleanup,
    observer,
    timer,
    scheduler,
    resizeHandler,
    mediaQuery,
    mediaHandler,
    artUrl,
    version: VERSION,
    themeId: THEME.id || "custom",
    detectShellMode,
    pet: petApi,
  };
  ensure();
  return { installed: true, version: VERSION, themeId: THEME.id || "custom", shell: detectShellMode() };
})(
  __DREAM_SKIN_CSS_JSON__,
  __DREAM_SKIN_ART_JSON__,
  __DREAM_SKIN_THEME_JSON__,
  __BUGFIRE_PROGRESS_JSON__,
  __BUGFIRE_ASSETS_JSON__,
)
