/*
 * app.js — BadaClaude のホスト (UI と I/O だけ)
 *
 * 対話の中身は brain.bada (Bada) が決めます。ここで行うのは:
 *   - Bada 処理系 (engine.js) の上で brain.bada を起動し、respond() を呼ぶ
 *   - 画面描画 (Markdown)、履歴の保存
 *   - Claude API モードのとき、brain が組み立てたシステムプロンプトで
 *     https://api.anthropic.com/v1/messages にストリーミング送信する
 */
"use strict";
(function () {
  const $ = id => document.getElementById(id);
  const store = {
    get(k, d) { try { const v = localStorage.getItem("badaclaude:" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("badaclaude:" + k, JSON.stringify(v)); } catch (e) { /* 保存不可の環境でも動く */ } }
  };
  const settings = Object.assign({ mode: "local", key: "", model: "claude-opus-5-5", effort: "medium", theme: "" }, store.get("settings", {}));
  if (settings.theme) document.documentElement.dataset.theme = settings.theme;

  /* ── Bada の頭脳を起動 ── */
  const KB = JSON.parse($("kb-data").textContent);
  const BRAIN_SRC = $("brain-src").textContent;
  const brain = new BadaEngine.Interp({ host: { kb: KB, mode: () => (settings.mode === "llm" && settings.key ? "llm" : "local") }, maxSteps: 4e9 });
  const callBrain = (name, args) => brain.call(brain.global.get(name), args || []);

  /* ── Markdown (HTML は常にエスケープしてから整形) ── */
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  function inline(s) {
    return esc(s)
      .replace(/`([^`]+)`/g, (m, c) => "<code>" + c + "</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[\s(（])_([^_]+)_(?=$|[\s).,。、）])/g, "$1<em>$2</em>")
      .replace(/(^|[\s(（])\*([^*\s][^*]*)\*(?=$|[\s).,。、）])/g, "$1<em>$2</em>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  }
  function md(src) {
    const lines = String(src).replace(/\r/g, "").split("\n"); let html = "", i = 0;
    while (i < lines.length) {
      const l = lines[i];
      const fence = /^```\s*([\w-]*)\s*$/.exec(l);
      if (fence) {
        const buf = []; i++;
        while (i < lines.length && !/^```\s*$/.test(lines[i])) buf.push(lines[i++]);
        i++;
        const lang = fence[1] || "";
        html += `<pre data-lang="${esc(lang)}">${lang === "bada" ? '<button class="run">▶ 実行</button>' : ""}<code>${esc(buf.join("\n"))}</code></pre>`;
        continue;
      }
      if (/^\s*\|.*\|\s*$/.test(l) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
        const cells = r => r.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
        let t = "<table><thead><tr>" + cells(l).map(c => "<th>" + inline(c) + "</th>").join("") + "</tr></thead><tbody>";
        i += 2;
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { t += "<tr>" + cells(lines[i]).map(c => "<td>" + inline(c) + "</td>").join("") + "</tr>"; i++; }
        html += t + "</tbody></table>"; continue;
      }
      const h = /^(#{1,3})\s+(.*)$/.exec(l);
      if (h) { html += `<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`; i++; continue; }
      if (/^>\s?/.test(l)) {
        const buf = []; while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ""));
        html += "<blockquote>" + buf.map(inline).join("<br>") + "</blockquote>"; continue;
      }
      if (/^\s*[-*]\s+/.test(l)) {
        let t = "<ul>"; while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) t += "<li>" + inline(lines[i++].replace(/^\s*[-*]\s+/, "")) + "</li>";
        html += t + "</ul>"; continue;
      }
      if (/^\s*\d+[.)]\s+/.test(l)) {
        let t = "<ol>"; while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) t += "<li>" + inline(lines[i++].replace(/^\s*\d+[.)]\s+/, "")) + "</li>";
        html += t + "</ol>"; continue;
      }
      if (!l.trim()) { i++; continue; }
      const buf = []; while (i < lines.length && lines[i].trim() && !/^(```|#{1,3}\s|>|\s*[-*]\s+|\s*\d+[.)]\s+)/.test(lines[i]) && !/^\s*\|.*\|\s*$/.test(lines[i])) buf.push(lines[i++]);
      if (!buf.length) { buf.push(lines[i++]); }
      html += "<p>" + buf.map(inline).join("<br>") + "</p>";
    }
    return html;
  }

  /* ── 会話の保存 ── */
  let convs = store.get("convs", []);
  let cur = null;
  const saveConvs = () => store.set("convs", convs.slice(0, 50));
  function newConv() { cur = { id: Date.now().toString(36), title: "新しいチャット", msgs: [] }; renderThread(); renderHist(); }
  function renderHist() {
    const h = $("hist"); h.innerHTML = "";
    convs.forEach(c => {
      const d = document.createElement("div"); d.className = "item" + (cur && c.id === cur.id ? " on" : "");
      const t = document.createElement("button"); t.className = "t"; t.textContent = c.title;
      t.onclick = () => { cur = c; renderThread(); renderHist(); show("chat"); closeSide(); };
      const x = document.createElement("button"); x.className = "x"; x.textContent = "×"; x.title = "削除";
      x.onclick = e => { e.stopPropagation(); convs = convs.filter(z => z !== c); saveConvs(); if (cur === c) newConv(); else renderHist(); };
      d.append(t, x); h.appendChild(d);
    });
  }

  /* ── スレッド描画 ── */
  const SUGGEST = ["ゼータ関数とベータ関数の関係は?", "リーマン予想は証明されたの?", "計算 rs_Z(14.134725)", "ベル状態を作って", "方程式は全部で何本?", "輸送機の設計図", "reviser で文法を拡張して", "あなたは誰?"];
  function renderThread() {
    const th = $("thread"); th.innerHTML = "";
    $("title").textContent = cur.title;
    if (!cur.msgs.length) {
      const e = document.createElement("div"); e.className = "empty";
      e.innerHTML = '<div class="logo" style="margin:0 auto;width:44px;height:44px;border-radius:12px;font-size:20px">⟨ψ⟩</div><div class="big">何を調べましょうか?</div><p>量子プログラミング言語 Bada で書かれた対話エンジン — 論文 10 本・方程式 2111 本・数値核・量子回路</p>';
      const ch = document.createElement("div"); ch.className = "chips";
      SUGGEST.forEach(s => { const b = document.createElement("button"); b.textContent = s; b.onclick = () => send(s); ch.appendChild(b); });
      e.appendChild(ch); th.appendChild(e); return;
    }
    cur.msgs.forEach(m => th.appendChild(msgEl(m)));
    scrollDown();
  }
  function msgEl(m) {
    const d = document.createElement("div"); d.className = "msg " + (m.role === "user" ? "user" : "bot");
    if (m.role === "user") { const b = document.createElement("div"); b.className = "bubble"; b.textContent = m.text; d.appendChild(b); return d; }
    d.innerHTML = '<div class="av">⟨ψ⟩</div><div class="body"><div class="md"></div></div>';
    fillBot(d, m); return d;
  }
  function fillBot(d, m) {
    const body = d.querySelector(".body"); const box = body.querySelector(".md");
    box.innerHTML = md(m.text || ""); box.classList.toggle("cursor", !!m.streaming);
    box.querySelectorAll("pre[data-lang=bada] .run").forEach(b => b.onclick = () => {
      $("code").value = b.parentElement.querySelector("code").textContent; show("editor"); runEditor();
    });
    body.querySelectorAll(".meta,details.trace").forEach(x => x.remove());
    if (m.streaming) return;
    const meta = document.createElement("div"); meta.className = "meta";
    const eng = m.engine === "llm" ? `Claude API (${esc(m.model || "")}) + Bada 文脈` : "ローカル Bada エンジン";
    meta.innerHTML = `<span>${eng}</span>` + (m.intent ? `<span>意図: ${esc(m.intent)} · 確信度 ${(+m.conf).toFixed(2)}</span>` : "") + '<button class="cp">コピー</button>';
    meta.querySelector(".cp").onclick = () => { try { navigator.clipboard.writeText(m.text); } catch (e) { } };
    body.appendChild(meta);
    if (m.trace && m.trace.length) {
      const t = document.createElement("details"); t.className = "trace";
      t.innerHTML = "<summary>思考過程 — Bada パイプライン</summary><table>" +
        m.trace.map(r => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td></tr>`).join("") +
        (m.sources && m.sources.length ? `<tr><td>出典</td><td>${m.sources.map(esc).join("<br>")}</td></tr>` : "") + "</table>";
      body.appendChild(t);
    }
  }
  const scrollDown = () => { const s = $("msgs"); s.scrollTop = s.scrollHeight; };

  /* ── 送信 ── */
  let busy = false;
  async function send(text) {
    text = (text || "").trim(); if (!text || busy) return;
    busy = true; $("send").disabled = true;
    if (!convs.includes(cur)) convs.unshift(cur);
    if (!cur.msgs.length) cur.title = text.replace(/\s+/g, " ").slice(0, 28);
    cur.msgs.push({ role: "user", text });
    renderThread(); renderHist();
    const bot = { role: "assistant", text: "", streaming: true };
    cur.msgs.push(bot);
    const el = msgEl(bot); $("thread").appendChild(el); scrollDown();
    try {
      await new Promise(r => setTimeout(r, 10));
      const r = callBrain("respond", [text]);
      Object.assign(bot, { intent: r.intent, conf: r.conf, trace: r.trace, sources: r.sources });
      if (r.mode === "llm") {
        bot.engine = "llm"; bot.model = settings.model;
        await askClaude(r.system, bot, () => { fillBot(el, bot); scrollDown(); });
      } else {
        bot.engine = "local"; bot.text = r.text;
      }
    } catch (e) {
      bot.text = (bot.text ? bot.text + "\n\n" : "") + "⚠ " + (e && e.message ? e.message : String(e));
    }
    bot.streaming = false; fillBot(el, bot); scrollDown();
    saveConvs(); renderLedger();
    busy = false; $("send").disabled = false;
  }

  /* ── Claude API (Messages API, SSE ストリーミング) ── */
  function history() {
    const out = [];
    for (const m of cur.msgs) {
      if (m.streaming) continue;
      const role = m.role === "user" ? "user" : "assistant";
      if (!m.text) continue;
      if (out.length && out[out.length - 1].role === role) out[out.length - 1].content += "\n\n" + m.text;
      else out.push({ role, content: m.text });
    }
    while (out.length && out[0].role !== "user") out.shift();
    return out.slice(-20);
  }
  async function askClaude(system, bot, onDelta) {
    const body = { model: settings.model, max_tokens: 16000, stream: true, system, messages: history() };
    const headers = {
      "content-type": "application/json",
      "x-api-key": settings.key,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true"
    };
    if (settings.model !== "claude-haiku-4-5") body.output_config = { effort: settings.effort };
    if (settings.model === "claude-opus-5-5" || settings.model === "claude-sonnet-5-5") {
      // 安全分類器による拒否時はサーバー側で自動的に代替モデルへ
      headers["anthropic-beta"] = "server-side-fallback-2026-07-01";
      body.fallbacks = "default";
    }
    const res = await fetch("https://api.anthropic.com/v1/messages", { method: "POST", headers, body: JSON.stringify(body) });
    if (!res.ok) {
      let msg = res.status + " " + res.statusText;
      try { const j = await res.json(); if (j.error && j.error.message) msg = res.status + ": " + j.error.message; } catch (e) { }
      throw new Error("Claude API エラー " + msg + (res.status === 401 ? " — API キーを確認してください。" : ""));
    }
    const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = "", stop = null;
    for (;;) {
      const { value, done } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      let k;
      while ((k = buf.indexOf("\n\n")) >= 0) {
        const block = buf.slice(0, k); buf = buf.slice(k + 2);
        const data = block.split("\n").filter(x => x.startsWith("data:")).map(x => x.slice(5).trim()).join("");
        if (!data) continue;
        let ev; try { ev = JSON.parse(data); } catch (e) { continue; }
        if (ev.type === "content_block_delta" && ev.delta && ev.delta.type === "text_delta") { bot.text += ev.delta.text; onDelta(); }
        else if (ev.type === "message_delta" && ev.delta) stop = ev.delta.stop_reason || stop;
        else if (ev.type === "error") throw new Error("Claude API: " + (ev.error && ev.error.message || "stream error"));
      }
    }
    if (stop === "refusal") bot.text += (bot.text ? "\n\n" : "") + "_この依頼は Claude の安全方針により応答できませんでした。_";
    if (stop === "max_tokens") bot.text += "\n\n_(出力上限に達したため途中で終了しました)_";
    bot.trace = (bot.trace || []).concat([["Claude", "stop_reason=" + stop + " · " + bot.text.length + " 字"]]);
    callBrain("after_llm", [bot.text, stop || ""]);
  }

  /* ── ビュー切り替え ── */
  function show(v) {
    document.querySelectorAll(".view").forEach(x => x.classList.toggle("on", x.id === "v-" + v));
    document.querySelectorAll("#tabs button").forEach(b => b.classList.toggle("on", b.dataset.v === v));
    if (v === "ledger") renderLedger();
    if (v === "eqs") renderEqs();
  }
  const closeSide = () => { $("side").classList.remove("open"); $("scrim").classList.remove("open"); };
  $("tabs").onclick = e => { const b = e.target.closest("button"); if (b) { show(b.dataset.v); closeSide(); } };
  $("menu").onclick = () => { $("side").classList.add("open"); $("scrim").classList.add("open"); };
  $("scrim").onclick = closeSide;
  $("newchat").onclick = () => { newConv(); show("chat"); closeSide(); };

  /* ── エディタ ── */
  const EXAMPLES = {
    "Unknown-Prior Engine (ゼロ保存 と |ψ|² = a)": `# 原稿 S.22 / Q.16 の再現
z := [1.6, 0.6, 0.1, -40, -0.4, 1.1, -40, 0.4]
a := softmax(z)
phi := map(range(8), |i| 0.3 * i)
cs := cognitive_system(a, [[a, phi], [unknown_prior(8), 0.5]], [0.7, 0.9])
print("base zeros      =", zeros_of(a))
print("posterior zeros =", cs.zeros)
print("|ψ|² = a 最大偏差 =", sci(cs.maxdiff, 2))
Omega >> ["engine", "verified", cs.zeros]
len(Omega)`,
    "ゼータ・ベータ・ガンマ": `print("ζ(2)         =", zeta(2), " π²/6 =", pi^2/6)
print("β(1/2, 1/2)  =", beta(0.5, 0.5), "  (= π, 臨界線の実部)")
print("Γ(1/2)²      =", gamma(0.5)^2)
print("ζ(−1)        =", zeta(-1))
# 定理 I-1: ζ(s) = 2^s π^(s−1) sin(πs/2) β(s,1−s)/Γ(s) ζ(1−s)
s := 2.5
lhs := zeta(s)
rhs := 2^s * pi^(s-1) * sin(pi*s/2) * beta(s, 1-s) / gamma(s) * zeta(1-s)
print("関数等式の差 =", abs(lhs - rhs))
# 定義方程式 ζ(s)/(x log x) = 1 の唯一解 x(s) = exp W(ζ(s))
x := exp(lambertw(zeta(2)))
print("x(2) =", x, "  検算 ζ(2)/(x log x) =", zeta(2) / (x * log(x)))`,
    "リーマン–ジーゲル Z と零点探索": `# Z(t) = e^{iθ(t)} ζ(1/2 + it) は実数値。符号変化の位置が非自明零点
zs := []
t := 10
while t < 40 {
  if rs_Z(t) * rs_Z(t + 0.1) < 0 { zs <- solve(|u| rs_Z(u), t, t + 0.1) }
  t = t + 0.1
}
print("零点 t =", map(zs, |z| round(z, 6)))`,
    "Q# 型量子回路 + @reviser 文法拡張": `@reviser GRAMMAR {
  rule bell(r) { H(r, 0); CNOT(r, 0, 1) }
  rule ghz(r, n) { H(r, 0); for k in range(n - 1) { CNOT(r, k, k + 1) } }
}
qubit q[2]
bell q
print("bell:", qstate(q))
qubit g[4]
ghz g, 4
print("ghz :", qstate(g))
print("測定:", map(range(4), |k| Measure(g, k)))
print("文法台帳:", rules())`,
    "Jones 多項式と設計図パラメータ": `th := rs_theta(11.7722)
t := exp(cx(0, th))
for k in ["3_1", "4_1", "5_1"] {
  print(k, ":", jones_poly(k), " |  V(t*) =", jones(k, t))
}
print("x log x = 1 の根 =", xlogx_root())
print("ラピディティ arcosh(64800) =", acosh(64800))`,
    "struct とクロージャ": `struct Vec { x, y }
fn Vec.norm(self) { return sqrt(self.x^2 + self.y^2) }
counter := fn() { n := 0; return || { n = n + 1; return n } }
c := counter()
c(); c()
print("norm =", Vec(3, 4).norm(), " counter =", c())
print(map([1, 2, 3, 4], |k| k * k))`
  };
  const ex = $("ex");
  Object.keys(EXAMPLES).forEach(k => { const o = document.createElement("option"); o.textContent = k; ex.appendChild(o); });
  ex.onchange = () => { $("code").value = EXAMPLES[ex.value]; $("out").textContent = ""; };
  $("code").value = EXAMPLES[ex.value = Object.keys(EXAMPLES)[0]];
  function runEditor() {
    const t0 = performance.now();
    const r = callBrain("eval_bada", [$("code").value]);
    const lines = r.out.slice();
    if (r.ok) lines.push("⇒ " + r.shown); else lines.push("⚠ " + r.error);
    $("out").textContent = lines.join("\n");
    $("runinfo").textContent = `${(performance.now() - t0).toFixed(1)} ms` + (r.ok ? ` · 台帳 ${r.ledger} 件` : "");
  }
  $("runbtn").onclick = runEditor;
  $("code").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); runEditor(); }
    if (e.key === "Tab") { e.preventDefault(); const t = e.target, s = t.selectionStart; t.setRangeText("  ", s, t.selectionEnd, "end"); }
  });

  /* ── 方程式レジストリ ── */
  const TAGS = {};
  KB.equations.forEach(q => q.tags.forEach(t => TAGS[t] = (TAGS[t] || 0) + 1));
  Object.keys(TAGS).sort().forEach(t => { const o = document.createElement("option"); o.value = t; o.textContent = `${t} (${TAGS[t]})`; $("eqtag").appendChild(o); });
  const STJ = { symb: "記号式", calc: "数値評価", holds: "成立", differs: "不成立" };
  function renderEqs() {
    const q = $("eqq").value.trim().toLowerCase(), st = $("eqst").value, tg = $("eqtag").value;
    const res = KB.equations.filter(e => (!st || e.status === st) && (!tg || e.tags.includes(tg)) && (!q || (e.id + " " + e.eq + " " + e.tags.join(" ")).toLowerCase().includes(q)));
    $("eqsub").textContent = `contact_blueprint.pdf の全方程式 ${KB.equations.length} 本 — 表示 ${Math.min(res.length, 300)} / 該当 ${res.length}`;
    $("eqlist").innerHTML = res.slice(0, 300).map(e => `<div class="eq"><span class="id">${esc(e.id)}</span><code>${esc(e.eq)}</code>${e.value ? ` <span style="color:var(--muted)">= ${esc(e.value)}</span>` : ""}<span class="st ${e.status}">${STJ[e.status]}</span> <span style="color:var(--muted);font-size:12px">${esc(e.tags.join(", "))}</span></div>`).join("");
  }
  let eqT; ["eqq", "eqst", "eqtag"].forEach(id => $(id).addEventListener("input", () => { clearTimeout(eqT); eqT = setTimeout(renderEqs, 120); }));

  /* ── 台帳 / brain ソース ── */
  function renderLedger() {
    const it = brain.Omega.items;
    $("led").innerHTML = it.slice(-400).map((f, i) => `<div>#${it.length - Math.min(it.length, 400) + i} ${esc(BadaEngine.show(f, 1))}</div>`).reverse().join("");
  }
  function highlight(src) {
    return esc(src).split("\n").map(l => {
      const ci = l.indexOf("#");
      let code = ci >= 0 ? l.slice(0, ci) : l, com = ci >= 0 ? `<span class="c">${l.slice(ci)}</span>` : "";
      code = code.replace(/(&quot;.*?&quot;)/g, '<span class="s">$1</span>')
        .replace(/\b(fn|if|elif|else|for|in|while|return|and|or|not|nil|true|false|rule|qubit|struct|break)\b/g, '<span class="k">$1</span>');
      return code + com;
    }).join("\n");
  }
  $("brainsrc").innerHTML = highlight(BRAIN_SRC);

  /* ── 設定 ── */
  function refreshBadge() {
    const api = settings.mode === "llm" && settings.key;
    $("badge").textContent = api ? "Claude API · " + settings.model : "ローカル Bada エンジン";
    $("badge").classList.toggle("api", !!api);
    $("hint").textContent = api ? "Claude API モード: Bada が検索・計算した文脈を添えて Claude に送ります。" : (settings.mode === "llm" ? "API キーが未設定のため、ローカル Bada エンジンで答えます。" : "ローカルモード: 同梱の論文と方程式、Bada の数値核だけで答えます。");
  }
  $("gear").onclick = () => {
    document.querySelectorAll("input[name=mode]").forEach(r => r.checked = r.value === settings.mode);
    $("key").value = settings.key; $("model").value = settings.model; $("effort").value = settings.effort;
    $("dlg").showModal();
  };
  $("dlg").addEventListener("close", () => {
    if ($("dlg").returnValue !== "ok") return;
    const m = document.querySelector("input[name=mode]:checked");
    settings.mode = m ? m.value : "local"; settings.key = $("key").value.trim();
    settings.model = $("model").value; settings.effort = $("effort").value;
    store.set("settings", settings); refreshBadge();
  });
  $("theme").onclick = () => {
    const dark = getComputedStyle(document.body).backgroundColor.match(/\d+/g).slice(0, 3).reduce((a, b) => a + +b, 0) < 300;
    settings.theme = dark ? "light" : "dark"; document.documentElement.dataset.theme = settings.theme; store.set("settings", settings);
  };

  /* ── 入力欄 ── */
  const inp = $("inp");
  const grow = () => { inp.style.height = "auto"; inp.style.height = Math.min(inp.scrollHeight, 220) + "px"; };
  inp.addEventListener("input", grow);
  inp.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); const v = inp.value; inp.value = ""; grow(); send(v); } });
  $("send").onclick = () => { const v = inp.value; inp.value = ""; grow(); send(v); };

  /* ── 起動 ── */
  setTimeout(() => {
    try {
      brain.run(BRAIN_SRC);
      const n = callBrain("brain_boot");
      $("ver").textContent = "brain " + brain.global.get("BRAIN_VERSION") + " · " + n + " 文書";
      $("boot").remove();
    } catch (e) {
      $("bootmsg").textContent = "起動に失敗しました: " + (e && e.message || e);
      return;
    }
    refreshBadge(); newConv(); renderHist(); inp.focus();
  }, 30);
})();
