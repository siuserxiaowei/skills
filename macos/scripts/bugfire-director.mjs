import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { TextDecoder } from "node:util";

import { validateBugfireManifest } from "./bugfire-pack.mjs";

const MAX_JSON_BYTES = 256 * 1024;
const MAX_AI_RESPONSE_BYTES = 1024 * 1024;
const MAX_DECISIONS = 8;
const MODES = new Set(["recorded-agent-fixture", "live-openai-compatible"]);
const STATUSES = new Set(["ai-draft", "human-approved"]);
const API_MODES = new Set(["chat-completions", "responses"]);
const UTF8 = new TextDecoder("utf-8", { fatal: true });
const ALLOWED_PATCH_PATHS = new Set([
  "/name",
  "/theme/tagline",
  "/theme/quote",
  "/theme/colors/background",
  "/theme/colors/panel",
  "/theme/colors/panelAlt",
  "/theme/colors/accent",
  "/theme/colors/accentAlt",
  "/theme/colors/secondary",
  "/theme/colors/highlight",
  "/theme/colors/text",
  "/theme/colors/muted",
  "/pet/name",
  "/pet/seasonLabel",
  "/gameplay/rewardXp",
  "/gameplay/sayings",
  "/gameplay/quests",
  "/gameplay/certificateTitle",
]);

function invalid(message) {
  throw new TypeError(`Invalid BUGFIRE director artifact: ${message}`);
}

function plainObject(value, name) {
  if (!value || typeof value !== "object" || Array.isArray(value)) invalid(`${name} must be an object`);
  return value;
}

function exactKeys(value, allowed, name) {
  const unexpected = Object.keys(value).filter((key) => !allowed.includes(key));
  if (unexpected.length) invalid(`${name} has unsupported fields: ${unexpected.join(", ")}`);
}

function text(value, name, maximum = 400) {
  if (typeof value !== "string" || !value.trim()) invalid(`${name} must be non-empty text`);
  const normalized = value.trim();
  if (normalized.length > maximum || /\p{C}/u.test(normalized)) invalid(`${name} is invalid or too long`);
  return normalized;
}

function stringList(value, name, { minimum = 1, maximum = 12, itemMaximum = 240 } = {}) {
  if (!Array.isArray(value) || value.length < minimum || value.length > maximum) {
    invalid(`${name} must contain ${minimum} to ${maximum} entries`);
  }
  return value.map((item, index) => text(item, `${name}[${index}]`, itemMaximum));
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stableValue(value[key])]));
  }
  return value;
}

export function stableJson(value) {
  return JSON.stringify(stableValue(value));
}

export function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function assertNoExactSecrets(value, secrets, name) {
  const exactSecrets = secrets.filter((secret) => typeof secret === "string" && secret.length > 0);
  if (!exactSecrets.length) return;
  const visit = (candidate) => {
    if (typeof candidate === "string") {
      if (exactSecrets.some((secret) => candidate.includes(secret))) {
        invalid(`${name} contains an exact credential value and cannot be persisted`);
      }
      return;
    }
    if (Array.isArray(candidate)) {
      for (const entry of candidate) visit(entry);
      return;
    }
    if (candidate && typeof candidate === "object") {
      for (const [key, entry] of Object.entries(candidate)) {
        visit(key);
        visit(entry);
      }
    }
  };
  visit(value);
}

function decodeUtf8(bytes, name) {
  try {
    return UTF8.decode(bytes);
  } catch {
    invalid(`${name} is not valid UTF-8`);
  }
}

async function readJson(file, name) {
  const absolute = path.resolve(file);
  const entry = await fs.lstat(absolute).catch((error) => {
    if (error?.code === "ENOENT") invalid(`${name} is missing: ${absolute}`);
    throw error;
  });
  if (!entry.isFile() || entry.isSymbolicLink() || entry.size < 2 || entry.size > MAX_JSON_BYTES) {
    invalid(`${name} must be a regular JSON file no larger than ${MAX_JSON_BYTES} bytes`);
  }
  const bytes = await fs.readFile(absolute);
  try {
    return { absolute, bytes, value: JSON.parse(decodeUtf8(bytes, name)) };
  } catch (error) {
    if (error instanceof TypeError && error.message.startsWith("Invalid BUGFIRE director artifact:")) throw error;
    invalid(`${name} is not valid JSON: ${error.message}`);
  }
}

async function assertOutputAbsent(file, name) {
  const absolute = path.resolve(file);
  const entry = await fs.lstat(absolute).catch((error) => {
    if (error?.code === "ENOENT") return null;
    throw error;
  });
  if (entry) invalid(`${name} already exists; refusing to overwrite: ${absolute}`);
  return absolute;
}

async function writeJsonNoClobber(file, value, name, { secrets = [] } = {}) {
  assertNoExactSecrets(value, secrets, name);
  const absolute = path.resolve(file);
  await fs.mkdir(path.dirname(absolute), { recursive: true, mode: 0o700 });
  const temporary = `${absolute}.${process.pid}.${crypto.randomBytes(8).toString("hex")}.tmp`;
  let handle;
  try {
    handle = await fs.open(temporary, "wx", 0o600);
    await handle.writeFile(`${JSON.stringify(value, null, 2)}\n`, "utf8");
    await handle.sync();
    await handle.close();
    handle = null;
    try {
      await fs.link(temporary, absolute);
    } catch (error) {
      if (error?.code === "EEXIST") invalid(`${name} already exists; refusing to overwrite: ${absolute}`);
      throw error;
    }
  } finally {
    if (handle) await handle.close().catch(() => {});
    await fs.rm(temporary, { force: true }).catch(() => {});
  }
  return absolute;
}

export function validateDirectorBrief(raw) {
  const brief = plainObject(raw, "brief");
  exactKeys(brief, [
    "schemaVersion", "name", "audience", "purpose", "character", "visualDirection",
    "constraints", "rights",
  ], "brief");
  if (brief.schemaVersion !== 1) invalid("brief.schemaVersion must be 1");
  const rights = plainObject(brief.rights, "brief.rights");
  exactKeys(rights, ["declaration", "sourceUrl"], "brief.rights");
  const sourceUrl = rights.sourceUrl === "" ? "" : text(rights.sourceUrl, "brief.rights.sourceUrl", 500);
  if (sourceUrl && !/^https:\/\//i.test(sourceUrl)) invalid("brief.rights.sourceUrl must use HTTPS");
  return {
    schemaVersion: 1,
    name: text(brief.name, "brief.name", 80),
    audience: text(brief.audience, "brief.audience", 240),
    purpose: text(brief.purpose, "brief.purpose", 400),
    character: text(brief.character, "brief.character", 600),
    visualDirection: text(brief.visualDirection, "brief.visualDirection", 600),
    constraints: stringList(brief.constraints, "brief.constraints", { maximum: 16, itemMaximum: 240 }),
    rights: {
      declaration: text(rights.declaration, "brief.rights.declaration", 240),
      sourceUrl,
    },
  };
}

function validatePatch(raw, name) {
  const patch = plainObject(raw, name);
  const entries = Object.entries(patch);
  if (!entries.length || entries.length > 12) invalid(`${name} must contain 1 to 12 fields`);
  for (const [pointer, value] of entries) {
    if (!ALLOWED_PATCH_PATHS.has(pointer)) invalid(`${name} cannot modify ${pointer}`);
    if (value === undefined || typeof value === "function" || typeof value === "symbol") {
      invalid(`${name}.${pointer} has an unsupported value`);
    }
  }
  return structuredClone(patch);
}

function validateDecision(raw, name) {
  const decision = plainObject(raw, name);
  exactKeys(decision, ["id", "title", "choice", "rationale", "manifestPatch"], name);
  const id = text(decision.id, `${name}.id`, 64);
  if (!/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/.test(id)) invalid(`${name}.id must be lowercase hyphen-case`);
  return {
    id,
    title: text(decision.title, `${name}.title`, 100),
    choice: text(decision.choice, `${name}.choice`, 400),
    rationale: text(decision.rationale, `${name}.rationale`, 600),
    manifestPatch: validatePatch(decision.manifestPatch, `${name}.manifestPatch`),
  };
}

function validateProvenance(raw) {
  const provenance = plainObject(raw, "provenance");
  exactKeys(provenance, [
    "mode", "provider", "model", "generatedAt", "briefSha256", "promptSha256",
    "endpointOrigin", "sourceNotice",
  ], "provenance");
  if (!MODES.has(provenance.mode)) invalid("provenance.mode is unsupported");
  const generatedAt = text(provenance.generatedAt, "provenance.generatedAt", 40);
  if (Number.isNaN(Date.parse(generatedAt))) invalid("provenance.generatedAt must be an ISO date-time");
  for (const field of ["briefSha256", "promptSha256"]) {
    if (typeof provenance[field] !== "string" || !/^[a-f0-9]{64}$/.test(provenance[field])) {
      invalid(`provenance.${field} must be a SHA-256 digest`);
    }
  }
  const endpointOrigin = provenance.endpointOrigin === "" ? "" : text(
    provenance.endpointOrigin, "provenance.endpointOrigin", 300,
  );
  if (provenance.mode === "live-openai-compatible" && !endpointOrigin) {
    invalid("live provenance must record an endpoint origin");
  }
  if (provenance.mode === "recorded-agent-fixture" && endpointOrigin) {
    invalid("a recorded fixture must not imply a live endpoint");
  }
  return {
    mode: provenance.mode,
    provider: text(provenance.provider, "provenance.provider", 120),
    model: text(provenance.model, "provenance.model", 120),
    generatedAt,
    briefSha256: provenance.briefSha256,
    promptSha256: provenance.promptSha256,
    endpointOrigin,
    sourceNotice: text(provenance.sourceNotice, "provenance.sourceNotice", 600),
  };
}

function validateHumanReview(raw) {
  const review = plainObject(raw, "humanReview");
  exactKeys(review, [
    "reviewer", "reviewedAt", "rejectedDecisionId", "reason", "originalDecision",
    "replacementDecision", "draftSha256",
  ], "humanReview");
  const reviewedAt = text(review.reviewedAt, "humanReview.reviewedAt", 40);
  if (Number.isNaN(Date.parse(reviewedAt))) invalid("humanReview.reviewedAt must be an ISO date-time");
  if (!/^[a-f0-9]{64}$/.test(review.draftSha256 || "")) invalid("humanReview.draftSha256 is invalid");
  return {
    reviewer: text(review.reviewer, "humanReview.reviewer", 100),
    reviewedAt,
    rejectedDecisionId: text(review.rejectedDecisionId, "humanReview.rejectedDecisionId", 64),
    reason: text(review.reason, "humanReview.reason", 600),
    originalDecision: validateDecision(review.originalDecision, "humanReview.originalDecision"),
    replacementDecision: validateDecision(review.replacementDecision, "humanReview.replacementDecision"),
    draftSha256: review.draftSha256,
  };
}

export function validateDirectorPlan(raw, { requiredStatus } = {}) {
  const plan = plainObject(raw, "plan");
  exactKeys(plan, [
    "schemaVersion", "artifactType", "status", "provenance", "creativeDecisions",
    "manifestProposal", "productionNotes", "humanReview",
  ], "plan");
  if (plan.schemaVersion !== 1 || plan.artifactType !== "bugfire-character-director-plan") {
    invalid("plan schema or artifactType is unsupported");
  }
  if (!STATUSES.has(plan.status) || (requiredStatus && plan.status !== requiredStatus)) {
    invalid(`plan.status must be ${requiredStatus || "ai-draft or human-approved"}`);
  }
  if (!Array.isArray(plan.creativeDecisions) || plan.creativeDecisions.length < 2 ||
      plan.creativeDecisions.length > MAX_DECISIONS) {
    invalid(`creativeDecisions must contain 2 to ${MAX_DECISIONS} entries`);
  }
  const decisions = plan.creativeDecisions.map((entry, index) => (
    validateDecision(entry, `creativeDecisions[${index}]`)
  ));
  if (new Set(decisions.map(({ id }) => id)).size !== decisions.length) invalid("decision ids must be unique");
  const humanReview = plan.status === "human-approved"
    ? validateHumanReview(plan.humanReview)
    : null;
  if (plan.status === "ai-draft" && plan.humanReview !== null) invalid("AI drafts must have humanReview: null");
  if (humanReview && !decisions.some(({ id }) => id === humanReview.rejectedDecisionId)) {
    invalid("humanReview must reference a decision retained in the reviewed plan");
  }
  if (humanReview) {
    const replacement = decisions.find(({ id }) => id === humanReview.rejectedDecisionId);
    if (humanReview.originalDecision.id !== humanReview.rejectedDecisionId ||
        humanReview.replacementDecision.id !== humanReview.rejectedDecisionId ||
        stableJson(replacement) !== stableJson(humanReview.replacementDecision)) {
      invalid("humanReview decisions are inconsistent with the reviewed plan");
    }
    const originalPaths = Object.keys(humanReview.originalDecision.manifestPatch).sort();
    const replacementPaths = Object.keys(humanReview.replacementDecision.manifestPatch).sort();
    if (stableJson(originalPaths) !== stableJson(replacementPaths) ||
        stableJson(humanReview.originalDecision.manifestPatch) ===
          stableJson(humanReview.replacementDecision.manifestPatch)) {
      invalid("humanReview must record a material same-surface replacement");
    }
  }
  const manifestProposal = validateBugfireManifest(plan.manifestProposal);
  const valueAtPointer = (pointer) => pointer.slice(1).split("/")
    .reduce((value, segment) => value?.[segment], manifestProposal);
  for (const decision of decisions) {
    for (const [pointer, value] of Object.entries(decision.manifestPatch)) {
      if (stableJson(valueAtPointer(pointer)) !== stableJson(value)) {
        invalid(`decision ${decision.id} is not reflected in manifestProposal at ${pointer}`);
      }
    }
  }
  const provenance = validateProvenance(plan.provenance);
  const productionNotes = stringList(
    plan.productionNotes, "productionNotes", { maximum: 16, itemMaximum: 400 },
  );
  const validated = {
    schemaVersion: 1,
    artifactType: "bugfire-character-director-plan",
    status: plan.status,
    provenance,
    creativeDecisions: decisions,
    manifestProposal,
    productionNotes,
    humanReview,
  };
  if (humanReview) {
    const originalDecisions = structuredClone(decisions);
    originalDecisions[originalDecisions.findIndex(({ id }) => id === humanReview.rejectedDecisionId)] =
      humanReview.originalDecision;
    const canonicalDraft = validateDirectorPlan({
      ...validated,
      status: "ai-draft",
      creativeDecisions: originalDecisions,
      manifestProposal: applyPatch(manifestProposal, humanReview.originalDecision.manifestPatch),
      humanReview: null,
    }, { requiredStatus: "ai-draft" });
    if (humanReview.draftSha256 !== sha256(stableJson(canonicalDraft))) {
      invalid("humanReview.draftSha256 does not match the reconstructed canonical draft");
    }
  }
  return validated;
}

function validatePlanBriefBinding(plan, rawBrief, stage) {
  if (!rawBrief) invalid(`${stage} requires the operator-controlled human brief`);
  const brief = validateDirectorBrief(rawBrief);
  if (sha256(stableJson(brief)) !== plan.provenance.briefSha256) {
    invalid(`${stage} brief digest does not match the director plan`);
  }
  if (stableJson(plan.manifestProposal.rights) !== stableJson(brief.rights)) {
    invalid(`${stage} plan rights do not exactly match the validated human brief rights`);
  }
  return brief;
}

function setJsonPointer(target, pointer, value) {
  const segments = pointer.slice(1).split("/");
  let cursor = target;
  for (const segment of segments.slice(0, -1)) {
    if (!Object.hasOwn(cursor, segment) || !cursor[segment] || typeof cursor[segment] !== "object") {
      invalid(`manifest patch target does not exist: ${pointer}`);
    }
    cursor = cursor[segment];
  }
  cursor[segments.at(-1)] = structuredClone(value);
}

function applyPatch(manifest, patch) {
  const updated = structuredClone(manifest);
  for (const [pointer, value] of Object.entries(patch)) setJsonPointer(updated, pointer, value);
  return validateBugfireManifest(updated);
}

export function directorPrompt() {
  return [
    "You are BUGFIRE Character Director. Turn an original-character brief into a structured creative plan.",
    "Return JSON only with creativeDecisions, manifestProposal, and productionNotes.",
    "The deterministic pack validator, not you, decides whether the output is installable.",
    "Do not claim asset ownership, live validation, installation, testing, or user approval.",
    "Every creative decision needs id, title, choice, rationale, and manifestPatch.",
    `manifestPatch keys may only be: ${[...ALLOWED_PATCH_PATHS].join(", ")}.`,
    "manifestProposal must be Bugfire Pack schemaVersion 1 and use local assets/background.png and assets/pet-idle.png.",
    "Keep every string concise. Use lower-case hyphen identifiers and six-digit hex colors.",
  ].join("\n");
}

function validateAiPayload(raw, briefRights) {
  const payload = plainObject(raw, "AI response");
  exactKeys(payload, ["creativeDecisions", "manifestProposal", "productionNotes"], "AI response");
  const manifestProposal = structuredClone(plainObject(payload.manifestProposal, "AI response.manifestProposal"));
  manifestProposal.rights = structuredClone(briefRights);
  const provisional = {
    schemaVersion: 1,
    artifactType: "bugfire-character-director-plan",
    status: "ai-draft",
    provenance: {
      mode: "recorded-agent-fixture",
      provider: "validation-placeholder",
      model: "validation-placeholder",
      generatedAt: "2000-01-01T00:00:00.000Z",
      briefSha256: "0".repeat(64),
      promptSha256: "0".repeat(64),
      endpointOrigin: "",
      sourceNotice: "Validation placeholder; replaced before an artifact is written.",
    },
    creativeDecisions: payload.creativeDecisions,
    manifestProposal,
    productionNotes: payload.productionNotes,
    humanReview: null,
  };
  const validated = validateDirectorPlan(provisional, { requiredStatus: "ai-draft" });
  return {
    creativeDecisions: validated.creativeDecisions,
    manifestProposal: validated.manifestProposal,
    productionNotes: validated.productionNotes,
  };
}

function safeEndpoint(baseUrl, apiMode) {
  if (!API_MODES.has(apiMode)) invalid(`api mode must be one of: ${[...API_MODES].join(", ")}`);
  let url;
  try {
    url = new URL(baseUrl);
  } catch {
    invalid("base URL is not a valid URL");
  }
  const loopback = new Set(["127.0.0.1", "localhost", "[::1]"]).has(url.hostname);
  if (url.protocol !== "https:" && !(url.protocol === "http:" && loopback)) {
    invalid("AI endpoint must use HTTPS, except HTTP loopback endpoints used for local models/tests");
  }
  url.username = "";
  url.password = "";
  const suffix = apiMode === "responses" ? "responses" : "chat/completions";
  url.pathname = `${url.pathname.replace(/\/$/, "")}/${suffix}`;
  url.search = "";
  url.hash = "";
  return url;
}

function responseText(payload, apiMode) {
  if (apiMode === "chat-completions") {
    const content = payload?.choices?.[0]?.message?.content;
    if (typeof content === "string") return content;
  } else {
    if (typeof payload?.output_text === "string") return payload.output_text;
    const textPart = payload?.output?.flatMap((item) => item?.content || [])
      .find((item) => typeof item?.text === "string");
    if (textPart) return textPart.text;
  }
  invalid("AI endpoint returned no supported text payload");
}

function responseLimitError() {
  return new Error(`AI endpoint response exceeded ${MAX_AI_RESPONSE_BYTES} bytes`);
}

async function readBoundedResponse(response) {
  const contentLength = response.headers?.get?.("content-length");
  const normalizedLength = typeof contentLength === "string" ? contentLength.trim() : "";
  if (/^\d+$/.test(normalizedLength) &&
      BigInt(normalizedLength) > BigInt(MAX_AI_RESPONSE_BYTES)) {
    await response.body?.cancel?.().catch(() => {});
    throw responseLimitError();
  }
  if (!response.body) return Buffer.alloc(0);
  if (typeof response.body.getReader !== "function") {
    throw new Error("AI endpoint response body is not a readable byte stream");
  }

  const reader = response.body.getReader();
  const chunks = [];
  let total = 0;
  let completed = false;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        completed = true;
        break;
      }
      if (!(value instanceof Uint8Array)) {
        throw new Error("AI endpoint response body returned a non-byte chunk");
      }
      if (value.byteLength > MAX_AI_RESPONSE_BYTES - total) throw responseLimitError();
      chunks.push(Buffer.from(value));
      total += value.byteLength;
    }
  } finally {
    if (!completed) await reader.cancel().catch(() => {});
    reader.releaseLock?.();
  }
  return Buffer.concat(chunks, total);
}

export async function draftWithOpenAI({ brief: rawBrief, baseUrl, apiKey, model, apiMode = "chat-completions", fetchImpl = fetch }) {
  const brief = validateDirectorBrief(rawBrief);
  const prompt = directorPrompt();
  const endpoint = safeEndpoint(baseUrl, apiMode);
  const selectedModel = text(model, "model", 120);
  if (typeof apiKey !== "string" || !apiKey.trim()) {
    throw new Error("BUGFIRE_OPENAI_API_KEY is missing; no live AI generation was performed");
  }
  const credential = apiKey.trim();
  const messages = [
    { role: "system", content: prompt },
    { role: "user", content: JSON.stringify(brief) },
  ];
  const body = apiMode === "responses"
    ? { model: selectedModel, input: messages, text: { format: { type: "json_object" } } }
    : { model: selectedModel, messages, response_format: { type: "json_object" } };
  const response = await fetchImpl(endpoint, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${credential}` },
    body: JSON.stringify(body),
    redirect: "error",
    signal: AbortSignal.timeout(60_000),
  });
  const responseBytes = await readBoundedResponse(response);
  const responseBody = decodeUtf8(responseBytes, "AI endpoint response");
  if (!response.ok) {
    const message = responseBody.slice(0, 500).replaceAll(credential, "[REDACTED]");
    throw new Error(`AI endpoint returned HTTP ${response.status}: ${message}`);
  }
  let envelope;
  try {
    envelope = JSON.parse(responseBody);
  } catch (error) {
    throw new Error(`AI endpoint envelope was not valid JSON: ${error.message}`);
  }
  let rawPayload;
  try {
    rawPayload = JSON.parse(responseText(envelope, apiMode));
  } catch (error) {
    throw new Error(`AI response was not valid JSON: ${error.message}`);
  }
  assertNoExactSecrets(rawPayload, [credential], "AI response payload");
  const payload = validateAiPayload(rawPayload, brief.rights);
  const plan = validateDirectorPlan({
    schemaVersion: 1,
    artifactType: "bugfire-character-director-plan",
    status: "ai-draft",
    provenance: {
      mode: "live-openai-compatible",
      provider: "OpenAI-compatible HTTP API",
      model: selectedModel,
      generatedAt: new Date().toISOString(),
      briefSha256: sha256(stableJson(brief)),
      promptSha256: sha256(prompt),
      endpointOrigin: endpoint.origin,
      sourceNotice: "Generated by a live API request. Endpoint origin is recorded; credentials and response headers are never stored.",
    },
    ...payload,
    humanReview: null,
  });
  assertNoExactSecrets(plan, [credential], "validated AI director plan");
  return plan;
}

function isWithin(base, target) {
  const relative = path.relative(base, target);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== "..");
}

async function assertNoSymlinkAncestors(absolute, name) {
  const resolved = path.resolve(absolute);
  const candidates = [process.cwd(), os.tmpdir(), os.homedir()]
    .map((candidate) => path.resolve(candidate))
    .filter((candidate) => isWithin(candidate, resolved))
    .sort((left, right) => right.length - left.length);
  const anchor = candidates[0] || path.parse(resolved).root;
  let cursor = anchor;
  const components = path.relative(anchor, resolved).split(path.sep).filter(Boolean);
  for (const component of components) {
    cursor = path.join(cursor, component);
    const entry = await fs.lstat(cursor).catch((error) => {
      if (error?.code === "ENOENT") return null;
      throw error;
    });
    if (!entry) return;
    if (entry.isSymbolicLink()) invalid(`${name} must not traverse a symbolic link: ${cursor}`);
  }
}

function validateReviewRequest(raw) {
  const review = plainObject(raw, "review request");
  exactKeys(review, [
    "schemaVersion", "reviewer", "reviewedAt", "rejectedDecisionId", "reason", "replacementDecision",
  ], "review request");
  if (review.schemaVersion !== 1) invalid("review request schemaVersion must be 1");
  const reviewedAt = text(review.reviewedAt, "reviewedAt", 40);
  if (Number.isNaN(Date.parse(reviewedAt))) invalid("reviewedAt must be an ISO date-time");
  return {
    schemaVersion: 1,
    reviewer: text(review.reviewer, "reviewer", 100),
    reviewedAt,
    rejectedDecisionId: text(review.rejectedDecisionId, "rejectedDecisionId", 64),
    reason: text(review.reason, "reason", 600),
    replacementDecision: validateDecision(review.replacementDecision, "replacementDecision"),
  };
}

export function applyHumanReview(rawDraft, rawReview, rawBrief) {
  const draft = validateDirectorPlan(rawDraft, { requiredStatus: "ai-draft" });
  validatePlanBriefBinding(draft, rawBrief, "human review");
  const review = validateReviewRequest(rawReview);
  const index = draft.creativeDecisions.findIndex(({ id }) => id === review.rejectedDecisionId);
  if (index < 0) invalid(`rejected decision does not exist: ${review.rejectedDecisionId}`);
  if (review.replacementDecision.id !== review.rejectedDecisionId) {
    invalid("replacement decision must keep the rejected decision id");
  }
  const original = draft.creativeDecisions[index];
  const originalPaths = Object.keys(original.manifestPatch).sort();
  const replacementPaths = Object.keys(review.replacementDecision.manifestPatch).sort();
  if (stableJson(originalPaths) !== stableJson(replacementPaths)) {
    invalid("replacement decision must cover exactly the same manifest fields as the rejected decision");
  }
  if (stableJson(original.manifestPatch) === stableJson(review.replacementDecision.manifestPatch)) {
    invalid("human replacement must materially change the rejected choice");
  }
  const decisions = structuredClone(draft.creativeDecisions);
  decisions[index] = review.replacementDecision;
  const manifest = applyPatch(draft.manifestProposal, review.replacementDecision.manifestPatch);
  return validateDirectorPlan({
    ...draft,
    status: "human-approved",
    creativeDecisions: decisions,
    manifestProposal: manifest,
    humanReview: {
      reviewer: review.reviewer,
      reviewedAt: review.reviewedAt,
      rejectedDecisionId: review.rejectedDecisionId,
      reason: review.reason,
      originalDecision: original,
      replacementDecision: review.replacementDecision,
      draftSha256: sha256(stableJson(draft)),
    },
  }, { requiredStatus: "human-approved" });
}

export async function materializeReviewedPlan(rawPlan, packDirectory, rawBrief) {
  const plan = validateDirectorPlan(rawPlan, { requiredStatus: "human-approved" });
  validatePlanBriefBinding(plan, rawBrief, "materialize");
  const root = path.resolve(packDirectory);
  await assertNoSymlinkAncestors(root, "pack output");
  const entry = await fs.lstat(root).catch((error) => {
    if (error?.code === "ENOENT") return null;
    throw error;
  });
  if (entry && (!entry.isDirectory() || entry.isSymbolicLink())) invalid("pack output must be a real directory");
  await fs.mkdir(root, { recursive: true, mode: 0o700 });
  await assertNoSymlinkAncestors(root, "pack output");
  const report = {
    pass: true,
    boundary: "AI proposes; human changes/approves; deterministic pack validator decides installability.",
    planSha256: sha256(stableJson(plan)),
    briefSha256: plan.provenance.briefSha256,
    generationMode: plan.provenance.mode,
    model: plan.provenance.model,
    humanReview: {
      reviewer: plan.humanReview.reviewer,
      reviewedAt: plan.humanReview.reviewedAt,
      rejectedDecisionId: plan.humanReview.rejectedDecisionId,
    },
    requiredNextStep: "Run bugfire-pack.mjs validate before build or install.",
  };
  const manifestOutput = path.join(root, "bugfire-pack.json");
  const reportOutput = path.join(root, "director-report.json");
  await assertOutputAbsent(manifestOutput, "materialized manifest output");
  await assertOutputAbsent(reportOutput, "materialized director report output");
  await writeJsonNoClobber(manifestOutput, plan.manifestProposal, "materialized manifest output");
  await writeJsonNoClobber(reportOutput, report, "materialized director report output");
  return { ...report, output: root };
}

export async function verifyRecordedFixture(planFile, checksumFile, briefFile) {
  if (!briefFile) invalid("recorded fixture verification requires its human brief");
  const planRecord = await readJson(planFile, "recorded plan fixture");
  const plan = validateDirectorPlan(planRecord.value, { requiredStatus: "ai-draft" });
  if (plan.provenance.mode !== "recorded-agent-fixture") invalid("fixture must be labeled recorded-agent-fixture");
  const checksum = decodeUtf8(
    await fs.readFile(path.resolve(checksumFile)), "fixture checksum",
  ).trim();
  const match = /^([a-f0-9]{64})(?:\s+\*?.+)?$/.exec(checksum);
  if (!match) invalid("fixture checksum file is malformed");
  const actual = sha256(planRecord.bytes);
  if (actual !== match[1]) invalid(`fixture checksum mismatch: expected ${match[1]}, got ${actual}`);
  if (plan.provenance.promptSha256 !== sha256(directorPrompt())) {
    invalid("fixture prompt digest does not match the current director contract");
  }
  const brief = (await readJson(briefFile, "fixture brief")).value;
  validatePlanBriefBinding(plan, brief, "recorded fixture verification");
  return {
    pass: true,
    mode: plan.provenance.mode,
    model: plan.provenance.model,
    sha256: actual,
    briefVerified: true,
    notice: plan.provenance.sourceNotice,
  };
}

function options(args) {
  const parsed = {};
  for (let index = 0; index < args.length; index += 2) {
    const key = args[index];
    const value = args[index + 1];
    if (!key?.startsWith("--") || value === undefined) throw new Error(`Invalid option: ${key || "missing"}`);
    parsed[key.slice(2)] = value;
  }
  return parsed;
}

async function cli(argv) {
  const [command, first, second, third, ...rest] = argv;
  if (command === "draft-live" && first && second) {
    const flags = options([third, ...rest].filter((value) => value !== undefined));
    await assertOutputAbsent(second, "AI draft output");
    const brief = (await readJson(first, "brief")).value;
    const apiKey = process.env.BUGFIRE_OPENAI_API_KEY || "";
    const plan = await draftWithOpenAI({
      brief,
      baseUrl: flags["base-url"] || process.env.BUGFIRE_OPENAI_BASE_URL || "https://api.openai.com/v1",
      apiKey,
      model: flags.model || process.env.BUGFIRE_OPENAI_MODEL || "",
      apiMode: flags["api-mode"] || "chat-completions",
    });
    await writeJsonNoClobber(second, plan, "AI draft output", { secrets: [apiKey] });
    return { pass: true, mode: plan.provenance.mode, model: plan.provenance.model, output: path.resolve(second) };
  }
  if (command === "verify-fixture" && first && second && third && rest.length === 0) {
    return verifyRecordedFixture(first, second, third);
  }
  if (command === "review" && first && second && third && rest.length === 1) {
    const output = rest[0];
    await assertOutputAbsent(output, "reviewed plan output");
    const draft = (await readJson(first, "AI draft")).value;
    const review = (await readJson(second, "human review")).value;
    const brief = (await readJson(third, "human brief")).value;
    const approved = applyHumanReview(draft, review, brief);
    await writeJsonNoClobber(output, approved, "reviewed plan output");
    return {
      pass: true,
      status: approved.status,
      rejectedDecisionId: approved.humanReview.rejectedDecisionId,
      output: path.resolve(output),
    };
  }
  if (command === "validate" && first && !second) {
    const plan = validateDirectorPlan((await readJson(first, "director plan")).value);
    return { pass: true, status: plan.status, mode: plan.provenance.mode, decisions: plan.creativeDecisions.length };
  }
  if (command === "materialize" && first && second && third && rest.length === 0) {
    const plan = (await readJson(first, "reviewed plan")).value;
    const brief = (await readJson(second, "human brief")).value;
    return materializeReviewedPlan(plan, third, brief);
  }
  throw new Error([
    "Usage:",
    "  bugfire-director.mjs draft-live <brief.json> <draft.json> --model <id> [--base-url <url>] [--api-mode chat-completions|responses]",
    "  bugfire-director.mjs verify-fixture <draft.json> <draft.sha256> <brief.json>",
    "  bugfire-director.mjs review <draft.json> <review.json> <brief.json> <reviewed.json>",
    "  bugfire-director.mjs validate <plan.json>",
    "  bugfire-director.mjs materialize <reviewed.json> <brief.json> <pack-dir>",
  ].join("\n"));
}

const modulePath = await fs.realpath(fileURLToPath(import.meta.url)).catch(() => path.resolve(fileURLToPath(import.meta.url)));
const entryPath = process.argv[1]
  ? await fs.realpath(process.argv[1]).catch(() => path.resolve(process.argv[1]))
  : "";
if (entryPath && entryPath === modulePath) {
  cli(process.argv.slice(2)).then((result) => {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  }).catch((error) => {
    process.stderr.write(`[bugfire-director] ${error.message}\n`);
    process.exitCode = 1;
  });
}
