/*
 * badalib.js — Bada アプリのランタイムライブラリ (ホスト組込み関数)
 *
 * Bada プログラムはアプリの「頭脳」(計算・設計・対話の流れ) を書き、
 * 重い処理 (三角形メッシュ・WebGL・図面の投影・Transformer の行列演算) は
 * ここに用意した組込み関数として呼び出します。
 *
 *   数学      sqrt exp ln log10 sin cos tan asin acos atan atan2 sinh cosh tanh asinh acosh
 *             floor ceil round int pow pi euler min2 max2 sig fixed sci rand rand_seed num
 *   文字列    substr find contains startswith endswith upper lower trim split join replace
 *             regex_find chars
 *   配列      slice copy range sort_num fill
 *   方程式    eq_get eq_search eq_count eq_tags
 *   GPT       gpt_ready gpt_encode gpt_decode gpt_logits gpt_block gpt_info
 *   3D CAD    cad_clear cad_torus cad_sphere cad_cylinder cad_cone cad_box cad_lathe cad_knot
 *             cad_fig8 cad_pose cad_hide cad_color cad_dim cad_bom cad_note cad_parts cad_bounds
 *   図面      sheet_draw
 *   UI        ui_param ui_check ui_select ui_text ui_set param ui_button ui_output ui_plot ui_hud
 *             ui_chips ui_toast view_set view_fit
 *   対話      chat_reply chat_ref chat_gen chat_stream chat_code
 *   要求      ui_request (日本語の要求欄 → Bada の on_request(q))  export_file
 *   ファイル  file_write file_read file_exists (Bada が書いたプログラムを保存)
 *   論文      paper_loaded paper_info paper_eqs paper_eq paper_tags paper_params paper_stat paper_search paper_text
 *             (投稿された論文 PDF を paper.js が解析したもの)
 *   知識      kb_ready kb_tokens kb_ndocs kb_nchunks kb_avglen kb_postings kb_len kb_doc kb_nsources kb_source
 *             (BadaClaude: 論文 10 本 + 方程式の転置索引。採点は Bada 側)
 *   Claude    claude_ready claude_model claude_ask (利用者が API キーを設定したときだけ)
 *   Bada      bada_expr (式を評価)
 *
 * 環境 (env) の ui / chat / exporter はタブごとの UI アダプタ。Node ではスタブで動く。
 */
(function (root) {
  "use strict";
  const CAD = root.CTCad || (typeof require !== "undefined" ? require("./cad.js") : null);
  const { m4, v3, shapes } = CAD;

  const toNum = (v) => (typeof v === "bigint" ? Number(v) : +v);
  const arr = (v) => (Array.isArray(v) ? v : []);

  // ------------------------------------------------------------ 数学・文字列・配列
  function mathLib(env) {
    let seed = 0x2111;
    const rng = () => { // mulberry32
      seed = (seed + 0x6d2b79f5) >>> 0; let t = seed;
      t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const f1 = (fn) => (x) => fn(toNum(x));
    return {
      sqrt: f1(Math.sqrt), exp: f1(Math.exp), ln: f1(Math.log), log10: f1(Math.log10),
      sin: f1(Math.sin), cos: f1(Math.cos), tan: f1(Math.tan), asin: f1(Math.asin), acos: f1(Math.acos), atan: f1(Math.atan),
      atan2: (y, x) => Math.atan2(toNum(y), toNum(x)),
      sinh: f1(Math.sinh), cosh: f1(Math.cosh), tanh: f1(Math.tanh), asinh: f1(Math.asinh), acosh: f1(Math.acosh),
      floor: f1(Math.floor), ceil: f1(Math.ceil), round: f1(Math.round), int: f1(Math.trunc),
      pow: (a, b) => Math.pow(toNum(a), toNum(b)), pi: () => Math.PI, euler: () => Math.E,
      min2: (a, b) => Math.min(toNum(a), toNum(b)), max2: (a, b) => Math.max(toNum(a), toNum(b)),
      sig: (x, p) => +toNum(x).toPrecision(Math.max(1, Math.min(21, toNum(p) || 6))),
      fixed: (x, n) => toNum(x).toFixed(Math.max(0, Math.min(20, toNum(n) || 0))),
      sci: (x, n) => toNum(x).toExponential(Math.max(0, Math.min(20, toNum(n) || 3))),
      rand: () => (env.random ? env.random() : rng()),
      rand_seed: (s) => { seed = toNum(s) >>> 0; return null; },
      num: (s) => { const v = parseFloat(s); return isNaN(v) ? null : v; },
      now_ms: () => Date.now(),
      // 文字列 (コードポイント単位)
      substr: (s, a, b) => Array.from(String(s)).slice(toNum(a), b == null ? undefined : toNum(b)).join(""),
      find: (s, sub) => { const i = String(s).indexOf(String(sub)); return i < 0 ? -1 : Array.from(String(s).slice(0, i)).length; },
      contains: (s, sub) => String(s).toLowerCase().includes(String(sub).toLowerCase()),
      startswith: (s, p) => String(s).startsWith(String(p)),
      endswith: (s, p) => String(s).endsWith(String(p)),
      upper: (s) => String(s).toUpperCase(), lower: (s) => String(s).toLowerCase(), trim: (s) => String(s).trim(),
      split: (s, sep) => String(s).split(String(sep)), join: (a, sep) => arr(a).map((x) => (x == null ? "nil" : String(x))).join(sep == null ? "" : String(sep)),
      replace: (s, a, b) => String(s).split(String(a)).join(String(b)),
      regex_find: (s, pat) => { try { return String(s).match(new RegExp(String(pat), "gu")) || []; } catch (e) { return []; } },
      chars: (s) => Array.from(String(s)),
      slice: (a, i, j) => arr(a).slice(toNum(i), j == null ? undefined : toNum(j)),
      copy: (a) => JSON.parse(JSON.stringify(arr(a))),
      range: (a, b) => { const o = []; for (let i = toNum(a); i < toNum(b); i++) o.push(i); return o; },
      fill: (n, v) => Array.from({ length: toNum(n) }, () => v),
      sort_num: (a) => arr(a).slice().sort((x, y) => toNum(x) - toNum(y)),
    };
  }

  // ------------------------------------------------------------ 方程式レジストリ
  function eqLib(env) {
    const byId = new Map(env.equations.map((e) => [e.id.toUpperCase(), e]));
    const rec = (e) => [e.id, e.status, e.tags.slice(), e.expr, e.value];
    return {
      eq_get: (id) => { const e = byId.get(String(id).toUpperCase()); return e ? rec(e) : null; },
      eq_search: (q, n, tag) => {
        const f = tag ? (e) => e.tags.includes(String(tag)) : null;
        return env.index.search(String(q), toNum(n) || 5, f).map((e) => e.id);
      },
      eq_count: (status) => (status ? env.equations.filter((e) => e.status === status).length : env.equations.length),
      eq_tags: (q) => env.index.tagsIn(String(q)),
    };
  }

  // ------------------------------------------------------------ Transformer (ContactGPT)
  function gptLib(env) {
    const G = root.ContactGPT || (typeof require !== "undefined" ? require("./gpt.js") : null);
    const model = () => env.model && env.model();
    return {
      gpt_ready: () => !!model(),
      gpt_encode: (s) => (model() ? model().encode(String(s)) : []),
      gpt_decode: (ids) => (model() ? model().decode(arr(ids).map(toNum)) : ""),
      gpt_block: () => (model() ? model().cfg.block : 0),
      // 文脈 ids (末尾 block 文字) に対する次の文字のロジット (語彙長の配列)
      gpt_logits: (ids) => {
        const m = model(); if (!m) return [];
        const ctx = arr(ids).slice(-m.cfg.block).map(toNum);
        const { logits } = m.forward(new G.Tape(false), Int32Array.from(ctx), 1, ctx.length, null, true);
        return Array.from(logits.subarray(0, m.vocab.length));
      },
      gpt_info: () => {
        const m = model(); if (!m) return [];
        return [["層", m.cfg.nLayer], ["ヘッド", m.cfg.nHead], ["埋め込み次元", m.cfg.nEmbd], ["文脈長", m.cfg.block], ["語彙", m.vocab.length], ["パラメータ", m.nParams], ["学習ステップ", m.step]];
      },
    };
  }

  // ------------------------------------------------------------ 3D CAD シーン
  class Scene {
    constructor() { this.parts = new Map(); this.meshCache = new Map(); this.dims = []; this.bom = []; this.notes = []; this.version = 0; }
    clear() { this.parts.clear(); this.dims = []; this.bom = []; this.notes = []; this.version++; }
    mesh(key, make) {
      if (!this.meshCache.has(key)) { if (this.meshCache.size > 400) this.meshCache.clear(); this.meshCache.set(key, make()); }
      return this.meshCache.get(key);
    }
    add(id, name, color, key, make) {
      const old = this.parts.get(id);
      const p = { id, name: String(name), color: normColor(color), mesh: this.mesh(key, make), matrix: old ? old.matrix : null, hidden: old ? old.hidden : false };
      this.parts.set(id, p); this.version++;
      return id;
    }
    list() { return Array.from(this.parts.values()); }
    visible() { return this.list().filter((p) => !p.hidden); }
    baked() { return this.visible().map((p) => Object.assign({}, p, { mesh: p.matrix ? p.mesh.transform(p.matrix) : p.mesh, matrix: null })); }
  }
  function normColor(c) {
    const s = String(c || "#9e9e9e");
    return /^#[0-9a-f]{6}$/i.test(s) ? s : "#9e9e9e";
  }
  function alignZ(dir) {
    const n = v3.norm(dir), z = [0, 0, 1], ax = v3.cross(z, n), s = v3.len(ax);
    if (s < 1e-9) return n[2] > 0 ? m4.ident() : m4.rot([1, 0, 0], Math.PI);
    return m4.rot(ax, Math.atan2(s, v3.dot(z, n)));
  }
  // 姿勢 = 変換命令の列 [["T",x,y,z], ["R",ax,ay,az,角度], ["S",sx,sy,sz], ["A",dx,dy,dz]] を左から合成
  function opsMatrix(ops) {
    let M = m4.ident();
    for (const o of arr(ops)) {
      const a = arr(o).map((x, i) => (i ? toNum(x) : x));
      let T;
      if (a[0] === "T") T = m4.translate(a[1] || 0, a[2] || 0, a[3] || 0);
      else if (a[0] === "R") T = m4.rot([a[1], a[2], a[3]], a[4] || 0);
      else if (a[0] === "S") T = m4.scale(a[1], a[2] == null ? a[1] : a[2], a[3] == null ? a[1] : a[3]);
      else if (a[0] === "A") T = alignZ([a[1], a[2], a[3]]);
      else continue;
      M = m4.mul(M, T);
    }
    return M;
  }
  const r4 = (x) => Math.round(toNum(x) * 1e4) / 1e4;
  function cadLib(env) {
    const S = env.scene;
    const P = (id) => { const p = S.parts.get(String(id)); if (!p) throw new Error(`部品 ${id} がありません`); return p; };
    return {
      cad_clear: () => { S.clear(); return null; },
      cad_torus: (id, name, color, R, r) => S.add(String(id), name, color, `torus:${r4(R)}:${r4(r)}`, () => shapes.torus(toNum(R), toNum(r), Math.max(48, Math.min(160, Math.round(toNum(R) * 2))), 16)),
      cad_sphere: (id, name, color, r) => S.add(String(id), name, color, `sphere:${r4(r)}`, () => shapes.sphere(toNum(r), 40, 20)),
      cad_cylinder: (id, name, color, r, h) => S.add(String(id), name, color, `cyl:${r4(r)}:${r4(h)}`, () => shapes.cylinder(toNum(r), toNum(h), 24)),
      cad_cone: (id, name, color, r1, r2, h) => S.add(String(id), name, color, `cone:${r4(r1)}:${r4(r2)}:${r4(h)}`, () => shapes.cone(toNum(r1), toNum(r2), toNum(h), 24)),
      cad_box: (id, name, color, sx, sy, sz) => S.add(String(id), name, color, `box:${r4(sx)}:${r4(sy)}:${r4(sz)}`, () => shapes.box(toNum(sx), toNum(sy), toNum(sz))),
      // 回転体: profile = [[半径, z], ...] (下 → 上)
      cad_lathe: (id, name, color, profile, seg) => {
        const pr = arr(profile).map((p) => [toNum(p[0]), toNum(p[1])]);
        return S.add(String(id), name, color, "lathe:" + (seg || 64) + ":" + pr.map((p) => r4(p[0]) + "," + r4(p[1])).join(";"), () => shapes.lathe(pr, toNum(seg) || 64));
      },
      // (p,q) トーラス結び目 — Jones 3_1 = (2,3), 5_1 = (2,5)
      cad_knot: (id, name, color, R, r, p, q, tube) => S.add(String(id), name, color, `knot:${r4(R)}:${r4(r)}:${p}:${q}:${r4(tube)}`, () => shapes.torusKnot(toNum(R), toNum(r), toNum(p), toNum(q), toNum(tube))),
      cad_fig8: (id, name, color, scale, tube) => S.add(String(id), name, color, `fig8:${r4(scale)}:${r4(tube)}`, () => shapes.figureEight(toNum(scale), toNum(tube))),
      cad_pose: (id, ops) => { P(id).matrix = opsMatrix(ops); return null; },
      cad_hide: (id, hidden) => { P(id).hidden = hidden == null ? true : !!hidden; return null; },
      cad_color: (id, color) => { P(id).color = normColor(color); return null; },
      cad_parts: () => S.list().map((p) => [p.id, p.name]),
      cad_bounds: () => { const b = boundsOf(S.baked()); return [b.min, b.max]; },
      // 図面注記: 直線寸法 (view, a:[x,y], b:[x,y], オフセット, 文字) / 半径寸法 (view, 中心, r, 角度, 文字)
      cad_dim: (view, a, b, off, text) => { S.dims.push({ view: String(view), type: "linear", a: arr(a).map(toNum), b: arr(b).map(toNum), off: toNum(off), text: String(text) }); return null; },
      cad_rdim: (view, c, r, ang, text) => { S.dims.push({ view: String(view), type: "radius", c: arr(c).map(toNum), r: toNum(r), ang: toNum(ang), text: String(text) }); return null; },
      cad_bom: (no, name, material, qty) => { S.bom.push([String(no), String(name), String(material), String(qty)]); return null; },
      cad_note: (text) => { S.notes.push(String(text)); return null; },
      sheet_draw: (title, number, author, theme) => {
        const D = root.CTDraft || require("./drafting.js");
        const s = D.sheet({ parts: S.baked(), dims: S.dims, bom: S.bom, notes: S.notes, title: String(title || "設計図"), number: String(number || "BADA-0001"),
          author: author ? String(author) : undefined, theme: theme === "paper" ? "paper" : "blue", colorLines: env.colorLines ? env.colorLines() : false });
        env.lastSheet = s; if (env.onSheet) env.onSheet(s);
        return s.scale;
      },
    };
  }
  function boundsOf(parts) {
    const mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    for (const p of parts) { const b = p.mesh.bounds(); for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], b.min[k]); mx[k] = Math.max(mx[k], b.max[k]); } }
    return { min: mn, max: mx };
  }

  // ------------------------------------------------------------ UI / 対話 (アダプタに委譲)
  function uiLib(env) {
    const ui = env.ui || {}, chat = env.chat || {};
    const call = (o, k, ...a) => (o[k] ? o[k](...a) : null);
    return {
      ui_param: (key, label, def, step) => call(ui, "param", String(key), String(label), toNum(def), step == null ? null : toNum(step)),
      ui_check: (key, label, def) => call(ui, "check", String(key), String(label), !!def),
      ui_select: (key, label, options, def) => call(ui, "select", String(key), String(label), arr(options).map(String), String(def)),
      ui_text: (key, label, def) => call(ui, "text", String(key), String(label), String(def == null ? "" : def)),
      ui_color: (key, label, def) => call(ui, "color", String(key), String(label), normColor(def)),
      ui_set: (key, v) => call(ui, "set", String(key), v),
      param: (key) => call(ui, "get", String(key)),
      ui_button: (label, fn) => call(ui, "button", String(label), String(fn)),
      ui_output: (key, label, value) => call(ui, "output", String(key), String(label), value),
      ui_section: (title) => call(ui, "section", String(title)),
      // series = [[名前, 色, [[x, y], ...]], ...]  marks = [[x, y, ラベル], ...]
      ui_plot: (key, title, series, marks) => call(ui, "plot", String(key), String(title), arr(series), arr(marks)),
      ui_hud: (text) => call(ui, "hud", String(text)),
      ui_toast: (text) => call(ui, "toast", String(text)),
      ui_chips: (list) => call(ui, "chips", arr(list).map(String)),
      view_set: (name) => call(ui, "view", String(name)),
      view_fit: () => call(ui, "fit"),
      chat_reply: (md) => call(chat, "reply", String(md)),
      chat_ref: (id) => call(chat, "ref", String(id)),
      chat_gen: (text) => call(chat, "gen", String(text)),
      // prompt から最大 n 文字を生成して流し込む (毎文字 Bada の gen_next(ids) / gen_stop(out) を呼ぶ)
      chat_stream: (prompt, n) => call(chat, "stream", String(prompt), toNum(n) || 100),
      // Bada が書いた Bada プログラムを表示 (実行・IDE で開くボタン付き)
      chat_code: (file, src, target, desc) => call(chat, "code", String(file), String(src), String(target || "console"), String(desc || "")),
      // 要求欄 (日本語の要求・質問 → on_request(q))
      ui_request: (placeholder) => call(ui, "request", String(placeholder || "")),
      // 書き出し: "stl" / "obj" / "dxf3" / "png" / "sheet" / "sheetpng" / "sheetdxf" / "params"
      export_file: (kind) => call(ui, "export", String(kind)),
      file_write: (name, src) => { const n = String(name); env.files[n] = String(src); if (env.onFileWrite) env.onFileWrite(n); return n; },
      file_read: (name) => (String(name) in env.files ? env.files[String(name)] : null),
      file_exists: (name) => String(name) in env.files,
    };
  }

  // 投稿された論文 (env.paper() が paper.js の analyze 結果を返す)
  function paperLib(env) {
    const P = () => (env.paper ? env.paper() : null);
    let idxFor = null, idx = null;
    const index = () => {
      const p = P(); if (!p) return null;
      if (idxFor !== p) {
        const C = root.CTChat || require("./chat.js");
        idx = new C.Index(p.equations.map((e) => ({ id: e.id, expr: e.text, tags: e.tags, status: e.status, value: e.value })));
        idxFor = p;
      }
      return idx;
    };
    const rec = (e) => [e.id, e.status, e.tags.slice(), e.text, e.value, e.page];
    return {
      paper_loaded: () => !!P(),
      // [題名, ファイル名, ページ数, 方程式数, 登録簿形式か, 種 (ハッシュ)]
      paper_info: () => { const p = P(); return p ? [p.title, p.file, p.pages, p.equations.length, p.registry, p.hash % 1000003] : null; },
      // 代表的な式 n 本 (数値評価・成立・不成立の式を優先し、残りは記号式)
      paper_eqs: (n) => {
        const p = P(); if (!p) return [];
        const k = Math.max(1, toNum(n) || 40), num = p.equations.filter((e) => e.status !== "symb"), sym = p.equations.filter((e) => e.status === "symb");
        const a = num.slice(0, Math.ceil(k / 2)); return a.concat(sym.slice(0, k - a.length)).concat(num.slice(a.length)).slice(0, k).map(rec);
      },
      paper_eq: (id) => { const p = P(); const e = p && p.equations.find((x) => x.id.toUpperCase() === String(id).toUpperCase()); return e ? rec(e) : null; },
      paper_tags: () => { const p = P(); return p ? Object.entries(p.tagCount).sort((a, b) => b[1] - a[1]) : []; },
      paper_params: (n) => {
        const p = P(); if (!p) return [];
        const seen = new Set(), out = [];
        for (const x of p.params) { if (seen.has(x.name)) continue; seen.add(x.name); out.push([x.name, x.value, x.unit]); if (out.length >= (toNum(n) || 12)) break; }
        return out;
      },
      paper_stat: () => { const p = P(); return p ? [p.stat.symb || 0, p.stat.calc || 0, p.stat.holds || 0, p.stat.differs || 0] : [0, 0, 0, 0]; },
      paper_search: (q, n) => { const ix = index(); return ix ? ix.search(String(q), toNum(n) || 5).map((e) => e.id) : []; },
      paper_text: (n) => { const p = P(); return p ? p.excerpt.slice(0, toNum(n) || 10) : []; },
    };
  }

  // ------------------------------------------------------------ 知識ベース (BadaClaude)
  // 論文 10 本のチャンク (data/badaclaude/kb.json) + 方程式 2111 本を 1 つの文書集合にし、
  // 転置索引 (語 → [[文書番号, 出現数], …]) だけをここで作る。BM25 の採点・順位付け・
  // 回答の組み立ては Bada (apps/badaclaude.bada) が行う。
  const KB_TAG_JA = { ROT: "複素回転体", SR: "特殊相対論", GAMMA: "ガンマ関数", ZETA: "ゼータ関数", BETA: "ベータ関数", JONES: "Jones 多項式",
    MANIFOLD: "大域的部分積分多様体", QUANTUM: "量子", TRANSPORT: "輸送", ENTROPY: "エントロピー", OTHER: "その他" };
  function kbTokens(s) {
    const out = [];
    const re = /[\p{Script=Han}々〆]+|[\p{Script=Katakana}ー]+|[\p{Script=Hiragana}]+|[A-Za-z][A-Za-z0-9_'.]*[A-Za-z0-9]|[A-Za-z]|\d+(?:\.\d+)?|[α-ωΑ-Ωβζγπψφθλ∫∮∇□⊕⊗ℏ]/gu;
    let m; const low = String(s).toLowerCase();
    while ((m = re.exec(low))) {
      const w = m[0];
      if (/^[\p{Script=Han}]+$/u.test(w) && w.length > 2) { out.push(w); for (let i = 0; i + 2 <= w.length; i++) out.push(w.slice(i, i + 2)); }
      else out.push(w);
    }
    return out;
  }
  const kbCache = new WeakMap();
  function kbIndex(env) {
    const kb = typeof env.kb === "function" ? env.kb() : env.kb;
    if (!kb) return null;
    let I = kbCache.get(kb);
    if (I) return I;
    const docs = [];
    for (const c of kb.chunks || []) { const src = kb.sources[c.src] || { title: "?" }; docs.push({ kind: "chunk", id: "S" + c.src + "p" + c.page, title: src.title, page: c.page, text: c.text, src: c.src }); }
    for (const e of env.equations || []) docs.push({ kind: "eq", id: e.id, title: "", page: 0, text: e.expr + (e.value ? " = " + e.value : ""), src: -1, tags: e.tags });
    const post = new Map(); let total = 0;
    docs.forEach((d, i) => {
      const toks = kbTokens(d.kind === "chunk" ? d.title + "\n" + d.text : d.text + " " + d.tags.map((t) => t + " " + (KB_TAG_JA[t] || t)).join(" ") + " " + d.id);
      const tf = new Map(); for (const t of toks) tf.set(t, (tf.get(t) || 0) + 1);
      for (const [t, n] of tf) { let l = post.get(t); if (!l) post.set(t, (l = [])); l.push([i, n]); }
      d.len = toks.length; total += toks.length;
    });
    I = { kb, docs, post, avg: docs.length ? total / docs.length : 1 };
    kbCache.set(kb, I);
    return I;
  }
  function kbLib(env) {
    const I = () => kbIndex(env);
    const doc = (i) => { const x = I(); return x && x.docs[toNum(i)]; };
    return {
      kb_ready: () => !!I(),
      kb_tokens: (s) => kbTokens(String(s)),
      kb_ndocs: () => (I() ? I().docs.length : 0),
      kb_avglen: () => (I() ? I().avg : 1),
      kb_postings: (t) => { const x = I(); const l = x && x.post.get(String(t)); return l ? l.map((p) => p.slice()) : []; },
      kb_len: (i) => { const d = doc(i); return d ? d.len : 0; },
      // [種類 ("chunk" | "eq"), ID, 論文名, ページ, 本文, 論文番号]
      kb_doc: (i) => { const d = doc(i); return d ? [d.kind, d.id, d.title, d.page, d.text, d.src] : null; },
      kb_nchunks: () => (I() ? I().docs.filter((d) => d.kind === "chunk").length : 0),
      kb_nsources: () => (I() ? I().kb.sources.length : 0),
      kb_source: (n) => { const x = I(); const s = x && x.kb.sources[toNum(n)]; return s ? [s.title, s.file, s.pages] : null; },
    };
  }

  // ------------------------------------------------------------ Claude API (BadaClaude, 任意)
  // 何を検索し何を Claude に渡すか (システムプロンプト) は Bada が決め、ホストは送信と
  // ストリーミング表示だけを担う。API キーは端末の localStorage にだけ保存される。
  function claudeLib(env) {
    const C = env.claude || {};
    return {
      claude_ready: () => !!(C.ready && C.ready()),
      claude_model: () => (C.model ? C.model() : ""),
      claude_ask: (system, q) => (C.ask ? C.ask(String(system), String(q)) : null),
    };
  }

  // Bada の式を同じ VM 上で評価する (電卓・REPL)
  function badaLib(env) {
    return {
      bada_expr: function (src) {
        const vm = this, B = root.Bada || require("./bada.js");
        const key = "__expr_value";
        try {
          vm.eval(`${key} <- (${String(src)})`);
          const fr = vm.frames[vm.frames.length - 1]; const v = fr[key]; delete fr[key];
          return v === undefined ? null : v;
        } catch (e) { return "エラー: " + e.message; }
      },
    };
  }

  // すべてのホスト関数をまとめる
  function makeHost(env) {
    return Object.assign({}, mathLib(env), env.equations ? eqLib(env) : {}, gptLib(env), env.scene ? cadLib(env) : {}, uiLib(env), paperLib(env), kbLib(env), claudeLib(env), badaLib(env));
  }

  // Bada アプリのインスタンス: ソースを VM に読み込み、build / frame / on_message を呼ぶ
  class BadaApp {
    constructor(env) {
      this.env = env; this.vm = null; this.error = null;
    }
    start(src, name) {
      const B = root.Bada || require("./bada.js");
      const env = this.env;
      if (env.scene) env.scene.clear();
      if (env.ui && env.ui.reset) env.ui.reset();
      this.vm = new B.BadaVM({ host: makeHost(env), files: env.files || {}, onPrint: env.onPrint, onTuple: env.onTuple, maxSteps: 5e7 });
      this.error = null;
      try { this.vm.load(src, name); if (this.vm.has("build")) this.vm.call("build", []); }
      catch (e) { this.error = e; if (env.onError) env.onError(e); }
      return this;
    }
    call(fn, args) {
      if (!this.vm || !this.vm.has(fn)) return null;
      try { return this.vm.call(fn, args || []); }
      catch (e) { this.error = e; if (this.env.onError) this.env.onError(e); return null; }
    }
    has(fn) { return !!(this.vm && this.vm.has(fn)); }
    eval(src) { this.vm.maxSteps = 5e7; this.vm.eval(src); }
  }

  const api = { mathLib, eqLib, gptLib, cadLib, uiLib, paperLib, kbLib, kbTokens, claudeLib, makeHost, Scene, BadaApp, opsMatrix, boundsOf };
  root.BadaLib = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
