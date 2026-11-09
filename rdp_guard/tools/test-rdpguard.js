/*
 * test-rdpguard.js — Bada RDP Guard コアの自己検査
 *   node rdp_guard/tools/test-rdpguard.js
 */
"use strict";
var path = require("path");
var crypto = require("crypto");
var G = require(path.join(__dirname, "..", "core", "rdpguard.js"));

var failed = 0;
function ok(c, l){ console.log((c ? "PASS" : "FAIL") + "  " + l); if (!c) failed++; }

/* ── SHA-256 が標準実装と一致 (既知ベクタ + crypto 突き合わせ) ── */
ok(G.hashHex(G.utf8("abc")) === "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
   "SHA-256('abc') が既知ベクタと一致");
ok(G.hashHex(G.utf8("")) === "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
   "SHA-256('') が既知ベクタと一致");
(function(){
  var buf = crypto.randomBytes(1000);
  var a = G.toHex(G.sha256(new Uint8Array(buf)));
  var b = crypto.createHash("sha256").update(buf).digest("hex");
  ok(a === b, "SHA-256 が Node crypto と 1000 バイトで一致");
})();

var rng = G.seedRng("test-seed");

/* ── Lamport 一回署名 ── */
(function(){
  var kp = G.lamportKeygen(rng);
  var digest = G.sha256(G.utf8("challenge-xyz"));
  var sig = G.lamportSign(digest, kp.priv);
  ok(G.lamportVerify(digest, sig, kp.pub), "Lamport: 正しい署名は検証を通る");
  var other = G.sha256(G.utf8("challenge-XYZ"));
  ok(!G.lamportVerify(other, sig, kp.pub), "Lamport: 別メッセージでは検証に失敗 (改ざん検知)");
  // 攻撃者は原像を知らないので偽造できない: 公開鍵だけから署名を作れない
  var forged = sig.slice(); forged[0] = G.toHex(rng(32));
  ok(!G.lamportVerify(digest, forged, kp.pub), "Lamport: 原像を知らない偽造は失敗 (一方向性)");
})();

/* ── Merkle 木 ── */
(function(){
  var leaves = ["aa","bb","cc","dd","ee"].map(function(s){ return G.hashHex(G.utf8(s)); });
  var root = G.merkleRoot(leaves);
  for (var i=0;i<leaves.length;i++){
    var p = G.merklePath(leaves, i);
    ok(G.merkleVerify(leaves[i], p, root), "Merkle: 葉 " + i + " の認証パスが根に結びつく");
  }
  var bad = G.merklePath(leaves, 2);
  ok(!G.merkleVerify(G.hashHex(G.utf8("zz")), bad, root), "Merkle: 偽の葉はパスが根に結びつかない");
})();

/* ── 端末の指紋と署名検証 ── */
(function(){
  var alice = G.createTerminal("Alice", 4, rng);
  ok(alice.fingerprint.length === 16 && alice.root.length === 64, "端末は安定した指紋 (Merkle 根) を持つ");
  var chal = "RDPGUARD1|sid|Alice>Bob|nonce";
  var s = G.signChallenge(alice, chal);
  ok(G.verifyTerminalSig(alice.root, chal, s), "端末署名: 本物の指紋で検証成功");
  // 別の端末 (別の指紋) では検証失敗 = なりすまし不可
  var mallory = G.createTerminal("Mallory", 4, rng);
  ok(!G.verifyTerminalSig(mallory.root, chal, s), "端末署名: 別端末の指紋では検証失敗");
})();

/* ── 相互認証ハンドシェイク: 正規は成功、攻撃者は失敗 ── */
(function(){
  var a = G.createTerminal("WorkstationA", 4, rng);
  var b = G.createTerminal("ServerB", 4, rng);
  // A と B は事前に互いの指紋を共有済み (ピン留め) とする
  var r = G.mutualHandshake(a, b, { sessionId: "S1", nonceA: "nA", nonceB: "nB" });
  ok(r.ok && r.aVerified && r.bVerified, "正規端末同士は相互認証に成功 (RDP 許可)");

  // 攻撃者 impostor が ServerB になりすまして A に接続しようとする。
  // impostor は B の秘密鍵を持たない別端末 (別の指紋)。A は B の *既知の指紋* で検証する。
  var impostor = G.createTerminal("ServerB", 4, rng);   // 名前は詐称できるが鍵は別物
  var chalBtoA = "RDPGUARD1|S2|ServerB>WorkstationA|nA2";
  var fakeSig = G.signChallenge(impostor, chalBtoA);
  ok(!G.verifyTerminalSig(b.root, chalBtoA, fakeSig),
     "なりすまし: 攻撃者の署名は本物 B の指紋で検証失敗 → RDP 乗っ取りを阻止");
  // 攻撃者が盗んだ「古い署名」を別セッションで再利用しても、チャレンジが違うので無効
  var stolen = G.signChallenge(b, "RDPGUARD1|S3|ServerB>WorkstationA|nOLD");
  ok(!G.verifyTerminalSig(b.root, "RDPGUARD1|S4|ServerB>WorkstationA|nNEW", stolen),
     "リプレイ: 盗んだ署名は別ノンス/セッションでは無効 (反射・再送攻撃対策)");
})();

/* ── Reviser: tuple-network 辞書式順序のポリシー・パッチ ── */
(function(){
  var base = [
    { tuple: ["*"], effect: "deny", note: "既定は全拒否" },
    { tuple: ["rdp", "office", "server1"], effect: "allow", note: "社内→server1 許可" }
  ];
  var patch1 = { id: "patch-a", rules: [
    { tuple: ["rdp", "office", "server1", "admin"], effect: "allow", note: "admin 許可" },
    { tuple: ["rdp", "vpn", "server1"], effect: "allow", note: "VPN 許可" }
  ]};
  var patch2 = { id: "patch-b", rules: [
    { tuple: ["rdp", "office", "server1", "admin"], effect: "deny", note: "インシデント対応で admin 一時停止" }
  ]};
  var pol = G.revise(base, [patch1, patch2]);

  ok(pol.decide(["rdp","office","server1","bob"]).effect === "allow", "社内の一般ユーザは許可");
  ok(pol.decide(["rdp","internet","server1","bob"]).effect === "deny", "社外は既定で拒否");
  // 同一タプルは辞書順で後の source (patch-b) が勝つ → admin は deny に改訂
  ok(pol.decide(["rdp","office","server1","admin"]).effect === "deny",
     "同一タプルは後のパッチが上書き (admin は一時停止 deny に改訂)");
  ok(pol.decide(["rdp","vpn","server1","carol"]).effect === "allow", "VPN 経由は許可");
  // 決定論性: 同じ入力は常に同じ effective ポリシー
  var pol2 = G.revise(base, [patch1, patch2]);
  ok(JSON.stringify(pol.rules) === JSON.stringify(pol2.rules), "Reviser は決定論的 (同じ入力→同じ順序の方針)");
  // 最長一致 (最も具体的なルール) が優先
  var d = pol.decide(["rdp","office","server1","admin"]);
  ok(d.rule && d.rule.tuple.length === 4, "最も具体的なルール (最長タプル一致) が適用される");
})();

console.log(failed === 0 ? "\nALL RDPGUARD TESTS PASSED" : "\n" + failed + " TEST(S) FAILED");
process.exit(failed === 0 ? 0 : 1);
