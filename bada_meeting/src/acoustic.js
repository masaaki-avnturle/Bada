/*
 * acoustic.js — 音響電信で会議の発言をやり取りする (接続の手続きなし。同じ部屋、または通話越し)
 *
 * AcousticLink: 送受信の規則 (音声には依存しない。io.transmit にフレーム本体の列を渡す)
 *   ・発言の通し番号 = 送る時点の議事録の長さ。受け取った側は、自分の議事録の長さと合うものだけ採る
 *   ・役割の発言は種類 1 のパケット (ハッシュだけ) で送り、受け取った側が自分のエージェントで再現する
 *   ・議題と人の発言は種類 2 (UTF-8 の文章。複数行可) で送る
 *   ・次の発言が聞こえなければ送り直す (役割の発言は 3 回まで、文章は 1 回)
 *   ・先の番号の発言が聞こえたら (= 聞き逃しがある)、足りない番号を要求する。その発言をした端末が送り直す
 * AcousticAudio: スピーカーで鳴らし、マイクで聞く (ブラウザの WebAudio)
 */
(function (global) {
  "use strict";
  var req = function (g, f) { return global[g] || (typeof require !== "undefined" ? require(f) : null); };
  var Tg = req("BadaTelegraph", "./telegraph.js"), E = req("BadaGPTEngine", "../../bada_gpt/src/engine.js");
  var hash4 = function (text) { return E.sha256(text).slice(0, 4); };
  var same = function (a, b) { return a.length === b.length && a.every(function (x, i) { return x === b[i]; }); };

  function AcousticLink(opts) {
    this.meeting = opts.meeting; this.onMessage = opts.onMessage; this.io = opts.io; this.retryMs = opts.retryMs || 6000;
    this.timers = opts.timers || { set: setTimeout, clear: clearTimeout };
    this.asm = new Tg.Assembler(); this.last = null; this.timer = null; this.heard = 0; this.sent = {}; this.asked = false;
  }
  AcousticLink.prototype.peers = function () { return this.heard ? 1 : 0; };
  AcousticLink.prototype.send = function (draft) {
    var mt = this.meeting(), m = Object.assign({}, draft, { seq: draft.kind === "agenda" ? 0 : mt.msgs.length });
    var byAgent = draft.kind !== "agenda" && draft.kind !== "comment";
    var packets = Tg.encodeMessage(m, byAgent, byAgent ? hash4(m.text) : null);
    if (m.kind === "agenda") this.sent = {};
    this.sent[m.seq] = packets;
    this.onMessage(m);
    this.last = { packets: packets, seq: m.seq, left: byAgent ? 3 : 1, text: m.text };
    this.io.transmit(packets); this._arm();
  };
  AcousticLink.prototype._arm = function () {
    var self = this; this.timers.clear(this.timer);
    this.timer = this.timers.set(function () {
      var mt = self.meeting(), l = self.last;
      if (!l || l.left <= 0 || mt.decided() || mt.msgs.length !== l.seq + 1 || mt.msgs[l.seq].text !== l.text) return;   // 次の発言が来ていれば送り直さない
      l.left--; self.io.transmit(l.packets); self._arm();
    }, this.retryMs);
  };
  // 復調したフレーム本体を 1 つ受け取る
  AcousticLink.prototype.receive = function (bytes) {
    var p = Tg.decodePacket(bytes); if (!p) return;
    this.heard++;
    var mt = this.meeting(), self = this;
    if (p.type === 3) { if (this.sent[p.seq]) this.io.transmit(this.sent[p.seq]); return; }
    var ahead = (p.seq - mt.msgs.length) & 0xFF;
    if (ahead >= 1 && ahead <= 127 && !(p.type === 2 && p.kind === "agenda")) {      // 聞き逃しがある: 足りない番号を要求する (3 秒に 1 回まで)
      if (!this.asked) { this.asked = true; this.timers.set(function () { self.asked = false; }, 3000); this.io.transmit([Tg.requestPacket(mt.msgs.length)]); }
      return;
    }
    if (p.type === 2) {
      var text = this.asm.add(p); if (text === null) return;
      if (p.kind === "agenda") { if (!(mt.msgs.length && mt.msgs[0].text === text)) this.onMessage({ seq: 0, role: p.role, kind: "agenda", text: text, data: {} }); }
      else if (p.seq === (mt.msgs.length & 0xFF)) this.onMessage({ seq: mt.msgs.length, role: p.role, kind: p.kind, text: text, data: {} });
    } else if (p.type === 1 && p.seq === (mt.msgs.length & 0xFF)) {
      var d = mt.next(p.role);                                           // 同じ議事録から、同じ発言を自分で作る
      if (d && d.kind === p.kind && same(Array.from(hash4(d.text)), Array.from(p.body))) this.onMessage(Object.assign({ seq: mt.msgs.length, role: p.role }, d));
    }
  };

  function AcousticAudio(onFrame, onState) { this.onFrame = onFrame; this.onState = onState || function () {}; this.ctx = null; this.demod = null; this.muteUntil = 0; this.queue = Promise.resolve(); this.listening = false; }
  AcousticAudio.prototype.start = async function () {
    var AC = global.AudioContext || global.webkitAudioContext;
    this.ctx = this.ctx || new AC(); if (this.ctx.state === "suspended") await this.ctx.resume();
    this.demod = new Tg.Demodulator(this.ctx.sampleRate, this.onFrame);
    try {
      var stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
      var self = this, src = this.ctx.createMediaStreamSource(stream), proc = this.ctx.createScriptProcessor(4096, 1, 1), sink = this.ctx.createGain();
      sink.gain.value = 0;                                                 // マイクの音をスピーカーに戻さない
      proc.onaudioprocess = function (e) { if (self.ctx.currentTime >= self.muteUntil) self.demod.feed(e.inputBuffer.getChannelData(0)); };   // 自分の送信中は聞かない
      src.connect(proc); proc.connect(sink); sink.connect(this.ctx.destination);
      this.stream = stream; this.listening = true; this.onState("受信中 (マイク)");
    } catch (e) { this.onState("マイクを使えません (送信のみ): " + e.message); }
  };
  AcousticAudio.prototype.stop = function () { if (this.stream) this.stream.getTracks().forEach(function (t) { t.stop(); }); this.listening = false; this.onState("停止"); };
  AcousticAudio.prototype.transmit = function (packets) {
    var self = this;
    this.queue = this.queue.then(async function () {
      if (!self.ctx) return;
      for (var w = 0; w < 30 && self.listening && self.demod.tone && self.ctx.currentTime >= self.muteUntil; w++) await new Promise(function (r) { setTimeout(r, 100 + Math.random() * 200); });   // ほかの端末が送信中なら待つ
      for (var i = 0; i < packets.length; i++) {
        var s = Tg.modulate(packets[i], self.ctx.sampleRate), buf = self.ctx.createBuffer(1, s.length, self.ctx.sampleRate), src = self.ctx.createBufferSource();
        buf.getChannelData(0).set(s); src.buffer = buf; src.connect(self.ctx.destination);
        var dur = s.length / self.ctx.sampleRate; self.muteUntil = self.ctx.currentTime + dur + 0.25;
        self.onState("送信中 (" + dur.toFixed(1) + " 秒)"); src.start();
        await new Promise(function (r) { src.onended = r; setTimeout(r, dur * 1000 + 500); });
        await new Promise(function (r) { setTimeout(r, 200); });
      }
      self.onState(self.listening ? "受信中 (マイク)" : "送信のみ");
    });
    return this.queue;
  };

  global.BadaAcoustic = { AcousticLink: AcousticLink, AcousticAudio: AcousticAudio, hash4: hash4 };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaAcoustic;
})(typeof window !== "undefined" ? window : globalThis);
