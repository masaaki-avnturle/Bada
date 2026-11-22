"""CLI:  python3 -m riemann_prover.cli run --height 500 --out certificate.json"""

from __future__ import annotations

import argparse
import json

from .verify import verify_rh_to_height, schoenfeld_check
from .drh import drh_evidence, CHARACTERS
from .certificate import build_certificate, seal, check_seal, SOUNDNESS

SYMBOL = {"verified": "∎ 数値検証完了", "disproved": "✗ 反証（反例あり）",
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
    cert = seal(build_certificate(rh, sch, drh), a.braid)
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


def main(argv=None):
    p = argparse.ArgumentParser(prog="riemann_prover")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="検証を実行して証明書を出力")
    r.add_argument("--height", type=float, default=500.0, help="零点検証の高さ T")
    r.add_argument("--psi-limit", type=int, default=10 ** 6, help="Schoenfeld 不等式の検査上限")
    r.add_argument("--primes", type=int, default=10 ** 6, help="DRH オイラー積の素数上限")
    r.add_argument("--braid", type=int, nargs="+", default=[1, 1, 1], help="封印に使う組みひも")
    r.add_argument("--out", help="証明書 JSON の出力先")
    r.set_defaults(fn=cmd_run)
    c = sub.add_parser("check", help="証明書の封印を検査")
    c.add_argument("file")
    c.add_argument("--braid", type=int, nargs="+")
    c.set_defaults(fn=cmd_check)
    a = p.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    raise SystemExit(main())
