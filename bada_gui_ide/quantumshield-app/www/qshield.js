/*
 * qshield.js — Bada QuantumShield コア (量子暗号の応用: 侵入時クレデンシャル自動変更)
 *
 * 量子暗号アプリ (qcrypto.js の Jones 多項式量子暗号) の応用。
 * 対象 PC にハッカーが「接触」(ポートスキャン / 不正接続 / 総当たり /
 * 盗んだ資格情報でのアクセス) したことを検知すると、量子システムが
 * そのサービスの「ポート番号・バインド IP・パスワード」を即座に
 * *量子鍵に同期して* 変更 (ローテーション) し、攻撃者を締め出す
 * — ムービング・ターゲット・ディフェンス (MTD)。
 *
 * 量子鍵同期の鍵 (正規の持ち主だけが追従できる仕組み):
 *   ・デバイスと正規の持ち主は「結び目図 (量子鍵)」を共有する。
 *   ・各世代 generation ごとに、量子鍵 (jonesKey) + 世代番号 + サービス名
 *     から、ポート/IP/パスワードを *決定論的に* 導出する (ローリングコード)。
 *   ・正規の持ち主は量子鍵を知っているので次の資格情報を計算して再接続できる。
 *   ・攻撃者は量子鍵 (結び目) を知らないので、ローテーション後の資格情報を
 *     予測できず、盗んだ古い資格情報も失効してアクセス不能になる。
 *
 * ※ これは防御の概念シミュレーションです。実機のファイアウォール・実際の
 *   パスワード・実ネットワークは変更しません (表示と数理のみ)。
 */
(function (global) {
  "use strict";
  var QC = (typeof require === "function") ? require("./qcrypto.js") : global.BadaQC;
  if (!QC) throw new Error("BadaQC (qcrypto.js) が必要です");

  /* ── 量子鍵から決定論的に値を導出 (ローリングコード) ──
   * seed = SHA256( jonesKey(knot) | service | field | generation )
   */
  function qbytes(knotId, service, field, generation, n) {
    var knot = QC.KNOTS[knotId % QC.KNOTS.length];
    var jk = QC.jonesKey(knot.diagram);                 // 量子鍵 (結び目の Kauffman 標本)
    var msg = QC.utf8(jk + "|" + service + "|" + field + "|" + generation + "|BadaQShield1");
    var h = QC.sha256(msg);
    // n バイト必要なら伸長 (ハッシュチェーン)
    var out = [], cur = h, i;
    while (out.length < n) {
      for (i = 0; i < cur.length && out.length < n; i++) out.push(cur[i]);
      cur = QC.sha256(QC.utf8(QC.hex(cur) + "|" + out.length));
    }
    return out;
  }
  function u32(bytes, off) {
    return ((bytes[off] << 24) | (bytes[off + 1] << 16) | (bytes[off + 2] << 8) | bytes[off + 3]) >>> 0;
  }

  /* ── 資格情報の導出 (サービス × 世代 → port / ip / password) ── */
  var PORT_LO = 20000, PORT_SPAN = 40000;               // エフェメラル範囲
  function deriveCreds(knotId, service, generation) {
    var b = qbytes(knotId, service, "creds", generation, 24);
    var port = PORT_LO + (u32(b, 0) % PORT_SPAN);
    // バインド IP は 10.42.x.y プール (量子鍵で移動)
    var ip = "10.42." + (b[4] % 254 + 1) + "." + (b[5] % 254 + 1);
    // パスワード: 導出バイト列を Base32 風に 16 文字
    var A = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    var pw = "";
    for (var i = 0; i < 16; i++) pw += A[b[6 + i] % 32];
    return { port: port, ip: ip, password: pw, generation: generation };
  }

  /* ── デバイス (守られる対象 PC) ── */
  var DEFAULT_SERVICES = ["ssh", "rdp", "web"];
  function createDevice(knotId, services) {
    knotId = knotId || 0;
    var svcNames = services || DEFAULT_SERVICES;
    var dev = { knotId: knotId, services: {}, log: [], threat: 0, events: 0 };
    svcNames.forEach(function (name) {
      dev.services[name] = { name: name, gen: 0, creds: deriveCreds(knotId, name, 0), compromised: false };
    });
    logEvent(dev, "boot", null, "QuantumShield 起動: 量子鍵 (結び目) で初期資格情報を導出");
    return dev;
  }
  function logEvent(dev, kind, service, text) {
    dev.log.unshift({ at: new Date().toISOString(), kind: kind, service: service, text: text });
    dev.log = dev.log.slice(0, 200);
  }

  /* ── 量子ローテーション: 侵入検知時に資格情報を変更 ── */
  function rotate(dev, serviceName, reason) {
    var s = dev.services[serviceName];
    if (!s) return null;
    var before = s.creds;
    s.gen += 1;
    s.creds = deriveCreds(dev.knotId, serviceName, s.gen);
    s.compromised = false;
    logEvent(dev, "rotate", serviceName,
      "量子ローテーション(世代" + s.gen + "): " + serviceName +
      " を port " + before.port + "→" + s.creds.port +
      " / ip " + before.ip + "→" + s.creds.ip + " / パスワード更新 — " + (reason || ""));
    return { before: before, after: s.creds };
  }

  /* ── 攻撃者の接触 → 検知 → ローテーションで締め出し ──
   * attempt: { type: "scan"|"bruteforce"|"connect"|"exploit",
   *            from: "<attacker ip>", port?, ip?, password? }
   * 返り値: { detected, blocked, rotated:{before,after}|null, message }
   */
  function attackerTouch(dev, serviceName, attempt) {
    var s = dev.services[serviceName];
    if (!s) return { detected: false, blocked: true, rotated: null, message: "unknown service" };
    dev.events += 1;
    var type = attempt.type || "connect";
    var from = attempt.from || "attacker";

    // 盗んだ/推測した資格情報が *現在の* ものと一致するか (ローテーション後は失効)
    var credsMatch = attempt.port === s.creds.port &&
                     attempt.ip === s.creds.ip &&
                     attempt.password === s.creds.password;

    // すべての攻撃的接触を侵入とみなす (スキャン・総当たり・不正接続・エクスプロイト)
    dev.threat += (type === "exploit" ? 5 : type === "bruteforce" ? 3 : type === "scan" ? 1 : 2);
    logEvent(dev, "intrusion", serviceName,
      "⚠ 侵入検知: " + from + " が " + serviceName + " に " + type +
      (credsMatch ? " (盗んだ資格情報が一致!)" : "") + " — 量子ローテーションを発火");

    // 検知したら即ローテーション → 攻撃者が今まさに使った資格情報は失効
    var r = rotate(dev, serviceName, "攻撃元 " + from + " の " + type + " を検知");

    // ローテーション後、攻撃者の持つ資格情報は必ず現在のものと不一致 = ブロック
    var nowMatch = attempt.port === s.creds.port &&
                   attempt.ip === s.creds.ip &&
                   attempt.password === s.creds.password;
    var blocked = !nowMatch;
    logEvent(dev, "block", serviceName,
      "⛔ " + from + " をブロック: 旧資格情報は失効 (409 access-denied)。新 port=" + s.creds.port);
    return {
      detected: true, blocked: blocked, rotated: r,
      message: (credsMatch
        ? "攻撃者が正しい資格情報で接触したが、接触と同時に量子ローテーションされ失効"
        : "攻撃者の資格情報は量子鍵を知らないため不一致") + " → アクセス不能"
    };
  }

  /* ── 正規の持ち主の接続 (量子鍵を知っているので追従できる) ── */
  function ownerConnect(dev, serviceName, knowsQuantumKnotId) {
    var s = dev.services[serviceName];
    if (!s) return { ok: false, message: "unknown service" };
    // 正規の持ち主は同じ結び目(量子鍵)と世代から現在の資格情報を計算
    var derived = deriveCreds(knowsQuantumKnotId, serviceName, s.gen);
    var ok = knowsQuantumKnotId === dev.knotId &&
             derived.port === s.creds.port && derived.password === s.creds.password;
    logEvent(dev, ok ? "owner-ok" : "owner-fail", serviceName,
      ok ? "✓ 正規の持ち主が量子鍵で現在の資格情報を計算し接続 (port " + s.creds.port + ")"
         : "✗ 量子鍵(結び目)が一致せず接続不可 — 偽の持ち主");
    return { ok: ok, creds: ok ? s.creds : null,
      message: ok ? "量子鍵同期により正規接続" : "量子鍵が違うため正規接続できない" };
  }

  var BadaQShield = {
    PORT_LO: PORT_LO, PORT_SPAN: PORT_SPAN,
    KNOTS: QC.KNOTS,
    deriveCreds: deriveCreds,
    createDevice: createDevice,
    rotate: rotate,
    attackerTouch: attackerTouch,
    ownerConnect: ownerConnect
  };
  if (typeof module !== "undefined" && module.exports) module.exports = BadaQShield;
  global.BadaQShield = BadaQShield;
})(typeof globalThis !== "undefined" ? globalThis : this);
