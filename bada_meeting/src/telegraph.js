/*
 * telegraph.js — Bada Telegraph の音響電信 (FSK モデム) と、会議用の小さなパケット
 *
 * 変調方式とフレームは bada_telegraph/www/index.html (BADA グラビトン電信) と同じ:
 *   space 1000 Hz / mark 1600 Hz・100 baud、各バイトは start(0) + 8 bit (LSB 先頭) + stop(1)、
 *   フレーム = プリアンブル (mark 12 bit) + SOF 0x7E + 長さ + 本体 + チェックサム (8 bit の和)
 * 元の実装との違い: 連続した入力を流しながら復調できる / チェックサムを実際に照合する /
 *   無音や雑音を信号と見なさないよう、2 つの周波数に電力が集まっている区間だけを読む。
 *
 * 会議パケット (フレームの本体。全員が同じエージェントを持つので、発言の本文は送らない):
 *   'B' 'M' 版 種類 通し番号 役割 発言の種類 部分番号 部分数 … 本体 … CRC-16
 *   種類 1 = 役割の発言: 本体は発言文の SHA-256 の先頭 4 バイト。受け取った側が自分のエージェントで
 *            同じ発言を作り、ハッシュが合えば議事録に加える
 *   種類 2 = 文章 (議題や人の発言): 本体は UTF-8。長い文章 (複数行を含む) は部分に分けて送る
 *   種類 3 = 送り直しの要求: 通し番号の発言を聞き逃した端末が送る。その発言をした端末が送り直す
 */
(function (global) {
  "use strict";
  var F_SPACE = 1000, F_MARK = 1600, BAUD = 100, SOF = 0x7E, MAX_BODY = 180;
  var ROLE_IDS = ["host", "kikaku", "planner", "engineer", "guest"];
  var KIND_IDS = ["agenda", "propose", "estimate", "concern", "revise", "schedule", "agree", "decide", "comment"];

  /* ───── 変調 ───── */
  function frameBytes(payload) {
    var body = [SOF, payload.length & 0xFF], sum = 0, i;
    for (i = 0; i < payload.length; i++) body.push(payload[i]);
    for (i = 0; i < body.length; i++) sum = (sum + body[i]) & 0xFF;
    body.push(sum); return body;
  }
  function modulate(payload, sr) {
    if (payload.length > 255) throw new Error("1 フレームは 255 バイトまでです");
    var bits = [], k, i, spb = Math.round(sr / BAUD);
    for (k = 0; k < 12; k++) bits.push(1);
    frameBytes(payload).forEach(function (b) { bits.push(0); for (i = 0; i < 8; i++) bits.push((b >> i) & 1); bits.push(1); });
    for (k = 0; k < 8; k++) bits.push(1);
    var out = new Float32Array(bits.length * spb), ph = 0, idx = 0;
    bits.forEach(function (bit) {
      var dp = 2 * Math.PI * (bit ? F_MARK : F_SPACE) / sr;
      for (i = 0; i < spb; i++) { out[idx++] = Math.sin(ph) * 0.9; ph += dp; if (ph > 2 * Math.PI) ph -= 2 * Math.PI; }
    });
    return out;
  }
  function seconds(payloadLength) { return (12 + 8 + (payloadLength + 3) * 10) / BAUD; }

  /* ───── 復調 (流しながら) ───── */
  function goertzel(s, start, n, f, sr) {
    var c = 2 * Math.cos(2 * Math.PI * f / sr), s1 = 0, s2 = 0, s0, i;
    for (i = 0; i < n; i++) { s0 = s[start + i] + c * s1 - s2; s2 = s1; s1 = s0; }
    return s1 * s1 + s2 * s2 - c * s1 * s2;
  }
  function Demodulator(sr, onFrame) {
    this.sr = sr; this.spb = Math.round(sr / BAUD); this.hop = Math.max(1, Math.round(this.spb / 8));
    this.onFrame = onFrame; this.buf = new Float32Array(0); this.tone = false;
  }
  // 位置 c (サンプル) を中心とする 1 ビット分の判定: +1 mark / −1 space / 0 信号なし
  Demodulator.prototype._bit = function (c) {
    var st = Math.round(c - this.spb / 2), n = this.spb, s = this.buf;
    if (st < 0 || st + n > s.length) return null;
    var m = goertzel(s, st, n, F_MARK, this.sr), sp = goertzel(s, st, n, F_SPACE, this.sr), e = 0, i;
    for (i = 0; i < n; i++) e += s[st + i] * s[st + i];
    if (e < 1e-7 * n || (m + sp) < 0.3 * e * n / 2) return 0;          // 無音、または 2 つの周波数に電力が集まっていない
    return m > sp ? 1 : -1;
  };
  Demodulator.prototype.feed = function (samples) {
    var nb = new Float32Array(this.buf.length + samples.length); nb.set(this.buf); nb.set(samples, this.buf.length); this.buf = nb;
    var spb = this.spb, need = 14 * spb, pos = 0, consumed = 0, guard = 0;
    while (pos + need < this.buf.length && guard++ < 100000) {
      // mark が続いたあと space に変わる点 (start bit の頭) を探す
      var a = this._bit(pos + spb / 2), b = this._bit(pos + spb / 2 + this.hop);
      if (!(a === 1 && b === -1)) { pos += this.hop; if (a === 0) consumed = pos; continue; }
      // 境界を 1 サンプル単位に近づける: mark → space の切り替わりを二分探索
      var lo = pos, hi = pos + this.hop;
      while (hi - lo > 2) { var mid = (lo + hi) >> 1; if (this._bit(mid + spb / 2) === 1) lo = mid; else hi = mid; }
      var start = hi + spb / 2;                                          // start bit の頭
      var bytes = this._bytes(start);
      if (bytes === null) break;                                          // まだ届ききっていない
      if (bytes) { this.onFrame(bytes.payload); pos = Math.round(bytes.end); consumed = pos; }
      else pos += spb;
    }
    this.tone = this._bit(Math.max(spb, this.buf.length - spb)) !== 0;    // 搬送波の有無 (送信前の確認に使う)
    var keep = Math.max(consumed, this.buf.length - Math.round(this.sr * 30));   // 古い分は 30 秒で捨てる
    if (keep > 0) this.buf = this.buf.slice(Math.min(keep, this.buf.length));
  };
  // start から 1 フレーム読む: {payload, end} / false (フレームではない) / null (サンプル不足)
  Demodulator.prototype._bytes = function (start) {
    var spb = this.spb, self = this, pos = start, out = [], len = -1;
    var readByte = function (p) {
      if (self._bit(p + 0.5 * spb) === null || self._bit(p + 9.5 * spb) === null) return null;
      if (self._bit(p + 0.5 * spb) !== -1) return false;                  // start bit は space
      var v = 0, k, bit;
      for (k = 0; k < 8; k++) { bit = self._bit(p + (k + 1.5) * spb); if (bit === 0) return false; if (bit === 1) v |= 1 << k; }
      return self._bit(p + 9.5 * spb) === 1 ? v : false;                  // stop bit は mark
    };
    for (;;) {
      var v = readByte(pos);
      if (v === null) return null;
      if (v === false) return false;
      out.push(v); pos += 10 * spb;
      if (out.length === 1 && v !== SOF) return false;
      if (out.length === 2) len = v;
      if (len >= 0 && out.length === len + 3) break;
    }
    var sum = 0, i; for (i = 0; i < out.length - 1; i++) sum = (sum + out[i]) & 0xFF;
    if (sum !== out[out.length - 1]) return false;
    return { payload: Uint8Array.from(out.slice(2, 2 + len)), end: pos };
  };

  /* ───── 会議パケット ───── */
  function crc16(bytes, n) {
    var crc = 0xFFFF, i, k;
    for (i = 0; i < n; i++) { crc ^= bytes[i] << 8; for (k = 0; k < 8; k++) crc = (crc & 0x8000) ? ((crc << 1) ^ 0x1021) & 0xFFFF : (crc << 1) & 0xFFFF; }
    return crc;
  }
  function packet(type, seq, role, kind, part, parts, body) {
    var p = [0x42, 0x4D, 1, type, seq & 0xFF, Math.max(0, ROLE_IDS.indexOf(role)), Math.max(0, KIND_IDS.indexOf(kind)), part, parts], i;
    for (i = 0; i < body.length; i++) p.push(body[i]);
    var c = crc16(p, p.length); p.push(c >> 8, c & 0xFF);
    return Uint8Array.from(p);
  }
  // 発言 m = {seq, role, kind, text} → フレームの本体の列。hash4 は発言文の SHA-256 の先頭 4 バイト
  function encodeMessage(m, byAgent, hash4) {
    if (byAgent) return [packet(1, m.seq, m.role, m.kind, 0, 1, hash4)];
    var utf = new TextEncoder().encode(m.text), parts = Math.max(1, Math.ceil(utf.length / MAX_BODY)), out = [], i;
    if (parts > 255) throw new Error("文章が長すぎます");
    for (i = 0; i < parts; i++) out.push(packet(2, m.seq, m.role, m.kind, i, parts, utf.subarray(i * MAX_BODY, (i + 1) * MAX_BODY)));
    return out;
  }
  function requestPacket(seq) { return packet(3, seq, "guest", "comment", 0, 1, []); }
  function decodePacket(bytes) {
    if (bytes.length < 11 || bytes[0] !== 0x42 || bytes[1] !== 0x4D || bytes[2] !== 1) return null;
    var n = bytes.length - 2; if (crc16(bytes, n) !== ((bytes[n] << 8) | bytes[n + 1])) return null;
    if (bytes[5] >= ROLE_IDS.length || bytes[6] >= KIND_IDS.length || bytes[7] >= bytes[8]) return null;
    return { type: bytes[3], seq: bytes[4], role: ROLE_IDS[bytes[5]], kind: KIND_IDS[bytes[6]], part: bytes[7], parts: bytes[8], body: bytes.slice(9, n) };
  }
  // 部分に分かれた文章を組み立てる
  function Assembler() { this.key = ""; this.got = []; }
  Assembler.prototype.add = function (p) {
    var key = p.seq + "/" + p.role + "/" + p.kind + "/" + p.parts;
    if (key !== this.key) { this.key = key; this.got = []; }
    this.got[p.part] = p.body;
    for (var i = 0; i < p.parts; i++) if (!this.got[i]) return null;
    var total = this.got.reduce(function (s, b) { return s + b.length; }, 0), all = new Uint8Array(total), o = 0;
    this.got.forEach(function (b) { all.set(b, o); o += b.length; });
    this.key = ""; this.got = [];
    try { return new TextDecoder("utf-8", { fatal: true }).decode(all); } catch (e) { return null; }
  };
  // 検査用: 16 bit PCM の WAV
  function wav(samples, sr) {
    var buf = new ArrayBuffer(44 + samples.length * 2), v = new DataView(buf), i;
    var str = function (o, s) { for (var k = 0; k < s.length; k++) v.setUint8(o + k, s.charCodeAt(k)); };
    str(0, "RIFF"); v.setUint32(4, 36 + samples.length * 2, true); str(8, "WAVEfmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, sr, true); v.setUint32(28, sr * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); str(36, "data"); v.setUint32(40, samples.length * 2, true);
    for (i = 0; i < samples.length; i++) v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, samples[i])) * 32767, true);
    return new Uint8Array(buf);
  }

  global.BadaTelegraph = { F_SPACE: F_SPACE, F_MARK: F_MARK, BAUD: BAUD, MAX_BODY: MAX_BODY, frameBytes: frameBytes, modulate: modulate, seconds: seconds,
    Demodulator: Demodulator, crc16: crc16, encodeMessage: encodeMessage, requestPacket: requestPacket, decodePacket: decodePacket, Assembler: Assembler, wav: wav, ROLE_IDS: ROLE_IDS, KIND_IDS: KIND_IDS };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaTelegraph;
})(typeof window !== "undefined" ? window : globalThis);
