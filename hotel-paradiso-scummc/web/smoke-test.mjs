// Loads the built page in headless Chromium, waits for the title screen,
// clicks "New game" and takes screenshots, so a broken build shows up in CI.
import { chromium, firefox } from 'playwright';
import { mkdirSync, writeFileSync } from 'fs';

const url = process.argv[2] || 'http://localhost:8000/';
const out = process.argv[3] || 'smoke-test';
const which = process.argv[4] || 'chromium';
const sequel = process.env.GAME === '2';     // the second game on the page (Sacra Pasta, AGS)
mkdirSync(out, { recursive: true });
const logs = [];
// Never hang CI: whatever happens, write what we have and exit after 150s
setTimeout(() => {
  writeFileSync(`${out}/${which}-console.txt`, logs.join('\n') + '\n[timeout] gave up after 150s\n');
  process.exit(3);
}, 150000).unref();
const headless = process.env.HEADED !== '1';
const browser = which.startsWith('firefox')
  ? await firefox.launch({ headless, firefoxUserPrefs: { 'media.autoplay.default': 0, 'webgl.force-enabled': true } })
  : await chromium.launch({ headless, args: ['--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
page.on('console', m => logs.push(`[${m.type()}] ${m.text()}`));
page.on('pageerror', e => logs.push(`[pageerror] ${e.message}`));
await page.goto(url);
await page.screenshot({ path: `${out}/${which}-0-landing.png` });
await page.locator('a.play').nth(sequel ? 1 : 0).click();
await page.waitForTimeout(1000);
// The page must survive a WebMIDI request (Firefox refuses it without an add-on)
logs.push('[midi] ' + await page.evaluate(async () => {
  if (!('requestMIDIAccess' in navigator)) return 'requestMIDIAccess not present';
  try { const m = await navigator.requestMIDIAccess({ sysex: true }); return 'resolved, outputs: ' + m.outputs.size; }
  catch (e) { return 'REJECTED: ' + e; }
}));
await page.waitForTimeout(25000);
await page.screenshot({ path: `${out}/${which}-1-title.png` });
const canvas = await page.$('canvas');
const box = canvas && await canvas.boundingBox();
if (box) {
  // "New game" sits at (160, 158) on Hotel Paradiso's 320x200 screen,
  // and at (320, 328) on Sacra Pasta's 640x400 one
  if (sequel) {
    // the AGS engine reads button state per frame, so hover first and hold the click
    await page.mouse.move(box.x + box.width * 320 / 640, box.y + box.height * 328 / 400);
    await page.waitForTimeout(500);
    await page.mouse.click(box.x + box.width * 320 / 640, box.y + box.height * 328 / 400, { delay: 150 });
    await page.waitForTimeout(6000);
  }
  else await page.mouse.click(box.x + box.width * 160 / 320, box.y + box.height * 161 / 200);
  await page.waitForTimeout(8000);
  await page.screenshot({ path: `${out}/${which}-2-game.png` });
}
writeFileSync(`${out}/${which}-console.txt`, logs.join('\n') + `\ncanvas: ${JSON.stringify(box)}\n`);
await browser.close();
