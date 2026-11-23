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

console.log("思念入力");
const lex = T.lexicon(a.msgs), p0 = T.predict("", lex, 8), p1 = T.predict("見", lex, 5);
ok(p0.length === 8 && p0.every(x => T.PHRASES.includes(x.text)) && near(p0.reduce((s, x) => s + x.p, 0), 1), "入力が空のときは定型句。確率の合計は 1");
ok(p1.length > 0 && p1.every(x => x.text.startsWith("見") && "見" + x.insert === x.text), "頭の文字から続きを予測する", JSON.stringify(p1));
ok(T.predict("予約と", lex, 5).some(x => x.text === "予約と取り消し"), "議事録に出た語句を候補にする");
ok(p0.every((x, i) => i === 0 || x.p <= p0[i - 1].p) && T.dwellMs(p0[0], 8, 800) < T.dwellMs(p0[7], 8, 800), "確からしい候補ほど滞留が短い");
ok(T.dwellMs(p0[0], 8, 800) >= 280 && T.dwellMs(p0[7], 8, 800) <= 1280 && T.dwellMs(p1[0], 1, 800) === 280, "滞留時間は基準の 0.35〜1.6 倍");
ok(T.progress(400, 800) === 0.5 && T.progress(2000, 800) === 1, "滞留の進み具合");

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
const scripts = Array.from(html.matchAll(/<script>([\s\S]*?)<\/script>/g), m => m[1]);
const sb = { console, TextEncoder, TextDecoder }; sb.window = sb; vm.createContext(sb);
try { vm.runInContext(scripts[0], sb); ok(["BadaEntropy", "BadaAgents", "BadaMeeting", "BadaThought", "BadaNet"].every(k => sb[k]), "埋め込んだライブラリが読み込める"); }
catch (e) { ok(false, "埋め込んだライブラリが読み込める", e.message); }
try { new vm.Script(scripts[1]); ok(true, "画面のスクリプトの構文"); } catch (e) { ok(false, "画面のスクリプトの構文", e.message); }

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
