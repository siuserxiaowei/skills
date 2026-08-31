import fs from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const MAX_MANIFEST_BYTES = 128 * 1024;
const MAX_BACKGROUND_BYTES = 16 * 1024 * 1024;
const MAX_PET_ART_BYTES = 4 * 1024 * 1024;
const MAX_TOTAL_PET_ART_BYTES = 16 * 1024 * 1024;
const MAX_BACKGROUND_DIMENSION = 8_192;
const MAX_BACKGROUND_PIXELS = 32 * 1024 * 1024;
const MAX_PET_ART_DIMENSION = 4_096;
const MAX_PET_ART_PIXELS = 8 * 1024 * 1024;
const ART_STATES = Object.freeze(["idle", "building", "bug", "fire", "success", "levelUp"]);
const OPTIONAL_ART_STATES = Object.freeze(ART_STATES.slice(1));
const QUEST_METRICS = new Set(["repairedBuilds", "successfulBuilds", "failedBuilds", "xp", "level"]);
const DEFAULT_LEVELS = Object.freeze([
  Object.freeze({ level: 1, minXp: 0, stage: "会描述", skill: "灵感火星" }),
  Object.freeze({ level: 2, minXp: 100, stage: "会搭建", skill: "结构嗅探" }),
  Object.freeze({ level: 3, minXp: 240, stage: "会除虫", skill: "BUGFIRE" }),
  Object.freeze({ level: 4, minXp: 450, stage: "会验收", skill: "测试结界" }),
  Object.freeze({ level: 5, minXp: 750, stage: "会交付", skill: "发布跃迁" }),
]);

function invalid(message) {
  throw new TypeError(`Invalid Bugfire Pack: ${message}`);
}

function plainObject(value, name) {
  if (!value || typeof value !== "object" || Array.isArray(value)) invalid(`${name} must be an object`);
  return value;
}

function keys(value, allowed, name) {
  const unexpected = Object.keys(value).filter((key) => !allowed.includes(key));
  if (unexpected.length) invalid(`${name} has unsupported fields: ${unexpected.join(", ")}`);
}

function text(value, name, max, { optional = false } = {}) {
  if (optional && (value === undefined || value === null || value === "")) return "";
  if (typeof value !== "string" || !value.trim()) invalid(`${name} must be non-empty text`);
  const normalized = value.trim();
  if (normalized.length > max) invalid(`${name} exceeds the maximum length of ${max}`);
  if (/\p{C}/u.test(normalized)) invalid(`${name} contains control characters`);
  return normalized;
}

function identifier(value, name) {
  const normalized = text(value, name, 64);
  if (!/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/.test(normalized)) {
    invalid(`${name} must be a lowercase hyphen-case identifier`);
  }
  return normalized;
}

function color(value, name) {
  if (typeof value !== "string" || !/^#[0-9a-f]{6}$/i.test(value)) {
    invalid(`${name} must be a six-digit hex color`);
  }
  return value.toLowerCase();
}

function hexToRgba(hex, alpha) {
  const value = Number.parseInt(hex.slice(1), 16);
  return `rgba(${value >> 16}, ${(value >> 8) & 255}, ${value & 255}, ${alpha})`;
}

function positiveInteger(value, name, maximum) {
  if (!Number.isSafeInteger(value) || value < 1 || value > maximum) {
    invalid(`${name} must be an integer from 1 to ${maximum}`);
  }
  return value;
}

function relativeAssetPath(value, name) {
  const normalized = text(value, name, 240);
  if (normalized.includes("\\") || path.posix.isAbsolute(normalized) ||
      normalized !== path.posix.normalize(normalized) || normalized.startsWith("../") ||
      !normalized.startsWith("assets/")) {
    invalid(`${name} must be a normalized relative path inside assets/`);
  }
  if (!/\.(?:png|jpe?g|webp)$/i.test(normalized)) {
    invalid(`${name} must reference PNG, JPEG, or WebP art`);
  }
  return normalized;
}

function isInside(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative !== "" && relative !== ".." && !relative.startsWith(`..${path.sep}`) &&
    !path.isAbsolute(relative);
}

function sameStableStat(before, after) {
  return before.dev === after.dev && before.ino === after.ino && before.size === after.size &&
    before.mtimeNs === after.mtimeNs && before.ctimeNs === after.ctimeNs;
}

async function readStableFile(file, name, maximum, { missing } = {}) {
  let entry;
  try {
    entry = await fs.lstat(file, { bigint: true });
  } catch (error) {
    if (error?.code === "ENOENT" && missing) invalid(missing);
    throw error;
  }
  if (!entry.isFile() || entry.isSymbolicLink()) invalid(`${name} must be a regular file, not a link`);

  let handle;
  try {
    handle = await fs.open(file, fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW);
  } catch (error) {
    if (error?.code === "ELOOP") invalid(`${name} must be a regular file, not a link`);
    if (error?.code === "ENOENT" && missing) invalid(missing);
    throw error;
  }
  try {
    const before = await handle.stat({ bigint: true });
    if (!sameStableStat(entry, before)) invalid(`${name} changed before it could be read`);
    if (!before.isFile() || before.size < 1n || before.size > BigInt(maximum)) {
      invalid(`${name} has an invalid file size`);
    }
    const content = await handle.readFile();
    const after = await handle.stat({ bigint: true });
    if (!sameStableStat(before, after) || BigInt(content.length) !== before.size) {
      invalid(`${name} changed while it was being read`);
    }
    return { content, bytes: content.length, stat: before };
  } finally {
    await handle.close();
  }
}

function imageDimensions(content, name) {
  const pngSignature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  if (content.length >= 8 && content.subarray(0, 8).equals(pngSignature)) {
    let offset = 8;
    let width = 0;
    let height = 0;
    let sawHeader = false;
    let sawEnd = false;
    while (offset + 12 <= content.length) {
      const chunkBytes = content.readUInt32BE(offset);
      const type = content.subarray(offset + 4, offset + 8).toString("ascii");
      const dataOffset = offset + 8;
      const next = dataOffset + chunkBytes + 4;
      if (next > content.length) invalid(`${name} contains a truncated PNG chunk`);
      if (!sawHeader) {
        if (type !== "IHDR" || chunkBytes !== 13) invalid(`${name} has an invalid PNG header`);
        width = content.readUInt32BE(dataOffset);
        height = content.readUInt32BE(dataOffset + 4);
        sawHeader = true;
      }
      if (type === "acTL") invalid(`${name} must not be an animated PNG`);
      if (type === "IEND") {
        sawEnd = true;
        break;
      }
      offset = next;
    }
    if (!sawHeader || !sawEnd) invalid(`${name} is not a complete PNG image`);
    return { format: "png", width, height };
  }

  if (content.length >= 3 && content[0] === 0xff && content[1] === 0xd8 && content[2] === 0xff) {
    const startOfFrame = new Set([
      0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7,
      0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf,
    ]);
    let offset = 2;
    while (offset < content.length) {
      while (offset < content.length && content[offset] !== 0xff) offset += 1;
      while (offset < content.length && content[offset] === 0xff) offset += 1;
      if (offset >= content.length) break;
      const marker = content[offset];
      offset += 1;
      if (marker === 0x00 || marker === 0xd8 || marker === 0xd9 || marker === 0x01 ||
          (marker >= 0xd0 && marker <= 0xd7)) continue;
      if (offset + 2 > content.length) invalid(`${name} contains a truncated JPEG segment`);
      const segmentBytes = content.readUInt16BE(offset);
      if (segmentBytes < 2 || offset + segmentBytes > content.length) {
        invalid(`${name} contains an invalid JPEG segment`);
      }
      if (startOfFrame.has(marker)) {
        if (segmentBytes < 8) invalid(`${name} has an invalid JPEG frame`);
        return {
          format: "jpeg",
          width: content.readUInt16BE(offset + 5),
          height: content.readUInt16BE(offset + 3),
        };
      }
      if (marker === 0xda) break;
      offset += segmentBytes;
    }
    invalid(`${name} has no readable JPEG frame`);
  }

  if (content.length >= 12 && content.subarray(0, 4).toString("ascii") === "RIFF" &&
      content.subarray(8, 12).toString("ascii") === "WEBP") {
    const riffEnd = content.readUInt32LE(4) + 8;
    if (riffEnd < 12 || riffEnd > content.length) invalid(`${name} has an invalid WebP container`);
    let offset = 12;
    let canvasWidth = 0;
    let canvasHeight = 0;
    let frameWidth = 0;
    let frameHeight = 0;
    let sawExtendedHeader = false;
    let sawFrame = false;
    while (offset + 8 <= riffEnd) {
      const type = content.subarray(offset, offset + 4).toString("ascii");
      const chunkBytes = content.readUInt32LE(offset + 4);
      const dataOffset = offset + 8;
      const dataEnd = dataOffset + chunkBytes;
      const next = dataEnd + (chunkBytes & 1);
      if (dataEnd > riffEnd || next > riffEnd) invalid(`${name} contains a truncated WebP chunk`);
      if (type === "ANIM" || type === "ANMF") invalid(`${name} must not be an animated WebP`);
      if (type === "VP8X") {
        if (sawExtendedHeader) invalid(`${name} has multiple WebP extended headers`);
        if (chunkBytes < 10) invalid(`${name} has an invalid WebP extended header`);
        if (content[dataOffset] & 0x02) invalid(`${name} must not be an animated WebP`);
        canvasWidth = 1 + content.readUIntLE(dataOffset + 4, 3);
        canvasHeight = 1 + content.readUIntLE(dataOffset + 7, 3);
        sawExtendedHeader = true;
      } else if (type === "VP8L") {
        if (chunkBytes < 5 || content[dataOffset] !== 0x2f) invalid(`${name} has an invalid lossless WebP frame`);
        if (sawFrame) invalid(`${name} has multiple WebP image frames`);
        const bits = content.readUInt32LE(dataOffset + 1);
        frameWidth = 1 + (bits & 0x3fff);
        frameHeight = 1 + ((bits >>> 14) & 0x3fff);
        sawFrame = true;
      } else if (type === "VP8 ") {
        if (chunkBytes < 10 || content[dataOffset + 3] !== 0x9d ||
            content[dataOffset + 4] !== 0x01 || content[dataOffset + 5] !== 0x2a) {
          invalid(`${name} has an invalid lossy WebP frame`);
        }
        if (sawFrame) invalid(`${name} has multiple WebP image frames`);
        frameWidth = content.readUInt16LE(dataOffset + 6) & 0x3fff;
        frameHeight = content.readUInt16LE(dataOffset + 8) & 0x3fff;
        sawFrame = true;
      }
      offset = next;
    }
    if (!frameWidth || !frameHeight || !sawFrame) invalid(`${name} has no readable WebP frame`);
    if (sawExtendedHeader && (canvasWidth !== frameWidth || canvasHeight !== frameHeight)) {
      invalid(`${name} WebP canvas dimensions do not match its image frame`);
    }
    return { format: "webp", width: frameWidth, height: frameHeight };
  }

  invalid(`${name} content is not a supported image`);
}

function validateImage(content, relative, name, { maximumDimension, maximumPixels }) {
  const image = imageDimensions(content, name);
  const extension = path.extname(relative).toLowerCase();
  const declaredFormat = extension === ".png" ? "png" :
    extension === ".jpg" || extension === ".jpeg" ? "jpeg" :
      extension === ".webp" ? "webp" : "";
  if (image.format !== declaredFormat) invalid(`${name} extension does not match its image content`);
  if (!Number.isSafeInteger(image.width) || !Number.isSafeInteger(image.height) ||
      image.width < 1 || image.height < 1 || image.width > maximumDimension ||
      image.height > maximumDimension || image.width * image.height > maximumPixels) {
    invalid(`${name} exceeds the allowed image dimensions or pixel count`);
  }
  return image;
}

async function imageFile(root, relative, name, limits) {
  const resolved = path.resolve(root, relative);
  if (!isInside(root, resolved)) invalid(`${name} must stay inside the pack`);
  let entry;
  try {
    entry = await fs.lstat(resolved, { bigint: true });
  } catch (error) {
    if (error?.code === "ENOENT") invalid(`${name} is missing: ${relative}`);
    throw error;
  }
  if (!entry.isFile() || entry.isSymbolicLink()) invalid(`${name} must be a regular file, not a link`);

  const canonical = await fs.realpath(resolved);
  if (!isInside(root, canonical)) invalid(`${name} must stay inside the pack, including linked parent directories`);
  const loaded = await readStableFile(canonical, name, limits.maximumBytes);
  const entryAfterRead = await fs.lstat(resolved, { bigint: true }).catch(() => null);
  const canonicalAfterRead = await fs.realpath(resolved).catch(() => "");
  if (!entryAfterRead || entryAfterRead.isSymbolicLink() || !entryAfterRead.isFile() ||
      !sameStableStat(entry, loaded.stat) || !sameStableStat(loaded.stat, entryAfterRead) ||
      canonicalAfterRead !== canonical || !isInside(root, canonicalAfterRead)) {
    invalid(`${name} changed location while it was being read`);
  }
  const image = validateImage(loaded.content, relative, name, limits);
  return { absolute: canonical, bytes: loaded.bytes, relative, content: loaded.content, image };
}

function validateManifestShape(raw) {
  const manifest = plainObject(raw, "manifest");
  keys(manifest, ["schemaVersion", "id", "name", "theme", "pet", "gameplay", "rights"], "manifest");
  if (manifest.schemaVersion !== 1) invalid("schemaVersion must be 1");

  const theme = plainObject(manifest.theme, "theme");
  keys(theme, ["background", "tagline", "quote", "colors"], "theme");
  const colors = plainObject(theme.colors, "theme.colors");
  keys(colors, ["background", "panel", "panelAlt", "accent", "accentAlt", "secondary", "highlight", "text", "muted"], "theme.colors");

  const pet = plainObject(manifest.pet, "pet");
  keys(pet, ["name", "seasonId", "seasonLabel", "art"], "pet");
  const art = plainObject(pet.art, "pet.art");
  keys(art, ART_STATES, "pet.art");
  if (typeof art.idle !== "string" || !art.idle.trim()) invalid("pet.art.idle is required");

  const gameplay = plainObject(manifest.gameplay, "gameplay");
  keys(gameplay, ["rewardXp", "sayings", "quests", "certificateTitle"], "gameplay");
  if (!Array.isArray(gameplay.sayings) || gameplay.sayings.length < 1 || gameplay.sayings.length > 12) {
    invalid("gameplay.sayings must contain 1 to 12 entries");
  }
  if (!Array.isArray(gameplay.quests) || gameplay.quests.length < 1 || gameplay.quests.length > 5) {
    invalid("gameplay.quests must contain 1 to 5 entries");
  }
  const questIds = new Set();
  const quests = gameplay.quests.map((quest, index) => {
    plainObject(quest, `gameplay.quests[${index}]`);
    keys(quest, ["id", "title", "metric", "target"], `gameplay.quests[${index}]`);
    const id = identifier(quest.id, `gameplay.quests[${index}].id`);
    if (questIds.has(id)) invalid("quest identifiers must be unique");
    questIds.add(id);
    if (!QUEST_METRICS.has(quest.metric)) invalid(`unsupported quest metric: ${quest.metric}`);
    return {
      id,
      title: text(quest.title, `gameplay.quests[${index}].title`, 40),
      metric: quest.metric,
      target: positiveInteger(quest.target, `gameplay.quests[${index}].target`, 100_000),
    };
  });

  const rights = plainObject(manifest.rights, "rights");
  keys(rights, ["declaration", "sourceUrl"], "rights");
  const sourceUrl = text(rights.sourceUrl, "rights.sourceUrl", 500, { optional: true });
  if (sourceUrl && !/^https:\/\//i.test(sourceUrl)) invalid("rights.sourceUrl must use HTTPS");

  return {
    schemaVersion: 1,
    id: identifier(manifest.id, "id"),
    name: text(manifest.name, "name", 80),
    theme: {
      background: relativeAssetPath(theme.background, "theme.background"),
      tagline: text(theme.tagline, "theme.tagline", 160),
      quote: text(theme.quote, "theme.quote", 80),
      colors: {
        background: color(colors.background, "theme.colors.background"),
        panel: color(colors.panel, "theme.colors.panel"),
        panelAlt: color(colors.panelAlt, "theme.colors.panelAlt"),
        accent: color(colors.accent, "theme.colors.accent"),
        accentAlt: color(colors.accentAlt, "theme.colors.accentAlt"),
        secondary: color(colors.secondary, "theme.colors.secondary"),
        highlight: color(colors.highlight, "theme.colors.highlight"),
        text: color(colors.text, "theme.colors.text"),
        muted: color(colors.muted, "theme.colors.muted"),
      },
    },
    pet: {
      name: text(pet.name, "pet.name", 80),
      seasonId: identifier(pet.seasonId, "pet.seasonId"),
      seasonLabel: text(pet.seasonLabel, "pet.seasonLabel", 80),
      art: Object.fromEntries(Object.entries(art).map(([state, asset]) => [
        state, relativeAssetPath(asset, `pet.art.${state}`),
      ])),
    },
    gameplay: {
      rewardXp: positiveInteger(gameplay.rewardXp, "gameplay.rewardXp", 100),
      sayings: gameplay.sayings.map((saying, index) => text(saying, `gameplay.sayings[${index}]`, 80)),
      quests,
      certificateTitle: text(gameplay.certificateTitle, "gameplay.certificateTitle", 80),
    },
    rights: {
      declaration: text(rights.declaration, "rights.declaration", 240),
      sourceUrl,
    },
  };
}

// The AI director produces a proposal, but this existing deterministic contract
// remains the only authority that can turn that proposal into an installable pack.
export { validateManifestShape as validateBugfireManifest };

async function readManifest(packRoot) {
  const manifestPath = path.join(packRoot, "bugfire-pack.json");
  const loaded = await readStableFile(manifestPath, "manifest", MAX_MANIFEST_BYTES, {
    missing: `manifest is missing: ${manifestPath}`,
  });
  if (loaded.bytes < 2) invalid("manifest has an invalid file size");
  try {
    return JSON.parse(loaded.content.toString("utf8"));
  } catch (error) {
    if (error instanceof SyntaxError) invalid(`manifest is not valid JSON: ${error.message}`);
    throw error;
  }
}

export function createStarterManifest() {
  return {
    schemaVersion: 1,
    id: "my-codex-companion",
    name: "我的 Codex 伙伴",
    theme: {
      background: "assets/background.png",
      tagline: "每一次 Build，都让作品和伙伴一起进化。",
      quote: "BUILD · FIX · LEARN · SHIP",
      colors: {
        background: "#050704",
        panel: "#0a0e09",
        panelAlt: "#11180e",
        accent: "#83ff45",
        accentAlt: "#c1ff72",
        secondary: "#ff7a1a",
        highlight: "#ff3d0a",
        text: "#f4efd8",
        muted: "#9aa58d",
      },
    },
    pet: {
      name: "我的补丁伙伴",
      seasonId: "season-1",
      seasonLabel: "SEASON 01 · BUILD TO EVOLVE",
      art: { idle: "assets/pet-idle.png" },
    },
    gameplay: {
      rewardXp: 35,
      sayings: ["今天也一起把 Bug 烧掉。", "先描述清楚，再动手构建。", "修复不是倒退，是进化素材。"],
      quests: [
        { id: "first-fix", title: "完成第一次修复重建", metric: "repairedBuilds", target: 1 },
        { id: "build-streak", title: "累计完成 3 次 Build", metric: "successfulBuilds", target: 3 },
        { id: "level-three", title: "成长到 Lv3", metric: "level", target: 3 },
      ],
      certificateTitle: "我的 Codex 成长纪念",
    },
    rights: {
      declaration: "我确认拥有这些素材的使用权，或素材许可允许本次使用。",
      sourceUrl: "",
    },
  };
}

export async function validateBugfirePack(packDirectory) {
  const requestedRoot = path.resolve(packDirectory);
  const root = await fs.realpath(requestedRoot).catch((error) => {
    if (error?.code === "ENOENT") invalid(`pack directory is missing: ${requestedRoot}`);
    throw error;
  });
  const rootStat = await fs.stat(root);
  if (!rootStat.isDirectory()) invalid(`pack root must be a directory: ${requestedRoot}`);
  const manifest = validateManifestShape(await readManifest(root));
  const background = await imageFile(root, manifest.theme.background, "theme.background", {
    maximumBytes: MAX_BACKGROUND_BYTES,
    maximumDimension: MAX_BACKGROUND_DIMENSION,
    maximumPixels: MAX_BACKGROUND_PIXELS,
  });
  const petFiles = {};
  let totalPetBytes = 0;
  for (const [state, relative] of Object.entries(manifest.pet.art)) {
    const file = await imageFile(root, relative, `pet.art.${state}`, {
      maximumBytes: MAX_PET_ART_BYTES,
      maximumDimension: MAX_PET_ART_DIMENSION,
      maximumPixels: MAX_PET_ART_PIXELS,
    });
    petFiles[state] = file;
    totalPetBytes += file.bytes;
  }
  if (totalPetBytes > MAX_TOTAL_PET_ART_BYTES) invalid("pet art exceeds the total size limit");

  return {
    pass: true,
    packRoot: root,
    manifest,
    background,
    petFiles,
    requiredUploads: [manifest.theme.background, manifest.pet.art.idle],
    optionalUploads: OPTIONAL_ART_STATES.filter((state) => manifest.pet.art[state])
      .map((state) => manifest.pet.art[state]),
    totalBytes: background.bytes + totalPetBytes,
  };
}

function extensionFor(file) {
  return path.extname(file.relative).toLowerCase().replace(".jpeg", ".jpg");
}

async function atomicWrite(file, value) {
  const temporary = `${file}.${process.pid}.tmp`;
  try {
    await fs.writeFile(temporary, value, { mode: 0o600 });
    await fs.rename(temporary, file);
    await fs.chmod(file, 0o600);
  } finally {
    await fs.rm(temporary, { force: true }).catch(() => {});
  }
}

function pathsOverlap(first, second) {
  const relative = path.relative(first, second);
  const reverse = path.relative(second, first);
  const descends = (value) => value === "" ||
    (value !== ".." && !value.startsWith(`..${path.sep}`) && !path.isAbsolute(value));
  return descends(relative) || descends(reverse);
}

async function canonicalComparisonPath(target) {
  let cursor = path.resolve(target);
  const suffix = [];
  while (true) {
    try {
      const canonical = await fs.realpath(cursor);
      return path.resolve(canonical, ...suffix);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
      const parent = path.dirname(cursor);
      if (parent === cursor) throw error;
      suffix.unshift(path.basename(cursor));
      cursor = parent;
    }
  }
}

export async function buildBugfirePack(packDirectory, outputDirectory, options = {}) {
  const sourceInput = path.resolve(packDirectory);
  const output = path.resolve(outputDirectory);
  const sourceCanonical = await fs.realpath(sourceInput);
  const outputCanonical = await canonicalComparisonPath(output);
  if (pathsOverlap(sourceInput, output) || pathsOverlap(sourceCanonical, outputCanonical)) {
    throw new Error("Source and output directories must not be the same or overlap");
  }
  const validated = await validateBugfirePack(sourceInput);
  const parent = path.dirname(output);
  const existing = await fs.readdir(output).catch((error) => {
    if (error?.code === "ENOENT") return null;
    throw error;
  });
  if (existing?.length && !options.replace) {
    throw new Error(`Output directory is non-empty; pass replace explicitly: ${output}`);
  }

  await fs.mkdir(parent, { recursive: true, mode: 0o700 });
  const temporary = `${output}.building.${process.pid}`;
  await fs.rm(temporary, { recursive: true, force: true });
  await fs.mkdir(temporary, { mode: 0o700 });
  try {
    const backgroundName = `background${extensionFor(validated.background)}`;
    await fs.writeFile(path.join(temporary, backgroundName), validated.background.content, { mode: 0o600 });
    await fs.chmod(path.join(temporary, backgroundName), 0o600);

    const art = {};
    for (const state of ART_STATES) {
      if (state !== "idle" && !validated.petFiles[state]) {
        art[state] = art.idle;
        continue;
      }
      const source = validated.petFiles[state];
      const outputName = state === "levelUp"
        ? `pet-level-up${extensionFor(source)}`
        : `pet-${state}${extensionFor(source)}`;
      if (!art[state] || !(await fs.stat(path.join(temporary, outputName)).catch(() => null))) {
        await fs.writeFile(path.join(temporary, outputName), source.content, { mode: 0o600 });
        await fs.chmod(path.join(temporary, outputName), 0o600);
      }
      art[state] = outputName;
    }

    const manifest = validated.manifest;
    const theme = {
      schemaVersion: 1,
      id: manifest.id,
      name: manifest.name,
      brandSubtitle: manifest.pet.seasonLabel,
      tagline: manifest.theme.tagline,
      projectPrefix: "载入项目 · ",
      projectLabel: "▸  选择构建项目",
      statusText: `${manifest.pet.name} ONLINE`,
      quote: manifest.theme.quote,
      image: backgroundName,
      colors: {
        ...manifest.theme.colors,
        line: hexToRgba(manifest.theme.colors.accent, 0.26),
      },
      pet: {
        id: manifest.id,
        name: manifest.pet.name,
        season: manifest.pet.seasonId,
        seasonLabel: manifest.pet.seasonLabel,
        demoReward: manifest.gameplay.rewardXp,
        levels: DEFAULT_LEVELS.map((level) => ({ ...level })),
        art,
        sayings: manifest.gameplay.sayings,
        quests: manifest.gameplay.quests,
        certificateTitle: manifest.gameplay.certificateTitle,
      },
      rights: manifest.rights,
    };
    const report = {
      pass: true,
      schemaVersion: 1,
      packId: manifest.id,
      packName: manifest.name,
      requiredUploads: validated.requiredUploads,
      optionalUploads: validated.optionalUploads,
      compiledAt: new Date().toISOString(),
    };
    await atomicWrite(path.join(temporary, "theme.json"), `${JSON.stringify(theme, null, 2)}\n`);
    await atomicWrite(path.join(temporary, "pack-report.json"), `${JSON.stringify(report, null, 2)}\n`);

    if (existing !== null) await fs.rm(output, { recursive: true, force: true });
    await fs.rename(temporary, output);
    return { ...report, output };
  } catch (error) {
    await fs.rm(temporary, { recursive: true, force: true });
    throw error;
  }
}

async function initialize(directory) {
  const root = path.resolve(directory);
  const existing = await fs.readdir(root).catch((error) => {
    if (error?.code === "ENOENT") return null;
    throw error;
  });
  if (existing?.length) throw new Error(`Starter directory is non-empty: ${root}`);
  await fs.mkdir(path.join(root, "assets"), { recursive: true, mode: 0o700 });
  await atomicWrite(
    path.join(root, "bugfire-pack.json"),
    `${JSON.stringify(createStarterManifest(), null, 2)}\n`,
  );
  return {
    pass: true,
    output: root,
    next: ["Upload assets/background.png", "Upload assets/pet-idle.png", "Edit bugfire-pack.json"],
  };
}

async function cli(argv) {
  const [command, first, second, ...rest] = argv;
  if (command === "init" && first && !second) return initialize(first);
  if (command === "validate" && first && !second) {
    const result = await validateBugfirePack(first);
    return {
      pass: result.pass,
      packId: result.manifest.id,
      packName: result.manifest.name,
      requiredUploads: result.requiredUploads,
      optionalUploads: result.optionalUploads,
      totalBytes: result.totalBytes,
    };
  }
  if (command === "build" && first && second) {
    const unexpected = rest.filter((arg) => arg !== "--replace");
    if (unexpected.length) throw new Error(`Unknown build arguments: ${unexpected.join(", ")}`);
    return buildBugfirePack(first, second, { replace: rest.includes("--replace") });
  }
  throw new Error(
    "Usage: bugfire-pack.mjs init <dir> | validate <dir> | build <source-dir> <output-dir> [--replace]",
  );
}

const modulePath = await fs.realpath(fileURLToPath(import.meta.url)).catch(() => path.resolve(fileURLToPath(import.meta.url)));
const entryPath = process.argv[1]
  ? await fs.realpath(process.argv[1]).catch(() => path.resolve(process.argv[1]))
  : "";
const isEntrypoint = Boolean(entryPath) && entryPath === modulePath;
if (isEntrypoint) {
  cli(process.argv.slice(2)).then((result) => {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  }).catch((error) => {
    process.stderr.write(`[bugfire-pack] ${error.message}\n`);
    process.exitCode = 1;
  });
}
