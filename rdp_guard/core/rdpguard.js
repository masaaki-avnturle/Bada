/*
 * rdpguard.js — Bada RDP Guard コア (RDP 防御: 端末間の相互デジタル署名認証)
 *
 * RDP の弱点である「なりすまし・セッション乗っ取り」を防ぐための *防御* ソフト。
 * RDP セッションを許可する前に、接続する 2 つの端末が互いに
 * **デジタル署名によるチャレンジ・レスポンス**で身元を証明し合う。
 * 秘密鍵を持たない攻撃者はどちらの端末にもなりすませないため、
 * 盗んだ資格情報だけでは RDP に入れない (多要素の端末認証)。
 *
 * 署名方式 — ハッシュ関数の *不可逆性* のみに依存する正統な構成:
 *   ・Lamport 一回署名 (OTS): 秘密鍵=乱数の原像、公開鍵=その SHA-256 ハッシュ。
 *     署名はメッセージのビットに応じて原像を公開する。ハッシュが一方向
 *     (非可逆) なので、公開鍵から秘密鍵は復元できない。
 *   ・Merkle 木: 複数の Lamport 公開鍵を 1 本の木にまとめ、根 (root) を端末の
 *     安定した「指紋 (fingerprint)」として公開する。各セッションは 1 枚の葉を
 *     使い、認証パスで指紋に結びつける (Merkle 署名方式 / XMSS 系の縮小版)。
 *   ・順序依存 (非可換) 性: Merkle パスと Reviser のタプル辞書式順序で、
 *     合成の順番が結果を変える (順序を変えると検証が通らない)。
 *
 * Reviser — tuple-network の *辞書式順序* でセキュリティ方針にパッチを当てる
 * 決定論的ポリシー・エンジン (誰が・どこから・どこへ・何を、を許可/拒否)。
 *
 * ※ これは防御の概念実装です。実際の RDP パケットや mstsc は操作しません。
 *   RDP ゲートウェイ/プロキシが接続前にこの verify を呼ぶ想定の参照実装です。
 */
(function (global) {
  "use strict";

  /* ── SHA-256 (純 JS, Node/ブラウザ共通) ── */
  var K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  function rotr(x, n){ return (x >>> n) | (x << (32 - n)); }
  function sha256(bytes){
    var l = bytes.length;
    var withOne = l + 1;
    var k = (56 - withOne % 64 + 64) % 64;
    var total = withOne + k + 8;
    var m = new Uint8Array(total);
    m.set(bytes, 0); m[l] = 0x80;
    var bitLen = l * 8;
    // 64-bit length (we assume < 2^32 bits)
    m[total - 4] = (bitLen >>> 24) & 0xff;
    m[total - 3] = (bitLen >>> 16) & 0xff;
    m[total - 2] = (bitLen >>> 8) & 0xff;
    m[total - 1] = bitLen & 0xff;
    var H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    var w = new Int32Array(64);
    for (var off = 0; off < total; off += 64){
      for (var i = 0; i < 16; i++){
        w[i] = (m[off+4*i]<<24)|(m[off+4*i+1]<<16)|(m[off+4*i+2]<<8)|(m[off+4*i+3]);
      }
      for (i = 16; i < 64; i++){
        var s0 = rotr(w[i-15],7) ^ rotr(w[i-15],18) ^ (w[i-15]>>>3);
        var s1 = rotr(w[i-2],17) ^ rotr(w[i-2],19) ^ (w[i-2]>>>10);
        w[i] = (w[i-16] + s0 + w[i-7] + s1) | 0;
      }
      var a=H[0],b=H[1],c=H[2],d=H[3],e=H[4],f=H[5],g=H[6],h=H[7];
      for (i = 0; i < 64; i++){
        var S1 = rotr(e,6) ^ rotr(e,11) ^ rotr(e,25);
        var ch = (e & f) ^ (~e & g);
        var t1 = (h + S1 + ch + K[i] + w[i]) | 0;
        var S0 = rotr(a,2) ^ rotr(a,13) ^ rotr(a,22);
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var t2 = (S0 + maj) | 0;
        h=g; g=f; f=e; e=(d+t1)|0; d=c; c=b; b=a; a=(t1+t2)|0;
      }
      H[0]=(H[0]+a)|0; H[1]=(H[1]+b)|0; H[2]=(H[2]+c)|0; H[3]=(H[3]+d)|0;
      H[4]=(H[4]+e)|0; H[5]=(H[5]+f)|0; H[6]=(H[6]+g)|0; H[7]=(H[7]+h)|0;
    }
    var out = new Uint8Array(32);
    for (i = 0; i < 8; i++){ out[4*i]=(H[i]>>>24)&0xff; out[4*i+1]=(H[i]>>>16)&0xff; out[4*i+2]=(H[i]>>>8)&0xff; out[4*i+3]=H[i]&0xff; }
    return out;
  }

  /* ── バイト/16進ユーティリティ ── */
  function toHex(u8){ var s=""; for (var i=0;i<u8.length;i++){ s += (u8[i]<16?"0":"") + u8[i].toString(16); } return s; }
  function fromHex(h){ var u=new Uint8Array(h.length/2); for (var i=0;i<u.length;i++) u[i]=parseInt(h.substr(2*i,2),16); return u; }
  function utf8(s){ if (typeof TextEncoder!=="undefined") return new TextEncoder().encode(s);
    var a=[]; for (var i=0;i<s.length;i++){ var c=s.charCodeAt(i);
      if (c<128) a.push(c); else if (c<2048){ a.push(192|(c>>6),128|(c&63)); }
      else { a.push(224|(c>>12),128|((c>>6)&63),128|(c&63)); } } return new Uint8Array(a); }
  function concat(a,b){ var u=new Uint8Array(a.length+b.length); u.set(a,0); u.set(b,a.length); return u; }
  function hash(u8){ return sha256(u8); }
  function hashHex(u8){ return toHex(sha256(u8)); }

  /* ── 乱数 (既定は安全な CSPRNG、テストは seedRng で決定論的に) ── */
  function secureRandom(n){
    if (typeof module !== "undefined" && module.exports){ return new Uint8Array(require("crypto").randomBytes(n)); }
    var a = new Uint8Array(n);
    if (typeof crypto !== "undefined" && crypto.getRandomValues) crypto.getRandomValues(a);
    else for (var i=0;i<n;i++) a[i]=Math.floor(Math.random()*256);
    return a;
  }
  /* 決定論的 RNG (テスト/デモ再現用): seed 文字列から SHA-256 カウンタ列 */
  function seedRng(seed){
    var ctr = 0, s = utf8(String(seed));
    return function (n){
      var out = new Uint8Array(n), pos = 0;
      while (pos < n){
        var block = sha256(concat(s, utf8("|" + (ctr++))));
        for (var i=0;i<block.length && pos<n;i++) out[pos++]=block[i];
      }
      return out;
    };
  }

  /* ── Lamport 一回署名 (256 ビット) ── */
  var N = 256;              /* メッセージダイジェストのビット数 */
  var LEN = 32;             /* 原像/ハッシュのバイト長 */
  function lamportKeygen(rng){
    var priv = new Array(N), pub = new Array(N);
    for (var i=0;i<N;i++){
      var p0 = rng(LEN), p1 = rng(LEN);
      priv[i] = [toHex(p0), toHex(p1)];
      pub[i]  = [hashHex(p0), hashHex(p1)];
    }
    return { priv: priv, pub: pub };
  }
  function bit(digest, i){ return (digest[i >> 3] >> (7 - (i & 7))) & 1; }
  function lamportSign(digest, priv){
    var sig = new Array(N);
    for (var i=0;i<N;i++) sig[i] = priv[i][bit(digest, i)];
    return sig;                 /* 公開する原像 (16進) の列 */
  }
  function lamportVerify(digest, sig, pub){
    if (!sig || sig.length !== N) return false;
    for (var i=0;i<N;i++){
      var b = bit(digest, i);
      if (hashHex(fromHex(sig[i])) !== pub[i][b]) return false;
    }
    return true;
  }
  /* Lamport 公開鍵をまとめた指紋 (Merkle の葉) */
  function lamportPubHash(pub){
    var s = "";
    for (var i=0;i<N;i++) s += pub[i][0] + pub[i][1];
    return hashHex(utf8(s));
  }

  /* ── Merkle 木 (葉ハッシュ → 根、認証パス、検証) ── */
  function merkleRoot(leafHashes){ return merkleBuild(leafHashes).root; }
  function merkleBuild(leafHashes){
    var levels = [leafHashes.slice()];
    var cur = leafHashes.slice();
    while (cur.length > 1){
      if (cur.length % 2 === 1) cur.push(cur[cur.length-1]); /* 奇数は複製 */
      var next = [];
      for (var i=0;i<cur.length;i+=2) next.push(hashHex(utf8(cur[i] + cur[i+1])));
      levels.push(next); cur = next;
    }
    return { root: cur[0], levels: levels };
  }
  function merklePath(leafHashes, index){
    var built = merkleBuild(leafHashes), path = [], idx = index;
    for (var lv=0; lv < built.levels.length-1; lv++){
      var level = built.levels[lv];
      var sib = (idx % 2 === 0) ? idx+1 : idx-1;
      if (sib >= level.length) sib = idx;          /* 複製されたケース */
      path.push({ hash: level[sib], right: (idx % 2 === 0) });
      idx = idx >> 1;
    }
    return path;
  }
  function merkleVerify(leafHash, path, root){
    var h = leafHash;
    for (var i=0;i<path.length;i++){
      h = path[i].right ? hashHex(utf8(h + path[i].hash)) : hashHex(utf8(path[i].hash + h));
    }
    return h === root;
  }

  /* ── 端末 (Terminal): Merkle 署名方式の鍵一式 ── */
  function createTerminal(name, nLeaves, rng){
    rng = rng || secureRandom;
    nLeaves = nLeaves || 4;
    var leaves = [], keys = [];
    for (var i=0;i<nLeaves;i++){
      var kp = lamportKeygen(rng);
      var leaf = lamportPubHash(kp.pub);
      keys.push(kp); leaves.push(leaf);
    }
    var root = merkleRoot(leaves);
    return {
      name: name, root: root, fingerprint: root.slice(0, 16),
      _keys: keys, _leaves: leaves, nLeaves: nLeaves, used: 0
    };
  }
  /* チャレンジ (相手のノンス + セッション文脈) に署名。葉を 1 枚消費する。 */
  function signChallenge(term, challengeStr){
    if (term.used >= term.nLeaves) return { error: "鍵の葉を使い切りました (再鍵が必要)" };
    var idx = term.used++;
    var digest = sha256(utf8(challengeStr));
    var kp = term._keys[idx];
    var sig = lamportSign(digest, kp.priv);
    var path = merklePath(term._leaves, idx);
    return { leaf: idx, pub: kp.pub, sig: sig, path: path };
  }
  /* 指紋 (root) に対して相手端末の署名を検証する */
  function verifyTerminalSig(fingerprintRoot, challengeStr, s){
    if (!s || s.error) return false;
    var digest = sha256(utf8(challengeStr));
    if (!lamportVerify(digest, s.sig, s.pub)) return false;      /* Lamport 署名が正しい */
    var leafHash = lamportPubHash(s.pub);
    return merkleVerify(leafHash, s.path, fingerprintRoot);      /* 指紋に結びつく */
  }

  /* ── 相互認証ハンドシェイク (双方が相手のノンスに署名) ── */
  function mutualHandshake(termA, termB, opts){
    opts = opts || {};
    var sid = opts.sessionId || toHex(secureRandom(8));
    var nonceA = opts.nonceA || toHex(secureRandom(16));
    var nonceB = opts.nonceB || toHex(secureRandom(16));
    /* 各端末は「セッション|自分→相手|相手のノンス」に署名 (リプレイ・反射攻撃対策) */
    var chalAtoB = "RDPGUARD1|" + sid + "|" + termA.name + ">" + termB.name + "|" + nonceB;
    var chalBtoA = "RDPGUARD1|" + sid + "|" + termB.name + ">" + termA.name + "|" + nonceA;
    var sigA = signChallenge(termA, chalAtoB);
    var sigB = signChallenge(termB, chalBtoA);
    /* 相手は相手の既知の指紋 (root) に対して検証する */
    var aOk = verifyTerminalSig(termA.root, chalAtoB, sigA);     /* B が A を検証 */
    var bOk = verifyTerminalSig(termB.root, chalBtoA, sigB);     /* A が B を検証 */
    var log = [
      { who: termA.name, text: "ノンス " + nonceA + " を提示し、B のチャレンジに署名 (葉 " + (sigA.leaf) + ")" },
      { who: termB.name, text: "ノンス " + nonceB + " を提示し、A のチャレンジに署名 (葉 " + (sigB.leaf) + ")" },
      { who: termB.name, text: "A の署名を A の指紋 " + termA.fingerprint + " で検証 → " + (aOk ? "OK" : "NG") },
      { who: termA.name, text: "B の署名を B の指紋 " + termB.fingerprint + " で検証 → " + (bOk ? "OK" : "NG") }
    ];
    return {
      ok: aOk && bOk, sessionId: sid, nonceA: nonceA, nonceB: nonceB,
      aVerified: aOk, bVerified: bOk, sigA: sigA, sigB: sigB, log: log,
      message: (aOk && bOk) ? "相互認証成功 — RDP セッションを許可" : "相互認証失敗 — RDP 接続を拒否"
    };
  }

  /* ── Reviser: tuple-network の辞書式順序でポリシーにパッチを当てる ──
   * rule = { tuple: ["zone","src","dst","user","action"...], effect: "allow"|"deny", note?, seq? }
   * 全ルール (base + patches) をタプルの辞書式順序 + seq で整列し、決定論的に
   * マップへ適用する。同じタプルは辞書順で後のパッチが上書き (監査可能)。 */
  function tupleKey(tuple){ return tuple.map(function (x){ return String(x); }).join("␟"); }
  function revise(baseRules, patchSets){
    var all = [];
    (baseRules || []).forEach(function (r, i){ all.push(norm(r, "base", i)); });
    (patchSets || []).forEach(function (patch){
      (patch.rules || []).forEach(function (r, i){ all.push(norm(r, patch.id || "patch", i)); });
    });
    /* 辞書式順序: まずタプル、同一タプル内は (パッチ適用順 seq) */
    all.sort(function (a, b){
      if (a.key < b.key) return -1; if (a.key > b.key) return 1;
      return a.seq - b.seq;
    });
    var map = {};
    all.forEach(function (r){ map[r.key] = r; });          /* 辞書順で後が勝つ */
    var effective = Object.keys(map).sort().map(function (k){ return map[k]; });
    return {
      rules: effective,
      decide: function (conn){ return decide(effective, conn); }
    };
    function norm(r, src, i){
      return { tuple: r.tuple, key: tupleKey(r.tuple), effect: r.effect === "allow" ? "allow" : "deny",
               note: r.note || "", source: src, seq: (r.seq != null ? r.seq : i) };
    }
  }
  /* 接続タプルに最も具体的 (タプル前方一致が最長) なルールを適用。既定は拒否。 */
  function decide(effective, conn){
    var connKey = conn.map(function (x){ return String(x); });
    var best = null, bestLen = -1;
    for (var i=0;i<effective.length;i++){
      var t = effective[i].tuple, ok = true;
      if (t.length > connKey.length){ continue; }
      for (var j=0;j<t.length;j++){
        if (String(t[j]) !== "*" && String(t[j]) !== connKey[j]){ ok = false; break; }
      }
      if (ok && t.length > bestLen){ best = effective[i]; bestLen = t.length; }
    }
    return { effect: best ? best.effect : "deny", rule: best, matched: !!best };
  }

  var RdpGuard = {
    sha256: sha256, toHex: toHex, fromHex: fromHex, utf8: utf8, hashHex: hashHex,
    secureRandom: secureRandom, seedRng: seedRng,
    lamportKeygen: lamportKeygen, lamportSign: lamportSign, lamportVerify: lamportVerify,
    lamportPubHash: lamportPubHash, merkleRoot: merkleRoot, merklePath: merklePath, merkleVerify: merkleVerify,
    createTerminal: createTerminal, signChallenge: signChallenge, verifyTerminalSig: verifyTerminalSig,
    mutualHandshake: mutualHandshake, revise: revise, decide: decide, tupleKey: tupleKey,
    N: N
  };
  if (typeof module !== "undefined" && module.exports) module.exports = RdpGuard;
  global.RdpGuard = RdpGuard;
})(typeof globalThis !== "undefined" ? globalThis : this);
