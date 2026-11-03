/*
 * ui.js — BadaGPT電信 の画面 (DOM)。engine/comprehend/generate/paper の純ロジックを配線する。
 *
 * 「電信して錬成」で badagpt.bada を Bada インタプリタが実行し、
 * Tele:: (電信) と GPT:: (BadaGPT) の各命令が順に画面の各段を駆動する。
 */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var isCordova = !!window.cordova;
  var LS = {
    get: function (k, d) { try { var v = localStorage.getItem("bgt:" + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem("bgt:" + k, JSON.stringify(v)); } catch (e) { /* 保存不可 */ } }
  };
  $("ver").textContent = BGT_VERSION;

  /* ───────── 例文 ───────── */
  var EXAMPLES = [
    ["📚 読書記録", "読んだ本を管理したい。項目はタイトル、著者、読了日、評価、感想。評価順に並べ替えたい。青いダークなデザインで、スマホとWindowsで使いたい。"],
    ["💴 家計簿", "毎月の家計簿をつけたい。支出と収入を記録してグラフで見たい。緑色で明るいデザインにして、CSVで書き出せるように。"],
    ["🍅 勉強セット", "勉強用にポモドーロタイマーと単語帳クイズ、それとToDoリストが欲しい。音で知らせて。Linuxでも使いたい。"],
    ["⚛ 量子と電信", "量子もつれのベル状態を試せる回路と、モールスで電信を打てる画面を一つのアプリに。紫のデザインで。"],
    ["🎨 子供向け", "子供と遊べるお絵かきとサイコロのアプリを作って。ピンク色で。"]
  ];
  EXAMPLES.forEach(function (ex) {
    var b = document.createElement("span"); b.className = "chip"; b.textContent = ex[0];
    b.onclick = function () { $("thought").value = ex[1]; };
    $("examples").appendChild(b);
  });
  $("thought").value = LS.get("draft", "");
  $("thought").oninput = function () { LS.set("draft", this.value); };
  $("author").value = LS.get("author", "");
  $("author").oninput = function () { LS.set("author", this.value); };

  /* ───────── 音声入力 (対応環境のみ) ───────── */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SR) {
    $("voiceBtn").classList.remove("hidden");
    $("voiceBtn").onclick = function () {
      var r = new SR(); r.lang = "ja-JP"; r.interimResults = false;
      r.onresult = function (e) { var t = e.results[0][0].transcript; $("thought").value += ($("thought").value ? "\n" : "") + t; LS.set("draft", $("thought").value); };
      r.onerror = function (e) { $("modemStat").textContent = "音声入力を使えません: " + e.error; };
      r.start(); $("modemStat").textContent = "🎙 話してください…";
    };
  }

  /* ───────── Android の実行時権限 ───────── */
  function androidPerm(name) {
    return new Promise(function (resolve) {
      var P = isCordova && window.cordova.plugins && window.cordova.plugins.permissions;
      if (!P) return resolve(true);
      P.requestPermission(P[name], function (s) { resolve(!!(s && s.hasPermission)); }, function () { resolve(false); });
    });
  }

  /* ───────── FSK 音響電信: スマホ ⇄ アプリで依頼文を送受信 ───────── */
  var AC = null;
  function ctx() { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === "suspended") AC.resume(); return AC; }
  var spec2 = $("spectrum"), sx = spec2.getContext("2d");
  function drawWave(d) {
    var W = spec2.clientWidth, H = 60, dpr = window.devicePixelRatio || 1;
    if (spec2.width !== W * dpr) { spec2.width = W * dpr; spec2.height = H * dpr; sx.setTransform(dpr, 0, 0, dpr, 0, 0); }
    sx.clearRect(0, 0, W, H); sx.strokeStyle = "rgba(123,224,192,.85)"; sx.beginPath();
    var step = Math.max(1, Math.floor(d.length / W));
    for (var x = 0; x < W; x++) { var y = H / 2 - (d[x * step] || 0) * H * 0.45; if (x) sx.lineTo(x, y); else sx.moveTo(x, y); }
    sx.stroke();
  }
  $("sendFskBtn").onclick = function () {
    var text = $("thought").value.trim();
    if (!text) { $("modemStat").textContent = "依頼文が空です。"; return; }
    var c = ctx(), s = fskModulate(text, c.sampleRate), buf = c.createBuffer(1, s.length, c.sampleRate);
    buf.getChannelData(0).set(s);
    var src = c.createBufferSource(); src.buffer = buf; src.connect(c.destination); src.start();
    $("spectrum").classList.remove("hidden");
    var i = 0, chunk = Math.round(c.sampleRate * 0.05);
    var iv = setInterval(function () { if (i + chunk >= s.length) { clearInterval(iv); return; } drawWave(s.subarray(i, i + chunk)); i += chunk; }, 50);
    $("modemStat").textContent = "🔊 電信中… " + (s.length / c.sampleRate).toFixed(1) + " 秒 (FSK 1000/1600 Hz · 100 baud)。相手の BadaGPT電信で「受信」してください。電話のスピーカー越しでも届きます。";
    src.onended = function () { $("modemStat").textContent = "送信完了。"; };
  };
  var mic = null, proc = null, msrc = null, rec = [], live = 0;
  function merged() { var n = 0; rec.forEach(function (a) { n += a.length; }); var o = new Float32Array(n), k = 0; rec.forEach(function (a) { o.set(a, k); k += a.length; }); return o; }
  function gotText(t) { $("thought").value = t; LS.set("draft", t); $("modemStat").innerHTML = "✓ 電信を受信しました (" + t.length + " 文字)。「電信して錬成」で錬成できます。"; }
  $("listenBtn").onclick = function () {
    androidPerm("RECORD_AUDIO").then(function () {
      return navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
    }).then(function (stream) {
      var c = ctx(); mic = stream; msrc = c.createMediaStreamSource(stream); proc = c.createScriptProcessor(4096, 1, 1); rec = []; live = 0;
      proc.onaudioprocess = function (e) {
        var d = e.inputBuffer.getChannelData(0); rec.push(new Float32Array(d)); drawWave(d);
        if (++live % 12 === 0) {
          var all = merged(), tail = all.length > c.sampleRate * 30 ? all.subarray(all.length - c.sampleRate * 30) : all;
          var t = fskDemodulate(tail, c.sampleRate); if (t) gotText(t);
        }
      };
      msrc.connect(proc); proc.connect(c.destination);
      $("spectrum").classList.remove("hidden"); $("listenBtn").classList.add("hidden"); $("stopBtn").classList.remove("hidden");
      $("modemStat").textContent = "🎙 受信中… スマホの BadaGPT電信で「この依頼を電信で送る」を押してください。";
    }).catch(function (e) { $("modemStat").innerHTML = "<span class=err>マイクを開始できません: " + escapeHtml(e.message || e) + "</span>"; });
  };
  $("stopBtn").onclick = function () {
    try { proc.disconnect(); msrc.disconnect(); mic.getTracks().forEach(function (t) { t.stop(); }); } catch (e) { /* 既に停止 */ }
    $("listenBtn").classList.remove("hidden"); $("stopBtn").classList.add("hidden");
    var t = fskDemodulate(merged(), (AC && AC.sampleRate) || 44100);
    if (t) gotText(t); else $("modemStat").textContent = "復号できませんでした (音量・距離・雑音を確認して再試行してください)。";
  };

  /* ───────── 電信アニメーション ───────── */
  var cv = $("stage"), cx = cv.getContext("2d"), anim = { t: 0, prog: -1, n: 5, done: false };
  function draw() {
    var dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = 190;
    if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = H * dpr; cx.setTransform(dpr, 0, 0, dpr, 0, 0); }
    anim.t += 0.03; var t = anim.t;
    cx.clearRect(0, 0, W, H);
    var sx0 = 50, rx = W - 50, my = H * 0.48, mx = W / 2;
    cx.save(); cx.translate(mx, my); cx.lineWidth = 1.5;
    for (var k = 0; k < anim.n; k++) {
      var a0 = k / anim.n * Math.PI * 2, a1 = (k + 2) / anim.n * Math.PI * 2, hue = 200 + (k * 40) % 140;
      cx.strokeStyle = "hsla(" + hue + ",85%,68%,.85)"; cx.beginPath();
      for (var u = 0; u <= 1.0001; u += 0.05) {
        var a = a0 + (a1 - a0) * u, rr = 34 * (1 + 0.18 * Math.sin(u * Math.PI * 2 + t * 2 + k));
        var px = Math.cos(a) * rr, py = Math.sin(a) * rr * 0.62; if (u === 0) cx.moveTo(px, py); else cx.lineTo(px, py);
      }
      cx.stroke();
    }
    cx.restore();
    cx.strokeStyle = "rgba(120,200,255,.5)"; cx.lineWidth = 1.1;
    for (var s = -1; s <= 1; s += 2) {
      cx.beginPath();
      for (var x = sx0; x < mx - 40; x += 4) { var ph = (x - sx0) / 40; cx.lineTo(x, my + s * 9 * Math.sin(ph * 2 - t * 4)); }
      cx.stroke();
    }
    cx.strokeStyle = "rgba(123,224,192,.85)"; cx.lineWidth = 1.4; cx.beginPath();
    for (var x2 = mx + 40; x2 < rx; x2 += 2) cx.lineTo(x2, my + 13 * Math.sin((x2 - mx) * 0.2 - t * 6));
    cx.stroke();
    if (anim.prog >= 0) {
      var p = Math.min(1, anim.prog), qx = sx0 + (rx - sx0) * p, qy = my - 30 * Math.sin(p * Math.PI);
      cx.save(); cx.shadowColor = "rgba(255,220,140,.9)"; cx.shadowBlur = 14; cx.fillStyle = "rgba(255,230,160,.95)";
      cx.beginPath(); cx.arc(qx, qy, 5.5, 0, 7); cx.fill(); cx.restore();
    }
    function node(x, live) { cx.save(); cx.shadowColor = "rgba(143,208,255,.7)"; cx.shadowBlur = 14; cx.fillStyle = live ? "rgba(92,208,138,.95)" : "rgba(143,208,255,.85)"; cx.beginPath(); cx.arc(x, my, 9, 0, 7); cx.fill(); cx.restore(); }
    node(sx0, false); node(rx, anim.done);
    cx.fillStyle = "rgba(168,190,228,.75)"; cx.font = "10px system-ui"; cx.textAlign = "center";
    cx.fillText("思考入力", sx0, my + 28); cx.fillText("Jones 量子チャンネル", mx, my + 56); cx.fillText("BadaGPT", rx, my + 28);
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);

  /* ───────── パイプライン ───────── */
  var STEP_NAMES = [["encode", "符号化"], ["knot", "結び目"], ["teleport", "量子転送"], ["graviton", "搬送波"], ["send", "配信"],
    ["comprehend", "全体把握"], ["plan", "設計"], ["generate", "生成"], ["verify", "検証"], ["paper", "論文"]];
  function renderSteps(state) {
    $("steps").innerHTML = STEP_NAMES.map(function (s) { return '<span class="' + (state[s[0]] || "") + '">' + s[1] + "</span>"; }).join("");
  }
  renderSteps({});
  var bada = null;
  function blog(line) {
    if (line) bada.out.push(line);
    $("bconsole").textContent = "BADA ▸ " + bada.out.slice(-40).join("\n");
    $("bconsole").scrollTop = $("bconsole").scrollHeight;
  }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  var cur = null; /* { spec, gen, ver, paper, metrics, engine, runtime } */

  function renderSpec(spec) {
    var fk = Object.keys(spec.features);
    var h = '<div class="cov"><div style="width:' + Math.round(spec.coverage * 100) + '%"></div></div>' +
      '<div class="muted">節の網羅率 <b style="color:#eaf4ff">' + Math.round(spec.coverage * 100) + "%</b> (" +
      spec.clauses.filter(function (c) { return c.hits.length; }).length + " / " + spec.clauses.length + " 節)</div>" +
      '<dl class="spec" style="margin-top:10px">' +
      "<dt>題名</dt><dd>" + escapeHtml(spec.title) + "</dd>" +
      "<dt>目的</dt><dd>" + escapeHtml(spec.purpose || "—") + "</dd>" +
      "<dt>モジュール</dt><dd>" + spec.modules.map(function (m) { return '<span class="pill" title="' + escapeHtml(m.reason) + '">' + m.icon + " " + escapeHtml(m.id === "records" ? spec.entity + "の管理" : m.label) + "</span>"; }).join("") + "</dd>" +
      (spec.fields.length && spec.modules.some(function (m) { return m.id === "records"; }) ?
        "<dt>データ項目</dt><dd>" + spec.fields.map(function (f) { return '<span class="pill">' + escapeHtml(f.name) + " : " + (TYPE_JA[f.type] || f.type) + "</span>"; }).join("") + "</dd>" : "") +
      "<dt>機能</dt><dd>" + (fk.length ? fk.map(function (k) { return '<span class="pill' + (spec.features[k].assumed ? " as" : "") + '" title="' + escapeHtml(spec.features[k].reason) + '">' + escapeHtml(spec.features[k].label) + "</span>"; }).join("") : "—") + "</dd>" +
      '<dt>見た目</dt><dd><span class="pill" style="border-color:' + spec.theme.accent + ";color:" + spec.theme.accent + '">● ' + (spec.theme.accentName || "標準") + "</span>" +
      '<span class="pill">' + (spec.theme.mode === "light" ? "ライト" : "ダーク") + "</span></dd>" +
      "<dt>対象</dt><dd>" + spec.platforms.map(function (p) { return '<span class="pill">' + PLATFORM_JA[p] + "</span>"; }).join("") + "</dd>" +
      "</dl>" +
      "<table><tr><th>#</th><th>節 (原文)</th><th>対応付け</th></tr>" +
      spec.clauses.map(function (c, i) {
        return "<tr><td>" + (i + 1) + "</td><td>" + escapeHtml(c.text) + '</td><td class="' + (c.hits.length ? "ok" : "ng") + '">' + escapeHtml(c.hits.length ? c.hits.join(" / ") : "未解釈 (要望メモとして保持)") + "</td></tr>";
      }).join("") + "</table>" +
      (spec.assumptions.length ? '<div class="muted" style="margin-top:8px">仮定: ' + spec.assumptions.map(escapeHtml).join("<br>") + "</div>" : "");
    $("specView").innerHTML = h;
  }

  /* 生成アプリをサンドボックスで実行し、実行時エラーを拾う */
  var probeWait = null;
  window.addEventListener("message", function (e) {
    if (!e.data || !e.data.bgt || !probeWait) return;
    if (e.data.bgt === "err") probeWait.errors.push(e.data.msg);
    if (e.data.bgt === "ok") { var w = probeWait; probeWait = null; w.resolve(w.errors); }
  });
  function runPreview(html) {
    var probe = "<script>addEventListener('error',function(e){parent.postMessage({bgt:'err',msg:String(e.message)},'*')});" +
      "addEventListener('load',function(){setTimeout(function(){parent.postMessage({bgt:'ok'},'*')},500)});<\/script>";
    var withProbe = html.replace(/<head>/i, "<head>" + probe);
    return new Promise(function (resolve) {
      probeWait = { errors: [], resolve: resolve };
      $("preview").srcdoc = withProbe;
      setTimeout(function () { if (probeWait) { var w = probeWait; probeWait = null; w.resolve(w.errors.length ? w.errors : null); } }, 4000);
    });
  }

  function claudeGenerate(spec) {
    var key = LS.get("apiKey", ""), model = LS.get("model", "claude-opus-5-5");
    var req = claudeRequest({ apiKey: key, model: model, spec: spec, effort: "high" });
    var st = sseNew();
    return fetch(req.url, { method: "POST", headers: req.headers, body: JSON.stringify(req.body) }).then(function (res) {
      if (!res.ok) return res.text().then(function (t) { throw new Error("HTTP " + res.status + ": " + t.slice(0, 200)); });
      var reader = res.body.getReader(), dec = new TextDecoder();
      function pump() {
        return reader.read().then(function (r) {
          if (r.done) return st;
          sseFeed(st, dec.decode(r.value, { stream: true }));
          $("genInfo").textContent = "Claude 生成中… " + st.text.length + " 文字";
          return pump();
        });
      }
      return pump();
    }).then(function (s) {
      if (s.error) throw new Error(s.error);
      if (s.stop === "refusal") throw new Error("Claude が依頼を辞退しました" + (s.stopDetails && s.stopDetails.category ? " (" + s.stopDetails.category + ")" : ""));
      if (s.stop === "max_tokens") throw new Error("出力が上限で途切れました");
      var html = extractHtml(s.text);
      if (!html) throw new Error("HTML 文書が返りませんでした");
      return { html: html, engine: model };
    });
  }

  async function go() {
    var text = $("thought").value.trim();
    if (!text) { $("specView").innerHTML = '<span class="err">依頼文 (思考入力) を書いてください。</span>'; return; }
    $("goBtn").disabled = true; $("goBtn").textContent = "電信中…";
    var state = {}; renderSteps(state);
    var M = telegraphMetrics(text), queue = [];
    anim.n = M.n; anim.prog = -1; anim.done = false;
    bada = new BadaInterp(function (ns, cmd) { queue.push(cmd); });
    var prog = BADAGPT_PROGRAM.replace(/^set entropy .*$/m, "set entropy = " + M.H.toFixed(4)).replace(/^set crossings .*$/m, "set crossings = " + M.n);
    try { bada.run(prog); } catch (e) { bada.out.push("! " + e.message); }
    /* 実行トレースは命令が画面を駆動するのに合わせて 1 行ずつ表示する */
    var trace = bada.out.slice(), tr = 0;
    while (tr < trace.length && !/^(Tele|GPT)::/.test(trace[tr])) tr++;
    bada.out = trace.slice(0, tr); blog();
    try {
      for (var qi = 0; qi < queue.length; qi++) {
        var cmd = queue[qi];
        state[cmd] = "run"; renderSteps(state); blog(trace[tr++]);
        if (cmd === "encode") { $("m-h").textContent = M.H.toFixed(3) + " bit"; $("m-xi").textContent = M.xi.toFixed(4); $("m-morse").textContent = M.morse; await sleep(220); }
        else if (cmd === "knot") { $("m-n").textContent = M.n + " / " + M.v2.toFixed(3); $("m-k").textContent = M.bracket; await sleep(220); }
        else if (cmd === "teleport") { $("m-fid").textContent = (M.fidelity * 100).toFixed(2) + "%"; await sleep(220); }
        else if (cmd === "graviton") { $("m-car").textContent = (M.carrierHz / 1e9).toFixed(3) + " GHz"; await sleep(160); }
        else if (cmd === "send") { for (var p = 0; p <= 1; p += 0.05) { anim.prog = p; await sleep(30); } anim.done = true; }
        else if (cmd === "comprehend") { cur = { metrics: M, spec: comprehend(text) }; renderSpec(cur.spec); await sleep(150); }
        else if (cmd === "plan") { blog("  → " + cur.spec.modules.map(function (m) { return m.id; }).join(" + ") + (cur.spec.fields.length ? " · fields " + cur.spec.fields.length : "")); await sleep(150); }
        else if (cmd === "generate") {
          $("genCard").classList.remove("hidden");
          var local = generateApp(cur.spec);
          cur.gen = local; cur.engine = "BadaGPT電信 内蔵エンジン (オフライン・規則ベース)";
          if (LS.get("apiKey", "")) {
            $("genInfo").textContent = "Claude に接続中…";
            try {
              var c = await claudeGenerate(cur.spec), cv2 = verifyApp(c.html, null);
              if (cv2.ok) { cur.gen = { html: c.html, slug: local.slug, file: local.file, modules: local.modules, bytes: utf8(c.html).length, lines: c.html.split("\n").length }; cur.engine = c.engine; }
              else blog("  ! Claude の出力が検証に不合格のため内蔵エンジンの結果を使います");
            } catch (e) { blog("  ! Claude: " + e.message + " — 内蔵エンジンの結果を使います"); }
          }
          $("genInfo").textContent = cur.engine + " · " + Math.round(cur.gen.bytes / 1024) + " KB · " + cur.gen.lines + " 行";
        }
        else if (cmd === "verify") {
          cur.ver = verifyApp(cur.gen.html, cur.spec);
          var errs = await runPreview(cur.gen.html);
          cur.runtime = errs === null ? { ok: true, detail: "読み込み完了の応答待ちがタイムアウト (エラーなし)" } : { ok: !errs.length, detail: errs.length ? errs[0] : "エラー 0 件" };
          $("checks").innerHTML = cur.ver.checks.concat([{ name: "実行時エラー (プレビュー)", ok: cur.runtime.ok, detail: cur.runtime.detail }]).map(function (c) {
            return '<li class="' + (c.ok ? "ok" : "ng") + '">' + escapeHtml(c.name) + ' <span class="muted">— ' + escapeHtml(c.detail) + "</span></li>";
          }).join("");
          if (!cur.ver.ok || !cur.runtime.ok) { state[cmd] = "fail"; renderSteps(state); continue; }
        }
        else if (cmd === "paper") {
          cur.paper = writePaper(cur.spec, cur.gen, cur.ver, { author: $("author").value.trim(), metrics: M, engine: cur.engine, runtime: cur.runtime, silent: lastSilent });
          cur.pdf = null;
          $("paperView").innerHTML = mdToHtml(cur.paper); $("paperCard").classList.remove("hidden");
        }
        state[cmd] = "done"; renderSteps(state);
      }
      renderCode();
      blog("✓ 錬成完了: " + cur.spec.title);
      var hist = LS.get("history", []);
      hist.unshift({ t: Date.now(), title: cur.spec.title, input: text, coverage: cur.spec.coverage });
      LS.set("history", hist.slice(0, 30)); renderHist();
    } catch (e) {
      blog("! " + (e && e.message || e));
    }
    $("goBtn").disabled = false; $("goBtn").textContent = "⚡ 電信して錬成 (Bada 実行)";
  }
  $("goBtn").onclick = go;

  $("vPhone").onclick = function () { $("preview").classList.add("phone"); this.classList.add("on"); $("vWide").classList.remove("on"); };
  $("vWide").onclick = function () { $("preview").classList.remove("phone"); this.classList.add("on"); $("vPhone").classList.remove("on"); };

  /* ───────── 保存 ───────── */
  function saveBytes(name, bytes, mime) {
    if (isCordova && window.resolveLocalFileSystemURL && window.cordova.file) {
      var dir = window.cordova.file.externalDataDirectory || window.cordova.file.dataDirectory;
      return new Promise(function (resolve, reject) {
        window.resolveLocalFileSystemURL(dir, function (d) {
          d.getFile(name, { create: true }, function (fe) {
            fe.createWriter(function (w) {
              w.onwriteend = function () { resolve("保存しました: " + fe.nativeURL.replace(/^file:\/\//, "")); };
              w.onerror = reject; w.write(new Blob([bytes], { type: mime }));
            }, reject);
          }, reject);
        }, reject);
      });
    }
    var a = document.createElement("a"), url = URL.createObjectURL(new Blob([bytes], { type: mime }));
    a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    return Promise.resolve("保存しました: " + name);
  }
  function report(p) {
    p.then(function (m) { $("outState").textContent = m; },
      function (e) { $("outState").innerHTML = "<span class=err>保存に失敗: " + escapeHtml(e && (e.message || e.code) || String(e)) + "</span>"; });
  }
  $("dlHtml").onclick = function () { if (cur && cur.gen) report(saveBytes(cur.gen.file + ".html", utf8(cur.gen.html), "text/html")); };
  $("dlMd").onclick = function () { if (cur && cur.paper) report(saveBytes(cur.gen.file + "-paper.md", utf8(cur.paper), "text/markdown")); };
  $("dlZip").onclick = function () {
    if (!cur || !cur.gen) return;
    report(saveBytes(cur.gen.file + "-project.zip", zipBuild(projectFiles(cur.spec, cur.gen.html, cur.paper)), "application/zip"));
  };
  $("dlPdf").onclick = function () {
    if (!cur || !cur.paper) return;
    if (!cur.pdf) cur.pdf = pdfFromJpegs(renderPages(cur.paper), cur.gen.slug);
    report(saveBytes(cur.gen.file + "-paper.pdf", cur.pdf, "application/pdf"));
  };

  /* ═══ ⑥ ソースコード化 ═══ */
  $("codeLang").innerHTML = CODE_LANGS.map(function (l) { return '<option value="' + l.id + '">' + l.label + "</option>"; }).join("");
  var codeGen = null;
  function renderCode() {
    if (!cur || !cur.spec) return;
    $("codeCard").classList.remove("hidden");
    codeGen = generateSource(cur.spec, $("codeLang").value);
    $("codeView").textContent = codeGen.files[0].data;
    $("codeNote").textContent = codeGen.note;
  }
  $("codeLang").onchange = renderCode;
  $("dlCode").onclick = function () {
    if (!cur || !cur.spec) return;
    if (!codeGen) renderCode();
    report(saveBytes(cur.gen.file + "." + codeGen.ext, utf8(codeGen.files[0].data), "text/plain"));
  };
  $("dlCodeZip").onclick = function () {
    if (!cur || !cur.spec) return;
    report(saveBytes(cur.gen.file + "-source.zip", zipBuild(sourceProject(cur.spec)), "application/zip"));
  };

  /* 論文を A4 画像ページに描く (日本語は端末のフォントで描画) */
  function renderPages(md) {
    var W = 1190, H = 1684, Mg = 100, pages = [], c, x, y;
    var FONT = "'Hiragino Mincho ProN','Yu Mincho','Noto Serif JP','Noto Serif CJK JP',serif";
    var GOTH = "'Hiragino Kaku Gothic ProN','Yu Gothic','Noto Sans JP','Noto Sans CJK JP',sans-serif";
    var st = {
      h1: { f: "bold 40px " + GOTH, lh: 58, before: 10 }, h2: { f: "bold 32px " + GOTH, lh: 48, before: 22 },
      h3: { f: "bold 27px " + GOTH, lh: 40, before: 14 }, p: { f: "24px " + FONT, lh: 40, before: 8 },
      li: { f: "24px " + FONT, lh: 38, before: 2, indent: 34 }, quote: { f: "23px " + FONT, lh: 36, before: 2, indent: 24 },
      code: { f: "20px monospace", lh: 30, before: 8, indent: 16 }, table: { f: "20px " + GOTH, lh: 32, before: 8 }, hr: { f: "20px sans-serif", lh: 24, before: 8 }
    };
    function newPage() { c = document.createElement("canvas"); c.width = W; c.height = H; x = c.getContext("2d"); x.fillStyle = "#fff"; x.fillRect(0, 0, W, H); x.fillStyle = "#111"; x.textBaseline = "top"; y = Mg; pages.push(c); }
    function wrap(text, maxW) {
      var out = [];
      String(text).split("\n").forEach(function (para) {
        var line = "";
        for (var i = 0; i < para.length; i++) {
          var ch = para[i];
          if (x.measureText(line + ch).width > maxW && line) {
            var sp = line.lastIndexOf(" ");
            if (/[A-Za-z0-9]/.test(ch) && sp > 0 && line.length - sp < 20) { out.push(line.slice(0, sp)); line = line.slice(sp + 1); } else { out.push(line); line = ""; }
          }
          line += ch;
        }
        out.push(line);
      });
      return out;
    }
    newPage();
    mdBlocks(md).forEach(function (b) {
      var s = st[b.type] || st.p, ind = s.indent || 0;
      x.font = s.f; y += s.before;
      if (b.type === "hr") { if (y + s.lh > H - Mg) newPage(); x.fillRect(Mg, y + 10, W - 2 * Mg, 1); y += s.lh; return; }
      if (b.type === "table") {
        /* 「#」列は細く、残りを等分 */
        var cols = b.rows[0] ? b.rows[0].length : 1, narrow = b.rows[0] && b.rows[0][0] === "#" ? 56 : 0;
        var cw = (W - 2 * Mg - narrow) / (cols - (narrow ? 1 : 0));
        var colX = function (ci) { return Mg + (narrow && ci > 0 ? narrow + (ci - 1) * cw : ci * cw); };
        var colW = function (ci) { return narrow && ci === 0 ? narrow : cw; };
        b.rows.forEach(function (r, ri) {
          x.font = (ri === 0 ? "bold " : "") + s.f;
          var cellLines = r.map(function (cell, ci) { return wrap(stripInline(cell), colW(ci) - 14); });
          var hgt = Math.max.apply(null, cellLines.map(function (l) { return l.length; })) * s.lh + 8;
          if (y + hgt > H - Mg) { newPage(); x.font = (ri === 0 ? "bold " : "") + s.f; }
          if (ri === 0) { x.fillStyle = "#eef1f6"; x.fillRect(Mg, y, W - 2 * Mg, hgt); x.fillStyle = "#111"; }
          cellLines.forEach(function (ls, ci) { ls.forEach(function (ln, li) { x.fillText(ln, colX(ci) + 6, y + 4 + li * s.lh); }); });
          y += hgt; x.fillStyle = "#ccd"; x.fillRect(Mg, y, W - 2 * Mg, 1); x.fillStyle = "#111";
        });
        return;
      }
      var text = b.type === "code" ? b.text : stripInline(b.text);
      wrap(text, W - 2 * Mg - ind - 16).forEach(function (ln, i) {
        if (y + s.lh > H - Mg) { newPage(); x.font = s.f; }
        if (b.type === "code") { x.fillStyle = "#f1f3f7"; x.fillRect(Mg + ind - 10, y - 4, W - 2 * Mg - ind + 10, s.lh); x.fillStyle = "#111"; }
        if (b.type === "quote") { x.fillStyle = "#9ab"; x.fillRect(Mg, y - 2, 4, s.lh); x.fillStyle = "#345"; }
        if (b.type === "li" && i === 0) x.fillText("・", Mg + 4, y);
        x.fillText(ln, Mg + ind, y); x.fillStyle = "#111"; y += s.lh;
      });
    });
    pages.forEach(function (pc, i) { var px = pc.getContext("2d"); px.font = "18px sans-serif"; px.fillStyle = "#888"; px.textAlign = "center"; px.fillText((i + 1) + " / " + pages.length, W / 2, H - 60); });
    return pages.map(function (pc) { return { w: W, h: H, jpeg: base64ToBytes(pc.toDataURL("image/jpeg", 0.9).split(",")[1]) }; });
  }

  /* ───────── 履歴 ───────── */
  function renderHist() {
    var h = LS.get("history", []);
    $("hist").innerHTML = h.length ? "" : '<div class="muted">まだありません。</div>';
    h.forEach(function (it) {
      var d = document.createElement("div");
      d.innerHTML = "<span>📨</span><b>" + escapeHtml(it.title) + "</b><i>" + Math.round(it.coverage * 100) + "% · " + new Date(it.t).toLocaleString("ja-JP") + "</i>";
      d.onclick = function () { $("thought").value = it.input; LS.set("draft", it.input); window.scrollTo(0, 0); };
      $("hist").appendChild(d);
    });
  }
  renderHist();

  /* ───────── 設定 ───────── */
  $("model").innerHTML = CLAUDE_MODELS.map(function (m) { return '<option value="' + m.id + '">' + m.label + "</option>"; }).join("");
  $("model").value = LS.get("model", "claude-opus-5-5");
  function keyState() { $("keyState").textContent = LS.get("apiKey", "") ? "キー保存済み — Claude で生成します" : "キーなし — 内蔵エンジンで生成します"; }
  $("saveKey").onclick = function () { LS.set("apiKey", $("apiKey").value.trim()); LS.set("model", $("model").value); $("apiKey").value = ""; keyState(); };
  $("clearKey").onclick = function () { LS.set("apiKey", ""); keyState(); };
  keyState();

  /* ═════════════ ⓪ サイレント・トーク (非言語思考入力) ═════════════ */
  var lastSilent = null;
  var CAT_LABEL = { tone: "感情・質感", domain: "領域", object: "対象", action: "動作", scale: "分量", platform: "環境" };
  var silentSeq = LS.get("silentSeq", []);
  function buildPalette() {
    var cats = {};
    SILENT_ATOMS.forEach(function (a) { (cats[a.cat] = cats[a.cat] || []).push(a); });
    var html = "";
    ["tone", "domain", "object", "action", "scale", "platform"].forEach(function (c) {
      if (!cats[c]) return;
      html += '<div class="spal-grp"><span class="lbl">' + CAT_LABEL[c] + '</span><div class="gl">' +
        cats[c].map(function (a) { return '<div class="sglyph" data-id="' + a.id + '" title="' + a.id + '">' + a.g + "</div>"; }).join("") + "</div></div>";
    });
    $("silent-palette").innerHTML = html;
    $("silent-palette").onclick = function (e) {
      var t = e.target.closest(".sglyph"); if (!t) return;
      silentSeq.push(t.getAttribute("data-id")); saveSeq(); renderStrip();
    };
  }
  function saveSeq() { LS.set("silentSeq", silentSeq); }
  function renderStrip() {
    var el = $("silent-strip");
    if (!silentSeq.length) { el.innerHTML = '<span class="muted">グリフをタップして並べてください。</span>'; return; }
    el.innerHTML = silentSeq.map(function (id, i) { var a = ATOM_BY_ID[id]; return '<span class="schip" data-i="' + i + '" title="タップで削除">' + (a ? a.g : "?") + "</span>"; }).join("");
    el.onclick = function (e) { var t = e.target.closest(".schip"); if (!t) return; silentSeq.splice(+t.getAttribute("data-i"), 1); saveSeq(); renderStrip(); };
  }
  buildPalette(); renderStrip();
  $("silent-undo").onclick = function () { silentSeq.pop(); saveSeq(); renderStrip(); };
  $("silent-clear").onclick = function () { silentSeq = []; saveSeq(); renderStrip(); };

  /* 🌫 思いを描く面: イメージした思いを連続した動きで入力。正規化した {x,y,t} を記録する。 */
  var gcv = $("silent-field"), gctx = gcv.getContext("2d"), gstrokes = [], gcur = null, gdrawing = false, gstart = 0;
  function gfit() {
    gcv.width = gcv.clientWidth; gcv.height = 240; redrawField();
  }
  function redrawField() {
    gctx.clearRect(0, 0, gcv.width, gcv.height);
    gctx.lineWidth = 2.5; gctx.lineCap = "round"; gctx.lineJoin = "round";
    gstrokes.forEach(function (st, si) {
      gctx.strokeStyle = "hsla(" + (200 + si * 24) % 360 + ",90%,68%,.9)"; gctx.beginPath();
      st.forEach(function (p, i) { var x = p.x * gcv.width, y = p.y * gcv.height; if (i) gctx.lineTo(x, y); else gctx.moveTo(x, y); });
      gctx.stroke();
    });
  }
  function gpt(e) { var r = gcv.getBoundingClientRect(); return { x: Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)), y: Math.max(0, Math.min(1, (e.clientY - r.top) / r.height)), t: (performance.now() - gstart) }; }
  function fieldStat() {
    var n = gstrokes.reduce(function (a, s) { return a + s.length; }, 0);
    $("silent-field-stat").textContent = gstrokes.length ? ("ひと筆 " + gstrokes.length + " 本・点 " + n + " 個を描きました。") : "まだ何も描かれていません。";
  }
  gcv.onpointerdown = function (e) { if (!gstart) gstart = performance.now(); gdrawing = true; gcur = [gpt(e)]; gstrokes.push(gcur); gcv.setPointerCapture(e.pointerId); };
  gcv.onpointermove = function (e) { if (!gdrawing) return; gcur.push(gpt(e)); redrawField(); };
  gcv.onpointerup = gcv.onpointercancel = function () { gdrawing = false; fieldStat(); };
  $("silent-field-undo").onclick = function () { gstrokes.pop(); redrawField(); fieldStat(); };
  $("silent-field-clear").onclick = function () { gstrokes = []; gstart = 0; redrawField(); fieldStat(); };
  /* リズムをタップ: 点の連なりとして記録 (無言のリズム入力) */
  $("silent-tap").onclick = function () {
    if (!gstart) gstart = performance.now();
    var t = performance.now() - gstart, x = 0.5 + (Math.sin(t / 130) * 0.18), y = 0.5 + (Math.cos(t / 90) * 0.18);
    gstrokes.push([{ x: x, y: y, t: t }, { x: x + 0.01, y: y + 0.01, t: t + 10 }]);
    redrawField(); fieldStat();
  };
  setTimeout(gfit, 0); addEventListener("resize", function () { setTimeout(gfit, 0); });
  function hasGesture() { return gstrokes.reduce(function (a, s) { return a + s.length; }, 0) >= 3; }
  function drawHeat(cv, rows, absMax) {
    var dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight || 90;
    cv.width = W * dpr; cv.height = H * dpr; var x = cv.getContext("2d"); x.setTransform(dpr, 0, 0, dpr, 0, 0); x.clearRect(0, 0, W, H);
    if (!rows.length) return;
    var r = rows.length, c = rows[0].length, cw = W / c, ch = H / r;
    for (var i = 0; i < r; i++) for (var j = 0; j < c; j++) {
      var v = rows[i][j] / (absMax || 1), hue = v >= 0 ? 200 : 20, light = 20 + Math.min(60, Math.abs(v) * 60);
      x.fillStyle = "hsl(" + hue + ",80%," + light + "%)"; x.fillRect(j * cw, i * ch, cw + 0.5, ch + 0.5);
    }
  }
  function volOpt() { var v = +$("silent-vol").value; return v > 0 ? { targetChars: v, images: 3 } : { images: 3 }; }
  function renderReadout(readout) {
    $("silent-readout").innerHTML = (readout && readout.length)
      ? readout.map(function (r) { return '<div class="rrow"><i>' + escHtml(r.label) + '</i><b>' + escHtml(r.value) + '</b><span>' + escHtml(r.meant) + "</span></div>"; }).join("")
      : '<div class="muted">グリフのみから構成しました (動きの読み取りはありません)。</div>';
  }
  function escHtml(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function runSilent() {
    var proc, readout, srcLabel;
    if (hasGesture()) {
      proc = gestureProcess(gstrokes, volOpt());
      /* グリフも足されていれば補いとして末尾に加える */
      if (silentSeq.length) { proc = silentProcess(proc.atoms.concat(silentSeq).concat(proc.seq.filter(function (s) { return s.indexOf("g:") === 0; })), volOpt()); }
      readout = (proc.readout || []); srcLabel = "描いた思い" + (silentSeq.length ? " + グリフ " + silentSeq.length + " 個" : "");
    } else if (silentSeq.length) {
      proc = silentProcess(silentSeq.slice(), volOpt()); readout = null; srcLabel = "グリフ " + silentSeq.length + " 個";
    } else {
      $("silent-outstate").innerHTML = '<span class="err">上の面に思いを描いてください (グリフだけでも可)。</span>'; return;
    }
    lastSilent = { seq: proc.seq, request: proc.request, document: proc.document, bada: proc.bada, imagery: proc.imagery, tags: proc.tags, readout: readout, features: proc.features };
    $("silent-out").classList.remove("hidden");
    renderReadout(readout);
    var amax = 0; proc.enc.seq.forEach(function (row) { row.forEach(function (v) { amax = Math.max(amax, Math.abs(v)); }); });
    drawHeat($("silent-latent"), proc.enc.seq, amax);
    drawHeat($("silent-att"), proc.enc.attention.length ? proc.enc.attention.slice(0, proc.seq.length) : [[0]], 1);
    $("silent-imgs").innerHTML = proc.imagery.join("");
    $("silent-req").textContent = proc.request;
    $("silent-doc").innerHTML = mdToHtml(proc.document.markdown);
    $("silent-doc-sum").textContent = "📖 思いを展開した文章 (" + proc.document.chars.toLocaleString("ja-JP") + " 字 / 目標 " + proc.document.target.toLocaleString("ja-JP") + " 字)";
    $("silent-bada").textContent = proc.bada;
    $("silent-outstate").textContent = srcLabel + " → latent " + proc.enc.pooled.length + " 次元に変換しました。「錬成」で BadaGPT がアプリを作ります。";
  }
  $("silent-run").onclick = runSilent;
  $("silent-send").onclick = function () {
    if (!lastSilent) runSilent();
    if (!lastSilent) return;
    $("thought").value = lastSilent.request; LS.set("draft", lastSilent.request);
    $("thought").scrollIntoView({ behavior: "smooth", block: "center" });
    go();
  };
  function sfile() { return "silent-" + (lastSilent ? lastSilent.seq.filter(function (s) { return s.indexOf("g:") < 0 && s.indexOf("sketch") < 0 && ATOM_BY_ID[s]; }).slice(0, 4).join("-") || "thought" : "thought"); }
  $("silent-dl-doc").onclick = function () { if (lastSilent) report(saveBytes(sfile() + ".md", utf8(lastSilent.document.markdown), "text/markdown")); };
  $("silent-dl-docpdf").onclick = function () { if (lastSilent) report(saveBytes(sfile() + ".pdf", pdfFromJpegs(renderPages(lastSilent.document.markdown), sfile()), "application/pdf")); };
  $("silent-dl-bada").onclick = function () { if (lastSilent) report(saveBytes("silent.bada", utf8(lastSilent.bada), "text/plain")); };
  $("silent-dl-img").onclick = function () {
    if (!lastSilent) return;
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="220" height="' + (160 * lastSilent.imagery.length) + '">' +
      lastSilent.imagery.map(function (s, i) { return '<g transform="translate(0,' + (i * 160) + ')">' + s.replace(/<\/?svg[^>]*>/g, "") + "</g>"; }).join("") + "</svg>";
    report(saveBytes(sfile() + "-imagery.svg", utf8(svg), "image/svg+xml"));
  };
})();
