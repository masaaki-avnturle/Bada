/*
 * e2e-test.js — 実際のブラウザで確かめる (Playwright と Chromium が必要。CI では実行しない)
 *   node bada_meeting/tools/e2e-test.js [スクリーンショットの出力先]
 * 1. 1 台で全役: 議題 → 決定まで自動で進む。滞留 (ホバー) で候補が確定する
 * 2. 3 つの画面を WebRTC でつなぎ、企画・プランナー・エンジニアを別々の画面に割り当てて会議する
 */
"use strict";
const { chromium } = require("playwright"), path = require("path");
const url = "file://" + path.join(__dirname, "..", "index.html"), shots = process.argv[2];
let pass = 0, fail = 0;
const ok = (c, name, extra) => { if (c) { pass++; console.log("  ✓ " + name); } else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  → " + String(extra).slice(0, 300) : "")); } };
const kinds = p => p.evaluate(() => BadaMeetingApp.meeting().msgs.map(m => m.kind + "/" + m.role).join(" "));
const decided = p => p.waitForFunction(() => BadaMeetingApp.meeting().decided(), null, { timeout: 60000 });

(async () => {
  const browser = await chromium.launch(), errors = [];
  const open = async vp => { const p = await browser.newPage({ viewport: vp || { width: 1200, height: 860 }, deviceScaleFactor: 1 }); p.on("pageerror", e => errors.push(e.message)); await p.goto(url); return p; };

  console.log("1 台で全役");
  const solo = await open();
  await solo.fill("#compose", "スマホ向けの予約アプリを3か月で作りたい");
  await solo.click("#acts .tile.act");
  await decided(solo);
  const k = await kinds(solo);
  ok(/^agenda\/host propose\/kikaku estimate\/engineer concern\/planner revise\/kikaku estimate\/engineer schedule\/planner/.test(k) && /decide\/planner$/.test(k), "議題 → 提案 → 見積り → 懸念 → 修正 → 日程 → 合意 → 決定", k);
  ok(await solo.locator(".msg.decide").count() === 1, "決定事項が表示される");
  // 滞留で確定: 候補の上にポインタを留めるだけ (クリックしない)
  await solo.fill("#compose", "");
  const cand = solo.locator("#cands .tile").first(), label = (await cand.locator("span").first().innerText()).replace(/\s*[\d.]+ 秒$/, "");
  await cand.hover(); await solo.waitForFunction(() => document.getElementById("compose").value.length > 0, null, { timeout: 5000 });
  ok((await solo.inputValue("#compose")) === label, "滞留だけで候補が入力される", await solo.inputValue("#compose"));
  await solo.mouse.move(5, 5); await solo.fill("#compose", "");
  await solo.locator("#kana .tile", { hasText: "よ" }).hover(); await solo.waitForFunction(() => document.getElementById("compose").value === "よ", null, { timeout: 5000 });
  ok(true, "かなも滞留で入力できる");
  await solo.mouse.move(5, 5); await solo.fill("#compose", "今日の昼ごはんは何にしますか");
  await solo.click("#acts .tile.act");
  await solo.waitForSelector(".msg .off");
  ok(true, "議題から外れた発言に印が付く");
  const [dl] = await Promise.all([solo.waitForEvent("download"), solo.click("#export")]);
  ok(dl.suggestedFilename() === "meeting-minutes.md", "議事録を保存できる");
  ok(!(await solo.evaluate(() => document.documentElement.scrollWidth > innerWidth)), "横スクロールが出ない");
  if (shots) await solo.screenshot({ path: path.join(shots, "meeting-solo.png") });

  console.log("3 台を WebRTC でつなぐ");
  const host = await open(), g1 = await open(), g2 = await open({ width: 390, height: 800 });
  await host.selectOption("#role", "kikaku");
  for (const [g, role] of [[g1, "engineer"], [g2, "planner"]]) {
    await host.click("#connect"); await host.click("#mkinvite");
    await host.waitForFunction(() => document.getElementById("invite").value.length > 100);
    const invite = await host.inputValue("#invite");
    await g.click("#connect"); await g.check("input[name=side][value=guest]"); await g.fill("#invitein", invite); await g.click("#mkanswer");
    await g.waitForFunction(() => document.getElementById("answer").value.length > 100);
    await host.fill("#answerin", await g.inputValue("#answer")); await host.click("#accept");
    await g.waitForFunction(() => /主催者と接続/.test(document.getElementById("status").textContent), null, { timeout: 20000 });
    await host.click("#close"); await g.click("#close"); await host.fill("#invite", "").catch(() => {});
    await host.evaluate(() => { document.getElementById("invite").value = ""; });
    await g.selectOption("#role", role);
  }
  ok(/接続 2 台/.test(await host.locator("#status").innerText()), "主催者に 2 台が接続", await host.locator("#status").innerText());
  await host.fill("#compose", "AndroidとWindows向けチャットアプリを4週間で");
  await host.click("#acts .tile.act");
  await Promise.all([decided(host), decided(g1), decided(g2)]);
  const [a, b, c] = await Promise.all([host, g1, g2].map(p => p.evaluate(() => JSON.stringify(BadaMeetingApp.meeting().msgs.map(m => [m.seq, m.role, m.kind, m.text])))));
  ok(a === b && b === c, "3 台の議事録が完全に一致する");
  ok(/propose\/kikaku estimate\/engineer concern\/planner revise\/kikaku/.test(await kinds(g2)), "各役割が別々の端末から発言している", await kinds(g2));
  // 人の発言: 期限の変更で話し合い直す
  await g1.fill("#compose", "期限を12週間にしましょう"); await g1.click("#acts .tile.act");
  await host.waitForFunction(() => /期限は 12 週間/.test(BadaMeetingApp.meeting().msgs[0].text) && BadaMeetingApp.meeting().decided(), null, { timeout: 60000 });
  ok(!/concern/.test(await kinds(host)), "期限を延ばすと懸念なしで決定に至る", await kinds(host));
  ok(!(await g2.evaluate(() => document.documentElement.scrollWidth > innerWidth)), "スマホ幅でも横スクロールが出ない");
  if (shots) { await host.screenshot({ path: path.join(shots, "meeting-host.png") }); await g2.screenshot({ path: path.join(shots, "meeting-phone.png") }); }
  ok(errors.length === 0, "ページのエラーなし", errors.join(" | "));
  await browser.close();
  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
