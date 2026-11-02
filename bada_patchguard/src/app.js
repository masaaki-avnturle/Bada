/*
 * app.js — Bada PatchGuard の画面 (入力・表示・書き出しだけ)
 * 判定はすべて guard.bada (Bada) が core.js 経由で行います。
 */
"use strict";
(function () {
  const $ = id => document.getElementById(id);
  const esc = s => String(s === null || s === undefined ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const store = {
    get(k, d) { try { const v = localStorage.getItem("badapatchguard:" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("badapatchguard:" + k, JSON.stringify(v)); } catch (e) { /* 保存できない環境でも動く */ } },
    del(k) { try { localStorage.removeItem("badapatchguard:" + k); } catch (e) { } }
  };
  const theme = store.get("theme", "");
  if (theme) document.documentElement.dataset.theme = theme;
  $("theme").onclick = () => {
    const dark = matchMedia("(prefers-color-scheme: dark)").matches;
    const cur = document.documentElement.dataset.theme || (dark ? "dark" : "light");
    const nx = cur === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = nx; store.set("theme", nx);
  };

  const DEFAULT_GUARD = $("guard-src").textContent;
  const EXAMPLES = JSON.parse($("examples").textContent);
  let guardSrc = store.get("guard", DEFAULT_GUARD);
  let pg = null;
  function loadCore(src) {
    pg = PatchGuardCore.create({ Engine: BadaEngine, PHP: PHPAnalyzer, Diff: PatchDiff, guardSrc: src });
    return pg;
  }
  try { loadCore(guardSrc); } catch (e) { guardSrc = DEFAULT_GUARD; store.del("guard"); loadCore(guardSrc); }

  /* ── 入力 (基 + 段) ── */
  const trees = [{ name: "書き換えの基", files: {} }, { name: "書き換えた後 (段 1)", files: {} }];
  let waivers = [];
  const TEXT_EXT = /\.(php|phtml|inc|html?|js|css|json|txt|md|xml|svg|ini|htaccess|tpl|twig|yml|yaml|sql|csv)$|(^|\/)\.htaccess$/i;
  function renderInputs() {
    const box = $("inputs"); box.innerHTML = "";
    trees.forEach((t, i) => {
      const d = document.createElement("div"); d.className = "tree";
      const n = Object.keys(t.files).length;
      d.innerHTML = `<h3>${i === 0 ? "🗂" : "✎"} ${esc(t.name)}${i >= 2 ? '<button class="x" title="この段を削除">×</button>' : ""}</h3>
        <div class="count">${n ? n + " ファイル" : "未選択 — ここへドラッグ＆ドロップもできます"}</div>
        <div class="btns">
          <label class="btn">フォルダ<input type="file" webkitdirectory multiple hidden></label>
          <label class="btn">ファイル<input type="file" multiple hidden></label>
          <button class="btn paste">貼り付け</button>
          ${n ? '<button class="btn clear">クリア</button>' : ""}
        </div>
        <div class="files">${Object.keys(t.files).sort().slice(0, 200).map(esc).join("<br>")}</div>`;
      const [dirIn, fileIn] = d.querySelectorAll("input[type=file]");
      dirIn.onchange = () => readFiles(dirIn.files, t, true);
      fileIn.onchange = () => readFiles(fileIn.files, t, false);
      d.querySelector(".paste").onclick = () => pasteInto(t);
      const cl = d.querySelector(".clear"); if (cl) cl.onclick = () => { t.files = {}; renderInputs(); };
      const x = d.querySelector(".x"); if (x) x.onclick = () => { trees.splice(i, 1); relabel(); renderInputs(); };
      d.addEventListener("dragover", e => { e.preventDefault(); d.classList.add("drag"); });
      d.addEventListener("dragleave", () => d.classList.remove("drag"));
      d.addEventListener("drop", e => { e.preventDefault(); d.classList.remove("drag"); dropInto(e.dataTransfer, t); });
      box.appendChild(d);
    });
  }
  function relabel() { trees.forEach((t, i) => { if (i) t.name = `書き換えた後 (段 ${i})`; }); }
  async function readFiles(list, t, isDir) {
    const arr = Array.from(list); let skipped = 0;
    // フォルダ選択では先頭のフォルダ名を取り除き、サイト内の相対パスにする
    for (const f of arr) {
      let p = (f.webkitRelativePath || f.name).replace(/\\/g, "/");
      if (isDir && p.includes("/")) p = p.slice(p.indexOf("/") + 1);
      if (/(^|\/)(\.git|node_modules|\.patchguard)\//.test(p) || !TEXT_EXT.test(p) || f.size > 4 * 1024 * 1024) { skipped++; continue; }
      t.files[p] = await f.text();
    }
    status(`${Object.keys(t.files).length} ファイルを読み込みました` + (skipped ? ` (対象外 ${skipped} 件をスキップ)` : ""));
    renderInputs();
  }
  async function dropInto(dt, t) {
    const items = Array.from(dt.items || []).map(i => i.webkitGetAsEntry && i.webkitGetAsEntry()).filter(Boolean);
    if (!items.length) return readFiles(dt.files, t, false);
    const files = [];
    const walk = (entry, pre) => new Promise(res => {
      if (entry.isFile) entry.file(f => { files.push([pre + f.name, f]); res(); }, () => res());
      else if (entry.isDirectory) {
        const r = entry.createReader(); const all = [];
        const more = () => r.readEntries(async es => { if (!es.length) { for (const e of all) await walk(e, pre + entry.name + "/"); res(); } else { all.push(...es); more(); } }, () => res());
        more();
      } else res();
    });
    for (const it of items) await walk(it, "");
    const strip = items.length === 1 && items[0].isDirectory;
    for (const [p0, f] of files) {
      const p = strip ? p0.slice(p0.indexOf("/") + 1) : p0;
      if (TEXT_EXT.test(p) && !/(^|\/)(\.git|node_modules|\.patchguard)\//.test(p)) t.files[p] = await f.text();
    }
    renderInputs();
  }
  function pasteInto(t) {
    $("pastepath").value = ""; $("pastetext").value = "";
    const dlg = $("pastedlg"); dlg.showModal();
    dlg.onclose = () => {
      if (dlg.returnValue !== "ok") return;
      const p = $("pastepath").value.trim().replace(/^\/+/, "");
      if (!p) return;
      t.files[p] = $("pastetext").value; renderInputs();
    };
  }
  $("addrev").onclick = () => { trees.push({ name: "", files: {} }); relabel(); renderInputs(); };
  document.querySelectorAll("[data-ex]").forEach(b => b.onclick = () => {
    const ex = EXAMPLES[b.dataset.ex];
    trees.length = 0;
    trees.push({ name: "書き換えの基", files: Object.assign({}, EXAMPLES.base) });
    ex.forEach(r => trees.push({ name: "", files: Object.assign({}, r) }));
    relabel(); renderInputs(); waivers = []; run();
  });
  const status = (s, err) => { $("status").innerHTML = err ? `<span class="err">${esc(s)}</span>` : esc(s); };

  /* ── 検査 ── */
  let rep = null;
  function run() {
    if (!Object.keys(trees[0].files).length && trees.slice(1).every(t => !Object.keys(t.files).length)) { status("基と後のファイルを入れてください", true); return; }
    const t0 = performance.now();
    try {
      rep = pg.revise(trees[0].files, trees.slice(1).map(t => t.files), waivers);
    } catch (e) { status("検査に失敗しました: " + (e && e.message || e), true); return; }
    status(`検査 ${(performance.now() - t0).toFixed(0)} ms — 変更 ${rep.net.files.length} ファイル、タプル ${rep.tuples} 件`);
    $("result").hidden = false;
    renderSummary(); renderFiles(); renderTuples(); renderExport();
  }
  $("run").onclick = () => { waivers = []; run(); };

  /* ── 概要 ── */
  const SEVJ = { critical: "致命的", high: "高", medium: "中", low: "低", info: "情報" };
  const DECJ = { ACCEPT: "ACCEPT — 受理", REVIEW: "REVIEW — 要確認", REJECT: "REJECT — 拒否" };
  const sevTag = s => `<span class="sev ${s}">${SEVJ[s] || s}</span>`;
  function renderSummary() {
    const n = rep.net, adds = n.files.reduce((s, f) => s + f.adds, 0), dels = n.files.reduce((s, f) => s + f.dels, 0);
    const cnt = ["critical", "high", "medium", "low", "info"].filter(k => rep.counts[k]).map(k => `<span class="stat">${sevTag(k)} ${rep.counts[k]}</span>`).join("");
    const heldN = Object.keys(rep.held).length;
    let h = `<div class="verdict"><span class="dec ${rep.decision}">${DECJ[rep.decision]}</span>
      <div class="stats"><span class="stat">変更 ${n.files.length} ファイル (+${adds} / −${dels})</span>${cnt || '<span class="stat">指摘なし</span>'}
      <span class="stat">安全パッチ ${n.files.length - heldN} / 保留 ${heldN}</span><span class="stat">タプル ${rep.tuples}</span></div></div>`;
    h += `<p class="sub" style="margin-top:12px">判定は折り畳んだ正味の変更 (書き換えの基 → 最終版) に対して行います。高以上が 1 つでもあれば REJECT、中があれば REVIEW です。免除した指摘は数えません。</p>`;
    if (rep.steps.length) {
      h += `<h2>折り畳み</h2><p>${rep.steps.length} 段のパッチ → 正味 1 本。 ${rep.fold.ok ? '<b style="color:var(--ok)">✓ 各段のパッチを基へ順に当てると最終版と一致</b>' : '<b class="err">✗ ' + esc(rep.fold.problems.join("; ")) + "</b>"}</p>
        <table class="grid"><tr><th>段</th><th>変更ファイル</th><th>指摘</th></tr>` +
        rep.steps.map(s => `<tr><td>${s.step}</td><td class="mono">${s.files.map(f => esc(f.path)).join(", ")}</td><td>${s.findings.length ? s.findings.map(f => sevTag(f.sev) + " " + esc(f.id)).join(" ") : "—"}</td></tr>`).join("") + "</table>";
      if (rep.cancelled.length) h += `<h3 style="font-size:14px">相殺された指摘 (途中の段にだけ現れ、最終版では消えた)</h3>` + rep.cancelled.map(f => `<div class="find ${f.sev}">${sevTag(f.sev)} 段 ${f.step} · ${esc(f.id)} ${esc(f.path)}:${f.line} — ${esc(f.msg)}</div>`).join("");
      if (rep.emergent.length) h += `<h3 style="font-size:14px">合成で初めて現れた指摘 (どの段単独でも出ない)</h3>` + rep.emergent.map(f => `<div class="find ${f.sev}">${sevTag(f.sev)} ${esc(f.id)} ${esc(f.path)}:${f.line} — ${esc(f.msg)}</div>`).join("");
    }
    if (heldN) h += `<h2 style="margin-top:14px">保留したファイル</h2><table class="grid">` + Object.keys(rep.held).map(p => `<tr><td class="mono">${esc(p)}</td><td>${esc(rep.held[p])}</td></tr>`).join("") + "</table>";
    if (waivers.length) h += `<h2 style="margin-top:14px">免除</h2><table class="grid">` + waivers.map(w => `<tr><td>${esc(w.id)}</td><td class="mono">${esc(w.path)}</td><td>${esc(w.reason)}</td></tr>`).join("") + "</table>";
    $("t-sum").innerHTML = h;
  }

  /* ── ファイルとパッチ (折り畳み表示) ── */
  function textOf(sha) { return sha ? (pg.blob(sha) || "") : ""; }
  function diffHtml(fl) {
    const base = textOf(fl.sha_a).split("\n"); const marks = new Set(fl.findings.map(f => f.line));
    let rows = "", aPos = 1;
    const foldRow = (from, to) => {
      const n = to - from + 1; if (n <= 0) return "";
      return `<tr class="fold" data-a="${from}" data-b="${to}"><td class="n"></td><td class="n"></td><td class="t">⋯ 変更のない ${n} 行を折り畳み中 (クリックで展開)</td></tr>`;
    };
    fl.hunks.forEach(h => {
      const hs = h.a_len === 0 ? h.a_start + 1 : h.a_start;
      rows += foldRow(aPos, hs - 1);
      rows += `<tr class="h"><td class="n"></td><td class="n"></td><td class="t">${esc(PatchDiff.hunkHeader(h))}</td></tr>`;
      let a = h.a_len === 0 ? h.a_start + 1 : h.a_start, b = h.b_len === 0 ? h.b_start + 1 : h.b_start;
      for (const [op, line0] of h.lines) {
        const line = line0.replace(PatchDiff.NOEOL, "");
        if (op === " ") { rows += `<tr><td class="n">${a}</td><td class="n">${b}</td><td class="t"> ${esc(line)}</td></tr>`; a++; b++; }
        else if (op === "-") { rows += `<tr class="d"><td class="n">${a}</td><td class="n"></td><td class="t">-${esc(line)}</td></tr>`; a++; }
        else { rows += `<tr class="a${marks.has(b) ? " mark" : ""}"><td class="n"></td><td class="n">${b}</td><td class="t">+${esc(line)}</td></tr>`; b++; }
      }
      aPos = a;
    });
    if (fl.sha_a) rows += foldRow(aPos, fl.a_lines);
    return { html: `<div class="diff"><table>${rows}</table></div>`, base };
  }
  function renderFiles() {
    const box = $("t-files"); box.innerHTML = "";
    if (!rep.net.files.length) { box.innerHTML = '<div class="empty">基と後に違いはありません</div>'; return; }
    for (const fl of rep.net.files) {
      const det = document.createElement("details"); det.className = "fl";
      const worst = fl.findings.filter(f => !f.waived).reduce((m, f) => pg.sevRank(f.sev) > pg.sevRank(m) ? f.sev : m, "none");
      det.open = worst !== "none" && pg.sevRank(worst) >= 2;
      const held = rep.held[fl.path];
      det.innerHTML = `<summary><span class="p">${esc(fl.path)}</span><span class="tag">${{ modified: "変更", added: "新規", deleted: "削除" }[fl.status]}</span>
        <span class="tag">+${fl.adds} −${fl.dels}</span>${worst !== "none" ? sevTag(worst) : ""}
        <span class="tag ${held ? "held" : "safe"}">${held ? "⏸ 保留: " + esc(held) : "✓ 安全パッチに含める"}</span></summary>`;
      if (fl.findings.length) {
        const fd = document.createElement("div"); fd.className = "finds";
        fl.findings.forEach(f => {
          const d = document.createElement("div"); d.className = `find ${f.sev}${f.waived ? " waived" : ""}`;
          d.innerHTML = `${sevTag(f.sev)} <b>${esc(f.id)}</b> ${esc(f.title)}${f.line ? ` <span class="msg">line ${f.line}</span>` : ""}
            ${f.waived ? `<span class="msg"> — 免除: ${esc(f.waived)}</span>` : '<button class="wv">免除…</button>'}
            <div>${esc(f.msg)}</div><div class="ev">${esc(f.evidence)}</div>`;
          const wb = d.querySelector(".wv"); if (wb) wb.onclick = () => askWaive(f);
          fd.appendChild(d);
        });
        det.appendChild(fd);
      }
      const { html, base } = diffHtml(fl);
      const wrap = document.createElement("div"); wrap.innerHTML = html; det.appendChild(wrap);
      wrap.addEventListener("click", e => {
        const tr = e.target.closest("tr.fold"); if (!tr) return;
        const from = +tr.dataset.a, to = +tr.dataset.b; let out = "";
        // 変更のない行は基と後で同じ。後の行番号は直前の行から数える
        const prev = tr.previousElementSibling; let bno = prev ? parseInt(prev.children[1].textContent, 10) || null : null;
        if (bno === null) bno = from; else bno++;
        for (let k = from; k <= to; k++) out += `<tr><td class="n">${k}</td><td class="n">${bno++}</td><td class="t"> ${esc(base[k - 1] || "")}</td></tr>`;
        tr.insertAdjacentHTML("afterend", out); tr.remove();
      });
      box.appendChild(det);
    }
  }
  function askWaive(f) {
    $("waiveinfo").textContent = `${f.id} ${f.path}:${f.line} — ${f.msg}`;
    $("waivereason").value = "";
    const dlg = $("waivedlg"); dlg.showModal();
    dlg.onclose = () => {
      if (dlg.returnValue !== "ok") return;
      const reason = $("waivereason").value.trim();
      if (!reason) { status("免除には理由が必要です", true); return; }
      waivers.push({ id: f.id, path: f.path, match: f.evidence, reason });
      run();
    };
  }

  /* ── タプル空間 ── */
  function renderTuples() {
    const q = $("tq").value.trim(); let pat = null, kind = null;
    if (q.startsWith("[")) {
      try { pat = JSON.parse(q.replace(/(^|[\[,]\s*)\*(?=\s*[,\]])/g, '$1"__STAR__"')); } catch (e) { $("tcount").textContent = "照会の形式: [\"patch\", *, *, \"index.php\"]"; return; }
    } else if (q) kind = q;
    const all = pg.tuples();
    const hit = all.filter(t => {
      if (kind) return String(t[0]).includes(kind);
      if (!pat) return true;
      return pat.length === t.length && pat.every((x, i) => x === "__STAR__" || x === t[i] || String(x) === String(t[i]));
    });
    $("tcount").textContent = `${hit.length} / ${all.length} 件 (追記のみ・凍結)`;
    $("ttable").innerHTML = "<tr><th>#</th><th>タプル</th></tr>" + hit.slice(-500).map(t => `<tr><td>${all.indexOf(t)}</td><td class="mono">${esc(JSON.stringify(t))}</td></tr>`).join("");
  }
  $("tq").addEventListener("input", renderTuples);

  /* ── 規則 ── */
  $("rulesrc").value = guardSrc;
  $("reload").onclick = () => {
    const src = $("rulesrc").value;
    try { loadCore(src); guardSrc = src; store.set("guard", src); $("rulemsg").textContent = `読み込みました: invariant ${pg.rules().checks.length} 件、sink ${Object.keys(pg.rules().sinks).length} 件`; if (rep) run(); }
    catch (e) { $("rulemsg").innerHTML = `<span class="err">${esc(e && e.message || e)}</span>`; loadCore(guardSrc); }
  };
  $("resetrules").onclick = () => { $("rulesrc").value = DEFAULT_GUARD; store.del("guard"); guardSrc = DEFAULT_GUARD; loadCore(guardSrc); $("rulemsg").textContent = "既定の規則に戻しました"; if (rep) run(); };

  /* ── 書き出し ── */
  function renderExport() {
    const outs = [
      ["net.patch", "正味パッチ (基 → 最終版)", () => pg.patchText(rep, false), "text/x-diff"],
      ["safe.patch", "安全な部分パッチ (保留を除く)", () => pg.patchText(rep, true), "text/x-diff"],
      ["rollback.patch", "ロールバック (最終版 → 基)", () => pg.rollbackText(rep), "text/x-diff"],
      ["report.json", "検査結果 (JSON)", () => JSON.stringify(slim(rep), null, 2), "application/json"],
      ["tuples.jsonl", "タプル空間 (JSON Lines)", () => pg.tuples().map(t => JSON.stringify(t)).join("\n") + "\n", "application/x-ndjson"]
    ];
    const box = $("exbtns"); box.innerHTML = "";
    outs.forEach(([name, label, make, type]) => {
      const b = document.createElement("button"); b.className = "btn"; b.textContent = "⬇ " + label;
      b.onclick = () => { const s = make(); $("expreview").textContent = s.slice(0, 20000) || "(空 — 該当するファイルがありません)"; download(name, s, type); };
      const cp = document.createElement("button"); cp.className = "btn"; cp.textContent = "⧉"; cp.title = name + " をコピー";
      cp.onclick = () => { const s = make(); $("expreview").textContent = s.slice(0, 20000); try { navigator.clipboard.writeText(s); status(name + " をコピーしました"); } catch (e) { status("コピーできませんでした", true); } };
      box.append(b, cp);
    });
    $("expreview").textContent = pg.patchText(rep, false).slice(0, 20000) || "(変更なし)";
  }
  function download(name, text, type) {
    try {
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name;
      document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
      status(name + " を保存しました (保存できない端末では ⧉ でコピーしてください)");
    } catch (e) { status("保存できませんでした。⧉ でコピーしてください", true); }
  }
  function slim(r) {
    return {
      run: r.run, version: r.version, decision: r.decision, counts: r.counts, held: r.held, fold: r.fold, waivers,
      files: r.net.files.map(f => ({ path: f.path, status: f.status, sha_base: f.sha_a, sha_after: f.sha_b, adds: f.adds, dels: f.dels, findings: f.findings })),
      steps: r.steps.map(s => ({ step: s.step, files: s.files.map(f => f.path), findings: s.findings })), cancelled: r.cancelled, emergent: r.emergent
    };
  }

  /* ── タブ ── */
  $("tabs").onclick = e => {
    const b = e.target.closest("button"); if (!b) return;
    document.querySelectorAll("#tabs button").forEach(x => x.classList.toggle("on", x === b));
    document.querySelectorAll(".tab").forEach(x => x.classList.toggle("on", x.id === "t-" + b.dataset.t));
  };

  renderInputs();
  status(`規則: invariant ${pg.rules().checks.length} 件 / sink ${Object.keys(pg.rules().sinks).length} 件 / sanitizer ${pg.rules().sanitizers.length} 件 — @reviser 文法: ${pg.rules().grammar.join(", ")}`);
})();
