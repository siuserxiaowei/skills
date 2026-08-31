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
  stableJson,
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

test("director inputs and endpoint envelopes reject malformed UTF-8", async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-utf8-"));
  const malformedPlan = path.join(workspace, "malformed-plan.json");
  await fs.writeFile(malformedPlan, Buffer.from([0x7b, 0xff, 0x7d]));
  await assert.rejects(verifyRecordedFixture(
    malformedPlan,
    path.join(DEMO, "ai-draft-plan.sha256"),
  ), /not valid UTF-8/i);

  const brief = await json(path.join(DEMO, "brief.json"));
  await assert.rejects(draftWithOpenAI({
    brief,
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "test-secret-never-persist",
    model: "local-contract-model",
    fetchImpl: async () => ({
      ok: true,
      status: 200,
      arrayBuffer: async () => Uint8Array.of(0xff).buffer,
    }),
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

test("human review must reject and materially replace exactly one decision surface", async () => {
  const draft = await json(path.join(DEMO, "ai-draft-plan.json"));
  const review = await json(path.join(DEMO, "human-review.json"));
  const approved = applyHumanReview(draft, review);
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
  await assert.rejects(async () => applyHumanReview(draft, unchanged), /materially change/i);
});

test("approved plan materializes, then the independent pack validator builds it", async () => {
  const plan = await json(path.join(DEMO, "reviewed-plan.json"));
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), "bugfire-director-build-"));
  const source = path.join(workspace, "source");
  const output = path.join(workspace, "output");
  await fs.mkdir(path.join(source, "assets"), { recursive: true });
  await fs.copyFile(path.join(DEMO, "assets", "background.png"), path.join(source, "assets", "background.png"));
  await fs.copyFile(path.join(DEMO, "assets", "pet-idle.png"), path.join(source, "assets", "pet-idle.png"));

  const materialized = await materializeReviewedPlan(plan, source);
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
    ["review", path.join(DEMO, "ai-draft-plan.json"), path.join(DEMO, "human-review.json"), existingOutput],
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
  const manifestExists = path.join(workspace, "manifest-exists");
  await fs.mkdir(manifestExists);
  await fs.writeFile(path.join(manifestExists, "bugfire-pack.json"), sentinel);
  await assert.rejects(materializeReviewedPlan(reviewed, manifestExists), /already exists; refusing to overwrite/i);
  assert.equal(await fs.readFile(path.join(manifestExists, "bugfire-pack.json"), "utf8"), sentinel);
  await assert.rejects(fs.access(path.join(manifestExists, "director-report.json")));

  const reportExists = path.join(workspace, "report-exists");
  await fs.mkdir(reportExists);
  await fs.writeFile(path.join(reportExists, "director-report.json"), sentinel);
  await assert.rejects(materializeReviewedPlan(reviewed, reportExists), /already exists; refusing to overwrite/i);
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
