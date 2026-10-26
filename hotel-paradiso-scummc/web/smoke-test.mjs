// Loads the built page in headless Chromium, waits for the title screen,
// clicks "New game" and takes screenshots, so a broken build shows up in CI.
import { chromium, firefox } from 'playwright';
import { mkdirSync, writeFileSync } from 'fs';

const url = process.argv[2] || 'http://localhost:8000/';
const out = process.argv[3] || 'smoke-test';
const which = process.argv[4] || 'chromium';
mkdirSync(out, { recursive: true });
const logs = [];
const browser = which === 'firefox'
  ? await firefox.launch({ firefoxUserPrefs: { 'media.autoplay.default': 0 } })
  : await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
page.on('console', m => logs.push(`[${m.type()}] ${m.text()}`));
page.on('pageerror', e => logs.push(`[pageerror] ${e.message}`));
await page.goto(url);
await page.screenshot({ path: `${out}/${which}-0-landing.png` });
await page.click('a.play');
await page.waitForTimeout(25000);
await page.screenshot({ path: `${out}/${which}-1-title.png` });
const canvas = await page.$('canvas');
const box = canvas && await canvas.boundingBox();
if (box) {
  // "New game" sits at (160, 158) on the 320x200 screen
  await page.mouse.click(box.x + box.width * 160 / 320, box.y + box.height * 161 / 200);
  await page.waitForTimeout(8000);
  await page.screenshot({ path: `${out}/${which}-2-game.png` });
}
writeFileSync(`${out}/${which}-console.txt`, logs.join('\n') + `\ncanvas: ${JSON.stringify(box)}\n`);
await browser.close();
