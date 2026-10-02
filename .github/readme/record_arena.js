#!/usr/bin/env node
// Rekam ulang .github/readme/arena.gif dari arena contoh run nyata (examples/sample-run/arena.html):
// final, uji falsifikasi, lalu pemenang. Butuh Playwright (alat dev) dan Python + Pillow untuk menyusun GIF.
//
//   python3 .claude/skills/argument-battle-royale/scripts/abr.py arena --run .claude/skills/argument-battle-royale/examples/sample-run
//   node .github/readme/record_arena.js [keluaran.gif]
"use strict";
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

function loadPlaywright() {
  for (const t of [process.env.PLAYWRIGHT_MODULE, "playwright", "/opt/node22/lib/node_modules/playwright"].filter(Boolean)) {
    try { return require(t); } catch (e) { /* coba berikutnya */ }
  }
  console.error("Playwright tidak ditemukan; set PLAYWRIGHT_MODULE.");
  process.exit(2);
}

const ROOT = path.resolve(__dirname, "..", "..");
const HTML = path.join(ROOT, ".claude", "skills", "argument-battle-royale", "examples", "sample-run", "arena.html");
const OUT = path.resolve(process.argv[2] || path.join(__dirname, "arena.gif"));
const FRAME_MS = 200;
const MAX_FRAMES = 190;

async function main() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "abr-rec-"));
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium" }).catch(() => chromium.launch());
  const page = await browser.newPage({ viewport: { width: 720, height: 900 }, deviceScaleFactor: 1 });
  // font eksternal tidak dibutuhkan untuk rekaman; blokir supaya rekaman tidak menunggu jaringan
  await page.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.abort());
  await page.goto("file://" + HTML);
  // tandai semua acara sebelum final sebagai sudah ditonton, supaya pemutaran mulai dari final
  await page.evaluate(() => {
    const D = JSON.parse(document.getElementById("abr-data").textContent);
    const ev = D.run.events;
    let last = -1;
    ev.forEach((e, i) => { if (e.t === "match") last = i; });
    localStorage.clear();
    localStorage.setItem("abr-seen:" + D.run.run_id, JSON.stringify(ev.slice(0, last).map((e) => e.id)));
  });
  await page.reload();
  const stage = page.locator("section.stage");
  let n = 0, seenWinner = 0;
  for (; n < MAX_FRAMES; n++) {
    const t0 = Date.now();
    await stage.screenshot({ path: path.join(tmp, "f" + String(n).padStart(4, "0") + ".png") });
    const head = await page.evaluate(() => document.getElementById("tkHead").textContent);
    if (/TOURNAMENT WINNER|Pemenang tahan-uji/.test(head)) seenWinner++;
    if (seenWinner > 22) break;  // tahan adegan pemenang sekitar 4 detik
    const wait = FRAME_MS - (Date.now() - t0);
    if (wait > 0) await page.waitForTimeout(wait);
  }
  await browser.close();
  const py = [
    "import glob, sys",
    "from PIL import Image",
    "fs = sorted(glob.glob(sys.argv[1] + '/f*.png'))",
    "ims = [Image.open(f).convert('RGB') for f in fs]",
    "pal = ims[len(ims) // 2].quantize(colors=96, method=Image.Quantize.MEDIANCUT)",
    "fr = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]",
    "fr[0].save(sys.argv[2], save_all=True, append_images=fr[1:], duration=" + FRAME_MS + ", loop=0, optimize=True)",
    "print(len(fr), 'frame', ims[0].size)",
  ].join("\n");
  execFileSync("python3", ["-c", py, tmp, OUT], { stdio: "inherit" });
  console.log("ditulis:", OUT, Math.round(fs.statSync(OUT).size / 1024) + " KB");
}
main().catch((e) => { console.error(e); process.exit(1); });
