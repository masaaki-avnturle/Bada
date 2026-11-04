/*
 * telephacy.js — Ω-Telephacy: 声を出さない「サイレント・トーク」音声認識 (口形 viseme)
 *
 * 本リポジトリの bada_silent_vim/silenttalk (Python) を移植したもの。
 * カメラ映像の口付近 ROI で、口の暗い領域 (口腔) の外接矩形から
 *   aperture (縦の開き)・spread (横の開き)・energy (暗部率 = 調音の力)
 * を測り、フレームを viseme 記号 C/A/I/U/O/E (C = 閉じ/休止) に分類する。
 * 連続する同じ viseme を縮約し (CTC 風)、休止 C で発話に区切り、縮約した
 * viseme 語 (例 "AI") を辞書で BadaGPT の語 (非言語アトム / 命令) に引く。
 * 7 段階の共鳴スケール (do〜si) は口形から再構成し、Γ多様体 × Jones 多項式の
 * 「熱エネルギー経路」(|V_{T(2,n)}(e^{2πi/5})|) で語の重みを付け、既存の
 * トランスフォーマー (silent.js) で語列を latent に組み立てる。
 *
 * 併せて取り入れたもの:
 *   - Ω-Telepathy: ホバー滞留 (dwell) で確定する、クリック不要の選択
 *   - Ω-Thermal Trace: 動きエネルギーの疑似サーモ表示 (実温度ではない)
 *   - イメージ入力: 画像の明るさ・彩度・色相 → 調子と色のアトム
 *
 * 正直な範囲 (重要):
 *   - 認識するのは、利用者本人が **声を出さずに口形の列として発音した語** であり、
 *     辞書にある viseme 語 (学習して使う無音の語彙) に限る。自由な読唇ではない。
 *   - 思考や他人の内面は読まない。熱 (温度) は測らず、疑似サーモは普通のカメラの
 *     動きエネルギーの疑似カラーである。Γ多様体・Jones は重み付けの可視化。
 *   - 利用者本人の顔を、本人の同意の上でカメラに映す。
 */
"use strict";

var VISEMES = ["C", "A", "I", "U", "O", "E"];
var VISEME_SHAPE = { C: [0.04, 0.15], A: [0.46, 0.62], I: [0.18, 0.62], O: [0.46, 0.30], U: [0.15, 0.24], E: [0.28, 0.40] };
var VISEME_HINT = { C: "口を閉じる", A: "大きく縦横に開く (あ)", I: "横に引いて薄く (い)", U: "小さくすぼめる (う)", O: "縦に丸く (お)", E: "中くらいに開く (え)" };

/* ───────────── 口形の特徴 (lipfeatures.py) ───────────── */
/* gray: 0..255 の配列 (長さ w*h)。暗い画素の外接矩形から特徴を得る。 */
function lipFeatures(gray, w, h, darkThresh) {
  var minR = h, maxR = -1, minC = w, maxC = -1, dark = 0, i = 0;
  for (var r = 0; r < h; r++) for (var c = 0; c < w; c++, i++) {
    if (gray[i] < darkThresh) { dark++; if (r < minR) minR = r; if (r > maxR) maxR = r; if (c < minC) minC = c; if (c > maxC) maxC = c; }
  }
  if (maxR < 0) return { aperture: 0, spread: 0, energy: 0 };
  return { aperture: (maxR - minR + 1) / h, spread: (maxC - minC + 1) / w, energy: dark / (w * h) };
}
/* カメラの明るさに合わせた暗さのしきい値: ROI 中央値の 55% (40..140 に制限) */
function adaptiveThresh(gray) {
  if (!gray || !gray.length) return 110;
  var a = Array.prototype.slice.call(gray).sort(function (p, q) { return p - q; });
  var med = a[a.length >> 1];
  return Math.max(40, Math.min(140, Math.round(med * 0.55)));
}
/* 較正: 閉じた口 (base) と大きく開けた口 (max) で 0..1 に正規化 */
function normalizeFeat(f, cal) {
  if (!cal || !cal.max) return f;
  function nz(v, lo, hi) { return hi > lo ? Math.max(0, Math.min(1, (v - lo) / (hi - lo))) : v; }
  return {
    aperture: nz(f.aperture, cal.base ? cal.base.aperture : 0, cal.max.aperture) * 0.5,
    spread: nz(f.spread, cal.base ? cal.base.spread : 0, cal.max.spread) * 0.65,
    energy: f.energy
  };
}
function classifyViseme(f) {
  var a = f.aperture, s = f.spread;
  if (f.energy < 0.02 || (a < 0.12 && s < 0.20)) return "C";
  var tall = a >= 0.34, wide = s >= 0.45;
  if (tall && wide) return "A";
  if (!tall && wide) return "I";
  if (tall && !wide) return "O";
  if (a < 0.22 && !wide) return "U";
  return "E";
}

/* ───────────── 7 段階の共鳴スケール (scale.py) ───────────── */
var BAND_NAMES = ["do", "re", "mi", "fa", "sol", "la", "si"];
function resonanceBands(f) {
  var centre = Math.max(0, Math.min(6, f.spread * 4 + (1 - f.aperture) * 2)), bands = [], total = 0;
  for (var b = 0; b < 7; b++) { var act = Math.max(0, 1 - Math.abs(b - centre)) * (0.2 + f.energy); bands.push(act); total += act; }
  return bands.map(function (x) { return x / (total || 1); });
}
function dominantBand(f) { var b = resonanceBands(f), best = 0; for (var i = 1; i < 7; i++) if (b[i] > b[best]) best = i; return best; }

/* ───────────── 辞書: viseme 語 → BadaGPT の語 ─────────────
 * 口形 2 つの列 (例 "AI" = あ→い) を、声を出さずに「発音」して語を伝える。 */
var TELEPHACY_LEXICON = {
  "AI": { atom: "records", label: "記録・管理" }, "AO": { atom: "book", label: "本" }, "AU": { atom: "person", label: "人" },
  "AE": { atom: "task", label: "ToDo" }, "IA": { atom: "note", label: "メモ" }, "IO": { atom: "time", label: "タイマー" },
  "IU": { atom: "money", label: "家計簿" }, "IE": { atom: "learn", label: "クイズ" }, "UA": { atom: "draw", label: "お絵かき" },
  "UI": { atom: "habit", label: "習慣" }, "UO": { atom: "random", label: "抽選" }, "UE": { atom: "quantum", label: "量子回路" },
  "OA": { atom: "sort", label: "並べ替え" }, "OI": { atom: "find", label: "検索" }, "OU": { atom: "graph", label: "グラフ" }, "OE": { atom: "export", label: "CSV 書き出し" },
  "EA": { atom: "cool", label: "暗い青" }, "EI": { atom: "warm", label: "明るい橙" }, "EU": { atom: "calm", label: "静かに" }, "EO": { atom: "urgent", label: "勢いよく" },
  "AIA": { atom: "android", label: "スマホ" }, "AIO": { atom: "windows", label: "Windows" }, "AIU": { atom: "linux", label: "Linux" },
  "OAO": { atom: "book_vol", label: "本一冊の分量" },
  "IOI": { cmd: "forge", label: "作って (錬成)" }, "UOU": { cmd: "reset", label: "やり直し" }, "EAE": { cmd: "undo", label: "ひとつ戻す" }
};

/* viseme 記号列 → 語トークン (連続重複の縮約 → C で区切る → 辞書) */
function decodeVisemes(seq, feats) {
  var collapsed = [];
  for (var i = 0; i < seq.length; i++) {
    if (collapsed.length && collapsed[collapsed.length - 1].v === seq[i]) continue;
    collapsed.push({ v: seq[i], f: feats ? feats[i] : null });
  }
  var tokens = [], cur = [];
  function flush() {
    if (!cur.length) return;
    var word = cur.map(function (x) { return x.v; }).join("");
    var fs = cur.map(function (x) { return x.f; }).filter(Boolean);
    var avg = fs.length ? { aperture: fs.reduce(function (a, x) { return a + x.aperture; }, 0) / fs.length, spread: fs.reduce(function (a, x) { return a + x.spread; }, 0) / fs.length, energy: fs.reduce(function (a, x) { return a + x.energy; }, 0) / fs.length } : { aperture: 0.3, spread: 0.4, energy: 0.2 };
    var e = TELEPHACY_LEXICON[word] || null;
    var band = dominantBand(avg);
    tokens.push({ visemes: word, atom: e ? e.atom || null : null, cmd: e ? e.cmd || null : null, label: e ? e.label : null, band: band, bandName: BAND_NAMES[band], feat: avg });
    cur = [];
  }
  collapsed.forEach(function (x) { if (x.v === "C") flush(); else cur.push(x); });
  flush();
  return tokens;
}
/* フレーム列 ({gray,w,h}) → トークン */
function decodeFrames(frames, cal) {
  var seq = [], feats = [];
  frames.forEach(function (fr) {
    var f = normalizeFeat(lipFeatures(fr.gray, fr.w, fr.h, fr.thresh != null ? fr.thresh : 110), cal);
    seq.push(classifyViseme(f)); feats.push(f);
  });
  return decodeVisemes(seq, feats);
}

/* ───────────── 合成 (synth.py): viseme → 口形フレーム ───────────── */
function drawViseme(v, w, h) {
  w = w || 32; h = h || 32;
  var sh = VISEME_SHAPE[v], cy = h / 2, cx = w / 2, ry = Math.max(0.5, sh[0] * h / 2), rx = Math.max(0.5, sh[1] * w / 2);
  var g = new Uint8Array(w * h), i = 0;
  for (var r = 0; r < h; r++) for (var c = 0; c < w; c++, i++) { var dy = (r - cy) / ry, dx = (c - cx) / rx; g[i] = (dx * dx + dy * dy <= 1) ? 40 : 255; }
  return { gray: g, w: w, h: h, thresh: 110 };
}
function synthUtterance(word, hold) {
  hold = hold || 2;
  var frames = [drawViseme("C")];
  for (var i = 0; i < word.length; i++) for (var k = 0; k < hold; k++) frames.push(drawViseme(word[i]));
  frames.push(drawViseme("C"));
  return frames;
}
function synthStream(words, hold) { var out = []; words.forEach(function (w) { out = out.concat(synthUtterance(w, hold)); }); return out; }

/* ───────────── Γ多様体 × Jones の「熱エネルギー経路」(可視化・重み) ───────────── */
/* feat ∈ [0,1] → (2,n) トーラス結び目 n = 3 + 2·round(7·feat)、|V(e^{2πi/5})| を 0..1 に */
function thermalPath(feat) {
  var n = 3 + 2 * Math.round(Math.max(0, Math.min(1, feat)) * 7);
  var v = Jones.Vabs(n, 2 * Math.PI / 5);
  return { n: n, abs: v, score: Math.min(1, v / 3) };
}

/* ───────────── 疑似サーモ (Ω-Thermal Trace のカラーマップ・実温度ではない) ───────────── */
function cmapThermal(t) {
  t = Math.max(0, Math.min(1, t));
  return [Math.min(1, t * 1.7) * 255 | 0, Math.min(1, Math.max(0, t * 1.7 - 0.55)) * 255 | 0, Math.min(1, Math.max(0, t * 2 - 1.45)) * 255 | 0];
}

/* ───────────── イメージ入力: 画像 → 調子・色のアトム ───────────── */
function imageFeatures(rgba, w, h) {
  var n = w * h, sumL = 0, sumS = 0, hueBins = new Array(6).fill(0);
  for (var i = 0; i < n; i++) {
    var r = rgba[i * 4] / 255, g = rgba[i * 4 + 1] / 255, b = rgba[i * 4 + 2] / 255;
    var mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn, s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    sumL += l; sumS += s;
    if (d > 0.08) { var hh; if (mx === r) hh = ((g - b) / d) % 6; else if (mx === g) hh = (b - r) / d + 2; else hh = (r - g) / d + 4; if (hh < 0) hh += 6; hueBins[Math.floor(hh) % 6] += s; }
  }
  var bright = sumL / n, sat = sumS / n, hb = 0; for (var k = 1; k < 6; k++) if (hueBins[k] > hueBins[hb]) hb = k;
  var atoms = [];
  atoms.push(bright > 0.55 ? "warm" : "cool");               /* 明るい → 明るい橙 / 暗い → 暗い青 */
  if (sat > 0.25) atoms.push(hb >= 3 && hb <= 4 ? "vivid" : hb === 0 || hb === 5 ? "urgent" : "joy"); /* 紫寄り / 赤寄り / その他 */
  else atoms.push("calm");
  return { brightness: bright, saturation: sat, hueBin: hb, atoms: atoms };
}

/* ───────────── ChatGPT 風チャット: 意図の振り分けと内蔵の返答 ───────────── */
function chatRoute(text) {
  var t = String(text || "").trim();
  if (!t) return { intent: "empty" };
  if (/^(こんにちは|こんばんは|おはよう|やあ|hello|hi)/i.test(t)) return { intent: "greeting" };
  if (/何が(でき|出来)|できること|使い方|help|ヘルプ/i.test(t)) return { intent: "capabilities" };
  if (/やり直|リセット|最初から/.test(t)) return { intent: "reset" };
  if (/作っ|作り|作成|錬成|欲しい|ほしい|したい|アプリ|ツール|作れ|build|make|create/i.test(t)) return { intent: "forge", request: t };
  return { intent: "chat", text: t };
}
function chatReplyLocal(route, ctx) {
  ctx = ctx || {};
  if (route.intent === "greeting") return "こんにちは。BadaGPT です。声を出さずに口形で、脳波で、描いた動きで、あるいは文字で、欲しいアプリを伝えてください。文章にして、アプリ・ソースコード・論文を錬成し、exe / apk に自動コンパイルします。";
  if (route.intent === "capabilities") return "できること: ① 思考入力 (Ω-Telephacy の無音の口形 / 脳波 BCI / 描いた動き / 体のサイン / 文字) を文章にする ② 依頼の全体を把握してアプリを生成・検証する ③ Python / Node / Bada のソースコードにする ④ GitHub へ 1 コミットして Actions で APK / Windows / Linux に自動コンパイルする ⑤ 生成過程を論文 (PDF) にまとめる。「作って」と伝えると錬成します。";
  if (route.intent === "reset") return "入力を消しました。もう一度、欲しいアプリを伝えてください。";
  if (route.intent === "empty") return "何を作りましょう？ 口形・脳波・動き・文字のどれでも伝えられます。";
  if (route.intent === "forged" && ctx.spec) {
    var s = ctx.spec;
    return "「" + s.title + "」を錬成しました。モジュール: " + s.modules.map(function (m) { return m.label; }).join("・") + " / 網羅率 " + Math.round(s.coverage * 100) + "% / 検証 " + (ctx.ver && ctx.ver.ok ? "合格" : "要確認") + "。下の ④ でアプリ、⑥ でソースコード、⑤ で論文 (PDF)、⑦ で exe / apk への自動コンパイルができます。";
  }
  return "承知しました。「作って」と伝えるか、口形で IOI (い→お→い) と発音すると、ここまでの内容でアプリを錬成します。";
}
