/*
 * ui.js — BadaGPT改 の画面・センサー・通信 (engine.js の上で動く)
 */
"use strict";
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var isCordova = !!window.cordova;

  /* ───────────── 保存 (記憶するときだけ localStorage) ───────────── */
  function store(remember) { try { return remember ? localStorage : sessionStorage; } catch (e) { return null; } }
  function getPref(k) {
    try { return localStorage.getItem(k) || sessionStorage.getItem(k) || ""; } catch (e) { return ""; }
  }
  function setPref(k, v, remember) {
    try { localStorage.removeItem(k); sessionStorage.removeItem(k); } catch (e) {}
    var s = store(remember); if (s && v) try { s.setItem(k, v); } catch (e) {}
  }

  /* ───────────── タブ ───────────── */
  function showTab(name) {
    Array.prototype.forEach.call(document.querySelectorAll("#tabs button"), function (b) {
      b.classList.toggle("on", b.getAttribute("data-tab") === name);
    });
    Array.prototype.forEach.call(document.querySelectorAll("section.tab"), function (s) {
      s.classList.toggle("on", s.id === "tab-" + name);
    });
    if (name === "bio") drawGamma();
  }
  $("tabs").addEventListener("click", function (e) {
    var t = e.target.getAttribute && e.target.getAttribute("data-tab");
    if (t) showTab(t);
  });

  /* ───────────── 設定 ───────────── */
  MODELS.forEach(function (m) {
    var o = document.createElement("option"); o.value = m.id; o.textContent = m.label; $("model").appendChild(o);
  });
  $("ver").textContent = KAI_VERSION;
  $("apiKey").value = getPref("kai_api_key");
  $("rememberKey").checked = (function () { try { return !!localStorage.getItem("kai_api_key"); } catch (e) { return false; } })();
  $("model").value = getPref("kai_model") || "claude-opus-5-5";
  $("effort").value = getPref("kai_effort") || "high";
  $("ghRepo").value = getPref("kai_gh_repo");
  $("ghBranch").value = getPref("kai_gh_branch") || "badagpt-kai-apps";
  $("ghToken").value = getPref("kai_gh_token");
  $("rememberGh").checked = (function () { try { return !!localStorage.getItem("kai_gh_token"); } catch (e) { return false; } })();
  function saveSettings() {
    setPref("kai_api_key", $("apiKey").value.trim(), $("rememberKey").checked);
    setPref("kai_model", $("model").value, true);
    setPref("kai_effort", $("effort").value, true);
    setPref("kai_gh_repo", $("ghRepo").value.trim(), true);
    setPref("kai_gh_branch", $("ghBranch").value.trim(), true);
    setPref("kai_gh_token", $("ghToken").value.trim(), $("rememberGh").checked);
    updateModeNote();
  }
  ["apiKey", "model", "effort", "ghRepo", "ghBranch", "ghToken", "rememberKey", "rememberGh"].forEach(function (id) {
    $(id).addEventListener("change", saveSettings);
  });
  function updateModeNote() {
    $("modeNote").textContent = $("apiKey").value.trim()
      ? "Claude (" + $("model").value + ", effort " + $("effort").value + ") で生成します。安全上の理由で拒否された場合は代替モデルへ自動で切り替わります。"
      : "API キー未設定のため、端末内の簡易生成 (オフライン) で作ります。本格的な生成は ④ 設定 で API キーを入れてください。";
  }
  updateModeNote();

  $("target").addEventListener("change", function () {
    $("langBox").style.display = $("target").value === "source" ? "" : "none";
  });

  /* ───────────── 音声入力 ───────────── */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition, rec = null;
  $("voiceBtn").addEventListener("click", function () {
    if (!SR) { $("voiceState").textContent = "この端末の WebView は音声認識に対応していません。キーボードの音声入力 (マイクキー) をお使いください。"; return; }
    if (rec) { rec.stop(); return; }
    rec = new SR(); rec.lang = "ja-JP"; rec.interimResults = true; rec.continuous = true;
    var base = $("req").value;
    rec.onresult = function (e) {
      var s = "";
      for (var i = 0; i < e.results.length; i++) s += e.results[i][0].transcript;
      $("req").value = (base ? base + "\n" : "") + s;
    };
    rec.onerror = function (e) { $("voiceState").textContent = "音声認識エラー: " + e.error; };
    rec.onend = function () { rec = null; $("voiceBtn").textContent = "🎙 音声入力"; $("voiceState").textContent = ""; };
    rec.start(); $("voiceBtn").textContent = "■ 止める"; $("voiceState").textContent = "聞き取り中…";
  });

  /* ───────────── スケッチ ───────────── */
  var sk = $("sketch"), sctx = sk.getContext("2d"), drawing = false, sketched = false;
  function clearSketch() { sctx.fillStyle = "#fff"; sctx.fillRect(0, 0, sk.width, sk.height); sketched = false; }
  clearSketch();
  function pos(e) {
    var r = sk.getBoundingClientRect();
    return [(e.clientX - r.left) * sk.width / r.width, (e.clientY - r.top) * sk.height / r.height];
  }
  sk.addEventListener("pointerdown", function (e) {
    drawing = true; sk.setPointerCapture(e.pointerId);
    var p = pos(e); sctx.beginPath(); sctx.moveTo(p[0], p[1]);
  });
  sk.addEventListener("pointermove", function (e) {
    if (!drawing) return;
    var p = pos(e);
    sctx.strokeStyle = $("penColor").value; sctx.lineWidth = +$("penSize").value;
    sctx.lineCap = "round"; sctx.lineJoin = "round";
    sctx.lineTo(p[0], p[1]); sctx.stroke(); sketched = true;
  });
  ["pointerup", "pointercancel"].forEach(function (ev) { sk.addEventListener(ev, function () { drawing = false; }); });
  $("sketchClear").addEventListener("click", clearSketch);

  /* ───────────── 写真 (長辺 1024px の JPEG に縮小) ───────────── */
  var photos = [];
  $("photo").addEventListener("change", function () {
    photos = []; $("thumbs").innerHTML = "";
    Array.prototype.slice.call($("photo").files, 0, 4).forEach(function (f) {
      var img = new Image(), url = URL.createObjectURL(f);
      img.onload = function () {
        var s = Math.min(1, 1024 / Math.max(img.width, img.height));
        var c = document.createElement("canvas"); c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        var d = c.toDataURL("image/jpeg", 0.85); photos.push(d);
        var t = new Image(); t.src = d; $("thumbs").appendChild(t);
        URL.revokeObjectURL(url);
      };
      img.src = url;
    });
  });

  /* ───────────── Android の実行時権限 ───────────── */
  function androidPerms(list) {
    return new Promise(function (resolve) {
      var P = isCordova && window.cordova.plugins && window.cordova.plugins.permissions;
      if (!P) return resolve(true);
      P.requestPermissions(list.map(function (n) { return P[n]; }), function (s) { resolve(!!(s && s.hasPermission)); },
                           function () { resolve(false); });
    });
  }

  /* ───────────── バイオフィードバック ───────────── */
  var bio = { bpm: NaN, rmssd: NaN, breath: NaN, calm: NaN };
  var ppg = [], breathS = [], camStream = null, micStream = null, audio = null, sound = null, lastBeat = 0, hueShift = 0;

  function ensureAudio() {
    if (!audio) { var AC = window.AudioContext || window.webkitAudioContext; audio = AC ? new AC() : null; }
    if (audio && audio.state === "suspended") audio.resume();
    return audio;
  }

  function fmt(x, d, unit) { return isFinite(x) ? x.toFixed(d) + unit : "—"; }
  function updateMeters() {
    bio.calm = calmIndex(bio.rmssd, bio.breath);
    $("mBpm").textContent = fmt(bio.bpm, 0, " bpm");
    $("mRmssd").textContent = fmt(bio.rmssd, 0, " ms");
    $("mBreath").textContent = fmt(bio.breath, 1, " /分");
    $("mCalm").textContent = fmt(bio.calm, 0, "");
    if (sound) {
      /* 呼吸が遅く落ち着くほど、ドローンの唸り (両耳の周波数差) をゆっくりにする */
      var beat = isFinite(bio.calm) ? 10 - 6 * bio.calm / 100 : 8;
      sound.r.frequency.setTargetAtTime(sound.base + beat, audio.currentTime, 0.5);
    }
  }

  function beep() {
    if (!sound) return;
    var t = audio.currentTime, o = audio.createOscillator(), g = audio.createGain();
    o.type = "sine";
    o.frequency.value = 330 + (isFinite(bio.calm) ? bio.calm * 2 : 100);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.18, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.25);
    o.connect(g).connect(audio.destination); o.start(t); o.stop(t + 0.3);
  }

  $("soundBtn").addEventListener("click", function () {
    var a = ensureAudio(); if (!a) return;
    if (sound) {
      sound.l.stop(); sound.r.stop(); sound = null; $("soundBtn").textContent = "🔈 音を鳴らす"; return;
    }
    var base = 174, merger = a.createChannelMerger(2), g = a.createGain();
    var l = a.createOscillator(), r = a.createOscillator();
    l.frequency.value = base; r.frequency.value = base + 8;
    l.connect(merger, 0, 0); r.connect(merger, 0, 1);
    g.gain.value = 0.06; merger.connect(g).connect(a.destination);
    l.start(); r.start();
    sound = { l: l, r: r, g: g, base: base };
    $("soundBtn").textContent = "🔇 音を止める";
    updateMeters();
  });

  /* 心拍 (カメラ PPG) */
  var vid = document.createElement("video"); vid.muted = true; vid.setAttribute("playsinline", "");
  var small = document.createElement("canvas"); small.width = 40; small.height = 30;
  var smallCtx = small.getContext("2d", { willReadFrequently: true });

  $("camBtn").addEventListener("click", function () {
    if (camStream) { stopCam(); return; }
    ensureAudio();
    androidPerms(["CAMERA"]).then(function () {
      return navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: 320, height: 240 }, audio: false });
    }).then(function (s) {
      camStream = s; vid.srcObject = s; vid.play();
      var track = s.getVideoTracks()[0];
      if (track.applyConstraints) track.applyConstraints({ advanced: [{ torch: true }] }).catch(function () {});
      ppg = []; $("camBtn").textContent = "■ 心拍の測定を止める";
      $("bioState").textContent = "指先をカメラとライトに当ててください…";
      requestAnimationFrame(camLoop);
    }).catch(function (e) { $("bioState").textContent = "カメラを使えません: " + (e && e.message || e); });
  });
  function stopCam() {
    camStream.getTracks().forEach(function (t) { t.stop(); }); camStream = null;
    $("camBtn").textContent = "❤ 心拍を測る (カメラ)";
  }
  var lastPpgAnalysis = 0;
  function camLoop() {
    if (!camStream) return;
    if (vid.readyState >= 2) {
      smallCtx.drawImage(vid, 0, 0, small.width, small.height);
      var d = smallCtx.getImageData(10, 7, 20, 16).data, r = 0, g = 0;
      for (var i = 0; i < d.length; i += 4) { r += d[i]; g += d[i + 1]; }
      var n = d.length / 4; r /= n; g /= n;
      var t = performance.now() / 1000, finger = r > 60 && r > g * 1.4;
      if (finger) {
        ppg.push({ t: t, v: r });
        while (ppg.length && t - ppg[0].t > 20) ppg.shift();
      } else if (ppg.length) { ppg = []; }
      if (t - lastPpgAnalysis > 0.5) {
        lastPpgAnalysis = t;
        if (!finger) $("bioState").textContent = "指先がカメラを覆っていないようです (画面が赤く明るくなる位置に)。";
        else {
          var res = ppgAnalyze(ppg);
          if (isFinite(res.bpm)) { bio.bpm = res.bpm; bio.rmssd = res.rmssd; $("bioState").textContent = "測定中 — 静止したまま続けると精度が上がります。"; }
          else $("bioState").textContent = "脈波を集めています… (" + Math.round(ppg.length ? t - ppg[0].t : 0) + " 秒)";
          var pk = res.peaks[res.peaks.length - 1];
          if (pk && pk.t > lastBeat + 0.3) { lastBeat = pk.t; beep(); hueShift += 25; drawGamma(); }
          updateMeters();
        }
      }
      drawWave();
    }
    requestAnimationFrame(camLoop);
  }
  function drawWave() {
    var c = $("wave"), x = c.getContext("2d"), W = c.width, H = c.height;
    x.fillStyle = "#05070b"; x.fillRect(0, 0, W, H);
    if (ppg.length < 10) return;
    var tEnd = ppg[ppg.length - 1].t, pts = ppg.filter(function (p) { return tEnd - p.t < 6; });
    var vs = pts.map(function (p) { return -p.v; }), mn = Math.min.apply(null, vs), mx = Math.max.apply(null, vs);
    x.strokeStyle = "#ff6b8a"; x.lineWidth = 2; x.beginPath();
    pts.forEach(function (p, i) {
      var px = W - (tEnd - p.t) / 6 * W, py = H - 10 - ((-p.v - mn) / ((mx - mn) || 1)) * (H - 20);
      if (i) x.lineTo(px, py); else x.moveTo(px, py);
    });
    x.stroke();
  }

  /* 呼吸 (マイク) */
  $("micBtn").addEventListener("click", function () {
    if (micStream) { micStream.getTracks().forEach(function (t) { t.stop(); }); micStream = null; $("micBtn").textContent = "🌬 呼吸を測る (マイク)"; return; }
    var a = ensureAudio(); if (!a) return;
    androidPerms(["RECORD_AUDIO", "MODIFY_AUDIO_SETTINGS"]).then(function () {
      return navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
    }).then(function (s) {
      micStream = s; breathS = [];
      var src = a.createMediaStreamSource(s), an = a.createAnalyser(); an.fftSize = 1024;
      /* 呼吸音は主に低〜中域の息のノイズ。高域を落として声や環境音の影響を減らす */
      var lp = a.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 1500;
      src.connect(lp).connect(an);
      var buf = new Float32Array(an.fftSize), lastA = 0;
      $("micBtn").textContent = "■ 呼吸の測定を止める";
      (function loop() {
        if (!micStream) return;
        an.getFloatTimeDomainData(buf);
        var s2 = 0; for (var i = 0; i < buf.length; i++) s2 += buf[i] * buf[i];
        var t = performance.now() / 1000;
        breathS.push({ t: t, v: Math.sqrt(s2 / buf.length) });
        while (breathS.length && t - breathS[0].t > 45) breathS.shift();
        if (t - lastA > 2) {
          lastA = t;
          var br = breathAnalyze(breathS);
          if (isFinite(br)) bio.breath = br;
          if (!camStream) $("bioState").textContent = isFinite(br) ? "呼吸を測定中…" : "呼吸のリズムを集めています… (" + Math.round(breathS.length ? t - breathS[0].t : 0) + " 秒)";
          updateMeters();
        }
        requestAnimationFrame(loop);
      })();
    }).catch(function (e) { $("bioState").textContent = "マイクを使えません: " + (e && e.message || e); });
  });

  /* ガンマ関数の模様 (Γ(z) の値は一度だけ計算してキャッシュ) */
  var gammaCache = null;
  function drawGamma() {
    var c = $("gamma"), x = c.getContext("2d"), W = c.width, H = c.height;
    if (!gammaCache) {
      gammaCache = new Float32Array(W * H * 2);
      for (var j = 0; j < H; j++) for (var i = 0; i < W; i++) {
        var re = -4 + 8 * i / (W - 1), im = 2.5 - 5 * j / (H - 1);
        var g = gammaC(re, im), k = (j * W + i) * 2;
        gammaCache[k] = Math.atan2(g[1], g[0]);
        gammaCache[k + 1] = Math.log(Math.hypot(g[0], g[1]) + 1e-12);
      }
    }
    var img = x.createImageData(W, H), sat = isFinite(bio.calm) ? 0.35 + 0.65 * bio.calm / 100 : 0.8;
    for (var p = 0; p < W * H; p++) {
      var hue = ((gammaCache[p * 2] / (2 * Math.PI) + 0.5) * 360 + hueShift) % 360;
      var light = 1 / (1 + Math.exp(-gammaCache[p * 2 + 1] / 1.5));
      var rgb = hsl(hue, sat, 0.12 + 0.7 * light);
      img.data[p * 4] = rgb[0]; img.data[p * 4 + 1] = rgb[1]; img.data[p * 4 + 2] = rgb[2]; img.data[p * 4 + 3] = 255;
    }
    x.putImageData(img, 0, 0);
  }
  function hsl(h, s, l) {
    var c = (1 - Math.abs(2 * l - 1)) * s, hp = h / 60, xx = c * (1 - Math.abs(hp % 2 - 1)), m = l - c / 2, r = 0, g = 0, b = 0;
    if (hp < 1) { r = c; g = xx; } else if (hp < 2) { r = xx; g = c; } else if (hp < 3) { g = c; b = xx; }
    else if (hp < 4) { g = xx; b = c; } else if (hp < 5) { r = xx; b = c; } else { r = c; b = xx; }
    return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
  }

  /* ───────────── 生成 ───────────── */
  var project = null, pdfBytes = null, busy = false;

  function log(s) { $("log").textContent = s; $("log").scrollTop = $("log").scrollHeight; }

  function collectInput() {
    var text = $("req").value.trim(), name = $("name").value.trim();
    if (!name) name = (text.split(/[\n。.!?！？]/)[0] || "BadaGPT改アプリ").slice(0, 24);
    var images = [];
    if ($("useSketch").checked && sketched) images.push(sk.toDataURL("image/png"));
    images = images.concat(photos);
    var b = $("useBio").checked && (isFinite(bio.bpm) || isFinite(bio.breath)) ? bio : null;
    return { text: text, name: name, target: $("target").value, lang: $("lang").value.trim(), images: images, bio: b };
  }

  async function generateWithClaude(input) {
    var req = claudeRequest({
      apiKey: $("apiKey").value.trim(), model: $("model").value, effort: $("effort").value,
      system: buildSystemPrompt(input.target, input.lang), content: buildUserContent(input)
    });
    var res = await fetch(req.url, { method: "POST", headers: req.headers, body: JSON.stringify(req.body) });
    if (!res.ok) {
      var msg = res.status + " " + res.statusText;
      try { var j = await res.json(); if (j.error && j.error.message) msg += " — " + j.error.message; } catch (e) {}
      throw new Error("Claude API エラー: " + msg);
    }
    var st = sseNew(), reader = res.body.getReader(), dec = new TextDecoder(), lastPaint = 0;
    for (;;) {
      var r = await reader.read();
      if (r.done) break;
      sseFeed(st, dec.decode(r.value, { stream: true }));
      if (st.error) throw new Error("Claude API エラー: " + st.error);
      var now = Date.now();
      if (now - lastPaint > 150) { lastPaint = now; log(st.text || "(考え中…)"); $("genState").textContent = "生成中… " + st.text.length + " 文字"; }
    }
    log(st.text);
    if (st.stop === "refusal") {
      throw new Error("この依頼は安全上の理由で生成されませんでした" +
        (st.stopDetails && st.stopDetails.explanation ? " (" + st.stopDetails.explanation + ")" : "") + "。");
    }
    var parsed = parseFiles(st.text);
    if (st.stop === "max_tokens" || parsed.truncated) parsed.warn = "出力が長すぎて途中で切れました。依頼を小さく分けてください。";
    return parsed;
  }

  $("genBtn").addEventListener("click", async function () {
    if (busy) return;
    saveSettings();
    var input = collectInput();
    if (!input.text && !input.images.length) { $("genState").textContent = "イメージを言葉かスケッチで入力してください。"; return; }
    busy = true; $("genBtn").disabled = true; project = null; pdfBytes = null;
    $("genState").textContent = "生成を開始…"; $("outState").textContent = "";
    showTab("output"); log("(生成中…)");
    try {
      var parsed;
      if ($("apiKey").value.trim()) parsed = await generateWithClaude(input);
      else {
        var files = input.target === "pdf" ? localGenerateDoc(input)
                  : input.target === "source" ? [{ path: "README.md", content: "# " + input.name + "\n\n" + input.text + "\n\n(任意言語のソースコード生成には ④ 設定 で Claude API キーが必要です。)\n" }]
                  : localGenerateApp(input);
        parsed = { files: files, notes: "端末内の簡易生成 (オフライン) で作りました。", truncated: false };
        log(parsed.notes + "\n\n" + files.map(function (f) { return "=== FILE: " + f.path + " ===\n" + f.content + "\n=== END FILE ==="; }).join("\n"));
      }
      if (!parsed.files.length) throw new Error("ファイルが生成されませんでした。依頼を具体的にして再試行してください。");
      var generated = parsed.files.slice();
      if (input.target === "pdf") {
        var md = (generated.filter(function (f) { return /\.md$/i.test(f.path); })[0] || generated[0]).content;
        var pages = renderDocPages(md);
        pdfBytes = pdfFromJpegs(pages, slugify(input.name));
        generated.push({ path: "document.pdf", data: pdfBytes });
        showPdfPreview(pages);
      }
      var slug = slugify(input.name);
      project = { name: input.name, slug: slug, target: input.target,
                  files: assembleProject({ name: input.name, slug: slug, target: input.target }, generated) };
      renderFiles();
      $("genState").textContent = "完了 — ③ 生成結果 を見てください。";
      $("outState").innerHTML = (parsed.warn ? "<span class=warn>" + escapeHtml(parsed.warn) + "</span><br>" : "") +
        (TARGETS[input.target].packaging
          ? "APK / EXE を作るには「GitHub にプッシュしてビルド」を押すか、ZIP をリポジトリに入れて push してください (Actions が自動でビルドします)。"
          : "ZIP で保存できます。");
    } catch (e) {
      $("genState").innerHTML = "<span class=err>" + escapeHtml(e.message || String(e)) + "</span>";
      $("outState").innerHTML = "<span class=err>" + escapeHtml(e.message || String(e)) + "</span>";
    } finally { busy = false; $("genBtn").disabled = false; }
  });

  function renderFiles() {
    var ul = $("files"); ul.innerHTML = "";
    project.files.forEach(function (f) {
      var li = document.createElement("li"), code = document.createElement("code");
      var size = typeof f.data === "string" ? utf8(f.data).length : f.data.length;
      code.textContent = f.path + "  (" + size.toLocaleString() + " B)";
      li.appendChild(code);
      if (typeof f.data === "string") {
        var pv = document.createElement("button"); pv.className = "b"; pv.textContent = "見る";
        pv.onclick = function () {
          $("previewCard").style.display = ""; $("previewTitle").textContent = f.path;
          $("pdfPages").innerHTML = ""; $("preview").style.display = ""; $("preview").textContent = f.data;
        };
        var cp = document.createElement("button"); cp.className = "b"; cp.textContent = "コピー";
        cp.onclick = function () {
          (navigator.clipboard ? navigator.clipboard.writeText(f.data) : Promise.reject()).then(
            function () { cp.textContent = "コピー済"; }, function () { cp.textContent = "コピー不可"; });
        };
        li.appendChild(pv); li.appendChild(cp);
      }
      ul.appendChild(li);
    });
    $("zipBtn").disabled = false;
    $("pushBtn").disabled = false;
    $("pdfBtn").style.display = pdfBytes ? "" : "none"; $("pdfBtn").disabled = !pdfBytes;
  }

  /* ───────────── PDF のページ描画 (日本語も端末のフォントで描ける) ───────────── */
  function renderDocPages(md) {
    var W = 1190, H = 1684, M = 100, pages = [], c, x, y;
    var styles = {
      h1: { f: "bold 46px sans-serif", lh: 66, before: 24 }, h2: { f: "bold 36px sans-serif", lh: 52, before: 20 },
      h3: { f: "bold 30px sans-serif", lh: 44, before: 14 }, p: { f: "26px sans-serif", lh: 40, before: 10 },
      li: { f: "26px sans-serif", lh: 40, before: 4, indent: 36 }, code: { f: "21px monospace", lh: 30, before: 10, indent: 20 },
      hr: { f: "26px sans-serif", lh: 30, before: 10 }
    };
    function newPage() {
      c = document.createElement("canvas"); c.width = W; c.height = H; x = c.getContext("2d");
      x.fillStyle = "#fff"; x.fillRect(0, 0, W, H); x.fillStyle = "#111"; x.textBaseline = "top"; y = M;
      pages.push(c);
    }
    function wrap(text, maxW) {
      var out = [];
      String(text).split("\n").forEach(function (para) {
        var line = "";
        for (var i = 0; i < para.length; i++) {
          var ch = para[i];
          if (x.measureText(line + ch).width > maxW && line) {
            /* 英単語の途中で切らない (空白まで戻る) */
            var sp = line.lastIndexOf(" ");
            if (/[A-Za-z0-9]/.test(ch) && sp > 0 && line.length - sp < 20) { out.push(line.slice(0, sp)); line = line.slice(sp + 1); }
            else { out.push(line); line = ""; }
          }
          line += ch;
        }
        out.push(line);
      });
      return out;
    }
    newPage();
    mdBlocks(md).forEach(function (b) {
      var s = styles[b.type] || styles.p, ind = s.indent || 0;
      x.font = s.f; y += s.before;
      if (b.type === "hr") {
        if (y + s.lh > H - M) newPage();
        x.fillRect(M, y + 12, W - 2 * M, 2); y += s.lh; return;
      }
      var text = b.type === "code" ? b.text : stripInline(b.text);
      var lines = wrap(text, W - 2 * M - ind - (b.type === "code" ? 20 : 0));
      lines.forEach(function (ln, i) {
        if (y + s.lh > H - M) { newPage(); x.font = s.f; }
        if (b.type === "code") { x.fillStyle = "#f1f3f7"; x.fillRect(M + ind - 10, y - 4, W - 2 * M - ind + 10, s.lh); x.fillStyle = "#111"; }
        if (b.type === "li" && i === 0) x.fillText("•", M + 8, y);
        x.fillText(ln, M + ind, y); y += s.lh;
      });
    });
    pages.forEach(function (pc, i) {
      var px = pc.getContext("2d"); px.font = "20px sans-serif"; px.fillStyle = "#888";
      px.fillText((i + 1) + " / " + pages.length, W / 2 - 20, H - 60);
    });
    return pages.map(function (pc) {
      return { canvas: pc, w: W, h: H, jpeg: base64ToBytes(pc.toDataURL("image/jpeg", 0.9).split(",")[1]) };
    });
  }
  function showPdfPreview(pages) {
    $("previewCard").style.display = ""; $("previewTitle").textContent = "PDF プレビュー (" + pages.length + " ページ)";
    $("preview").style.display = "none"; $("pdfPages").innerHTML = "";
    pages.forEach(function (p) { var im = new Image(); im.src = p.canvas.toDataURL("image/jpeg", 0.7); $("pdfPages").appendChild(im); });
  }

  /* ───────────── ファイル保存 ───────────── */
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
  function reportSave(p) {
    p.then(function (m) { $("outState").textContent = m; },
           function (e) { $("outState").innerHTML = "<span class=err>保存に失敗: " + escapeHtml(e && (e.message || e.code) || String(e)) + "</span>"; });
  }
  $("zipBtn").addEventListener("click", function () {
    if (project) reportSave(saveBytes(project.slug + ".zip", zipBuild(project.files), "application/zip"));
  });
  $("pdfBtn").addEventListener("click", function () {
    if (pdfBytes) reportSave(saveBytes(project.slug + ".pdf", pdfBytes, "application/pdf"));
  });

  /* ───────────── GitHub へ 1 コミットでプッシュ ───────────── */
  async function gh(method, path, token, body) {
    var res = await fetch("https://api.github.com" + path, {
      method: method,
      headers: { "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined
    });
    var j = null; try { j = await res.json(); } catch (e) {}
    if (!res.ok) { var err = new Error("GitHub " + res.status + ": " + (j && j.message || res.statusText) + " (" + method + " " + path + ")"); err.status = res.status; throw err; }
    return j;
  }
  $("pushBtn").addEventListener("click", async function () {
    if (!project) return;
    saveSettings();
    var repo = $("ghRepo").value.trim(), branch = $("ghBranch").value.trim() || "badagpt-kai-apps", token = $("ghToken").value.trim();
    if (!/^[\w.-]+\/[\w.-]+$/.test(repo) || !token) { $("outState").innerHTML = "<span class=warn>④ 設定 で GitHub のリポジトリとトークンを入れてください。</span>"; return; }
    $("pushBtn").disabled = true;
    try {
      var R = "/repos/" + repo, ref;
      $("outState").textContent = "ブランチを確認中…";
      try { ref = await gh("GET", R + "/git/ref/heads/" + encodeURIComponent(branch), token); }
      catch (e) {
        if (e.status !== 404) throw e;
        var info = await gh("GET", R, token);
        var baseRef = await gh("GET", R + "/git/ref/heads/" + encodeURIComponent(info.default_branch), token);
        ref = await gh("POST", R + "/git/refs", token, { ref: "refs/heads/" + branch, sha: baseRef.object.sha });
      }
      var parent = await gh("GET", R + "/git/commits/" + ref.object.sha, token);
      var tree = [];
      for (var i = 0; i < project.files.length; i++) {
        var f = project.files[i];
        $("outState").textContent = "アップロード中… " + (i + 1) + " / " + project.files.length;
        var bytes = typeof f.data === "string" ? utf8(f.data) : f.data;
        var blob = await gh("POST", R + "/git/blobs", token, { content: bytesToBase64(bytes), encoding: "base64" });
        tree.push({ path: f.path, mode: "100644", type: "blob", sha: blob.sha });
      }
      var t = await gh("POST", R + "/git/trees", token, { base_tree: parent.tree.sha, tree: tree });
      var commit = await gh("POST", R + "/git/commits", token, {
        message: "BadaGPT改: " + project.name + " (" + TARGETS[project.target].label + ") を生成", tree: t.sha, parents: [parent.sha] });
      await gh("PATCH", R + "/git/refs/heads/" + encodeURIComponent(branch), token, { sha: commit.sha });
      var base = "https://github.com/" + repo;
      $("outState").innerHTML = "<span class=ok>プッシュしました。</span> " +
        "<a href=\"" + base + "/commit/" + commit.sha + "\" target=\"_blank\" rel=\"noopener\">コミット</a> ・ " +
        (TARGETS[project.target].packaging
          ? "<a href=\"" + base + "/actions\" target=\"_blank\" rel=\"noopener\">ビルドの進行 (Actions)</a> ・ " +
            "<a href=\"" + base + "/releases/tag/" + project.slug + "-latest\" target=\"_blank\" rel=\"noopener\">完成した APK / EXE (Releases)</a>"
          : "<a href=\"" + base + "/tree/" + encodeURIComponent(branch) + "/apps/" + project.slug + "\" target=\"_blank\" rel=\"noopener\">ファイル</a>");
    } catch (e) {
      $("outState").innerHTML = "<span class=err>" + escapeHtml(e.message || String(e)) + "</span>" +
        (/(403|404)/.test(e.message) ? "<br>トークンの権限 (Contents / Workflows の書き込み) と対象リポジトリを確認してください。" : "");
    } finally { $("pushBtn").disabled = false; }
  });

  /* Cordova: 外部リンクは既定ブラウザで開く */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[target=_blank]");
    if (a && isCordova && window.cordova.InAppBrowser) { e.preventDefault(); window.cordova.InAppBrowser.open(a.href, "_system"); }
  });
})();
