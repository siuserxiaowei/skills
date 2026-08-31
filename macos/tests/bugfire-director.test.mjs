import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  applyHumanReview,
  draftWithOpenAI,
  materializeReviewedPlan,
  sha256,
  stableJson,
  validateDirectorBrief,
  validateDirectorPlan,
  verifyRecordedFixture,
} from "../scripts/bugfire-director.mjs";
import { buildBugfirePack, validateBugfirePack } from "../scripts/bugfire-pack.mjs";

const MACOS = path.resolve(fileURLToPath(new URL("../", import.meta.url)));
const PROJECT = await fs.access(path.join(MACOS, "contest", "bugfire"))
  .then(() => MACOS, () => path.dirname(MACOS));
const DEMO = path.join(PROJECT, "contest", "bugfire", "demo");
const DIRECTOR = path.join(MACOS, "scripts", "bugfire-director.mjs");
const execFileAsync = promisify(execFile);

async function json(file) {
  return JSON.parse(await fs.readFile(file, "utf8"));
}

function chatResponse(payload, { ok = true, status = 200 } = {}) {
  const envelope = { choices: [{ message: { content: JSON.stringify(payload) } }] };
  const bytes = Buffer.from(JSON.stringify(envelope));
  let delivered = false;
  return {
    ok,
    status,
    headers: { get: () => null },
    body: {
      getReader: () => ({
        read: async () => {
          if (delivered) return { done: true, value: undefined };
          delivered = true;
          return { done: false, value: bytes };
        },
        cancel: async () => {},
        releaseLock: () => {},
      }),
    },
  };
}

function byteResponse(bytes, { ok = true, status = 200, contentLength = null } = {}) {
  const payload = Buffer.from(bytes);
  let delivered = false;
  return {
    ok,
    status,
    headers: {
      get: (name) => name.toLowerCase() === "content-length" ? contentLength : null,
    },
    body: {
      getReader: () => ({
        read: async () => {
          if (delivered) return { done: true, value: undefined };
          delivered = true;
          return { done: false, value: payload };
        },
        cancel: async () => {},
        releaseLock: () => {},
      }),
    },
  };
}

test("recorded AI fixture is explicit, schema-valid, and checksum locked", async () => {
  const result = await verifyRecordedFixture(
    path.join(DEMO, "ai-draft-plan.json"),
    path.join(DEMO, "ai-draft-plan.sha256"),
    path.join(DEMO, "brief.json"),
  );
  assert.equal(result.pass, true);
  assert.equal(result.mode, "recorded-agent-fixture");
  assert.equal(result.briefVerified, true);
  assert.match(result.model, /model ID not independently attested/i);
  assert.doesNotMatch(result.model, /^gpt-/i);
  assert.match(result.notice, /not presented as a live API call/i);
});

test("recorded fixture checksum input must be a small regular UTF-8 file", async (t) => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-checksum-boundary-"));
  t.after(() => fs.rm(workspace, { recursive: true, force: true }));
  const validChecksum = path.join(DEMO, "ai-draft-plan.sha256");
  const oversized = path.join(workspace, "oversized.sha256");
  const linked = path.join(workspace, "linked.sha256");
  const malformed = path.join(workspace, "malformed.sha256");
  const directory = path.join(workspace, "directory.sha256");
  await fs.writeFile(oversized, Buffer.alloc(4 * 1024 + 1, 0x61));
  await fs.symlink(validChecksum, linked);
  await fs.writeFile(malformed, Buffer.from([0xff]));
  await fs.mkdir(directory);

  for (const checksum of [oversized, linked, directory]) {
    await assert.rejects(verifyRecordedFixture(
      path.join(DEMO, "ai-draft-plan.json"),
      checksum,
      path.join(DEMO, "brief.json"),
    ), /fixture checksum must be a regular text file no larger than 4096 bytes/i);
  }
  await assert.rejects(verifyRecordedFixture(
    path.join(DEMO, "ai-draft-plan.json"),
    malformed,
    path.join(DEMO, "brief.json"),
  ), /fixture checksum is not valid UTF-8/i);
});

test("director provenance and review timestamps require canonical RFC 3339", async () => {
  const draft = await json(path.join(DEMO, "ai-draft-plan.json"));
  const review = await json(path.join(DEMO, "human-review.json"));
  const brief = await json(path.join(DEMO, "brief.json"));
  const invalidTimestamps = [
    "1",
    "2026-08-31",
    "August 31, 2026",
    "2026-02-30T06:00:00Z",
    "2026-08-31T24:00:00Z",
    "2026-08-31T06:00:60Z",
    "2026-08-31t06:00:00z",
    "2026-08-31T06:00:00+24:00",
    " 2026-08-31T06:00:00Z",
    "2026-08-31T06:00:00Z ",
  ];
  for (const timestamp of invalidTimestamps) {
    const invalidDraft = structuredClone(draft);
    invalidDraft.provenance.generatedAt = timestamp;
    assert.throws(
      () => validateDirectorPlan(invalidDraft, { requiredStatus: "ai-draft" }),
      /canonical RFC 3339 date-time/,
    );

    const invalidReview = structuredClone(review);
    invalidReview.reviewedAt = timestamp;
    assert.throws(
      () => applyHumanReview(draft, invalidReview, brief),
      /canonical RFC 3339 date-time/,
    );
  }

  const offsetDraft = structuredClone(draft);
  offsetDraft.provenance.generatedAt = "2026-08-31T13:49:09+08:00";
  assert.equal(
    validateDirectorPlan(offsetDraft, { requiredStatus: "ai-draft" }).provenance.generatedAt,
    "2026-08-31T13:49:09+08:00",
  );
  const fractionalReview = structuredClone(review);
  fractionalReview.reviewedAt = "2026-08-31T14:00:00.123456789+08:00";
  assert.equal(
    applyHumanReview(draft, fractionalReview, brief).humanReview.reviewedAt,
    "2026-08-31T14:00:00.123456789+08:00",
  );
});

test("a checksum-valid recorded fixture cannot replace the human brief rights", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-fixture-rights-"));
  const forgedPlan = structuredClone(await json(path.join(DEMO, "ai-draft-plan.json")));
  forgedPlan.manifestProposal.rights = {
    declaration: "A recorded model falsely replaces the human rights declaration.",
    sourceUrl: "https://malicious.example.test/forged-rights",
  };
  const bytes = Buffer.from(`${JSON.stringify(forgedPlan, null, 2)}\n`);
  const planFile = path.join(workspace, "forged-plan.json");
  const checksumFile = path.join(workspace, "forged-plan.sha256");
  await fs.writeFile(planFile, bytes);
  await fs.writeFile(checksumFile, `${sha256(bytes)}  forged-plan.json\n`);

  await assert.rejects(verifyRecordedFixture(
    planFile,
    checksumFile,
    path.join(DEMO, "brief.json"),
  ), /rights.*brief|brief.*rights/i);
});

test("a forged recorded plan cannot bypass brief binding through review and materialize", async () => {
  const brief = await json(path.join(DEMO, "brief.json"));
  const draft = structuredClone(await json(path.join(DEMO, "ai-draft-plan.json")));
  const review = await json(path.join(DEMO, "human-review.json"));
  draft.manifestProposal.rights = {
    declaration: "A forged draft replaces the operator-controlled rights declaration.",
    sourceUrl: "https://malicious.example.test/bypass-rights",
  };
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-bypass-"));
  const forgedPlanFile = path.join(workspace, "forged-plan.json");
  const reviewedOutput = path.join(workspace, "reviewed.json");
  await fs.writeFile(forgedPlanFile, `${JSON.stringify(draft, null, 2)}\n`);

  assert.throws(() => applyHumanReview(draft, review, brief), /brief.*rights|rights.*brief/i);
  await assert.rejects(execFileAsync(process.execPath, [
    DIRECTOR,
    "review",
    forgedPlanFile,
    path.join(DEMO, "human-review.json"),
    path.join(DEMO, "brief.json"),
    reviewedOutput,
  ]), (error) => {
    assert.match(error.stderr, /brief.*rights|rights.*brief/i);
    return true;
  });
  await assert.rejects(fs.access(reviewedOutput));

  await assert.rejects(execFileAsync(process.execPath, [
    DIRECTOR,
    "review",
    forgedPlanFile,
    path.join(DEMO, "human-review.json"),
    reviewedOutput,
  ]), (error) => {
    assert.match(error.stderr, /Usage:.*brief\.json/s);
    return true;
  });

  const attackerBrief = structuredClone(brief);
  attackerBrief.rights = structuredClone(draft.manifestProposal.rights);
  const attackerDraft = structuredClone(draft);
  attackerDraft.provenance.briefSha256 = sha256(stableJson(validateDirectorBrief(attackerBrief)));
  const attackerReviewed = applyHumanReview(attackerDraft, review, attackerBrief);
  const attackerReviewedFile = path.join(workspace, "attacker-reviewed.json");
  await fs.writeFile(attackerReviewedFile, `${JSON.stringify(attackerReviewed, null, 2)}\n`);

  await assert.rejects(
    materializeReviewedPlan(attackerReviewed, path.join(workspace, "pack"), brief),
    /brief digest|brief.*rights|rights.*brief/i,
  );
  await assert.rejects(execFileAsync(process.execPath, [
    DIRECTOR,
    "materialize",
    attackerReviewedFile,
    path.join(DEMO, "brief.json"),
    path.join(workspace, "cli-pack"),
  ]), (error) => {
    assert.match(error.stderr, /brief digest|brief.*rights|rights.*brief/i);
    return true;
  });
  await assert.rejects(execFileAsync(process.execPath, [
    DIRECTOR,
    "materialize",
    attackerReviewedFile,
    path.join(workspace, "cli-pack-without-brief"),
  ]), (error) => {
    assert.match(error.stderr, /Usage:.*brief\.json/s);
    return true;
  });
  await assert.rejects(fs.access(path.join(workspace, "pack", "bugfire-pack.json")));
  await assert.rejects(fs.access(path.join(workspace, "cli-pack", "bugfire-pack.json")));
});

test("director inputs and endpoint envelopes reject malformed UTF-8", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-utf8-"));
  const malformedPlan = path.join(workspace, "malformed-plan.json");
  await fs.writeFile(malformedPlan, Buffer.from([0x7b, 0xff, 0x7d]));
  await assert.rejects(verifyRecordedFixture(
    malformedPlan,
    path.join(DEMO, "ai-draft-plan.sha256"),
    path.join(DEMO, "brief.json"),
  ), /not valid UTF-8/i);

  const brief = await json(path.join(DEMO, "brief.json"));
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "test-secret-never-persist",
    model: "local-contract-model",
    fetchImpl: async () => byteResponse(Uint8Array.of(0xff)),
  }), /AI endpoint response is not valid UTF-8/i);
});

test("contest boards are offline 16:9 artifacts with rights-table hashes", async () => {
  const rights = await fs.readFile(path.join(PROJECT, "ASSET_RIGHTS.csv"), "utf8");
  const boardRoot = path.join(PROJECT, "contest", "bugfire", "boards");
  for (const filename of ["01-ai-draft.png", "02-human-rejection.png", "03-pack-preview.png"]) {
    const bytes = await fs.readFile(path.join(boardRoot, filename));
    assert.equal(bytes.subarray(1, 4).toString("ascii"), "PNG");
    assert.equal(bytes.readUInt32BE(16), 1920);
    assert.equal(bytes.readUInt32BE(20), 1080);
    const digest = (await import("node:crypto")).default.createHash("sha256").update(bytes).digest("hex");
    assert.match(rights, new RegExp(`${filename.replace(".", "\\.")}[^\\n]+${digest}`));
  }
  const sources = await Promise.all([
    fs.readFile(path.join(boardRoot, "source", "01-ai-draft.html"), "utf8"),
    fs.readFile(path.join(boardRoot, "source", "02-human-rejection.html"), "utf8"),
  ]);
  assert.doesNotMatch(sources.join("\n"), /(?:src|href)=["']https?:/i);
});

test("every public BUGFIRE documentation raster has a rights row and exact digest", async () => {
  const rights = await fs.readFile(path.join(PROJECT, "ASSET_RIGHTS.csv"), "utf8");
  assert.match(rights, /^repository_path,main_package_path,asset_type,/);
  const imageRoot = path.join(PROJECT, "docs", "images");
  const files = (await fs.readdir(imageRoot)).filter((file) => /^bugfire-.*\.png$/.test(file)).sort();
  assert.equal(files.length, 12);
  for (const file of files) {
    const repositoryPath = `docs/images/${file}`;
    const bytes = await fs.readFile(path.join(imageRoot, file));
    const digest = (await import("node:crypto")).default.createHash("sha256").update(bytes).digest("hex");
    const escapedPath = repositoryPath.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    assert.match(rights, new RegExp(`^${escapedPath},${escapedPath},[^\\n]+,${digest},`, "m"));
  }
  assert.match(rights, /bugfire-pages-preview\.png[^\n]+157add6/);
  assert.match(rights, /bugfire-social-card\.png[^\n]+157add6/);
  assert.match(rights, /bugfire-video-cover\.png[^\n]+b4118e9/);
});

test("human review must reject and materially replace exactly one decision surface", async () => {
  const draft = await json(path.join(DEMO, "ai-draft-plan.json"));
  const review = await json(path.join(DEMO, "human-review.json"));
  const brief = await json(path.join(DEMO, "brief.json"));
  const approved = applyHumanReview(draft, review, brief);
  assert.equal(approved.status, "human-approved");
  assert.equal(approved.humanReview.rejectedDecisionId, "alert-first-palette");
  assert.equal(approved.humanReview.originalDecision.manifestPatch["/theme/colors/accent"], "#ff7a1a");
  assert.equal(approved.manifestProposal.theme.colors.accent, "#35d9d1");
  assert.notEqual(
    stableJson(approved.humanReview.originalDecision),
    stableJson(approved.humanReview.replacementDecision),
  );

  const unchanged = structuredClone(review);
  unchanged.replacementDecision = approved.humanReview.originalDecision;
  await assert.rejects(async () => applyHumanReview(draft, unchanged, brief), /materially change/i);
});

test("approved plan materializes, then the independent pack validator builds it", async () => {
  const plan = await json(path.join(DEMO, "reviewed-plan.json"));
  const brief = await json(path.join(DEMO, "brief.json"));
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-build-"));
  const source = path.join(workspace, "source");
  const output = path.join(workspace, "output");
  await fs.mkdir(path.join(source, "assets"), { recursive: true });
  await fs.copyFile(path.join(DEMO, "assets", "background.png"), path.join(source, "assets", "background.png"));
  await fs.copyFile(path.join(DEMO, "assets", "pet-idle.png"), path.join(source, "assets", "pet-idle.png"));

  const materialized = await materializeReviewedPlan(plan, source, brief);
  assert.match(materialized.boundary, /AI proposes.*human.*deterministic/i);
  assert.equal((await fs.stat(path.join(source, "bugfire-pack.json"))).mode & 0o777, 0o600);
  assert.equal((await fs.stat(path.join(source, "director-report.json"))).mode & 0o777, 0o600);
  const validated = await validateBugfirePack(source);
  assert.equal(validated.pass, true);
  const built = await buildBugfirePack(source, output);
  assert.equal(built.pass, true);
  const theme = await json(path.join(output, "theme.json"));
  assert.equal(theme.colors.accent, "#35d9d1");
  assert.equal(theme.pet.name, "零号补丁兽");
  await fs.access(path.join(output, "pack-report.json"));
});

test("an AI draft cannot bypass the human gate and materialize", async () => {
  const draft = await json(path.join(DEMO, "ai-draft-plan.json"));
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-gate-"));
  await assert.rejects(materializeReviewedPlan(draft, workspace), /human-approved/i);
});

test("draft, review, and materialize outputs refuse to overwrite existing files", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-no-clobber-"));
  const existingOutput = path.join(workspace, "existing.json");
  const sentinel = "operator-owned output\n";
  await fs.writeFile(existingOutput, sentinel);

  for (const args of [
    ["draft-live", path.join(DEMO, "brief.json"), existingOutput, "--model", "unused-model"],
    [
      "review", path.join(DEMO, "ai-draft-plan.json"), path.join(DEMO, "human-review.json"),
      path.join(DEMO, "brief.json"), existingOutput,
    ],
  ]) {
    await assert.rejects(execFileAsync(process.execPath, [DIRECTOR, ...args], {
      env: { ...process.env, BUGFIRE_OPENAI_API_KEY: "" },
    }), (error) => {
      assert.match(error.stderr, /already exists; refusing to overwrite/i);
      return true;
    });
    assert.equal(await fs.readFile(existingOutput, "utf8"), sentinel);
  }

  const reviewed = await json(path.join(DEMO, "reviewed-plan.json"));
  const brief = await json(path.join(DEMO, "brief.json"));
  const manifestExists = path.join(workspace, "manifest-exists");
  await fs.mkdir(manifestExists);
  await fs.writeFile(path.join(manifestExists, "bugfire-pack.json"), sentinel);
  await assert.rejects(
    materializeReviewedPlan(reviewed, manifestExists, brief),
    /already exists; refusing to overwrite/i,
  );
  assert.equal(await fs.readFile(path.join(manifestExists, "bugfire-pack.json"), "utf8"), sentinel);
  await assert.rejects(fs.access(path.join(manifestExists, "director-report.json")));

  const reportExists = path.join(workspace, "report-exists");
  await fs.mkdir(reportExists);
  await fs.writeFile(path.join(reportExists, "director-report.json"), sentinel);
  await assert.rejects(
    materializeReviewedPlan(reviewed, reportExists, brief),
    /already exists; refusing to overwrite/i,
  );
  assert.equal(await fs.readFile(path.join(reportExists, "director-report.json"), "utf8"), sentinel);
  await assert.rejects(fs.access(path.join(reportExists, "bugfire-pack.json")));
});

test("live mode exercises both OpenAI-compatible API shapes without storing credentials", async (context) => {
  const brief = await json(path.join(DEMO, "brief.json"));
  const recorded = await json(path.join(DEMO, "ai-draft-plan.json"));
  const payload = {
    creativeDecisions: recorded.creativeDecisions,
    manifestProposal: recorded.manifestProposal,
    productionNotes: recorded.productionNotes,
  };
  const requestRecords = [];
  const server = http.createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    requestRecords.push({
      method: request.method,
      url: request.url,
      authorization: request.headers.authorization,
      body: JSON.parse(Buffer.concat(chunks).toString("utf8")),
    });
    response.writeHead(200, { "content-type": "application/json" });
    const envelope = request.url === "/v1/responses"
      ? { output_text: JSON.stringify(payload) }
      : { choices: [{ message: { content: JSON.stringify(payload) } }] };
    response.end(JSON.stringify(envelope));
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  context.after(() => new Promise((resolve) => server.close(resolve)));
  const address = server.address();

  const chatPlan = await draftWithOpenAI({
    brief,
    baseUrl: `http://127.0.0.1:${address.port}/v1`,
    apiKey: "test-secret-never-persist",
    model: "local-contract-model",
  });
  const responsesPlan = await draftWithOpenAI({
    brief,
    baseUrl: `http://127.0.0.1:${address.port}/v1`,
    apiKey: "test-secret-never-persist",
    model: "local-contract-model",
    apiMode: "responses",
  });

  assert.deepEqual(requestRecords.map(({ method }) => method), ["POST", "POST"]);
  assert.deepEqual(requestRecords.map(({ url }) => url), ["/v1/chat/completions", "/v1/responses"]);
  assert.deepEqual(requestRecords.map(({ authorization }) => authorization), [
    "Bearer test-secret-never-persist",
    "Bearer test-secret-never-persist",
  ]);
  assert.equal(requestRecords[0].body.response_format.type, "json_object");
  assert.equal(requestRecords[1].body.text.format.type, "json_object");
  for (const plan of [chatPlan, responsesPlan]) {
    assert.equal(plan.provenance.mode, "live-openai-compatible");
    assert.equal(plan.provenance.endpointOrigin, `http://127.0.0.1:${address.port}`);
    assert.doesNotMatch(JSON.stringify(plan), /test-secret-never-persist/);
    assert.equal(validateDirectorPlan(plan).status, "ai-draft");
  }
});

test("a malicious live endpoint cannot reflect the exact API key into any persisted plan field", async (context) => {
  const apiKey = "reflected-secret-must-never-persist-7f31";
  const brief = await json(path.join(DEMO, "brief.json"));
  const recorded = await json(path.join(DEMO, "ai-draft-plan.json"));
  const payload = {
    creativeDecisions: structuredClone(recorded.creativeDecisions),
    manifestProposal: structuredClone(recorded.manifestProposal),
    productionNotes: structuredClone(recorded.productionNotes),
  };
  payload.creativeDecisions[0].choice = apiKey;
  payload.manifestProposal.name = apiKey;
  payload.creativeDecisions[0].manifestPatch["/name"] = apiKey;

  const server = http.createServer(async (request, response) => {
    for await (const _chunk of request) {
      // Drain the request before replying so the child process observes a normal API exchange.
    }
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ choices: [{ message: { content: JSON.stringify(payload) } }] }));
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  context.after(() => new Promise((resolve) => server.close(resolve)));
  const address = server.address();
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-secret-"));
  const output = path.join(workspace, "malicious-plan.json");

  await assert.rejects(execFileAsync(process.execPath, [
    DIRECTOR,
    "draft-live",
    path.join(DEMO, "brief.json"),
    output,
    "--model",
    "local-contract-model",
    "--base-url",
    `http://127.0.0.1:${address.port}/v1`,
  ], {
    env: { ...process.env, BUGFIRE_OPENAI_API_KEY: apiKey },
  }), (error) => {
    assert.match(error.stderr, /secret|credential|persist/i);
    assert.doesNotMatch(`${error.stdout}\n${error.stderr}`, new RegExp(apiKey));
    return true;
  });
  await assert.rejects(fs.access(output));
});

test("malformed live JSON cannot reflect the exact API key through CLI parse errors", async (context) => {
  const apiKey = "test-key";
  const server = http.createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const requestBody = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    response.writeHead(200, { "content-type": "application/json" });
    if (requestBody.model === "malformed-envelope-model") {
      response.end(apiKey);
    } else {
      response.end(JSON.stringify({ choices: [{ message: { content: apiKey } }] }));
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  context.after(() => new Promise((resolve) => server.close(resolve)));
  const address = server.address();
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-parse-secret-"));
  const cases = [
    ["malformed-envelope-model", "envelope.json", /endpoint envelope was not valid JSON/i],
    ["malformed-content-model", "content.json", /AI response was not valid JSON/i],
  ];

  for (const [model, filename, expectedError] of cases) {
    const output = path.join(workspace, filename);
    await assert.rejects(execFileAsync(process.execPath, [
      DIRECTOR,
      "draft-live",
      path.join(DEMO, "brief.json"),
      output,
      "--model",
      model,
      "--base-url",
      `http://127.0.0.1:${address.port}/v1`,
    ], {
      env: { ...process.env, BUGFIRE_OPENAI_API_KEY: apiKey },
    }), (error) => {
      assert.match(error.stderr, expectedError);
      assert.doesNotMatch(`${error.stdout}\n${error.stderr}`, new RegExp(apiKey));
      return true;
    });
    await assert.rejects(fs.access(output));
  }
});

test("AI manifest rights are forcibly derived from the human brief", async () => {
  const brief = await json(path.join(DEMO, "brief.json"));
  const recorded = await json(path.join(DEMO, "ai-draft-plan.json"));
  const payload = {
    creativeDecisions: recorded.creativeDecisions,
    manifestProposal: {
      ...recorded.manifestProposal,
      rights: {
        declaration: "The model falsely claims ownership of every supplied asset.",
        sourceUrl: "https://malicious.example.test/fabricated-rights",
      },
    },
    productionNotes: recorded.productionNotes,
  };

  const plan = await draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "rights-boundary-test-key",
    model: "local-contract-model",
    fetchImpl: async () => chatResponse(payload),
  });

  assert.deepEqual(plan.manifestProposal.rights, brief.rights);
  assert.doesNotMatch(JSON.stringify(plan), /malicious\.example|falsely claims ownership/i);
});

test("materialize recomputes and enforces the canonical AI draft digest", async () => {
  const reviewed = await json(path.join(DEMO, "reviewed-plan.json"));
  const brief = await json(path.join(DEMO, "brief.json"));
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-digest-"));
  const forged = structuredClone(reviewed);
  forged.humanReview.draftSha256 = "0".repeat(64);
  await assert.rejects(
    materializeReviewedPlan(forged, path.join(workspace, "forged"), brief),
    /draftSha256|draft digest|canonical draft/i,
  );
  await assert.rejects(fs.access(path.join(workspace, "forged", "bugfire-pack.json")));

  const tampered = structuredClone(reviewed);
  tampered.productionNotes = [...tampered.productionNotes, "Unbound post-review mutation"];
  await assert.rejects(
    materializeReviewedPlan(tampered, path.join(workspace, "tampered"), brief),
    /draftSha256|draft digest|canonical draft/i,
  );
});

test("materialize refuses a symlink ancestor before creating pack artifacts", async () => {
  const reviewed = await json(path.join(DEMO, "reviewed-plan.json"));
  const brief = await json(path.join(DEMO, "brief.json"));
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-symlink-"));
  const outside = path.join(workspace, "outside");
  const linked = path.join(workspace, "linked");
  await fs.mkdir(outside);
  await fs.symlink(outside, linked, "dir");

  await assert.rejects(
    materializeReviewedPlan(reviewed, path.join(linked, "pack"), brief),
    /symbolic link|symlink/i,
  );
  await assert.rejects(fs.access(path.join(outside, "pack", "bugfire-pack.json")));
});

test("director CLI covers fixture verification, review, validation, and materialization", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-cli-"));
  const reviewed = path.join(workspace, "reviewed.json");
  const pack = path.join(workspace, "pack");

  const verified = JSON.parse((await execFileAsync(process.execPath, [
    DIRECTOR,
    "verify-fixture",
    path.join(DEMO, "ai-draft-plan.json"),
    path.join(DEMO, "ai-draft-plan.sha256"),
    path.join(DEMO, "brief.json"),
  ])).stdout);
  assert.equal(verified.pass, true);

  const reviewResult = JSON.parse((await execFileAsync(process.execPath, [
    DIRECTOR,
    "review",
    path.join(DEMO, "ai-draft-plan.json"),
    path.join(DEMO, "human-review.json"),
    path.join(DEMO, "brief.json"),
    reviewed,
  ])).stdout);
  assert.equal(reviewResult.status, "human-approved");

  const validation = JSON.parse((await execFileAsync(process.execPath, [
    DIRECTOR,
    "validate",
    reviewed,
  ])).stdout);
  assert.equal(validation.status, "human-approved");

  const materialized = JSON.parse((await execFileAsync(process.execPath, [
    DIRECTOR,
    "materialize",
    reviewed,
    path.join(DEMO, "brief.json"),
    pack,
  ])).stdout);
  assert.equal(materialized.pass, true);
  await fs.access(path.join(pack, "bugfire-pack.json"));
  await fs.access(path.join(pack, "director-report.json"));

  await assert.rejects(execFileAsync(process.execPath, [
    DIRECTOR,
    "verify-fixture",
    path.join(DEMO, "ai-draft-plan.json"),
    path.join(DEMO, "ai-draft-plan.sha256"),
  ]), (error) => {
    assert.match(error.stderr, /Usage:.*brief\.json/s);
    return true;
  });
  await assert.rejects(execFileAsync(process.execPath, [DIRECTOR, "unknown"]), (error) => {
    assert.match(error.stderr, /Usage:/);
    return true;
  });
});

test("director rejects malformed briefs, endpoints, API envelopes, and fixture checksums", async () => {
  const brief = await json(path.join(DEMO, "brief.json"));
  assert.throws(() => validateDirectorBrief(null), /brief must be an object/i);
  assert.throws(() => validateDirectorBrief({ ...brief, unexpected: true }), /unsupported fields/i);
  assert.throws(() => validateDirectorBrief({
    ...brief,
    rights: { ...brief.rights, sourceUrl: "http://insecure.example.test/art" },
  }), /must use HTTPS/i);

  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "not a URL",
    apiKey: "test-key",
    model: "test-model",
  }), /valid URL/i);
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "test-key",
    model: "test-model",
    apiMode: "unsupported",
  }), /api mode/i);
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "test-key",
    model: "test-model",
    fetchImpl: async () => byteResponse("test-key quota exceeded", { ok: false, status: 429 }),
  }), (error) => {
    assert.match(error.message, /HTTP 429.*\[REDACTED\]/i);
    assert.doesNotMatch(error.message, /test-key/);
    return true;
  });
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "test-key",
    model: "test-model",
    fetchImpl: async () => byteResponse("not-json"),
  }), /envelope was not valid JSON/i);
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "test-key",
    model: "test-model",
    fetchImpl: async () => byteResponse(JSON.stringify({ choices: [] })),
  }), /no supported text payload/i);

  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-checksum-"));
  const checksum = path.join(workspace, "wrong.sha256");
  await fs.writeFile(checksum, `${"0".repeat(64)}  ai-draft-plan.json\n`);
  await assert.rejects(verifyRecordedFixture(
    path.join(DEMO, "ai-draft-plan.json"),
    checksum,
    path.join(DEMO, "brief.json"),
  ), /checksum mismatch/i);
});

test("director validators reject broken plan, provenance, and review bindings", async () => {
  const draft = await json(path.join(DEMO, "ai-draft-plan.json"));
  const review = await json(path.join(DEMO, "human-review.json"));
  const brief = await json(path.join(DEMO, "brief.json"));

  assert.throws(() => validateDirectorPlan({}), /schema|artifactType/i);
  assert.throws(() => validateDirectorPlan({
    ...draft,
    creativeDecisions: draft.creativeDecisions.slice(0, 1),
  }), /2 to 8/i);
  const duplicate = structuredClone(draft);
  duplicate.creativeDecisions[1].id = duplicate.creativeDecisions[0].id;
  assert.throws(() => validateDirectorPlan(duplicate), /unique/i);
  const detached = structuredClone(draft);
  detached.manifestProposal.name = "A manifest value detached from its decision";
  assert.throws(() => validateDirectorPlan(detached), /not reflected/i);
  const liveWithoutOrigin = structuredClone(draft);
  liveWithoutOrigin.provenance.mode = "live-openai-compatible";
  liveWithoutOrigin.provenance.endpointOrigin = "";
  assert.throws(() => validateDirectorPlan(liveWithoutOrigin), /endpoint origin/i);
  const fixtureWithOrigin = structuredClone(draft);
  fixtureWithOrigin.provenance.endpointOrigin = "https://api.example.test";
  assert.throws(() => validateDirectorPlan(fixtureWithOrigin), /must not imply a live endpoint/i);
  const invalidDigest = structuredClone(draft);
  invalidDigest.provenance.briefSha256 = "not-a-digest";
  assert.throws(() => validateDirectorPlan(invalidDigest), /SHA-256 digest/i);

  const unknownDecision = structuredClone(review);
  unknownDecision.rejectedDecisionId = "does-not-exist";
  unknownDecision.replacementDecision.id = "does-not-exist";
  assert.throws(() => applyHumanReview(draft, unknownDecision, brief), /does not exist/i);
  const changedId = structuredClone(review);
  changedId.replacementDecision.id = "different-id";
  assert.throws(() => applyHumanReview(draft, changedId, brief), /keep the rejected decision id/i);
  const changedSurface = structuredClone(review);
  changedSurface.replacementDecision.manifestPatch = {
    "/theme/colors/accent": "#35d9d1",
  };
  assert.throws(() => applyHumanReview(draft, changedSurface, brief), /exactly the same manifest fields/i);
});

test("live response size and JSON-content boundaries fail closed", async () => {
  const brief = await json(path.join(DEMO, "brief.json"));
  let preflightRead = false;
  let preflightCancelled = false;
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "test-key",
    model: "test-model",
    fetchImpl: async () => ({
      ok: true,
      status: 200,
      headers: { get: () => String(1024 * 1024 + 1) },
      body: {
        cancel: async () => { preflightCancelled = true; },
        getReader: () => {
          preflightRead = true;
          throw new Error("oversized Content-Length must be rejected before streaming");
        },
      },
    }),
  }), /response exceeded/i);
  assert.equal(preflightRead, false);
  assert.equal(preflightCancelled, true);
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "test-key",
    model: "test-model",
    fetchImpl: async () => byteResponse(JSON.stringify({
      choices: [{ message: { content: "not-json" } }],
    })),
  }), /AI response was not valid JSON/i);

  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-input-errors-"));
  const malformed = path.join(workspace, "malformed.json");
  await fs.writeFile(malformed, "{not-json", "utf8");
  await assert.rejects(verifyRecordedFixture(
    malformed,
    path.join(DEMO, "ai-draft-plan.sha256"),
    path.join(DEMO, "brief.json"),
  ), /not valid JSON/i);
  await assert.rejects(verifyRecordedFixture(
    path.join(workspace, "missing.json"),
    path.join(DEMO, "ai-draft-plan.sha256"),
    path.join(DEMO, "brief.json"),
  ), /is missing/i);
});

test("a loopback response is cancelled while streaming just beyond the byte limit", async (context) => {
  const brief = await json(path.join(DEMO, "brief.json"));
  const chunk = Buffer.alloc(64 * 1024, 0x20);
  const plannedBytes = 2 * 1024 * 1024;
  let attemptedBytes = 0;
  let completed = false;
  let closedBeforeCompletion = false;
  let resolveClosed;
  const closed = new Promise((resolve) => { resolveClosed = resolve; });
  const server = http.createServer(async (request, response) => {
    for await (const _chunk of request) {
      // Drain the request before sending a deliberately oversized chunked response.
    }
    response.writeHead(200, { "content-type": "application/json" });
    response.once("close", () => {
      closedBeforeCompletion = !completed;
      resolveClosed();
    });
    while (!response.destroyed && attemptedBytes < plannedBytes) {
      response.write(chunk);
      attemptedBytes += chunk.length;
      await new Promise((resolve) => setTimeout(resolve, 4));
    }
    if (!response.destroyed) {
      completed = true;
      response.end();
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  context.after(() => new Promise((resolve) => {
    server.close(resolve);
    server.closeAllConnections?.();
  }));
  const address = server.address();

  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: `http://127.0.0.1:${address.port}/v1`,
    apiKey: "stream-limit-test-key",
    model: "local-contract-model",
  }), /response exceeded/i);
  await Promise.race([
    closed,
    new Promise((_, reject) => setTimeout(() => reject(new Error("stream was not cancelled")), 2_000)),
  ]);
  assert.equal(closedBeforeCompletion, true);
  assert.ok(attemptedBytes < plannedBytes, `server sent all ${attemptedBytes} planned bytes`);
});

test("live mode fails closed without a key and rejects non-TLS remote endpoints", async () => {
  const brief = await json(path.join(DEMO, "brief.json"));
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "https://api.example.test/v1",
    apiKey: "",
    model: "test-model",
  }), /no live AI generation was performed/i);
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://api.example.test/v1",
    apiKey: "secret",
    model: "test-model",
  }), /HTTPS/i);
});
