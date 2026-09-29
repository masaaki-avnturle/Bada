#!/usr/bin/env python3
"""conformance.py — Bada 処理系の JS 移植 (src/bada.js) が Python 本家
(bada_silent_vim/bada) と同じ結果を出すかを、リポジトリ内の全 .bada で検査する。

  python3 contact_transporter/tools/conformance.py      (リポジトリのルートで実行)
"""
import contextlib, glob, io, json, os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "bada_silent_vim"))
from bada import load_program, compile_source  # noqa: E402
from bada.vm import BadaVM  # noqa: E402

# アプリ用ライブラリ (ホスト関数) を使う contact_transporter/bada 以下は対象外
files = sorted(f for f in glob.glob("**/*.bada", recursive=True)
               if "node_modules" not in f and not f.startswith("contact_transporter/"))
ref = {}
for f in files:
    try:
        vm = BadaVM(compile_source(load_program(f)))
        with contextlib.redirect_stdout(io.StringIO()):
            vm.run()
        ref[f] = {"out": vm.output}
    except Exception as e:  # エラーになるプログラムは「両方エラー」を期待する
        ref[f] = {"err": f"{type(e).__name__}: {e}"}

js = r"""
const fs = require("fs"), path = require("path"), B = require("./contact_transporter/src/bada.js");
const ref = JSON.parse(fs.readFileSync(0, "utf8"));
function load(p, seen = new Set()) {
  p = path.resolve(p); if (seen.has(p)) return ""; seen.add(p);
  return fs.readFileSync(p, "utf8").split("\n").map((l) => { const s = l.trim();
    if (s.startsWith("#include")) return load(path.join(path.dirname(p), s.slice(8).trim().replace(/^["<]|[">]$/g, "")), seen);
    return l; }).join("\n");
}
let ok = 0, bad = 0;
for (const [f, r] of Object.entries(ref)) {
  let j; try { const vm = new B.BadaVM(); vm.load(load(f)); j = { out: vm.output }; } catch (e) { j = { err: e.message }; }
  const same = (r.err && j.err) || (!r.err && !j.err && JSON.stringify(r.out) === JSON.stringify(j.out));
  if (same) ok++; else { bad++; console.log("MISMATCH", f, JSON.stringify(r).slice(0, 200), "|", JSON.stringify(j).slice(0, 200)); }
}
console.log(`Bada conformance (Python ↔ JS): ${ok} 本一致, ${bad} 本不一致`);
process.exit(bad ? 1 : 0);
"""
p = subprocess.run(["node", "-e", js], input=json.dumps(ref), text=True)
sys.exit(p.returncode)
