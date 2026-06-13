#!/usr/bin/env node
/*
 * run_plugin.js — Ω-Apriori プラグイン: ビルド / 電子署名 / 検証 / 実行 (Node CLI)
 *
 * 「未知事前エンジンAI」を任意アプリに付加するための署名付きJSバンドルを生成・検証・実行する。
 * 電子デジタル署名の原理(ECDSA P-256 / SHA-256, Web Crypto)で、改竄されていない正規の
 * バンドルだけを検証通過させてから実行する。ブラウザの index.html と同一方式。
 *
 *   node run_plugin.js keygen <priv.jwk.json> <pub.jwk.json>
 *   node run_plugin.js build  <spec.json> <out_bundle.js>
 *   node run_plugin.js sign   <bundle.js> <priv.jwk.json> <pub.jwk.json> <out_manifest.json>
 *   node run_plugin.js verify <bundle.js> <manifest.json>
 *   node run_plugin.js run    <bundle.js> <manifest.json>        # 検証→実行→デモ
 *
 * spec.json: { "cfg":{inbits,layers,width,outbits}, "genome_hex":"..", "plugins":["go_lookahead",..] }
 *
 * ⚠ 概念実証・教育用。付加は自分が管理する/許諾されたアプリに対してのみ。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { webcrypto } = require("node:crypto");
const subtle = webcrypto.subtle;

const HERE = __dirname;
const ALG = { name: "ECDSA", namedCurve: "P-256" };
const SIGN_ALG = { name: "ECDSA", hash: "SHA-256" };

function b64(buf) { return Buffer.from(buf).toString("base64"); }
function unb64(s) { return new Uint8Array(Buffer.from(s, "base64")); }
async function sha256hex(text) {
  const d = await subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Buffer.from(d).toString("hex");
}

async function keygen(privPath, pubPath) {
  const kp = await subtle.generateKey(ALG, true, ["sign", "verify"]);
  const priv = await subtle.exportKey("jwk", kp.privateKey);
  const pub = await subtle.exportKey("jwk", kp.publicKey);
  fs.writeFileSync(privPath, JSON.stringify(priv, null, 1));
  fs.writeFileSync(pubPath, JSON.stringify(pub, null, 1));
  console.log("keypair written:", privPath, pubPath);
}

// runtime + 選択プラグイン + bootstrap を連結した自己完結バンドルを生成
function buildBundle(spec) {
  const runtime = fs.readFileSync(path.join(HERE, "apriori_runtime.js"), "utf8");
  let parts = ["/* Ω-Apriori signed bundle — conceptual/educational only */", runtime];
  const wanted = spec.plugins || [];
  for (const name of wanted) {
    const p = path.join(HERE, "plugins", name + ".js");
    if (!fs.existsSync(p)) throw new Error("unknown plugin: " + name);
    parts.push(fs.readFileSync(p, "utf8"));
  }
  const manifest = { cfg: spec.cfg, genome_hex: spec.genome_hex, plugins: wanted };
  const boot = `
/* bootstrap: instantiate engine and attach plugins to host */
(function(){
  var G = (typeof window!=='undefined')?window:globalThis;
  var M = ${JSON.stringify(manifest)};
  var eng = new G.OmegaApriori(M);
  var P = G.OMEGA_PLUGINS||{};
  (M.plugins||[]).forEach(function(n){ if(P[n]) eng.register(P[n]); });
  G.omegaApriori = eng;
  if (typeof console!=='undefined') console.log("Ω-Apriori attached. capabilities:", eng.capabilities());
})();
`;
  parts.push(boot);
  return parts.join("\n");
}

async function importPriv(jwk) { return subtle.importKey("jwk", jwk, ALG, true, ["sign"]); }
async function importPub(jwk) { return subtle.importKey("jwk", jwk, ALG, true, ["verify"]); }

async function sign(bundlePath, privPath, pubPath, manifestOut) {
  const bundle = fs.readFileSync(bundlePath, "utf8");
  const priv = await importPriv(JSON.parse(fs.readFileSync(privPath, "utf8")));
  const pubJwk = JSON.parse(fs.readFileSync(pubPath, "utf8"));
  const data = new TextEncoder().encode(bundle);
  const sig = await subtle.sign(SIGN_ALG, priv, data);
  const manifest = {
    engine: "Omega-Apriori", note: "conceptual/educational only",
    alg: "ECDSA-P256-SHA256",
    bundle_file: path.basename(bundlePath),
    bundle_sha256: await sha256hex(bundle),
    signature_b64: b64(sig),
    pubkey_jwk: pubJwk,
    created: new Date().toISOString()
  };
  fs.writeFileSync(manifestOut, JSON.stringify(manifest, null, 1));
  console.log("signed →", manifestOut, "\n  sha256:", manifest.bundle_sha256.slice(0, 24) + "…");
}

async function verify(bundlePath, manifestPath) {
  const bundle = fs.readFileSync(bundlePath, "utf8");
  const m = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const digest = await sha256hex(bundle);
  if (m.bundle_sha256 && m.bundle_sha256 !== digest) {
    console.error("✗ sha256 mismatch — bundle altered"); return false;
  }
  const pub = await importPub(m.pubkey_jwk);
  const ok = await subtle.verify(SIGN_ALG, pub, unb64(m.signature_b64), new TextEncoder().encode(bundle));
  console.log(ok ? "✓ signature VALID — bundle authentic & untampered"
                 : "✗ signature INVALID — do not execute");
  return ok;
}

async function run(bundlePath, manifestPath) {
  const ok = await verify(bundlePath, manifestPath);
  if (!ok) { console.error("refusing to execute unverified bundle"); process.exit(2); }
  const bundle = fs.readFileSync(bundlePath, "utf8");
  // 検証済みバンドルを実行 (globalThis.omegaApriori を生成)
  (0, eval)(bundle);
  const eng = globalThis.omegaApriori;
  console.log("\n--- demo ---");
  console.log("infer(0b101101) =", eng.infer(0b101101));
  const caps = eng.capabilities();
  if (caps.includes("completion"))
    console.log("completion('AI',4) =", eng.call("completion", "AI", 4).predicted);
  if (caps.includes("overview")) {
    const grid = [[1, 2, 3, 4], [2, 9, 8, 1], [0, 1, 7, 2], [3, 1, 0, 1]];
    console.log("overview:", eng.call("overview", grid, { rows: 2, cols: 2 }).summary);
  }
  if (caps.includes("go_lookahead")) {
    const b = [[0, 0, 0], [0, 1, 2], [0, 0, 0]];
    console.log("go_lookahead best move:", eng.call("go_lookahead", b, 1, 2).move);
  }
}

async function main() {
  const [cmd, ...a] = process.argv.slice(2);
  try {
    if (cmd === "keygen") await keygen(a[0] || "priv.jwk.json", a[1] || "pub.jwk.json");
    else if (cmd === "build") {
      const spec = JSON.parse(fs.readFileSync(a[0], "utf8"));
      fs.writeFileSync(a[1] || "omega-apriori.plugin.js", buildBundle(spec));
      console.log("bundle built →", a[1] || "omega-apriori.plugin.js");
    }
    else if (cmd === "sign") await sign(a[0], a[1], a[2], a[3] || "omega-apriori.manifest.json");
    else if (cmd === "verify") process.exit((await verify(a[0], a[1])) ? 0 : 1);
    else if (cmd === "run") await run(a[0], a[1]);
    else {
      console.log("usage: node run_plugin.js <keygen|build|sign|verify|run> ...");
      process.exit(1);
    }
  } catch (e) { console.error("error:", e.message); process.exit(1); }
}
main();
