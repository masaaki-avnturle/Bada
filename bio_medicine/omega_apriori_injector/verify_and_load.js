/*
 * verify_and_load.js — ホストアプリ側ローダ (署名検証 → 付加)
 *
 * 任意のWebアプリに本ファイルを読み込み、署名付きバンドル(plugin.js)を
 * manifest.json の ECDSA 署名で検証し、改竄が無い正規バンドルのみ実行して
 * 未知事前エンジンAI (window.omegaApriori) を付加する。
 *
 *   <script src="verify_and_load.js"></script>
 *   <script>
 *     omegaVerifyAndLoad("omega-apriori.plugin.js","omega-apriori.manifest.json")
 *       .then(function(eng){ console.log("attached:", eng.capabilities()); });
 *   </script>
 *
 * ⚠ 概念実証・教育用。付加は自分が管理する/許諾されたアプリに対してのみ。
 */
(function (global) {
  "use strict";
  var SIGN = { name: "ECDSA", hash: "SHA-256" }, ALG = { name: "ECDSA", namedCurve: "P-256" };

  function b642ab(b) { var s = atob(b), a = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) a[i] = s.charCodeAt(i); return a; }
  async function sha256hex(text) {
    var d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.prototype.map.call(new Uint8Array(d), function (x) { return x.toString(16).padStart(2, "0"); }).join("");
  }

  // bundleText/manifest を直接渡す検証＋実行
  global.omegaVerifyBundle = async function (bundleText, manifest) {
    if (manifest.bundle_sha256) {
      var dg = await sha256hex(bundleText);
      if (dg !== manifest.bundle_sha256) throw new Error("sha256 mismatch — bundle altered");
    }
    var pub = await crypto.subtle.importKey("jwk", manifest.pubkey_jwk, ALG, true, ["verify"]);
    var ok = await crypto.subtle.verify(SIGN, pub, b642ab(manifest.signature_b64),
      new TextEncoder().encode(bundleText));
    if (!ok) throw new Error("signature INVALID — refusing to execute");
    (0, eval)(bundleText);            // 検証済みのみ実行 → window.omegaApriori
    return global.omegaApriori;
  };

  // URL から取得して検証＋実行
  global.omegaVerifyAndLoad = async function (bundleUrl, manifestUrl) {
    var bundle = await (await fetch(bundleUrl)).text();
    var manifest = await (await fetch(manifestUrl)).json();
    return global.omegaVerifyBundle(bundle, manifest);
  };
})(typeof window !== "undefined" ? window : globalThis);
