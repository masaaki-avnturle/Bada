/*
 * chat.js — BadaGPT の対話層 (依存: engine.js)
 *
 * 言語モデルではありません。入力文からキーワードで意図を判定し、engine.js の
 * 計算を実行して、その結果と判定 (証明完了 / 反証 / 未解決) を文章にします。
 * 応答のたびに「意図 → 実行 → 検証」の過程を開示します。
 */
(function (global) {
  "use strict";
  var E = global.BadaGPTEngine || (typeof require !== "undefined" ? require("./engine.js") : null);

  var SYMBOL = { proved: "∎ 証明完了 (QED)", verified: "∎ 数値検証完了", disproved: "✗ 反証（反例あり）",
                 open: "? 未解決（経験的証拠のみ）", inconclusive: "… 判定不能" };
  var OPEN_NOTE = "有限の範囲をいくら調べても、予想そのものの証明にはなりません。";

  function num(text, re, dflt, lo, hi) {
    var m = text.match(re); if (!m) return dflt;
    return Math.max(lo, Math.min(hi, +m[1]));
  }

  function detect(text) {
    var t = text.toLowerCase();
    if (/[=＝]/.test(text) && /(σ|Σ|∑|sum|和|帰納|[nk]\s*[\^²³(])/i.test(text)) return "induct";
    if (/(検査|ガード|guard|patchguard|改ざん)/.test(t)) return "guard";
    if (/(証明書|封印|certificate|すべて|全部|まとめて)/.test(t)) return "certificate";
    if (/(深リーマン|deep|drh|オイラー積)/.test(t)) return "drh";
    if (/(リーマン|riemann|零点|\brh\b)/.test(t)) return "rh";
    if (/(コラッツ|collatz|3n\s*\+\s*1)/.test(t)) return "collatz";
    if (/(ゴールドバッハ|goldbach)/.test(t)) return "goldbach";
    if (/(ルジャンドル|legendre)/.test(t)) return "legendre";
    if (/(ゼータ|zeta|ζ)/.test(t)) return "zeta";
    if (/(量子|grover|グローバー|反例)/.test(t)) return "quantum";
    if (/(帰納|induction)/.test(t)) return "induction_demo";
    if (/(未解決|予想|conjecture)/.test(t)) return "quantum";
    return "help";
  }

  function qLines(q) {
    var out = ["【量子探索】" + q.title + ": " + q.statement,
               "  擬似量子コンピュータ " + q.qubits + " 量子ビット, n = " + q.range[0] + "〜" + q.range[1] +
               ", Grover 反復 " + q.iterations + " 回, 反例の観測確率 " + q.success_probability.toFixed(4)];
    if (q.status === "disproved")
      out.push("  判定: " + SYMBOL.disproved + "  反例 n = " + q.counterexample + "（範囲内の反例 " + q.counterexamples_in_range + " 個、古典的に再検査済み）");
    else if (q.bounded_status === "verified") out.push("  判定: " + SYMBOL.open + "  この範囲に反例なし（全数検査）");
    else out.push("  判定: " + SYMBOL.inconclusive + "  " + q.shots + " 回の測定で反例を観測できず");
    return out;
  }
  function rhLines(rh) {
    return ["【命題】" + rh.claim, "  判定: " + SYMBOL[rh.status],
            "    偏角の原理による零点総数 N(T) = " + rh.zeros_in_strip_argument_principle +
            "  (整数からのずれ " + rh.argument_principle_residual.toExponential(2) + ")",
            "    臨界線上の符号変化の個数   = " + rh.zeros_on_critical_line_sign_changes,
            "    最初の零点: " + rh.first_zeros.map(function (z) { return z.toFixed(6); }).join(", ")];
  }
  function schLines(s) {
    return ["【命題】(RH と同値な Schoenfeld 不等式の有限部分) " + s.claim, "  判定: " + SYMBOL[s.status],
            "    最大比 = " + s.max_ratio.toFixed(4) + " (x = " + s.max_ratio_at + ")  ※ 1 未満なら成立"];
  }
  function drhLines(d) {
    var out = ["【命題】(深リーマン予想) " + d.claim, "  判定: " + SYMBOL.open,
               "    L(s,χ) = " + d.L[0].toFixed(9) + (d.L[1] < 0 ? "" : "+") + d.L[1].toFixed(9) + "i" + (d.sqrt2_factor ? "   極限は √2·L(s,χ)" : ""),
               "    x          DRH極限との相対誤差   素のL(s,χ)との相対誤差"];
    d.table.forEach(function (r) {
      out.push("    " + String(r.x).padEnd(10) + " " + r.rel_error_vs_DRH_limit.toFixed(6).padEnd(21) + " " + r.rel_error_vs_plain_L.toFixed(6));
    });
    return out;
  }
  function inductLines(e) {
    if (e.kind === "sum_identity")
      return ["【帰納法】" + e.claim, "  判定: " + SYMBOL[e.status]].concat(e.steps.map(function (x) { return "    " + x; }));
    if (e.kind === "repair")
      return ["【帰納法＋修正】" + e.original.claim, "  元の主張: " + SYMBOL[e.original.status] + "  " + e.original.steps[0],
              "  保存量のドリフト: " + e.drift_before + "  →  " + e.drift_after,
              "  修正後: " + e.repaired.claim, "  判定: " + SYMBOL[e.repaired.status]];
    if (e.kind === "collatz_descent")
      return ["【補集合の解析】" + e.claim, "  判定: " + SYMBOL[e.status] + "  （手法: " + e.method + "）",
              "    剰余類の " + (e.excluded_fraction * 100).toFixed(2) + "% を最小反例の候補から除外。コラッツ予想そのものは " + SYMBOL.open];
    return ["【帰納法の限界】" + e.problem + ": " + e.note];
  }
  function guardLines(rep, n) {
    var out = ["── 証明書 PatchGuard ──  段数 " + n + "  変更 " + Object.keys(rep.net_patch).length + " 箇所"];
    rep.findings.forEach(function (f) { out.push("  [" + f.severity + "] " + f.id + " " + f.why); });
    rep.cancelled.forEach(function (f) { out.push("  (相殺) " + f.id + " " + f.why); });
    out.push("判定: " + rep.verdict);
    return out;
  }

  // 「Σ f(k) = g(n)」という文から f, g を取り出す
  function parseClaim(text) {
    var parts = text.replace(/_\s*(\([^)]*\)|\{[^}]*\})/, "").split(/[=＝]/);
    if (parts.length !== 2) throw new Error("「Σ f(k) = g(n)」の形で書いてください");
    var lhs = parts[0].replace(/^.*(Σ|∑|σ|sum|総和|帰納法[でに]?)/i, "");
    var rhs = parts[1].replace(/(を|で|は|の|から|について)?\s*(証明|判定|確認|帰納|論文|ソース|コード|厳密|生成).*$/, "");
    return { f: E.pParse(lhs), g: E.pParse(rhs) };
  }

  var HELP = [
    "BadaGPT は、数学の予想を「計算で確かめられる範囲」で調べる対話アプリです。話しかけ方の例:",
    "  ・リーマン予想を高さ 1000 まで調べて",
    "  ・深リーマン予想の証拠を見せて",
    "  ・Σ k^2 = n(n+1)(2n+1)/5        ← 帰納法で判定し、誤りなら修正します",
    "  ・コラッツ予想を 14 ビットで / ゴールドバッハ予想 / ルジャンドル予想",
    "  ・未解決問題の反例を 12 量子ビットで探して",
    "  ・ζ(0.5+14.1347i)",
    "  ・証明書を作って → 証明書を検査して",
    "",
    "※ リーマン予想・深リーマン予想などの未解決問題そのものは証明できません。判定は必ず「未解決」になります。"
  ];

  // reply(text, state) → { intent, lines[], steps[] }   (state.cert に最新の証明書を保持)
  function reply(text, state) {
    state = state || {};
    var intent = detect(text), lines = [], steps = ["① 意図解析: " + intent], T, k, q;
    try {
      if (intent === "rh") {
        T = num(text, /(\d+(?:\.\d+)?)/, 500, 20, 5000);
        steps.push("② 実行: 零点計数 (偏角の原理 と 符号変化), Schoenfeld 不等式, Lagarias 形の量子探索");
        lines = rhLines(E.verifyRH(T)).concat([""], schLines(E.schoenfeld(1e6)), [""], qLines(E.quantumSearch("riemann_lagarias", 10, 0)),
          ["", "【リーマン予想】 判定: " + SYMBOL.open, OPEN_NOTE]);
      } else if (intent === "drh") {
        steps.push("② 実行: 臨界線上のオイラー積の部分積 (x ≤ 10^6)");
        Object.keys(E.CHARACTERS).forEach(function (c) { lines = lines.concat(drhLines(E.drhEvidence(c, 0, 1e6)), [""]); });
        lines = lines.concat(drhLines(E.drhEvidence("chi_-4", 1, 1e6)), ["", "【深リーマン予想】 判定: " + SYMBOL.open,
          "収束は遅く単調でもありません。部分積は証拠であって証明ではありません。"]);
      } else if (intent === "induct") {
        var claim = parseClaim(text), f = claim.f, g = claim.g;
        steps.push("② 実行: 基底 g(0)=0 と 段 g(n+1)−g(n)−f(n+1)≡0 を厳密な有理数演算で検査");
        var res = E.proveSum(f, g);
        lines = inductLines(res);
        if (res.status === "disproved") {
          steps.push("③ 修正: 保存量 I(n)=g(n)−Σf(k) の等位集合 I≡0 へ射影");
          var rep = E.repairSum(f, g);
          lines = lines.concat(["  保存量のドリフト: " + rep.drift_before + "  →  " + rep.drift_after,
                                "  修正後: " + rep.repaired.claim, "  判定: " + SYMBOL[rep.status]]);
        }
      } else if (intent === "induction_demo") {
        steps.push("② 実行: 帰納法の例題・証明の修正・コラッツ降下補題");
        E.inductionReport(12).forEach(function (e) { lines = lines.concat(inductLines(e), [""]); });
      } else if (intent === "collatz") {
        k = num(text, /(\d+)\s*(?:ビット|bit)/i, 12, 1, 18);
        steps.push("② 実行: 降下補題 (法 2^" + k + ") と量子探索");
        lines = inductLines(E.collatzDescent(k)).concat([""], qLines(E.quantumSearch("collatz", Math.min(k, 14), 0)),
          ["", "【コラッツ予想】 判定: " + SYMBOL.open, "降下補題は最小反例の候補を絞るだけで、候補が空であることは示せません。"]);
      } else if (intent === "goldbach" || intent === "legendre") {
        k = num(text, /(\d+)\s*(?:量子ビット|ビット|qubit|bit)/i, 10, 2, 13);
        steps.push("② 実行: 擬似量子コンピュータで反例を Grover 探索");
        lines = qLines(E.quantumSearch(intent, k, 0)).concat(["", OPEN_NOTE]);
      } else if (intent === "quantum") {
        k = num(text, /(\d+)\s*(?:量子ビット|ビット|qubit|bit)/i, 10, 2, 13);
        steps.push("② 実行: 5 つの命題について擬似量子コンピュータ (" + k + " 量子ビット) で反例を探索");
        E.quantumSearchAll(k, 0).forEach(function (r) { lines = lines.concat(qLines(r), [""]); });
        lines.push("シミュレーションではオラクルの構成に 2^k 回の古典計算を使うため、量子的な高速化は得られません。");
      } else if (intent === "zeta") {
        var m = text.replace(/\s+/g, "").match(/(-?\d+(?:\.\d+)?)(?:([+-]\d+(?:\.\d+)?)i)?/);
        if (!m) throw new Error("ζ(0.5+14.1347i) のように s を指定してください");
        var sr = +m[1], si = m[2] ? +m[2] : 0;
        if (sr === 1 && si === 0) throw new Error("s = 1 は ζ の極です");
        steps.push("② 実行: Euler–Maclaurin 展開");
        q = E.zeta(sr, si);
        lines = ["ζ(" + sr + (si ? (si > 0 ? "+" : "") + si + "i" : "") + ") = " + q[0].toPrecision(12) + (q[1] < 0 ? " − " : " + ") + Math.abs(q[1]).toPrecision(12) + "i",
                 "|ζ| = " + Math.hypot(q[0], q[1]).toExponential(4) + "   （倍精度の数値計算）"];
      } else if (intent === "certificate") {
        T = num(text, /高さ\s*(\d+)/, 500, 20, 5000);
        steps.push("② 実行: 全検証を実行して証明書を作成し、Jones 多項式暗号で封印");
        state.previous = state.cert || null;
        state.cert = E.fullCertificate({ height: T, qubits: 10, sieveBits: 12 });
        var c = state.cert;
        lines = rhLines(c.rh_bounded).concat([""], schLines(c.schoenfeld), ["",
          "深リーマン予想の証拠 " + c.drh_evidence.length + " 件 / 量子探索 " + c.quantum_search.length + " 件 / 帰納法 " + c.induction.length + " 件を収録",
          "【リーマン予想】 判定: " + SYMBOL.open, "【深リーマン予想】 判定: " + SYMBOL.open, "",
          "封印: 組みひも [" + c.seal.braid + "]  Jones V(t) = " + c.seal.jones_polynomial + "  鍵指紋 " + c.seal.key_fingerprint,
          "「保存」で JSON として書き出せます。"]);
      } else if (intent === "guard") {
        if (!state.cert) throw new Error("先に「証明書を作って」と入力するか、証明書 JSON を読み込んでください");
        var stages = state.base ? [state.base, state.cert] : [state.cert];
        steps.push("② 実行: 不変量 RG01〜RG11 を検査 (零点総数は再計算して照合)");
        lines = guardLines(E.guard(stages, true), stages.length);
      } else lines = HELP.slice();
    } catch (err) {
      lines = ["入力を処理できませんでした: " + err.message];
    }
    if (intent !== "help") steps.push("③ 検証: 判定は 証明完了 / 反証 / 未解決 のいずれか。未解決の予想を証明済みとは出力しない");
    return { intent: intent, steps: steps, lines: lines };
  }

  global.BadaGPTChat = { detect: detect, reply: reply, parseClaim: parseClaim, HELP: HELP, SYMBOL: SYMBOL };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaGPTChat;
})(typeof window !== "undefined" ? window : globalThis);
