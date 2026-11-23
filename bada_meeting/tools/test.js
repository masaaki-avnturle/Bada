/*
 * test.js — Bada 思念会議の単体テスト (Node だけで動く)
 *   node bada_meeting/tools/test.js
 */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const En = require("../src/entropy.js"), Ag = require("../src/agents.js"), M = require("../src/meeting.js"), T = require("../src/thought.js"), N = require("../src/net.js");
let pass = 0, fail = 0;
const ok = (c, name, extra) => { if (c) { pass++; console.log("  ✓ " + name); } else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  → " + String(extra).slice(0, 300) : "")); } };
const near = (a, b, e) => Math.abs(a - b) < (e || 1e-9);

console.log("エントロピー方程式群");
ok(near(En.density(Math.E), Math.E) && En.density(1) === 0, "(E1) x log x");
ok(near(En.entropy(En.bag("alpha beta gamma delta")), Math.log(4)), "(E1) 一様な 4 語は log 4");
ok(near(En.divergence(En.bag("alpha beta"), En.bag("alpha beta")), 0) && near(En.divergence(En.bag("alpha beta"), En.bag("gamma delta")), Math.LN2), "ずれは 0 から log 2");
ok(En.gate(Math.log(1.7632228343518968) + 1e-9, 0).pass && !En.gate(Math.log(1.7632228343518968) - 1e-6, 0).pass, "(E2) D = 0 のしきい値は x log x = 1 の根");
ok(En.gate(2, 0.2).margin > En.gate(2, 0.6).margin, "(E2) ずれが大きいほど門は厳しい");
let z = 0, half = 0; for (let r = 1; r < 200000; r++) { z += En.kernel(r); if (r === 100000) half = z; }
ok(z - half < 1e-7 && z > 0.69 && z < 0.70 && En.kernel(1) > En.kernel(2), "(E3) 核の総和は収束する (約 0.693)", z);
ok(En.flow([0.5, 0.5, 0.5]) === 0 && En.flow([0.1, 0.6, 0.1]) > En.flow([0.3, 0.35, 0.3]), "(E4) 話題が飛ぶほど流れ F が大きい");
ok(En.tokens("予約アプリを3か月で作りたい").includes("予約") && En.tokens("アプリケーションエンジニア").includes("アプリケーションエンジニア"), "字句化");

console.log("役割の能力");
ok(Ag.domainOf("予約アプリ").name === "予約・日程" && Ag.domainOf("チャット").name === "メッセージング" && Ag.domainOf("何か便利なもの").name === "一般", "分野の判定");
ok(Ag.deadlineOf("3か月で") === 13 && Ag.deadlineOf("10週間") === 10 && Ag.deadlineOf("１２週間") === 12 && Ag.deadlineOf("すぐに") === null, "期限の読み取り");
ok(Ag.platformsOf("AndroidとWindows").join() === "Android,Windows" && Ag.platformsOf("勤怠管理").join() === "Web", "対応環境の判定");
const f1 = [{ name: "a", weeks: 2 }, { name: "b", weeks: 3 }], e1 = Ag.estimate(f1, ["Web"], 2), e2 = Ag.estimate(f1, ["Android", "iOS"], 2);
ok(e1.impl === 5 && near(e1.person_weeks, 8) && near(e1.calendar_weeks, 4) && near(e2.impl, 6.8, 0.05), "見積りの計算 (工程の上乗せ・環境数の上乗せ)", JSON.stringify(e1));
ok(Ag.directive("期限を8週間にしましょう").deadline_weeks === 8 && Ag.directive("8週間かかりました") === null, "人の発言の指示を読む");

console.log("会議");
const kinds = mt => mt.msgs.map(m => m.kind).join(" ");
const a = M.runLocal("スマホ向けの予約アプリを3か月で作りたい");
ok(kinds(a) === "agenda propose estimate concern revise estimate schedule agree agree decide", "期限を超える → 範囲を絞って決定", kinds(a));
const pa = a.msgs.filter(m => m.kind === "revise")[0].data, sa = a.msgs.find(m => m.kind === "schedule").data;
ok(pa.later.length === 1 && pa.later[0].name === "口コミ" && pa.features.every(f => f.priority <= pa.later[0].priority), "優先度の低い機能から次期へ回す");
ok(sa.total_weeks <= 13 && near(sa.milestones[sa.milestones.length - 1].end_week, sa.total_weeks), "日程は期限に収まり、工程の合計と一致する", JSON.stringify(sa.milestones));
const b = M.runLocal("社内の勤怠管理をWebで");
ok(kinds(b) === "agenda propose estimate schedule agree agree decide" && b.msgs.find(m => m.kind === "schedule").data.deadline_weeks === null, "期限の指定が無ければ見積りを期限にする", kinds(b));
const c = M.runLocal("AndroidとWindows向けチャットアプリを4週間で"), sc = c.msgs.find(m => m.kind === "schedule").data, rc = c.msgs.find(m => m.kind === "revise");
ok(c.decided() && rc.data.features.every(f => f.priority === 1) && /これ以上削れません/.test(rc.text) && sc.total_weeks <= rc.data.deadline_weeks, "最重要の機能は削らず、期限の延長を提案する", rc.text);
ok(["学習アプリ", "健康記録アプリを2か月で", "パズルゲームを6週間で", "EC サイトを Web で 5 か月", "何か便利なものを作りたい"].every(t => M.runLocal(t).decided()), "どの分野でも決定に至る");
const off = new M.Meeting();
off.add({ seq: 0, role: "host", kind: "agenda", text: "スマホ向けの予約アプリを3か月で作りたい" });
ok(!off.add({ seq: 1, kind: "comment", text: "今日の昼ごはんは何にしますか" }).measure.pass && off.add({ seq: 2, kind: "comment", text: "予約の取り消しは前日までにしたい" }).measure.pass, "門 (E2): 議題から外れた発言は通らず、議題に沿う発言は通る");
ok(off.add({ seq: 2, kind: "comment", text: "重複" }) === null && off.stats().off_topic === 1, "同じ番号の発言は 2 度入らない");
ok(off.next("kikaku").kind === "propose", "人の発言が挟まっても役割は議題に応じる");
const md = a.minutes();
ok(/## 1\. 企画/.test(md) && /## 3\. 日程/.test(md) && /決定済み/.test(md) && /次期に回す機能: 口コミ/.test(md) && /担当者による確認が必要/.test(md), "議事録と計画書");

console.log("入力 (電鍵・候補・ポインタ)");
const lex = T.lexicon(a.msgs), p0 = T.predict("", lex, 8), p1 = T.predict("見", lex, 5);
ok(p0.length === 8 && p0.every(x => T.PHRASES.includes(x.text)) && near(p0.reduce((s, x) => s + x.p, 0), 1), "入力が空のときは定型句。確率の合計は 1");
ok(p1.length > 0 && p1.every(x => x.text.startsWith("見") && "見" + x.insert === x.text), "頭の文字から続きを予測する", JSON.stringify(p1));
ok(T.predict("1 行目\n予約と", lex, 5).some(x => x.text === "予約と取り消し"), "複数行でも、最後の行の末尾から候補を出す");
ok(p0.every((x, i) => i === 0 || x.p <= p0[i - 1].p), "候補は確率の高い順");
const uniq = t => new Set(Object.values(t)).size === Object.keys(t).length;
ok(uniq(T.KANA) && uniq(T.LATIN), "モールス符号表に重複がない (和文 " + Object.keys(T.KANA).length + " 字 / 欧文 " + Object.keys(T.LATIN).length + " 字)");
ok(T.LATIN.S === "..." && T.LATIN.O === "---" && T.KANA["い"] === ".-" && T.KANA["ん"] === ".-.-." && T.decodeSymbol("--.--", "kana") === "あ" && T.decodeSymbol("......", "kana") === null, "符号表の値");
ok(T.append("か", "゛") === "が" && T.append("は", "゜") === "ぱ" && T.append("ん", "゛") === "ん" && T.append("", "゛") === "" && T.append("a", "b") === "ab", "濁点・半濁点は直前のかなに付く");
ok(T.toMorse("しゅっぱつ", "kana") === T.toMorse("しゆつはつ", "kana").replace(/-\.\.\. \.--\.$/, "-... ..--. .--."), "小書きの字は大きい字の符号で送る");
ok(T.toMorse("が", "kana") === ".-.. .." && T.toMorse("sos", "latin") === "... --- ...", "文字 → 符号");
// 電鍵: 長短と間合いだけで打つ
function keyIn(text, mode, unit) {
  const k = new T.Keyer(unit, mode); let t = 0, out = "";
  const emit = evs => evs.forEach(e => { if (e.char) out = T.append(out, e.char); });
  for (const line of text.split("\n")) {
    if (out || line !== text.split("\n")[0]) out += "\n";
    for (const sym of T.toMorse(line, mode).split(" ")) {
      if (sym === "/") { t += 7 * unit; emit(k.tick(t)); continue; }
      for (const c of sym) { emit(k.down(t)); t += c === "." ? 0.8 * unit : 3.2 * unit; emit(k.up(t)); t += 0.9 * unit; }
      t += 3 * unit; emit(k.tick(t));
    }
    t += 10 * unit; emit(k.tick(t));
  }
  return out;
}
ok(keyIn("よやくあぷりをつくりたいです。", "kana", 100) === "よやくあぷりをつくりたいです。", "電鍵: 和文を長短だけで入力できる");
ok(keyIn("きげんは\n12しゅうかん", "kana", 150) === "きげんは\n12しゆうかん", "電鍵: 複数行 (改行は Enter)。小書きの字は大きい字になる", JSON.stringify(keyIn("きげんは\n12しゅうかん", "kana", 150)));
ok(keyIn("sos help 73", "latin", 100).trim() === "sos help 73", "電鍵: 欧文は語の間に空白が入る", JSON.stringify(keyIn("sos help 73", "latin", 100)));
const kk = new T.Keyer(100, "kana"); kk.down(0); kk.up(50); kk.down(140); kk.up(190); kk.down(280); kk.up(330); kk.down(420); kk.up(470); kk.down(560); kk.up(610); kk.down(700); kk.up(750);
ok(kk.tick(1100)[0].unknown === "......" && kk.idle(1200), "表にない符号は文字にせず知らせる");
const km = new T.Keyer(100, "kana"); km.down(0); km.up(50); km.tick(400); km.setMode("latin");
ok(km.tick(5000).length === 0 && km.idle(5000), "和文 / 欧文を切り替えた直後に余分な空白が入らない");

ok(T.dwellMs(p0[0], 8, 800) < T.dwellMs(p0[7], 8, 800) && T.dwellMs(p0[0], 8, 800) >= 280 && T.dwellMs(p0[7], 8, 800) <= 1280 && T.dwellMs(p1[0], 1, 800) === 280, "ポインタの滞留: 確からしい候補ほど短い (基準の 0.35〜1.6 倍)");
ok(T.GRID.length === 11 && T.GRID.join("").includes("↵") && T.GRID.join("").includes("゛"), "かな盤に改行と濁点がある");

console.log("音響電信 (Bada Telegraph の FSK モデム)");
const Tg = require("../src/telegraph.js"), Ac = require("../src/acoustic.js");
ok(Tg.F_SPACE === 1000 && Tg.F_MARK === 1600 && Tg.BAUD === 100, "Bada Telegraph と同じ 1000 / 1600 Hz・100 baud");
const fb = Tg.frameBytes([1, 2, 3]);
ok(fb[0] === 0x7E && fb[1] === 3 && fb[5] === ((0x7E + 3 + 1 + 2 + 3) & 0xFF), "フレーム = SOF 0x7E + 長さ + 本体 + チェックサム");
let seed = 11; const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296 - 0.5; };
function channel(texts, sr, gain, noise, chunk) {
  const sig = []; const sil = n => { for (let i = 0; i < n; i++) sig.push(0); };
  sil(Math.round(sr * 0.31));
  texts.forEach(t => { Tg.modulate(new TextEncoder().encode(t), sr).forEach(v => sig.push(v * gain)); sil(Math.round(sr * 0.27)); });
  const x = Float32Array.from(sig, v => v + noise * 2 * rnd()), got = [], d = new Tg.Demodulator(sr, p => got.push(new TextDecoder().decode(p)));
  for (let i = 0; i < x.length; i += chunk) d.feed(x.subarray(i, i + chunk));
  return got;
}
const texts = ["hello", "議題: 予約アプリ\n2 行目\n3 行目", "x".repeat(255)];
ok(JSON.stringify(channel(texts, 44100, 0.9, 0, 4096)) === JSON.stringify(texts), "変調 → 復調 (複数行・255 バイトを含む)");
ok(JSON.stringify(channel(texts, 48000, 0.5, 0.05, 4096)) === JSON.stringify(texts), "48 kHz・音量半分・雑音あり");
ok(JSON.stringify(channel(texts, 44100, 0.6, 0.3, 1024)) === JSON.stringify(texts), "雑音が信号の半分の振幅でも復調できる");
ok(channel(texts, 44100, 0.5, 0.6, 4096).length === 0, "雑音が信号を上回ると復調しない (誤った文章も出さない)");
let falseFrames = 0; const dn = new Tg.Demodulator(44100, () => falseFrames++);
dn.feed(Float32Array.from({ length: 44100 * 10 }, () => 0.5 * rnd())); dn.feed(new Float32Array(44100 * 3));
ok(falseFrames === 0, "雑音と無音だけではフレームを検出しない");
const pk = Tg.encodeMessage({ seq: 3, role: "planner", kind: "concern", text: "x" }, true, Ac.hash4("x"))[0], dp = Tg.decodePacket(pk);
ok(pk.length === 15 && dp.type === 1 && dp.seq === 3 && dp.role === "planner" && dp.kind === "concern" && dp.body.length === 4, "役割の発言は 15 バイトのパケット (本文は送らずハッシュだけ)");
ok(Tg.seconds(pk.length) < 2.1, "役割の発言 1 つの送信は約 2 秒", Tg.seconds(pk.length));
const bad = pk.slice(); bad[4] ^= 1;
ok(Tg.decodePacket(bad) === null && Tg.decodePacket(Uint8Array.from([1, 2, 3])) === null, "CRC-16 が合わないパケットは捨てる");
const long = "長い発言です。\n".repeat(60), lp = Tg.encodeMessage({ seq: 1, role: "guest", kind: "comment", text: long }, false, null), asm = new Tg.Assembler();
let joined = null; lp.forEach(q => { joined = asm.add(Tg.decodePacket(q)) || joined; });
ok(lp.length > 1 && lp.every(q => q.length <= 255) && joined === long, "長い複数行の文章は部分に分けて送り、組み立て直す (" + lp.length + " 部分)");
// 3 端末を、実際のモデム (変調 → 雑音 → 復調) でつないだ模擬の音響空間。drops 番目の送信は誰にも届かない
function acousticMeeting(agenda, drops, noise) {
  const sr = 16000, pend = [], air = []; let clock = 0, n = 0;
  const timers = { set: (f, ms) => { const h = { f, at: clock + ms }; pend.push(h); return h; }, clear: h => { const i = pend.indexOf(h); if (i >= 0) pend.splice(i, 1); } };
  const nodes = ["kikaku", "engineer", "planner"].map(role => {
    const nd = { role, mt: new M.Meeting() };
    nd.demod = new Tg.Demodulator(sr, f => nd.link.receive(f));
    nd.link = new Ac.AcousticLink({ meeting: () => nd.mt, timers, onMessage: m => { if (nd.mt.add(m)) nd.dirty = true; }, io: { transmit: p => air.push({ from: nd, p }) } });
    return nd;
  });
  nodes[0].link.send({ role: "host", kind: "agenda", text: agenda });
  for (let guard = 0; guard < 800; guard++) {
    if (air.length) {
      const { from, p } = air.shift(); if (drops.includes(n++)) continue;
      p.forEach(q => { const s = Tg.modulate(q, sr), x = Float32Array.from({ length: s.length + sr / 2 }, (_, i) => (i < s.length ? s[i] * 0.5 : 0) + noise * 2 * rnd()); nodes.forEach(o => { if (o !== from) o.demod.feed(x); }); });
      continue;
    }
    let acted = false;
    for (const nd of nodes) if (nd.dirty) { nd.dirty = false; const d = nd.mt.next(nd.role); if (d) { nd.link.send(Object.assign({ role: nd.role }, d)); acted = true; break; } }
    if (acted) continue;
    if (!pend.length) break;
    pend.sort((x, y) => x.at - y.at); const h = pend.shift(); clock = h.at; h.f();
  }
  return { same: new Set(nodes.map(nd => JSON.stringify(nd.mt.msgs.map(m => [m.seq, m.role, m.kind, m.text])))).size === 1, decided: nodes.every(nd => nd.mt.decided()), n, agenda: nodes[2].mt.msgs[0] && nodes[2].mt.msgs[0].text };
}
const multi = "スマホ向けの予約アプリを\n3か月で作りたい\n(複数行の議題)";
let r = acousticMeeting(multi, [], 0.05);
ok(r.same && r.decided && r.agenda === multi && r.n === 10, "音だけで 3 端末が会議し、議事録が一致する (送信 10 回)", JSON.stringify(r));
r = acousticMeeting(multi, [0], 0.1);
ok(r.same && r.decided, "最初の議題が届かなくても、要求と送り直しで追いつく", JSON.stringify(r));
r = acousticMeeting(multi, [0, 1, 2, 5, 9], 0.1);
ok(r.same && r.decided, "送信が 5 回失われても決定に至る", JSON.stringify(r));
r = acousticMeeting(multi, [3, 4, 7, 8, 12, 13], 0.15);
ok(r.same && r.decided, "別の箇所で 6 回失われても決定に至る", JSON.stringify(r));

console.log("通信 (パケットと主催者の配信)");
const raw = N.pack({ t: "msg", m: { text: "こんにちは" } });
ok(N.unpack(raw).m.text === "こんにちは", "パケットの往復");
let broken = false; try { N.unpack(raw.replace("こんにちは", "こんばんは")); } catch (e) { broken = true; }
ok(broken, "書き換えられたパケットを SHA-256 で検出する");
// 主催者 1 + 参加者 2 を、データチャネルの代わりの配線でつなぐ
const pipe = () => { const A = { readyState: "open" }, B = { readyState: "open" }; A.send = d => B.onmessage({ data: d }); B.send = d => A.onmessage({ data: d }); return [A, B]; };
const logs = [[], [], []], hubs = [new N.Hub({ host: true, onMessage: m => logs[0].push(m) }), new N.Hub({ host: false, onMessage: m => logs[1].push(m) }), new N.Hub({ host: false, onMessage: m => logs[2].push(m) })];
for (const g of [1, 2]) { const [x, y] = pipe(); const hl = { ch: x }, gl = { ch: y }; hubs[0].links.push(hl); hubs[0]._wire(hl); hubs[g].links = [gl]; hubs[g]._wire(gl); }
hubs[0].send({ role: "host", kind: "agenda", text: "議題" }); hubs[1].send({ role: "engineer", kind: "comment", text: "参加者 1 から" }); hubs[2].send({ role: "planner", kind: "comment", text: "参加者 2 から" });
ok(logs.every(l => JSON.stringify(l) === JSON.stringify(logs[0])) && logs[0].map(m => m.seq).join() === "0,1,2", "主催者が通し番号を付け、全員の議事録が同じ順序になる");
hubs[1].links[0].ch.onmessage({ data: "{壊れたデータ" });
ok(logs[1].length === 3, "壊れたパケットは無視する");
let noHost = false; try { new N.Hub({ host: false }).send({ kind: "comment", text: "x" }); } catch (e) { noHost = true; }
ok(noHost, "主催者につながっていなければ送信を断る");

console.log("配布 HTML");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
ok(!/(src|href)\s*=\s*["']https?:/.test(html) && !/stun:/.test(html), "外部の資源も STUN サーバーも参照しない");
ok(/pointerenter/.test(html) && /id="ptrmode"/.test(html) && /rows="6"/.test(html), "ポインタ (滞留) 入力があり、発言欄は複数行");
const multiMt = M.runLocal("スマホ向けの予約アプリを\n3か月で作りたい");
ok(multiMt.decided() && /\*\*議題\*\*: スマホ向けの予約アプリを \/ 3か月で作りたい/.test(multiMt.minutes()), "複数行の議題でも会議が成り立ち、議事録に収まる");
const scripts = Array.from(html.matchAll(/<script>([\s\S]*?)<\/script>/g), m => m[1]);
const sb = { console, TextEncoder, TextDecoder }; sb.window = sb; vm.createContext(sb);
try { vm.runInContext(scripts[0], sb); ok(["BadaEntropy", "BadaAgents", "BadaMeeting", "BadaThought", "BadaNet", "BadaTelegraph", "BadaAcoustic"].every(k => sb[k]), "埋め込んだライブラリが読み込める"); }
catch (e) { ok(false, "埋め込んだライブラリが読み込める", e.message); }
try { new vm.Script(scripts[1]); ok(true, "画面のスクリプトの構文"); } catch (e) { ok(false, "画面のスクリプトの構文", e.message); }

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
