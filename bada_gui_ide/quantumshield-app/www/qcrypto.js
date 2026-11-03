/*
 * qcrypto.js — Bada QuantumCrypto コア
 *
 * zone:// ウルトラネットワーク (bada_gui_ide/browser/zone-lib.bada) の
 * Jones 多項式量子暗号を、単独の「暗号化 / 解除(復号)」アプリ用に
 * JavaScript へ移植したものです。依存ライブラリなし・完全自己完結。
 *
 *   鍵導出:  結び目図の Kauffman ブラケット標本 (zone-lib.bada の
 *            kauffman()/jones_key() をそのまま移植) + パスフレーズを
 *            PBKDF2-HMAC-SHA256 で 64 バイトの鍵素材に伸長
 *   QKD:     Bell 対 (|00>+|11>)/√2 の測定シミュレーションで
 *            セッションソルトを採取 (zone-lib.bada の qkd_session() 相当)
 *   本体:    ChaCha20 ストリーム暗号 + HMAC-SHA256 タグ
 *            (encrypt-then-MAC の AEAD — 改ざんは復号前に検出して拒否)
 *
 * コンテナ形式 (バイナリ → Base64 アーマー):
 *   magic "BQC1" | ver(1) | flags(1) | knotId(1) | saltLen(1) | salt |
 *   nonce(12) | nameLen(2,BE) | nameUTF8 | ciphertext | tag(32)
 */
(function (global) {
  "use strict";

  /* ================= UTF-8 / bytes ================= */
  var TE = typeof TextEncoder !== "undefined" ? new TextEncoder() : null;
  var TD = typeof TextDecoder !== "undefined" ? new TextDecoder("utf-8", { fatal: false }) : null;

  function utf8(str) {
    if (TE) return TE.encode(str);
    var out = [], i, c;
    for (i = 0; i < str.length; i++) {
      c = str.codePointAt(i);
      if (c > 0xffff) i++;
      if (c < 0x80) out.push(c);
      else if (c < 0x800) out.push(0xc0 | (c >> 6), 0x80 | (c & 63));
      else if (c < 0x10000) out.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
      else out.push(0xf0 | (c >> 18), 0x80 | ((c >> 12) & 63), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    }
    return new Uint8Array(out);
  }
  function utf8dec(bytes) {
    if (TD) return TD.decode(bytes);
    var s = "", i = 0, b, c;
    while (i < bytes.length) {
      b = bytes[i++];
      if (b < 0x80) c = b;
      else if (b < 0xe0) c = ((b & 31) << 6) | (bytes[i++] & 63);
      else if (b < 0xf0) c = ((b & 15) << 12) | ((bytes[i++] & 63) << 6) | (bytes[i++] & 63);
      else c = ((b & 7) << 18) | ((bytes[i++] & 63) << 12) | ((bytes[i++] & 63) << 6) | (bytes[i++] & 63);
      s += String.fromCodePoint(c);
    }
    return s;
  }
  function concat() {
    var total = 0, i, off = 0;
    for (i = 0; i < arguments.length; i++) total += arguments[i].length;
    var out = new Uint8Array(total);
    for (i = 0; i < arguments.length; i++) { out.set(arguments[i], off); off += arguments[i].length; }
    return out;
  }
  function hex(bytes) {
    var s = "", i;
    for (i = 0; i < bytes.length; i++) s += (bytes[i] < 16 ? "0" : "") + bytes[i].toString(16);
    return s;
  }
  function randomBytes(n) {
    var out = new Uint8Array(n), i;
    var cr = (typeof crypto !== "undefined" && crypto.getRandomValues) ? crypto
           : (typeof globalThis !== "undefined" && globalThis.crypto && globalThis.crypto.getRandomValues) ? globalThis.crypto
           : null;
    if (cr) { cr.getRandomValues(out); return out; }
    for (i = 0; i < n; i++) out[i] = Math.floor(Math.random() * 256);
    return out;
  }
  function ctEq(a, b) {
    if (a.length !== b.length) return false;
    var d = 0, i;
    for (i = 0; i < a.length; i++) d |= a[i] ^ b[i];
    return d === 0;
  }

  /* ================= Base64 ================= */
  var B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  function b64enc(bytes) {
    var s = "", i, b0, b1, b2;
    for (i = 0; i + 2 < bytes.length; i += 3) {
      b0 = bytes[i]; b1 = bytes[i + 1]; b2 = bytes[i + 2];
      s += B64[b0 >> 2] + B64[((b0 & 3) << 4) | (b1 >> 4)] + B64[((b1 & 15) << 2) | (b2 >> 6)] + B64[b2 & 63];
    }
    var rem = bytes.length - i;
    if (rem === 1) { b0 = bytes[i]; s += B64[b0 >> 2] + B64[(b0 & 3) << 4] + "=="; }
    else if (rem === 2) { b0 = bytes[i]; b1 = bytes[i + 1]; s += B64[b0 >> 2] + B64[((b0 & 3) << 4) | (b1 >> 4)] + B64[(b1 & 15) << 2] + "="; }
    return s;
  }
  function b64dec(str) {
    str = str.replace(/[^A-Za-z0-9+/=]/g, "");
    var out = [], i, e0, e1, e2, e3;
    for (i = 0; i < str.length; i += 4) {
      e0 = B64.indexOf(str[i]); e1 = B64.indexOf(str[i + 1]);
      e2 = str[i + 2] === "=" || str[i + 2] === undefined ? -1 : B64.indexOf(str[i + 2]);
      e3 = str[i + 3] === "=" || str[i + 3] === undefined ? -1 : B64.indexOf(str[i + 3]);
      out.push((e0 << 2) | (e1 >> 4));
      if (e2 >= 0) out.push(((e1 & 15) << 4) | (e2 >> 2));
      if (e3 >= 0) out.push(((e2 & 3) << 6) | e3);
    }
    return new Uint8Array(out);
  }

  /* ================= SHA-256 (pure JS) ================= */
  var K256 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];
  var SHA256_INIT = new Int32Array([0x6a09e667, 0xbb67ae85 | 0, 0x3c6ef372, 0xa54ff53a | 0,
                                    0x510e527f, 0x9b05688c | 0, 0x1f83d9ab, 0x5be0cd19]);
  var W64 = new Int32Array(64);
  /* H (Int32Array(8)) を 16 ワードの block で 1 回圧縮する (in-place) */
  function sha256Compress(H, block) {
    var w = W64, j;
    for (j = 0; j < 16; j++) w[j] = block[j];
    for (j = 16; j < 64; j++) {
      var x = w[j - 15], y = w[j - 2];
      var s0 = ((x >>> 7) | (x << 25)) ^ ((x >>> 18) | (x << 14)) ^ (x >>> 3);
      var s1 = ((y >>> 17) | (y << 15)) ^ ((y >>> 19) | (y << 13)) ^ (y >>> 10);
      w[j] = (w[j - 16] + s0 + w[j - 7] + s1) | 0;
    }
    var a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
    for (j = 0; j < 64; j++) {
      var S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
      var ch = (e & f) ^ (~e & g);
      var t1 = (h + S1 + ch + K256[j] + w[j]) | 0;
      var S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
      var mj = (a & b) ^ (a & c) ^ (b & c);
      var t2 = (S0 + mj) | 0;
      h = g; g = f; f = e; e = (d + t1) | 0;
      d = c; c = b; b = a; a = (t1 + t2) | 0;
    }
    H[0] = (H[0] + a) | 0; H[1] = (H[1] + b) | 0; H[2] = (H[2] + c) | 0; H[3] = (H[3] + d) | 0;
    H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0; H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
  }
  function bytesToWords(bytes, off, words, n) {
    for (var j = 0; j < n; j++) {
      var k = off + j * 4;
      words[j] = ((bytes[k] << 24) | (bytes[k + 1] << 16) | (bytes[k + 2] << 8) | bytes[k + 3]) | 0;
    }
  }
  function wordsToBytes(words, n) {
    var out = new Uint8Array(n * 4);
    for (var j = 0; j < n; j++) {
      out[j * 4] = (words[j] >>> 24) & 255; out[j * 4 + 1] = (words[j] >>> 16) & 255;
      out[j * 4 + 2] = (words[j] >>> 8) & 255; out[j * 4 + 3] = words[j] & 255;
    }
    return out;
  }
  function sha256(msg) {
    var len = msg.length;
    var padded = new Uint8Array(((len + 9 + 63) >> 6) << 6);
    padded.set(msg);
    padded[len] = 0x80;
    var bitLen = len * 8;
    var hi = Math.floor(bitLen / 0x100000000), lo = bitLen >>> 0;
    padded[padded.length - 8] = (hi >>> 24) & 255; padded[padded.length - 7] = (hi >>> 16) & 255;
    padded[padded.length - 6] = (hi >>> 8) & 255; padded[padded.length - 5] = hi & 255;
    padded[padded.length - 4] = (lo >>> 24) & 255; padded[padded.length - 3] = (lo >>> 16) & 255;
    padded[padded.length - 2] = (lo >>> 8) & 255; padded[padded.length - 1] = lo & 255;
    var H = new Int32Array(SHA256_INIT);
    var block = new Int32Array(16);
    for (var i = 0; i < padded.length; i += 64) {
      bytesToWords(padded, i, block, 16);
      sha256Compress(H, block);
    }
    return wordsToBytes(H, 8);
  }

  /* ================= HMAC-SHA256 / PBKDF2 ================= */
  function hmacPads(key) {
    if (key.length > 64) key = sha256(key);
    var ipad = new Uint8Array(64), opad = new Uint8Array(64), i;
    for (i = 0; i < 64; i++) { ipad[i] = (key[i] || 0) ^ 0x36; opad[i] = (key[i] || 0) ^ 0x5c; }
    return { ipad: ipad, opad: opad };
  }
  function hmacWithPads(pads, msg) {
    return sha256(concat(pads.opad, sha256(concat(pads.ipad, msg))));
  }
  function hmacSha256(key, msg) { return hmacWithPads(hmacPads(key), msg); }

  function pbkdf2Sha256(password, salt, iterations, dkLen) {
    var pads = hmacPads(password);
    /* ipad / opad ブロックの圧縮結果 (HMAC 中間状態) を先に 1 回だけ計算し、
       反復本体 (32 バイト固定長メッセージの HMAC) を圧縮 2 回で回す。 */
    var block = new Int32Array(16), i, j;
    var ipadState = new Int32Array(SHA256_INIT);
    bytesToWords(pads.ipad, 0, block, 16);
    sha256Compress(ipadState, block);
    var opadState = new Int32Array(SHA256_INIT);
    bytesToWords(pads.opad, 0, block, 16);
    sha256Compress(opadState, block);
    /* 2 ブロック目 = digest(8 ワード) + 0x80 パディング + 長さ 768 bit */
    var tail = new Int32Array(16);
    tail[8] = 0x80000000 | 0;
    tail[15] = 768;
    var H = new Int32Array(8);
    function hmac32(digestWords) { /* digestWords(8) → 上書きで新 digest */
      for (j = 0; j < 8; j++) tail[j] = digestWords[j];
      for (j = 0; j < 8; j++) H[j] = ipadState[j];
      sha256Compress(H, tail);
      for (j = 0; j < 8; j++) tail[j] = H[j];
      for (j = 0; j < 8; j++) H[j] = opadState[j];
      sha256Compress(H, tail);
      for (j = 0; j < 8; j++) digestWords[j] = H[j];
    }
    var blocks = Math.ceil(dkLen / 32);
    var dk = new Uint8Array(blocks * 32);
    for (var bi = 1; bi <= blocks; bi++) {
      var ctr = new Uint8Array([(bi >>> 24) & 255, (bi >>> 16) & 255, (bi >>> 8) & 255, bi & 255]);
      var u0 = hmacWithPads(pads, concat(salt, ctr));
      var u = new Int32Array(8), t = new Int32Array(8);
      bytesToWords(u0, 0, u, 8);
      for (j = 0; j < 8; j++) t[j] = u[j];
      for (i = 1; i < iterations; i++) {
        hmac32(u);
        for (j = 0; j < 8; j++) t[j] ^= u[j];
      }
      dk.set(wordsToBytes(t, 8), (bi - 1) * 32);
    }
    return dk.subarray(0, dkLen);
  }

  /* ================= ChaCha20 (RFC 8439 のブロック関数) ================= */
  function chacha20Xor(key32, nonce12, data) {
    var out = new Uint8Array(data.length);
    var kv = new DataView(key32.buffer, key32.byteOffset, 32);
    var nv = new DataView(nonce12.buffer, nonce12.byteOffset, 12);
    var state = new Int32Array(16), work = new Int32Array(16), i, j;
    state[0] = 0x61707865; state[1] = 0x3320646e; state[2] = 0x79622d32; state[3] = 0x6b206574;
    for (i = 0; i < 8; i++) state[4 + i] = kv.getUint32(i * 4, true);
    for (i = 0; i < 3; i++) state[13 + i] = nv.getUint32(i * 4, true);
    var counter = 0, pos = 0;
    function qr(a, b, c, d) {
      work[a] = (work[a] + work[b]) | 0; work[d] ^= work[a]; work[d] = (work[d] << 16) | (work[d] >>> 16);
      work[c] = (work[c] + work[d]) | 0; work[b] ^= work[c]; work[b] = (work[b] << 12) | (work[b] >>> 20);
      work[a] = (work[a] + work[b]) | 0; work[d] ^= work[a]; work[d] = (work[d] << 8) | (work[d] >>> 24);
      work[c] = (work[c] + work[d]) | 0; work[b] ^= work[c]; work[b] = (work[b] << 7) | (work[b] >>> 25);
    }
    var block = new Uint8Array(64), bv = new DataView(block.buffer);
    while (pos < data.length) {
      state[12] = counter++;
      for (i = 0; i < 16; i++) work[i] = state[i];
      for (i = 0; i < 10; i++) {
        qr(0, 4, 8, 12); qr(1, 5, 9, 13); qr(2, 6, 10, 14); qr(3, 7, 11, 15);
        qr(0, 5, 10, 15); qr(1, 6, 11, 12); qr(2, 7, 8, 13); qr(3, 4, 9, 14);
      }
      for (i = 0; i < 16; i++) bv.setUint32(i * 4, (work[i] + state[i]) | 0, true);
      var n = Math.min(64, data.length - pos);
      for (j = 0; j < n; j++) out[pos + j] = data[pos + j] ^ block[j];
      pos += n;
    }
    return out;
  }

  /* ================= Kauffman ブラケット (zone-lib.bada の移植) ================= */
  function ipow(base, e) {
    var r = 1.0, k, m;
    if (e < 0) { m = -e; for (k = 0; k < m; k++) r *= base; return 1.0 / r; }
    for (k = 0; k < e; k++) r *= base;
    return r;
  }
  function ufFind(parent, x) {
    var r = x;
    while (parent[r] >= 0) r = parent[r];
    return r;
  }
  /* cross: [[id, e0, e1, e2, e3, sign], ...] — zone_diagram() と同形式 */
  function kauffman(cross, A) {
    var n = cross.length;
    if (n === 0) return 1.0;
    var maxlbl = 0, i, k;
    for (i = 0; i < n; i++) for (k = 1; k <= 4; k++) if (cross[i][k] > maxlbl) maxlbl = cross[i][k];
    var U = maxlbl + 1;
    var states = 1 << n;
    var d = -(A * A) - 1.0 / (A * A);
    var sum = 0.0;
    for (var st = 0; st < states; st++) {
      var parent = new Int32Array(U).fill(-1);
      var aCnt = 0, bCnt = 0;
      for (i = 0; i < n; i++) {
        var e0 = cross[i][1], e1 = cross[i][2], e2 = cross[i][3], e3 = cross[i][4];
        var ra, rb;
        if (((st >> i) & 1) === 0) {
          ra = ufFind(parent, e0); rb = ufFind(parent, e1); if (ra !== rb) parent[ra] = rb;
          ra = ufFind(parent, e2); rb = ufFind(parent, e3); if (ra !== rb) parent[ra] = rb;
          aCnt++;
        } else {
          ra = ufFind(parent, e1); rb = ufFind(parent, e2); if (ra !== rb) parent[ra] = rb;
          ra = ufFind(parent, e3); rb = ufFind(parent, e0); if (ra !== rb) parent[ra] = rb;
          bCnt++;
        }
      }
      var seen = new Uint8Array(U), loops = 0, lbl;
      for (lbl = 0; lbl < U; lbl++) {
        var r = ufFind(parent, lbl);
        if (!seen[r]) { seen[r] = 1; loops++; }
      }
      sum += ipow(A, aCnt - bCnt) * ipow(d, loops - 1);
    }
    return sum;
  }
  function f5(x) { return x.toFixed(5); }
  function jonesKey(diagram) {
    var As = [0.8, 1.0, 1.2, 1.5, 2.0];
    var acc = "jones|", i;
    for (i = 0; i < As.length; i++) acc += f5(kauffman(diagram, As[i])) + "|";
    return hex(sha256(utf8(acc)));
  }

  /* 結び目カタログ — 0/1 は zone_diagram() の図をそのまま採用 */
  var KNOTS = [
    { id: 0, name: "三葉結び目 (trefoil 3₁)",
      diagram: [[0, 1, 2, 3, 4, 1], [1, 3, 4, 5, 6, 1], [2, 5, 6, 1, 2, 1]] },
    { id: 1, name: "8の字結び目 (figure-eight 4₁)",
      diagram: [[0, 1, 2, 3, 4, 1], [1, 3, 4, 5, 6, 1], [2, 5, 6, 7, 8, 1], [3, 7, 8, 1, 2, 1]] },
    { id: 2, name: "五葉結び目 (cinquefoil 5₁)",
      diagram: [[0, 1, 2, 3, 4, 1], [1, 3, 4, 5, 6, 1], [2, 5, 6, 7, 8, 1], [3, 7, 8, 9, 10, 1], [4, 9, 10, 1, 2, 1]] }
  ];

  /* ================= Bell 対 QKD セッション (シミュレーション) ================= */
  function qkdSession() {
    /* (|00> + |11>)/√2 を用意して測定 — 相関ビット列を採取 */
    var rounds = 16, bits = [], i;
    var rnd = randomBytes(rounds);
    for (i = 0; i < rounds; i++) {
      var outcome = rnd[i] & 1; /* 測定で 00 か 11 に収縮 → 双方同じビット */
      bits.push(outcome);
    }
    return { bits: bits, basis: "Bell (|00>+|11>)/√2 × " + rounds };
  }

  /* ================= 鍵導出 ================= */
  var MAGIC = utf8("BQC1");
  var VERSION = 1;
  var PBKDF2_ITERS = 24000;

  function deriveKeys(passphrase, knotId, salt) {
    var knot = KNOTS[knotId] || KNOTS[0];
    var jk = jonesKey(knot.diagram);
    var saltMix = concat(salt, utf8("BadaQC1|" + jk));
    var dk = pbkdf2Sha256(utf8(passphrase), saltMix, PBKDF2_ITERS, 64);
    return { encKey: dk.subarray(0, 32), macKey: dk.subarray(32, 64), jones: jk, knot: knot };
  }

  /* ================= コンテナ 暗号化 / 復号 ================= */
  function encryptBytes(passphrase, plainBytes, opts) {
    opts = opts || {};
    var knotId = (opts.knotId | 0) % KNOTS.length;
    var isFile = !!opts.filename;
    var salt = randomBytes(16);
    var qkd = qkdSession();
    var nonce = randomBytes(12);
    /* QKD の相関ビットを nonce に折り込む (双方が同じ列を観測する想定) */
    for (var i = 0; i < 12 && i < qkd.bits.length; i++) nonce[i] ^= qkd.bits[i];
    var keys = deriveKeys(passphrase, knotId, salt);
    var nameBytes = isFile ? utf8(String(opts.filename)) : new Uint8Array(0);
    if (nameBytes.length > 65535) nameBytes = nameBytes.subarray(0, 65535);
    var header = concat(
      MAGIC,
      new Uint8Array([VERSION, isFile ? 1 : 0, knotId, salt.length]),
      salt, nonce,
      new Uint8Array([(nameBytes.length >> 8) & 255, nameBytes.length & 255]),
      nameBytes
    );
    var ct = chacha20Xor(keys.encKey, nonce, plainBytes);
    var tag = hmacWithPads(hmacPads(keys.macKey), concat(header, ct));
    return {
      container: concat(header, ct, tag),
      meta: {
        knot: keys.knot.name, jones: keys.jones, qkd: qkd.basis,
        qkdBits: qkd.bits.join(""), salt: hex(salt), nonce: hex(nonce),
        tag: hex(tag), plainLen: plainBytes.length, cipherLen: ct.length
      }
    };
  }

  function decryptContainer(passphrase, container) {
    if (container.length < 4 + 4 + 12 + 2 + 32) throw new Error("データが短すぎます (BQC1 コンテナではありません)");
    for (var i = 0; i < 4; i++) if (container[i] !== MAGIC[i]) throw new Error("マジックが一致しません (BQC1 コンテナではありません)");
    var ver = container[4], flags = container[5], knotId = container[6], saltLen = container[7];
    if (ver !== VERSION) throw new Error("未対応バージョンです: " + ver);
    var off = 8;
    var salt = container.subarray(off, off + saltLen); off += saltLen;
    var nonce = container.subarray(off, off + 12); off += 12;
    var nameLen = (container[off] << 8) | container[off + 1]; off += 2;
    var nameBytes = container.subarray(off, off + nameLen); off += nameLen;
    if (container.length < off + 32) throw new Error("コンテナが壊れています");
    var header = container.subarray(0, off);
    var ct = container.subarray(off, container.length - 32);
    var tag = container.subarray(container.length - 32);
    var keys = deriveKeys(passphrase, knotId, salt);
    var expect = hmacWithPads(hmacPads(keys.macKey), concat(header, ct));
    if (!ctEq(expect, tag)) {
      throw new Error("解除失敗: 認証タグが一致しません (パスフレーズが違うか、データが改ざんされています) — 409 zone-guard-reject");
    }
    var plain = chacha20Xor(keys.encKey, nonce, ct);
    return {
      plain: plain,
      isFile: (flags & 1) === 1,
      filename: nameLen ? utf8dec(nameBytes) : "",
      meta: {
        knot: keys.knot.name, jones: keys.jones, salt: hex(salt),
        nonce: hex(nonce), tag: hex(tag), plainLen: plain.length, cipherLen: ct.length
      }
    };
  }

  /* ================= アーマー (テキスト形式) ================= */
  var ARMOR_BEGIN = "-----BEGIN BADA QUANTUM CIPHER-----";
  var ARMOR_END = "-----END BADA QUANTUM CIPHER-----";
  function armor(container) {
    var b = b64enc(container), lines = [], i;
    for (i = 0; i < b.length; i += 64) lines.push(b.substring(i, i + 64));
    return ARMOR_BEGIN + "\n" + lines.join("\n") + "\n" + ARMOR_END;
  }
  function dearmor(text) {
    var s = text.indexOf(ARMOR_BEGIN), e = text.indexOf(ARMOR_END);
    var body = (s >= 0 && e > s) ? text.substring(s + ARMOR_BEGIN.length, e) : text;
    var bytes = b64dec(body);
    if (bytes.length === 0) throw new Error("アーマー本文が見つかりません");
    return bytes;
  }
  function isArmored(text) { return text.indexOf(ARMOR_BEGIN) >= 0; }

  /* ================= 高水準 API ================= */
  function encryptText(passphrase, text, knotId) {
    var r = encryptBytes(passphrase, utf8(text), { knotId: knotId });
    return { armored: armor(r.container), meta: r.meta };
  }
  function decryptText(passphrase, armoredText) {
    var r = decryptContainer(passphrase, dearmor(armoredText));
    return { text: utf8dec(r.plain), filename: r.filename, isFile: r.isFile, meta: r.meta };
  }

  var BadaQC = {
    VERSION: VERSION,
    PBKDF2_ITERS: PBKDF2_ITERS,
    KNOTS: KNOTS,
    ARMOR_BEGIN: ARMOR_BEGIN,
    ARMOR_END: ARMOR_END,
    sha256: sha256,
    hmacSha256: hmacSha256,
    pbkdf2Sha256: pbkdf2Sha256,
    chacha20Xor: chacha20Xor,
    kauffman: kauffman,
    jonesKey: jonesKey,
    qkdSession: qkdSession,
    encryptBytes: encryptBytes,
    decryptContainer: decryptContainer,
    encryptText: encryptText,
    decryptText: decryptText,
    armor: armor,
    dearmor: dearmor,
    isArmored: isArmored,
    utf8: utf8,
    utf8dec: utf8dec,
    hex: hex,
    b64enc: b64enc,
    b64dec: b64dec
  };

  if (typeof module !== "undefined" && module.exports) module.exports = BadaQC;
  global.BadaQC = BadaQC;
})(typeof globalThis !== "undefined" ? globalThis : this);
