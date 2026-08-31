import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ENGINE = path.resolve(fileURLToPath(new URL("../", import.meta.url)));
const ROOT = path.basename(ENGINE) === "macos" ? path.dirname(ENGINE) : ENGINE;
const page = path.join(ROOT, "docs", "index.html");

test("GitHub Pages demo exposes the default experience and conversion paths", async () => {
  const html = await fs.readFile(page, "utf8");
  assert.match(html, /<title>BUGFIRE 补丁兽/);
  assert.match(html, /name="description"/);
  assert.match(html, /property="og:image"/);
  assert.match(html, /application\/ld\+json/);
  assert.match(html, /id="demo-stage"/);
  assert.match(html, /data-shot="home"/);
  assert.match(html, /data-shot="cabin"/);
  assert.match(html, /data-shot="level"/);
  assert.match(html, /CHARACTER DIRECTOR/);
  assert.match(html, /AI 提案，人工否决，校验器裁决/);
  assert.match(html, /bugfire-director-ai-draft\.png/);
  assert.match(html, /model ID 不作独立可验证声明/);
  assert.match(html, /releases\/latest/);
  assert.match(html, /skills\/codex-bugfire-customizer\/SKILL\.md/);
  assert.doesNotMatch(html, /https?:\/\/(?:fonts\.googleapis|fonts\.gstatic|cdn\.|unpkg|jsdelivr)/);
});

test("Pages source includes discoverability files and local social/director art", async () => {
  for (const filename of [
    ".nojekyll", "robots.txt", "sitemap.xml", "llms.txt", "404.html",
    "images/bugfire-social-card.png", "images/bugfire-director-ai-draft.png",
    "images/bugfire-director-human-rejection.png", "images/bugfire-director-pack-preview.png",
  ]) {
    await fs.access(path.join(ROOT, "docs", filename));
  }
});
