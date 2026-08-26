/*
 * flash.js — 瞬読(フラッシュ)提示エンジン
 * Ω-Whispered — Masaaki Yamaguchi / Bada (bio_medicine/omega_whispered)
 *
 * 速読法の「瞬読」に倣い、数学の専門用語・記号・バラバラにした方程式のトークンを
 * 画面上のランダムな位置・角度・大きさで一斉に提示し、短時間で消す。
 *
 *   注視点(+) → バースト提示(可変 ms) → マスク(残像で読み取れないようにする) → 設問
 *
 * さらに 2-down/1-up ステアケース法で露出時間を適応的に上下させ、
 * 反転(reversal)点の幾何平均として「瞬読閾値(ms)」を推定する。
 * これは心理物理で標準的な閾値推定手続きで、収束先は約 70.7% 正答点にあたる。
 */
(function (root) {
  "use strict";

  /* ============================ 乱数・幾何補助 ============================ */
  function rnd(a, b) { return a + Math.random() * (b - a); }
  function overlaps(r, list, pad) {
    for (var i = 0; i < list.length; i++) {
      var o = list[i];
      if (r.x < o.x + o.w + pad && o.x < r.x + r.w + pad &&
          r.y < o.y + o.h + pad && o.y < r.y + r.h + pad) return true;
    }
    return false;
  }

  /* ============================ バースト提示 ============================ */
  /*
   * stage : 提示領域の DOM(position:relative)
   * items : [{text, cls}] 表示する要素(順序はここでシャッフル済みを想定)
   * ms    : 露出時間(ミリ秒)
   * opts  : {fix:注視点ms, mask:マスクms, minFont, maxFont, rotate,
 *           onPhase:function(name) — "fix"|"show"|"mask"|"end" の各段階で呼ばれる(電子音用)}
   * 戻り値: Promise(実測露出 ms を解決)
   */
  function burst(stage, items, ms, opts) {
    opts = opts || {};
    var fixMs = opts.fix === undefined ? 500 : opts.fix;
    var maskMs = opts.mask === undefined ? 120 : opts.mask;
    var minF = opts.minFont || 17, maxF = opts.maxFont || 30;
    var rot = opts.rotate === undefined ? 22 : opts.rotate;
    var onPhase = typeof opts.onPhase === "function" ? opts.onPhase : function () {};

    function clear() { while (stage.firstChild) stage.removeChild(stage.firstChild); }

    function fixation() {
      return new Promise(function (res) {
        clear();
        onPhase("fix");
        var f = document.createElement("div");
        f.className = "fl fix";
        f.textContent = "+";
        stage.appendChild(f);
        setTimeout(res, fixMs);
      });
    }

    /* ランダム位置に散らす(できるだけ重ならないように試行) */
    function scatter() {
      clear();
      var W = stage.clientWidth || 520, H = stage.clientHeight || 300, placed = [];
      items.forEach(function (it) {
        var el = document.createElement("span");
        el.className = "fl " + (it.cls || "");
        el.textContent = it.text;
        el.style.fontSize = rnd(minF, maxF).toFixed(1) + "px";
        el.style.visibility = "hidden";
        stage.appendChild(el);
        var w = el.offsetWidth, h = el.offsetHeight, r = null;
        for (var tries = 0; tries < 60; tries++) {
          var cand = { x: rnd(4, Math.max(5, W - w - 4)), y: rnd(4, Math.max(5, H - h - 4)), w: w, h: h };
          if (!overlaps(cand, placed, 6)) { r = cand; break; }
        }
        if (!r) r = { x: rnd(4, Math.max(5, W - w - 4)), y: rnd(4, Math.max(5, H - h - 4)), w: w, h: h };
        placed.push(r);
        el.style.left = r.x + "px";
        el.style.top = r.y + "px";
        el.style.transform = "rotate(" + rnd(-rot, rot).toFixed(1) + "deg)";
        el.style.visibility = "visible";
      });
    }

    /* マスク: ランダムな記号片を薄く敷いて残像からの読み取りを防ぐ */
    function mask() {
      clear();
      var chars = "∫∂∇⊗⊕∑∏≅≡⊢∈∀∃⋆†ℵ𝒪ΓζπχσμλωΩ√∞≪⌊⟨‖∅∪∩→↦⇒";
      var W = stage.clientWidth || 520, H = stage.clientHeight || 300;
      for (var i = 0; i < 70; i++) {
        var m = document.createElement("span");
        m.className = "fl mask";
        m.textContent = chars.charAt(Math.floor(Math.random() * chars.length));
        m.style.left = rnd(0, W - 14).toFixed(0) + "px";
        m.style.top = rnd(0, H - 18).toFixed(0) + "px";
        m.style.fontSize = rnd(13, 26).toFixed(0) + "px";
        m.style.transform = "rotate(" + rnd(-40, 40).toFixed(0) + "deg)";
        stage.appendChild(m);
      }
    }

    return fixation().then(function () {
      return new Promise(function (res) {
        var t0 = (root.performance && performance.now) ? performance.now() : Date.now();
        onPhase("show");
        scatter();
        /* 描画済みフレームから計時するため、次のフレームで待機を開始する */
        var start = function () {
          setTimeout(function () {
            var t1 = (root.performance && performance.now) ? performance.now() : Date.now();
            onPhase("mask");
            mask();
            setTimeout(function () { clear(); onPhase("end"); res(t1 - t0); }, maskMs);
          }, ms);
        };
        if (root.requestAnimationFrame) requestAnimationFrame(start); else start();
      });
    });
  }

  /* ====================== 方程式を「バラバラ」に分解 ====================== */
  /*
   * 方程式を、意味のある最小のかたまり(記号・数・添字つき変数)へ分割する。
   * 例: "∫_M dω = ∮_∂M ω" → ["∫_M", "dω", "=", "∮_∂M", "ω"]
   * 分割後は呼び出し側でシャッフルして散らす(＝バラバラにランダム提示)。
   */
  function tokenize(eq) {
    var raw = String(eq).replace(/[{}]/g, "").split(/\s+/).filter(Boolean), out = [];
    raw.forEach(function (tk) {
      /* 長いかたまりだけを、演算子の直前で分割する(演算子は右側の断片に付ける) */
      if (Array.from(tk).length > 7) {
        tk.split(/(?=[=+−])/).filter(Boolean).forEach(function (p) { out.push(p); });
      } else out.push(tk);
    });
    /* 1 文字だけの括弧など、意味を持たない断片は隣へ吸収する */
    var merged = [];
    out.forEach(function (t) {
      t = t.trim();
      if (!t) return;
      if (/^[()\[\]]$/.test(t) && merged.length) merged[merged.length - 1] += t;
      else merged.push(t);
    });
    return merged;
  }

  /* ========================= ステアケース(閾値推定) ========================= */
  /*
   * 2-down/1-up: 2 連続正答で露出時間を短くし、1 誤答で長くする。
   * 反転点(短縮↔延長の切り替わり)の露出時間の幾何平均を閾値とする。
   */
  function Staircase(o) {
    o = o || {};
    this.ms = o.start || 600;
    this.min = o.min || 40;
    this.max = o.max || 2000;
    this.down = o.down || 2;          /* 何連続正答で短縮するか */
    this.fDown = o.factorDown || 0.78;
    this.fUp = o.factorUp || 1.32;
    this.run = 0;
    this.lastDir = 0;
    this.reversals = [];
    this.history = [];
  }
  Staircase.prototype.current = function () { return Math.round(this.ms); };
  Staircase.prototype.update = function (ok) {
    var before = this.ms, dir = 0;
    if (ok) {
      this.run++;
      if (this.run >= this.down) { this.run = 0; dir = -1; this.ms = Math.max(this.min, this.ms * this.fDown); }
    } else {
      this.run = 0; dir = 1; this.ms = Math.min(this.max, this.ms * this.fUp);
    }
    if (dir !== 0) {
      if (this.lastDir !== 0 && dir !== this.lastDir) this.reversals.push(before);
      this.lastDir = dir;
    }
    this.history.push({ ms: Math.round(before), ok: ok });
    return this.current();
  };
  /* 閾値: 直近 6 反転点の幾何平均。反転が 2 未満なら正答した露出の幾何平均で代用 */
  Staircase.prototype.threshold = function () {
    var vals = this.reversals.slice(-6), reliable = vals.length >= 2;
    if (!reliable) {
      vals = this.history.filter(function (h) { return h.ok; }).map(function (h) { return h.ms; });
    }
    if (!vals.length) return { ms: this.current(), reliable: false, reversals: this.reversals.length };
    var s = 0;
    vals.forEach(function (v) { s += Math.log(Math.max(1, v)); });
    return { ms: Math.round(Math.exp(s / vals.length)), reliable: reliable, reversals: this.reversals.length };
  };

  var API = { burst: burst, tokenize: tokenize, Staircase: Staircase };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.FlashEngine = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
