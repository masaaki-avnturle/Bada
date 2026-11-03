/*
 * qshield-test.js — Bada QuantumShield コアの自己検査
 *   node bada_gui_ide/quantumshield-app/test/qshield-test.js
 */
"use strict";
var path = require("path");
var QS = require(path.join(__dirname, "..", "www", "qshield.js"));

var failed = 0;
function ok(cond, label) {
  console.log((cond ? "PASS" : "FAIL") + "  " + label);
  if (!cond) failed++;
}

/* ── 資格情報の決定論性 (量子鍵同期) ── */
var c1 = QS.deriveCreds(0, "ssh", 0), c2 = QS.deriveCreds(0, "ssh", 0);
ok(c1.port === c2.port && c1.password === c2.password && c1.ip === c2.ip,
   "deriveCreds is deterministic (量子鍵同期ローリングコード)");
ok(QS.deriveCreds(0, "ssh", 0).port !== QS.deriveCreds(0, "ssh", 1).port,
   "世代が変わると port が変わる (ローテーション)");
ok(QS.deriveCreds(0, "ssh", 0).password !== QS.deriveCreds(0, "ssh", 1).password,
   "世代が変わると password が変わる");
ok(QS.deriveCreds(0, "ssh", 5).port !== QS.deriveCreds(1, "ssh", 5).port,
   "別の結び目(量子鍵)では別の資格情報 — 攻撃者は予測不能");
ok(c1.port >= QS.PORT_LO && c1.port < QS.PORT_LO + QS.PORT_SPAN, "port はエフェメラル範囲内");

/* ── デバイス初期化 ── */
var dev = QS.createDevice(0);
ok(dev.services.ssh && dev.services.rdp && dev.services.web, "device に ssh/rdp/web サービス");
ok(dev.services.ssh.gen === 0, "初期世代は 0");

/* ── 攻撃者が接触 → 検知 → ローテーション → ブロック ── */
var sshBefore = Object.assign({}, dev.services.ssh.creds);
var r = QS.attackerTouch(dev, "ssh", { type: "connect", from: "203.0.113.7",
  port: sshBefore.port, ip: sshBefore.ip, password: "guessed" });
ok(r.detected, "攻撃的接触を侵入として検知");
ok(r.rotated && r.rotated.before.port === sshBefore.port, "ローテーション前は旧 port");
ok(dev.services.ssh.creds.port !== sshBefore.port, "接触後 port が変わった");
ok(dev.services.ssh.gen === 1, "世代が 1 に進んだ");
ok(r.blocked, "攻撃者はブロックされた");

/* ── 盗んだ正しい資格情報でも、接触と同時にローテーションされ失効 ── */
var dev2 = QS.createDevice(1);
var stolen = Object.assign({}, dev2.services.rdp.creds);     // 攻撃者が完全な資格情報を盗んだ
var r2 = QS.attackerTouch(dev2, "rdp", { type: "connect", from: "198.51.100.9",
  port: stolen.port, ip: stolen.ip, password: stolen.password });
ok(r2.detected && r2.blocked, "盗んだ正しい資格情報での接続も、接触時に失効してブロック");
ok(dev2.services.rdp.creds.port !== stolen.port || dev2.services.rdp.creds.password !== stolen.password,
   "盗まれた資格情報は接触後に無効 (port か password が変化)");
// 盗んだ資格情報で再接続しても現在のものと一致しない
var reuse = QS.attackerTouch(dev2, "rdp", { type: "connect", from: "198.51.100.9",
  port: stolen.port, ip: stolen.ip, password: stolen.password });
ok(reuse.blocked, "古い盗難資格情報の再利用もブロック");

/* ── 各攻撃タイプが脅威度を上げ、都度ローテーションする ── */
var dev3 = QS.createDevice(0);
var g0 = dev3.services.web.gen;
QS.attackerTouch(dev3, "web", { type: "scan", from: "a" });
QS.attackerTouch(dev3, "web", { type: "bruteforce", from: "a" });
QS.attackerTouch(dev3, "web", { type: "exploit", from: "a" });
ok(dev3.services.web.gen === g0 + 3, "scan/bruteforce/exploit それぞれでローテーション (3 世代)");
ok(dev3.threat >= 1 + 3 + 5, "脅威スコアが累積 (scan1+brute3+exploit5)");

/* ── 正規の持ち主は量子鍵を知っているので追従して接続できる ── */
var dev4 = QS.createDevice(2);
QS.attackerTouch(dev4, "ssh", { type: "scan", from: "x" });      // 何度かローテーション
QS.attackerTouch(dev4, "ssh", { type: "bruteforce", from: "x" });
var owner = QS.ownerConnect(dev4, "ssh", 2);                      // 同じ結び目(量子鍵)=2
ok(owner.ok && owner.creds.port === dev4.services.ssh.creds.port,
   "正規の持ち主は量子鍵で現在の資格情報を計算して接続できる");
var fake = QS.ownerConnect(dev4, "ssh", 0);                       // 違う結び目(量子鍵)
ok(!fake.ok, "量子鍵(結び目)が違う偽の持ち主は接続できない");

/* ── ログが append-only で侵入/ローテーション/ブロックを記録 ── */
ok(dev.log.some(function (e) { return e.kind === "intrusion"; }) &&
   dev.log.some(function (e) { return e.kind === "rotate"; }) &&
   dev.log.some(function (e) { return e.kind === "block"; }),
   "監査ログに intrusion / rotate / block を記録");

console.log(failed === 0 ? "\nALL QUANTUMSHIELD TESTS PASSED" : "\n" + failed + " TEST(S) FAILED");
process.exit(failed === 0 ? 0 : 1);
