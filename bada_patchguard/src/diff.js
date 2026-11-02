/*
 * diff.js — 行単位の差分・パッチ適用・逆パッチ・SHA-256 (Bada へ渡すネイティブ組込み)
 *
 *   diffLines(a, b)          Myers の O(ND) 差分 → ハンク (文脈 3 行)
 *   applyHunks(text, hunks)  文脈を厳密に照合して適用 (ずれた土台には当てない)
 *   reverseHunks(hunks)      逆パッチ (ロールバック)
 *   unified(path, a, b, hs)  git 互換の unified diff 文字列
 *   parseUnified(text)       unified diff をファイル毎のハンクへ
 *   sha256(text)             UTF-8 の SHA-256 (16 進)
 */
"use strict";

/* 末尾に改行の無い最終行には NOEOL 印を付けて比較する
   (改行の有無の変化も「最終行の変更」として差分・照合の対象になる) */
const NOEOL = "\u0000";
function splitLines(s) {
  s = String(s);
  if (s === "") return { lines: [], eofNL: true };
  const eofNL = s.endsWith("\n");
  const lines = (eofNL ? s.slice(0, -1) : s).split("\n");
  if (!eofNL) lines[lines.length - 1] += NOEOL;
  return { lines, eofNL };
}
function joinLines(lines) {
  if (!lines.length) return "";
  const last = lines[lines.length - 1];
  if (last.endsWith(NOEOL)) return lines.slice(0, -1).concat([last.slice(0, -1)]).join("\n");
  return lines.join("\n") + "\n";
}

/* Myers の差分: 編集列 [[op, text], ...] (op: " " 共通, "-" 削除, "+" 追加) */
function myers(A, B) {
  const N = A.length, M = B.length, MAX = N + M;
  const V = new Int32Array(2 * MAX + 2); const trace = [];
  const off = MAX;
  outer:
  for (let D = 0; D <= MAX; D++) {
    trace.push(V.slice());
    for (let k = -D; k <= D; k += 2) {
      let x;
      if (k === -D || (k !== D && V[off + k - 1] < V[off + k + 1])) x = V[off + k + 1];
      else x = V[off + k - 1] + 1;
      let y = x - k;
      while (x < N && y < M && A[x] === B[y]) { x++; y++; }
      V[off + k] = x;
      if (x >= N && y >= M) { trace.push(V.slice()); break outer; }
    }
  }
  const ops = []; let x = N, y = M;
  for (let D = trace.length - 2; D >= 0 && (x > 0 || y > 0); D--) {
    const Vd = trace[D]; const k = x - y;
    let pk;
    if (k === -D || (k !== D && Vd[off + k - 1] < Vd[off + k + 1])) pk = k + 1; else pk = k - 1;
    const px = Vd[off + pk], py = px - pk;
    while (x > px && y > py) { ops.push([" ", A[x - 1]]); x--; y--; }
    if (D > 0) { if (x === px) ops.push(["+", B[y - 1]]); else ops.push(["-", A[x - 1]]); }
    x = px; y = py;
  }
  while (x > 0 && y > 0) { ops.push([" ", A[x - 1]]); x--; y--; }
  return ops.reverse();
}

function diffLines(a, b, ctx) {
  ctx = ctx === undefined ? 3 : ctx;
  const sa = splitLines(a), sb = splitLines(b);
  const A = sa.lines, B = sb.lines;
  // 共通の先頭・末尾を先に剥がして高速化
  let pre = 0; while (pre < A.length && pre < B.length && A[pre] === B[pre]) pre++;
  let suf = 0; while (suf < A.length - pre && suf < B.length - pre && A[A.length - 1 - suf] === B[B.length - 1 - suf]) suf++;
  const mid = myers(A.slice(pre, A.length - suf), B.slice(pre, B.length - suf));
  const ops = A.slice(0, pre).map(l => [" ", l]).concat(mid, A.slice(A.length - suf).map(l => [" ", l]));
  const hunks = []; let ai = 0, bi = 0, cur = null, lastChange = -1;
  ops.forEach((op, idx) => {
    const changed = op[0] !== " ";
    if (changed) {
      if (!cur || idx - lastChange > 2 * ctx) {
        if (cur) closeH(cur);
        const back = Math.min(ctx, countBack(ops, idx));
        cur = { a_start: ai - back + 1, b_start: bi - back + 1, lines: ops.slice(idx - back, idx).map(o => [" ", o[1]]) };
      } else {
        for (let q = lastChange + 1; q < idx; q++) cur.lines.push([" ", ops[q][1]]);
      }
      cur.lines.push(op); lastChange = idx;
    }
    if (op[0] !== "+") ai++;
    if (op[0] !== "-") bi++;
  });
  if (cur) closeH(cur);
  function countBack(o, idx) { let n = 0; for (let q = idx - 1; q >= 0 && o[q][0] === " "; q--) n++; return n; }
  function closeH(h) {
    let after = 0, q = lastChange + 1;
    while (after < ctx && q < ops.length && ops[q][0] === " ") { h.lines.push([" ", ops[q][1]]); after++; q++; }
    h.a_len = h.lines.filter(l => l[0] !== "+").length;
    h.b_len = h.lines.filter(l => l[0] !== "-").length;
    if (h.a_len === 0) h.a_start -= 1;
    if (h.b_len === 0) h.b_start -= 1;
    hunks.push(h);
  }
  const adds = ops.filter(o => o[0] === "+").length, dels = ops.filter(o => o[0] === "-").length;
  return { hunks, adds, dels, a_lines: A.length, b_lines: B.length };
}

/* 厳密適用: ハンクの文脈と削除行が土台と一字一句一致しなければ失敗 */
function applyHunks(text, hunks) {
  const s = splitLines(text); const A = s.lines; const out = []; let ai = 0;
  for (const h of hunks) {
    const start = h.a_len === 0 ? h.a_start : h.a_start - 1;
    if (start < ai || start > A.length) return { ok: false, error: `ハンク @@ -${h.a_start} の位置が不正です` };
    while (ai < start) out.push(A[ai++]);
    for (const [op, line] of h.lines) {
      if (op === "+") { out.push(line); continue; }
      if (A[ai] !== line) return { ok: false, error: `line ${ai + 1}: 土台が記録と一致しません (期待 ${JSON.stringify(line.replace(NOEOL, "")).slice(0, 80)}, 実際 ${JSON.stringify(A[ai] === undefined ? "(EOF)" : A[ai].replace(NOEOL, "")).slice(0, 80)})` };
      if (op === " ") out.push(line);
      ai++;
    }
  }
  while (ai < A.length) out.push(A[ai++]);
  return { ok: true, text: joinLines(out) };
}

function reverseHunks(hunks) {
  return hunks.map(h => ({
    a_start: h.b_start, a_len: h.b_len, b_start: h.a_start, b_len: h.a_len,
    lines: h.lines.map(([op, l]) => [op === "+" ? "-" : op === "-" ? "+" : " ", l])
  }));
}

function hunkHeader(h) {
  const r = (s, n) => (n === 1 ? `${s}` : `${s},${n}`);
  return `@@ -${r(h.a_start, h.a_len)} +${r(h.b_start, h.b_len)} @@`;
}
function unified(path, d, meta) {
  meta = meta || {};
  const aName = meta.a_absent ? "/dev/null" : "a/" + path, bName = meta.b_absent ? "/dev/null" : "b/" + path;
  const head = [`diff --git a/${path} b/${path}`];
  if (meta.a_sha || meta.b_sha) head.push(`PatchGuard-Base-SHA256: ${meta.a_sha || "-"}`, `PatchGuard-After-SHA256: ${meta.b_sha || "-"}`);
  head.push(`--- ${aName}`, `+++ ${bName}`);
  const body = [];
  d.hunks.forEach(h => {
    body.push(hunkHeader(h));
    for (const [op, l] of h.lines) {
      if (l.endsWith(NOEOL)) { body.push(op + l.slice(0, -1)); body.push("\\ No newline at end of file"); }
      else body.push(op + l);
    }
  });
  return head.concat(body).join("\n") + "\n";
}

/* unified diff (この形式と git diff) をファイル毎に読み戻す */
function parseUnified(text) {
  const files = []; let f = null, h = null;
  const lines = String(text).replace(/\r\n/g, "\n").split("\n");
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (l.startsWith("diff --git ")) { f = { path: null, a_sha: null, b_sha: null, hunks: [], a_absent: false, b_absent: false }; files.push(f); h = null; continue; }
    if (l.startsWith("PatchGuard-Base-SHA256: ") && f) { const v = l.slice(24).trim(); f.a_sha = v === "-" ? null : v; continue; }
    if (l.startsWith("PatchGuard-After-SHA256: ") && f) { const v = l.slice(25).trim(); f.b_sha = v === "-" ? null : v; continue; }
    if (l.startsWith("--- ") && (!h || lines[i + 1] && lines[i + 1].startsWith("+++ "))) {
      if (!f || f.hunks.length) { f = { path: null, a_sha: null, b_sha: null, hunks: [], a_absent: false, b_absent: false }; files.push(f); }
      const a = l.slice(4).trim(); f.a_absent = a === "/dev/null"; if (!f.a_absent) f.path = a.replace(/^a\//, "");
      h = null; continue;
    }
    if (l.startsWith("+++ ") && f && !h) { const b = l.slice(4).trim(); f.b_absent = b === "/dev/null"; if (!f.b_absent) f.path = b.replace(/^b\//, ""); continue; }
    const m = /^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@/.exec(l);
    if (m && f) { h = { a_start: +m[1], a_len: m[2] === undefined ? 1 : +m[2], b_start: +m[3], b_len: m[4] === undefined ? 1 : +m[4], lines: [] }; f.hunks.push(h); continue; }
    if (h && l.startsWith("\\")) { const last = h.lines[h.lines.length - 1]; if (last) last[1] += NOEOL; continue; }
    if (h && (l[0] === " " || l[0] === "+" || l[0] === "-")) { h.lines.push([l[0], l.slice(1)]); continue; }
    if (h && l === "" && i < lines.length - 1) { h.lines.push([" ", ""]); continue; }
  }
  return files.filter(x => x.path);
}

/* SHA-256 (純 JS / 同期) */
const K256 = new Uint32Array([0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);
function utf8(s) {
  if (typeof TextEncoder !== "undefined") return new TextEncoder().encode(s);
  return Uint8Array.from(Buffer.from(s, "utf8"));
}
function sha256(str) {
  const msg = utf8(String(str)); const l = msg.length;
  const nb = ((l + 9 + 63) >> 6) << 6; const buf = new Uint8Array(nb); buf.set(msg); buf[l] = 0x80;
  const bits = l * 8; const dv = new DataView(buf.buffer);
  dv.setUint32(nb - 4, bits >>> 0); dv.setUint32(nb - 8, Math.floor(bits / 4294967296));
  const H = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const W = new Uint32Array(64);
  for (let o = 0; o < nb; o += 64) {
    for (let t = 0; t < 16; t++) W[t] = dv.getUint32(o + t * 4);
    for (let t = 16; t < 64; t++) {
      const x = W[t - 15], y = W[t - 2];
      const s0 = (x >>> 7 | x << 25) ^ (x >>> 18 | x << 14) ^ (x >>> 3);
      const s1 = (y >>> 17 | y << 15) ^ (y >>> 19 | y << 13) ^ (y >>> 10);
      W[t] = (W[t - 16] + s0 + W[t - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, h] = H;
    for (let t = 0; t < 64; t++) {
      const S1 = (e >>> 6 | e << 26) ^ (e >>> 11 | e << 21) ^ (e >>> 25 | e << 7);
      const ch = (e & f) ^ (~e & g);
      const t1 = (h + S1 + ch + K256[t] + W[t]) >>> 0;
      const S0 = (a >>> 2 | a << 30) ^ (a >>> 13 | a << 19) ^ (a >>> 22 | a << 10);
      const mj = (a & b) ^ (a & c) ^ (b & c);
      const t2 = (S0 + mj) >>> 0;
      h = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
    }
    H[0] += a; H[1] += b; H[2] += c; H[3] += d; H[4] += e; H[5] += f; H[6] += g; H[7] += h;
  }
  return Array.from(H, x => (x >>> 0).toString(16).padStart(8, "0")).join("");
}

const PatchDiff = { NOEOL, splitLines, joinLines, diffLines, applyHunks, reverseHunks, unified, parseUnified, sha256, hunkHeader };
if (typeof module !== "undefined" && module.exports) module.exports = PatchDiff;
