#!/usr/bin/env node
// Uji ujung-ke-ujung arena HTML (demo) di Chromium headless dengan Playwright (alat dev opsional).
//
//   node .github/scripts/e2e_arena.js [folder-keluaran]
//
// Menulis arena demo lewat `abr.py arena --demo`, membukanya, memutar 4x, lalu memeriksa:
//   - tidak ada console error / pageerror
//   - data Gobyet tersemat, semua gambar sprite termuat (tidak ada gambar rusak)
//   - kanvas berisi piksel pada setiap adegan yang diamati
//   - tiap petarung demo mendapat karakter Gobyet dan duel menggambar dua karakter berbeda
//   - label pemenang "TOURNAMENT WINNER" tampil dan "ABSOLUTE TRUTH" tidak pernah tampil
//   - mode cadangan: tanpa data Gobyet, arena tetap jalan dengan sprite Clawd tanpa error
// Screenshot disimpan ke folder keluaran. Kode keluar 1 bila ada pemeriksaan yang gagal.
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { execFileSync } = require("node:child_process");

function loadPlaywright() {
  const tries = [process.env.PLAYWRIGHT_MODULE, "playwright", "/opt/node22/lib/node_modules/playwright"].filter(Boolean);
  for (const t of tries) {
    try { return require(t); } catch (e) { /* coba berikutnya */ }
  }
  console.error("Playwright tidak ditemukan; set PLAYWRIGHT_MODULE.");
  process.exit(2);
}

const ROOT = path.resolve(__dirname, "..", "..");
const SKILL = path.join(ROOT, ".claude", "skills", "argument-battle-royale");
const OUT = path.resolve(process.argv[2] || fs.mkdtempSync(path.join(os.tmpdir(), "abr-e2e-")));
fs.mkdirSync(OUT, { recursive: true });
const results = [];
function check(name, ok, detail) { results.push({ name, ok: !!ok, detail: detail || "" }); }
// Font Google Fonts di template sudah ada sejak sebelum Gobyet; di sandbox tanpa akses keluar request-nya gagal.
// Kegagalan request ke host eksternal dicatat sebagai info, bukan error halaman.
const EXTERNAL = /^https:\/\/fonts\.(googleapis|gstatic)\.com\//;
function watch(page, errors, external) {
  page.on("requestfailed", (r) => { if (EXTERNAL.test(r.url())) external.push(r.url()); else errors.push("request gagal: " + r.url()); });
  page.on("console", (m) => { if (m.type() === "error" && !/Failed to load resource/.test(m.text())) errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));
}

async function main() {
  const html = path.join(OUT, "arena-demo.html");
  execFileSync("python3", [path.join(SKILL, "scripts", "abr.py"), "arena", "--demo", "--out", html], { stdio: "pipe" });
  // versi tanpa Gobyet (mode cadangan Clawd)
  const raw = fs.readFileSync(html, "utf8");
  const open = '<script id="abr-data" type="application/json">';
  const i0 = raw.indexOf(open) + open.length, i1 = raw.indexOf("</script>", i0);
  const data = JSON.parse(raw.slice(i0, i1));
  data.gobyet = null;
  const htmlNoG = path.join(OUT, "arena-demo-tanpa-gobyet.html");
  fs.writeFileSync(htmlNoG, raw.slice(0, i0) + JSON.stringify(data).replace(/<\//g, "<\\/") + raw.slice(i1));

  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium" }).catch(() => chromium.launch());
  try {
    // ---------- mode Gobyet ----------
    const page = await browser.newPage({ viewport: { width: 900, height: 1100 } });
    const errors = [], external = [];
    watch(page, errors, external);
    await page.goto("file://" + html);
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.click('[data-speed="4"]');
    const info = await page.evaluate(() => {
      const D = JSON.parse(document.getElementById("abr-data").textContent);
      return { hasG: !!(D.gobyet && D.gobyet.chars), nChars: D.gobyet ? Object.keys(D.gobyet.chars).length : 0, cast: D.run.cast,
               fighters: Object.keys(D.run.fighters) };
    });
    check("data Gobyet tersemat", info.hasG && info.nChars >= 30, info.nChars + " karakter");
    const castOk = info.fighters.every((f) => info.cast && info.cast[f] && info.cast[f].char);
    check("tiap petarung punya karakter", castOk, JSON.stringify(info.cast));
    const chars = new Set(info.fighters.map((f) => info.cast[f].char));
    check("petarung demo memakai karakter berbeda", chars.size >= 3, Array.from(chars).join(", "));

    await page.waitForTimeout(1500);
    const broken = await page.evaluate(() => new Promise((res) => {
      const D = JSON.parse(document.getElementById("abr-data").textContent);
      const srcs = [];
      Object.values(D.gobyet.chars).forEach((c) => Object.values(c.states).forEach((s) => srcs.push(s.src)));
      Object.values(D.gobyet.icons).forEach((s) => srcs.push(s));
      let left = srcs.length, bad = 0;
      srcs.forEach((src) => { const im = new Image(); im.onload = () => { if (!im.naturalWidth) bad++; if (--left === 0) res({ total: srcs.length, bad }); };
        im.onerror = () => { bad++; if (--left === 0) res({ total: srcs.length, bad }); }; im.src = src; });
    }));
    check("semua sprite dan ikon termuat", broken.bad === 0, broken.total + " gambar, rusak " + broken.bad);

    const seenTicker = new Set(), shots = [];
    let fightFrames = 0, distinctPair = false;
    for (let k = 0; k < 60; k++) {
      await page.waitForTimeout(700);
      const st = await page.evaluate(() => {
        const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
        const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
        let n = 0;
        for (let i = 3; i < d.length; i += 16) if (d[i]) n++;
        return { n, head: document.getElementById("tkHead").textContent, meta: document.getElementById("tkMeta").textContent,
                 text: document.getElementById("tkText").textContent, hud: !document.getElementById("hud").hidden };
      });
      seenTicker.add(st.head);
      if (st.hud) fightFrames++;
      if (k % 6 === 0 || /TOURNAMENT|Putusan|falsifikasi/i.test(st.head)) {
        const p = path.join(OUT, "arena-" + String(k).padStart(2, "0") + ".png");
        await page.locator("#cv").screenshot({ path: p });
        shots.push(p);
      }
      if (st.n === 0) check("kanvas tidak kosong (t=" + k + ")", false, st.head);
      if (/TOURNAMENT WINNER/.test(st.head)) break;
    }
    const heads = Array.from(seenTicker);
    check("label TOURNAMENT WINNER tampil", heads.some((h) => /TOURNAMENT WINNER/.test(h)), heads.slice(-3).join(" | "));
    const body = await page.content();
    check("tidak ada ABSOLUTE TRUTH", !/ABSOLUTE TRUTH/i.test(body) && !heads.some((h) => /ABSOLUTE TRUTH/i.test(h)));
    check("duel diputar", fightFrames > 3, fightFrames + " sampel dengan HUD duel");
    check("tanpa error halaman (Gobyet)", errors.length === 0, errors.slice(0, 3).join(" | ") +
      (external.length ? " [info: " + external.length + " request font eksternal gagal di sandbox]" : ""));
    await page.close();

    // ---------- mode cadangan Clawd ----------
    const p2 = await browser.newPage({ viewport: { width: 900, height: 1100 } });
    const err2 = [], ext2 = [];
    watch(p2, err2, ext2);
    await p2.goto("file://" + htmlNoG);
    await p2.evaluate(() => localStorage.clear());
    await p2.reload();
    await p2.click('[data-speed="4"]');
    const g2 = await p2.evaluate(() => JSON.parse(document.getElementById("abr-data").textContent).gobyet);
    await p2.waitForTimeout(6000);
    const n2 = await p2.evaluate(() => {
      const cv = document.getElementById("cv"), d = cv.getContext("2d").getImageData(0, 0, cv.width, cv.height).data;
      let n = 0; for (let i = 3; i < d.length; i += 16) if (d[i]) n++; return n;
    });
    await p2.locator("#cv").screenshot({ path: path.join(OUT, "arena-cadangan-clawd.png") });
    check("cadangan Clawd: data Gobyet kosong", g2 === null);
    check("cadangan Clawd: kanvas tergambar", n2 > 0, n2 + " piksel sampel");
    check("cadangan Clawd: tanpa error halaman", err2.length === 0, err2.slice(0, 3).join(" | "));
    fs.writeFileSync(path.join(OUT, "e2e.json"), JSON.stringify({ results, shots, heads }, null, 1));
  } finally {
    await browser.close();
  }
  let bad = 0;
  for (const r of results) { console.log((r.ok ? "LULUS " : "GAGAL ") + r.name + (r.detail ? "  — " + r.detail : "")); if (!r.ok) bad++; }
  console.log(bad ? "E2E GAGAL (" + bad + ")" : "E2E LULUS", "| keluaran:", OUT);
  process.exit(bad ? 1 : 0);
}
main().catch((e) => { console.error(e); process.exit(1); });
