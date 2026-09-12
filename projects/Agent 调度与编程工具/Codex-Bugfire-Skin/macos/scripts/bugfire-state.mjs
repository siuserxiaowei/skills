import fs from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { spawn } from "node:child_process";
import path from "node:path";

const SCHEMA_VERSION = 1;
const SEED_XP = 220;
const MAX_IDENTIFIER_LENGTH = 120;
const MAX_CARD_ID_LENGTH = 256;
const MAX_SETTLED_EVENT_IDS = 256;
const MAX_PROGRESS_FILE_BYTES = 1024 * 1024;
const LOCK_WAIT_MS = 5_000;
const LOCKF_PATH = "/usr/bin/lockf";
const SEASON_DISCLAIMER = "个人成长纪念卡，由本地活动生成；非官方认证，不代表专业资格。";
const PROGRESS_KEYS = [
  "cards",
  "failedBuilds",
  "petId",
  "repairedBuilds",
  "schemaVersion",
  "seasonId",
  "settledEventIds",
  "successfulBuilds",
  "unlockedSkills",
  "updatedAt",
  "xp",
];

export const LEVELS = Object.freeze([
  Object.freeze({ level: 1, minXp: 0, stage: "会描述", skill: "灵感火星" }),
  Object.freeze({ level: 2, minXp: 100, stage: "会搭建", skill: "结构嗅探" }),
  Object.freeze({ level: 3, minXp: 240, stage: "会除虫", skill: "BUGFIRE" }),
  Object.freeze({ level: 4, minXp: 450, stage: "会验收", skill: "测试结界" }),
  Object.freeze({ level: 5, minXp: 750, stage: "会交付", skill: "发布跃迁" }),
]);

// Four level-up cards (Lv2–Lv5) plus one season certificate.
const MAX_CARDS = LEVELS.length;
const LEVEL_CARD_KEYS = ["earnedAt", "id", "kind", "level", "skill", "stage"];
const SEASON_CARD_KEYS = [
  "disclaimer", "earnedAt", "id", "kind", "petId", "seasonId", "title",
];

export const SEASON_CERTIFICATE_DISCLAIMER = SEASON_DISCLAIMER;

function invalid(message) {
  throw new TypeError(`Invalid progress: ${message}`);
}

function isPlainObject(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function validTimestamp(value) {
  if (typeof value !== "string") return false;
  try {
    return new Date(value).toISOString() === value;
  } catch {
    return false;
  }
}

function timestamp(value) {
  const resolved = value ?? new Date().toISOString();
  if (!validTimestamp(resolved)) invalid("updatedAt must be an ISO timestamp");
  return resolved;
}

function identifier(value, name, maxLength = MAX_IDENTIFIER_LENGTH) {
  if (typeof value !== "string" || !value.trim() || value.length > maxLength) {
    invalid(`${name} must be a non-empty string`);
  }
  return value;
}

function nonNegativeInteger(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) invalid(`${name} must be a non-negative integer`);
}

function unlockedSkillsForXp(xp) {
  return LEVELS.filter((entry) => entry.minXp <= xp).map((entry) => entry.skill);
}

function sameStrings(left, right) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function hasExactKeys(value, expected) {
  return sameStrings(Object.keys(value).sort(), expected);
}

function validateCard(card, progress) {
  if (!isPlainObject(card)) invalid("cards must contain objects");
  identifier(card.id, "card id", MAX_CARD_ID_LENGTH);
  if (!validTimestamp(card.earnedAt)) invalid("card earnedAt must be an ISO timestamp");

  if (card.kind === "level") {
    if (!hasExactKeys(card, LEVEL_CARD_KEYS)) invalid("level card schema is invalid");
    const level = LEVELS.find((entry) => entry.level === card.level);
    if (!level || level.level < 2 || level.minXp > progress.xp ||
        level.stage !== card.stage || level.skill !== card.skill) {
      invalid("level card does not match the level table");
    }
    return;
  }
  if (card.kind === "season") {
    if (!hasExactKeys(card, SEASON_CARD_KEYS)) invalid("season card schema is invalid");
    if (card.petId !== progress.petId || card.seasonId !== progress.seasonId ||
        card.title !== "BUGFIRE 赛季证书" || card.disclaimer !== SEASON_DISCLAIMER ||
        levelForXp(progress.xp).level !== 5 || progress.successfulBuilds < 10 ||
        progress.repairedBuilds < 3) {
      invalid("season card does not match this progress record");
    }
    return;
  }
  invalid("card kind is unsupported");
}

export function levelForXp(xp) {
  if (!Number.isSafeInteger(xp) || xp < 0) throw new RangeError("XP must be a non-negative integer");
  for (let index = LEVELS.length - 1; index >= 0; index -= 1) {
    if (xp >= LEVELS[index].minXp) return LEVELS[index];
  }
  return LEVELS[0];
}

export function validateProgress(value) {
  if (!isPlainObject(value)) invalid("record must be an object");
  const keys = Object.keys(value).sort();
  if (!sameStrings(keys, PROGRESS_KEYS)) invalid("schema fields do not match version 1");
  if (value.schemaVersion !== SCHEMA_VERSION) invalid("schemaVersion is unsupported");
  identifier(value.petId, "petId");
  identifier(value.seasonId, "seasonId");
  nonNegativeInteger(value.xp, "xp");
  nonNegativeInteger(value.failedBuilds, "failedBuilds");
  nonNegativeInteger(value.successfulBuilds, "successfulBuilds");
  nonNegativeInteger(value.repairedBuilds, "repairedBuilds");
  if (value.repairedBuilds > value.successfulBuilds || value.repairedBuilds > value.failedBuilds) {
    invalid("repairedBuilds cannot exceed successfulBuilds or failedBuilds");
  }
  if (!Array.isArray(value.unlockedSkills) ||
      !sameStrings(value.unlockedSkills, unlockedSkillsForXp(value.xp))) {
    invalid("unlockedSkills do not match xp");
  }
  if (!Array.isArray(value.cards) || value.cards.length > MAX_CARDS) {
    invalid("cards must be a bounded array");
  }
  value.cards.forEach((card) => validateCard(card, value));
  const cardIds = value.cards.map((card) => card.id);
  if (new Set(cardIds).size !== cardIds.length) invalid("card ids must be unique");
  const levelCards = value.cards.filter((card) => card.kind === "level");
  const cardLevels = levelCards.map((card) => card.level);
  if (new Set(cardLevels).size !== cardLevels.length) invalid("level cards must be unique");
  if (value.cards.filter((card) => card.kind === "season").length > 1) {
    invalid("season card must be unique");
  }
  if (!Array.isArray(value.settledEventIds) ||
      value.settledEventIds.length > MAX_SETTLED_EVENT_IDS ||
      value.settledEventIds.some((eventId) =>
        typeof eventId !== "string" || !eventId || eventId.length > MAX_IDENTIFIER_LENGTH)) {
    invalid("settledEventIds must contain non-empty strings");
  }
  if (new Set(value.settledEventIds).size !== value.settledEventIds.length) {
    invalid("settledEventIds must be unique");
  }
  if (!validTimestamp(value.updatedAt)) invalid("updatedAt must be an ISO timestamp");
  return structuredClone(value);
}

function baseProgress({ petId, seasonId, now, xp }) {
  const progress = {
    schemaVersion: SCHEMA_VERSION,
    petId: identifier(petId, "petId"),
    seasonId: identifier(seasonId, "seasonId"),
    xp,
    failedBuilds: 0,
    successfulBuilds: 0,
    repairedBuilds: 0,
    unlockedSkills: unlockedSkillsForXp(xp),
    cards: [],
    settledEventIds: [],
    updatedAt: timestamp(now),
  };
  return validateProgress(progress);
}

export function createSeedProgress(options = {}) {
  return baseProgress({ ...options, xp: SEED_XP });
}

export function resetProgress(options = {}) {
  return baseProgress({ ...options, xp: 0 });
}

function levelCard(entry, eventId, earnedAt) {
  return {
    id: `level-${entry.level}-${eventId}`,
    kind: "level",
    level: entry.level,
    stage: entry.stage,
    skill: entry.skill,
    earnedAt,
  };
}

function seasonCard(progress, eventId, earnedAt) {
  return {
    id: `season-${progress.seasonId}-${eventId}`,
    kind: "season",
    petId: progress.petId,
    seasonId: progress.seasonId,
    title: "BUGFIRE 赛季证书",
    disclaimer: SEASON_DISCLAIMER,
    earnedAt,
  };
}

export function settleBuild(current, event) {
  const progress = validateProgress(current);
  if (!isPlainObject(event)) invalid("settlement event must be an object");
  const eventId = identifier(event.eventId, "eventId");
  if (progress.settledEventIds.includes(eventId)) {
    return { progress, awardedXp: 0, duplicate: true, levelUp: null, card: null };
  }
  if (!new Set(["failed", "success", "repair-success"]).has(event.outcome)) {
    invalid("settlement outcome is unsupported");
  }
  const earnedAt = timestamp(event.now);
  const requestedReward = event.rewardXp ?? 0;
  nonNegativeInteger(requestedReward, "rewardXp");
  const awardedXp = event.outcome === "failed" ? 0 : requestedReward;
  const previousLevel = levelForXp(progress.xp);
  const next = {
    ...progress,
    xp: progress.xp + awardedXp,
    failedBuilds: progress.failedBuilds + (event.outcome === "failed" ? 1 : 0),
    successfulBuilds: progress.successfulBuilds + (event.outcome === "failed" ? 0 : 1),
    repairedBuilds: progress.repairedBuilds + (event.outcome === "repair-success" ? 1 : 0),
    settledEventIds: [...progress.settledEventIds, eventId].slice(-MAX_SETTLED_EVENT_IDS),
    updatedAt: earnedAt,
  };
  const nextLevel = levelForXp(next.xp);
  next.unlockedSkills = unlockedSkillsForXp(next.xp);
  const newLevelCards = LEVELS
    .filter((entry) => entry.level > previousLevel.level && entry.level <= nextLevel.level)
    .map((entry) => levelCard(entry, eventId, earnedAt));
  next.cards = [...progress.cards, ...newLevelCards];

  const alreadyCertified = next.cards.some((card) => card.kind === "season");
  if (nextLevel.level === 5 && next.successfulBuilds >= 10 && next.repairedBuilds >= 3 &&
      !alreadyCertified) {
    next.cards.push(seasonCard(next, eventId, earnedAt));
  }

  const validated = validateProgress(next);
  return {
    progress: validated,
    awardedXp,
    duplicate: false,
    levelUp: nextLevel.level === previousLevel.level
      ? null
      : { from: previousLevel.level, to: nextLevel.level },
    card: newLevelCards[0] ?? null,
  };
}

export async function loadProgress(filePath, options = {}) {
  let fileStat;
  try {
    fileStat = await fs.stat(filePath);
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
    return createSeedProgress(options);
  }
  if (!fileStat.isFile() || fileStat.size > MAX_PROGRESS_FILE_BYTES) {
    await quarantineProgress(filePath, "corrupt");
    return createSeedProgress(options);
  }

  let source;
  try {
    source = await fs.readFile(filePath, "utf8");
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
    return createSeedProgress(options);
  }

  try {
    const progress = validateProgress(JSON.parse(source));
    if ((options.petId && progress.petId !== options.petId) ||
        (options.seasonId && progress.seasonId !== options.seasonId)) {
      await quarantineProgress(filePath, "previous");
      return createSeedProgress(options);
    }
    return progress;
  } catch (error) {
    if (error instanceof SyntaxError || error instanceof TypeError) {
      await quarantineProgress(filePath, "corrupt");
      return createSeedProgress(options);
    }
    throw error;
  }
}

async function quarantineProgress(filePath, label) {
  const backupPath = `${filePath}.${label}.${Date.now()}.${randomUUID()}`;
  try {
    await fs.rename(filePath, backupPath);
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
  }
}

function lockFailure(lockPath, code, signal, stderr) {
  const detail = stderr.trim().slice(0, 512);
  if (code === 75) return new Error(`Timed out waiting for progress lock: ${lockPath}`);
  return new Error(
    `Progress lock helper exited before acquisition (${code ?? signal ?? "unknown"})` +
    (detail ? `: ${detail}` : ""),
  );
}

async function acquireProgressLock(filePath) {
  // This is deliberately distinct from the pre-1.2 directory lock. lockf -k
  // requires one stable inode; it must never be unlinked between contenders.
  const lockPath = `${filePath}.lockf`;
  const readyMarker = `BUGFIRE_LOCK_READY:${randomUUID()}\n`;
  await fs.mkdir(path.dirname(filePath), { recursive: true, mode: 0o700 });
  await fs.writeFile(lockPath, "", { flag: "a", mode: 0o600 });
  await fs.chmod(lockPath, 0o600);
  if (!(await fs.lstat(lockPath)).isFile()) {
    throw new Error(`Progress lock guard is not a regular file: ${lockPath}`);
  }

  const holder = spawn(LOCKF_PATH, [
    "-k",
    "-n",
    "-s",
    "-w",
    "-t", String(Math.ceil(LOCK_WAIT_MS / 1_000)),
    lockPath,
    "/bin/cat",
  ], { stdio: ["pipe", "pipe", "pipe"] });
  holder.stdin.on("error", () => {});
  holder.stdout.setEncoding("utf8");
  holder.stderr.setEncoding("utf8");

  try {
    await new Promise((resolve, reject) => {
      let stdout = "";
      let stderr = "";
      let settled = false;
      const timer = setTimeout(() => {
        finish(new Error(`Timed out starting progress lock helper: ${lockPath}`));
      }, LOCK_WAIT_MS + 1_500);

      function cleanup() {
        clearTimeout(timer);
        holder.stdout.off("data", onStdout);
        holder.stderr.off("data", onStderr);
        holder.off("error", onError);
        holder.off("exit", onExit);
      }
      function finish(error) {
        if (settled) return;
        settled = true;
        cleanup();
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      }
      function onStdout(chunk) {
        stdout = `${stdout}${chunk}`.slice(-1_024);
        if (stdout === readyMarker) finish();
      }
      function onStderr(chunk) {
        stderr = `${stderr}${chunk}`.slice(-4_096);
      }
      function onError(error) {
        finish(error);
      }
      function onExit(code, signal) {
        finish(lockFailure(lockPath, code, signal, stderr));
      }

      holder.stdout.on("data", onStdout);
      holder.stderr.on("data", onStderr);
      holder.on("error", onError);
      holder.on("exit", onExit);
      // lockf does not exec cat until the kernel lock is held. The exact nonce
      // can therefore only echo after acquisition; keeping stdin open holds it.
      holder.stdin.write(readyMarker);
    });
  } catch (error) {
    holder.stdin.end();
    if (holder.exitCode === null && holder.signalCode === null) holder.kill("SIGTERM");
    await new Promise((resolve) => {
      if (holder.exitCode !== null || holder.signalCode !== null) {
        resolve();
        return;
      }
      const timer = setTimeout(() => {
        holder.kill("SIGKILL");
        resolve();
      }, 1_000);
      holder.once("exit", () => {
        clearTimeout(timer);
        resolve();
      });
    });
    throw error;
  }

  return { holder, lockPath };
}

function assertProgressLockHeld(lock) {
  if (lock.holder.exitCode !== null || lock.holder.signalCode !== null) {
    throw new Error(`Progress lock was lost while the transaction was running: ${lock.lockPath}`);
  }
}

async function releaseProgressLock(lock) {
  if (lock.holder.exitCode !== null || lock.holder.signalCode !== null) return false;
  return new Promise((resolve) => {
    let settled = false;
    const finish = (released) => {
      if (settled) return;
      settled = true;
      clearTimeout(termTimer);
      clearTimeout(killTimer);
      lock.holder.off("exit", onExit);
      resolve(released);
    };
    const onExit = () => finish(true);
    const termTimer = setTimeout(() => lock.holder.kill("SIGTERM"), 1_000);
    const killTimer = setTimeout(() => {
      lock.holder.kill("SIGKILL");
      finish(false);
    }, 2_000);
    lock.holder.once("exit", onExit);
    lock.holder.stdin.end();
  });
}

export async function withProgressLock(filePath, operation) {
  if (typeof filePath !== "string" || !filePath || typeof operation !== "function") {
    throw new TypeError("withProgressLock requires a file path and operation");
  }
  const lock = await acquireProgressLock(filePath);
  try {
    const result = await operation(() => assertProgressLockHeld(lock));
    assertProgressLockHeld(lock);
    return result;
  } finally {
    await releaseProgressLock(lock);
  }
}

export async function transactProgress(filePath, options, transaction) {
  if (typeof transaction !== "function") {
    throw new TypeError("transactProgress requires a transaction function");
  }
  return withProgressLock(filePath, async (assertLockHeld) => {
    const current = await loadProgress(filePath, options);
    const result = await transaction(current);
    if (!isPlainObject(result) || !Object.hasOwn(result, "progress")) {
      throw new TypeError("progress transaction must return a result containing progress");
    }
    const progress = validateProgress(result.progress);
    assertLockHeld();
    await saveProgress(filePath, progress);
    assertLockHeld();
    return { ...result, progress };
  });
}

export async function saveProgress(filePath, value) {
  const progress = validateProgress(value);
  const directory = path.dirname(filePath);
  const temporary = path.join(
    directory,
    `.${path.basename(filePath)}.${process.pid}.${randomUUID()}.tmp`,
  );
  await fs.mkdir(directory, { recursive: true, mode: 0o700 });
  try {
    await fs.writeFile(temporary, `${JSON.stringify(progress, null, 2)}\n`, {
      encoding: "utf8",
      mode: 0o600,
      flag: "wx",
    });
    await fs.rename(temporary, filePath);
    await fs.chmod(filePath, 0o600);
  } finally {
    await fs.rm(temporary, { force: true }).catch(() => {});
  }
  return progress;
}
