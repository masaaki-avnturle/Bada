/*
 * net.js — WebRTC の接続コードと、SHA-256 つきパケット
 *
 * 端末どうしの最初の 1 本は、接続コードを相手に渡してつなぐ (招待コード → 返信コード)。
 * つながったデータチャネルは p2p.js の Node に渡し、そこから先のリンクは網が自動で張る。
 * 既定では STUN サーバーを使わないので、接続できるのは同じ LAN の中。
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

  function gathered(pc) {
    return new Promise(function (resolve) {
      if (pc.iceGatheringState === "complete") return resolve();
      var done = function () { if (pc.iceGatheringState === "complete") { pc.removeEventListener("icegatheringstatechange", done); resolve(); } };
      pc.addEventListener("icegatheringstatechange", done); setTimeout(resolve, 4000);
    });
  }
  // データチャネルを P2P の端末 (p2p.js の Node) につなぐ
  function bind(node, ch, pc) {
    var chan = { send: function (t) { ch.send(t); }, close: function () { try { ch.close(); pc.close(); } catch (e) { } } }, dead = false;
    var open = function () { node.attach(chan); };
    var close = function () { if (!dead) { dead = true; node.closed(chan); } };
    if (ch.readyState === "open") open(); else ch.onopen = open;
    ch.onmessage = function (ev) { node.receive(chan, ev.data); };
    ch.onclose = close;
    // 相手が急に消えた場合、データチャネルの close は遅れて届く。接続の状態が切れた時点で閉じたものとして扱う
    pc.addEventListener("connectionstatechange", function () { if (/^(disconnected|failed|closed)$/.test(pc.connectionState)) close(); });
  }
  // WebRTC の接続コード: offer() → 相手が answer(code) → 自分が accept(pc, code)。STUN は使わない (同じ LAN の中)
  var Rtc = {
    offer: async function (node) {
      var pc = new RTCPeerConnection({ iceServers: [] }); bind(node, pc.createDataChannel("zone"), pc);
      await pc.setLocalDescription(await pc.createOffer()); await gathered(pc);
      return { pc: pc, code: b64.enc(JSON.stringify(pc.localDescription)) };
    },
    answer: async function (node, code) {
      var pc = new RTCPeerConnection({ iceServers: [] });
      pc.ondatachannel = function (ev) { bind(node, ev.channel, pc); };
      await pc.setRemoteDescription(JSON.parse(b64.dec(code)));
      await pc.setLocalDescription(await pc.createAnswer()); await gathered(pc);
      return { pc: pc, code: b64.enc(JSON.stringify(pc.localDescription)) };
    },
    accept: async function (pc, code) { await pc.setRemoteDescription(JSON.parse(b64.dec(code))); }
  };

  global.BadaNet = { Rtc: Rtc, bind: bind, pack: pack, unpack: unpack, b64: b64 };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaNet;
})(typeof window !== "undefined" ? window : globalThis);
