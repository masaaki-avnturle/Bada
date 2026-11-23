/*
 * p2p.js — zone:// ウルトラネットワークの上の P2P 網 (主催者なし。どの端末も対等)
 *
 *   ・各端末はリング上の位置 zone_id("peer:" + 名前) を持つ
 *   ・最初の 1 本だけ手でつなぐ (接続コード)。あとは、知っている端末の一覧をうわさで広げ、
 *     リング上の隣接 (次・前・2 つ先) へ、網を通した合図の中継で自動的にリンクを張る
 *   ・宛先つきの電文は、宛先の位置に近い隣へ貪欲に転送する (zone_route と同じ考え方)。
 *     近づける隣が無いときは、重複を捨てながら全リンクへ広げる
 *   ・会議の部屋は zone://<部屋>.zone.jp/meeting。その鍵 zone_id(URL) に最も近い端末が
 *     「担当」になり、発言に通し番号を付けて全員へ広げる。担当が抜ければ次に近い端末が引き継ぐ
 *   ・会議の電文は、部屋の結び目から導いた Jones 鍵で封印する (zone_seal)。開けられない電文は捨てる。
 *     つなぐときにも、同じ鍵で封印した証明を求める (鍵の違う端末は網に入れない)
 *   ・担当は、役割の発言が議事録の続きとして正しいときだけ番号を付ける (同じ役割の二重発言を防ぐ)
 *   ・zone:// のレコード (議事録など) は、URL の鍵に最も近い端末が預かる (PUT / GET)
 *
 * 通信路には依存しない: attach(chan) に {send(text)} を渡し、届いた文字列を receive(chan, text) に渡す。
 */
(function (global) {
  "use strict";
  var Z = global.BadaZone || (typeof require !== "undefined" ? require("./zone.js") : null);

  function Node(o) {
    this.name = o.name; this.id = Z.peerId(o.name); this.room = o.room; this.key = o.key;
    this.url = "zone://" + o.room + ".zone.jp/meeting"; this.rkey = Z.zoneId(this.url);
    this.minutes = o.minutes; this.onMeeting = o.onMeeting; this.onChange = o.onChange || function () {};
    this.onNeedLink = o.onNeedLink || function () {}; this.onSignal = o.onSignal || function () {};
    this.validate = o.validate || function () { return true; };
    this.random = o.random || Math.random;
    this.links = {}; this.chans = []; this.members = {}; this.members[this.name] = { id: this.id };
    this.seen = {}; this.n = 0; this.dialing = {}; this.store = {}; this.waiting = {}; this.rejects = 0; this.lastRoute = [];
  }
  var P = Node.prototype;
  P.memberList = function () { var m = this.members; return Object.keys(m).map(function (n) { return { name: n, id: m[n].id }; }); };
  P.owner = function () { return Z.nearest(this.memberList(), this.rkey).name; };
  P.peers = function () { return Object.keys(this.links).length; };
  P._mid = function () { return this.name + "#" + (++this.n) + "#" + Math.floor(this.random() * 1e9).toString(36); };
  P._seal = function (obj) { return Z.seal(JSON.stringify(obj), this.key, Math.floor(this.random() * 4096)); };
  P._open = function (sealed) { var t = Z.open(sealed, this.key); if (t === null) { this.rejects++; this.onChange(); return null; } try { return JSON.parse(t); } catch (e) { this.rejects++; return null; } };
  P._send = function (name, frame) { var c = this.links[name]; if (c) { try { c.send(JSON.stringify(frame)); return true; } catch (e) { } } return false; };
  P._all = function (frame, except) { var self = this; Object.keys(this.links).forEach(function (n) { if (n !== except) self._send(n, frame); }); };

  /* ── リンクの開閉と、端末の一覧 ── */
  P.attach = function (chan) { this.chans.push(chan); chan.send(JSON.stringify({ t: "hello", name: this.name, room: this.room, members: Object.keys(this.members), proof: this._seal({ hello: this.name }) })); };
  P.closed = function (chan) {
    var self = this, name = Object.keys(this.links).filter(function (n) { return self.links[n] === chan; })[0];
    this.chans = this.chans.filter(function (c) { return c !== chan; });
    if (!name) return;
    delete this.links[name]; delete this.members[name];
    this._flood("gone", { name: name }); this._rebalance(); this.onChange();
  };
  P._learn = function (names) {
    var self = this, added = false;
    (names || []).forEach(function (n) { if (typeof n === "string" && n && !self.members[n]) { self.members[n] = { id: Z.peerId(n) }; added = true; } });
    if (added) { this._all({ t: "members", names: Object.keys(this.members) }); this._rebalance(); this.onChange(); }
  };
  // リング上の隣接へのリンクが無ければ張る。互いに隣接なら名前の小さい側から (両側から同時に張らないように)。
  // 「2 つ先」のように自分だけが必要とするリンクは、自分から張る
  P._rebalance = function () {
    var self = this, list = this.memberList();
    Z.neighbors(list, this.name).forEach(function (n) {
      var mutual = Z.neighbors(list, n).indexOf(self.name) >= 0;
      if (!self.links[n] && !self.dialing[n] && (!mutual || self.name < n)) { self.dialing[n] = true; self.onNeedLink(n); }
    });
  };
  P.dialFailed = function (name) { if (this.dialing[name]) { delete this.dialing[name]; if (!this.links[name]) this._rebalance(); } };   // つながらなければ張り直す
  // 網を抜ける: 抜けることを全員に知らせてから、リンクを閉じる
  P.leave = function () {
    this._flood("gone", { name: this.name });
    this.chans.forEach(function (c) { if (c.close) c.close(); });
  };
  P.signal = function (to, body) { this._route(to, "signal", body); };

  /* ── 電文の受信 ── */
  P.receive = function (chan, text) {
    var f; try { f = JSON.parse(text); } catch (e) { return; }
    if (!f || typeof f !== "object") return;
    if (f.t === "hello") {
      if (typeof f.name !== "string" || !f.name || f.name === this.name || f.room !== this.room) return;
      var proof = this._open(f.proof); if (!proof || proof.hello !== f.name) return;      // 結び目 (鍵) が違う端末とはつながない
      this.links[f.name] = chan; delete this.dialing[f.name];
      this._learn([f.name].concat(f.members || []));
      this._send(f.name, { t: "members", names: Object.keys(this.members) });
      this._send(f.name, { t: "sync", body: this._seal({ msgs: this.minutes() }) });
      this._rebalance(); this.onChange(); return;
    }
    var from = null, self = this; Object.keys(this.links).forEach(function (n) { if (self.links[n] === chan) from = n; });
    if (!from) return;                                   // hello の前の電文は受け付けない
    if (f.t === "members") return this._learn(f.names);
    if (f.t === "sync") { var s = this._open(f.body); if (s) this._sync(s.msgs || []); return; }
    if (!f.mid || this.seen[f.mid]) return;              // 重複は捨てる (輪を回らない)
    this.seen[f.mid] = true;
    f.path = (f.path || []).concat([this.name]);
    if (f.t === "flood") { this._all(f, from); this._handleFlood(f); }
    else if (f.t === "route") this._forward(f, from);
  };
  // 相手の議事録を取り込む: 自分が空なら全部、同じ議題なら足りない分
  P._sync = function (msgs) {
    var mine = this.minutes();
    if (!msgs.length || (mine.length && mine[0].text !== msgs[0].text) || msgs.length <= mine.length) return;
    for (var i = mine.length ? mine.length : 0; i < msgs.length; i++) this.onMeeting(msgs[i]);
  };

  /* ── 全員へ広げる ── */
  P._flood = function (kind, body) {
    var f = { t: "flood", mid: this._mid(), kind: kind, body: body, path: [this.name] };
    this.seen[f.mid] = true; this._all(f, null);
  };
  P._handleFlood = function (f) {
    if (f.kind === "msg") { var m = this._open(f.body); if (m) { this.lastRoute = f.path; this.onMeeting(m); this.onChange(); } }
    else if (f.kind === "gone" && f.body && f.body.name !== this.name && this.members[f.body.name] && (!this.links[f.body.name] || f.path[0] === f.body.name)) {
      delete this.members[f.body.name]; delete this.links[f.body.name]; this._rebalance(); this.onChange();     // 本人からの知らせなら、直結していても外す
    }
  };

  /* ── 宛先つきの電文: 貪欲な転送 ── */
  P._route = function (to, kind, body) {
    var f = { t: "route", mid: this._mid(), to: to, kind: kind, body: body, path: [this.name], ttl: 16 };
    this.seen[f.mid] = true; this._forward(f, null);
  };
  P._forward = function (f, from) {
    if (f.to === this.name) return this._deliver(f);
    if (--f.ttl <= 0) return;
    if (this._send(f.to, f)) return;                     // 直接つながっていればそのまま
    var self = this, target = Z.peerId(f.to), best = null, bd = Z.ringDist(this.id, target);
    if (!f.spread) Object.keys(this.links).forEach(function (n) { var d = Z.ringDist(self.members[n] ? self.members[n].id : Z.peerId(n), target); if (d < bd) { bd = d; best = n; } });
    if (best) this._send(best, f);
    else if (f.spread) this._all(f, from);
    else {                                                // 近づける隣が無い: 全リンクへ広げる。来た道を戻れるよう、別の電文として出し直す (重複は受け側が捨てる)
      f.spread = true; f.mid = f.mid + "~"; this.seen[f.mid] = true; this._all(f, null);
    }
  };
  P._deliver = function (f) {
    var from = f.path[0], b = f.body;
    this.lastRoute = f.path;
    if (f.kind === "signal") this.onSignal(from, b);
    else if (f.kind === "draft") { var d = this._open(b); if (d) this._draft(d); }
    else if (f.kind === "put") { this.store[b.url] = b.sealed; }
    else if (f.kind === "get") this._route(from, "reply", { rid: b.rid, sealed: this.store[b.url] || null });
    else if (f.kind === "reply" && this.waiting[b.rid]) { var cb = this.waiting[b.rid]; delete this.waiting[b.rid]; cb(b.sealed, f.path); }
    this.onChange();
  };

  /* ── 会議 ── */
  P.send = function (draft) { this._draft(draft); };
  P._draft = function (draft) {
    var owner = this.owner();
    if (owner !== this.name) return this._route(owner, "draft", this._seal(draft));
    if (!this.validate(draft)) return;                                                              // 議事録の続きとして正しくない発言は採らない
    var m = Object.assign({}, draft, { seq: draft.kind === "agenda" ? 0 : this.minutes().length });   // 担当が通し番号を付ける
    this._flood("msg", this._seal(m)); this.lastRoute = [this.name]; this.onMeeting(m);
  };

  /* ── zone:// レコード ── */
  P.zoneOwner = function (url) { return Z.nearest(this.memberList(), Z.zoneId(url)).name; };
  P.put = function (url, text) {
    if (!Z.parse(url)) throw new Error("zone:// の URL ではありません");
    var owner = this.zoneOwner(url), sealed = this._seal({ text: text });
    if (owner === this.name) this.store[url] = sealed; else this._route(owner, "put", { url: url, sealed: sealed });
    return owner;
  };
  // cb(status, text, path): 200 / 404 zone-not-found / 409 zone-guard-reject
  P.get = function (url, cb) {
    if (!Z.parse(url)) return cb(400, "zone:// の URL ではありません", []);
    var self = this, owner = this.zoneOwner(url);
    var done = function (sealed, path) {
      if (!sealed) return cb(404, "zone-not-found", path);
      var o = Z.open(sealed, self.key); if (o === null) return cb(409, "zone-guard-reject", path);
      cb(200, JSON.parse(o).text, path);
    };
    if (owner === this.name) return done(this.store[url] || null, [this.name]);
    var rid = this._mid(); this.waiting[rid] = done; this._route(owner, "get", { url: url, rid: rid });
  };
  P.info = function () {
    var self = this, owner = this.owner();
    return { name: this.name, id: this.id, url: this.url, key: this.rkey, owner: owner, rejects: this.rejects, lastRoute: this.lastRoute,
             members: Z.sortRing(this.memberList()).map(function (p) { return { name: p.name, id: p.id, self: p.name === self.name, direct: !!self.links[p.name], owner: p.name === owner }; }) };
  };

  global.BadaP2P = { Node: Node };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaP2P;
})(typeof window !== "undefined" ? window : globalThis);
