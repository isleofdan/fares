// Full-page screenshot of the fares page with Playwright's headless Chromium.
// Run: npm run screenshot [-- <page.html> <out.png>]
// Defaults: /data/home/dan/fares-data/fares.html -> docs/fares-page.png
import { chromium } from "playwright";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

const page = process.argv[2] || "/data/home/dan/fares-data/fares.html";
const out = process.argv[3] || "docs/fares-page.png";

const browser = await chromium.launch();
const tab = await browser.newPage({ viewport: { width: 900, height: 1000 } });
await tab.goto(pathToFileURL(resolve(page)).href);
// Open the glossary so the screenshot shows it too.
await tab.evaluate(() => document.querySelectorAll("details").forEach((d) => (d.open = true)));
const sections = await tab.locator("section").count();
await tab.screenshot({ path: out, fullPage: true });
await browser.close();
console.log(`wrote ${out} (${sections} route sections)`);
