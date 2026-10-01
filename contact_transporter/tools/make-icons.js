#!/usr/bin/env node
/*
 * make-icons.js — アプリごとのアイコン (app/icons/<アプリ>.png, 1024×1024) を作る
 *   同じようなアプリが並んでも見分けられるよう、色と図柄をアプリごとに変える。
 *   package-app.js が Android (Cordova) / Windows・Linux (Electron) のアイコンに使う。
 *   node tools/make-icons.js   (Playwright の Chromium で SVG を描画。生成した PNG はコミット済み)
 */
const fs = require("fs"), path = require("path");
const OUT = path.join(__dirname, "..", "app", "icons");
const bg = (a, b) => `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient></defs><rect width="1024" height="1024" rx="220" fill="url(#g)"/>`;
const label = (t, y, size, color) => `<text x="512" y="${y}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-weight="700" font-size="${size}" fill="${color || "#fff"}">${t}</text>`;
const ICONS = {
  // 統合アプリ: 4 アプリの色を 4 つの点で結ぶ「N」
  nexus: bg("#0b1b3a", "#3a0b4a") +
    `<circle cx="512" cy="470" r="300" fill="none" stroke="#ffffff22" stroke-width="18"/>` +
    `<path d="M312 670 L312 270 L712 670 L712 270" fill="none" stroke="#fff" stroke-width="74" stroke-linecap="round" stroke-linejoin="round"/>` +
    `<circle cx="312" cy="270" r="62" fill="#4fc3f7"/><circle cx="712" cy="270" r="62" fill="#ffb300"/><circle cx="312" cy="670" r="62" fill="#26a69a"/><circle cx="712" cy="670" r="62" fill="#ab47bc"/>` +
    label("NEXUS", 905, 128, "#e3f2fd"),
  // ContactGPT: 青の吹き出し
  contactgpt: bg("#0d47a1", "#42a5f5") +
    `<path d="M200 240 h624 a70 70 0 0 1 70 70 v300 a70 70 0 0 1 -70 70 h-380 l-150 130 v-130 h-94 a70 70 0 0 1 -70 -70 v-300 a70 70 0 0 1 70 -70z" fill="#fff"/>` +
    label("GPT", 545, 200, "#0d47a1") + label("ContactGPT", 935, 96, "#e3f2fd"),
  // BadaClaude: 琥珀色の ψ
  badaclaude: bg("#e65100", "#ffca28") +
    `<circle cx="512" cy="450" r="290" fill="#ffffff26"/>` + label("ψ", 610, 420, "#fff") + label("BadaClaude", 935, 100, "#fff8e1"),
  // 輸送機 3D CAD: 緑のジンバル環
  transporter: bg("#004d40", "#26a69a") +
    `<ellipse cx="512" cy="450" rx="320" ry="320" fill="none" stroke="#fff" stroke-width="34"/><ellipse cx="512" cy="450" rx="320" ry="120" fill="none" stroke="#b2dfdb" stroke-width="28"/>` +
    `<ellipse cx="512" cy="450" rx="120" ry="320" fill="none" stroke="#b2dfdb" stroke-width="28"/><circle cx="512" cy="450" r="70" fill="#fff"/>` + label("CAD", 935, 110, "#e0f2f1"),
  // UFO 設計図面: 紫の円盤
  ufo: bg("#311b92", "#7e57c2") +
    `<ellipse cx="512" cy="420" rx="170" ry="140" fill="#d1c4e9"/><ellipse cx="512" cy="500" rx="380" ry="110" fill="#fff"/><ellipse cx="512" cy="500" rx="380" ry="110" fill="none" stroke="#311b92" stroke-width="16"/>` +
    `<circle cx="352" cy="505" r="26" fill="#7e57c2"/><circle cx="512" cy="520" r="26" fill="#7e57c2"/><circle cx="672" cy="505" r="26" fill="#7e57c2"/>` +
    `<path d="M420 620 L360 760 M512 625 L512 770 M604 620 L664 760" stroke="#ede7f6" stroke-width="22" stroke-linecap="round"/>` + label("UFO", 935, 110, "#ede7f6"),
  // 論文から作ったアプリ (ランナー): 灰色の論文
  runner: bg("#37474f", "#78909c") +
    `<path d="M300 170 h330 l130 130 v470 h-460z" fill="#fff"/><path d="M630 170 v130 h130" fill="#cfd8dc"/>` +
    `<path d="M370 380 h290 M370 460 h290 M370 540 h200 M370 620 h250" stroke="#78909c" stroke-width="30" stroke-linecap="round"/>` + label("Bada", 935, 110, "#eceff1"),
};
(async () => {
  const { chromium } = require(require("child_process").execSync("npm root -g").toString().trim() + "/playwright");
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1024, height: 1024 } });
  fs.mkdirSync(OUT, { recursive: true });
  for (const [k, body] of Object.entries(ICONS)) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">${body}</svg>`;
    fs.writeFileSync(path.join(OUT, k + ".svg"), svg);
    await p.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
    await p.screenshot({ path: path.join(OUT, k + ".png"), omitBackground: true, clip: { x: 0, y: 0, width: 1024, height: 1024 } });
    // Linux (.deb / AppImage) 用: 大きさごとの PNG (ファイル名が大きさ。単体の PNG だと大きさ 0x0 扱いになる)
    const dir = path.join(OUT, k + "-linux");
    fs.mkdirSync(dir, { recursive: true });
    for (const n of [512, 256, 128, 64, 48, 32]) {
      await p.setViewportSize({ width: n, height: n });
      await p.setContent(`<html><body style="margin:0;background:transparent">${svg.replace('width="1024" height="1024"', `width="${n}" height="${n}"`)}</body></html>`);
      await p.screenshot({ path: path.join(dir, `${n}x${n}.png`), omitBackground: true, clip: { x: 0, y: 0, width: n, height: n } });
    }
    await p.setViewportSize({ width: 1024, height: 1024 });
    console.log("app/icons/" + k + ".png + " + k + "-linux/");
  }
  await b.close();
})();
