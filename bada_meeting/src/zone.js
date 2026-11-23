/*
 * zone.js — zone:// ウルトラネットワークの計算 (bada_gui_ide/browser/zone-lib.bada の移植)
 *
 *   名前付け   zone_id(s) = str_hash(s) mod 4096。ピアの位置は zone_id("peer:" + 名前)
 *   リング     ring_dist、最も近いピア (dht_nearest)、隣接 ±1 と +2 のフィンガー (peer_neighbors)、
 *              貪欲な転送 (zone_route)
 *   封印       zone_seal / zone_open — (Jones 鍵, ソルト) を種にした鍵ストリーム + 認証タグ
 * Jones 鍵 (結び目図の Kauffman ブラケットから導く鍵) は移植せず、元の zone-lib.bada を
 * Bada 処理系で実行して求める (selfCheck)。同時に、この移植が元のコードと同じ値を返すことを確かめる。
 *
 * 注意: zone の封印は仕組みを示すためのもので、鍵は約 20 ビットしかない。秘密を守る用途には使えない。
 */
(function (global) {
  "use strict";
  var RING = 4096;
  function strHash(s) { var h = 7, i; s = String(s); for (i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 999983; return h; }
  function zoneId(s) { return strHash(s) % RING; }
  function peerId(name) { return zoneId("peer:" + name); }
  function parse(url) {
    url = String(url); if (url.indexOf("zone://") !== 0) return null;
    var rest = url.slice(7), cut = rest.indexOf("/"), host = cut < 0 ? rest : rest.slice(0, cut);
    return host ? { host: host, path: cut < 0 ? "/" : rest.slice(cut), labels: host.split(".") } : null;
  }
  function ringDist(a, b) { var d = Math.abs(a - b); return Math.min(d, RING - d); }
  // peers = [{name, id}]。key に最も近いピア (同じ距離なら名前順で先のもの — 全端末で同じ答えになるように)
  function nearest(peers, key) {
    var best = null;
    peers.forEach(function (p) {
      var d = ringDist(p.id, key);
      if (!best || d < best.d || (d === best.d && p.name < best.p.name)) best = { p: p, d: d };
    });
    return best ? best.p : null;
  }
  function sortRing(peers) { return peers.slice().sort(function (a, b) { return a.id - b.id || (a.name < b.name ? -1 : 1); }); }
  // リング上の隣接: 次・前・2 つ先 (zone-lib の peer_neighbors と同じ)
  function neighbors(peers, name) {
    var ring = sortRing(peers), n = ring.length, i = ring.findIndex(function (p) { return p.name === name; }), out = [];
    if (i < 0 || n < 2) return out;
    [ring[(i + 1) % n], ring[(i + n - 1) % n], ring[(i + 2) % n]].forEach(function (p) { if (p.name !== name && out.indexOf(p.name) < 0) out.push(p.name); });
    return out;
  }
  // start から key へ、隣接だけを使って貪欲に進む経路 (zone_route と同じ規則)
  function route(peers, start, key) {
    var ring = sortRing(peers), by = {}, cur = start, path = [start], hop, moved = true;
    ring.forEach(function (p) { by[p.name] = p; });
    for (hop = 0; moved && hop < 16; hop++) {
      moved = false;
      var best = by[cur];
      neighbors(ring, cur).forEach(function (nb) { if (ringDist(by[nb].id, key) < ringDist(best.id, key)) best = by[nb]; });
      if (best.name !== cur) { cur = best.name; path.push(cur); moved = true; }
    }
    return path;
  }

  /* ── 封印 (鍵ストリーム + 認証タグ) ── */
  function lcg(state) { return (state * 48271) % 2147483647; }
  function keySeed(key, salt) { var s = (key + salt * 2654435761) % 2147483647; return s <= 0 ? s + 2147483646 : s; }
  function tag(ct, key, salt) { var h = (key % 999983) + salt + 1, i; for (i = 0; i < ct.length; i++) h = (h * 31 + ct[i] + 7) % 2147483647; return h; }
  function seal(plain, key, salt) {
    var state = keySeed(key, salt), ct = [], i;
    for (i = 0; i < plain.length; i++) { state = lcg(state); ct.push((plain.charCodeAt(i) + (state % 65536)) % 65536); }
    return [ct, salt, tag(ct, key, salt)];
  }
  // 認証タグが合わなければ null (zone-guard-reject)
  function open(sealed, key) {
    if (!Array.isArray(sealed) || !Array.isArray(sealed[0]) || tag(sealed[0], key, sealed[1]) !== sealed[2]) return null;
    var state = keySeed(key, sealed[1]), out = "", i;
    for (i = 0; i < sealed[0].length; i++) { state = lcg(state); out += String.fromCharCode((sealed[0][i] - (state % 65536) + 65536) % 65536); }
    return out;
  }

  var KNOTS = { trefoil: { label: "三葉結び目", host: "url.or.jp" }, figure8: { label: "8 の字結び目", host: "bada.or.jp" } };
  // 元の zone-lib.bada を Bada 処理系で実行して Jones 鍵を求め、この移植と元のコードの値が一致することを確かめる
  function selfCheck(Bada, lib) {
    var names = ["tokyo.zone.jp", "osaka.zone.jp", "nagoya.zone.jp", "sapporo.zone.jp", "fukuoka.zone.jp", "naha.zone.jp"], urls = ["zone://url.or.jp/", "zone://会議.zone.jp/meeting", "zone://bada.or.jp/"];
    var sample = "zone 自己検査 — 複数行\n2 行目 ✓", prog = lib + "\nNET := zone_boot()\n";
    prog += 'print("@@JK", jones_key(zone_diagram("url.or.jp")), jones_key(zone_diagram("bada.or.jp")))\n';
    names.forEach(function (n) { prog += 'print("@@ID", zone_id("peer:' + n + '"))\n'; });
    urls.forEach(function (u) { var q = JSON.stringify(u); prog += 'print("@@KEY", zone_id(' + q + '))\nprint("@@ROUTE", zone_route(NET, zone_id(' + q + ')))\nprint("@@OWNER", dht_nearest(NET, zone_id(' + q + '))[0])\n'; });
    prog += "G := zone_seal(" + JSON.stringify(sample) + ', 1546, 77)\nprint("@@TAG", G[2])\nprint("@@CT", G[0][0], G[0][5], len(G[0]))\n';
    var r = Bada.run(prog, { maxSteps: 30000000 });
    if (!r.ok) return { ok: false, error: r.error || (r.parseErrors || []).join("; ") };
    var get = function (k) { return r.output.split("\n").filter(function (l) { return l.indexOf("@@" + k + " ") === 0; }).map(function (l) { return l.slice(k.length + 3).trim(); }); };
    var jk = get("JK")[0].split(" ").map(Number), peers = names.map(function (n) { return { name: n, id: peerId(n) }; }), ring = sortRing(peers), g = seal(sample, 1546, 77);
    var num = function (s) { return Math.round(parseFloat(s)); };
    var checks = {
      ids: get("ID").map(num).join() === peers.map(function (p) { return p.id; }).join(),
      keys: get("KEY").map(num).join() === urls.map(zoneId).join(),
      owners: get("OWNER").join() === urls.map(function (u) { return nearest(peers, zoneId(u)).name; }).join(),
      routes: get("ROUTE").map(function (s) { return s.replace(/[\[\]"\s]/g, ""); }).join("|") === urls.map(function (u) { return route(peers, ring[0].name, zoneId(u)).join(","); }).join("|"),
      seal: num(get("TAG")[0]) === g[2] && get("CT")[0].split(" ").map(num).join() === [g[0][0], g[0][5], g[0].length].join(),
      open: open(g, 1546) === sample && open(g, 1547) === null
    };
    var ok = Object.keys(checks).every(function (k) { return checks[k]; }) && jk.every(function (x) { return x > 0; }) && jk[0] !== jk[1];
    return { ok: ok, checks: checks, jones: { trefoil: jk[0], figure8: jk[1] }, raw: ok ? undefined : r.output.split("\n").filter(function (l) { return l.indexOf("@@") === 0; }) };
  }

  global.BadaZone = { RING: RING, strHash: strHash, zoneId: zoneId, peerId: peerId, parse: parse, ringDist: ringDist, nearest: nearest, sortRing: sortRing,
                      neighbors: neighbors, route: route, seal: seal, open: open, tag: tag, KNOTS: KNOTS, selfCheck: selfCheck };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaZone;
})(typeof window !== "undefined" ? window : globalThis);
