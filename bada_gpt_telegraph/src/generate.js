/*
 * generate.js — BadaGPT電信の「生成」と「検証」
 *
 * 仕様 (spec) のモジュールを組み合わせ、依存ゼロ・オフライン動作の
 * 自己完結 HTML アプリを 1 ファイルで組み立てる。
 *
 * 生成アプリの実行時コードは、このファイル内に本物の JS 関数として書き
 * (= このファイル自体の構文検査・テストの対象になる)、
 * Function.prototype.toString で文字列化して埋め込む。
 * そのため各関数は外側の変数を参照せず、引数 (設定 C) と
 * RT_core が window に置く共通部品だけを使う。
 */
"use strict";

/* ═════════════ 生成アプリの共通ランタイム ═════════════ */
function RT_core(APP) {
  window.APP = APP;
  window.$ = function (s, r) { return (r || document).querySelector(s); };
  window.$$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  window.esc = function (s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  };
  window.uid = function () { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); };
  window.Store = {
    get: function (k, d) { try { var v = localStorage.getItem(APP.key + ":" + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(APP.key + ":" + k, JSON.stringify(v)); } catch (e) { /* 保存不可の環境でも動作は続ける */ } }
  };
  window.fmtNum = function (n) { return Number(n || 0).toLocaleString("ja-JP"); };
  window.today = function () { var d = new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); };
  window.toast = function (msg) {
    var t = document.getElementById("toast");
    t.textContent = msg; t.className = "show";
    clearTimeout(window.__toastT); window.__toastT = setTimeout(function () { t.className = ""; }, 1800);
  };
  /* ファイル保存: Android (Cordova) は端末へ、ブラウザ / Electron はダウンロード */
  window.saveFile = function (name, text, mime) {
    var blob = new Blob([text], { type: mime || "text/plain" });
    if (window.cordova && window.resolveLocalFileSystemURL && window.cordova.file) {
      var dir = window.cordova.file.externalDataDirectory || window.cordova.file.dataDirectory;
      window.resolveLocalFileSystemURL(dir, function (d) {
        d.getFile(name, { create: true }, function (fe) {
          fe.createWriter(function (w) { w.onwriteend = function () { toast("保存しました: " + name); }; w.write(blob); });
        });
      });
      return;
    }
    var a = document.createElement("a"), url = URL.createObjectURL(blob);
    a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    toast("保存しました: " + name);
  };
  window.toCSV = function (rows, cols) {
    function q(v) { v = v == null ? "" : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
    return "﻿" + [cols.map(function (c) { return q(c.name); }).join(",")]
      .concat(rows.map(function (r) { return cols.map(function (c) { return q(r[c.key]); }).join(","); })).join("\n");
  };
  window.pickJSON = function (cb) {
    var inp = document.createElement("input"); inp.type = "file"; inp.accept = ".json,application/json";
    inp.onchange = function () {
      var f = inp.files[0]; if (!f) return;
      var r = new FileReader();
      r.onload = function () { try { cb(JSON.parse(r.result)); toast("読み込みました"); } catch (e) { toast("JSON を読めません"); } };
      r.readAsText(f);
    };
    inp.click();
  };
  var AC = null;
  window.beep = function (freq, dur) {
    try {
      AC = AC || new (window.AudioContext || window.webkitAudioContext)();
      if (AC.state === "suspended") AC.resume();
      var o = AC.createOscillator(), g = AC.createGain(), t0 = AC.currentTime;
      o.frequency.value = freq || 880; o.connect(g); g.connect(AC.destination);
      g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.2, t0 + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + (dur || 0.2));
      o.start(t0); o.stop(t0 + (dur || 0.2) + 0.05);
    } catch (e) { /* 音が出せない環境 */ }
  };
  /* 棒グラフ (canvas) */
  window.barChart = function (cv, labels, values, color) {
    var dpr = window.devicePixelRatio || 1, W = cv.clientWidth || 300, H = cv.clientHeight || 160;
    cv.width = W * dpr; cv.height = H * dpr;
    var x = cv.getContext("2d"); x.setTransform(dpr, 0, 0, dpr, 0, 0); x.clearRect(0, 0, W, H);
    var st = getComputedStyle(document.body), fg = st.getPropertyValue("--muted") || "#888";
    if (!values.length) { x.fillStyle = fg; x.font = "12px sans-serif"; x.fillText("データがありません", 10, 20); return; }
    var max = Math.max.apply(null, values.map(function (v) { return Math.abs(v); }).concat([1]));
    var n = values.length, bw = Math.max(4, (W - 20) / n - 6);
    values.forEach(function (v, i) {
      var h = (H - 34) * Math.abs(v) / max, px = 10 + i * (bw + 6);
      x.fillStyle = color || st.getPropertyValue("--acc"); x.fillRect(px, H - 20 - h, bw, h);
      x.fillStyle = fg; x.font = "10px sans-serif";
      x.fillText(String(labels[i]).slice(0, 6), px, H - 6);
      x.fillText(fmtNum(Math.round(v * 100) / 100), px, H - 24 - h);
    });
  };
  window.APP_start = function () {
    var tabs = $$(".tabs button");
    function show(id) {
      tabs.forEach(function (b) { b.classList.toggle("on", b.getAttribute("data-tab") === id); });
      $$("main > section").forEach(function (s) { s.hidden = s.id !== "p-" + id; });
      Store.set("tab", id);
      window.dispatchEvent(new CustomEvent("tabshow", { detail: id }));
    }
    tabs.forEach(function (b) { b.onclick = function () { show(b.getAttribute("data-tab")); }; });
    var first = $("main > section"), saved = Store.get("tab", "");
    if (first) show(document.getElementById("p-" + saved) ? saved : first.id.slice(2));
    var mode = Store.get("theme", APP.theme);
    document.body.setAttribute("data-theme", mode);
    $("#themeBtn").onclick = function () {
      mode = mode === "dark" ? "light" : "dark"; document.body.setAttribute("data-theme", mode); Store.set("theme", mode);
    };
    var pb = $("#printBtn"); if (pb) pb.onclick = function () { window.print(); };
    $("#aboutBtn").onclick = function () { $("#about").hidden = false; };
    $("#aboutClose").onclick = function () { $("#about").hidden = true; };
  };
}

/* ═════════════ モジュール: 記録・管理 (CRUD) ═════════════ */
function MOD_records(C) {
  var root = document.getElementById("p-records"), F = C.fields, items = Store.get("records", []), editing = null;
  function input(f) {
    var id = "rf-" + f.key;
    if (f.type === "text") return '<textarea id="' + id + '" rows="2"></textarea>';
    if (f.type === "bool") return '<input id="' + id + '" type="checkbox">';
    if (f.type === "rating") return '<select id="' + id + '"><option value="">—</option>' + [1, 2, 3, 4, 5].map(function (n) { return '<option value="' + n + '">' + "★★★★★".slice(0, n) + "</option>"; }).join("") + "</select>";
    return '<input id="' + id + '" type="' + (f.type === "number" ? "number" : f.type === "date" ? "date" : "text") + '"' + (f.type === "number" ? ' step="any"' : "") + ">";
  }
  var numF = F.filter(function (f) { return f.type === "number" || f.type === "rating"; })[0];
  root.innerHTML =
    '<div class="card"><h2>' + esc(C.entity) + ' を登録</h2><div class="form">' +
    F.map(function (f) { return '<label class="' + (f.type === "text" ? "wide" : "") + '"><span>' + esc(f.name) + "</span>" + input(f) + "</label>"; }).join("") +
    '</div><div class="row"><button class="pri" id="r-save">保存</button><button id="r-clear">クリア</button></div></div>' +
    '<div class="card"><div class="row bar">' +
    (C.features.search ? '<input id="r-q" type="search" placeholder="🔍 検索">' : "") +
    (C.features.sort ? '<select id="r-sort"><option value="">新しい順</option>' + F.map(function (f) { return '<option value="' + f.key + ':1">' + esc(f.name) + ' ↑</option><option value="' + f.key + ':-1">' + esc(f.name) + " ↓</option>"; }).join("") + "</select>" : "") +
    (C.features.export ? '<button id="r-csv">CSV</button><button id="r-json">バックアップ</button><button id="r-imp">復元</button>' : "") +
    '</div><div id="r-count" class="muted"></div><div id="r-list" class="list"></div></div>' +
    (C.features.chart && numF ? '<div class="card"><h2>📊 ' + esc(numF.name) + ' のグラフ (直近 20 件)</h2><canvas id="r-chart" class="chart"></canvas></div>' : "");
  function val(f) { var e = document.getElementById("rf-" + f.key); return f.type === "bool" ? e.checked : e.value; }
  function setVal(f, v) { var e = document.getElementById("rf-" + f.key); if (f.type === "bool") e.checked = !!v; else e.value = v == null ? "" : v; }
  function show(f, v) {
    if (f.type === "bool") return v ? "✔" : "—";
    if (f.type === "rating") return v ? "★★★★★".slice(0, +v) : "—";
    if (f.type === "number") return v === "" || v == null ? "—" : fmtNum(v);
    return esc(v || "—");
  }
  function render() {
    var q = C.features.search ? $("#r-q").value.trim().toLowerCase() : "";
    var rows = items.filter(function (it) { return !q || F.some(function (f) { return String(it[f.key] || "").toLowerCase().indexOf(q) >= 0; }); });
    var so = C.features.sort ? $("#r-sort").value : "";
    if (so) {
      var k = so.split(":")[0], dir = +so.split(":")[1];
      var ft = F.filter(function (f) { return f.key === k; })[0].type;
      rows = rows.slice().sort(function (a, b) {
        var x = a[k], y = b[k];
        if (ft === "number" || ft === "rating") { x = +x || 0; y = +y || 0; return (x - y) * dir; }
        return String(x || "").localeCompare(String(y || ""), "ja") * dir;
      });
    } else rows = rows.slice().reverse();
    $("#r-count").textContent = rows.length + " / " + items.length + " 件";
    $("#r-list").innerHTML = rows.map(function (it) {
      return '<div class="item" data-id="' + it.id + '"><div class="grow">' +
        F.map(function (f, i) { return i === 0 ? "<b>" + show(f, it[f.key]) + "</b>" : '<span class="kv"><i>' + esc(f.name) + "</i>" + show(f, it[f.key]) + "</span>"; }).join(" ") +
        '</div><button data-act="edit">編集</button><button data-act="del" class="danger">削除</button></div>';
    }).join("") || '<p class="muted">まだ登録がありません。</p>';
    var cv = document.getElementById("r-chart");
    if (cv) {
      var last = items.slice(-20);
      barChart(cv, last.map(function (it) { return it[F[0].key] || "?"; }), last.map(function (it) { return +it[numF.key] || 0; }));
    }
  }
  function clear() { editing = null; F.forEach(function (f) { setVal(f, f.type === "date" ? today() : ""); }); $("#r-save").textContent = "保存"; }
  $("#r-save").onclick = function () {
    var rec = { id: editing || uid() };
    F.forEach(function (f) { rec[f.key] = val(f); });
    if (!F.some(function (f) { return rec[f.key] !== "" && rec[f.key] !== false; })) { toast("内容を入力してください"); return; }
    if (editing) items = items.map(function (it) { return it.id === editing ? rec : it; }); else items.push(rec);
    Store.set("records", items); clear(); render(); toast("保存しました");
  };
  $("#r-clear").onclick = clear;
  $("#r-list").onclick = function (e) {
    var b = e.target.closest("button"); if (!b) return;
    var id = b.closest(".item").getAttribute("data-id"), it = items.filter(function (x) { return x.id === id; })[0];
    if (b.getAttribute("data-act") === "del") { if (confirm("削除しますか？")) { items = items.filter(function (x) { return x.id !== id; }); Store.set("records", items); render(); } }
    else { editing = id; F.forEach(function (f) { setVal(f, it[f.key]); }); $("#r-save").textContent = "更新"; window.scrollTo(0, 0); }
  };
  if (C.features.search) $("#r-q").oninput = render;
  if (C.features.sort) $("#r-sort").onchange = render;
  if (C.features.export) {
    $("#r-csv").onclick = function () { saveFile(C.slug + "-records.csv", toCSV(items, F), "text/csv"); };
    $("#r-json").onclick = function () { saveFile(C.slug + "-backup.json", JSON.stringify(items, null, 2), "application/json"); };
    $("#r-imp").onclick = function () { pickJSON(function (d) { if (Array.isArray(d)) { items = d; Store.set("records", items); render(); } }); };
  }
  window.addEventListener("tabshow", function (e) { if (e.detail === "records") render(); });
  clear(); render();
}

/* ═════════════ モジュール: ToDo ═════════════ */
function MOD_todo(C) {
  var root = document.getElementById("p-todo"), tasks = Store.get("todo", []), filter = "all";
  root.innerHTML = '<div class="card"><h2>✅ ToDo</h2><div class="row">' +
    '<input id="t-text" placeholder="やること" class="grow"><input id="t-due" type="date"><select id="t-pri"><option value="2">中</option><option value="3">高</option><option value="1">低</option></select>' +
    '<button class="pri" id="t-add">追加</button></div>' +
    '<div class="progress"><div id="t-prog"></div></div><div class="row bar">' +
    '<button data-f="all" class="on">すべて</button><button data-f="open">未完了</button><button data-f="done">完了</button>' +
    (C.features.search ? '<input id="t-q" type="search" placeholder="🔍 検索">' : "") +
    (C.features.export ? '<button id="t-csv">CSV</button>' : "") +
    '</div><div id="t-list" class="list"></div></div>';
  function render() {
    var q = C.features.search ? $("#t-q").value.trim().toLowerCase() : "";
    var rows = tasks.filter(function (t) { return (filter === "all" || (filter === "done") === !!t.done) && (!q || t.text.toLowerCase().indexOf(q) >= 0); })
      .sort(function (a, b) { return (a.done - b.done) || (b.pri - a.pri) || String(a.due || "9").localeCompare(String(b.due || "9")); });
    var done = tasks.filter(function (t) { return t.done; }).length;
    $("#t-prog").style.width = (tasks.length ? done / tasks.length * 100 : 0) + "%";
    $("#t-list").innerHTML = rows.map(function (t) {
      var late = t.due && !t.done && t.due < today();
      return '<div class="item' + (t.done ? " done" : "") + '" data-id="' + t.id + '"><input type="checkbox"' + (t.done ? " checked" : "") + '>' +
        '<div class="grow">' + esc(t.text) + ' <span class="pill p' + t.pri + '">' + ["", "低", "中", "高"][t.pri] + "</span>" +
        (t.due ? ' <span class="kv' + (late ? " late" : "") + '"><i>期限</i>' + esc(t.due) + "</span>" : "") +
        '</div><button class="danger">削除</button></div>';
    }).join("") || '<p class="muted">タスクはありません。</p>';
  }
  function save() { Store.set("todo", tasks); render(); }
  $("#t-add").onclick = function () {
    var v = $("#t-text").value.trim(); if (!v) return;
    tasks.push({ id: uid(), text: v, due: $("#t-due").value, pri: +$("#t-pri").value, done: false });
    $("#t-text").value = ""; save();
  };
  $("#t-text").onkeydown = function (e) { if (e.key === "Enter") $("#t-add").click(); };
  $("#t-list").onclick = function (e) {
    var it = e.target.closest(".item"); if (!it) return;
    var id = it.getAttribute("data-id");
    if (e.target.tagName === "BUTTON") tasks = tasks.filter(function (t) { return t.id !== id; });
    else if (e.target.type === "checkbox") tasks.forEach(function (t) { if (t.id === id) { t.done = e.target.checked; if (t.done && C.features.sound) beep(1320, 0.15); } });
    save();
  };
  $$("[data-f]", root).forEach(function (b) { b.onclick = function () { filter = b.getAttribute("data-f"); $$("[data-f]", root).forEach(function (x) { x.classList.toggle("on", x === b); }); render(); }; });
  if (C.features.search) $("#t-q").oninput = render;
  if (C.features.export) $("#t-csv").onclick = function () {
    saveFile(C.slug + "-todo.csv", toCSV(tasks, [{ key: "text", name: "やること" }, { key: "due", name: "期限" }, { key: "pri", name: "優先度" }, { key: "done", name: "完了" }]), "text/csv");
  };
  render();
}

/* ═════════════ モジュール: メモ ═════════════ */
function MOD_notes(C) {
  var root = document.getElementById("p-notes"), notes = Store.get("notes", []), cur = null;
  root.innerHTML = '<div class="card split"><div class="side"><div class="row"><button class="pri" id="n-new">＋ 新規</button>' +
    (C.features.export ? '<button id="n-exp">書き出し</button>' : "") + '</div>' +
    (C.features.search ? '<input id="n-q" type="search" placeholder="🔍 検索">' : "") +
    '<div id="n-list" class="list"></div></div><div class="main"><input id="n-title" placeholder="タイトル">' +
    '<textarea id="n-body" rows="12" placeholder="本文 (自動保存)"></textarea><div class="row"><span id="n-info" class="muted grow"></span><button id="n-del" class="danger">削除</button></div></div></div>';
  function render() {
    var q = C.features.search ? $("#n-q").value.trim().toLowerCase() : "";
    $("#n-list").innerHTML = notes.filter(function (n) { return !q || (n.title + n.body).toLowerCase().indexOf(q) >= 0; })
      .sort(function (a, b) { return b.t - a.t; })
      .map(function (n) { return '<div class="item' + (n.id === cur ? " on" : "") + '" data-id="' + n.id + '"><div class="grow"><b>' + esc(n.title || "(無題)") + '</b><div class="muted">' + esc(n.body.slice(0, 40)) + "</div></div></div>"; }).join("") ||
      '<p class="muted">メモはありません。</p>';
  }
  function open(id) {
    cur = id; var n = notes.filter(function (x) { return x.id === id; })[0];
    $("#n-title").value = n ? n.title : ""; $("#n-body").value = n ? n.body : "";
    $("#n-info").textContent = n ? new Date(n.t).toLocaleString("ja-JP") : ""; render();
  }
  function persist() {
    if (!cur) { if (!$("#n-title").value && !$("#n-body").value) return; cur = uid(); notes.push({ id: cur, title: "", body: "", t: 0 }); }
    notes.forEach(function (n) { if (n.id === cur) { n.title = $("#n-title").value; n.body = $("#n-body").value; n.t = Date.now(); } });
    Store.set("notes", notes); render();
  }
  $("#n-title").oninput = persist; $("#n-body").oninput = persist;
  $("#n-new").onclick = function () { open(null); $("#n-title").focus(); };
  $("#n-del").onclick = function () { if (cur && confirm("削除しますか？")) { notes = notes.filter(function (n) { return n.id !== cur; }); Store.set("notes", notes); open(null); } };
  $("#n-list").onclick = function (e) { var it = e.target.closest(".item"); if (it) open(it.getAttribute("data-id")); };
  if (C.features.search) $("#n-q").oninput = render;
  if (C.features.export) $("#n-exp").onclick = function () {
    saveFile(C.slug + "-notes.txt", notes.map(function (n) { return "# " + (n.title || "(無題)") + "\n" + n.body; }).join("\n\n---\n\n"), "text/plain");
  };
  render();
}

/* ═════════════ モジュール: 家計簿 ═════════════ */
function MOD_budget(C) {
  var root = document.getElementById("p-budget"), rows = Store.get("budget", []);
  var cats = Store.get("cats", ["食費", "日用品", "交通", "住居", "光熱", "通信", "娯楽", "医療", "給与", "その他"]);
  root.innerHTML = '<div class="card"><h2>💴 家計簿に記入</h2><div class="form">' +
    '<label><span>日付</span><input id="b-date" type="date"></label>' +
    '<label><span>種別</span><select id="b-type"><option value="out">支出</option><option value="in">収入</option></select></label>' +
    '<label><span>分類</span><select id="b-cat"></select></label><label><span>金額 (円)</span><input id="b-amt" type="number" min="0" step="1"></label>' +
    '<label class="wide"><span>メモ</span><input id="b-memo"></label></div><div class="row"><button class="pri" id="b-add">記入</button><button id="b-newcat">分類を追加</button></div></div>' +
    '<div class="card"><div class="row bar"><input id="b-month" type="month">' + (C.features.export ? '<button id="b-csv">CSV</button>' : "") + '</div>' +
    '<div class="stats"><div><i>収入</i><b id="b-in"></b></div><div><i>支出</i><b id="b-out"></b></div><div><i>収支</i><b id="b-bal"></b></div></div>' +
    '<canvas id="b-chart" class="chart"></canvas><div id="b-list" class="list"></div></div>';
  function fillCats() { $("#b-cat").innerHTML = cats.map(function (c) { return "<option>" + esc(c) + "</option>"; }).join(""); }
  function render() {
    var m = $("#b-month").value, cur = rows.filter(function (r) { return !m || r.date.slice(0, 7) === m; });
    var sIn = 0, sOut = 0, byCat = {};
    cur.forEach(function (r) { if (r.type === "in") sIn += r.amt; else { sOut += r.amt; byCat[r.cat] = (byCat[r.cat] || 0) + r.amt; } });
    $("#b-in").textContent = fmtNum(sIn) + " 円"; $("#b-out").textContent = fmtNum(sOut) + " 円";
    $("#b-bal").textContent = fmtNum(sIn - sOut) + " 円"; $("#b-bal").className = sIn - sOut < 0 ? "neg" : "";
    var ks = Object.keys(byCat).sort(function (a, b) { return byCat[b] - byCat[a]; });
    barChart($("#b-chart"), ks, ks.map(function (k) { return byCat[k]; }));
    $("#b-list").innerHTML = cur.slice().sort(function (a, b) { return a.date < b.date ? 1 : -1; }).map(function (r) {
      return '<div class="item" data-id="' + r.id + '"><div class="grow"><b class="' + (r.type === "in" ? "pos" : "neg") + '">' + (r.type === "in" ? "+" : "−") + fmtNum(r.amt) + " 円</b> " +
        '<span class="pill">' + esc(r.cat) + '</span> <span class="kv"><i>' + esc(r.date) + "</i>" + esc(r.memo) + '</span></div><button class="danger">削除</button></div>';
    }).join("") || '<p class="muted">この月の記入はありません。</p>';
  }
  $("#b-add").onclick = function () {
    var amt = Math.round(+$("#b-amt").value); if (!amt) { toast("金額を入力してください"); return; }
    rows.push({ id: uid(), date: $("#b-date").value || today(), type: $("#b-type").value, cat: $("#b-cat").value, amt: amt, memo: $("#b-memo").value });
    Store.set("budget", rows); $("#b-amt").value = ""; $("#b-memo").value = ""; render();
  };
  $("#b-newcat").onclick = function () { var c = prompt("新しい分類名"); if (c) { cats.push(c); Store.set("cats", cats); fillCats(); $("#b-cat").value = c; } };
  $("#b-list").onclick = function (e) {
    if (e.target.tagName !== "BUTTON") return;
    var id = e.target.closest(".item").getAttribute("data-id");
    rows = rows.filter(function (r) { return r.id !== id; }); Store.set("budget", rows); render();
  };
  $("#b-month").onchange = render;
  if (C.features.export) $("#b-csv").onclick = function () {
    saveFile(C.slug + "-budget.csv", toCSV(rows.map(function (r) { return { date: r.date, type: r.type === "in" ? "収入" : "支出", cat: r.cat, amt: r.amt, memo: r.memo }; }),
      [{ key: "date", name: "日付" }, { key: "type", name: "種別" }, { key: "cat", name: "分類" }, { key: "amt", name: "金額" }, { key: "memo", name: "メモ" }]), "text/csv");
  };
  window.addEventListener("tabshow", function (e) { if (e.detail === "budget") render(); });
  fillCats(); $("#b-date").value = today(); $("#b-month").value = today().slice(0, 7); render();
}

/* ═════════════ モジュール: タイマー ═════════════ */
function MOD_timer(C) {
  var root = document.getElementById("p-timer");
  root.innerHTML = '<div class="card center"><h2>⏱ ストップウォッチ</h2><div class="big" id="sw-t">00:00.0</div>' +
    '<div class="row c"><button class="pri" id="sw-go">スタート</button><button id="sw-lap">ラップ</button><button id="sw-rst">リセット</button></div><div id="sw-laps" class="muted"></div></div>' +
    '<div class="card center"><h2>⏳ タイマー</h2><div class="big" id="cd-t">05:00</div>' +
    '<div class="row c"><input id="cd-min" type="number" min="0" value="5" style="width:5em"> 分 <input id="cd-sec" type="number" min="0" max="59" value="0" style="width:5em"> 秒</div>' +
    '<div class="row c"><button data-m="1">1分</button><button data-m="3">3分</button><button data-m="5">5分</button><button data-m="25">25分 🍅</button></div>' +
    '<div class="row c"><button class="pri" id="cd-go">開始</button><button id="cd-rst">リセット</button><label class="inl"><input type="checkbox" id="cd-pomo"> ポモドーロ (25分作業 / 5分休憩)</label></div>' +
    '<div id="cd-state" class="muted"></div></div>';
  function mmss(ms, tenth) {
    var s = Math.max(0, ms) / 1000, m = Math.floor(s / 60), r = s - m * 60;
    return ("0" + m).slice(-2) + ":" + (tenth ? ("0" + r.toFixed(1)).slice(-4) : ("0" + Math.ceil(r - 1e-9) % 60).slice(-2));
  }
  var swStart = 0, swAcc = 0, swRun = false, laps = [];
  function swTick() { if (!swRun) return; $("#sw-t").textContent = mmss(swAcc + Date.now() - swStart, true); requestAnimationFrame(swTick); }
  $("#sw-go").onclick = function () {
    if (swRun) { swAcc += Date.now() - swStart; swRun = false; this.textContent = "スタート"; }
    else { swStart = Date.now(); swRun = true; this.textContent = "ストップ"; swTick(); }
  };
  $("#sw-lap").onclick = function () { if (!swRun) return; laps.unshift(mmss(swAcc + Date.now() - swStart, true)); $("#sw-laps").innerHTML = laps.map(function (l, i) { return "ラップ " + (laps.length - i) + ": " + l; }).join("<br>"); };
  $("#sw-rst").onclick = function () { swRun = false; swAcc = 0; laps = []; $("#sw-t").textContent = "00:00.0"; $("#sw-go").textContent = "スタート"; $("#sw-laps").innerHTML = ""; };
  var cdEnd = 0, cdLeft = 300000, cdRun = false, cdTimer = null, phase = "作業";
  function cdSet() { cdLeft = ((+$("#cd-min").value || 0) * 60 + (+$("#cd-sec").value || 0)) * 1000; $("#cd-t").textContent = mmss(cdLeft); }
  function ring() { for (var i = 0; i < 3; i++) setTimeout(function () { beep(988, 0.25); }, i * 350); }
  function cdTick() {
    var left = cdEnd - Date.now(); $("#cd-t").textContent = mmss(left);
    if (left <= 0) {
      clearInterval(cdTimer); cdRun = false; ring(); $("#cd-go").textContent = "開始";
      if ($("#cd-pomo").checked) {
        phase = phase === "作業" ? "休憩" : "作業";
        $("#cd-min").value = phase === "作業" ? 25 : 5; $("#cd-sec").value = 0; cdSet();
        $("#cd-state").textContent = "次は " + phase + " です。開始を押してください。";
      } else $("#cd-state").textContent = "時間です！";
    }
  }
  $("#cd-go").onclick = function () {
    if (cdRun) { clearInterval(cdTimer); cdLeft = cdEnd - Date.now(); cdRun = false; this.textContent = "再開"; return; }
    cdEnd = Date.now() + cdLeft; cdRun = true; this.textContent = "一時停止"; $("#cd-state").textContent = $("#cd-pomo").checked ? phase + "中" : "";
    cdTimer = setInterval(cdTick, 200);
  };
  $("#cd-rst").onclick = function () { clearInterval(cdTimer); cdRun = false; $("#cd-go").textContent = "開始"; cdSet(); $("#cd-state").textContent = ""; };
  $("#cd-min").oninput = cdSet; $("#cd-sec").oninput = cdSet;
  $$("[data-m]", root).forEach(function (b) { b.onclick = function () { $("#cd-min").value = b.getAttribute("data-m"); $("#cd-sec").value = 0; $("#cd-rst").click(); }; });
  cdSet();
}

/* ═════════════ モジュール: 電卓 (eval を使わない構文解析) ═════════════ */
function MOD_calc(C) {
  var root = document.getElementById("p-calc"), hist = Store.get("calc", []);
  var keys = ["C", "(", ")", "÷", "7", "8", "9", "×", "4", "5", "6", "−", "1", "2", "3", "+", "0", ".", "⌫", "="];
  root.innerHTML = '<div class="card calc"><div class="disp"><div id="c-expr" class="muted"></div><div id="c-out" class="big">0</div></div>' +
    '<div class="keys">' + keys.map(function (k) { return '<button data-k="' + k + '"' + (k === "=" ? ' class="pri"' : "") + ">" + k + "</button>"; }).join("") + "</div>" +
    '<div id="c-hist" class="muted"></div></div>';
  function evaluate(src) {
    var toks = src.replace(/×/g, "*").replace(/÷/g, "/").replace(/−/g, "-").match(/\d*\.?\d+|[-+*/()]/g) || [], i = 0;
    function peek() { return toks[i]; }
    function expr() { var v = term(); while (peek() === "+" || peek() === "-") { var op = toks[i++], r = term(); v = op === "+" ? v + r : v - r; } return v; }
    function term() { var v = fac(); while (peek() === "*" || peek() === "/") { var op = toks[i++], r = fac(); v = op === "*" ? v * r : v / r; } return v; }
    function fac() {
      var t = toks[i++];
      if (t === "-") return -fac();
      if (t === "(") { var v = expr(); if (toks[i++] !== ")") throw new Error("括弧"); return v; }
      if (t == null || isNaN(+t)) throw new Error("式");
      return +t;
    }
    var v = expr(); if (i < toks.length) throw new Error("式"); return v;
  }
  var expr = "";
  function show() { $("#c-out").textContent = expr || "0"; $("#c-hist").innerHTML = hist.slice(-5).reverse().map(esc).join("<br>"); }
  root.querySelector(".keys").onclick = function (e) {
    var k = e.target.getAttribute("data-k"); if (!k) return;
    if (k === "C") expr = "";
    else if (k === "⌫") expr = expr.slice(0, -1);
    else if (k === "=") {
      try { var r = Math.round(evaluate(expr) * 1e10) / 1e10; if (!isFinite(r)) throw new Error(); hist.push(expr + " = " + r); Store.set("calc", hist.slice(-50)); $("#c-expr").textContent = expr + " ="; expr = String(r); }
      catch (err) { $("#c-expr").textContent = "エラー"; }
    } else expr += k;
    show();
  };
  show();
}

/* ═════════════ モジュール: カウンター ═════════════ */
function MOD_counter(C) {
  var root = document.getElementById("p-counter"), cs = Store.get("counters", [{ id: uid(), name: "カウント", n: 0 }]);
  root.innerHTML = '<div class="card"><div class="row"><input id="k-name" placeholder="カウンター名" class="grow"><button class="pri" id="k-add">追加</button></div><div id="k-list" class="counters"></div></div>';
  function render() {
    $("#k-list").innerHTML = cs.map(function (c) {
      return '<div class="ctr" data-id="' + c.id + '"><div class="muted">' + esc(c.name) + '</div><div class="big">' + c.n + '</div>' +
        '<div class="row c"><button data-d="-1">−</button><button class="pri" data-d="1">＋</button><button data-d="0">0</button><button data-d="x" class="danger">×</button></div></div>';
    }).join("");
  }
  $("#k-add").onclick = function () { cs.push({ id: uid(), name: $("#k-name").value || "カウント", n: 0 }); $("#k-name").value = ""; Store.set("counters", cs); render(); };
  $("#k-list").onclick = function (e) {
    var d = e.target.getAttribute("data-d"); if (d == null) return;
    var id = e.target.closest(".ctr").getAttribute("data-id");
    if (d === "x") cs = cs.filter(function (c) { return c.id !== id; });
    else cs.forEach(function (c) { if (c.id === id) c.n = d === "0" ? 0 : c.n + (+d); });
    if (C.features.sound && d === "1") beep(660, 0.05);
    Store.set("counters", cs); render();
  };
  render();
}

/* ═════════════ モジュール: クイズ / 単語帳 ═════════════ */
function MOD_quiz(C) {
  var root = document.getElementById("p-quiz");
  var cards = Store.get("cards", [{ id: uid(), q: "apple", a: "りんご" }, { id: uid(), q: "telegraph", a: "電信" }, { id: uid(), q: "entanglement", a: "量子もつれ" }]);
  var order = [], pos = 0, score = { ok: 0, ng: 0 };
  root.innerHTML = '<div class="card center"><h2>🎓 クイズ</h2><div id="q-card" class="flash"><div id="q-q" class="big"></div><div id="q-a" class="muted" hidden></div></div>' +
    '<div class="row c"><button id="q-show">答えを見る</button><button class="pri" id="q-ok" hidden>正解 ⭕</button><button id="q-ng" hidden>不正解 ❌</button></div>' +
    '<div id="q-score" class="muted"></div><button id="q-restart">シャッフルして最初から</button></div>' +
    '<div class="card"><h2>カードを追加</h2><div class="row"><input id="q-nq" placeholder="問題" class="grow"><input id="q-na" placeholder="答え" class="grow"><button class="pri" id="q-add">追加</button></div><div id="q-list" class="list"></div></div>';
  function restart() {
    order = cards.map(function (c) { return c.id; });
    for (var i = order.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = order[i]; order[i] = order[j]; order[j] = t; }
    pos = 0; score = { ok: 0, ng: 0 }; next();
  }
  function cur() { var id = order[pos]; return cards.filter(function (c) { return c.id === id; })[0]; }
  function next() {
    var c = cur();
    $("#q-a").hidden = true; $("#q-ok").hidden = true; $("#q-ng").hidden = true; $("#q-show").hidden = !c;
    $("#q-q").textContent = c ? c.q : "おしまい！"; $("#q-a").textContent = c ? c.a : "";
    $("#q-score").textContent = "⭕ " + score.ok + "  ❌ " + score.ng + "  (" + Math.min(pos + 1, order.length) + " / " + order.length + ")";
  }
  function list() {
    $("#q-list").innerHTML = cards.map(function (c) { return '<div class="item" data-id="' + c.id + '"><div class="grow"><b>' + esc(c.q) + "</b> → " + esc(c.a) + '</div><button class="danger">削除</button></div>'; }).join("");
  }
  $("#q-show").onclick = function () { $("#q-a").hidden = false; $("#q-ok").hidden = false; $("#q-ng").hidden = false; this.hidden = true; };
  $("#q-ok").onclick = function () { score.ok++; if (C.features.sound) beep(1046, 0.12); pos++; next(); };
  $("#q-ng").onclick = function () { score.ng++; if (C.features.sound) beep(220, 0.2); pos++; next(); };
  $("#q-restart").onclick = restart;
  $("#q-add").onclick = function () {
    var q = $("#q-nq").value.trim(), a = $("#q-na").value.trim(); if (!q || !a) return;
    cards.push({ id: uid(), q: q, a: a }); Store.set("cards", cards); $("#q-nq").value = ""; $("#q-na").value = ""; list();
  };
  $("#q-list").onclick = function (e) {
    if (e.target.tagName !== "BUTTON") return;
    var id = e.target.closest(".item").getAttribute("data-id"); cards = cards.filter(function (c) { return c.id !== id; }); Store.set("cards", cards); list();
  };
  list(); restart();
}

/* ═════════════ モジュール: お絵かき ═════════════ */
function MOD_draw(C) {
  var root = document.getElementById("p-draw");
  root.innerHTML = '<div class="card"><div class="row bar"><input type="color" id="d-col" value="#ff4d6d"><input type="range" id="d-size" min="1" max="40" value="6">' +
    '<button id="d-pen" class="on">✏ ペン</button><button id="d-eraser">🧽 消しゴム</button><button id="d-undo">↶ 戻す</button><button id="d-clear" class="danger">全消し</button><button class="pri" id="d-save">PNG 保存</button></div>' +
    '<canvas id="d-cv" class="paper"></canvas></div>';
  var cv = $("#d-cv"), x = cv.getContext("2d"), drawing = false, last = null, erase = false, undo = [];
  function fit() {
    var img = cv.width ? x.getImageData(0, 0, cv.width, cv.height) : null;
    cv.width = cv.clientWidth; cv.height = Math.round(cv.clientWidth * 0.7);
    x.fillStyle = "#fff"; x.fillRect(0, 0, cv.width, cv.height); if (img) x.putImageData(img, 0, 0);
  }
  function pt(e) { var r = cv.getBoundingClientRect(); return { x: (e.clientX - r.left) * cv.width / r.width, y: (e.clientY - r.top) * cv.height / r.height }; }
  cv.onpointerdown = function (e) { drawing = true; last = pt(e); undo.push(x.getImageData(0, 0, cv.width, cv.height)); if (undo.length > 30) undo.shift(); cv.setPointerCapture(e.pointerId); };
  cv.onpointermove = function (e) {
    if (!drawing) return;
    var p = pt(e); x.strokeStyle = erase ? "#fff" : $("#d-col").value; x.lineWidth = +$("#d-size").value * (erase ? 3 : 1);
    x.lineCap = "round"; x.lineJoin = "round"; x.beginPath(); x.moveTo(last.x, last.y); x.lineTo(p.x, p.y); x.stroke(); last = p;
  };
  cv.onpointerup = cv.onpointercancel = function () { drawing = false; };
  $("#d-pen").onclick = function () { erase = false; this.classList.add("on"); $("#d-eraser").classList.remove("on"); };
  $("#d-eraser").onclick = function () { erase = true; this.classList.add("on"); $("#d-pen").classList.remove("on"); };
  $("#d-undo").onclick = function () { var u = undo.pop(); if (u) x.putImageData(u, 0, 0); };
  $("#d-clear").onclick = function () { undo.push(x.getImageData(0, 0, cv.width, cv.height)); x.fillStyle = "#fff"; x.fillRect(0, 0, cv.width, cv.height); };
  $("#d-save").onclick = function () {
    var a = document.createElement("a"); a.href = cv.toDataURL("image/png"); a.download = C.slug + "-drawing.png"; document.body.appendChild(a); a.click(); a.remove();
  };
  window.addEventListener("tabshow", function (e) { if (e.detail === "draw" && cv.clientWidth && cv.width !== cv.clientWidth) fit(); });
  setTimeout(fit, 0);
}

/* ═════════════ モジュール: 単位変換 ═════════════ */
function MOD_convert(C) {
  var root = document.getElementById("p-convert");
  var U = {
    "長さ": { "mm": 0.001, "cm": 0.01, "m": 1, "km": 1000, "inch": 0.0254, "ft": 0.3048, "mile": 1609.344, "尺": 0.30303 },
    "重さ": { "g": 0.001, "kg": 1, "t": 1000, "oz": 0.0283495, "lb": 0.453592, "貫": 3.75 },
    "面積": { "m²": 1, "km²": 1e6, "坪": 3.30579, "畳": 1.62, "a": 100, "ha": 10000 },
    "温度": { "℃": "c", "℉": "f", "K": "k" }
  };
  root.innerHTML = '<div class="card"><h2>📐 単位変換</h2><div class="row"><select id="v-cat">' + Object.keys(U).map(function (k) { return "<option>" + k + "</option>"; }).join("") + "</select></div>" +
    '<div class="row"><input id="v-in" type="number" step="any" value="1" class="grow"><select id="v-from"></select> → <select id="v-to"></select></div><div id="v-out" class="big"></div><div id="v-all" class="muted"></div></div>';
  function units() { return U[$("#v-cat").value]; }
  function conv(v, f, t) {
    var u = units();
    if ($("#v-cat").value === "温度") {
      var c = f === "℃" ? v : f === "℉" ? (v - 32) * 5 / 9 : v - 273.15;
      return t === "℃" ? c : t === "℉" ? c * 9 / 5 + 32 : c + 273.15;
    }
    return v * u[f] / u[t];
  }
  function fill() {
    var ks = Object.keys(units()), o = ks.map(function (k) { return "<option>" + k + "</option>"; }).join("");
    $("#v-from").innerHTML = o; $("#v-to").innerHTML = o; $("#v-to").selectedIndex = Math.min(1, ks.length - 1); run();
  }
  function run() {
    var v = +$("#v-in").value, f = $("#v-from").value, t = $("#v-to").value;
    $("#v-out").textContent = (Math.round(conv(v, f, t) * 1e6) / 1e6) + " " + t;
    $("#v-all").innerHTML = Object.keys(units()).map(function (k) { return esc(k) + ": " + (Math.round(conv(v, f, k) * 1e6) / 1e6); }).join(" ／ ");
  }
  $("#v-cat").onchange = fill; $("#v-in").oninput = run; $("#v-from").onchange = run; $("#v-to").onchange = run;
  fill();
}

/* ═════════════ モジュール: 抽選 / サイコロ ═════════════ */
function MOD_random(C) {
  var root = document.getElementById("p-random");
  root.innerHTML = '<div class="card center"><h2>🎲 サイコロ</h2><div class="row c"><select id="r-n">' + [1, 2, 3, 4, 5].map(function (n) { return '<option value="' + n + '">' + n + " 個</option>"; }).join("") + '</select><button class="pri" id="r-roll">振る</button><button id="r-coin">コイン</button></div><div id="r-dice" class="dice"></div><div id="r-sum" class="muted"></div></div>' +
    '<div class="card"><h2>🎯 くじ引き (1 行に 1 候補)</h2><textarea id="r-items" rows="4"></textarea><div class="row"><button class="pri" id="r-pick">抽選</button><label class="inl"><input type="checkbox" id="r-norep"> 当たりを候補から外す</label></div><div id="r-res" class="big center"></div></div>';
  var F = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"];
  $("#r-items").value = Store.get("lottery", "グー\nチョキ\nパー");
  $("#r-roll").onclick = function () {
    var n = +$("#r-n").value, vs = [];
    for (var i = 0; i < n; i++) vs.push(1 + Math.floor(Math.random() * 6));
    $("#r-dice").textContent = vs.map(function (v) { return F[v - 1]; }).join(" ");
    $("#r-sum").textContent = "合計 " + vs.reduce(function (a, b) { return a + b; }, 0);
    if (C.features.sound) beep(520, 0.08);
  };
  $("#r-coin").onclick = function () { $("#r-dice").textContent = Math.random() < 0.5 ? "🪙 表" : "🪙 裏"; $("#r-sum").textContent = ""; };
  $("#r-items").oninput = function () { Store.set("lottery", this.value); };
  $("#r-pick").onclick = function () {
    var items = $("#r-items").value.split("\n").map(function (s) { return s.trim(); }).filter(Boolean);
    if (!items.length) { $("#r-res").textContent = "候補がありません"; return; }
    var k = Math.floor(Math.random() * items.length), w = items[k];
    $("#r-res").textContent = "🎉 " + w;
    if ($("#r-norep").checked) { items.splice(k, 1); $("#r-items").value = items.join("\n"); Store.set("lottery", $("#r-items").value); }
  };
}

/* ═════════════ モジュール: 習慣 ═════════════ */
function MOD_habit(C) {
  var root = document.getElementById("p-habit"), hs = Store.get("habits", [{ id: uid(), name: "読書 15 分", days: {} }]);
  root.innerHTML = '<div class="card"><h2>📅 習慣トラッカー (直近 14 日)</h2><div class="row"><input id="h-name" placeholder="新しい習慣" class="grow"><button class="pri" id="h-add">追加</button></div><div id="h-list"></div></div>';
  function key(d) { return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
  function lastDays() { var out = []; for (var i = 13; i >= 0; i--) { var d = new Date(); d.setDate(d.getDate() - i); out.push(d); } return out; }
  function streak(h) { var n = 0, d = new Date(); if (!h.days[key(d)]) d.setDate(d.getDate() - 1); while (h.days[key(d)]) { n++; d.setDate(d.getDate() - 1); } return n; }
  function render() {
    var ds = lastDays();
    $("#h-list").innerHTML = hs.map(function (h) {
      return '<div class="habit" data-id="' + h.id + '"><div class="row"><b class="grow">' + esc(h.name) + '</b><span class="pill">🔥 ' + streak(h) + ' 日連続</span><button class="danger" data-x="1">×</button></div><div class="days">' +
        ds.map(function (d) { var k = key(d); return '<button data-k="' + k + '" class="' + (h.days[k] ? "on" : "") + '" title="' + k + '">' + d.getDate() + "</button>"; }).join("") + "</div></div>";
    }).join("") || '<p class="muted">習慣を追加してください。</p>';
  }
  $("#h-add").onclick = function () { var n = $("#h-name").value.trim(); if (!n) return; hs.push({ id: uid(), name: n, days: {} }); $("#h-name").value = ""; Store.set("habits", hs); render(); };
  $("#h-list").onclick = function (e) {
    var b = e.target.closest("button"); if (!b) return;
    var id = b.closest(".habit").getAttribute("data-id");
    if (b.getAttribute("data-x")) hs = hs.filter(function (h) { return h.id !== id; });
    else hs.forEach(function (h) { if (h.id === id) { var k = b.getAttribute("data-k"); if (h.days[k]) delete h.days[k]; else { h.days[k] = 1; if (C.features.sound) beep(880, 0.1); } } });
    Store.set("habits", hs); render();
  };
  render();
}

/* ═════════════ モジュール: 電信 (モールス) ═════════════ */
function MOD_telegraph(C) {
  var root = document.getElementById("p-telegraph");
  var M = { A: ".-", B: "-...", C: "-.-.", D: "-..", E: ".", F: "..-.", G: "--.", H: "....", I: "..", J: ".---", K: "-.-", L: ".-..", M: "--", N: "-.", O: "---", P: ".--.", Q: "--.-", R: ".-.", S: "...", T: "-", U: "..-", V: "...-", W: ".--", X: "-..-", Y: "-.--", Z: "--..", "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.", ".": ".-.-.-", ",": "--..--", "?": "..--..", "/": "-..-." };
  var R = {}; Object.keys(M).forEach(function (k) { R[M[k]] = k; });
  root.innerHTML = '<div class="card"><h2>📡 モールス電信</h2><textarea id="m-text" rows="2">SOS HELLO BADA</textarea><div class="row"><button class="pri" id="m-enc">符号化 ▶</button><button id="m-play">🔊 打電</button><button id="m-dec">◀ 復号</button></div>' +
    '<textarea id="m-code" rows="3" class="mono"></textarea><p class="muted">英数字と . , ? / に対応。語の区切りは " / "。</p></div>';
  function enc(s) { return s.toUpperCase().split(" ").map(function (w) { return w.split("").map(function (ch) { return M[ch] || ""; }).filter(Boolean).join(" "); }).join(" / "); }
  function dec(s) { return s.trim().split(/\s*\/\s*/).map(function (w) { return w.split(/\s+/).map(function (c) { return R[c] || ""; }).join(""); }).join(" "); }
  $("#m-enc").onclick = function () { $("#m-code").value = enc($("#m-text").value); };
  $("#m-dec").onclick = function () { $("#m-text").value = dec($("#m-code").value); };
  $("#m-play").onclick = function () {
    var code = $("#m-code").value || enc($("#m-text").value), t = 0, u = 80;
    code.split("").forEach(function (s) {
      if (s === ".") { setTimeout(function () { beep(700, u / 1000); }, t); t += u * 2; }
      else if (s === "-") { setTimeout(function () { beep(700, 3 * u / 1000); }, t); t += u * 4; }
      else t += u * 2;
    });
  };
  $("#m-enc").click();
}

/* ═════════════ モジュール: 量子回路 (2 qubit 状態ベクトル) ═════════════ */
function MOD_quantum(C) {
  var root = document.getElementById("p-quantum"), st, log = [];
  root.innerHTML = '<div class="card"><h2>⚛ 量子回路 (2 qubit)</h2><div class="row bar"><button data-g="H0">H q0</button><button data-g="H1">H q1</button><button data-g="X0">X q0</button><button data-g="X1">X q1</button><button data-g="Z0">Z q0</button><button data-g="CX">CNOT q0→q1</button></div>' +
    '<div class="row bar"><button class="pri" id="qm-bell">ベル状態を作る</button><button id="qm-meas">測定 ×1000</button><button id="qm-rst">|00⟩ に戻す</button></div>' +
    '<div id="qm-circ" class="mono"></div><div id="qm-amp"></div><canvas id="qm-chart" class="chart"></canvas></div>';
  var S = Math.SQRT1_2;
  function reset() { st = [[1, 0], [0, 0], [0, 0], [0, 0]]; log = []; render(); }
  function apply1(q, m) {
    var out = st.map(function () { return [0, 0]; });
    for (var i = 0; i < 4; i++) {
      var b = (i >> q) & 1;
      for (var nb = 0; nb < 2; nb++) {
        var j = (i & ~(1 << q)) | (nb << q), c = m[nb][b];
        out[j][0] += c * st[i][0]; out[j][1] += c * st[i][1];
      }
    }
    st = out;
  }
  function gate(g) {
    if (g[0] === "H") apply1(+g[1], [[S, S], [S, -S]]);
    if (g[0] === "X") apply1(+g[1], [[0, 1], [1, 0]]);
    if (g[0] === "Z") apply1(+g[1], [[1, 0], [0, -1]]);
    if (g === "CX") { var t = st[1]; st[1] = st[3]; st[3] = t; }
    log.push(g); render();
  }
  function probs() { return st.map(function (a) { return a[0] * a[0] + a[1] * a[1]; }); }
  function render(counts) {
    var p = probs(), lab = ["|00⟩", "|01⟩", "|10⟩", "|11⟩"];
    $("#qm-circ").textContent = "回路: " + (log.join(" → ") || "(なし)");
    $("#qm-amp").innerHTML = st.map(function (a, i) {
      return '<div class="amp"><span class="mono">' + lab[i] + '</span><span class="mono">' + a[0].toFixed(3) + (a[1] ? (a[1] < 0 ? " − " : " + ") + Math.abs(a[1]).toFixed(3) + "i" : "") +
        '</span><div class="progress"><div style="width:' + (p[i] * 100) + '%"></div></div><span>' + (p[i] * 100).toFixed(1) + "%</span></div>";
    }).join("");
    barChart($("#qm-chart"), lab, counts || p.map(function (x) { return Math.round(x * 1000) / 10; }));
  }
  $$("[data-g]", root).forEach(function (b) { b.onclick = function () { gate(b.getAttribute("data-g")); }; });
  $("#qm-bell").onclick = function () { reset(); gate("H0"); gate("CX"); };
  $("#qm-rst").onclick = reset;
  $("#qm-meas").onclick = function () {
    var p = probs(), c = [0, 0, 0, 0];
    for (var s = 0; s < 1000; s++) { var r = Math.random(), k = 0; while (k < 3 && r > p[k]) { r -= p[k]; k++; } c[k]++; }
    render(c);
  };
  window.addEventListener("tabshow", function (e) { if (e.detail === "quantum") render(); });
  reset();
}

/* ═════════════ 組み立て ═════════════ */

var MODULE_IMPL = {
  records: MOD_records, todo: MOD_todo, notes: MOD_notes, budget: MOD_budget, timer: MOD_timer, calc: MOD_calc,
  counter: MOD_counter, quiz: MOD_quiz, draw: MOD_draw, convert: MOD_convert, random: MOD_random, habit: MOD_habit,
  telegraph: MOD_telegraph, quantum: MOD_quantum
};

var APP_CSS = [
  ":root{--acc:#8fd0ff}",
  "body[data-theme=dark]{--bg:#0b0f1a;--bg2:#141b2d;--card:rgba(24,32,54,.75);--line:rgba(150,190,255,.18);--fg:#e8f0ff;--muted:#93a4c4;--inp:rgba(0,0,0,.28)}",
  "body[data-theme=light]{--bg:#f4f6fb;--bg2:#e8edf7;--card:#fff;--line:#d5dcea;--fg:#1b2333;--muted:#66728a;--inp:#fff}",
  "*{box-sizing:border-box}html,body{margin:0}",
  "body{background:linear-gradient(180deg,var(--bg2),var(--bg) 40%);color:var(--fg);font:15px/1.55 -apple-system,'Hiragino Kaku Gothic ProN','Yu Gothic UI','Noto Sans JP',system-ui,sans-serif;min-height:100vh;padding:0 0 40px}",
  ".top{display:flex;align-items:center;gap:10px;padding:14px 16px 8px;max-width:900px;margin:0 auto}.top>div:first-child{flex:1;min-width:0}",
  "h1{margin:0;font-size:20px;font-weight:600;color:var(--acc)}.sub{margin:2px 0 0;font-size:12px;color:var(--muted)}",
  ".tools button{background:none;border:1px solid var(--line);color:var(--fg);border-radius:10px;padding:6px 9px;cursor:pointer}",
  ".tabs{display:flex;gap:6px;overflow-x:auto;padding:6px 16px;max-width:900px;margin:0 auto}",
  ".tabs button{flex:0 0 auto;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:20px;padding:7px 14px;cursor:pointer;font-size:14px}",
  ".tabs button.on{background:var(--acc);color:#061018;border-color:var(--acc)}",
  "main{max-width:900px;margin:0 auto;padding:6px 16px}",
  ".card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;margin:0 0 12px;box-shadow:0 8px 30px rgba(0,0,0,.12)}",
  ".card h2{margin:0 0 10px;font-size:14px;color:var(--acc);letter-spacing:.04em}",
  "input,select,textarea{background:var(--inp);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:8px 10px;font:inherit;min-width:0;max-width:100%}",
  "textarea{width:100%;resize:vertical}input[type=checkbox]{width:20px;height:20px;accent-color:var(--acc)}input[type=color]{padding:2px;width:44px;height:36px}",
  "button{background:var(--bg2);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:8px 13px;font:inherit;cursor:pointer}",
  "button.pri,button.on{background:var(--acc);color:#061018;border-color:var(--acc);font-weight:600}button.danger{color:#ff6b6b}button:active{transform:scale(.97)}",
  ".row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}.row.c{justify-content:center}.grow{flex:1;min-width:120px}.bar{margin-top:0}",
  ".form{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}.form label{display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--muted)}.form label.wide{grid-column:1/-1}.form input,.form select,.form textarea{width:100%}",
  ".list{display:flex;flex-direction:column;gap:6px;margin-top:8px}",
  ".item{display:flex;gap:8px;align-items:center;padding:9px 10px;border:1px solid var(--line);border-radius:12px;background:var(--inp);cursor:default}.item.on{border-color:var(--acc)}.item.done .grow{text-decoration:line-through;opacity:.55}",
  ".kv{font-size:12px;color:var(--muted);margin-right:8px}.kv i{font-style:normal;opacity:.7;margin-right:4px}.kv.late{color:#ff6b6b}",
  ".pill{font-size:11px;padding:2px 8px;border-radius:20px;border:1px solid var(--line);color:var(--muted)}.pill.p3{color:#ff6b6b;border-color:#ff6b6b}",
  ".muted{color:var(--muted);font-size:13px}.center{text-align:center}.big{font-size:40px;font-weight:300;font-variant-numeric:tabular-nums;margin:6px 0}.mono{font-family:ui-monospace,Menlo,Consolas,monospace}",
  ".progress{height:8px;border-radius:8px;background:var(--inp);border:1px solid var(--line);overflow:hidden;margin:8px 0;flex:1}.progress>div{height:100%;background:var(--acc);transition:width .3s}",
  ".chart{width:100%;height:180px;display:block;margin-top:8px}.paper{width:100%;border-radius:12px;touch-action:none;background:#fff;display:block}",
  ".stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0}.stats div{border:1px solid var(--line);border-radius:12px;padding:8px;text-align:center}.stats i{display:block;font-style:normal;font-size:12px;color:var(--muted)}",
  ".pos{color:#3ccf7a}.neg{color:#ff6b6b}",
  ".split{display:grid;grid-template-columns:240px 1fr;gap:12px}.split .main{display:flex;flex-direction:column;gap:8px}@media(max-width:640px){.split{grid-template-columns:1fr}}",
  ".calc{max-width:360px;margin-left:auto;margin-right:auto}.disp{text-align:right;padding:8px;border:1px solid var(--line);border-radius:12px;background:var(--inp);overflow:hidden}.keys{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0}.keys button{padding:16px 0;font-size:20px}",
  ".counters{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}.ctr{border:1px solid var(--line);border-radius:14px;padding:10px;text-align:center}",
  ".flash{min-height:120px;border:1px dashed var(--line);border-radius:14px;padding:16px;margin-bottom:8px}.dice{font-size:64px;line-height:1.2}",
  ".habit{border:1px solid var(--line);border-radius:12px;padding:6px 10px;margin:8px 0}.days{display:grid;grid-template-columns:repeat(14,1fr);gap:4px}.days button{padding:6px 0;font-size:11px}",
  ".amp{display:grid;grid-template-columns:52px 150px 1fr 52px;gap:8px;align-items:center;font-size:13px}",
  ".inl{display:inline-flex;gap:6px;align-items:center;font-size:13px;color:var(--muted)}",
  "#about{position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;padding:16px;z-index:9}#about[hidden]{display:none}",
  "#about>div{background:var(--bg);border:1px solid var(--line);border-radius:16px;padding:16px;max-width:560px;max-height:80vh;overflow:auto}",
  "#toast{position:fixed;left:50%;bottom:20px;transform:translateX(-50%) translateY(80px);background:var(--acc);color:#061018;padding:8px 16px;border-radius:20px;transition:.25s;z-index:10}#toast.show{transform:translateX(-50%)}",
  "footer{text-align:center;font-size:11px;color:var(--muted);margin-top:20px}",
  "@media print{.tabs,.tools,button,footer{display:none!important}main>section{display:block!important}.card{box-shadow:none}}"
].join("\n");

/* <script> 内へ埋め込む JSON (閉じタグ文字列で script が途切れないよう < を \u003c に逃がす) */
function scriptJSON(v) { return JSON.stringify(v).replace(/</g, "\\u003c").replace(/\u2028/g, "\\u2028").replace(/\u2029/g, "\\u2029"); }

/* 仕様 → 自己完結 HTML */
function generateApp(spec) {
  var slug = slugify(spec.title);
  var feats = {};
  Object.keys(spec.features || {}).forEach(function (k) { feats[k] = true; });
  var mods = spec.modules.filter(function (m) { return MODULE_IMPL[m.id]; });
  var about = {
    purpose: spec.purpose, input: spec.input, coverage: spec.coverage,
    unresolved: spec.unresolved || [], assumptions: spec.assumptions || []
  };
  var APP = { key: "bgt-" + slug, title: spec.title, theme: spec.theme.mode, version: BGT_VERSION };
  var tabs = mods.length > 1 ? '<nav class="tabs">' + mods.map(function (m) {
    return '<button data-tab="' + m.id + '">' + m.icon + " " + escapeHtml(m.id === "records" ? (spec.entity || "記録") : m.label) + "</button>";
  }).join("") + "</nav>" : "";
  var sections = mods.map(function (m) { return '<section id="p-' + m.id + '"></section>'; }).join("\n");
  var aboutHtml = "<h2>この依頼について</h2><p class=\"muted\">BadaGPT電信が次の依頼から生成しました (節の網羅率 " + Math.round(spec.coverage * 100) + "%)。</p>" +
    "<blockquote>" + escapeHtml(spec.input || "") + "</blockquote>" +
    (about.assumptions.length ? "<h3>仮定</h3><ul>" + about.assumptions.map(function (a) { return "<li>" + escapeHtml(a) + "</li>"; }).join("") + "</ul>" : "") +
    (about.unresolved.length ? "<h3>解釈できなかった節 (要望メモ)</h3><ul>" + about.unresolved.map(function (a) { return "<li>" + escapeHtml(a) + "</li>"; }).join("") + "</ul>" : "") +
    "<p class=\"muted\">データはこの端末の中だけに保存されます (ネットワーク通信なし)。</p><button id=\"aboutClose\" class=\"pri\">閉じる</button>";
  var cfgBase = { slug: fileBase(spec.title), features: feats, entity: spec.entity || "データ", fields: (spec.fields || []).map(function (f) { return { key: f.key, name: f.name, type: f.type }; }) };
  var js = ['"use strict";',
    "(" + RT_core.toString() + ")(" + scriptJSON(APP) + ");"]
    .concat(mods.map(function (m) { return "(" + MODULE_IMPL[m.id].toString() + ")(" + scriptJSON(cfgBase) + ");"; }))
    .concat(["APP_start();"]).join("\n\n");
  var css = APP_CSS.replace(":root{--acc:#8fd0ff}", ":root{--acc:" + spec.theme.accent + "}");
  var html = "<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"UTF-8\">\n" +
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n" +
    "<meta name=\"generator\" content=\"BadaGPT Telegraph " + BGT_VERSION + "\">\n" +
    "<title>" + escapeHtml(spec.title) + "</title>\n<style>\n" + css + "\n</style>\n</head>\n" +
    "<body data-theme=\"" + spec.theme.mode + "\">\n" +
    "<header class=\"top\"><div><h1>" + escapeHtml(spec.title) + "</h1><p class=\"sub\">" + escapeHtml(spec.purpose || "") + "</p></div>" +
    "<div class=\"tools\"><button id=\"themeBtn\" title=\"ダーク / ライト\">◐</button>" + (feats.print ? "<button id=\"printBtn\" title=\"印刷\">🖨</button>" : "") +
    "<button id=\"aboutBtn\" title=\"この依頼について\">ⓘ</button></div></header>\n" + tabs + "\n<main>\n" + sections + "\n</main>\n" +
    "<div id=\"about\" hidden><div>" + aboutHtml + "</div></div><div id=\"toast\"></div>\n" +
    "<footer>Generated by BadaGPT電信 v" + BGT_VERSION + " · オフライン動作 · データは端末内に保存</footer>\n" +
    "<script>\n" + js + "\n<\/script>\n</body>\n</html>\n";
  return { html: html, slug: slug, file: fileBase(spec.title), modules: mods.map(function (m) { return m.id; }), bytes: utf8(html).length, lines: html.split("\n").length };
}

/* HTML から <script> 本文を取り出す */
function extractScripts(html) {
  var out = [], re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi, m;
  while ((m = re.exec(html))) { if (!/\bsrc\s*=/.test(m[1]) && !/type\s*=\s*["']?(?!text\/javascript|module)[^"'\s>]+/i.test(m[1])) out.push(m[2]); }
  return out;
}

/* 検証: 構文・モジュールの存在・オフライン性・依頼との対応 */
function verifyApp(html, spec) {
  var checks = [];
  function add(name, ok, detail) { checks.push({ name: name, ok: !!ok, detail: detail || "" }); }
  add("HTML 文書の骨格", /^<!DOCTYPE html>/i.test(html.trim()) && /<\/html>\s*$/i.test(html.trim()), "DOCTYPE と </html>");
  var scripts = extractScripts(html), syntaxErr = "";
  scripts.forEach(function (s) { try { new Function(s); } catch (e) { syntaxErr = syntaxErr || e.message; } }); // eslint-disable-line no-new-func
  add("JavaScript 構文", scripts.length > 0 && !syntaxErr, syntaxErr || scripts.length + " 個のスクリプト");
  var ext = html.match(/\b(?:src|href)\s*=\s*["']https?:\/\/[^"']+/gi) || [];
  add("オフライン動作 (外部読み込みなし)", ext.length === 0, ext.length ? ext[0] : "外部 URL 0 件");
  if (spec) {
    var missing = spec.modules.filter(function (m) { return MODULE_IMPL[m.id] && html.indexOf('id="p-' + m.id + '"') < 0; });
    add("依頼されたモジュールの実装", !missing.length, missing.length ? "不足: " + missing.map(function (m) { return m.label; }).join(", ") : spec.modules.map(function (m) { return m.label; }).join(" / "));
    if (spec.fields && spec.fields.length && html.indexOf('id="p-records"') >= 0) {
      var nf = spec.fields.filter(function (f) { return html.indexOf(scriptJSON(f.name).slice(1, -1)) < 0; });
      add("項目 (データモデル) の実装", !nf.length, nf.length ? "不足: " + nf.map(function (f) { return f.name; }).join(", ") : spec.fields.length + " 項目");
    }
    add("題名の反映", html.indexOf(escapeHtml(spec.title)) >= 0, spec.title);
    add("依頼文の網羅率", spec.coverage >= 0.5, Math.round(spec.coverage * 100) + "% (" + spec.clauses.filter(function (c) { return c.hits.length; }).length + "/" + spec.clauses.length + " 節)");
  }
  add("サイズ", html.length < 2000000, Math.round(utf8(html).length / 1024) + " KB");
  return { ok: checks.every(function (c) { return c.ok; }), checks: checks };
}
