import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, test } from "node:test";

import * as bugfireState from "../scripts/bugfire-state.mjs";

const {
  LEVELS,
  SEASON_CERTIFICATE_DISCLAIMER,
  createSeedProgress,
  loadProgress,
  saveProgress,
  settleBuild,
  validateProgress,
} = bugfireState;

const PET_ID = "bugfire-patch-dragon";
const SEASON_ID = "season-1";
const NOW = "2026-07-16T08:00:00.000Z";
const RECOVERY_NOW = "2026-07-16T09:00:00.000Z";
const MAX_EVENT_ID_LENGTH = 120;
const MAX_SETTLED_EVENT_IDS = 256;
const MAX_PROGRESS_FILE_BYTES = 1024 * 1024;
const MAX_PROGRESS_CARDS = LEVELS.length;
const temporaryDirectories = [];

function seed(now = NOW, overrides = {}) {
  return {
    ...createSeedProgress({ petId: PET_ID, seasonId: SEASON_ID, now }),
    ...overrides,
  };
}

function levelCard(level, id = `level-${level}-fixture`) {
  const entry = LEVELS.find((candidate) => candidate.level === level);
  return {
    id,
    kind: "level",
    level,
    stage: entry.stage,
    skill: entry.skill,
    earnedAt: NOW,
  };
}

function seasonCard(id = "season-season-1-fixture") {
  return {
    id,
    kind: "season",
    petId: PET_ID,
    seasonId: SEASON_ID,
    title: "BUGFIRE 赛季证书",
    disclaimer: SEASON_CERTIFICATE_DISCLAIMER,
    earnedAt: NOW,
  };
}

async function temporaryPath() {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-hardening-test-"));
  temporaryDirectories.push(directory);
  return path.join(directory, "progress.json");
}

async function assertCorruptBackup(filePath, expectedSource) {
  const basename = path.basename(filePath);
  const entries = await fs.readdir(path.dirname(filePath));
  const backups = entries.filter((entry) =>
    entry === `${basename}.corrupt` || entry.startsWith(`${basename}.corrupt.`));

  assert.equal(backups.length, 1, "the rejected source must be retained as one .corrupt backup");
  assert.equal(
    await fs.readFile(path.join(path.dirname(filePath), backups[0]), "utf8"),
    expectedSource,
    "the recovery backup must preserve the exact rejected bytes",
  );
}

async function waitForReady(child, marker = "READY\n") {
  child.stdout.setEncoding("utf8");
  let output = "";
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("fixture did not become ready")), 2_000);
    const onData = (chunk) => {
      output += chunk;
      if (!output.includes(marker)) return;
      clearTimeout(timeout);
      child.stdout.off("data", onData);
      resolve();
    };
    child.stdout.on("data", onData);
    child.once("error", reject);
    child.once("exit", (code, signal) => {
      if (!output.includes(marker)) {
        clearTimeout(timeout);
        reject(new Error(`fixture exited before ready (${code ?? signal})`));
      }
    });
  });
}

async function onceExit(child) {
  if (child.exitCode !== null || child.signalCode !== null) return;
  await new Promise((resolve) => child.once("exit", resolve));
}

afterEach(async () => {
  await Promise.all(temporaryDirectories.splice(0).map((directory) =>
    fs.rm(directory, { recursive: true, force: true })));
});

test("the maximum accepted eventId always produces valid level and season card ids", () => {
  const maximumEventId = "e".repeat(MAX_EVENT_ID_LENGTH);
  const levelResult = settleBuild(seed(), {
    eventId: maximumEventId,
    outcome: "success",
    rewardXp: 20,
    now: NOW,
  });

  assert.equal(levelResult.card?.id, `level-3-${maximumEventId}`);
  assert.deepEqual(validateProgress(levelResult.progress), levelResult.progress);

  const maximumSeasonId = "s".repeat(120);
  const nearlyCertified = seed(NOW, {
    seasonId: maximumSeasonId,
    xp: 740,
    failedBuilds: 3,
    successfulBuilds: 9,
    repairedBuilds: 2,
    unlockedSkills: LEVELS.slice(0, 4).map((entry) => entry.skill),
    settledEventIds: ["failure-1", "failure-2", "failure-3"],
  });
  const seasonResult = settleBuild(nearlyCertified, {
    eventId: maximumEventId,
    outcome: "repair-success",
    rewardXp: 35,
    now: NOW,
  });
  const certificate = seasonResult.progress.cards.find((card) => card.kind === "season");

  assert.equal(certificate?.id, `season-${maximumSeasonId}-${maximumEventId}`);
  assert.deepEqual(validateProgress(seasonResult.progress), seasonResult.progress);
  assert.throws(() => settleBuild(seed(), {
    eventId: "e".repeat(MAX_EVENT_ID_LENGTH + 1),
    outcome: "failed",
    rewardXp: 0,
    now: NOW,
  }), /eventId|progress|invalid/i);
});

test("level and season cards have exact schemas", () => {
  const levelResult = settleBuild(seed(), {
    eventId: "level-schema",
    outcome: "success",
    rewardXp: 20,
    now: NOW,
  });
  const level = levelResult.card;
  assert.deepEqual(Object.keys(level).sort(), [
    "earnedAt", "id", "kind", "level", "skill", "stage",
  ]);
  assert.throws(() => validateProgress({
    ...levelResult.progress,
    cards: [{ ...level, unexpected: true }],
  }), /card|schema|progress|invalid/i);

  const certificate = seasonCard();
  const certified = seed(NOW, {
    xp: 750,
    failedBuilds: 3,
    successfulBuilds: 10,
    repairedBuilds: 3,
    unlockedSkills: LEVELS.map((entry) => entry.skill),
    cards: [certificate],
  });
  assert.deepEqual(Object.keys(certificate).sort(), [
    "disclaimer", "earnedAt", "id", "kind", "petId", "seasonId", "title",
  ]);
  assert.deepEqual(validateProgress(certified), certified);
  const { title: _title, ...missingTitle } = certificate;
  assert.throws(() => validateProgress({ ...certified, cards: [missingTitle] }), /card|schema|progress|invalid/i);
  assert.throws(() => validateProgress({
    ...certified,
    cards: [{ ...certificate, unexpected: true }],
  }), /card|schema|progress|invalid/i);
});

test("a progress record cannot contain two cards for the same level", () => {
  const duplicateLevel = seed(NOW, {
    cards: [levelCard(2, "level-2-first"), levelCard(2, "level-2-second")],
  });

  assert.throws(() => validateProgress(duplicateLevel), /card|level|progress|invalid/i);
});

test("the card history is bounded to the four level-ups plus one season certificate", () => {
  const maximumCards = seed(NOW, {
    xp: 750,
    failedBuilds: 3,
    successfulBuilds: 10,
    repairedBuilds: 3,
    unlockedSkills: LEVELS.map((entry) => entry.skill),
    cards: [levelCard(2), levelCard(3), levelCard(4), levelCard(5), seasonCard()],
  });

  assert.equal(maximumCards.cards.length, MAX_PROGRESS_CARDS);
  assert.deepEqual(validateProgress(maximumCards), maximumCards);
  assert.throws(() => validateProgress({
    ...maximumCards,
    cards: [...maximumCards.cards, seasonCard("season-season-1-overflow")],
  }), /card|progress|invalid/i);
});

test("settled event ids roll at a fixed bound and discard the oldest ids", () => {
  let progress = seed();
  const ids = Array.from(
    { length: MAX_SETTLED_EVENT_IDS + 2 },
    (_, index) => `failure-${index}`,
  );
  for (const eventId of ids) {
    progress = settleBuild(progress, {
      eventId,
      outcome: "failed",
      rewardXp: 35,
      now: NOW,
    }).progress;
  }

  assert.equal(progress.settledEventIds.length, MAX_SETTLED_EVENT_IDS);
  assert.deepEqual(progress.settledEventIds, ids.slice(-MAX_SETTLED_EVENT_IDS));
  assert.equal(progress.settledEventIds.includes(ids[0]), false);
  assert.equal(progress.settledEventIds.includes(ids[1]), false);
});

test("validation rejects an unbounded settled event history from disk", () => {
  const eventIds = Array.from(
    { length: MAX_SETTLED_EVENT_IDS + 1 },
    (_, index) => `event-${index}`,
  );

  assert.throws(() => validateProgress({
    ...seed(),
    settledEventIds: eventIds,
  }), /settledEventIds|event|progress|invalid/i);
});

test("loadProgress quarantines an oversized valid JSON file and returns the seed", async () => {
  const progressPath = await temporaryPath();
  const original = JSON.stringify(seed(NOW));
  const oversizedSource = `${original}${" ".repeat(MAX_PROGRESS_FILE_BYTES + 1)}`;
  await fs.writeFile(progressPath, oversizedSource, "utf8");

  const recovered = await loadProgress(progressPath, {
    petId: PET_ID,
    seasonId: SEASON_ID,
    now: RECOVERY_NOW,
  });

  assert.deepEqual(recovered, seed(RECOVERY_NOW));
  await assertCorruptBackup(progressPath, oversizedSource);
});

test("loadProgress quarantines malformed data and returns the seed", async () => {
  const progressPath = await temporaryPath();
  const malformedSource = "{not-json";
  await fs.writeFile(progressPath, malformedSource, "utf8");

  const recovered = await loadProgress(progressPath, {
    petId: PET_ID,
    seasonId: SEASON_ID,
    now: RECOVERY_NOW,
  });

  assert.deepEqual(recovered, seed(RECOVERY_NOW));
  await assertCorruptBackup(progressPath, malformedSource);
});

test("concurrent progress transactions settle both events without a lost update", async () => {
  const { transactProgress } = bugfireState;
  assert.equal(
    typeof transactProgress,
    "function",
    "bugfire-state must export transactProgress(filePath, options, transaction)",
  );

  const progressPath = await temporaryPath();
  const options = { petId: PET_ID, seasonId: SEASON_ID, now: NOW };
  await saveProgress(progressPath, seed());
  const events = [
    { eventId: "parallel-success-a", outcome: "success", rewardXp: 35, now: NOW },
    { eventId: "parallel-success-b", outcome: "success", rewardXp: 35, now: NOW },
  ];

  const results = await Promise.all(events.map((event) =>
    transactProgress(progressPath, options, (current) => settleBuild(current, event))));
  const persisted = await loadProgress(progressPath, options);

  assert.equal(results.every((result) => result.duplicate === false), true);
  assert.equal(persisted.xp, 290);
  assert.equal(persisted.successfulBuilds, 2);
  assert.deepEqual([...persisted.settledEventIds].sort(), events.map((event) => event.eventId).sort());
});

test("progress transactions honor the macOS kernel lock instead of path-age reclamation", {
  skip: process.platform !== "darwin",
}, async () => {
  const { withProgressLock } = bugfireState;
  const progressPath = await temporaryPath();
  const lockPath = `${progressPath}.lockf`;
  await fs.writeFile(lockPath, "", { mode: 0o600 });
  const holder = spawn("/usr/bin/lockf", [
    "-k", "-t", "1", lockPath,
    process.execPath,
    "-e", 'process.stdout.write("READY\\n"); process.stdin.resume();',
  ], { stdio: ["pipe", "pipe", "pipe"] });
  await waitForReady(holder);

  let contenderRan = false;
  const contender = withProgressLock(progressPath, async () => {
    contenderRan = true;
  });
  await new Promise((resolve) => setTimeout(resolve, 80));
  assert.equal(contenderRan, false, "the contender must wait for the kernel-held lock");

  holder.stdin.end();
  await contender;
  assert.equal(contenderRan, true);
  assert.equal((await fs.stat(lockPath)).isFile(), true, "-k keeps one stable lock inode");
});

test("a killed lock holder leaves no stale directory to reclaim", {
  skip: process.platform !== "darwin",
}, async () => {
  const { withProgressLock } = bugfireState;
  const progressPath = await temporaryPath();
  const lockPath = `${progressPath}.lockf`;
  const moduleUrl = new URL("../scripts/bugfire-state.mjs", import.meta.url).href;
  const fixture = [
    `import { withProgressLock } from ${JSON.stringify(moduleUrl)};`,
    `await withProgressLock(${JSON.stringify(progressPath)}, async () => {`,
    '  process.stdout.write("READY\\n");',
    "  await new Promise(() => setInterval(() => {}, 1_000));",
    "});",
  ].join("\n");
  const holder = spawn(process.execPath, ["--input-type=module", "-e", fixture], {
    stdio: ["ignore", "pipe", "pipe"],
  });
  await waitForReady(holder);
  holder.kill("SIGKILL");
  await new Promise((resolve) => holder.once("exit", resolve));

  assert.equal(
    (await fs.stat(lockPath)).isFile(),
    true,
    "kernel locking must use a stable file, never an ownerless directory",
  );
  assert.equal(await withProgressLock(progressPath, async () => "recovered"), "recovered");
});

test("a pre-1.2 ownerless lock directory cannot block the kernel guard", {
  skip: process.platform !== "darwin",
}, async () => {
  const { withProgressLock } = bugfireState;
  const progressPath = await temporaryPath();
  const legacyLockPath = `${progressPath}.lock`;
  await fs.mkdir(legacyLockPath, { mode: 0o700 });

  assert.equal(await withProgressLock(progressPath, async () => "migrated"), "migrated");
  assert.equal((await fs.stat(`${progressPath}.lockf`)).isFile(), true);
  assert.equal((await fs.stat(legacyLockPath)).isDirectory(), true,
    "the new lock must not race by deleting legacy metadata");
});

test("killing a queued parent cannot leave a late orphan lock holder", {
  skip: process.platform !== "darwin",
}, async () => {
  const { withProgressLock } = bugfireState;
  const progressPath = await temporaryPath();
  const lockPath = `${progressPath}.lockf`;
  await fs.writeFile(lockPath, "", { mode: 0o600 });
  const first = spawn("/usr/bin/lockf", [
    "-k", "-t", "1", lockPath,
    process.execPath,
    "-e", 'process.stdout.write("READY\\n"); process.stdin.resume();',
  ], { stdio: ["pipe", "pipe", "pipe"] });
  await waitForReady(first);

  const moduleUrl = new URL("../scripts/bugfire-state.mjs", import.meta.url).href;
  const waiter = spawn(process.execPath, ["--input-type=module", "-e", [
    `import { withProgressLock } from ${JSON.stringify(moduleUrl)};`,
    `await withProgressLock(${JSON.stringify(progressPath)}, async () => {`,
    '  process.stdout.write("UNEXPECTED_ACQUIRE\\n");',
    "});",
  ].join("\n")], { stdio: ["ignore", "pipe", "pipe"] });
  await new Promise((resolve) => setTimeout(resolve, 80));
  waiter.kill("SIGKILL");
  await onceExit(waiter);
  first.stdin.end();

  const startedAt = Date.now();
  assert.equal(await withProgressLock(progressPath, async () => "next"), "next");
  assert.ok(Date.now() - startedAt < 1_000, "the orphan waiter must release immediately on EOF");
});

test("the kernel coordination file keeps one stable inode across acquisitions", async () => {
  const { withProgressLock } = bugfireState;
  const progressPath = await temporaryPath();
  const lockPath = `${progressPath}.lockf`;
  assert.equal(await withProgressLock(progressPath, async () => "first"), "first");
  const first = await fs.stat(lockPath);
  assert.equal(first.isFile(), true);
  assert.equal(first.mode & 0o777, 0o600);

  assert.equal(await withProgressLock(progressPath, async () => "second"), "second");
  const second = await fs.stat(lockPath);
  assert.equal(second.isFile(), true);
  assert.equal(second.ino, first.ino, "-k must prevent unlink/recreate split-lock races");
});

test("a live lock is never reclaimed by a contender", async () => {
  const { withProgressLock } = bugfireState;
  const progressPath = await temporaryPath();
  const lockPath = `${progressPath}.lockf`;
  let releaseHolder;
  let contenderRan = false;
  const holder = withProgressLock(progressPath, () => new Promise((resolve) => {
    releaseHolder = resolve;
  }));

  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (releaseHolder) break;
    await new Promise((resolve) => setTimeout(resolve, 5));
  }
  assert.equal(typeof releaseHolder, "function");
  const contender = withProgressLock(progressPath, async () => {
    contenderRan = true;
  });
  await new Promise((resolve) => setTimeout(resolve, 80));

  assert.equal(contenderRan, false);
  assert.equal((await fs.stat(lockPath)).isFile(), true);
  releaseHolder();
  await holder;
  await contender;
  assert.equal(contenderRan, true);
});

test("many lock contenders never overlap their critical sections", async () => {
  const { withProgressLock } = bugfireState;
  const progressPath = await temporaryPath();
  let active = 0;
  let maximumActive = 0;
  await Promise.all(Array.from({ length: 8 }, (_, index) =>
    withProgressLock(progressPath, async () => {
      active += 1;
      maximumActive = Math.max(maximumActive, active);
      await new Promise((resolve) => setTimeout(resolve, 8 + (index % 3)));
      active -= 1;
    })));

  assert.equal(maximumActive, 1);
});
