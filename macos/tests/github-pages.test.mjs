import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";

const ENGINE = path.resolve(new URL("../", import.meta.url).pathname);
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
  assert.match(html, /releases\/latest/);
  assert.match(html, /skills\/codex-bugfire-customizer\/SKILL\.md/);
  assert.doesNotMatch(html, /https?:\/\/(?:fonts\.googleapis|fonts\.gstatic|cdn\.|unpkg|jsdelivr)/);
});

test("Pages source includes discoverability files and local social art", async () => {
  for (const filename of [".nojekyll", "robots.txt", "sitemap.xml", "llms.txt", "404.html", "images/bugfire-social-card.png"]) {
    await fs.access(path.join(ROOT, "docs", filename));
  }
});
