/*
 * roundtrip.js — Bada QuantumCrypto コアの自己検査
 *   node bada_gui_ide/quantumcrypto-app/test/roundtrip.js
 */
"use strict";
const path = require("path");
const QC = require(path.join(__dirname, "..", "www", "qcrypto.js"));

let failed = 0;
function ok(cond, label) {
  console.log((cond ? "PASS" : "FAIL") + "  " + label);
  if (!cond) failed++;
}

/* --- SHA-256 既知ベクタ --- */
ok(QC.hex(QC.sha256(QC.utf8(""))) ===
   "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "sha256(empty)");
ok(QC.hex(QC.sha256(QC.utf8("abc"))) ===
   "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "sha256(abc)");

/* --- HMAC-SHA256 既知ベクタ (RFC 4231 Test Case 2) --- */
ok(QC.hex(QC.hmacSha256(QC.utf8("Jefe"), QC.utf8("what do ya want for nothing?"))) ===
   "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843", "hmac-sha256(rfc4231#2)");

/* --- ChaCha20 は XOR ストリームなので二度掛けで元に戻る --- */
{
  const key = QC.sha256(QC.utf8("key")), nonce = new Uint8Array(12).fill(7);
  const msg = QC.utf8("stream cipher self-inverse ストリーム");
  const ct = QC.chacha20Xor(key, nonce, msg);
  const back = QC.chacha20Xor(key, nonce, ct);
  ok(QC.hex(back) === QC.hex(msg) && QC.hex(ct) !== QC.hex(msg), "chacha20 self-inverse");
}

/* --- Kauffman ブラケット: 交差 0 個 = 1、決定性 --- */
ok(QC.kauffman([], 1.2) === 1.0, "kauffman(empty)=1");
for (const knot of QC.KNOTS) {
  const a = QC.jonesKey(knot.diagram), b = QC.jonesKey(knot.diagram);
  ok(a === b && /^[0-9a-f]{64}$/.test(a), "jonesKey deterministic: " + knot.name);
}
ok(QC.jonesKey(QC.KNOTS[0].diagram) !== QC.jonesKey(QC.KNOTS[1].diagram),
   "jonesKey distinguishes trefoil vs figure-eight");

/* --- テキスト暗号化 → 解除 (CJK 含む) --- */
{
  const pass = "ももたろう🍑 pass-2026";
  const msg = "量子暗号テスト: zone://url.or.jp — Jones多項式 AEAD ✔";
  const enc = QC.encryptText(pass, msg, 1);
  ok(enc.armored.indexOf(QC.ARMOR_BEGIN) === 0, "armored header present");
  const dec = QC.decryptText(pass, enc.armored);
  ok(dec.text === msg, "text round-trip (CJK)");
  ok(dec.meta.knot === QC.KNOTS[1].name, "knot id preserved in container");
}

/* --- 誤パスフレーズは拒否 --- */
{
  const enc = QC.encryptText("correct horse", "secret", 0);
  let threw = false;
  try { QC.decryptText("wrong horse", enc.armored); } catch (e) { threw = true; }
  ok(threw, "wrong passphrase rejected");
}

/* --- 改ざんは拒否 (409 zone-guard-reject) --- */
{
  const enc = QC.encryptText("p@ss", "tamper me", 2);
  const bytes = QC.dearmor(enc.armored);
  bytes[bytes.length - 40] ^= 0x55; /* 暗号文の 1 バイトを反転 */
  let threw = false, msg = "";
  try { QC.decryptContainer("p@ss", bytes); } catch (e) { threw = true; msg = String(e.message); }
  ok(threw && msg.indexOf("zone-guard-reject") >= 0, "tampered ciphertext rejected");
}

/* --- バイナリ ファイル round-trip --- */
{
  const data = new Uint8Array(4096);
  for (let i = 0; i < data.length; i++) data[i] = (i * 31 + 7) & 255;
  const enc = QC.encryptBytes("file-pass", data, { knotId: 0, filename: "写真.png" });
  const dec = QC.decryptContainer("file-pass", enc.container);
  ok(dec.isFile && dec.filename === "写真.png", "filename preserved");
  ok(QC.hex(dec.plain) === QC.hex(data), "binary file round-trip");
}

/* --- 空平文も可 --- */
{
  const enc = QC.encryptText("p", "", 0);
  ok(QC.decryptText("p", enc.armored).text === "", "empty plaintext round-trip");
}

console.log(failed === 0 ? "\nALL TESTS PASSED" : "\n" + failed + " TEST(S) FAILED");
process.exit(failed === 0 ? 0 : 1);
