/*
 * lab.js — BadaClaude の「証明ラボ」: ネイティブ組込み (JavaScript 側)
 *
 * brain.bada / lab.bada から呼ばれる道具を Bada 処理系に登録します。
 *   lab_prove(text)            未知事前エンジン: 数値検証・帰納法・量子探索 (BadaGPT エンジン)
 *   lab_spec(text)             「Σ f(k) = g(n)」を帰納法で判定し、コード生成用の仕様にする
 *   lab_emit(spec, lang, opt)  仕様から厳密化されたソースコードを生成 (規則は lab.bada のリバイザが決める)
 *   lab_paper(spec) / lab_report(topic)   証明の論文 / 未解決問題の計算的証拠の報告 (Markdown + LaTeX)
 *   jones_encrypt / jones_decrypt / lab_seal   Jones 多項式量子暗号
 *
 * 健全性: 未解決の予想を「証明済み」とする論文もコードも生成しない。
 */
(function (global) {
  "use strict";
  var E = global.BadaGPTEngine || (typeof require !== "undefined" ? require("../../bada_gpt/src/engine.js") : null);
  var Chat = global.BadaGPTChat || (typeof require !== "undefined" ? require("../../bada_gpt/src/chat.js") : null);
  var PL = E.poly;

  /* ───────────── 仕様 (spec): 証明済みの和の公式 ───────────── */
  function gcd(a, b) { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) { var t = a % b; a = b; b = t; } return a; }
  function intForm(p) {                     // 有理係数の多項式 → 整数係数 P と共通分母 D
    var D = 1n;
    p.forEach(function (c) { D = D * c.d / gcd(D, c.d); });
    return { P: p.map(function (c) { return c.n * (D / c.d); }), D: D };
  }
  function evalInt(P, n) { var acc = 0n; for (var i = P.length - 1; i >= 0; i--) acc = acc * n + P[i]; return acc; }
  function absSum(P, n) { var acc = 0n; for (var i = P.length - 1; i >= 0; i--) acc = acc * n + (P[i] < 0n ? -P[i] : P[i]); return acc; }
  // 中間値がすべて limit 未満に収まる最大の n (厳密な BigInt 計算)
  function safeBound(P, F, limit, cap) {
    var ok = function (n) { var N = BigInt(n); return absSum(P, N) < limit && absSum(F, N) * (N + 1n) < limit; };
    if (!ok(0)) return -1;
    var lo = 0, hi = cap;
    if (ok(hi)) return hi;
    while (hi - lo > 1) { var mid = (lo + hi) >> 1; if (ok(mid)) lo = mid; else hi = mid; }
    return lo;
  }

  function makeSpec(text) {
    var claim;
    try { claim = Chat.parseClaim(text); } catch (e) { return { ok: false, error: e.message }; }
    return specFromPolys(claim.f, claim.g);
  }
  function specFromPolys(f, g) {
    var original = E.proveSum(f, g), proof = original, repaired = null;
    if (original.status !== "proved") { repaired = E.repairSum(f, g); proof = repaired.repaired; }
    var fp = PL.make(proof.f), gp = PL.make(proof.g);
    var fi = intForm(fp), gi = intForm(gp);
    var step = PL.shift(gp), stepDiff = PL.add(step, gp, -1), fNext = PL.shift(fp);
    return {
      ok: true, claim: proof.claim, status: proof.status, f: proof.f, g: proof.g, steps: proof.steps,
      original_status: original.status, original_claim: original.claim,
      counterexample: original.status === "disproved" ? original.steps[0] : null,
      drift_before: repaired ? repaired.drift_before : "0", drift_after: repaired ? repaired.drift_after : "0",
      f_integer: fi.D === 1n,
      P: (gi.P.length ? gi.P : [0n]).map(String), D: String(gi.D), F: (fi.P.length ? fi.P : [0n]).map(String),
      g_next_minus_g: E.pStr(stepDiff), f_next: E.pStr(fNext),
      tex: { f: polyTex(fp, "k"), g: polyTex(gp, "n"), g_next: polyTex(step, "n"), diff: polyTex(stepDiff, "n"), f_next: polyTex(fNext, "n") }
    };
  }

  function polyTex(p, v) {
    if (!p.length) return "0";
    var out = "";
    for (var i = p.length - 1; i >= 0; i--) {
      var c = p[i]; if (c.n === 0n) continue;
      var neg = c.n < 0n, n = neg ? -c.n : c.n;
      var mag = c.d === 1n ? String(n) : "\\frac{" + n + "}{" + c.d + "}";
      var mono = i === 0 ? "" : i === 1 ? v : v + "^{" + i + "}";
      if (mono && c.d === 1n && n === 1n) mag = "";
      out += (out ? (neg ? " - " : " + ") : (neg ? "-" : "")) + mag + (mag && mono && c.d === 1n ? "\\," : "") + mono;
    }
    return out;
  }

  /* ───────────── 厳密化されたソースコードの生成 ───────────── */
  var I64 = 1n << 63n, I128 = 1n << 127n, F53 = 1n << 53n;
  // 各言語の発行器。r = { P, D, F (BigInt 配列), limit, claim, strict } → ソース文字列
  var EMIT = {
    python: function (r) {
      return ['"""' + r.header.join("\n") + '"""', "",
        "P = [" + r.P.join(", ") + "]   # g(n) = (Σ P[i]·n^i) / D", "D = " + r.D, "F = [" + r.F.join(", ") + "]   # f(k) = Σ F[i]·k^i", "", "",
        "def _horner(coeffs: list[int], x: int) -> int:", "    acc = 0", "    for c in reversed(coeffs):", "        acc = acc * x + c", "    return acc", "", "",
        "def closed(n: int) -> int:", '    """閉形式 g(n)。Python の int は任意精度なので桁あふれしない。"""',
        "    if not isinstance(n, int) or isinstance(n, bool) or n < 0:", '        raise ValueError("n must be a non-negative integer")',
        "    q, rem = divmod(_horner(P, n), D)", "    if rem != 0:", '        raise ArithmeticError("exact division failed")', "    return q", "", "",
        "def reference(n: int) -> int:", '    """定義どおりの和 Σ_{k=1}^{n} f(k)。"""',
        "    if not isinstance(n, int) or isinstance(n, bool) or n < 0:", '        raise ValueError("n must be a non-negative integer")',
        "    return sum(_horner(F, k) for k in range(1, n + 1))", "", "",
        "def self_test(limit: int = " + r.limit + ") -> None:", "    for n in range(limit + 1):", "        if closed(n) != reference(n):",
        '            raise AssertionError(f"mismatch at n = {n}")', "", "", 'if __name__ == "__main__":', "    self_test()", '    print("OK", closed(' + r.limit + "))", ""].join("\n");
    },
    javascript: function (r) {
      return ["/*", r.header.join("\n"), "*/", '"use strict";',
        "const P = [" + r.P.map(function (c) { return c + "n"; }).join(", ") + "];   // g(n) = (Σ P[i]·n^i) / D", "const D = " + r.D + "n;",
        "const F = [" + r.F.map(function (c) { return c + "n"; }).join(", ") + "];   // f(k) = Σ F[i]·k^i", "",
        "function horner(coeffs, x) {", "  let acc = 0n;", "  for (let i = coeffs.length - 1; i >= 0; i--) acc = acc * x + coeffs[i];", "  return acc;", "}", "",
        "/** 閉形式 g(n)。BigInt なので桁あふれしない。n は非負の BigInt。 */", "function closed(n) {",
        '  if (typeof n !== "bigint" || n < 0n) throw new RangeError("n must be a non-negative BigInt");', "  const v = horner(P, n);",
        '  if (v % D !== 0n) throw new Error("exact division failed");', "  return v / D;", "}", "",
        "/** 定義どおりの和 Σ_{k=1}^{n} f(k)。 */", "function reference(n) {",
        '  if (typeof n !== "bigint" || n < 0n) throw new RangeError("n must be a non-negative BigInt");',
        "  let s = 0n;", "  for (let k = 1n; k <= n; k++) s += horner(F, k);", "  return s;", "}", "",
        "function selfTest(limit = " + r.limit + "n) {", "  for (let n = 0n; n <= limit; n++) {",
        '    if (closed(n) !== reference(n)) throw new Error("mismatch at n = " + n);', "  }", "}", "",
        "selfTest();", 'console.log("OK " + closed(' + r.limit + "n));", 'if (typeof module !== "undefined") module.exports = { closed, reference, selfTest };', ""].join("\n");
    },
    ruby: function (r) {
      return ["# frozen_string_literal: true", r.header.map(function (l) { return "# " + l; }).join("\n"), "",
        "P = [" + r.P.join(", ") + "].freeze   # g(n) = (Σ P[i]·n^i) / D", "D = " + r.D, "F = [" + r.F.join(", ") + "].freeze   # f(k) = Σ F[i]·k^i", "",
        "def horner(coeffs, x)", "  coeffs.reverse.reduce(0) { |acc, c| acc * x + c }", "end", "",
        "# 閉形式 g(n)。Ruby の Integer は任意精度なので桁あふれしない。", "def closed(n)",
        '  raise ArgumentError, "n must be a non-negative Integer" unless n.is_a?(Integer) && n >= 0', "  q, rem = horner(P, n).divmod(D)",
        '  raise ZeroDivisionError, "exact division failed" unless rem.zero?', "  q", "end", "",
        "# 定義どおりの和 Σ_{k=1}^{n} f(k)。", "def reference(n)",
        '  raise ArgumentError, "n must be a non-negative Integer" unless n.is_a?(Integer) && n >= 0', "  (1..n).sum { |k| horner(F, k) }", "end", "",
        "def self_test(limit = " + r.limit + ")", "  (0..limit).each do |n|", '    raise "mismatch at n = #{n}" unless closed(n) == reference(n)', "  end", "end", "",
        "if $PROGRAM_NAME == __FILE__", "  self_test", '  puts "OK #{closed(' + r.limit + ')}"', "end", ""].join("\n");
    },
    java: function (r) {
      var arr = function (a) { return "{" + a.map(function (c) { return 'new BigInteger("' + c + '")'; }).join(", ") + "}"; };
      return ["/*", r.header.join("\n"), "*/", "import java.math.BigInteger;", "", "public final class RigorSum {",
        "    private static final BigInteger[] P = " + arr(r.P) + ";   // g(n) = (Σ P[i]·n^i) / D",
        '    private static final BigInteger D = new BigInteger("' + r.D + '");',
        "    private static final BigInteger[] F = " + arr(r.F) + ";   // f(k) = Σ F[i]·k^i", "", "    private RigorSum() {}", "",
        "    private static BigInteger horner(BigInteger[] coeffs, BigInteger x) {", "        BigInteger acc = BigInteger.ZERO;",
        "        for (int i = coeffs.length - 1; i >= 0; i--) acc = acc.multiply(x).add(coeffs[i]);", "        return acc;", "    }", "",
        "    /** 閉形式 g(n)。BigInteger なので桁あふれしない。 */", "    public static BigInteger closed(BigInteger n) {",
        '        if (n == null || n.signum() < 0) throw new IllegalArgumentException("n must be a non-negative integer");',
        "        BigInteger[] qr = horner(P, n).divideAndRemainder(D);",
        '        if (qr[1].signum() != 0) throw new ArithmeticException("exact division failed");', "        return qr[0];", "    }", "",
        "    /** 定義どおりの和 Σ_{k=1}^{n} f(k)。 */", "    public static BigInteger reference(BigInteger n) {",
        '        if (n == null || n.signum() < 0) throw new IllegalArgumentException("n must be a non-negative integer");',
        "        BigInteger s = BigInteger.ZERO;", "        for (BigInteger k = BigInteger.ONE; k.compareTo(n) <= 0; k = k.add(BigInteger.ONE)) s = s.add(horner(F, k));",
        "        return s;", "    }", "", "    public static void main(String[] args) {", "        for (long n = 0; n <= " + r.limit + "L; n++) {",
        "            BigInteger b = BigInteger.valueOf(n);",
        '            if (!closed(b).equals(reference(b))) throw new AssertionError("mismatch at n = " + n);', "        }",
        '        System.out.println("OK " + closed(BigInteger.valueOf(' + r.limit + "L)));", "    }", "}", ""].join("\n");
    },
    go: function (r) {
      var arr = function (a) { return "[]string{" + a.map(function (c) { return '"' + c + '"'; }).join(", ") + "}"; };
      return ["/*", r.header.join("\n"), "*/", "package main", "", "import (", '\t"errors"', '\t"fmt"', '\t"math/big"', '\t"os"', ")", "",
        "var (", "\tcoefP = mustInts(" + arr(r.P) + ") // g(n) = (Σ P[i]·n^i) / D", '\tdenD  = mustInts([]string{"' + r.D + '"})[0]',
        "\tcoefF = mustInts(" + arr(r.F) + ") // f(k) = Σ F[i]·k^i", ")", "",
        "func mustInts(ss []string) []*big.Int {", "\tout := make([]*big.Int, len(ss))", "\tfor i, s := range ss {", "\t\tv, ok := new(big.Int).SetString(s, 10)",
        "\t\tif !ok {", '\t\t\tpanic("bad coefficient " + s)', "\t\t}", "\t\tout[i] = v", "\t}", "\treturn out", "}", "",
        "func horner(coeffs []*big.Int, x *big.Int) *big.Int {", "\tacc := new(big.Int)", "\tfor i := len(coeffs) - 1; i >= 0; i-- {",
        "\t\tacc.Mul(acc, x)", "\t\tacc.Add(acc, coeffs[i])", "\t}", "\treturn acc", "}", "",
        "// Closed は閉形式 g(n)。math/big なので桁あふれしない。", "func Closed(n *big.Int) (*big.Int, error) {", "\tif n == nil || n.Sign() < 0 {",
        '\t\treturn nil, errors.New("n must be a non-negative integer")', "\t}", "\tq, rem := new(big.Int).QuoRem(horner(coefP, n), denD, new(big.Int))",
        "\tif rem.Sign() != 0 {", '\t\treturn nil, errors.New("exact division failed")', "\t}", "\treturn q, nil", "}", "",
        "// Reference は定義どおりの和 Σ_{k=1}^{n} f(k)。", "func Reference(n *big.Int) (*big.Int, error) {", "\tif n == nil || n.Sign() < 0 {",
        '\t\treturn nil, errors.New("n must be a non-negative integer")', "\t}", "\ts := new(big.Int)", "\tone := big.NewInt(1)",
        "\tfor k := big.NewInt(1); k.Cmp(n) <= 0; k.Add(k, one) {", "\t\ts.Add(s, horner(coefF, k))", "\t}", "\treturn s, nil", "}", "",
        "func main() {", "\tfor n := int64(0); n <= " + r.limit + "; n++ {", "\t\tb := big.NewInt(n)", "\t\tc, err1 := Closed(b)", "\t\tr, err2 := Reference(b)",
        "\t\tif err1 != nil || err2 != nil || c.Cmp(r) != 0 {", '\t\t\tfmt.Println("FAIL", n)', "\t\t\tos.Exit(1)", "\t\t}", "\t}",
        "\tv, _ := Closed(big.NewInt(" + r.limit + "))", '\tfmt.Println("OK", v)', "}", ""].join("\n");
    },
    rust: function (r) {
      return [r.header.map(function (l) { return "// " + l; }).join("\n"), "",
        "const P: [i128; " + r.P.length + "] = [" + r.P.join(", ") + "]; // g(n) = (Σ P[i]·n^i) / D", "const D: i128 = " + r.D + ";",
        "const F: [i128; " + r.F.length + "] = [" + r.F.join(", ") + "]; // f(k) = Σ F[i]·k^i", "",
        "#[derive(Debug, PartialEq, Eq)]", "pub enum RigorError {", "    Negative,", "    Overflow,", "    InexactDivision,", "}", "",
        "fn horner(coeffs: &[i128], x: i128) -> Result<i128, RigorError> {", "    let mut acc: i128 = 0;", "    for &c in coeffs.iter().rev() {",
        "        acc = acc.checked_mul(x).and_then(|v| v.checked_add(c)).ok_or(RigorError::Overflow)?;", "    }", "    Ok(acc)", "}", "",
        "/// 閉形式 g(n)。すべての演算を checked_* で行い、桁あふれは Err(Overflow) で返す。", "pub fn closed(n: i128) -> Result<i128, RigorError> {",
        "    if n < 0 {", "        return Err(RigorError::Negative);", "    }", "    let v = horner(&P, n)?;", "    if v % D != 0 {",
        "        return Err(RigorError::InexactDivision);", "    }", "    Ok(v / D)", "}", "",
        "/// 定義どおりの和 Σ_{k=1}^{n} f(k)。", "pub fn reference(n: i128) -> Result<i128, RigorError> {", "    if n < 0 {", "        return Err(RigorError::Negative);", "    }",
        "    let mut s: i128 = 0;", "    let mut k: i128 = 1;", "    while k <= n {", "        s = s.checked_add(horner(&F, k)?).ok_or(RigorError::Overflow)?;", "        k += 1;", "    }", "    Ok(s)", "}", "",
        "fn main() {", "    for n in 0..=" + r.limit + "_i128 {", "        match (closed(n), reference(n)) {", "            (Ok(a), Ok(b)) if a == b => {}",
        "            other => {", '                println!("FAIL {} {:?}", n, other);', "                std::process::exit(1);", "            }", "        }", "    }",
        '    println!("OK {}", closed(' + r.limit + ").unwrap());", "}", ""].join("\n");
    },
    c: function (r) {
      var lit = function (c) { return "INT64_C(" + c + ")"; };
      return ["/*", r.header.join("\n"), "*/", "#include <inttypes.h>", "#include <stdint.h>", "#include <stdio.h>", "",
        "static const int64_t P[] = {" + r.P.map(lit).join(", ") + "}; /* g(n) = (sum P[i] n^i) / D */", "static const int64_t D = " + lit(r.D) + ";",
        "static const int64_t F[] = {" + r.F.map(lit).join(", ") + "}; /* f(k) = sum F[i] k^i */", "#define LEN(a) ((int)(sizeof(a) / sizeof((a)[0])))", "",
        "/* 桁あふれを検出したら 0 を返す (未定義動作に入らない)。 */", "static int horner(const int64_t *coeffs, int len, int64_t x, int64_t *out) {", "    int64_t acc = 0;",
        "    for (int i = len - 1; i >= 0; i--) {", "        if (__builtin_mul_overflow(acc, x, &acc) || __builtin_add_overflow(acc, coeffs[i], &acc)) return 0;", "    }",
        "    *out = acc;", "    return 1;", "}", "",
        "/* 閉形式 g(n)。成功で 1、n < 0・桁あふれ・割り切れない場合は 0。 */", "int closed(int64_t n, int64_t *out) {", "    int64_t v;",
        "    if (n < 0 || !horner(P, LEN(P), n, &v) || v % D != 0) return 0;", "    *out = v / D;", "    return 1;", "}", "",
        "/* 定義どおりの和。成功で 1、桁あふれで 0。 */", "int reference(int64_t n, int64_t *out) {", "    int64_t s = 0, t;", "    if (n < 0) return 0;",
        "    for (int64_t k = 1; k <= n; k++) {", "        if (!horner(F, LEN(F), k, &t) || __builtin_add_overflow(s, t, &s)) return 0;", "    }", "    *out = s;", "    return 1;", "}", "",
        "int main(void) {", "    int64_t a, b;", "    for (int64_t n = 0; n <= " + lit(r.limit) + "; n++) {", "        if (!closed(n, &a) || !reference(n, &b) || a != b) {",
        '            printf("FAIL %" PRId64 "\\n", n);', "            return 1;", "        }", "    }", "    if (!closed(" + lit(r.limit) + ", &a)) return 1;",
        '    printf("OK %" PRId64 "\\n", a);', "    return 0;", "}", ""].join("\n");
    },
    bada: function (r) {
      return [r.header.map(function (l) { return "# " + l; }).join("\n"), "",
        "P := [" + r.P.join(", ") + "]   # g(n) = (Σ P[i]·n^i) / D", "D := " + r.D, "F := [" + r.F.join(", ") + "]   # f(k) = Σ F[i]·k^i",
        "NMAX := " + r.nmax + "   # この範囲では中間値がすべて 2^53 未満 (倍精度で厳密)", "",
        "fn horner(coeffs, x) {", "  acc := 0", "  i := len(coeffs) - 1", "  while i >= 0 {", "    acc = acc * x + coeffs[i]", "    i = i - 1", "  }", "  return acc", "}", "",
        "# 閉形式 g(n)。範囲外の n には nil を返す (誤った値を返さない)。", "fn closed(n) {", "  if n < 0 or n > NMAX or int(n) != n { return nil }", "  v := horner(P, n)",
        "  if v % D != 0 { return nil }", "  return v / D", "}", "",
        "# 定義どおりの和 Σ_{k=1}^{n} f(k)。", "fn reference(n) {", "  if n < 0 or n > NMAX or int(n) != n { return nil }", "  s := 0", "  k := 1",
        "  while k <= n {", "    s = s + horner(F, k)", "    k = k + 1", "  }", "  return s", "}", "",
        "fn self_test(limit) {", "  n := 0", "  while n <= limit {", "    if closed(n) != reference(n) { return n }", "    n = n + 1", "  }", "  return -1", "}", "",
        "bad := self_test(" + r.limit + ")", 'if bad == -1 { print("OK " + str(closed(' + r.limit + "))) } else { print(\"FAIL \" + str(bad)) }", ""].join("\n");
    }
  };
  var FILES = { python: "rigor_sum.py", javascript: "rigor_sum.js", ruby: "rigor_sum.rb", java: "RigorSum.java", go: "rigor_sum.go",
                rust: "rigor_sum.rs", c: "rigor_sum.c", bada: "rigor_sum.bada" };

  // opt = { overflow: "bigint" | "checked64" | "checked128" | "bound53", selftest: N, notes: [..] } — lab.bada のリバイザ規則から渡される
  function emit(spec, lang, opt) {
    if (!EMIT[lang]) return { ok: false, lang: lang, error: "未対応の言語です: " + lang };
    if (!spec || !spec.ok || spec.status !== "proved") return { ok: false, lang: lang, error: "証明済みの仕様がありません" };
    if (!spec.f_integer) return { ok: false, lang: lang, error: "f の係数が整数でないため、整数演算だけの厳密なコードにできません" };
    opt = opt || {};
    var P = spec.P.map(BigInt), F = spec.F.map(BigInt), D = BigInt(spec.D), N = Math.max(1, Math.min(+opt.selftest || 200, 2000));
    var mode = opt.overflow || "bigint", lim = mode === "checked64" ? I64 : mode === "checked128" ? I128 : mode === "bound53" ? F53 : null;
    var nmax = N;
    if (lim) {
      var fits = P.concat(F, [D]).every(function (c) { return (c < 0n ? -c : c) < lim; });
      nmax = fits ? safeBound(P, F, lim, 1000000) : -1;
      if (nmax < 1) return { ok: false, lang: lang, error: "係数が " + mode + " の範囲に収まりません" };
    }
    var limit = Math.min(N, nmax), expected = evalInt(P, BigInt(limit)) / D;
    var header = ["厳密化されたソースコード — BadaClaude のリバイザ (@reviser RIGOR) が生成",
      "定理 (数学的帰納法で証明済み): " + spec.claim, "厳密化規則: 桁あふれ = " + mode + " / 割り算 = 余り 0 を検査 / 入力 = n ≥ 0 を検査 / 自己検査 = n ≤ " + limit]
      .concat((opt.notes || []).map(function (s) { return "  - " + s; }));
    var code = EMIT[lang]({ P: P.map(String), F: F.map(String), D: String(D), limit: String(limit), nmax: String(lim ? nmax : limit), header: header });
    return { ok: true, lang: lang, file: FILES[lang], code: code, limit: limit, nmax: lim ? nmax : null, overflow: mode, expected: "OK " + expected };
  }

  /* ───────────── 論文 (Markdown + LaTeX) ───────────── */
  function sealText(text, braid) {
    braid = braid && braid.length ? braid.map(Number) : [1, 1, 1];
    var key = E.braidKey(braid), digest = E.sha256(text);
    return { braid: braid, jones: E.jonesStr(braid), fingerprint: E.fingerprint(key), sha256: E.hex(digest), sealed: E.hex(E.jonesEncrypt(key, digest)) };
  }
  function checkSealText(text, seal) {
    try { return E.hex(E.jonesDecrypt(E.braidKey(seal.braid), E.unhex(seal.sealed))) === E.hex(E.sha256(text)); } catch (e) { return false; }
  }
  function texEsc(s) { return String(s).replace(/([#$%&_{}])/g, "\\$1").replace(/\^/g, "\\^{}").replace(/~/g, "\\~{}"); }
  function texDoc(title, body) {
    return ["\\documentclass[11pt]{article}", "\\usepackage{amsmath,amssymb,amsthm}", "% 日本語の本文は LuaLaTeX + luatexja でコンパイルしてください", "\\usepackage{luatexja}",
      "\\newtheorem{theorem}{定理}", "\\newtheorem{conjecture}{予想}", "\\newtheorem{lemma}{補題}", "\\title{" + title + "}", "\\author{BadaClaude (未知事前エンジン)}", "\\date{\\today}",
      "\\begin{document}", "\\maketitle", body, "\\end{document}", ""].join("\n");
  }

  function paper(spec, code) {
    if (!spec || !spec.ok) return { ok: false, error: (spec && spec.error) || "主張がありません" };
    var t = spec.tex, repaired = spec.original_status !== "proved";
    var title = "和の公式 Σ f(k) = g(n) の数学的帰納法による証明";
    var md = ["# 定理: " + spec.claim, "", "**生成**: BadaClaude 未知事前エンジン · **判定**: ∎ 証明完了 (QED) · **手法**: 数学的帰納法 (厳密な有理数演算で機械検査)", "",
      "## 1. 主張", "", "すべての整数 $n \\ge 0$ について", "", "$$\\sum_{k=1}^{n} \\left(" + t.f + "\\right) = " + t.g + ".$$", ""];
    if (repaired) md = md.concat(["### 元の主張とその修正", "", "入力された主張 `" + spec.original_claim + "` は**誤り**です (" + spec.counterexample + ")。",
      "保存量 $I(n) = g(n) - \\sum_{k \\le n} f(k)$ のドリフト (帰納の段の残差) は `" + spec.drift_before + "` でした。",
      "$I \\equiv 0$ の等位集合へ射影して閉形式を修正し (ドリフト `" + spec.drift_after + "`)、修正後の式を以下で証明します。", ""]);
    md = md.concat(["## 2. 証明", "", "$g(n) = " + t.g + "$、$f(k) = " + t.f + "$ とおき、$S(n) = \\sum_{k=1}^{n} f(k)$ と書く。", "",
      "**基底.** $g(0) = 0$ であり、空和 $S(0) = 0$ に一致する。", "",
      "**帰納の段.** $S(n) = g(n)$ を仮定する。$S(n+1) = S(n) + f(n+1) = g(n) + f(n+1)$ なので、$g(n+1) - g(n) = f(n+1)$ を示せばよい。展開すると", "",
      "$$g(n+1) = " + t.g_next + ",$$", "", "$$g(n+1) - g(n) = " + t.diff + ", \\qquad f(n+1) = " + t.f_next + ".$$", "",
      "両辺は多項式として係数ごとに一致する。よって $S(n+1) = g(n+1)$。", "", "数学的帰納法により、すべての $n \\ge 0$ で $S(n) = g(n)$ が成り立つ。 $\\blacksquare$", "",
      "## 3. 機械検査", "", "- 基底 $g(0) = 0$ と、残差多項式 $g(n+1) - g(n) - f(n+1)$ の全係数が 0 であることを、BigInt による有理数の厳密演算で確認した。",
      "- 浮動小数点は使っていない。多項式の恒等式なので、この検査は有限個の係数比較で完結する (健全)。", ""]);
    if (code && code.ok) md = md.concat(["## 4. 付録: 証明から生成した厳密なコード (" + code.lang + ")", "",
      "証明済みの閉形式を整数演算だけで評価し、定義どおりの和と $n \\le " + code.limit + "$ で照合する。実行すると `" + code.expected + "` を出力する。", "", "```" + code.lang, code.code + "```", ""]);
    md = md.concat(["## 健全性に関する注記", "", "本稿が証明するのは上の多項式恒等式だけである。リーマン予想などの未解決問題については何も主張しない。"]);
    var body = ["\\begin{theorem}", "すべての整数 $n \\ge 0$ について", "\\[ \\sum_{k=1}^{n} \\left(" + t.f + "\\right) = " + t.g + ". \\]", "\\end{theorem}",
      repaired ? "\\paragraph{元の主張の修正} 入力された主張は誤りであった (" + texEsc(spec.counterexample) + ")。保存量 $I(n) = g(n) - \\sum_{k \\le n} f(k)$ の等位集合 $I \\equiv 0$ へ射影して閉形式を修正した。" : "",
      "\\begin{proof}", "$g(n) = " + t.g + "$, $f(k) = " + t.f + "$, $S(n) = \\sum_{k=1}^{n} f(k)$ とおく。",
      "\\emph{基底.} $g(0) = 0 = S(0)$。", "\\emph{帰納の段.} $S(n) = g(n)$ を仮定すると $S(n+1) = g(n) + f(n+1)$。一方",
      "\\[ g(n+1) - g(n) = " + t.diff + " = f(n+1) \\]", "が多項式として成り立つので $S(n+1) = g(n+1)$。数学的帰納法により主張が従う。", "\\end{proof}",
      "\\paragraph{機械検査} 基底と残差多項式 $g(n+1) - g(n) - f(n+1) \\equiv 0$ を有理数の厳密演算で確認した。",
      "\\paragraph{健全性} 本稿が証明するのは上の多項式恒等式だけであり、未解決問題については何も主張しない。"].filter(Boolean).join("\n");
    return finish(title, md.join("\n"), texDoc(title, body), "proved");
  }

  var TOPICS = {
    rh: { name: "リーマン予想", statement: "$\\zeta(s)$ の非自明な零点はすべて $\\operatorname{Re} s = 1/2$ 上にある。" },
    drh: { name: "深リーマン予想", statement: "非自明な Dirichlet 指標 $\\chi$ に対し、$\\operatorname{Re} s = 1/2$ 上で $\\prod_{p \\le x}(1 - \\chi(p)p^{-s})^{-1}$ が $x \\to \\infty$ で収束する。" },
    collatz: { name: "コラッツ予想", statement: "すべての $n \\ge 1$ は $n \\mapsto n/2$ ($n$ 偶数), $3n+1$ ($n$ 奇数) の反復で 1 に到達する。" },
    goldbach: { name: "ゴールドバッハ予想", statement: "4 以上のすべての偶数は 2 つの素数の和である。" },
    legendre: { name: "ルジャンドル予想", statement: "すべての $n \\ge 1$ について $n^2$ と $(n+1)^2$ の間に素数がある。" }
  };
  var PROMPT = { rh: "リーマン予想を高さ 500 まで調べて", drh: "深リーマン予想の証拠", collatz: "コラッツ予想を 12 ビットで",
                 goldbach: "ゴールドバッハ予想を 10 量子ビットで", legendre: "ルジャンドル予想を 10 量子ビットで" };
  // 未解決問題: 「証明」ではなく「計算的証拠の報告」しか出さない
  function report(topic) {
    var T = TOPICS[topic];
    if (!T) return { ok: false, error: "対象が分かりません。帰納法で示せる和の公式 (例: Σ k^2 = n(n+1)(2n+1)/6) か、リーマン予想・深リーマン予想・コラッツ予想・ゴールドバッハ予想・ルジャンドル予想を指定してください" };
    var r = Chat.reply(PROMPT[topic], {}), title = T.name + "に関する計算的証拠の報告 (証明ではない)";
    var md = ["# " + title, "", "**生成**: BadaClaude 未知事前エンジン · **判定**: ? 未解決 (経験的証拠のみ)", "",
      "> **本稿は" + T.name + "の証明ではない。** " + T.name + "は未解決問題であり、以下は有限範囲の計算結果の記録である。", "",
      "## 1. 予想", "", T.statement, "", "## 2. 計算結果", "", "```", r.lines.join("\n"), "```", "",
      "## 3. この結果から言えること・言えないこと", "", "- 言えること: 上に記した有限の範囲では、予想に反する事例が見つからなかった (または記載の補題が成り立つ)。",
      "- 言えないこと: 範囲の外については何も分からない。有限の検証をいくら積み重ねても、すべての場合についての主張の証明にはならない。",
      "- 数値は倍精度浮動小数点によるもので、区間演算による厳密な評価ではない (整数だけの計算を除く)。", "",
      "## 4. 証明に必要なもの", "", "範囲に依存しない論証 (解析的な評価、あるいは無限降下が閉じる構造) が必要であり、本エンジンはそれを持たない。"].join("\n");
    var body = ["\\begin{conjecture}[" + T.name + "]", T.statement, "\\end{conjecture}", "\\paragraph{注意} 本稿は証明ではない。" + T.name + "は未解決であり、以下は有限範囲の計算結果の記録である。",
      "\\begin{verbatim}", r.lines.join("\n"), "\\end{verbatim}", "\\paragraph{限界} 有限の検証は、すべての場合についての主張の証明にならない。"].join("\n");
    return finish(title, md, texDoc(title, body), "open");
  }
  function finish(title, md, tex, status) {
    var seal = sealText(md);
    md += "\n\n---\n封印 (Jones 多項式量子暗号): 組みひも [" + seal.braid + "] · V(t) = " + seal.jones + " · 鍵指紋 " + seal.fingerprint + " · SHA-256 " + seal.sha256.slice(0, 16) + "…";
    return { ok: true, title: title, status: status, md: md, tex: tex, seal: seal };
  }

  /* ───────────── Bada 処理系への登録 ───────────── */
  function install(I) {
    var state = {}, def = function (name, fn) { fn.bname = name; I.global.def(name, fn); };
    var braidOf = function (v) { var b = (Array.isArray(v) ? v : []).map(Number).filter(function (x) { return Number.isInteger(x) && x !== 0 && Math.abs(x) <= 8; }); return b.length ? b.slice(0, 12) : [1, 1, 1]; };
    def("lab_intent", function (a) { return Chat.detect(String(a[0])); });
    def("lab_prove", function (a) {
      var r = Chat.reply(String(a[0]), state);
      return { intent: r.intent, steps: r.steps, lines: r.lines, has_cert: !!state.cert };
    });
    def("lab_spec", function (a) { return makeSpec(String(a[0])); });
    def("lab_emit", function (a) { return emit(a[0], String(a[1]), a[2] || {}); });
    def("lab_paper", function (a) { return paper(a[0], a[1]); });
    def("lab_report", function (a) { return report(String(a[0])); });
    def("lab_seal", function (a) { return sealText(String(a[0]), braidOf(a[1])); });
    def("lab_check_seal", function (a) { return checkSealText(String(a[0]), a[1]); });
    def("jones_encrypt", function (a) {
      var braid = braidOf(a[0]), key = E.braidKey(braid);
      return { braid: braid, jones: E.jonesStr(braid), fingerprint: E.fingerprint(key), hex: E.hex(E.jonesEncrypt(key, E.utf8(String(a[1])))) };
    });
    def("jones_decrypt", function (a) {
      try {
        var hx = String(a[1]).replace(/\s+/g, "");
        if (!/^([0-9a-f]{2}){49,}$/i.test(hx)) return { ok: false, error: "暗号文は 16 進文字列で指定してください" };
        return { ok: true, text: new TextDecoder().decode(E.jonesDecrypt(E.braidKey(braidOf(a[0])), E.unhex(hx.toLowerCase()))) };
      } catch (e) { return { ok: false, error: "復号できません。組みひも (鍵) が違うか、暗号文が改ざんされています" }; }
    });
    return state;
  }

  global.BadaLab = { install: install, makeSpec: makeSpec, emit: emit, paper: paper, report: report, sealText: sealText, checkSealText: checkSealText, FILES: FILES };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaLab;
})(typeof window !== "undefined" ? window : globalThis);
