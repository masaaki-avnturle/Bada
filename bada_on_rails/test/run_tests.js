#!/usr/bin/env node
/*
 * run_tests.js — Bada on Rails 結合テスト
 *
 *   node bada_on_rails/test/run_tests.js
 *
 * examples/quantum_blog を一時ディレクトリへコピーして (リポジトリ内の
 * DB を汚さないため)、HTTP を経由せず RailsApp#handleRequest を直接叩く。
 * 乱数は seed 固定で決定的。
 */
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");
const { RailsApp } = require("../lib/kernel.js");
const gen = require("../lib/generators.js");

let passed = 0, failed = 0;
function ok(cond, name, detail) {
  if (cond) { passed++; console.log("  ok  " + name); }
  else { failed++; console.error("FAIL  " + name + (detail ? " — " + detail : "")); }
}
function includes(hay, needle) { return String(hay).indexOf(needle) >= 0; }

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, e.name), d = path.join(dst, e.name);
    if (e.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "bada-rails-test-"));
process.on("exit", () => { try { fs.rmSync(tmp, { recursive: true, force: true }); } catch (e) {} });

/* ================= quantum_blog ================= */
console.log("== quantum_blog ==");
const blogRoot = path.join(tmp, "quantum_blog");
copyDir(path.join(__dirname, "..", "examples", "quantum_blog"), blogRoot);

const app = new RailsApp(blogRoot, { seed: 42, quiet: true });
app.boot();

const get = (url) => app.handleRequest({ method: "GET", url, headers: {}, body: "" });
const post = (url, form) => app.handleRequest({
  method: "POST", url, headers: { "content-type": "application/x-www-form-urlencoded" },
  body: Object.keys(form).map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(form[k])).join("&")
});

/* --- routes --- */
const table = app.routesTable();
ok(table.length >= 11, "routes registered (" + table.length + ")");
ok(table.some((r) => r.method === "GET" && r.pattern === "/" && r.target === "posts#index"), "root route");
ok(table.some((r) => r.method === "DELETE" && r.pattern === "/posts/:id"), "resources :posts expands RESTful routes");
ok(table.some((r) => r.pattern === "/lucky" && /^branch:\d+$/.test(r.target)), "branch object as route target");

/* --- seeds + index --- */
let r = get("/");
ok(r.status === 200, "GET / is 200");
ok(includes(r.body, "Bada on Rails へようこそ"), "seeded post on index");
ok(includes(r.body, "Akashic 台帳"), "index shows ledger tail");
ok(includes(r.body, "quantum_blog"), "layout applied");

/* --- show --- */
r = get("/posts/1");
ok(r.status === 200 && includes(r.body, "追記専用の Akashic 台帳"), "GET /posts/1 shows body");

/* --- superposed field collapses on first read, then stays --- */
r = get("/posts/3");
const m3 = String(r.body).match(/status: (draft|published)/);
ok(!!m3, "superposed status collapsed to draft|published", r.body.slice(0, 200));
const r2 = get("/posts/3");
ok(includes(r2.body, "status: " + (m3 ? m3[1] : "?")), "collapsed status is stable across reads");
ok(app.db.facts.some((f) => f.kind === "collapse" && f.model === "post" && f.id === "3"), "collapse fact committed to ledger");

/* --- create (strong parameters + XSS escape) --- */
r = post("/posts", { title: "<script>alert(1)</script>", body: "b", status: "draft", evil: "1" });
ok(r.status === 302, "POST /posts redirects");
const loc = r.headers.Location;
ok(/^\/posts\/\d+$/.test(loc), "redirect Location " + loc);
r = get(loc);
ok(includes(r.body, "&lt;script&gt;alert(1)&lt;/script&gt;") && !includes(r.body, "<script>alert(1)"), "HTML escaped by default");
const created = app.db.facts.filter((f) => f.kind === "create").pop();
ok(!("evil" in created.fields), "strong parameters filter undeclared fields");

/* --- update via _method override --- */
const id = loc.split("/").pop();
r = post("/posts/" + id, { _method: "PATCH", title: "Updated title", body: "b2", status: "published" });
ok(r.status === 302, "PATCH via _method redirects");
r = get("/posts/" + id);
ok(includes(r.body, "Updated title") && includes(r.body, "status: published"), "record updated");

/* --- destroy (tombstone fact, ledger keeps growing) --- */
const before = app.db.facts.length;
r = post("/posts/" + id, { _method: "DELETE" });
ok(r.status === 302, "DELETE redirects");
ok(get("/posts/" + id).status === 404, "destroyed record is 404");
ok(app.db.facts.length === before + 1 && app.db.facts[app.db.facts.length - 1].kind === "destroy", "destroy is an append-only tombstone");

/* --- superposed create through the form --- */
r = post("/posts", { title: "Q", body: "qb", status: "superposed" });
const qid = r.headers.Location.split("/").pop();
r = get("/posts/" + qid);
ok(/status: (draft|published)/.test(r.body), "form status=superposed collapses on read");

/* --- quantum demo page --- */
r = get("/quantum");
ok(r.status === 200 && includes(r.body, "分岐オブジェクト"), "GET /quantum renders");
ok(includes(r.body, "0.5") && includes(r.body, "0.3"), "branch_state probabilities shown (phase preserved |amp|^2)");
ok(app.db.facts.some((f) => f.kind === "measurement" && f.what === "collapse"), "collapse measurement in ledger");

/* --- branch route: /lucky dispatches to a measured action --- */
r = get("/lucky");
ok(r.status === 200, "GET /lucky is 200 (measured dispatch)");
ok(app.db.facts.some((f) => f.kind === "measurement" && f.what === "route"), "route measurement in ledger");
{
  /* アンサンブル: 十分な回数で両分岐が現れる */
  const seen = new Set();
  for (let i = 0; i < 40; i++) {
    const rr = get("/lucky");
    seen.add(includes(rr.body, "もう一度測定する") ? "quantum" : "index");
  }
  ok(seen.size === 2, "both branches of /lucky occur across requests");
}

/* --- 404 / static --- */
ok(get("/nope").status === 404, "unknown path is 404");
r = get("/application.css");
ok(r.status === 200 && /text\/css/.test(r.ctype), "static css served");

/* --- persistence: reboot from ledger file --- */
{
  const app2 = new RailsApp(blogRoot, { seed: 7, quiet: true });
  app2.boot();
  const rr = app2.handleRequest({ method: "GET", url: "/posts/3", headers: {}, body: "" });
  ok(includes(rr.body, "status: " + (m3 ? m3[1] : "?")), "collapsed value survives reboot (ledger replay)");
  ok(app2.db.facts.length > 5, "ledger replayed from db/akashic.jsonl");
}

/* --- Bada 作用素を直接 (console 相当) --- */
{
  const rr = app.session.eval('collapse(superpose ["only"] with [1.0])');
  ok(rr.errors.length === 0 && rr.value === "only", "superpose/collapse operator in session");
  const st = app.session.eval('branch_state(superpose ["a", "b"] with [3, 1])');
  ok(st.value === "[[a, 0.75000], [b, 0.25000]]", "weights normalize to Born probabilities", st.value);
}

/* ================= generator ================= */
console.log("== generators (new + scaffold) ==");
const genRoot = path.join(tmp, "genapp");
gen.newApp(genRoot, null);
gen.scaffold(genRoot, "item", ["name:string", "note:text"], null);

const app3 = new RailsApp(genRoot, { seed: 1, quiet: true });
app3.boot();
const g3 = (url) => app3.handleRequest({ method: "GET", url, headers: {}, body: "" });
const p3 = (url, form) => app3.handleRequest({
  method: "POST", url, headers: { "content-type": "application/x-www-form-urlencoded" },
  body: Object.keys(form).map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(form[k])).join("&")
});

r = g3("/");
ok(r.status === 200 && includes(r.body, "Bada on Rails"), "new app welcome page renders (branch heading)");
r = g3("/items");
ok(r.status === 200, "scaffold index renders");
r = g3("/items/new");
ok(r.status === 200 && includes(r.body, "<form"), "scaffold new form renders");
r = p3("/items", { name: "第一項目", note: "メモ" });
ok(r.status === 302, "scaffold create redirects");
r = g3(r.headers.Location);
ok(includes(r.body, "第一項目"), "scaffold show renders created record");
r = p3("/items/1", { _method: "PATCH", name: "改名", note: "n2" });
r = g3("/items/1");
ok(includes(r.body, "改名"), "scaffold update works");
r = p3("/items/1", { _method: "DELETE" });
ok(g3("/items/1").status === 404, "scaffold destroy works");

/* ================= summary ================= */
console.log("\n" + passed + " passed, " + failed + " failed");
process.exit(failed ? 1 : 0);
