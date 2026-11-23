/*
 * e2e-test.js — 実際のブラウザで確かめる (Playwright と Chromium が必要。CI では実行しない)
 *   node bada_meeting/tools/e2e-test.js [スクリーンショットの出力先]
 * 操作はすべてキーボードで行う (マウス・タッチを使わない)。
 * 1. 1 台で全役: 複数行の議題 → 決定。電鍵 (Space の長短) と Alt + 数字で入力
 * 2. 3 つの画面を WebRTC でつなぐ (接続の操作もキーボードだけ)
 * 3. 音響電信: 別の端末が鳴らした音 (WAV を偽のマイク入力にする) を復調して、会議に応じる
 */
"use strict";
const { chromium } = require("playwright"), path = require("path"), fs = require("fs"), os = require("os");
const Tg = require("../src/telegraph.js"), Ac = require("../src/acoustic.js"), M = require("../src/meeting.js"), Th = require("../src/thought.js");
const url = "file://" + path.join(__dirname, "..", "index.html"), shots = process.argv[2];
let pass = 0, fail = 0;
const ok = (c, name, extra) => { if (c) { pass++; console.log("  ✓ " + name); } else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  → " + String(extra).slice(0, 300) : "")); } };
const kinds = p => p.evaluate(() => BadaMeetingApp.meeting().msgs.map(m => m.kind + "/" + m.role).join(" "));
const decided = p => p.waitForFunction(() => BadaMeetingApp.meeting().decided(), null, { timeout: 60000 });
const sleep = ms => new Promise(r => setTimeout(r, ms));
// キーボードだけで操作する補助
const type = async (p, text) => { await p.focus("#compose"); for (const [i, line] of text.split("\n").entries()) { if (i) await p.keyboard.press("Enter"); await p.keyboard.insertText(line); } };
const press = async (p, sel) => { await p.focus(sel); await p.keyboard.press("Enter"); };
const paste = async (p, sel, text) => { await p.focus(sel); await p.keyboard.insertText(text); };

(async () => {
  const errors = [];
  const watch = p => { p.on("pageerror", e => errors.push(e.message)); return p; };
  // 複数の画面を 1 つのブラウザで開くと、背面の画面のタイマーが絞られる。実機では画面ごとに別の端末なので、この制限を外す
  const NO_THROTTLE = ["--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows"];
  let browser = await chromium.launch({ args: NO_THROTTLE });
  const open = async vp => { const p = watch(await browser.newPage({ viewport: vp || { width: 1200, height: 860 }, deviceScaleFactor: 1 })); await p.goto(url); return p; };

  console.log("1 台で全役 (キーボードだけ)");
  const solo = await open();
  ok(await solo.evaluate(() => document.activeElement.id === "compose"), "開いた時点で発言欄にフォーカスがある");
  await type(solo, "スマホ向けの予約アプリを\n3か月で作りたい\n(複数行の議題)");
  await solo.keyboard.press("Control+Enter");
  await decided(solo);
  const k = await kinds(solo);
  ok(/^agenda\/host propose\/kikaku estimate\/engineer concern\/planner revise\/kikaku estimate\/engineer schedule\/planner/.test(k) && /decide\/planner$/.test(k), "複数行の議題 → 提案 → 見積り → 懸念 → 修正 → 日程 → 合意 → 決定", k);
  ok((await solo.evaluate(() => BadaMeetingApp.meeting().msgs[0].text)).split("\n").length === 3 && (await solo.locator(".msg.agenda .text").evaluate(e => getComputedStyle(e).whiteSpace)) === "pre-wrap", "議題の改行が保たれて表示される");
  // 電鍵: F2 で入り、Space の長短で和文モールスを打つ
  await solo.keyboard.press("F2");
  const unit = 120, keyIn = async (text, mode) => {
    for (const sym of Th.toMorse(text, mode).split(" ")) {
      for (const c of sym) { await solo.keyboard.down("Space"); await sleep(c === "." ? unit * 0.7 : unit * 3); await solo.keyboard.up("Space"); await sleep(unit * 0.8); }
      await sleep(unit * 3.2);
    }
  };
  await keyIn("よやくは", "kana"); await solo.keyboard.press("Enter"); await keyIn("ぜんじつまで", "kana");
  await sleep(500);
  ok((await solo.inputValue("#compose")) === "よやくは\nぜんじつまで", "電鍵 (和文モールス) で 2 行を入力。濁点は直前のかなに付く", JSON.stringify(await solo.inputValue("#compose")));
  await solo.keyboard.press("F3"); await solo.keyboard.press("Enter"); await keyIn("ok", "latin"); await sleep(400);
  ok(/\nok ?$/.test(await solo.inputValue("#compose")), "F3 で欧文に切り替えて打てる", JSON.stringify(await solo.inputValue("#compose")));
  await solo.keyboard.press("F2");
  await solo.keyboard.press("Control+a"); await solo.keyboard.press("Backspace");
  await solo.keyboard.press("Alt+1");
  ok((await solo.inputValue("#compose")).length > 2, "Alt + 数字で候補が入る", await solo.inputValue("#compose"));
  await solo.keyboard.press("Control+a"); await solo.keyboard.press("Backspace");
  await type(solo, "今日の昼ごはんは\n何にしますか"); await solo.keyboard.press("Control+Enter");
  await solo.waitForSelector(".msg .off");
  ok(true, "議題から外れた発言 (複数行) に印が付く");
  const [dl] = await Promise.all([solo.waitForEvent("download"), solo.keyboard.press("F6")]);
  ok(dl.suggestedFilename() === "meeting-minutes.md", "F6 で議事録を保存できる");
  ok(!(await solo.evaluate(() => document.documentElement.scrollWidth > innerWidth)), "横スクロールが出ない");
  if (shots) await solo.screenshot({ path: path.join(shots, "meeting-solo.png") });

  console.log("3 台を WebRTC でつなぐ (キーボードだけ)");
  const host = await open(), g1 = await open(), g2 = await open({ width: 390, height: 800 });
  await host.focus("#role"); await host.selectOption("#role", "kikaku");
  for (const [g, role] of [[g1, "engineer"], [g2, "planner"]]) {
    await press(host, "#connect"); await press(host, "#mkinvite");
    await host.waitForFunction(() => document.getElementById("invite").value.length > 100);
    const invite = await host.inputValue("#invite");
    await press(g, "#connect"); await g.focus("input[name=side][value=guest]"); await g.keyboard.press("Space");
    await paste(g, "#invitein", invite); await press(g, "#mkanswer");
    await g.waitForFunction(() => document.getElementById("answer").value.length > 100);
    await paste(host, "#answerin", await g.inputValue("#answer")); await press(host, "#accept");
    await g.waitForFunction(() => /主催者と接続/.test(document.getElementById("status").textContent), null, { timeout: 20000 });
    await host.keyboard.press("Escape"); await g.keyboard.press("Escape");
    await host.evaluate(() => { document.getElementById("invite").value = ""; });
    await g.selectOption("#role", role);
  }
  ok(/接続 2 台/.test(await host.locator("#status").innerText()), "主催者に 2 台が接続", await host.locator("#status").innerText());
  await type(host, "AndroidとWindows向け\nチャットアプリを4週間で"); await host.keyboard.press("Control+Enter");
  await Promise.all([decided(host), decided(g1), decided(g2)]);
  const [a, b, c] = await Promise.all([host, g1, g2].map(p => p.evaluate(() => JSON.stringify(BadaMeetingApp.meeting().msgs.map(m => [m.seq, m.role, m.kind, m.text])))));
  ok(a === b && b === c, "3 台の議事録が完全に一致する");
  await type(g1, "期限を12週間にしましょう"); await g1.keyboard.press("Control+Enter");
  await host.waitForFunction(() => /期限は 12 週間/.test(BadaMeetingApp.meeting().msgs[0].text) && BadaMeetingApp.meeting().decided(), null, { timeout: 60000 });
  ok(!/concern/.test(await kinds(host)), "期限を延ばすと懸念なしで決定に至る", await kinds(host));
  ok(!(await g2.evaluate(() => document.documentElement.scrollWidth > innerWidth)), "スマホ幅でも横スクロールが出ない");
  if (shots) await g2.screenshot({ path: path.join(shots, "meeting-phone.png") });
  await browser.close();

  console.log("音響電信 (別の端末の音を、偽のマイク入力として聞かせる)");
  // 相手側 (企画とプランナー) が鳴らすはずの音を、同じモデムで作る
  const sr = 48000, agenda = "スマホ向けの予約アプリを\n3か月で作りたい", ref = M.runLocal(agenda);
  const sil = s => new Float32Array(Math.round(sr * s)), parts = [sil(4)];
  const add = (m, byAgent) => Tg.encodeMessage(m, byAgent, byAgent ? Ac.hash4(m.text) : null).forEach(p => { parts.push(Tg.modulate(p, sr).map(v => v * 0.5), sil(0.4)); });
  add(ref.msgs[0], false); parts.push(sil(1)); add(ref.msgs[1], true);
  parts.push(sil(9));                                     // この間に、画面 (エンジニア) が見積りを送信する
  add(ref.msgs[3], true); parts.push(sil(4));
  const all = new Float32Array(parts.reduce((s, x) => s + x.length, 0)); let o = 0; parts.forEach(x => { all.set(x, o); o += x.length; });
  const wavPath = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "bm-")), "peer.wav"); fs.writeFileSync(wavPath, Tg.wav(all, sr));
  browser = await chromium.launch({ args: NO_THROTTLE.concat(["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--use-file-for-fake-audio-capture=" + wavPath + "%noloop", "--autoplay-policy=no-user-gesture-required"]) });
  const ac = await open();
  await ac.selectOption("#role", "engineer");
  await ac.keyboard.press("F4");
  await ac.waitForFunction(() => /受信中|送信/.test(document.getElementById("acstate").textContent), null, { timeout: 15000 });
  ok(/音響電信で動作中/.test(await ac.locator("#status").innerText()), "F4 で音響電信を開始 (接続の手続きなし)");
  await ac.waitForFunction(() => BadaMeetingApp.meeting().msgs.length >= 2, null, { timeout: 40000 }).catch(() => {});
  const got = await ac.evaluate(() => BadaMeetingApp.meeting().msgs.map(m => [m.seq, m.role, m.kind, m.text]));
  ok(got.length >= 2 && got[0][3] === agenda && got[1][2] === "propose" && got[1][3] === ref.msgs[1].text, "音から複数行の議題を復調し、企画の発言をハッシュの照合で再現した", JSON.stringify(got.map(x => x[2])));
  await ac.waitForFunction(() => BadaMeetingApp.meeting().msgs.length >= 4, null, { timeout: 40000 }).catch(() => {});
  const fin = await ac.evaluate(() => BadaMeetingApp.meeting().msgs.map(m => m.kind + "/" + m.role).join(" "));
  ok(fin === "agenda/host propose/kikaku estimate/engineer concern/planner", "この端末のエンジニアが見積りを音で送信し、続くプランナーの発言も受信した", fin);
  ok((await ac.evaluate(() => BadaMeetingApp.meeting().msgs[2].text)) === ref.msgs[2].text, "この端末が作った見積りは、相手側の計算と同じ内容");
  if (shots) await ac.screenshot({ path: path.join(shots, "meeting-acoustic.png") });
  await browser.close(); fs.rmSync(path.dirname(wavPath), { recursive: true, force: true });

  ok(errors.length === 0, "ページのエラーなし", errors.join(" | "));
  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
