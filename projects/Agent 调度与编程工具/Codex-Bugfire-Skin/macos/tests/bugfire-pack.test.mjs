import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  buildBugfirePack,
  createStarterManifest,
  validateBugfirePack,
} from "../scripts/bugfire-pack.mjs";

const ROOT = new URL("../", import.meta.url);
const bundledBackground = new URL("assets/portal-hero.png", ROOT);

async function fixture(overrides = {}) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-test-"));
  const assets = path.join(directory, "assets");
  await fs.mkdir(assets);
  await fs.copyFile(bundledBackground, path.join(assets, "background.png"));
  await fs.copyFile(bundledBackground, path.join(assets, "pet-idle.png"));
  const manifest = {
    ...createStarterManifest(),
    id: "test-companion",
    name: "测试伙伴",
    ...overrides,
  };
  await fs.writeFile(path.join(directory, "bugfire-pack.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  return directory;
}

function jpegFixture(width, height) {
  const content = Buffer.from([
    0xff, 0xd8,
    0xff, 0xc0, 0x00, 0x11, 0x08, 0x00, 0x01, 0x00, 0x01, 0x03,
    0x01, 0x11, 0x00, 0x02, 0x11, 0x00, 0x03, 0x11, 0x00,
    0xff, 0xd9,
  ]);
  content.writeUInt16BE(height, 7);
  content.writeUInt16BE(width, 9);
  return content;
}

function webpFixture(width, height, { animated = false } = {}) {
  if (animated) {
    const content = Buffer.alloc(30);
    content.write("RIFF", 0, "ascii");
    content.writeUInt32LE(22, 4);
    content.write("WEBP", 8, "ascii");
    content.write("VP8X", 12, "ascii");
    content.writeUInt32LE(10, 16);
    content[20] = 0x02;
    content.writeUIntLE(width - 1, 24, 3);
    content.writeUIntLE(height - 1, 27, 3);
    return content;
  }
  const content = Buffer.alloc(26);
  content.write("RIFF", 0, "ascii");
  content.writeUInt32LE(18, 4);
  content.write("WEBP", 8, "ascii");
  content.write("VP8L", 12, "ascii");
  content.writeUInt32LE(5, 16);
  content[20] = 0x2f;
  content.writeUInt32LE((width - 1) | ((height - 1) << 14), 21);
  return content;
}

function webpChunk(type, payload) {
  const padding = payload.length & 1;
  const chunk = Buffer.alloc(8 + payload.length + padding);
  chunk.write(type, 0, "ascii");
  chunk.writeUInt32LE(payload.length, 4);
  payload.copy(chunk, 8);
  return chunk;
}

function webpContainer(chunks) {
  const body = Buffer.concat(chunks);
  const content = Buffer.alloc(12 + body.length);
  content.write("RIFF", 0, "ascii");
  content.writeUInt32LE(content.length - 8, 4);
  content.write("WEBP", 8, "ascii");
  body.copy(content, 12);
  return content;
}

function extendedLossyWebpFixture(width, height) {
  const extended = Buffer.alloc(10);
  extended.writeUIntLE(width - 1, 4, 3);
  extended.writeUIntLE(height - 1, 7, 3);
  const frame = Buffer.alloc(10);
  frame.set([0x9d, 0x01, 0x2a], 3);
  frame.writeUInt16LE(width, 6);
  frame.writeUInt16LE(height, 8);
  return webpContainer([
    webpChunk("VP8X", extended),
    webpChunk("VP8 ", frame),
  ]);
}

function extendedLosslessWebpFixture(canvasWidth, canvasHeight, frameWidth, frameHeight) {
  const extended = Buffer.alloc(10);
  extended.writeUIntLE(canvasWidth - 1, 4, 3);
  extended.writeUIntLE(canvasHeight - 1, 7, 3);
  const frame = Buffer.alloc(5);
  frame[0] = 0x2f;
  frame.writeUInt32LE((frameWidth - 1) | ((frameHeight - 1) << 14), 1);
  return webpContainer([
    webpChunk("VP8X", extended),
    webpChunk("VP8L", frame),
  ]);
}

async function replaceIdleArt(directory, filename, content) {
  const manifestPath = path.join(directory, "bugfire-pack.json");
  const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
  manifest.pet.art.idle = `assets/${filename}`;
  await fs.writeFile(path.join(directory, "assets", filename), content);
  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
}

test("starter manifest documents the minimum upload contract", () => {
  const manifest = createStarterManifest();
  assert.equal(manifest.schemaVersion, 1);
  assert.equal(manifest.theme.background, "assets/background.png");
  assert.equal(manifest.pet.art.idle, "assets/pet-idle.png");
  assert.equal(manifest.pet.art.building, undefined);
  assert.equal(manifest.gameplay.quests.length, 3);
  assert.deepEqual(manifest.gameplay.quests.map((quest) => quest.metric), [
    "repairedBuilds", "successfulBuilds", "level",
  ]);
});

test("validates one background plus one reusable pet image", async () => {
  const directory = await fixture();
  const result = await validateBugfirePack(directory);
  assert.equal(result.pass, true);
  assert.deepEqual(result.requiredUploads, ["assets/background.png", "assets/pet-idle.png"]);
  assert.deepEqual(result.optionalUploads, []);
});

test("accepts optional per-state pet art and keeps all paths inside the pack", async () => {
  const directory = await fixture();
  const manifestPath = path.join(directory, "bugfire-pack.json");
  const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
  for (const state of ["building", "bug", "fire", "success", "levelUp"]) {
    const filename = `assets/pet-${state}.png`;
    await fs.copyFile(bundledBackground, path.join(directory, filename));
    manifest.pet.art[state] = filename;
  }
  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);

  const result = await validateBugfirePack(directory);
  assert.equal(result.pass, true);
  assert.equal(result.optionalUploads.length, 5);

  manifest.pet.art.fire = "../outside.png";
  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  await assert.rejects(validateBugfirePack(directory), /inside|relative|path/i);
});

test("rejects malformed colors, quest metrics, unsafe identifiers, and oversized text", async () => {
  const starter = createStarterManifest();
  const invalidCases = [
    { id: "../escape" },
    { theme: { ...starter.theme, colors: { ...starter.theme.colors, accent: "red" } } },
    { gameplay: { quests: [{ id: "bad", title: "Bad", metric: "sourceLines", target: 1 }] } },
    { pet: { ...starter.pet, name: "x".repeat(81) } },
  ];
  for (const overrides of invalidCases) {
    const directory = await fixture(overrides);
    await assert.rejects(validateBugfirePack(directory), /invalid|must|unsupported|identifier|color|length/i);
  }
});

test("rejects manifest boundary violations and inconsistent declarations", async () => {
  const starter = createStarterManifest();
  const invalidCases = [
    { gameplay: { ...starter.gameplay, rewardXp: 0 } },
    { gameplay: { ...starter.gameplay, rewardXp: 101 } },
    { pet: { ...starter.pet, art: { idle: "assets/pet-idle.svg" } } },
    { gameplay: { ...starter.gameplay, sayings: [] } },
    { gameplay: { ...starter.gameplay, sayings: Array.from({ length: 13 }, () => "hello") } },
    { gameplay: { ...starter.gameplay, quests: [] } },
    { gameplay: { ...starter.gameplay, quests: Array.from({ length: 6 }, (_, index) => ({
      id: `quest-${index}`, title: `Quest ${index}`, metric: "xp", target: 1,
    })) } },
    { gameplay: { ...starter.gameplay, quests: [starter.gameplay.quests[0], starter.gameplay.quests[0]] } },
    { rights: { ...starter.rights, sourceUrl: "http://example.com/art" } },
    { unexpected: true },
  ];
  for (const overrides of invalidCases) {
    const directory = await fixture(overrides);
    await assert.rejects(validateBugfirePack(directory), /invalid|must|unsupported|unique|https|fields/i);
  }
});

test("requires idle art during validation rather than crashing during build", async () => {
  const starter = createStarterManifest();
  for (const art of [{}, { building: "assets/pet-idle.png" }]) {
    const directory = await fixture({ pet: { ...starter.pet, art } });
    await assert.rejects(validateBugfirePack(directory), /idle/i);
  }
});

test("rejects missing, non-directory, linked, and oversized manifest entry points", async () => {
  const missingRoot = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-missing-root-"));
  await fs.rm(missingRoot, { recursive: true });
  await assert.rejects(validateBugfirePack(missingRoot), /pack directory.*missing/i);

  const fileRoot = path.join(os.tmpdir(), `bugfire-pack-file-root-${process.pid}-${Date.now()}`);
  await fs.writeFile(fileRoot, "not a directory");
  await assert.rejects(validateBugfirePack(fileRoot), /pack root.*directory/i);

  const linkedManifest = await fixture();
  const manifestPath = path.join(linkedManifest, "bugfire-pack.json");
  const manifestTarget = path.join(linkedManifest, "manifest-target.json");
  await fs.rename(manifestPath, manifestTarget);
  await fs.symlink(manifestTarget, manifestPath);
  await assert.rejects(validateBugfirePack(linkedManifest), /manifest.*regular file|link/i);

  const oversizedManifest = await fixture();
  await fs.writeFile(
    path.join(oversizedManifest, "bugfire-pack.json"),
    Buffer.alloc((128 * 1024) + 1, 0x20),
  );
  await assert.rejects(validateBugfirePack(oversizedManifest), /manifest.*file size/i);
});

test("rejects missing, malformed, linked, fake, oversized-dimension, and animated assets", async () => {
  const missingManifest = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-missing-manifest-"));
  await assert.rejects(validateBugfirePack(missingManifest), /manifest.*missing/i);

  const malformedManifest = await fixture();
  await fs.writeFile(path.join(malformedManifest, "bugfire-pack.json"), "{not-json", "utf8");
  await assert.rejects(validateBugfirePack(malformedManifest), /valid JSON|manifest/i);

  const missingArt = await fixture();
  await fs.rm(path.join(missingArt, "assets", "pet-idle.png"));
  await assert.rejects(validateBugfirePack(missingArt), /missing/i);

  const emptyArt = await fixture();
  await fs.writeFile(path.join(emptyArt, "assets", "pet-idle.png"), "");
  await assert.rejects(validateBugfirePack(emptyArt), /size|image/i);

  const linkedArt = await fixture();
  await fs.rm(path.join(linkedArt, "assets", "pet-idle.png"));
  await fs.symlink(
    path.join(linkedArt, "assets", "background.png"),
    path.join(linkedArt, "assets", "pet-idle.png"),
  );
  await assert.rejects(validateBugfirePack(linkedArt), /link|regular/i);

  const escapedParent = await fixture();
  const outside = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-outside-"));
  await fs.copyFile(bundledBackground, path.join(outside, "background.png"));
  await fs.copyFile(bundledBackground, path.join(outside, "pet-idle.png"));
  await fs.rm(path.join(escapedParent, "assets"), { recursive: true });
  await fs.symlink(outside, path.join(escapedParent, "assets"), "dir");
  await assert.rejects(validateBugfirePack(escapedParent), /inside|link|pack/i);

  const fakeImage = await fixture();
  await fs.writeFile(path.join(fakeImage, "assets", "pet-idle.png"), "not really a png");
  await assert.rejects(validateBugfirePack(fakeImage), /image|content/i);

  const hugeDimensions = await fixture();
  const hugePng = Buffer.from(await fs.readFile(bundledBackground));
  hugePng.writeUInt32BE(50_000, 16);
  hugePng.writeUInt32BE(50_000, 20);
  await fs.writeFile(path.join(hugeDimensions, "assets", "pet-idle.png"), hugePng);
  await assert.rejects(validateBugfirePack(hugeDimensions), /dimension|pixel|image/i);

  const animated = await fixture();
  const png = Buffer.from(await fs.readFile(bundledBackground));
  const fakeAnimationChunk = Buffer.concat([
    Buffer.alloc(4), Buffer.from("acTL"), Buffer.alloc(4),
  ]);
  const animatedPng = Buffer.concat([png.subarray(0, 33), fakeAnimationChunk, png.subarray(33)]);
  await fs.writeFile(path.join(animated, "assets", "pet-idle.png"), animatedPng);
  await assert.rejects(validateBugfirePack(animated), /animated|animation|image/i);
});

test("validates JPEG and WebP metadata, matching extensions, dimensions, and animation flags", async () => {
  const jpeg = await fixture();
  await replaceIdleArt(jpeg, "pet-idle.jpg", jpegFixture(320, 240));
  const jpegResult = await validateBugfirePack(jpeg);
  assert.deepEqual(jpegResult.petFiles.idle.image, { format: "jpeg", width: 320, height: 240 });

  const webp = await fixture();
  await replaceIdleArt(webp, "pet-idle.webp", webpFixture(256, 128));
  const webpResult = await validateBugfirePack(webp);
  assert.deepEqual(webpResult.petFiles.idle.image, { format: "webp", width: 256, height: 128 });

  const mismatched = await fixture();
  await replaceIdleArt(mismatched, "pet-idle.jpg", await fs.readFile(bundledBackground));
  await assert.rejects(validateBugfirePack(mismatched), /extension|match|content/i);

  const oversized = await fixture();
  await replaceIdleArt(oversized, "pet-idle.jpg", jpegFixture(5_000, 1_000));
  await assert.rejects(validateBugfirePack(oversized), /dimension|pixel/i);

  const animatedWebp = await fixture();
  await replaceIdleArt(animatedWebp, "pet-idle.webp", webpFixture(64, 64, { animated: true }));
  await assert.rejects(validateBugfirePack(animatedWebp), /animated|animation/i);
});

test("validates extended lossy WebP and rejects unsafe WebP container structures", async () => {
  const extended = await fixture();
  await replaceIdleArt(extended, "pet-idle.webp", extendedLossyWebpFixture(640, 360));
  const result = await validateBugfirePack(extended);
  assert.deepEqual(result.petFiles.idle.image, { format: "webp", width: 640, height: 360 });

  const invalidContainers = [
    {
      name: "declared RIFF length exceeds the file",
      content: (() => {
        const content = webpFixture(32, 32);
        content.writeUInt32LE(content.length + 100, 4);
        return content;
      })(),
      error: /container/i,
    },
    {
      name: "chunk payload is truncated",
      content: (() => {
        const content = webpContainer([webpChunk("VP8L", Buffer.from([0x2f, 0, 0, 0, 0]))]);
        content.writeUInt32LE(100, 16);
        return content;
      })(),
      error: /truncated/i,
    },
    {
      name: "animation chunk is declared",
      content: webpContainer([webpChunk("ANIM", Buffer.alloc(6))]),
      error: /animated|animation/i,
    },
    {
      name: "extended header is too short",
      content: webpContainer([webpChunk("VP8X", Buffer.alloc(9))]),
      error: /extended header/i,
    },
    {
      name: "lossless frame signature is invalid",
      content: webpContainer([webpChunk("VP8L", Buffer.alloc(5))]),
      error: /lossless.*frame/i,
    },
    {
      name: "lossy frame signature is invalid",
      content: webpContainer([webpChunk("VP8 ", Buffer.alloc(10))]),
      error: /lossy.*frame/i,
    },
    {
      name: "container has no readable frame",
      content: webpContainer([webpChunk("EXIF", Buffer.from("meta"))]),
      error: /no readable.*frame/i,
    },
    {
      name: "tiny extended canvas cannot hide an oversized lossless frame",
      content: extendedLosslessWebpFixture(1, 1, 16_384, 16_384),
      error: /canvas.*match|dimension|pixel/i,
    },
    {
      name: "multiple still-image frames are rejected",
      content: webpContainer([
        webpChunk("VP8L", webpFixture(2, 2).subarray(20, 25)),
        webpChunk("VP8L", webpFixture(2, 2).subarray(20, 25)),
      ]),
      error: /multiple.*frames/i,
    },
  ];
  for (const invalidContainer of invalidContainers) {
    const directory = await fixture();
    await replaceIdleArt(directory, "pet-idle.webp", invalidContainer.content);
    await assert.rejects(
      validateBugfirePack(directory),
      invalidContainer.error,
      invalidContainer.name,
    );
  }
});

test("rejects JPEG streams with truncated, invalid, or missing frame segments", async () => {
  const invalidJpegs = [
    { content: Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00]), error: /truncated/i },
    { content: Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x01, 0xff, 0xd9]), error: /invalid.*segment/i },
    { content: Buffer.from([0xff, 0xd8, 0xff, 0xd9]), error: /no readable.*frame/i },
  ];
  for (const invalidJpeg of invalidJpegs) {
    const directory = await fixture();
    await replaceIdleArt(directory, "pet-idle.jpg", invalidJpeg.content);
    await assert.rejects(validateBugfirePack(directory), invalidJpeg.error);
  }
});

test("build compiles a runtime theme and copies only declared assets", async () => {
  const directory = await fixture();
  const output = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-output-"));
  await fs.rm(output, { recursive: true });
  const result = await buildBugfirePack(directory, output);

  assert.equal(result.pass, true);
  const theme = JSON.parse(await fs.readFile(path.join(output, "theme.json"), "utf8"));
  assert.equal(theme.schemaVersion, 1);
  assert.equal(theme.id, "test-companion");
  assert.equal(theme.image, "background.png");
  assert.equal(theme.pet.art.idle, "pet-idle.png");
  assert.equal(theme.pet.art.fire, "pet-idle.png", "missing states reuse idle art");
  assert.equal(theme.pet.quests.length, 3);
  assert.equal(theme.pet.sayings.length > 0, true);
  await fs.access(path.join(output, "background.png"));
  await fs.access(path.join(output, "pet-idle.png"));
  assert.equal((await fs.stat(path.join(output, "theme.json"))).mode & 0o777, 0o600);
});

test("build preserves declared state-specific art and level-up naming", async () => {
  const directory = await fixture();
  const manifestPath = path.join(directory, "bugfire-pack.json");
  const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
  for (const state of ["fire", "levelUp"]) {
    const filename = `pet-${state}.png`;
    await fs.copyFile(bundledBackground, path.join(directory, "assets", filename));
    manifest.pet.art[state] = `assets/${filename}`;
  }
  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);

  const output = path.join(os.tmpdir(), `bugfire-pack-states-${process.pid}-${Date.now()}`);
  const result = await buildBugfirePack(directory, output);
  assert.equal(result.pass, true);
  const theme = JSON.parse(await fs.readFile(path.join(output, "theme.json"), "utf8"));
  assert.equal(theme.pet.art.fire, "pet-fire.png");
  assert.equal(theme.pet.art.levelUp, "pet-level-up.png");
  await fs.access(path.join(output, "pet-fire.png"));
  await fs.access(path.join(output, "pet-level-up.png"));
});

test("build refuses to overwrite a non-empty output unless replace is explicit", async () => {
  const directory = await fixture();
  const output = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-existing-"));
  await fs.writeFile(path.join(output, "keep.txt"), "user file");
  await assert.rejects(buildBugfirePack(directory, output), /non-empty|replace/i);
  await buildBugfirePack(directory, output, { replace: true });
  await assert.rejects(fs.access(path.join(output, "keep.txt")));
});

test("build never treats its source pack as a replaceable output", async () => {
  const directory = await fixture();
  await assert.rejects(
    buildBugfirePack(directory, directory, { replace: true }),
    /source|output|overlap|same/i,
  );
  await fs.access(path.join(directory, "bugfire-pack.json"));
  await fs.access(path.join(directory, "assets", "pet-idle.png"));
});

test("build rejects output nested within source and source nested within output", async () => {
  const sourceWithNestedOutput = await fixture();
  await assert.rejects(
    buildBugfirePack(sourceWithNestedOutput, path.join(sourceWithNestedOutput, "compiled"), { replace: true }),
    /source|output|overlap/i,
  );
  await fs.access(path.join(sourceWithNestedOutput, "bugfire-pack.json"));

  const container = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-pack-containing-output-"));
  const source = path.join(container, "source");
  await fs.rename(await fixture(), source);
  await assert.rejects(
    buildBugfirePack(source, container, { replace: true }),
    /source|output|overlap/i,
  );
  await fs.access(path.join(source, "bugfire-pack.json"));
});
