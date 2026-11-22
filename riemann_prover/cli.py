"""CLI:  python3 -m riemann_prover.cli run --height 500 --out certificate.json"""

from __future__ import annotations

import argparse
import json

from .verify import verify_rh_to_height, schoenfeld_check
from .drh import drh_evidence, CHARACTERS
from .certificate import build_certificate, seal, check_seal, SOUNDNESS

SYMBOL = {"proved": "∎ 証明完了 (QED)", "verified": "∎ 数値検証完了", "disproved": "✗ 反証（反例あり）",
          "open": "? 未解決（経験的証拠のみ）", "inconclusive": "… 判定不能"}


def render(cert: dict) -> str:
    rh, sch = cert["rh_bounded"], cert["schoenfeld"]
    out = ["── リーマン予想 / 深リーマン予想 検証エンジン ──", ""]
    out += [f"【命題1】{rh['claim']}",
            f"  判定: {SYMBOL[rh['status']]}",
            f"    偏角の原理による零点総数 N(T) = {rh['zeros_in_strip_argument_principle']}"
            f"  (整数からのずれ {rh['argument_principle_residual']:.2e})",
            f"    臨界線上の符号変化の個数   = {rh['zeros_on_critical_line_sign_changes']}",
            f"    最初の零点: {', '.join(f'{z:.6f}' for z in rh['first_zeros'])}", ""]
    out += [f"【命題2】(RH と同値な Schoenfeld 不等式の有限部分) {sch['claim']}",
            f"  判定: {SYMBOL[sch['status']]}",
            f"    最大比 = {sch['max_ratio']:.4f} (x = {sch['max_ratio_at']})  ※ 1 未満なら成立", ""]
    for i, d in enumerate(cert["drh_evidence"], 3):
        out += [f"【命題{i}】(深リーマン予想) {d['claim']}",
                f"  判定: {SYMBOL[d['status']]}",
                f"    L(s,χ) = {d['L'][0]:.9f}{d['L'][1]:+.9f}i"
                + ("   極限は √2·L(s,χ)" if d["sqrt2_factor"] else ""),
                "    x          DRH極限との相対誤差   素のL(s,χ)との相対誤差"]
        out += [f"    {r['x']:<10d} {r['rel_error_vs_DRH_limit']:<21.6f} {r['rel_error_vs_plain_L']:.6f}"
                for r in d["table"]]
        out.append("")
    for q in cert.get("quantum_search", []):
        out += [f"【量子探索】{q['title']}: {q['statement']}",
                f"  擬似量子コンピュータ {q['qubits']} 量子ビット, n = {q['range'][0]}〜{q['range'][1]}, "
                f"Grover 反復 {q['iterations']} 回, 反例の観測確率 {q['success_probability']:.4f}",
                (f"  判定: {SYMBOL['disproved']}  反例 n = {q['counterexample']}"
                 f"（範囲内の反例 {q['counterexamples_in_range']} 個、古典的に再検査済み）"
                 if q["status"] == "disproved" else
                 f"  判定: {SYMBOL['open']}  この範囲に反例なし（全数検査）"
                 if q["bounded_status"] == "verified" else
                 f"  判定: {SYMBOL['inconclusive']}  {q['shots']} 回の測定で反例を観測できず"), ""]
    for e in cert.get("induction", []):
        k = e["kind"]
        if k == "sum_identity":
            out += [f"【帰納法】{e['claim']}", f"  判定: {SYMBOL[e['status']]}"] + [f"    {x}" for x in e["steps"]] + [""]
        elif k == "repair":
            o, r = e["original"], e["repaired"]
            out += [f"【帰納法＋修正】{o['claim']}",
                    f"  元の主張: {SYMBOL[o['status']]}  {o['steps'][0]}",
                    f"  保存量のドリフト: {e['drift_before']}  →  {e['drift_after']}",
                    f"  修正後: {r['claim']}", f"  判定: {SYMBOL[r['status']]}", ""]
        elif k == "collatz_descent":
            out += [f"【補集合の解析】{e['claim']}",
                    f"  判定: {SYMBOL[e['status']]}  （手法: {e['method']}）",
                    f"    剰余類の {e['excluded_fraction'] * 100:.2f}% を最小反例の候補から除外。"
                    f"コラッツ予想そのものは {SYMBOL['open']}", ""]
        else:
            out += [f"【帰納法の限界】{e['problem']}: {e['note']}", ""]
    out += ["【リーマン予想】      判定: " + SYMBOL["open"],
            "【深リーマン予想】    判定: " + SYMBOL["open"], "",
            "※ " + SOUNDNESS]
    if "seal" in cert:
        s = cert["seal"]
        out += ["", f"封印: 組みひも {s['braid']}  Jones V(t) = {s['jones_polynomial']}"
                    f"  鍵指紋 {s['key_fingerprint']}"]
    return "\n".join(out)


def cmd_run(a):
    rh = verify_rh_to_height(a.height)
    sch = schoenfeld_check(a.psi_limit)
    drh = [drh_evidence(name, 0.0, a.primes) for name in CHARACTERS]
    drh.append(drh_evidence("chi_-4", 1.0, a.primes))
    from .qsim import quantum_search_all
    from .induction import induction_report
    cert = seal(build_certificate(rh, sch, drh, quantum_search_all(a.qubits, a.seed),
                                  induction_report(a.sieve_bits)), a.braid)
    print(render(cert))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(cert, f, ensure_ascii=False, indent=2)
        print(f"\n証明書を保存: {a.out}")


def cmd_check(a):
    with open(a.file, encoding="utf-8") as f:
        cert = json.load(f)
    ok = check_seal(cert, a.braid)
    print("封印: 有効（改ざんなし）" if ok else "封印: 無効（改ざん、または組みひもが違う）")
    return 0 if ok else 1


def cmd_guard(a):
    from .patchguard import check
    stages = []
    for path in a.files:
        with open(path, encoding="utf-8") as f:
            stages.append(json.load(f))
    rep = check(stages, recompute=a.recompute)
    print(f"── 証明書 PatchGuard ──  段数 {len(stages)}  変更 {len(rep['net_patch'])} 箇所")
    for f in rep["findings"]:
        print(f"  [{f['severity']}] {f['id']} {f['why']}")
    for f in rep["cancelled"]:
        print(f"  (相殺) {f['id']} {f['why']}")
    print(f"判定: {rep['verdict']}")
    if a.out:
        with open(a.out, "a", encoding="utf-8") as f:
            for t in rep["tuples"]:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
    return {"ACCEPT": 0, "REVIEW": 1, "REJECT": 2}[rep["verdict"]]


def cmd_induct(a):
    from .induction import prove_sum, repair_sum
    res = prove_sum(a.f, a.g)
    print(f"主張: {res['claim']}\n判定: {SYMBOL[res['status']]}")
    for x in res["steps"]:
        print("  " + x)
    if res["status"] == "disproved":
        rep = repair_sum(a.f, a.g)
        print(f"保存量のドリフト: {rep['drift_before']}  →  {rep['drift_after']}")
        print(f"修正後: {rep['repaired']['claim']}\n判定: {SYMBOL[rep['status']]}")
    return 0 if res["status"] == "proved" else 2


def main(argv=None):
    p = argparse.ArgumentParser(prog="riemann_prover")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="検証を実行して証明書を出力")
    r.add_argument("--height", type=float, default=500.0, help="零点検証の高さ T")
    r.add_argument("--psi-limit", type=int, default=10 ** 6, help="Schoenfeld 不等式の検査上限")
    r.add_argument("--primes", type=int, default=10 ** 6, help="DRH オイラー積の素数上限")
    r.add_argument("--braid", type=int, nargs="+", default=[1, 1, 1], help="封印に使う組みひも")
    r.add_argument("--qubits", type=int, default=10, help="擬似量子コンピュータの量子ビット数")
    r.add_argument("--sieve-bits", type=int, default=12, help="コラッツ降下ふるいの法 2^k の k")
    r.add_argument("--seed", type=int, default=0, help="測定の乱数種")
    r.add_argument("--out", help="証明書 JSON の出力先")
    r.set_defaults(fn=cmd_run)
    c = sub.add_parser("check", help="証明書の封印を検査")
    c.add_argument("file")
    c.add_argument("--braid", type=int, nargs="+")
    c.set_defaults(fn=cmd_check)
    g = sub.add_parser("guard", help="証明書（またはその書き換え 基→後…）を門で検査")
    g.add_argument("files", nargs="+", help="証明書 JSON。複数なら時系列で折り畳む")
    g.add_argument("--recompute", action="store_true", help="零点総数 N(T) を再計算して照合")
    g.add_argument("--out", help="タプル台帳 (JSONL, 追記) の出力先")
    g.set_defaults(fn=cmd_guard)
    i = sub.add_parser("induct", help="Σ f(k) = g(n) を帰納法で判定し、誤っていれば修正")
    i.add_argument("--f", nargs="+", required=True, help="f の係数 (低次から。例: 0 0 1 は k²)")
    i.add_argument("--g", nargs="+", required=True, help="g の係数 (低次から。分数可: 1/6)")
    i.set_defaults(fn=cmd_induct)
    a = p.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    raise SystemExit(main())
