import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, test } from "node:test";

import {
  LEVELS,
  createSeedProgress,
  levelForXp,
  loadProgress,
  resetProgress,
  saveProgress,
  settleBuild,
  validateProgress,
} from "../scripts/bugfire-state.mjs";

const NOW = "2026-07-16T08:00:00.000Z";
const NEXT = "2026-07-16T08:01:00.000Z";
const DISCLAIMER = "个人成长纪念卡，由本地活动生成；非官方认证，不代表专业资格。";
const PET_ID = "bugfire-patch-dragon";
const SEASON_ID = "season-1";
const temporaryDirectories = [];

function expectedSeed(overrides = {}) {
  return {
    schemaVersion: 1,
    petId: PET_ID,
    seasonId: SEASON_ID,
    xp: 220,
    failedBuilds: 0,
    successfulBuilds: 0,
    repairedBuilds: 0,
    unlockedSkills: ["灵感火星", "结构嗅探"],
    cards: [],
    settledEventIds: [],
    updatedAt: NOW,
    ...overrides,
  };
}

async function temporaryPath() {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-state-test-"));
  temporaryDirectories.push(directory);
  return path.join(directory, "progress.json");
}

afterEach(async () => {
  await Promise.all(temporaryDirectories.splice(0).map((directory) =>
    fs.rm(directory, { recursive: true, force: true })));
});

test("level table and XP boundaries match the five Vibe Coding stages", () => {
  assert.deepEqual(LEVELS, [
    { level: 1, minXp: 0, stage: "会描述", skill: "灵感火星" },
    { level: 2, minXp: 100, stage: "会搭建", skill: "结构嗅探" },
    { level: 3, minXp: 240, stage: "会除虫", skill: "BUGFIRE" },
    { level: 4, minXp: 450, stage: "会验收", skill: "测试结界" },
    { level: 5, minXp: 750, stage: "会交付", skill: "发布跃迁" },
  ]);

  for (const [xp, expectedLevel] of [
    [0, 1],
    [99, 1],
    [100, 2],
    [239, 2],
    [240, 3],
    [449, 3],
    [450, 4],
    [749, 4],
    [750, 5],
    [100_000, 5],
  ]) {
    assert.equal(levelForXp(xp).level, expectedLevel, `${xp} XP`);
  }
  assert.throws(() => levelForXp(-1), /xp/i);
  assert.throws(() => levelForXp(Number.NaN), /xp/i);
  assert.throws(() => levelForXp(1.5), /xp/i);
});

test("first use creates the clearly labelled Lv2 experience seed", () => {
  const progress = createSeedProgress({ petId: PET_ID, seasonId: SEASON_ID, now: NOW });

  assert.deepEqual(progress, expectedSeed());
  assert.equal(levelForXp(progress.xp).level, 2);
  assert.equal(LEVELS[2].minXp - progress.xp, 20);
});

test("reset clears activity and cards and returns the pet to Lv1 at 0 XP", () => {
  const progress = resetProgress({ petId: PET_ID, seasonId: SEASON_ID, now: NEXT });

  assert.deepEqual(progress, expectedSeed({
    xp: 0,
    unlockedSkills: ["灵感火星"],
    updatedAt: NEXT,
  }));
  assert.equal(levelForXp(progress.xp).level, 1);
});

test("a failed Build records the failure but never awards XP", () => {
  const seed = createSeedProgress({ petId: PET_ID, seasonId: SEASON_ID, now: NOW });
  const snapshot = structuredClone(seed);
  const result = settleBuild(seed, {
    eventId: "demo-failure-1",
    outcome: "failed",
    rewardXp: 35,
    now: NEXT,
  });

  assert.deepEqual(seed, snapshot, "settlement must not mutate its input");
  assert.equal(result.awardedXp, 0);
  assert.equal(result.duplicate, false);
  assert.equal(result.levelUp, null);
  assert.equal(result.card, null);
  assert.deepEqual(result.progress, expectedSeed({
    failedBuilds: 1,
    settledEventIds: ["demo-failure-1"],
    updatedAt: NEXT,
  }));
});

test("a repaired Build awards 35 XP, unlocks Lv3, and settles only once", () => {
  const failed = settleBuild(
    createSeedProgress({ petId: PET_ID, seasonId: SEASON_ID, now: NOW }),
    { eventId: "demo-failure-1", outcome: "failed", rewardXp: 35, now: NEXT },
  ).progress;
  const repairedAt = "2026-07-16T08:02:00.000Z";
  const first = settleBuild(failed, {
    eventId: "demo-repair-1",
    outcome: "repair-success",
    rewardXp: 35,
    now: repairedAt,
  });

  assert.equal(first.awardedXp, 35);
  assert.equal(first.duplicate, false);
  assert.deepEqual(first.levelUp, { from: 2, to: 3 });
  assert.equal(first.progress.xp, 255);
  assert.equal(first.progress.failedBuilds, 1);
  assert.equal(first.progress.successfulBuilds, 1);
  assert.equal(first.progress.repairedBuilds, 1);
  assert.deepEqual(first.progress.unlockedSkills, ["灵感火星", "结构嗅探", "BUGFIRE"]);
  assert.deepEqual(first.progress.settledEventIds, ["demo-failure-1", "demo-repair-1"]);
  assert.equal(first.progress.cards.length, 1);
  assert.equal(first.card?.kind, "level");
  assert.equal(first.card?.level, 3);
  assert.equal(first.card?.stage, "会除虫");
  assert.equal(first.card?.skill, "BUGFIRE");
  assert.equal(first.card?.earnedAt, repairedAt);
  assert.equal(typeof first.card?.id, "string");
  assert.notEqual(first.card?.id, "");

  const duplicate = settleBuild(first.progress, {
    eventId: "demo-repair-1",
    outcome: "repair-success",
    rewardXp: 35,
    now: "2026-07-16T08:03:00.000Z",
  });
  assert.equal(duplicate.awardedXp, 0);
  assert.equal(duplicate.duplicate, true);
  assert.equal(duplicate.levelUp, null);
  assert.equal(duplicate.card, null);
  assert.deepEqual(duplicate.progress, first.progress, "a replay must be a complete no-op");
});

test("Lv5 creates one season certificate only when all achievement gates are met", () => {
  const nearlyEligible = expectedSeed({
    xp: 740,
    failedBuilds: 3,
    successfulBuilds: 9,
    repairedBuilds: 2,
    unlockedSkills: ["灵感火星", "结构嗅探", "BUGFIRE", "测试结界"],
    settledEventIds: ["failure-1", "failure-2", "failure-3"],
  });
  const achieved = settleBuild(nearlyEligible, {
    eventId: "repair-to-level-five",
    outcome: "repair-success",
    rewardXp: 35,
    now: NEXT,
  });

  assert.equal(achieved.progress.xp, 775);
  assert.equal(achieved.progress.successfulBuilds, 10);
  assert.equal(achieved.progress.repairedBuilds, 3);
  assert.deepEqual(achieved.levelUp, { from: 4, to: 5 });
  assert.equal(achieved.progress.cards.filter((card) => card.kind === "level").length, 1);
  const certificates = achieved.progress.cards.filter((card) => card.kind === "season");
  assert.equal(certificates.length, 1);
  assert.equal(certificates[0].disclaimer, DISCLAIMER);
  assert.equal(typeof certificates[0].id, "string");
  assert.notEqual(certificates[0].id, "");

  const replay = settleBuild(achieved.progress, {
    eventId: "repair-to-level-five",
    outcome: "repair-success",
    rewardXp: 35,
    now: "2026-07-16T08:04:00.000Z",
  });
  assert.equal(replay.duplicate, true);
  assert.deepEqual(replay.progress, achieved.progress);
  assert.equal(replay.progress.cards.filter((card) => card.kind === "season").length, 1);
});

test("Lv5 does not create a season certificate while build gates are incomplete", () => {
  const incomplete = expectedSeed({
    xp: 740,
    failedBuilds: 3,
    successfulBuilds: 8,
    repairedBuilds: 2,
    unlockedSkills: ["灵感火星", "结构嗅探", "BUGFIRE", "测试结界"],
    settledEventIds: ["failure-1", "failure-2", "failure-3"],
  });
  const result = settleBuild(incomplete, {
    eventId: "repair-with-too-few-successes",
    outcome: "repair-success",
    rewardXp: 35,
    now: NEXT,
  });

  assert.equal(result.progress.xp, 775);
  assert.equal(result.progress.successfulBuilds, 9);
  assert.equal(result.progress.repairedBuilds, 3);
  assert.equal(result.progress.cards.some((card) => card.kind === "season"), false);
});

test("progress validation accepts the canonical schema and rejects corrupt state", () => {
  const seed = createSeedProgress({ petId: PET_ID, seasonId: SEASON_ID, now: NOW });
  assert.deepEqual(validateProgress(seed), seed);

  const invalidValues = [
    { ...seed, schemaVersion: 2 },
    { ...seed, petId: "" },
    { ...seed, seasonId: "" },
    { ...seed, xp: -1 },
    { ...seed, xp: 1.5 },
    { ...seed, failedBuilds: -1 },
    { ...seed, successfulBuilds: 0, repairedBuilds: 1 },
    { ...seed, failedBuilds: 0, repairedBuilds: 1, successfulBuilds: 1 },
    { ...seed, unlockedSkills: ["BUGFIRE"] },
    { ...seed, cards: {} },
    { ...seed, settledEventIds: ["same", "same"] },
    { ...seed, updatedAt: "yesterday" },
    { ...seed, unexpected: true },
  ];
  for (const value of invalidValues) {
    assert.throws(() => validateProgress(value), /progress|schema|invalid/i);
  }
});

test("loadProgress seeds first use and recovers malformed or invalid saved data", async () => {
  const missingPath = await temporaryPath();
  const options = { petId: PET_ID, seasonId: SEASON_ID, now: NOW };
  assert.deepEqual(await loadProgress(missingPath, options), expectedSeed());

  const malformedPath = await temporaryPath();
  await fs.writeFile(malformedPath, "{not-json", "utf8");
  assert.deepEqual(await loadProgress(malformedPath, options), expectedSeed());

  const invalidPath = await temporaryPath();
  await fs.writeFile(invalidPath, JSON.stringify({ ...expectedSeed(), xp: -10 }), "utf8");
  assert.deepEqual(await loadProgress(invalidPath, options), expectedSeed());
});

test("saveProgress atomically writes mode 0600 and preserves the last valid save", async () => {
  const progressPath = await temporaryPath();
  const seed = createSeedProgress({ petId: PET_ID, seasonId: SEASON_ID, now: NOW });
  await saveProgress(progressPath, seed);

  assert.deepEqual(JSON.parse(await fs.readFile(progressPath, "utf8")), seed);
  assert.equal((await fs.stat(progressPath)).mode & 0o777, 0o600);
  assert.deepEqual(await fs.readdir(path.dirname(progressPath)), [path.basename(progressPath)]);
  assert.deepEqual(
    await loadProgress(progressPath, { petId: PET_ID, seasonId: SEASON_ID, now: NEXT }),
    seed,
  );

  const before = await fs.readFile(progressPath, "utf8");
  await assert.rejects(saveProgress(progressPath, { ...seed, xp: -1 }), /progress|xp|invalid/i);
  assert.equal(await fs.readFile(progressPath, "utf8"), before);
  assert.deepEqual(await fs.readdir(path.dirname(progressPath)), [path.basename(progressPath)]);
});
