/*
 * e2e-test.js — 実際のブラウザで確かめる (Playwright と Chromium が必要。CI では実行しない)
 *   node bada_meeting/tools/e2e-test.js [スクリーンショットの出力先]
 * 1〜3 の操作はすべてキーボードで行う (マウス・タッチを使わない)。4 はポインタだけで行う。
 * 1. 1 台で全役: 複数行の議題 → 決定。電鍵 (Space の長短) と Alt + 数字で入力
 * 2. P2P 網 (zone): 4 つの画面を一列につなぎ、自動で網になること・主催者なしの会議・zone:// レコード・
 *    結び目の違う端末の排除・担当の引き継ぎを確かめる
 * 4. ポインタ (滞留) だけで複数行を入力して発言する
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

  console.log("ポインタ (滞留) だけで入力する");
  const ptr = await open();
  const hover = async (loc, want) => { await loc.hover(); await ptr.waitForFunction(v => document.getElementById("compose").value === v, want, { timeout: 5000 }); await ptr.mouse.move(2, 2); };
  await hover(ptr.locator("#grid .tile", { hasText: "よ" }), "よ");
  await hover(ptr.locator("#grid .tile", { hasText: "か" }), "よか");
  await hover(ptr.locator("#grid .tile", { hasText: "゛" }), "よが");
  await hover(ptr.locator("#padacts .tile", { hasText: "改行" }), "よが\n");
  await hover(ptr.locator("#grid .tile", { hasText: "も" }), "よが\nも");
  ok(true, "かな盤にポインタを留めるだけで、濁点つき・複数行を入力できる");
  await hover(ptr.locator("#padacts .tile", { hasText: "全部消す" }), "");
  const firstCand = ptr.locator("#cands .tile").first(), label = (await firstCand.innerText()).replace(/^Alt\+\d\s*/, "").replace(/\s*\(\d+%\)$/, "").trim();
  await hover(firstCand, label);
  ok(true, "候補もポインタを留めて入れられる: " + label);
  await ptr.keyboard.press("F7"); await ptr.keyboard.press("Control+a"); await ptr.keyboard.press("Backspace");
  ok(await ptr.locator("#pad").isHidden(), "F7 でポインタ入力を切ると、かな盤が隠れる");
  await ptr.locator("#cands .tile").first().hover(); await sleep(2200);
  ok((await ptr.inputValue("#compose")) === "", "切のときは、留めても入力されない");
  await ptr.mouse.move(2, 2); await ptr.keyboard.press("F7");
  for (const ch of "よやく") await hover(ptr.locator("#grid .tile", { hasText: ch }), (await ptr.inputValue("#compose")) + ch);
  await ptr.locator("#padacts .tile", { hasText: "発言する" }).hover();
  await ptr.waitForFunction(() => BadaMeetingApp.meeting().msgs.length > 0, null, { timeout: 5000 }); await ptr.mouse.move(2, 2);
  await decided(ptr);
  ok((await ptr.evaluate(() => BadaMeetingApp.meeting().msgs[0].text)) === "よやく", "ポインタだけで議題を送り、会議が決定まで進む");
  ok(!(await ptr.evaluate(() => document.documentElement.scrollWidth > innerWidth)), "横スクロールが出ない (ポインタ入力あり)");
  if (shots) await ptr.screenshot({ path: path.join(shots, "meeting-pointer.png") });
  await ptr.close();

  console.log("P2P 網 (zone): 4 台を一列につなぐ → 網が隣どうしを自動でつなぐ (キーボードだけ)");
  const names = ["tokyo", "osaka", "nagoya", "sapporo"], pages = {};
  for (const n of names) {
    const p = pages[n] = await open(n === "sapporo" ? { width: 390, height: 800 } : undefined);
    await p.keyboard.press("F8"); await p.focus("#pname"); await p.keyboard.press("Control+a"); await p.keyboard.insertText(n); await press(p, "#apply"); await p.keyboard.press("Escape");
  }
  ok(await pages.tokyo.evaluate(() => BadaMeetingApp.zoneCheck.ok && BadaMeetingApp.zoneCheck.jones.trefoil === 919492), "起動時に元の zone-lib.bada を Bada で実行し、移植した計算と一致 (Jones 鍵 919492)");
  const link = async (a, b) => {               // a が招待し、b が返信する (手でつなぐのはこの 1 本ずつ)
    await a.keyboard.press("F8"); await a.evaluate(() => { document.getElementById("invite").value = ""; }); await press(a, "#mkinvite");
    await a.waitForFunction(() => document.getElementById("invite").value.length > 100);
    await b.keyboard.press("F8"); await paste(b, "#invitein", await a.inputValue("#invite")); await press(b, "#mkanswer");
    await b.waitForFunction(() => document.getElementById("answer").value.length > 100);
    await paste(a, "#answerin", await b.inputValue("#answer")); await press(a, "#accept");
    await a.keyboard.press("Escape"); await b.keyboard.press("Escape");
    await b.evaluate(() => { document.getElementById("invitein").value = ""; document.getElementById("answer").value = ""; });
  };
  await link(pages.tokyo, pages.osaka); await link(pages.osaka, pages.nagoya); await link(pages.nagoya, pages.sapporo);
  const all = Object.values(pages);
  await Promise.all(all.map(p => p.waitForFunction(() => BadaMeetingApp.node().info().members.length === 4 && BadaMeetingApp.node().peers() === 3, null, { timeout: 60000 }))).catch(async e => {
    for (const n of names) console.log("    状態", n, await pages[n].evaluate(() => JSON.stringify([BadaMeetingApp.node().name, Object.keys(BadaMeetingApp.node().members), Object.keys(BadaMeetingApp.node().links), Object.keys(BadaMeetingApp.node().dialing)])));
    throw e;
  });
  ok(true, "手でつないだのは 3 本。うわさで 4 台を知り、残りのリンクは網が自動で張った (全台が直結 3)");
  const owners = await Promise.all(all.map(p => p.evaluate(() => BadaMeetingApp.node().owner())));
  ok(new Set(owners).size === 1, "全台が同じ担当 (部屋の鍵に最も近い端末) を選ぶ: " + owners[0], owners.join());
  const owner = owners[0], rest = names.filter(n => n !== owner), roleOf = { [rest[0]]: "kikaku", [rest[1]]: "engineer", [rest[2]]: "planner" };
  for (const n of rest) await pages[n].selectOption("#role", roleOf[n]);      // 担当の端末は役割なし (番号を付けて配るだけ)
  await type(pages[rest[2]], "AndroidとWindows向け\nチャットアプリを4週間で"); await pages[rest[2]].keyboard.press("Control+Enter");
  await Promise.all(all.map(decided));
  const logs = await Promise.all(all.map(p => p.evaluate(() => JSON.stringify(BadaMeetingApp.meeting().msgs.map(m => [m.seq, m.role, m.kind, m.text])))));
  ok(new Set(logs).size === 1 && /"decide"/.test(logs[0]), "主催者なしで会議が決定に至り、4 台の議事録が完全に一致する");
  ok(/P2P 網 4 台/.test(await pages.tokyo.locator("#status").innerText()), "状態表示", await pages.tokyo.locator("#status").innerText());
  // zone:// レコード: 預け先は URL の鍵に最も近い端末
  const A = pages[rest[0]], B = pages[rest[1]];
  await A.keyboard.press("F8"); await press(A, "#zput");
  ok(/PUT → 預け先/.test(await A.locator("#zout").innerText()), "議事録を zone:// に公開: " + (await A.locator("#zout").innerText()));
  await A.keyboard.press("Escape"); await sleep(500);
  await B.keyboard.press("F8"); await press(B, "#zget");
  await B.waitForFunction(() => /^200/.test(document.getElementById("zout").textContent), null, { timeout: 10000 });
  ok(/# 会議の議事録と計画書/.test(await B.locator("#zout").innerText()), "別の端末から GET して、封印を開いて読める");
  await B.focus("#zurl"); await B.keyboard.press("Control+a"); await B.keyboard.insertText("zone://kaigi.zone.jp/none"); await press(B, "#zget");
  await B.waitForFunction(() => /^404/.test(document.getElementById("zout").textContent), null, { timeout: 10000 });
  ok(true, "無いレコードは 404 zone-not-found"); await B.keyboard.press("Escape");
  // 結び目 (鍵) が違う端末は網に入れない
  const X = await open();
  await X.keyboard.press("F8"); await X.focus("#pname"); await X.keyboard.press("Control+a"); await X.keyboard.insertText("intruder"); await X.selectOption("#knot", "figure8"); await press(X, "#apply"); await X.keyboard.press("Escape");
  await link(A, X); await sleep(2500);
  ok((await X.evaluate(() => BadaMeetingApp.node().info().members.length)) === 1 && (await A.evaluate(() => BadaMeetingApp.node().info().members.length)) === 4 && (await X.evaluate(() => BadaMeetingApp.meeting().msgs.length)) === 0, "結び目が違う端末は、つないでも網に入れず、議事録も届かない");
  await X.close();
  // 担当の端末が抜ける → 次に近い端末が引き継ぐ
  await pages[owner].close();
  const left = rest.map(n => pages[n]);
  await Promise.all(left.map(p => p.waitForFunction(() => BadaMeetingApp.node().info().members.length === 3, null, { timeout: 30000 })));
  const owners2 = await Promise.all(left.map(p => p.evaluate(() => BadaMeetingApp.node().owner())));
  ok(new Set(owners2).size === 1 && owners2[0] !== owner, "担当が抜けると、残りの全台が次に近い端末 (" + owners2[0] + ") を担当にする", owners2.join());
  await type(pages[rest[1]], "期限を12週間にしましょう"); await pages[rest[1]].keyboard.press("Control+Enter");
  await Promise.all(left.map(p => p.waitForFunction(() => /期限は 12 週間/.test((BadaMeetingApp.meeting().msgs[0] || {}).text || "") && BadaMeetingApp.meeting().decided(), null, { timeout: 60000 })));
  const logs2 = await Promise.all(left.map(p => p.evaluate(() => JSON.stringify(BadaMeetingApp.meeting().msgs.map(m => [m.seq, m.role, m.kind, m.text])))));
  ok(new Set(logs2).size === 1 && !/concern/.test(logs2[0]), "引き継いだ後も会議が進み、期限を延ばすと懸念なしで決定に至る");
  ok(!(await pages[rest[2]].evaluate(() => document.documentElement.scrollWidth > innerWidth)), "横スクロールが出ない (P2P)");
  await pages[rest[0]].keyboard.press("F8"); await sleep(300);
  if (shots) await pages[rest[0]].screenshot({ path: path.join(shots, "meeting-p2p.png") });
  await browser.close();

  console.log("音響電信 (別の端末の音を、偽のマイク入力として聞かせる)");
  // 相手側 (企画とプランナー) が鳴らすはずの音を、同じモデムで作る
  const sr = 48000, agenda = "スマホ向けの予約アプリを\n3か月で作りたい", ref = M.runLocal(agenda);
  const sil = s => new Float32Array(Math.round(sr * s)), parts = [sil(4)];
  const add = (m, byAgent) => Tg.encodeMessage(m, byAgent, byAgent ? Ac.hash4(m.text) : null).forEach(p => { parts.push(Tg.modulate(p, sr).map(v => v * 0.5), sil(0.4)); });
  // 実際の端末は、次の発言が聞こえなければ送り直す。ここでも同じ電文を 2 回ずつ入れておく (重複は受け側が捨てる)
  add(ref.msgs[0], false); parts.push(sil(1)); add(ref.msgs[1], true); parts.push(sil(1.5)); add(ref.msgs[1], true);
  parts.push(sil(9));                                     // この間に、画面 (エンジニア) が見積りを送信する
  add(ref.msgs[3], true); parts.push(sil(2)); add(ref.msgs[3], true); parts.push(sil(4));
  const pcm = new Float32Array(parts.reduce((s, x) => s + x.length, 0)); let o = 0; parts.forEach(x => { pcm.set(x, o); o += x.length; });
  const wavPath = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "bm-")), "peer.wav"); fs.writeFileSync(wavPath, Tg.wav(pcm, sr));
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
