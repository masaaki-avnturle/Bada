/*
 * net.js — コンピュータ同士のやり取り (サーバーなし)
 *
 * 発言は「パケット」(JSON テキスト + SHA-256) にして送ります。経路は 2 つ:
 *   ・1 台の中だけ (ループバック)
 *   ・WebRTC データチャネル。接続は「接続コード」を相手に渡して行います
 *     (主催者がコードを作る → 参加者が貼り付けて返信コードを作る → 主催者が貼り付ける)。
 *     既定では STUN サーバーを使わないので、同じ LAN の中で接続できます。
 * 主催者が発言に通し番号を付けて全員に配るので、全員の議事録が同じ順序になります。
 */
(function (global) {
  "use strict";
  var E = global.BadaGPTEngine || (typeof require !== "undefined" ? require("../../bada_gpt/src/engine.js") : null);

  function pack(body) { var text = JSON.stringify(body); return JSON.stringify({ v: 1, body: text, sha256: E.hex(E.sha256(text)) }); }
  function unpack(raw) {
    var o = JSON.parse(raw);
    if (!o || o.v !== 1 || typeof o.body !== "string" || E.hex(E.sha256(o.body)) !== o.sha256) throw new Error("パケットが壊れています");
    return JSON.parse(o.body);
  }
  var b64 = {
    enc: function (s) { return btoa(unescape(encodeURIComponent(s))); },
    dec: function (s) { return decodeURIComponent(escape(atob(String(s).trim()))); }
  };

  // Hub: 主催者 (通し番号を付けて配る) または参加者 (主催者へ送る)
  function Hub(opts) {
    this.host = !!opts.host; this.onMessage = opts.onMessage || function () {}; this.onPeers = opts.onPeers || function () {};
    this.seq = 0; this.links = []; this.iceServers = opts.iceServers || [];
  }
  Hub.prototype.send = function (draft) {             // draft = {role, name, kind, text, data}
    if (this.host) this._stamp(draft);
    else if (this.links[0] && this.links[0].ch && this.links[0].ch.readyState === "open") this.links[0].ch.send(pack({ t: "draft", m: draft }));
    else throw new Error("主催者につながっていません");
  };
  Hub.prototype._stamp = function (draft) {
    if (draft.kind === "agenda") this.seq = 0;
    var m = Object.assign({}, draft, { seq: this.seq++ }), raw = pack({ t: "msg", m: m });
    this.links.forEach(function (l) { if (l.ch && l.ch.readyState === "open") l.ch.send(raw); });
    this.onMessage(m);
  };
  Hub.prototype._receive = function (raw) {
    var p; try { p = unpack(raw); } catch (e) { return; }      // 壊れたパケットは捨てる
    if (this.host && p.t === "draft") this._stamp(p.m);
    else if (!this.host && p.t === "msg") this.onMessage(p.m);
    else if (!this.host && p.t === "sync") p.msgs.forEach(this.onMessage);
  };
  Hub.prototype.peers = function () { return this.links.filter(function (l) { return l.ch && l.ch.readyState === "open"; }).length; };
  Hub.prototype._wire = function (link, history) {
    var self = this;
    link.ch.onopen = function () { if (self.host && history) link.ch.send(pack({ t: "sync", msgs: history() })); self.onPeers(self.peers()); };
    link.ch.onclose = function () { self.onPeers(self.peers()); };
    link.ch.onmessage = function (ev) { self._receive(ev.data); };
  };
  function gathered(pc) {
    return new Promise(function (resolve) {
      if (pc.iceGatheringState === "complete") return resolve();
      var done = function () { if (pc.iceGatheringState === "complete") { pc.removeEventListener("icegatheringstatechange", done); resolve(); } };
      pc.addEventListener("icegatheringstatechange", done); setTimeout(resolve, 4000);
    });
  }
  // 主催者: 招待コードを作る。history() は参加時に送る、それまでの議事録
  Hub.prototype.invite = async function (history) {
    var pc = new RTCPeerConnection({ iceServers: this.iceServers }), link = { pc: pc, ch: pc.createDataChannel("meeting") };
    this.links.push(link); this._wire(link, history);
    await pc.setLocalDescription(await pc.createOffer()); await gathered(pc);
    return { link: link, code: b64.enc(JSON.stringify(pc.localDescription)) };
  };
  Hub.prototype.accept = async function (link, answerCode) { await link.pc.setRemoteDescription(JSON.parse(b64.dec(answerCode))); };
  // 参加者: 招待コードから返信コードを作る
  Hub.prototype.join = async function (inviteCode) {
    var self = this, pc = new RTCPeerConnection({ iceServers: this.iceServers }), link = { pc: pc, ch: null };
    this.links = [link];
    pc.ondatachannel = function (ev) { link.ch = ev.channel; self._wire(link); };
    await pc.setRemoteDescription(JSON.parse(b64.dec(inviteCode)));
    await pc.setLocalDescription(await pc.createAnswer()); await gathered(pc);
    return b64.enc(JSON.stringify(pc.localDescription));
  };

  global.BadaNet = { Hub: Hub, pack: pack, unpack: unpack, b64: b64 };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaNet;
})(typeof window !== "undefined" ? window : globalThis);
