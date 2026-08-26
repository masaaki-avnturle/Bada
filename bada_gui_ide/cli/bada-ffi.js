/*
 * bada-ffi.js — @reviser : extension のホスト側 FFI ブリッジ (Node.js)
 *
 * Bada の拡張トランザクション
 *     @reviser : extension <lang> { fun NAME |params| """code""" }
 * で宣言された python / java / c 拡張を、サブプロセスとして実行します。
 * (lang=bada はインタープリタ内で完結するためここには来ません)
 *
 * 呼び出し規約 (bada.js の makeFfiNative と対):
 *   - 各引数は JSON 文字列 1 個 = プロセス引数 1 個
 *   - stdout を trim し、JSON として読めれば値に、読めなければ文字列に
 *
 * 言語ごとのコード規約:
 *   python — code は ARGS (JSON デコード済みリスト) を読み、RESULT に代入
 *   c      — code は  double NAME(double p1, ...)  の関数本体 (数値のみ)
 *   java   — code は  static double run(double[] args)  の本体 (数値のみ)
 *
 * C / Java はソースのハッシュでキャッシュし、同じ拡張の再コンパイルを避けます。
 */
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");
const { spawnSync } = require("child_process");

const CACHE = path.join(os.tmpdir(), "bada-ext-cache");
const COMPILE_TIMEOUT = 60000;
const RUN_TIMEOUT = 30000;

function sha(s) { return crypto.createHash("sha1").update(s).digest("hex").slice(0, 16); }

function firstAvailable(cands, probeArgs) {
  for (const c of cands) {
    const r = spawnSync(c, probeArgs, { encoding: "utf8", timeout: 10000 });
    if (r.status === 0) return c;
  }
  return null;
}

let PY = undefined, GCC = undefined, JAVAC = undefined, JAVA = undefined;
function python() { if (PY === undefined) PY = firstAvailable(["python3", "python"], ["--version"]); return PY; }
function gcc() { if (GCC === undefined) GCC = firstAvailable(["gcc", "cc", "clang"], ["--version"]); return GCC; }
function javac() { if (JAVAC === undefined) JAVAC = firstAvailable(["javac"], ["-version"]); return JAVAC; }
function java() { if (JAVA === undefined) JAVA = firstAvailable(["java"], ["-version"]); return JAVA; }

function run(cmd, args, timeout) {
  const r = spawnSync(cmd, args, { encoding: "utf8", timeout: timeout || RUN_TIMEOUT });
  if (r.error) return { ok: false, stdout: "", error: String(r.error.message || r.error) };
  if (r.status !== 0) return { ok: false, stdout: r.stdout || "", error: (r.stderr || "exit " + r.status).trim() };
  return { ok: true, stdout: r.stdout || "", error: null };
}

function ffiPython(name, code, params, argv) {
  const py = python();
  if (!py) return { ok: false, stdout: "", error: "python3 が見つかりません" };
  const wrapper =
    "import sys, json\n" +
    "ARGS = [json.loads(a) for a in sys.argv[1:]]\n" +
    "RESULT = None\n" +
    code + "\n" +
    "if RESULT is not None:\n" +
    "    print(json.dumps(RESULT))\n";
  return run(py, ["-c", wrapper, ...argv]);
}

function ffiC(name, code, params, argv) {
  const cc = gcc();
  if (!cc) return { ok: false, stdout: "", error: "gcc/cc/clang が見つかりません (Ubuntu: sudo apt install build-essential / Windows: MinGW-w64)" };
  fs.mkdirSync(CACHE, { recursive: true });
  const id = "bx_" + sha("c|" + name + "|" + params.join(",") + "|" + code);
  const exe = path.join(CACHE, id + (process.platform === "win32" ? ".exe" : ""));
  if (!fs.existsSync(exe)) {
    const sig = params.length ? params.map((p) => "double " + p).join(", ") : "void";
    const call = params.map((_, i) => "a[" + i + "]").join(", ");
    const src =
      "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n" +
      "static double " + name + "(" + sig + ") {\n" + code + "\n}\n" +
      "int main(int argc, char** argv) {\n" +
      "  double a[16]; memset(a, 0, sizeof a);\n" +
      "  for (int i = 1; i < argc && i <= 16; i++) a[i-1] = atof(argv[i]);\n" +
      "  (void)argc; (void)argv;\n" +
      "  printf(\"%.17g\\n\", " + name + "(" + call + "));\n" +
      "  return 0;\n}\n";
    const cfile = path.join(CACHE, id + ".c");
    fs.writeFileSync(cfile, src);
    const b = spawnSync(cc, ["-O2", "-o", exe, cfile, "-lm"], { encoding: "utf8", timeout: COMPILE_TIMEOUT });
    if (b.status !== 0) return { ok: false, stdout: "", error: "C 拡張のコンパイル失敗:\n" + (b.stderr || "") };
  }
  return run(exe, argv);
}

function ffiJava(name, code, params, argv) {
  const jc = javac(), jv = java();
  if (!jc || !jv) return { ok: false, stdout: "", error: "JDK (javac/java) が見つかりません" };
  fs.mkdirSync(CACHE, { recursive: true });
  const id = "j_" + sha("java|" + name + "|" + params.join(",") + "|" + code);
  const dir = path.join(CACHE, id);
  const cls = path.join(dir, "BadaExt.class");
  if (!fs.existsSync(cls)) {
    fs.mkdirSync(dir, { recursive: true });
    const src =
      "public class BadaExt {\n" +
      "  static double run(double[] args) {\n" + code + "\n  }\n" +
      "  public static void main(String[] argv) {\n" +
      "    double[] a = new double[Math.max(argv.length, 16)];\n" +
      "    for (int i = 0; i < argv.length; i++) { try { a[i] = Double.parseDouble(argv[i]); } catch (Exception e) { a[i] = 0; } }\n" +
      "    double r = run(a);\n" +
      "    if (r == Math.rint(r) && !Double.isInfinite(r)) System.out.println((long) r);\n" +
      "    else System.out.println(r);\n" +
      "  }\n}\n";
    const jfile = path.join(dir, "BadaExt.java");
    fs.writeFileSync(jfile, src);
    const b = spawnSync(jc, ["-d", dir, jfile], { encoding: "utf8", timeout: COMPILE_TIMEOUT });
    if (b.status !== 0) return { ok: false, stdout: "", error: "Java 拡張のコンパイル失敗:\n" + (b.stderr || "") };
  }
  return run(jv, ["-cp", dir, "BadaExt", ...argv]);
}

/* ffi(lang, name, code, params, argv) -> {ok, stdout, error} */
function ffi(lang, name, code, params, argv) {
  try {
    if (lang === "python" || lang === "python3" || lang === "py") return ffiPython(name, code, params, argv);
    if (lang === "c") return ffiC(name, code, params, argv);
    if (lang === "java") return ffiJava(name, code, params, argv);
    return { ok: false, stdout: "", error: "未対応の拡張言語: " + lang + " (bada / c / python / java)" };
  } catch (e) {
    return { ok: false, stdout: "", error: String(e && e.message ? e.message : e) };
  }
}

module.exports = { ffi };
