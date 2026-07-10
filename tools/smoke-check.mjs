import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { sources } from "../data/sources.js";

const PORT = 5175;
const HOST = "127.0.0.1";
const ROOT = path.resolve(fileURLToPath(new URL("..", import.meta.url)));

let playwright;

try {
  playwright = await import("playwright");
} catch {
  console.log("Playwright unavailable; smoke check skipped.");
  process.exit(0);
}

const chromium = playwright.chromium || playwright.default?.chromium;

if (!chromium) {
  console.log("Playwright unavailable; smoke check skipped.");
  process.exit(0);
}

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

function createStaticServer() {
  return http.createServer(async (request, response) => {
    try {
      const requestUrl = new URL(request.url, `http://${request.headers.host}`);
      const pathname = decodeURIComponent(requestUrl.pathname);
      const relativePath = pathname === "/" ? "index.html" : pathname.slice(1);
      const filePath = path.resolve(ROOT, relativePath);

      if (!filePath.startsWith(`${ROOT}${path.sep}`) && filePath !== ROOT) {
        response.writeHead(403);
        response.end("Forbidden");
        return;
      }

      const body = await fs.readFile(filePath);
      response.writeHead(200, {
        "Cache-Control": "no-store",
        "Content-Type": contentTypes[path.extname(filePath)] || "application/octet-stream",
      });
      response.end(body);
    } catch (error) {
      const status = error.code === "ENOENT" ? 404 : 500;
      response.writeHead(status);
      response.end(status === 404 ? "Not found" : "Server error");
    }
  });
}

function listen(server) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(PORT, HOST, () => {
      server.off("error", reject);
      resolve();
    });
  });
}

function closeServer(server) {
  return new Promise((resolve, reject) => {
    if (!server.listening) {
      resolve();
      return;
    }

    server.close((error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve();
    });
  });
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function countCards(page) {
  return page.locator(".source-card").count();
}

async function checkSearch(page, query, minimumCount) {
  await page.fill("#searchInput", query);
  await page.waitForTimeout(100);
  const cardCount = await countCards(page);
  assert(cardCount >= minimumCount, `Search "${query}" returned ${cardCount} cards; expected at least ${minimumCount}.`);
}

const server = createStaticServer();
let browser;
let serverStarted = false;

try {
  await listen(server);
  serverStarted = true;

  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const url = `http://${HOST}:${PORT}/`;

  await page.goto(url, { waitUntil: "networkidle" });

  const pageTitle = await page.title();
  assert(pageTitle === "AI Agent 架构阅读台", `Unexpected page title: "${pageTitle}".`);

  const h1 = await page.locator("h1").innerText();
  assert(h1 === "AI Agent 架构阅读台", `Unexpected h1: "${h1}".`);

  const privateResearchLinks = await page.locator('a[href*="vi8r050ecuz.feishu.cn"]').count();
  assert(privateResearchLinks === 0, "The public page must not expose the private Feishu research document.");

  const initialCardCount = await countCards(page);
  assert(initialCardCount === sources.length, `Expected ${sources.length} source cards, found ${initialCardCount}.`);

  const heroImageLoaded = await page.locator(".hero-art img").evaluate((image) => image.complete && image.naturalWidth > 0);
  assert(heroImageLoaded, "Hero image did not load.");

  await checkSearch(page, "MCP", 2);
  await checkSearch(page, "HR", 8);

  await page.click("[data-clear-filters]");
  assert(await page.inputValue("#searchInput") === "", "Clearing filters should reset the search input.");
  assert(await page.locator("#sortSelect").inputValue() === "priority", "Clearing filters should restore recommended sorting.");
  assert(await countCards(page) === sources.length, "Clearing filters should restore every source card.");

  await page.setViewportSize({ width: 390, height: 900 });
  await page.fill("#searchInput", "");
  await page.waitForTimeout(100);

  const overflow = await page.evaluate(() => {
    const documentWidth = document.documentElement.scrollWidth;
    const bodyWidth = document.body.scrollWidth;
    const viewportWidth = document.documentElement.clientWidth;

    return {
      scrollWidth: Math.max(documentWidth, bodyWidth),
      viewportWidth,
    };
  });

  assert(
    overflow.scrollWidth <= overflow.viewportWidth + 1,
    `Mobile viewport overflows horizontally: scrollWidth ${overflow.scrollWidth}, viewport ${overflow.viewportWidth}.`,
  );

  console.log("Smoke check passed.");
} finally {
  if (browser) {
    await browser.close();
  }
  if (serverStarted) {
    await closeServer(server);
  }
}
