/*
 * engine-test.js — BadaGPT電信のエンジン単体テスト (Node で実行)
 *
 *   node bada_gpt_telegraph/tools/engine-test.js
 *
 * src/engine.js · comprehend.js · generate.js · paper.js を 1 つの文脈で読み込み、
 * DOM を使わない純ロジックを検証します:
 *   1. 電信エンジン — Bada インタプリタ / Ξ / Jones / モールス / FSK 往復
 *   2. 全体把握 — モジュール・対象・項目・機能・配色・対象環境・題名・網羅率
 *   3. 生成と検証 — 全モジュールの単独生成と全部入り、検証の合否、埋め込みの安全性
 *   4. 論文 — 章立てと数値の整合
 *   5. ビルド一式 — ZIP 構造 / appId / ワークフロー
 *   6. PDF / Markdown
 *   7. Claude (任意) — リクエスト本体 / SSE / HTML 抽出
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.join(__dirname, "..");
const ctx = { console, TextEncoder, TextDecoder, atob, btoa, Uint8Array, Float32Array, Map };
vm.createContext(ctx);
for (const f of ["src/engine.js", "src/comprehend.js", "src/generate.js", "src/paper.js"]) {
  vm.runInContext(fs.readFileSync(path.join(root, f), "utf8"), ctx, { filename: f });
}
const E = (expr) => vm.runInContext(expr, ctx);
const call = (fn, ...args) => E(fn).apply(null, args);

let pass = 0, fail = 0;
function ok(cond, name) {
  if (cond) { pass++; } else { fail++; console.log("  ✗ " + name); }
}
function section(t) { console.log("■ " + t); }

/* 1. 電信エンジン */
section("電信エンジン");
{
  const log = [];
  const it = new (E("BadaInterp"))((ns, cmd) => log.push(ns + "::" + cmd));
  const out = it.run(E("BADAGPT_PROGRAM"));
  ok(log.join(",") === "Tele::encode,Tele::knot,Tele::teleport,Tele::graviton,Tele::send,GPT::comprehend,GPT::plan,GPT::generate,GPT::verify,GPT::paper", "badagpt.bada が Tele:: → GPT:: の順に全命令を実行");
  ok(/^Ω::push thought_node/.test(out[0]), "Omega::push のトレース");
  let threw = false; try { it.exec("nonsense ???"); } catch (e) { threw = /syntax error/.test(e.message); }
  ok(threw, "不正な行は構文エラー");
  ok(Math.abs(call("shannon", "aabb") - 1) < 1e-12, "シャノンエントロピー H(aabb) = 1");
  ok(Math.abs(call("betaFn", 2, 3) - 1 / 12) < 1e-9, "β(2,3) = 1/12");
  ok(isFinite(call("bXi", "依頼文")) && call("bXi", "依頼文") > 0, "Ξ は有限の正値");
  const J = E("Jones");
  ok(J.bracketStr(3).length > 0 && isFinite(J.Vreal(3, 2)), "Jones 多項式 (三葉結び目)");
  ok(call("toMorse", "SOS") === "... --- ...", "モールス SOS");
  const M = call("telegraphMetrics", "家計簿をつけたい");
  ok(M.n >= 2 && M.n <= 12 && M.fidelity >= 0.5 && M.fidelity < 1, "電信指標の範囲");
  for (const [txt, sr] of [["読んだ本を管理したい。青いデザインで。", 44100], ["HELLO BadaGPT 電信 ⚡", 48000], ["x", 22050]]) {
    const s = call("fskModulate", txt, sr);
    ok(call("fskDemodulate", s, sr) === txt, "FSK 往復 (" + sr + " Hz): " + txt);
  }
  const noisy = call("fskModulate", "ノイズ耐性テスト", 44100);
  for (let i = 0; i < noisy.length; i++) noisy[i] = noisy[i] * 0.4 + (Math.random() - 0.5) * 0.3;
  ok(call("fskDemodulate", noisy, 44100) === "ノイズ耐性テスト", "FSK 雑音下の復号");
  const long = "長".repeat(300);
  ok(call("fskDemodulate", call("fskModulate", long, 44100), 44100) === long, "FSK 256 バイト超 (長さ 2 バイト)");
  ok(call("fskDemodulate", new Float32Array(44100), 44100) === "", "無音は空文字");
}

/* 2. 全体把握 */
section("全体把握");
const comp = (t) => call("comprehend", t);
{
  const s = comp("読んだ本を管理したい。項目はタイトル、著者、読了日、評価、感想。評価順に並べ替えたい。青いダークなデザインで、スマホとWindowsで使いたい");
  ok(s.modules.map(m => m.id).join() === "records", "本: records モジュール");
  ok(s.entity === "本", "本: 対象 = 本");
  ok(s.fields.map(f => f.name + ":" + f.type).join() === "タイトル:string,著者:string,読了日:date,評価:rating,感想:text", "本: 項目と型");
  ok(s.features.sort && !s.features.sort.assumed, "本: 並べ替え (明示)");
  ok(s.features.search && s.features.search.assumed, "本: 検索 (仮定)");
  ok(s.theme.mode === "dark" && s.theme.accent === "#4f8cff", "本: ダーク + 青");
  ok(s.platforms.join() === "android,windows", "本: スマホ + Windows");
  ok(s.coverage === 1 && s.unresolved.length === 0, "本: 網羅率 100%");
  ok(s.title === "本の管理アプリ", "本: 題名の自動命名");
  ok(s.clauses.length === 5, "本: 5 節 (項目の列挙は 1 節)");
}
{
  const s = comp("毎月の家計簿をつけたい。支出と収入を記録してグラフで見たい。緑色で明るいデザインにして、CSVで書き出せるように。");
  ok(s.modules.map(m => m.id).join() === "budget", "家計簿: budget のみ (records を重ねない)");
  ok(s.theme.mode === "light" && s.theme.accentName === "緑", "家計簿: ライト + 緑");
  ok(s.features.chart && !s.features.chart.assumed && s.features.export && !s.features.export.assumed, "家計簿: グラフ・CSV (明示)");
  ok(s.platforms.length === 3 && s.assumptions.some(a => /プラットフォーム/.test(a)), "家計簿: 対象未指定は 3 種 + 仮定を記録");
}
{
  const s = comp("勉強用にポモドーロタイマーと単語帳クイズ、それとToDoリストが欲しい。音で知らせて。");
  ok(["timer", "quiz", "todo"].every(id => s.modules.some(m => m.id === id)), "勉強: timer + quiz + todo");
  ok(s.features.sound, "勉強: 音");
}
{
  const s = comp("「ワインノート」というアプリ。ワインの銘柄・産地・購入日・評価を記録");
  ok(s.title === "ワインノート", "ワイン: 「」の題名");
  ok(s.entity === "ワイン" && s.fields.length === 4, "ワイン: 対象と項目");
  ok(!s.modules.some(m => m.id === "notes"), "ワイン: 題名中の「ノート」でメモを呼ばない");
}
{
  const s = comp("Book title:string author:string price:integer read:boolean を管理");
  ok(s.entity === "Book" && s.fields.map(f => f.type).join() === "string,string,number,bool", "Rails 形式の項目");
}
{
  const s = comp("タスクを管理したい。期限も");
  ok(s.modules.map(m => m.id).join() === "todo", "「タスクを管理」は todo へ");
}
{
  const s = comp("よくわからないけど何か便利なものをお願いします");
  ok(s.modules.map(m => m.id).join() === "notes,todo" && s.assumptions.length >= 1, "曖昧な依頼は メモ + ToDo と仮定");
}
{
  const s = comp("顧客を管理したい。テレパシーで相手の気持ちを当てる機能も");
  ok(s.fields.map(f => f.name).join() === "名前,会社,電話,メール,メモ", "顧客: 既定の項目");
  ok(s.unresolved.length === 1 && /テレパシー/.test(s.unresolved[0]) && s.coverage < 1, "解釈できない節は未解釈として保持");
}
ok(call("splitClauses", "").length === 0 && comp("").modules.length > 0, "空の依頼でも落ちない");

/* 3. 生成と検証 */
section("生成と検証");
{
  const ids = Object.keys(E("MODULE_IMPL"));
  ok(ids.length === 14, "モジュール 14 種");
  for (const id of ids) {
    const s = comp("アプリを作って");
    s.modules = [{ id, label: id, icon: "*", reason: "test" }];
    if (id === "records") { s.entity = "本"; s.fields = [{ key: "f0", name: "題", type: "string" }, { key: "f1", name: "点", type: "number" }]; }
    const g = call("generateApp", s), v = call("verifyApp", g.html, s);
    ok(v.ok, "単独生成 + 検証: " + id + (v.ok ? "" : " " + JSON.stringify(v.checks.filter(c => !c.ok))));
  }
  const all = comp("全部入りのアプリを作って");
  all.modules = ids.map(id => ({ id, label: id, icon: "*", reason: "t" }));
  all.entity = "本"; all.fields = [{ key: "f0", name: "題", type: "string" }];
  all.features = { search: {}, sort: {}, export: {}, chart: {}, sound: {}, print: {} };
  const g = call("generateApp", all);
  ok(call("verifyApp", g.html, all).ok, "全 14 モジュール + 全機能");
  ok((g.html.match(/<section id="p-/g) || []).length === 14 && (g.html.match(/data-tab=/g) || []).length === 14, "タブとパネル 14 個");
  ok(!/https?:\/\//.test(g.html.replace(/https?:\/\/[^"'\s]*\.(?:w3|cordova)\.org[^"'\s]*/g, "")), "外部 URL なし");

  const evil = comp("「</script><script>alert(1)</script>」という名前で本を管理");
  const ge = call("generateApp", evil);
  ok(call("verifyApp", ge.html, evil).ok, "題名に </script> を含んでも検証合格");
  ok((ge.html.match(/<\/script>/g) || []).length === 1, "埋め込みで script が途切れない");

  const bad = call("verifyApp", "<!DOCTYPE html><html><script>function(</script><script src=\"https://cdn.example/x.js\"></script></html>", null);
  ok(!bad.ok && bad.checks.filter(c => !c.ok).length === 2, "検証が構文エラーと外部読み込みを検出");
  ok(call("extractScripts", "<script>a()</script><script type=\"application/x-bada\">set x = 1</script><script src=\"x.js\"></script>").length === 1, "JS 以外・src 付きの script は対象外");
  ok(call("fileBase", "本の管理/アプリ: v1?") === "本の管理アプリ_v1" && call("fileBase", "") === "badagpt-app", "ファイル名の整形");
}

/* 4. 論文 */
section("論文");
{
  const s = comp("顧客を管理したい。テレパシーで相手の気持ちを当てる機能も。赤いデザインで印刷したい");
  const g = call("generateApp", s), v = call("verifyApp", g.html, s);
  const md = call("writePaper", s, g, v, { author: "山口 雅旭", date: "2026-10-12" });
  for (const h of ["## 要旨", "## 1. 序論", "## 2. 方法", "## 3. 結果", "### 3.1 依頼の全体把握", "### 3.4 検証", "## 4. 考察", "## 5. 結論", "## 参考文献"]) ok(md.includes(h), "論文の章: " + h);
  ok(md.includes("山口 雅旭") && md.includes("2026-10-12"), "著者と日付");
  ok(md.includes("「テレパシーで相手の気持ちを当てる機能も」"), "未解釈の節を考察に明記");
  ok(md.includes("網羅率 " + Math.round(s.coverage * 100) + "%"), "網羅率の数値が一致");
  ok(md.includes("脳の信号を読み取るものではない"), "限界の明記");
  const html = call("mdToHtml", md);
  ok(/<table>/.test(html) && /<blockquote>/.test(html) && /<h1>/.test(html), "論文 Markdown → HTML (表・引用)");
}

/* 5. ビルド一式 */
section("ビルド一式");
{
  const s = comp("毎月の家計簿をつけたい");
  const g = call("generateApp", s);
  const files = call("projectFiles", s, g.html, "# paper");
  const names = files.map(f => f.path);
  for (const p of ["README.md", "www/index.html", "paper/paper.md", "electron/package.json", "electron/main.js", "cordova/config.xml", ".github/workflows/build.yml"]) ok(names.includes(p), "同梱: " + p);
  const pkg = JSON.parse(files.find(f => f.path === "electron/package.json").data);
  ok(/^io\.github\.badagpt\.[a-z][a-z0-9_]*$/.test(pkg.build.appId), "appId は Java パッケージ名の形式: " + pkg.build.appId);
  ok(pkg.build.win.target.includes("nsis") && pkg.build.linux.target.includes("AppImage") && pkg.build.linux.target.includes("deb"), "Windows + Linux ターゲット");
  const wf = files.find(f => f.path === ".github/workflows/build.yml").data;
  ok(/android-apk:/.test(wf) && /windows-exe:/.test(wf) && /linux-app:/.test(wf), "ワークフローに 3 ジョブ");
  ok(call("appIdFor", "123-abc") === "io.github.badagpt.app_123_abc", "数字始まりの slug も有効な appId");
  const z = call("zipBuild", files);
  ok(z[0] === 0x50 && z[1] === 0x4B && z[2] === 3 && z[3] === 4, "ZIP ローカルヘッダ");
  const eocd = z.length - 22;
  ok(z[eocd] === 0x50 && z[eocd + 1] === 0x4B && z[eocd + 2] === 5 && z[eocd + 3] === 6 && z[eocd + 10] === files.length, "ZIP 終端レコードとファイル数");
  ok(call("crc32", call("utf8", "123456789")) === 0xCBF43926, "CRC-32 標準値");
}

/* 6. PDF / Markdown */
section("PDF / Markdown");
{
  const jpeg = new Uint8Array([0xFF, 0xD8, 0xFF, 0xD9]);
  const pdf = call("pdfFromJpegs", [{ jpeg, w: 10, h: 10 }, { jpeg, w: 10, h: 10 }], "論文 test");
  const txt = Buffer.from(pdf).toString("latin1");
  ok(txt.startsWith("%PDF-1.4") && txt.trimEnd().endsWith("%%EOF") && /\/Count 2/.test(txt), "PDF 構造");
  const m = txt.match(/startxref\n(\d+)/);
  ok(m && txt.slice(+m[1], +m[1] + 4) === "xref", "PDF startxref が xref を指す");
  const b = call("mdBlocks", "# T\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n> q\n- li\n```\ncode\n```");
  ok(b.map(x => x.type).join() === "h1,table,quote,li,code" && b[1].rows.length === 2, "Markdown ブロック解析");
}

/* 7. Claude (任意) */
section("Claude (任意)");
{
  const s = comp("顧客を管理したい。テレパシーの機能も");
  const r = call("claudeRequest", { apiKey: "k", spec: s });
  ok(r.body.model === "claude-opus-5-5" && r.body.stream === true && r.body.output_config.effort === "high", "既定モデル・ストリーミング・effort");
  ok(r.body.thinking.type === "adaptive" && !("budget_tokens" in r.body.thinking), "adaptive thinking");
  ok(r.headers["anthropic-version"] === "2023-06-01" && r.headers["x-api-key"] === "k" && r.headers["anthropic-dangerous-direct-browser-access"] === "true", "ヘッダ");
  ok(r.headers["anthropic-beta"] === "server-side-fallback-2026-07-01" && r.body.fallbacks === "default", "拒否時の代替モデル");
  const rh = call("claudeRequest", { apiKey: "k", spec: s, model: "claude-haiku-5-5" });
  ok(!("fallbacks" in rh.body) && !rh.headers["anthropic-beta"], "Haiku は fallbacks なし");
  ok(/UNRESOLVED/.test(r.body.messages[0].content) && /テレパシー/.test(r.body.messages[0].content), "未解釈の節を Claude に渡す");
  const st = call("sseNew");
  const ev = (o) => "event: x\ndata: " + JSON.stringify(o) + "\n\n";
  const stream = ev({ type: "content_block_delta", delta: { type: "text_delta", text: "```html\n<!DOCTYPE html><html>" } }) +
    ev({ type: "content_block_delta", delta: { type: "text_delta", text: "<body>hi</body></html>\n```" } }) +
    ev({ type: "message_delta", delta: { stop_reason: "end_turn" }, usage: { output_tokens: 9 } });
  for (let i = 0; i < stream.length; i += 7) call("sseFeed", st, stream.slice(i, i + 7));
  ok(st.stop === "end_turn" && st.outTokens === 9, "SSE: 分割受信でも stop_reason / usage");
  ok(call("extractHtml", st.text) === "<!DOCTYPE html><html><body>hi</body></html>\n", "HTML 抽出 (フェンス付き)");
  ok(call("extractHtml", "説明だけ") === "", "HTML がなければ空");
  const st2 = call("sseNew"); call("sseFeed", st2, ev({ type: "message_delta", delta: { stop_reason: "refusal", stop_details: { category: "cyber" } } }));
  ok(st2.stop === "refusal" && st2.stopDetails.category === "cyber", "SSE: refusal と stop_details");
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
