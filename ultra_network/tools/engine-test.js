/*
 * engine-test.js — Bada UltraNetwork のエンジン単体テスト (Node で実行)
 *
 *   node ultra_network/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、純ロジック部分を検証します。
 * サンドボックスには document / window を与えないので、末尾の boot() は
 * 走らず (typeof document === "undefined" のガード)、エンジンだけが載ります。
 *
 *   1. SHA-256 / HMAC-SHA256 — 既知答えと RFC 4231 テストベクタ
 *   2. LINE / Instagram の Webhook 署名検証 (X-Line-Signature /
 *      X-Hub-Signature-256) — 正しい秘密は通り、誤った秘密は落ちる
 *   3. HD-PLC 物理層 — Zimmermann–Dostert 伝達関数、適応ビットローディング、
 *      アマチュア無線帯ノッチ、ウェーブレット変換の厳密な逆変換、
 *      ウェーブレット OFDM の完全往復、IEEE 1901 フレームの CRC、CSMA/CA
 *   4. NTT 写像層 — 写像 φ と逆写像 φ⁻¹、音声帯 16-QAM モデム、
 *      G.711 µ-law + RTP、INS ネット 64 のディジタル透過
 *   5. zone:// — URL 文法、リング DHT の解決、@@ ブロックの相互運用
 *   6. Jones 多項式量子暗号 — Kauffman ブラケットからの鍵導出、
 *      Bell 対 QKD の零保存、AEAD の往復と 409 zone-guard-reject
 *   7. STREAMS — 全 5 層を通した往復が完全一致すること、
 *      および 3 種類の攻撃がそれぞれ正しい状態符号で排除されること
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

/* ── index.html からインラインスクリプトを抽出 ── */
const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

/* document / window を与えない = boot() は走らない */
const sandbox = { console, Math, JSON, Date, Object, Array, String, Number, Boolean, isNaN, parseInt, parseFloat };
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "ultra_network/index.html" });
const E = sandbox;

/* ── 小さなテストハーネス ── */
let pass = 0, fail = 0;
function ok(cond, name, detail) {
  if (cond) { pass++; console.log("  ok   " + name + (detail ? "  — " + detail : "")); }
  else { fail++; console.log("  FAIL " + name + (detail ? "  — " + detail : "")); }
}
function group(title) { console.log("\n" + title); }

const U8 = (s) => E.bytesOfUtf8(s);
const S8 = (b) => E.utf8OfBytes(b);

/* ══ 1. SHA-256 / HMAC-SHA256 ══════════════════════════════════ */
group("1. SHA-256 / HMAC-SHA256");
ok(E.toHex(E.sha256([])) === "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  'SHA-256("") が既知答えと一致');
ok(E.toHex(E.sha256(U8("abc"))) === "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
  'SHA-256("abc") が既知答えと一致');
ok(E.toHex(E.sha256(U8("a".repeat(1000000)))) ===
  "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0",
  "SHA-256 100 万文字 (複数ブロック + 長さ符号化)");
{
  const k = new Array(20).fill(0x0b);
  ok(E.toHex(E.hmacSha256(k, U8("Hi There"))) ===
    "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7", "RFC 4231 テストベクタ #1");
  ok(E.toHex(E.hmacSha256(U8("Jefe"), U8("what do ya want for nothing?"))) ===
    "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843", "RFC 4231 テストベクタ #2");
  const k3 = new Array(20).fill(0xaa), d3 = new Array(50).fill(0xdd);
  ok(E.toHex(E.hmacSha256(k3, d3)) ===
    "773ea91e36800e46854db8ebd09181a72959098b3ef8c122d9635514ced565fe", "RFC 4231 テストベクタ #3");
  const k4 = new Array(131).fill(0xaa);
  ok(E.toHex(E.hmacSha256(k4, U8("Test Using Larger Than Block-Size Key - Hash Key First"))) ===
    "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54",
    "RFC 4231 テストベクタ #6 (ブロック長超の鍵)");
}
ok(E.constTimeEq([1, 2, 3], [1, 2, 3]) && !E.constTimeEq([1, 2, 3], [1, 2, 4]) && !E.constTimeEq([1], [1, 2]),
  "定数時間比較");
ok(E.toBase64(U8("hello")) === "aGVsbG8=" && E.toBase64(U8("hi")) === "aGk=", "Base64 (詰め物つき)");
ok(S8(U8("電力線 🔌 zone://")) === "電力線 🔌 zone://", "UTF-8 の往復 (CJK + 絵文字)");
{
  /* 回線から来るバイト列は攻撃者に触られうる。復号器は決して投げてはならない */
  const cases = [
    [0xff, 0xfe, 0xfd], [0x80, 0x81], [0xe3, 0x81], [0xf0], [0xf7, 0xbf, 0xbf, 0xbf],
    [0xc0, 0x80], [0xed, 0xa0, 0x80], [0xf4, 0x90, 0x80, 0x80], [0xe3, 0x81, 0x41]
  ];
  let threw = null;
  for (const c of cases) { try { S8(c); } catch (e) { threw = c.join(","); break; } }
  ok(threw === null, "壊れた UTF-8 でも復号器は例外を投げない", threw ? "投げた: " + threw : "9 通りすべて U+FFFD で吸収");
  let fuzzOk = true;
  for (let t = 0; t < 400; t++) {
    const n = 1 + (t % 12), a = [];
    for (let i = 0; i < n; i++) a.push((t * 37 + i * 101) & 255);
    try { S8(a); } catch (e) { fuzzOk = false; break; }
  }
  ok(fuzzOk, "無作為バイト列 400 通りでも投げない");
  ok(S8([0x41, 0xff, 0x42]) === "A�B", "不正バイトは U+FFFD 1 個に置き換わり前後は保たれる");
}

/* ══ 2. LINE / Instagram の Webhook 署名 ═══════════════════════ */
group("2. LINE / Instagram Webhook の署名検証");
{
  const body = E.simLineBody(3, "seed-a"), raw = JSON.stringify(body);
  const sig = E.lineSignature("channel-secret", raw);
  ok(E.lineVerify("channel-secret", raw, sig), "LINE: X-Line-Signature が一致する");
  ok(!E.lineVerify("channel-secret", raw, E.lineSignature("wrong", raw)), "LINE: 誤った秘密は拒否される");
  ok(!E.lineVerify("channel-secret", raw + " ", sig), "LINE: 本文が 1 文字違えば拒否される");
  const ing = E.msgIngestLine(raw, { channelSecret: "channel-secret", signature: sig });
  ok(ing.ok && ing.messages.length === 3, "LINE: Webhook から 3 通を取り込む");
  ok(ing.messages[0].platform === "line" && ing.messages[0].meta.replyToken, "LINE: replyToken を保持する");
  ok(E.msgIngestLine(raw, { channelSecret: "channel-secret", signature: "bogus" }).status === 401,
    "LINE: 署名不一致は 401");
}
{
  const body = E.simInstagramBody(2, "seed-b"), raw = JSON.stringify(body);
  const sig = E.igSignature("app-secret", raw);
  ok(sig.startsWith("sha256=") && sig.length === 71, "Instagram: sha256= 接頭辞つき hex");
  ok(E.igVerify("app-secret", raw, sig), "Instagram: X-Hub-Signature-256 が一致する");
  ok(!E.igVerify("app-secret", raw, E.igSignature("wrong", raw)), "Instagram: 誤った秘密は拒否される");
  const ing = E.msgIngestInstagram(raw, { appSecret: "app-secret", signature: sig });
  ok(ing.ok && ing.messages.length === 2 && ing.messages[0].platform === "instagram",
    "Instagram: Webhook から 2 通を取り込む");
  ok(E.msgIngestInstagram(raw, { appSecret: "app-secret", signature: "sha256=00" }).status === 401,
    "Instagram: 署名不一致は 401");
}
{
  const out = E.msgToOutbound(E.msgNew({ platform: "line", chatId: "U1", text: "こんにちは", meta: { replyToken: "rt1" } }));
  ok(out.endpoint === "https://api.line.me/v2/bot/message/reply" &&
     out.body.replyToken === "rt1" && out.body.messages[0].type === "text" &&
     out.body.messages[0].text === "こんにちは", "LINE: reply の送信要求が公式仕様の形");
  const push = E.msgToOutbound(E.msgNew({ platform: "line", chatId: "U2", text: "push" }));
  ok(push.endpoint === "https://api.line.me/v2/bot/message/push" && push.body.to === "U2",
    "LINE: replyToken が無ければ push になる");
  const ig = E.msgToOutbound(E.msgNew({ platform: "instagram", chatId: "1784140001", text: "hi" }), { igId: "1784149999" });
  ok(ig.endpoint === "https://graph.instagram.com/v21.0/1784149999/messages" &&
     ig.body.recipient.id === "1784140001" && ig.body.message.text === "hi",
    "Instagram: /<IG_ID>/messages の送信要求が公式仕様の形");
}

/* ══ 3. HD-PLC 物理層 ═══════════════════════════════════════════ */
group("3. HD-PLC 物理層 (IEEE 1901 ウェーブレット OFDM)");
{
  const x = [];
  for (let i = 0; i < 512; i++) x.push(Math.sin(i / 7) * 3 + Math.cos(i / 3) - i / 500);
  const y = E.dwtSynthesize(E.dwtAnalyze(x));
  let mx = 0; for (let i = 0; i < 512; i++) mx = Math.max(mx, Math.abs(y[i] - x[i]));
  ok(mx < 1e-9, "ウェーブレット変換: 解析と合成が厳密な逆変換", "最大誤差 " + mx.toExponential(1));
}
ok(E.PLC.N_CARRIER === 512 && Math.abs(E.PLC.DF - 50781.25) < 1e-6,
  "帯域 2–28 MHz を 512 分割", "Δf = " + (E.PLC.DF / 1e3).toFixed(2) + " kHz");
ok(Math.abs(E.PLC.SYMBOL_SEC * 1e6 - 19.69) < 0.01,
  "シンボル長 = 1/Δf (ガードインターバル無し)", (E.PLC.SYMBOL_SEC * 1e6).toFixed(2) + " µs");
ok(E.inHamBand(7.1e6) && E.inHamBand(14.2e6) && !E.inHamBand(5.0e6), "アマチュア無線帯の判定");
{
  const near = E.plcChannel("router", "study"), far = E.plcChannel("living", "bedroom");
  const avg = (a) => a.reduce((s, v) => s + v, 0) / a.length;
  ok(avg(near.snrDb) > avg(far.snrDb), "近いコンセントほど SNR が高い",
    avg(near.snrDb).toFixed(1) + " dB > " + avg(far.snrDb).toFixed(1) + " dB");
  ok(E.plcCouplingDb("router", "study") < E.plcCouplingDb("living", "kitchen"),
    "分岐が多いほど結合損が大きい");
  const same = E.plcChannel("router", "study");
  ok(JSON.stringify(same.snrDb) === JSON.stringify(near.snrDb), "同じコンセント対なら回線特性は再現する");
}
{
  const ch = E.plcChannel("living", "kitchen"), tm = E.plcToneMap(ch);
  let notchOk = true, capOk = true;
  for (let i = 0; i < E.PLC.N_CARRIER; i++) {
    if (tm.notched[i] && tm.bits[i] !== 0) notchOk = false;
    if (tm.bits[i] > E.PLC.MAX_BITS) capOk = false;
  }
  ok(notchOk, "ノッチしたサブキャリアにはビットを割り当てない", tm.notchCount + " 本をノッチ");
  ok(capOk, "割当ビットは 32-PAM (5 bit) が上限");
  ok(tm.activeCarriers > 50 && tm.phyBps > 1e6, "適応ビットローディング",
    (tm.phyBps / 1e6).toFixed(1) + " Mbps / 有効 " + tm.activeCarriers + " 本 / 平均 " + tm.avgBits.toFixed(2) + " bit");
  const hist = [0, 0, 0, 0, 0, 0]; tm.bits.forEach((b) => hist[b]++);
  ok(hist.filter((h) => h > 0).length >= 3, "SNR に応じてビット数が分布する", "0–5 → " + hist.join("/"));
}
{
  const ch = E.plcChannel("router", "study"), tm = E.plcToneMap(ch);
  const txt = "ウルトラネットワーク payload 0123456789 ✓ 電力線";
  const p = U8(txt), mod = E.plcModulate(p, tm);
  ok(S8(E.plcDemodulate(mod.samples, tm, mod.bitLen)) === txt,
    "ウェーブレット OFDM の完全往復", mod.nSymbols + " シンボル / " + mod.samples.length + " 標本");
  const noisy = E.plcThroughChannel(mod.samples, ch, tm, 0, "n1");
  ok(S8(E.plcDemodulate(noisy, tm, mod.bitLen)) === txt, "設計 SNR では回線雑音を通しても誤らない");
  const bad = E.plcThroughChannel(mod.samples, ch, tm, 22, "n2");
  ok(S8(E.plcDemodulate(bad, tm, mod.bitLen)) !== txt, "22 dB 劣化させると誤りが現れる");
}
{
  const p = U8("frame test ペイロード"), f = E.plcFrame(p, { src: 1, dst: 2, cap: 2 });
  const good = E.plcDeframe(f.bytes);
  ok(good.ok && S8(good.bytes) === "frame test ペイロード", "IEEE 1901 フレームの組立と分解",
    f.nBlocks + " PB × " + 520 + " バイト");
  const t1 = f.bytes.slice(); t1[40] ^= 0xff;
  ok(E.plcDeframe(t1).reason === "pb-crc", "ペイロード破損を CRC-32 が検出");
  const t2 = f.bytes.slice(); t2[10] ^= 0xff;
  ok(E.plcDeframe(t2).reason === "fc-crc", "フレーム制御の破損を CRC-24 が検出");
  const t3 = f.bytes.slice(); t3[0] ^= 0xff;
  ok(E.plcDeframe(t3).reason === "no-preamble", "プリアンブル欠落を検出");
  const big = U8("あ".repeat(600));
  ok(S8(E.plcDeframe(E.plcFrame(big, {}).bytes).bytes) === "あ".repeat(600), "複数 PB ブロックにまたがる搬送");
}
{
  const r = E.plcCsma([{ name: "A", cap: 1 }, { name: "B", cap: 3 }, { name: "C", cap: 3 }, { name: "D", cap: 0 }], "x");
  ok(r.maxCap === 3 && ["B", "C"].includes(r.winner), "CSMA/CA: 最優先 CAP が送信権を取る", "勝者 " + r.winner);
  ok(r.prs0.includes("B") && !r.prs0.includes("D"), "PRS0 スロットで CAP≧2 が主張する");
}

/* ══ 4. NTT 写像層 ══════════════════════════════════════════════ */
group("4. NTT 電話回線への写像");
{
  const reg = E.nttRegistryNew();
  const urls = ["zone://url.or.jp/", "zone://url.or.jp/news", "zone://bada.or.jp/",
                "zone://url.or.jp/msg/line/U1", "zone://url.or.jp/msg/instagram/17841"];
  let allBack = true, allStable = true, fmtOk = true;
  urls.forEach((u) => {
    const rec = E.nttMap(reg, u, "geo");
    if (E.nttUnmap(reg, rec.number) !== u) allBack = false;
    if (E.nttMap(reg, u, "geo").number !== rec.number) allStable = false;
    if (!/^\d{10}$/.test(rec.number)) fmtOk = false;
    if (rec.e164 !== "+81" + rec.number.slice(1)) fmtOk = false;
  });
  ok(allBack, "写像 φ⁻¹ が厳密な逆写像", E.nttMap(reg, urls[0], "geo").display + " ↦ " + urls[0]);
  ok(allStable, "写像 φ は安定 (同じ URL は常に同じ番号)");
  ok(fmtOk, "0AB-J は 10 桁、E.164 は +81 で表される");
  ok(E.nttMap(reg, urls[0], "ip").number.startsWith("050"), "050 の IP 電話帯へも写せる");
  ok(E.nttMap(reg, urls[0], "mobile").number.startsWith("090"), "090 の携帯帯へも写せる");
  ok(E.nttUnmap(reg, "03-1234-5678") === null, "未割当の番号は逆引きできない");
  ok(E.nttFormat("03", "12345678") === "03-1234-5678" && E.nttFormat("011", "2345678") === "011-234-5678",
    "番号の整形");
}
{
  const reg = E.nttRegistryNew();
  reg.byNumber[E.nttMap(reg, "zone://a.or.jp/", "ip").number] = "zone://squatter/";
  const rec = E.nttMap(reg, "zone://b.or.jp/", "ip");
  ok(!!rec.number, "衝突時は空き番号を線形探索して割り当てる");
}
{
  const txt = "音声帯 300–3400 Hz を通す封筒 #42 ✓";
  const p = U8(txt);
  const metal = E.nttBearerSend(p, "metal");
  ok(S8(E.nttBearerRecv(metal)) === txt, "メタル: 音声帯 16-QAM の往復",
    metal.bps + " bps / " + metal.baud + " baud / " + metal.nSymbols + " シンボル");
  ok(metal.bps === 8000 && metal.baud === 2000, "V.32 型 16-QAM のパラメータ");
  const pts = E.nttConstellation(metal.samples, 200);
  ok(pts.every((q) => [1, 3].includes(Math.abs(Math.round(q.i))) && [1, 3].includes(Math.abs(Math.round(q.q)))),
    "受信点が 16-QAM の格子上に乗る");
  const isdn = E.nttBearerSend(p, "isdn");
  ok(S8(E.nttBearerRecv(isdn)) === txt, "INS ネット 64: B チャネルのディジタル透過", isdn.octets.length + " オクテット");
  const hikari = E.nttBearerSend(p, "hikari");
  ok(S8(E.nttBearerRecv(hikari)) === txt, "ひかり電話: G.711 µ-law + RTP の往復",
    hikari.packets.length + " パケット (PCMU 20 ms)");
  ok(hikari.packets[0].header[1] === 0 && hikari.packets[0].payload.length === 160,
    "RTP ヘッダが PT=0 (PCMU) / 20 ms ペイロード");
  const shuffled = { kind: "rtp", line: "hikari", bitLen: hikari.bitLen, packets: hikari.packets.slice().reverse() };
  ok(S8(E.nttBearerRecv(shuffled)) === txt, "RTP パケットの順序が乱れても並べ直して復元する");
}
{
  let worst = 0;
  for (let v = -8000; v <= 8000; v += 137) {
    const d = E.muLawDecode(E.muLawEncode(v));
    worst = Math.max(worst, Math.abs(d - v) / (Math.abs(v) + 200));
  }
  ok(worst < 0.09, "G.711 µ-law の量子化誤差が判定余裕の内側", "最大 " + (worst * 100).toFixed(1) + "%");
}
{
  const reg = E.nttRegistryNew();
  const call = E.nttCall(reg, "zone://url.or.jp/", "zone://bada.or.jp/", "hikari");
  ok(call.states.length === 6 && call.states[0].st === "on-hook" && call.states[5].st === "data",
    "呼制御の状態機械", call.from.display + " → " + call.to.display);
}

/* ══ 5. zone:// ═════════════════════════════════════════════════ */
group("5. zone:// ウルトラネットワーク WWW");
{
  const z = E.zoneParse("zone://url.or.jp/msg/line/U1");
  ok(z && z.host === "url.or.jp" && z.path === "/msg/line/U1" && z.labels.join(".") === "url.or.jp",
    "zone:// の文法を解析する");
  ok(E.zoneParse("zone://url.or.jp").path === "/", "パス省略時は / になる");
  ok(E.zoneParse("https://url.or.jp/") === null && E.zoneParse("x zone://y") === null,
    "zone:// 以外は拒否する (400 bad-zone)");
  ok(E.strHash("zone://url.or.jp/") === E.strHash("zone://url.or.jp/") &&
     E.zoneId("zone://url.or.jp/") < E.RING, "zone_id はリング位数の内側に落ちる");
}
{
  const net = E.netSort(E.ZONE_PEERS.map(E.peerNew));
  ok(net.length === 6 && net.every((p, i) => i === 0 || net[i - 1].id <= p.id), "リングは node-id 順に整列する");
  let allReach = true;
  for (const u of ["zone://url.or.jp/", "zone://bada.or.jp/x", "zone://url.or.jp/msg/line/U9"]) {
    const key = E.zoneId(u);
    const r = E.dhtRoute(net, net[0], key);
    if (r.peer.name !== E.dhtNearest(net, key).name) allReach = false;
  }
  ok(allReach, "貪欲ルーティングが担当ピアへ到達する");
  ok(E.ringDist(10, E.RING - 10) === 20, "リング距離は巡回的");
}
{
  const u = E.ultraNew();
  const route = E.dhtRoute(u.ctx.net, u.ctx.net[0], E.zoneId("zone://url.or.jp/"));
  const blk = E.zoneServeBlock(u.ctx, "zone://url.or.jp/", 200, "# home", route, { ct: [11, 22, 33], tag: 99 }, 12345);
  ok(blk.includes("@@HOST url.or.jp") && blk.includes("@@PATH /") && blk.includes("@@STATUS 200") &&
     blk.includes("@@BODY_BEGIN") && blk.includes("@@BODY_END") && blk.includes("@@JONESKEY 12345"),
    "ZoneBrowser が読む @@ ブロックを出力する");
  ok(E.ZONE_STATUS[409] === "zone-guard-reject" && E.ZONE_STATUS[495] === "quantum-channel-compromised",
    "状態符号が既存の zone:// 実装と同じ");
}
{
  const rec = { url: "zone://url.or.jp/msg/line/U1", salt: 1234, tag: 3735928559, ct: [0, 65535, 1, 42] };
  const back = E.envelopeDecode(E.envelopeEncode(rec));
  ok(back.ok && back.url === rec.url && back.salt === rec.salt && back.tag === rec.tag &&
     JSON.stringify(back.ct) === JSON.stringify(rec.ct), "封筒の符号化と復号が往復する");
  ok(E.envelopeDecode([1, 2, 3]).status === 400, "壊れた封筒は 400 bad-zone");
}

/* ══ 6. Jones 多項式量子暗号 ════════════════════════════════════ */
group("6. Jones 多項式量子暗号");
{
  ok(Math.abs(E.kauffman([], 1.0) - 1.0) < 1e-12, "交点の無い図のブラケットは 1");
  const tre = E.zoneDiagram("url.or.jp"), fig = E.zoneDiagram("bada.or.jp");
  ok(tre.length === 3 && fig.length === 4, "三葉結び目は交点 3、8 の字結び目は交点 4");
  const ka = E.jonesKey(tre), kb = E.jonesKey(fig);
  ok(ka !== kb, "異なる結び目は異なる鍵を与える", "三葉 " + ka + " / 8 の字 " + kb);
  ok(E.jonesKey(tre) === ka, "鍵導出は決定的");
}
{
  const key = E.jonesKey(E.zoneDiagram("url.or.jp"));
  const other = E.jonesKey(E.zoneDiagram("bada.or.jp"));
  const txt = "コンセントから zone:// が見えてる 🔌 — 日本語と絵文字";
  const sealed = E.zoneSeal(txt, key, 7);
  ok(E.zoneOpen(sealed, key).text === txt, "AEAD の往復 (16 bit 符号単位なので CJK も通る)");
  ok(sealed.ct.every((v) => v >= 0 && v < 65536), "暗号文は 16 bit 符号単位に収まる");
  const t = { ct: sealed.ct.slice(), salt: sealed.salt, tag: sealed.tag }; t.ct[0] = (t.ct[0] + 1) % 65536;
  ok(E.zoneOpen(t, key).status === 409, "暗号文の改竄は 409 zone-guard-reject");
  const t2 = { ct: sealed.ct, salt: sealed.salt, tag: sealed.tag + 1 };
  ok(E.zoneOpen(t2, key).status === 409, "タグの偽造は 409");
  ok(E.zoneOpen(sealed, other).status === 409, "結び目が違えば開封できない");
  ok(E.zoneSeal(txt, key, 7).tag !== E.zoneSeal(txt, key, 8).tag, "ソルトが変わればタグも変わる");
}
{
  const good = E.qkdSession(3, false), tapped = E.qkdSession(3, true);
  ok(good.ok && good.forbidden < 1e-12, "Bell 対: 禁止状態 |01⟩,|10⟩ が厳密に 0", "Σ=" + good.forbidden);
  ok(Math.abs(good.dist[0] - 0.5) < 1e-12 && Math.abs(good.dist[3] - 0.5) < 1e-12, "|00⟩ と |11⟩ が各 1/2");
  ok(!tapped.ok && tapped.forbidden > 1e-6, "盗聴すると相関が壊れ検出される", "Σ=" + tapped.forbidden.toFixed(4));
  const reg0 = E.qubit(2);
  ok(reg0.amp[0] === 1 && reg0.amp.slice(1).every((v) => v === 0), "qubit(n) は |0…0⟩ から始まる");
  const xr = E.measure(E.gateX(E.qubit(1), 0));
  ok(Math.abs(xr[1] - 1) < 1e-12, "X ゲートが |0⟩ を |1⟩ にする");
}

/* ══ 7. STREAMS 全層 ════════════════════════════════════════════ */
group("7. AT&T ベル研究所式 STREAMS — 全 5 層の往復");
{
  const u = E.ultraNew({ lineId: "metal" });
  ok(u.stream.modules.map((x) => x.name).join(",") === "ntt,zone,jones,msgmux",
    "driver の上に 4 モジュールが積まれている", "plc ← ntt ← zone ← jones ← msgmux ← head");
  const msg = E.msgNew({ platform: "line", chatId: "U4af", displayName: "田中 さくら",
    text: "電力線から NTT を経て zone:// へ 🔌☎🌐" });
  const r = E.ultraSend(u, msg);
  ok(r.ok && r.identical, "全 5 層を通した往復が完全一致", r.status + " " + r.reason);
  ok(r.received.text === msg.text && r.received.displayName === msg.displayName,
    "本文と表示名が保たれる");
  const names = r.trace.map((t) => t.dir[0] + t.module).join(" ");
  ok(names === "dhead dmsgmux djones dzone dntt dplc uplc untt uzone ujones umsgmux uhead",
    "下りと上りが各層を 1 回ずつ通る", names);
  ok(r.phy.nSymbols > 0 && r.phy.phyBps > 1e6 && r.wireSamples > 0, "物理層の計量が得られる",
    r.phy.nSymbols + " OFDM シンボル / " + (r.phy.phyBps / 1e6).toFixed(0) + " Mbps / " +
    (r.phy.airTimeSec * 1e6).toFixed(0) + " µs 占有");
  ok(r.ntt.number.number.length === 10 && r.zone.route.peer && r.crypto.key > 0,
    "各層が自分の計量を残す", "φ=" + r.ntt.number.display + " / ピア=" + r.zone.route.peer.name);
  ok(u.ctx.ledger.length >= 2, "アカシック台帳に追記される", u.ctx.ledger.length + " 件");
}
{
  for (const line of ["metal", "isdn", "hikari"]) {
    const u = E.ultraNew({ lineId: line });
    const r = E.ultraSend(u, E.msgNew({ platform: "instagram", chatId: "17841", text: "配線図の写真あげたよ" }));
    ok(r.ok && r.identical, "回線種別ごとの往復: " + E.NTT_LINES[line].name);
  }
}
{
  for (const pair of [["router", "study"], ["living", "kitchen"], ["bedroom", "router"]]) {
    const u = E.ultraNew();
    E.ultraRelink(u, pair[0], pair[1], "metal");
    const r = E.ultraSend(u, E.msgNew({ platform: "line", chatId: "U1", text: "コンセントを変えても届く" }));
    ok(r.ok && r.identical, "コンセント対 " + pair.join(" → ") + " でも往復する",
      (r.phy.phyBps / 1e6).toFixed(0) + " Mbps");
  }
}
group("   攻撃 — それぞれ正しい状態符号で排除される");
{
  const mk = () => E.msgNew({ platform: "line", chatId: "U1", text: "攻撃試験" });
  const a = E.ultraNew(); a.ctx.tamper = true;
  const ra = E.ultraSend(a, mk());
  ok(!ra.ok && ra.status === 503, "物理層で回線を改竄 → PLC の CRC が弾く", ra.status + " " + ra.reason);

  const b = E.ultraNew(); b.ctx.tamperZone = true;
  const rb = E.ultraSend(b, mk());
  ok(!rb.ok && rb.status === 409, "悪意あるピアがレコードを書換え → AEAD が弾く", rb.status + " " + rb.reason);

  const c = E.ultraNew(); c.ctx.tapped = true;
  const rc = E.ultraSend(c, mk());
  ok(!rc.ok && rc.status === 495, "量子路を盗聴 → 送信そのものを止める", rc.status + " " + rc.reason);

  const d = E.ultraNew({ marginDb: 22, seed: "deg" });
  const rd = E.ultraSend(d, mk());
  ok(!rd.ok, "電力線を 22 dB 劣化させる → 復号できない", rd.status + " " + rd.reason);
}
{
  const u = E.ultraNew({ lineId: "hikari" });
  const a = E.ultraIngest(u, "line", 3, "cs", "i1");
  const b = E.ultraIngest(u, "instagram", 2, "as", "i2");
  ok(a.ok && a.results.every((x) => x.ok && x.identical), "LINE の 3 通が受信箱まで届く");
  ok(b.ok && b.results.every((x) => x.ok && x.identical), "Instagram の 2 通が受信箱まで届く");
  ok(u.inbox.messages.length === 5, "統合受信箱に 5 通", E.inboxThreads(u.inbox).length + " スレッド");
  const th = E.inboxThreads(u.inbox);
  ok(th.every((t) => t.messages.length > 0) &&
     th.every((t, i) => i === 0 || th[i - 1].messages[th[i - 1].messages.length - 1].ts >= t.messages[t.messages.length - 1].ts),
    "スレッドは最新順に並ぶ");
  ok(th.some((t) => t.platform === "line") && th.some((t) => t.platform === "instagram"),
    "LINE と Instagram が 1 つの受信箱に同居する");
}
{
  const m = E.msgNew({ platform: "line", chatId: "U1", displayName: "田中", text: "直列化 ✓", meta: { replyToken: "rt" } });
  const back = E.msgDeserialize(E.msgSerialize(m));
  ok(back.text === m.text && back.displayName === m.displayName && back.meta.replyToken === "rt",
    "統合メッセージの直列化が往復する");
  ok(E.msgZoneUrl(m) === "zone://url.or.jp/msg/line/U1", "メッセージの zone アドレス");
}

/* ── 総括 ── */
console.log("\n" + "─".repeat(58));
console.log("合格 " + pass + " / " + (pass + fail) + (fail ? ("  不合格 " + fail) : "  — すべて合格"));
process.exit(fail ? 1 : 0);
