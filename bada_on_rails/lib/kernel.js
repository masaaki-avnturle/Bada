/* ============================================================================
 * kernel.js — Bada on Rails フレームワークカーネル (Node.js)
 *
 * 量子プログラミング言語 Bada (bada_gui_ide/www/bada.js) の上に実装した
 * Rails 風フルスタック Web フレームワーク。アプリケーションコード
 * (config/routes.bada / app/models / app/controllers / app/views) はすべて
 * Bada 言語で書かれ、このカーネルは次の 3 層だけを提供します:
 *
 *   1. rails FFI 言語 — railtie.bada の `@reviser : extension rails { ... }`
 *      が宣言するホスト関数群 (ルーティング登録・DB・レンダリング・分岐
 *      オブジェクト)。bada.js の FFI 規約 (JSON over argv/stdout) に従う。
 *   2. Akashic DB — 追記専用 JSONL 台帳 (db/akashic.jsonl)。作成・更新・
 *      削除・測定 (分岐収縮) がすべて事実としてコミットされ、現在状態は
 *      台帳の畳み込み (replay) で得られる。tuplespace の永続版。
 *   3. 分岐オブジェクト (BranchSpace) — 値の重ね合わせ。振幅 (複素数) を
 *      保持し、collapse は Born 則 |amp|^2 で分岐を選び、測定事実を
 *      Akashic 台帳へ追記する。位相回転は確率を変えない (|psi|^2 保存)。
 *
 * ルーティング DSL・モデル宣言は Bada の @reviser : grammar 文法拡張で
 * 実装される (lib/railtie.bada)。ビューは ERB 風 .bada.erb テンプレートを
 * Bada コードへコンパイルして同一セッションで評価する。
 * ==========================================================================*/
"use strict";

const fs = require("fs");
const path = require("path");
const http = require("http");

const Bada = require("../../bada_gui_ide/www/bada.js");

/* 他言語拡張 (@reviser : extension python/c/java) 用の既存ブリッジ。
   無くても rails 拡張だけで動作する。 */
let foreignFfi = null;
try { foreignFfi = require("../../bada_gui_ide/cli/bada-ffi.js").ffi; } catch (e) { foreignFfi = null; }

/* ---------------------------------------------------------------- utils */

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function badaStr(s) {
  return '"' + String(s)
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\r/g, "\\r")
    .replace(/\n/g, "\\n")
    .replace(/\t/g, "\\t") + '"';
}

/* JS 値 → Bada ソースリテラル (テンプレート/ローカル束縛のプレリュード用) */
function badaLiteral(v) {
  if (v === null || v === undefined) return "nil";
  if (typeof v === "number") return Number.isFinite(v) ? String(v) : "0";
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "string") return badaStr(v);
  if (Array.isArray(v)) return "[" + v.map(badaLiteral).join(", ") + "]";
  return badaStr(JSON.stringify(v));
}

function htmlEscape(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function fmtScalar(v) {
  if (v === null || v === undefined) return "";
  if (typeof v === "number") {
    if (Number.isInteger(v)) return String(v);
    return String(Math.round(v * 1e6) / 1e6);
  }
  if (Array.isArray(v)) return "[" + v.map(fmtScalar).join(", ") + "]";
  return String(v);
}

function pairsToObj(pairs) {
  const o = {};
  if (Array.isArray(pairs)) {
    for (const pr of pairs) {
      if (Array.isArray(pr) && pr.length >= 2 && typeof pr[0] === "string") o[pr[0]] = pr[1];
    }
  }
  return o;
}

const MIME = {
  ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".html": "text/html; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg",
  ".svg": "image/svg+xml", ".ico": "image/x-icon", ".txt": "text/plain; charset=utf-8",
  ".json": "application/json; charset=utf-8"
};

/* ------------------------------------------------------- 分岐オブジェクト */
/* 値の重ね合わせ。amps は複素振幅 {re, im}。collapse は Born 則で分岐を
   1 つ選び恒久確定 (射影測定)。sample は「同じ状態を毎回準備し直す
   アンサンブル抽出」で、量子ルーティングのように毎リクエスト測定し直す
   用途に使う。位相回転 branch_phase は |amp|^2 を変えない。 */
class BranchSpace {
  constructor(rng) {
    this.rng = rng;
    this.seq = 0;
    this.reg = new Map();
  }
  make(values, weights) {
    if (!Array.isArray(values) || values.length === 0) return null;
    let w;
    if (Array.isArray(weights) && weights.length === values.length) {
      w = weights.map((x) => Math.abs(Number(x) || 0));
    } else {
      w = values.map(() => 1);
    }
    let s = w.reduce((a, b) => a + b, 0);
    if (s <= 0) { w = values.map(() => 1); s = values.length; }
    const amps = w.map((x) => ({ re: Math.sqrt(x / s), im: 0 }));
    const h = "branch:" + (++this.seq);
    this.reg.set(h, { values: values.slice(), amps, measured: null });
    return h;
  }
  get(h) { return this.reg.get(h) || null; }
  probs(h) {
    const b = this.get(h);
    if (!b) return null;
    const p = b.amps.map((a) => a.re * a.re + a.im * a.im);
    const s = p.reduce((a, c) => a + c, 0) || 1;
    return p.map((x) => x / s);
  }
  phase(h, i, theta) {
    const b = this.get(h);
    if (!b || i < 0 || i >= b.amps.length) return null;
    const a = b.amps[i], c = Math.cos(theta), s = Math.sin(theta);
    b.amps[i] = { re: a.re * c - a.im * s, im: a.re * s + a.im * c };
    return h;
  }
  pick(h) {
    const b = this.get(h), p = this.probs(h);
    if (!b) return null;
    let r = this.rng(), i = 0;
    for (; i < p.length - 1; i++) { r -= p[i]; if (r < 0) break; }
    return { index: i, value: b.values[i], probs: p };
  }
  collapse(h) {
    const b = this.get(h);
    if (!b) return null;
    if (b.measured !== null) {
      return { index: b.measured, value: b.values[b.measured], probs: this.probs(h), repeated: true };
    }
    const m = this.pick(h);
    if (m) b.measured = m.index;
    return m;
  }
  state(h) {
    const b = this.get(h), p = this.probs(h);
    if (!b) return null;
    return b.values.map((v, i) => [v, Math.round(p[i] * 10000) / 10000]);
  }
}

/* ------------------------------------------------------------- Akashic DB */
/* 追記専用 JSONL 台帳。事実 (fact) の種類:
     create   {model, id, at, fields}
     update   {model, id, at, fields}
     destroy  {model, id, at}
     collapse {model, id, at, field, value, probs}   — 重ね合わせ属性の測定
     measurement {at, branch, value, probs, what}    — 分岐オブジェクトの測定
   現在状態は台帳のリプレイで得る。削除も墓標事実であり、台帳は消えない。 */
class AkashicDB {
  constructor(file) {
    this.file = file || null;
    this.facts = [];
    this.state = new Map();   /* model -> Map(id -> {id, at, fields}) */
    this.counters = new Map();
    if (this.file && fs.existsSync(this.file)) {
      const lines = fs.readFileSync(this.file, "utf8").split("\n");
      for (const line of lines) {
        const t = line.trim();
        if (!t) continue;
        try { this.apply(JSON.parse(t), false); } catch (e) { /* 壊れた行は無視 */ }
      }
    }
  }
  table(model) {
    if (!this.state.has(model)) this.state.set(model, new Map());
    return this.state.get(model);
  }
  apply(fact, persist) {
    this.facts.push(fact);
    if (fact.kind === "create") {
      this.table(fact.model).set(String(fact.id), { id: String(fact.id), at: fact.at, fields: Object.assign({}, fact.fields) });
      const c = this.counters.get(fact.model) || 0;
      const n = parseInt(fact.id, 10);
      if (Number.isFinite(n) && n > c) this.counters.set(fact.model, n);
    } else if (fact.kind === "update") {
      const r = this.table(fact.model).get(String(fact.id));
      if (r) Object.assign(r.fields, fact.fields);
    } else if (fact.kind === "destroy") {
      this.table(fact.model).delete(String(fact.id));
    } else if (fact.kind === "collapse") {
      const r = this.table(fact.model).get(String(fact.id));
      if (r) r.fields[fact.field] = fact.value;
    }
    if (persist && this.file) {
      fs.mkdirSync(path.dirname(this.file), { recursive: true });
      fs.appendFileSync(this.file, JSON.stringify(fact) + "\n");
    }
  }
  commit(fact) {
    fact.at = fact.at || new Date().toISOString();
    this.apply(fact, true);
    return fact;
  }
  nextId(model) {
    const n = (this.counters.get(model) || 0) + 1;
    this.counters.set(model, n);
    return String(n);
  }
}

/* -------------------------------------------------------- ERB コンパイラ */
/* .bada.erb → Bada ソース。
     <%= expr %>            HTML エスケープして出力
     <%= raw expr %>        エスケープなしで出力
     <% each expr as v %>   反復 (while へコンパイル — Bada の環境規則上、
                            for-in は外側変数への蓄積ができないため)
     <% if expr %> / <% else %> / <% end %>
     <% partial "a/_b" %>   コンパイル時インライン展開
     <% 任意のBada文 %>      そのまま埋め込み                                */
function compileErb(src, resolvePartial, depth) {
  depth = depth || 0;
  if (depth > 8) throw new Error("partial nesting too deep (cycle?)");
  const out = [];
  let loopN = 0;
  const stack = [];
  const parts = String(src).split(/(<%=?[\s\S]*?%>)/g);
  for (const part of parts) {
    if (!part) continue;
    if (part.startsWith("<%=")) {
      const code = part.slice(3, -2).trim();
      const raw = /^raw\s+/.test(code);
      const expr = raw ? code.replace(/^raw\s+/, "") : code;
      out.push("__o = __o + " + (raw ? "(" + expr + ")" : "h(" + expr + ")"));
    } else if (part.startsWith("<%")) {
      const code = part.slice(2, -2).trim();
      let m;
      if ((m = code.match(/^each\s+([\s\S]+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)$/))) {
        const n = loopN++;
        out.push("__it" + n + " := (" + m[1] + ")");
        out.push("__i" + n + " := 0");
        out.push("while (__i" + n + " < len(__it" + n + ")) {");
        out.push(m[2] + " := __it" + n + "[__i" + n + "]");
        out.push("__i" + n + " = __i" + n + " + 1");
        stack.push("each");
      } else if ((m = code.match(/^if\s+([\s\S]+)$/))) {
        out.push("if (" + m[1] + ") {");
        stack.push("if");
      } else if (code === "else") {
        out.push("} else {");
      } else if (code === "end") {
        if (!stack.length) throw new Error("unbalanced <% end %> in template");
        stack.pop();
        out.push("}");
      } else if ((m = code.match(/^partial\s+"([^"]+)"$/))) {
        const sub = resolvePartial(m[1]);
        out.push(compileErb(sub, resolvePartial, depth + 1));
      } else if (code) {
        out.push(code);
      }
    } else {
      out.push('__o = __o + ' + badaStr(part));
    }
  }
  if (stack.length) throw new Error("unbalanced block in template (missing <% end %>)");
  return out.join("\n");
}

/* ------------------------------------------------------------- RailsApp */

class RailsApp {
  constructor(root, opts) {
    opts = opts || {};
    this.root = path.resolve(root);
    this.opts = opts;
    this.log = opts.log || ((s) => process.stderr.write(s + "\n"));
    this.quiet = !!opts.quiet;
    const seed = opts.seed === undefined ? ((Date.now() ^ (Math.random() * 0xffffffff)) >>> 0) : (opts.seed >>> 0);
    this.rng = mulberry32(seed);
    this.db = new AkashicDB(opts.dbPath === undefined ? path.join(this.root, "db", "akashic.jsonl") : opts.dbPath);
    this.branches = new BranchSpace(this.rng);
    this.routes = [];
    this.models = new Map();     /* name -> {fields:[...]} */
    this.pendingSource = [];     /* rails_model が積む生成 Bada コード */
    this.current = null;         /* リクエストごとの {params, method, path, response, intent} */
    this._probe = undefined;
    this._emitted = null;
    this.viewCache = new Map();
    this.session = Bada.createSession({
      out: (s) => { if (!this.quiet) this.log("[bada] " + s); },
      ffi: (lang, name, code, params, argv) => this.ffiDispatch(lang, name, code, params, argv)
    });
  }

  info(s) { if (!this.quiet) this.log(s); }

  /* ---------------- boot ---------------- */
  boot() {
    this.evalFile(path.join(__dirname, "railtie.bada"));
    const modelsDir = path.join(this.root, "app", "models");
    if (fs.existsSync(modelsDir)) {
      for (const f of fs.readdirSync(modelsDir).sort()) {
        if (f.endsWith(".bada")) this.evalFile(path.join(modelsDir, f));
      }
    }
    this.evalFile(path.join(this.root, "config", "routes.bada"));
    const ctrlDir = path.join(this.root, "app", "controllers");
    if (fs.existsSync(ctrlDir)) {
      for (const f of fs.readdirSync(ctrlDir).sort()) {
        if (f.endsWith(".bada")) this.evalFile(path.join(ctrlDir, f));
      }
    }
    const seeds = path.join(this.root, "db", "seeds.bada");
    if (fs.existsSync(seeds)) this.evalFile(seeds);
    return this;
  }

  evalFile(file) {
    if (!fs.existsSync(file)) throw new Error("missing file: " + file);
    this.evalSource(fs.readFileSync(file, "utf8"), path.relative(this.root, file));
  }

  evalSource(src, label) {
    const r = this.session.eval(src);
    if (r.errors && r.errors.length) {
      throw new Error("Bada errors in " + (label || "<eval>") + ":\n  " + r.errors.join("\n  "));
    }
    /* rails_model 等が生成コードを積んでいたら続けて評価する */
    while (this.pendingSource.length) {
      const gen = this.pendingSource.shift();
      const g = this.session.eval(gen);
      if (g.errors && g.errors.length) {
        throw new Error("Bada errors in generated code for " + (label || "<eval>") + ":\n  " + g.errors.join("\n  "));
      }
    }
    return r;
  }

  /* ---------------- FFI dispatch (lang = "rails") ---------------- */
  ffiDispatch(lang, name, code, params, argv) {
    if (lang !== "rails") {
      if (foreignFfi) return foreignFfi(lang, name, code, params, argv);
      return { ok: false, stdout: "", error: "no host bridge for lang " + lang };
    }
    let args;
    try { args = argv.map((a) => JSON.parse(a)); }
    catch (e) { return { ok: false, stdout: "", error: "bad argv" }; }
    try {
      const r = this.hostcall(name, args);
      return { ok: true, stdout: JSON.stringify(r === undefined ? null : r), error: null };
    } catch (e) {
      return { ok: false, stdout: "", error: String(e && e.message ? e.message : e) };
    }
  }

  hostcall(name, a) {
    switch (name) {
      /* -------- ルーティング / モデル宣言 -------- */
      case "rails_route": return this.addRoute(String(a[0]), String(a[1]), a[2]);
      case "rails_resources": return this.addResources(String(a[0]));
      case "rails_model": return this.addModel(String(a[0]), a[1]);

      /* -------- リクエスト -------- */
      case "param": {
        const req = this.current;
        if (!req) return null;
        const v = req.params[String(a[0])];
        return v === undefined ? null : v;
      }
      case "params_all": {
        const req = this.current;
        if (!req) return [];
        return Object.keys(req.params).map((k) => [k, req.params[k]]);
      }
      case "request_method": return this.current ? this.current.method : null;
      case "request_path": return this.current ? this.current.path : null;

      /* -------- レスポンス -------- */
      case "render_view": {
        const locals = [];
        const flat = Array.isArray(a[1]) ? a[1] : [];
        for (let i = 0; i + 1 < flat.length; i += 2) locals.push([String(flat[i]), flat[i + 1]]);
        this.setIntent({ view: String(a[0]), locals });
        return null;
      }
      case "render_html": this.setResponse({ status: 200, ctype: "text/html; charset=utf-8", body: String(a[0]) }); return null;
      case "render_json": this.setResponse({ status: 200, ctype: "application/json; charset=utf-8", body: JSON.stringify(a[0]) }); return null;
      case "redirect_to": this.setResponse({ status: 302, ctype: "text/plain; charset=utf-8", body: "redirected", headers: { Location: String(a[0]) } }); return null;
      case "head": this.setResponse({ status: Math.trunc(Number(a[0]) || 204), ctype: "text/plain; charset=utf-8", body: "" }); return null;

      /* -------- Akashic DB -------- */
      case "db_all": return this.dbAll(String(a[0]));
      case "db_find": return this.dbFind(String(a[0]), a[1]);
      case "db_create": return this.dbCreate(String(a[0]), a[1]);
      case "db_update": return this.dbUpdate(String(a[0]), a[1], a[2]);
      case "db_destroy": return this.dbDestroy(String(a[0]), a[1]);
      case "db_count": return this.db.table(String(a[0])).size;
      case "akashic_len": return this.db.facts.length;
      case "akashic_tail": {
        const n = Math.max(0, Math.trunc(Number(a[0]) || 0));
        return this.db.facts.slice(-n).map((f) => JSON.stringify(f));
      }

      /* -------- 分岐オブジェクト -------- */
      case "branch_make": return this.branches.make(a[0], a[1]);
      case "branch_uniform": return this.branches.make(a[0], null);
      case "branch_phase": return this.branches.phase(String(a[0]), Math.trunc(Number(a[1]) || 0), Number(a[2]) || 0);
      case "branch_probs": return this.branches.probs(String(a[0]));
      case "branch_values": { const b = this.branches.get(String(a[0])); return b ? b.values : null; }
      case "branch_state": return this.branches.state(String(a[0]));
      case "branch_collapse": {
        const m = this.branches.collapse(String(a[0]));
        if (!m) return null;
        if (!m.repeated) {
          this.db.commit({ kind: "measurement", what: "collapse", branch: String(a[0]), value: m.value, probs: m.probs.map((p) => Math.round(p * 10000) / 10000) });
        }
        return m.value;
      }

      /* -------- ユーティリティ -------- */
      case "h": return Array.isArray(a[0]) ? htmlEscape(fmtScalar(a[0])) : htmlEscape(fmtScalar(a[0]));
      case "fmt": return fmtScalar(a[0]);
      case "pairs_get": {
        const pairs = a[0], k = String(a[1]);
        if (!Array.isArray(pairs)) return null;
        for (const pr of pairs) if (Array.isArray(pr) && String(pr[0]) === k) return pr.length > 1 ? pr[1] : null;
        return null;
      }
      case "log": this.info("[app] " + a.map(fmtScalar).join(" ")); return null;
      case "__probe": this._probe = a[0]; return null;
      case "__rails_emit": this._emitted = String(a[0] === null || a[0] === undefined ? "" : a[0]); return null;

      default:
        throw new Error("unknown rails hostcall: " + name);
    }
  }

  setIntent(intent) {
    if (!this.current) return;
    if (this.current.intent || this.current.response) {
      this.info("[bada-rails] warn: double render ignored (" + intent.view + ")");
      return;
    }
    this.current.intent = intent;
  }
  setResponse(res) {
    if (!this.current) return;
    if (this.current.intent || this.current.response) {
      this.info("[bada-rails] warn: double render ignored");
      return;
    }
    this.current.response = res;
  }

  /* ---------------- routes ---------------- */
  addRoute(method, pattern, target) {
    const segs = pattern === "/" ? [] : pattern.replace(/^\/+|\/+$/g, "").split("/");
    this.routes.push({ method: method.toUpperCase(), pattern, segs, target });
    return this.routes.length - 1;
  }
  addResources(name) {
    const n = String(name).replace(/[^A-Za-z0-9_]/g, "");
    const t = (act) => n + "#" + act;
    this.addRoute("GET", "/" + n, t("index"));
    this.addRoute("GET", "/" + n + "/new", t("new"));
    this.addRoute("POST", "/" + n, t("create"));
    this.addRoute("GET", "/" + n + "/:id", t("show"));
    this.addRoute("GET", "/" + n + "/:id/edit", t("edit"));
    this.addRoute("PATCH", "/" + n + "/:id", t("update"));
    this.addRoute("PUT", "/" + n + "/:id", t("update"));
    this.addRoute("DELETE", "/" + n + "/:id", t("destroy"));
    return n;
  }
  addModel(name, fields) {
    const n = String(name).replace(/[^A-Za-z0-9_]/g, "");
    const fl = Array.isArray(fields) ? fields.map((f) => String(f).replace(/[^A-Za-z0-9_]/g, "")) : [];
    this.models.set(n, { fields: fl });
    /* Bada 側にモデルヘルパ関数を生成 (post_all / post_find / ...) */
    this.pendingSource.push([
      "def " + n + "_all || => db_all(" + badaStr(n) + ")",
      "def " + n + "_find |id| => db_find(" + badaStr(n) + ", id)",
      "def " + n + "_create |fields| => db_create(" + badaStr(n) + ", fields)",
      "def " + n + "_update |id, fields| => db_update(" + badaStr(n) + ", id, fields)",
      "def " + n + "_destroy |id| => db_destroy(" + badaStr(n) + ", id)",
      "def " + n + "_count || => db_count(" + badaStr(n) + ")"
    ].join("\n"));
    return n;
  }
  matchRoute(method, pathname) {
    const segs = pathname === "/" ? [] : pathname.replace(/^\/+|\/+$/g, "").split("/").map(decodeURIComponent);
    for (const r of this.routes) {
      if (r.method !== method) continue;
      if (r.segs.length !== segs.length) continue;
      const params = {};
      let ok = true;
      for (let i = 0; i < segs.length; i++) {
        const p = r.segs[i];
        if (p.startsWith(":")) params[p.slice(1)] = segs[i];
        else if (p !== segs[i]) { ok = false; break; }
      }
      if (ok) return { route: r, params };
    }
    return null;
  }
  routesTable() {
    return this.routes.map((r) => ({ method: r.method, pattern: r.pattern, target: r.target }));
  }

  /* ---------------- Akashic DB 操作 (強いパラメータ + 重ね合わせ属性) --- */
  permit(model, pairs) {
    const obj = pairsToObj(pairs);
    const decl = this.models.get(model);
    const out = {};
    for (const k of Object.keys(obj)) {
      if (decl && decl.fields.length && decl.fields.indexOf(k) < 0) continue; /* strong parameters */
      let v = obj[k];
      /* 分岐オブジェクトのハンドルは重ね合わせのまま保存する */
      if (typeof v === "string" && /^branch:\d+$/.test(v) && this.branches.get(v)) {
        const b = this.branches.get(v);
        v = { __superposed: { values: b.values, probs: this.branches.probs(v) } };
      }
      out[k] = v;
    }
    return out;
  }
  recToPairs(model, rec) {
    /* 重ね合わせ属性は最初の読み出しで測定・確定する (遅延収縮)。
       測定は collapse 事実として台帳へ追記され、以後は同じ値を返す。 */
    const decl = this.models.get(model);
    const keys = decl && decl.fields.length ? decl.fields : Object.keys(rec.fields);
    const pairs = [["id", rec.id], ["created_at", rec.at || ""]];
    for (const k of keys) {
      let v = rec.fields[k];
      if (v && typeof v === "object" && v.__superposed) {
        const sp = v.__superposed;
        let r = this.rng(), i = 0;
        for (; i < sp.values.length - 1; i++) { r -= sp.probs[i]; if (r < 0) break; }
        v = sp.values[i];
        this.db.commit({ kind: "collapse", model, id: rec.id, field: k, value: v, probs: sp.probs.map((p) => Math.round(p * 10000) / 10000) });
      }
      pairs.push([k, v === undefined || v === null ? "" : v]);
    }
    return pairs;
  }
  dbCreate(model, pairs) {
    const id = this.db.nextId(model);
    this.db.commit({ kind: "create", model, id, fields: this.permit(model, pairs) });
    return id;
  }
  dbFind(model, id) {
    const rec = this.db.table(model).get(String(id));
    return rec ? this.recToPairs(model, rec) : null;
  }
  dbAll(model) {
    const out = [];
    for (const rec of this.db.table(model).values()) out.push(this.recToPairs(model, rec));
    return out;
  }
  dbUpdate(model, id, pairs) {
    const rec = this.db.table(model).get(String(id));
    if (!rec) return null;
    this.db.commit({ kind: "update", model, id: String(id), fields: this.permit(model, pairs) });
    return String(id);
  }
  dbDestroy(model, id) {
    const rec = this.db.table(model).get(String(id));
    if (!rec) return false;
    this.db.commit({ kind: "destroy", model, id: String(id) });
    return true;
  }

  /* ---------------- views ---------------- */
  viewPath(name) { return path.join(this.root, "app", "views", name + ".bada.erb"); }
  compiledView(name) {
    const file = this.viewPath(name);
    if (!fs.existsSync(file)) throw new Error("missing view template: " + path.relative(this.root, file));
    const mtime = fs.statSync(file).mtimeMs;
    const cached = this.viewCache.get(file);
    if (cached && cached.mtime === mtime) return cached.code;
    const src = fs.readFileSync(file, "utf8");
    const code = compileErb(src, (p) => {
      const pf = this.viewPath(p);
      if (!fs.existsSync(pf)) throw new Error("missing partial: " + p);
      return fs.readFileSync(pf, "utf8");
    }, 0);
    this.viewCache.set(file, { mtime, code });
    return code;
  }
  renderTemplate(name, locals) {
    const prelude = (locals || []).map(([k, v]) => k.replace(/[^A-Za-z0-9_]/g, "") + " := " + badaLiteral(v)).join("\n");
    const src = prelude + "\n__o := \"\"\n" + this.compiledView(name) + "\n__rails_emit(__o)";
    this._emitted = null;
    const r = this.session.eval(src);
    if (r.errors && r.errors.length) throw new Error("view " + name + ":\n  " + r.errors.join("\n  "));
    return this._emitted === null ? "" : this._emitted;
  }
  renderWithLayout(name, locals) {
    let html = this.renderTemplate(name, locals);
    if (fs.existsSync(this.viewPath("layouts/application"))) {
      html = this.renderTemplate("layouts/application", [["__content", html]]);
    }
    return html;
  }

  /* ---------------- dispatch ---------------- */
  handleRequest(req) {
    const started = Date.now();
    const q = req.url.indexOf("?");
    const pathname = q < 0 ? req.url : req.url.slice(0, q);
    const query = q < 0 ? "" : req.url.slice(q + 1);
    const params = {};
    parseUrlEncoded(query, params);
    if (req.body && /application\/json/.test(req.headers && req.headers["content-type"] || "")) {
      try {
        const o = JSON.parse(req.body);
        if (o && typeof o === "object") for (const k of Object.keys(o)) params[k] = o[k];
      } catch (e) { /* ignore */ }
    } else if (req.body) {
      parseUrlEncoded(req.body, params);
    }
    let method = String(req.method || "GET").toUpperCase();
    if (method === "POST" && typeof params._method === "string") {
      const o = params._method.toUpperCase();
      if (o === "PATCH" || o === "PUT" || o === "DELETE") method = o;
    }

    let res;
    try {
      res = this.dispatch(method, pathname, params);
    } catch (e) {
      res = this.errorPage(500, "Internal Bada Error", String(e && e.message ? e.message : e));
    }
    const ms = Date.now() - started;
    this.info("[bada-rails] " + method + " " + pathname + " -> " + res.status + " (" + ms + "ms)");
    return res;
  }

  dispatch(method, pathname, params) {
    const m = this.matchRoute(method, pathname);
    if (!m) {
      const st = this.serveStatic(pathname);
      if (st) return st;
      return this.errorPage(404, "No route matches", method + " " + pathname);
    }
    let target = m.route.target;
    /* 分岐オブジェクトをルート先に指定できる: リクエストごとに同じ重ね
       合わせを準備し直して測定する (アンサンブル)。測定は台帳へ記録。 */
    if (typeof target === "string" && /^branch:\d+$/.test(target) && this.branches.get(target)) {
      const pick = this.branches.pick(target);
      this.db.commit({ kind: "measurement", what: "route", branch: target, value: pick.value, probs: pick.probs.map((p) => Math.round(p * 10000) / 10000) });
      target = String(pick.value);
    }
    const mm = String(target).match(/^([A-Za-z0-9_]+)#([A-Za-z0-9_]+)$/);
    if (!mm) return this.errorPage(500, "Bad route target", String(target));
    const fn = mm[1] + "_" + mm[2];

    this._probe = undefined;
    let pr = this.session.eval("__probe(" + fn + ")");
    if (pr.errors && pr.errors.length) return this.errorPage(500, "Dispatch error", pr.errors.join("\n"));
    if (this._probe === fn) {
      return this.errorPage(500, "Undefined action", "controller action `def " + fn + "` is not defined (target " + target + ")");
    }

    /* パスパラメータ (:id など) はクエリ/フォームより優先 */
    this.current = { method, path: pathname, params: Object.assign({}, params, m.params), response: null, intent: null };
    try {
      const r = this.session.eval(fn + "()");
      if (r.errors && r.errors.length) return this.errorPage(500, "Action error in " + fn, r.errors.join("\n"));
      if (this.current.intent) {
        const html = this.renderWithLayout(this.current.intent.view, this.current.intent.locals);
        return { status: 200, ctype: "text/html; charset=utf-8", body: html, headers: {} };
      }
      if (this.current.response) {
        const res = this.current.response;
        res.headers = res.headers || {};
        return res;
      }
      return { status: 204, ctype: "text/plain; charset=utf-8", body: "", headers: {} };
    } finally {
      this.current = null;
    }
  }

  serveStatic(pathname) {
    const pub = path.join(this.root, "public");
    if (!fs.existsSync(pub)) return null;
    const target = path.normalize(path.join(pub, pathname));
    if (!target.startsWith(pub + path.sep)) return null;
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
    const ext = path.extname(target).toLowerCase();
    return {
      status: 200,
      ctype: MIME[ext] || "application/octet-stream",
      body: fs.readFileSync(target),
      headers: {}
    };
  }

  errorPage(status, title, detail) {
    const body = "<!doctype html><meta charset='utf-8'><title>" + htmlEscape(title) +
      "</title><body style='font-family:monospace;background:#0a0c12;color:#e8e2d0;padding:2em'>" +
      "<h1 style='color:#c8a44a'>" + status + " — " + htmlEscape(title) + "</h1>" +
      "<pre style='white-space:pre-wrap;color:#9fb4d8'>" + htmlEscape(detail || "") + "</pre>" +
      "<p><a style='color:#4a80d0' href='/'>← root</a> · Bada on Rails</p></body>";
    return { status, ctype: "text/html; charset=utf-8", body, headers: {} };
  }

  /* ---------------- HTTP server ---------------- */
  server(port) {
    const srv = http.createServer((req, res) => {
      const chunks = [];
      let size = 0;
      req.on("data", (c) => { size += c.length; if (size < 1048576) chunks.push(c); });
      req.on("end", () => {
        const out = this.handleRequest({
          method: req.method,
          url: req.url,
          headers: req.headers,
          body: Buffer.concat(chunks).toString("utf8")
        });
        const headers = Object.assign({ "Content-Type": out.ctype }, out.headers || {});
        res.writeHead(out.status, headers);
        res.end(out.body);
      });
    });
    srv.listen(port, () => {
      this.log("[bada-rails] Bada on Rails " + VERSION + " — listening on http://localhost:" + port);
      this.log("[bada-rails] app root: " + this.root + " · Akashic ledger: " + (this.db.file || "(memory)") + " · " + this.routes.length + " routes");
    });
    return srv;
  }
}

function parseUrlEncoded(s, into) {
  if (!s) return;
  for (const kv of String(s).split("&")) {
    if (!kv) continue;
    const eq = kv.indexOf("=");
    const k = eq < 0 ? kv : kv.slice(0, eq);
    const v = eq < 0 ? "" : kv.slice(eq + 1);
    try {
      into[decodeURIComponent(k.replace(/\+/g, " "))] = decodeURIComponent(v.replace(/\+/g, " "));
    } catch (e) { /* 不正なエンコードは無視 */ }
  }
}

const VERSION = "0.1.0";

module.exports = { RailsApp, AkashicDB, BranchSpace, compileErb, badaLiteral, badaStr, VERSION };
