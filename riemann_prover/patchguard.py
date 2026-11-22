"""証明書の書き換えを守る門 — BadaPatchGuard の仕組みを証明書に適用したもの。

BadaPatchGuard (bada_patchguard/, ブランチ ccr-fd691112-eo2fdo) は PHP サイトの
「書き換えの基」と「書き換えた後」を SHA-256 で内容アドレス化してタプル台帳に置き、
その差 (パッチ) を不変量で検査して ACCEPT / REVIEW / REJECT を決める。
ここでは同じ手順を検証証明書に対して行う。守る性質は「計算で裏付けられていない
主張への書き換えを通さない」こと — とくに未解決の予想を「証明済み」に書き換える
パッチは必ず REJECT になる。

  ["cert",  run, k, sha]                         各段の証明書
  ["patch", run, k, sha_base, sha_after, 変更数]   隣り合う段の差
  ["finding", run, 段, id, 重大度, 説明]            不変量の違反
  ["gate",  run, 判定]                            正味 (基 → 最終) の判定
"""

from __future__ import annotations

import hashlib
import json

from .certificate import SOUNDNESS, check_seal

SEVERITY = {"critical": 3, "high": 2, "medium": 1, "low": 0}


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def flatten(obj, prefix="") -> dict:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}/{k}"))
        return out
    if isinstance(obj, list):
        out = {}
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}/{i}"))
        return out
    return {prefix: obj}


def diff(base: dict, after: dict) -> dict:
    """{path: (old, new)} — the patch between two certificates."""
    a, b = flatten(base), flatten(after)
    return {p: (a.get(p), b.get(p)) for p in sorted(set(a) | set(b)) if a.get(p) != b.get(p)}


def _get(d, *path, default=None):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return default
        d = d[p]
    return d


def _f(fid, sev, why):
    return {"id": fid, "severity": sev, "why": why}


def invariants(base: dict | None, cert: dict, recompute: bool = False) -> list[dict]:
    """Findings for one certificate (and for the rewrite base → cert, if base is given)."""
    out = []
    for key, name in (("riemann_hypothesis", "リーマン予想"),
                      ("deep_riemann_hypothesis", "深リーマン予想")):
        v = _get(cert, "verdicts", key)
        if v != "open":
            out.append(_f("RG01", "critical",
                          f"{name}の判定が {v!r}。検査可能な証明なしに未解決以外へは書き換えられない"))
    rh = cert.get("rh_bounded", {})
    if rh.get("status") == "verified" or _get(cert, "verdicts", "rh_up_to_height") == "verified":
        n = rh.get("zeros_in_strip_argument_principle")
        m = rh.get("zeros_on_critical_line_sign_changes")
        if n is None or n != m or not rh.get("argument_principle_residual", 1) < 1e-3:
            out.append(_f("RG02", "critical",
                          f"高さ {rh.get('height')} まで検証済みとあるが、零点総数 {n} と線上の個数 {m} が裏付けない"))
        elif recompute:
            from .verify import zero_count
            got, _ = zero_count(float(rh["height"]))
            if got != n:
                out.append(_f("RG03", "critical",
                              f"再計算した N({rh['height']}) = {got} が記載の {n} と一致しない"))
    sch = cert.get("schoenfeld", {})
    if sch.get("status") == "verified" and not sch.get("max_ratio", 1) < 1:
        out.append(_f("RG04", "high", f"Schoenfeld 不等式が検証済みとあるが最大比 {sch.get('max_ratio')} が 1 以上"))
    for i, d in enumerate(cert.get("drh_evidence", [])):
        if d.get("status") != "open":
            out.append(_f("RG05", "critical",
                          f"深リーマン予想の証拠 #{i} の判定が {d.get('status')!r}。有限の部分積は証明にならない"))
    for q in cert.get("quantum_search", []):
        name, st, cx = q.get("problem"), q.get("status"), q.get("counterexample")
        if st == "disproved":
            from .qsim import PROBLEMS, is_counterexample
            if name not in PROBLEMS or cx is None or not is_counterexample(name, cx):
                out.append(_f("RG10", "critical", f"{name}: 反証とあるが、反例 {cx!r} が古典的な再検査を通らない"))
        elif st != "open":
            out.append(_f("RG10", "critical",
                          f"{name}: 判定が {st!r}。有限範囲の量子探索は予想の証明にならない"))
    for i, e in enumerate(cert.get("induction", [])):
        from .induction import recheck
        try:
            ok = recheck(e)
        except Exception:
            ok = False
        if not ok:
            out.append(_f("RG11", "critical",
                          f"帰納法の項目 #{i} ({e.get('kind')}) の判定 {e.get('status')!r} が再導出と一致しない"))
    if cert.get("soundness") != SOUNDNESS:
        out.append(_f("RG06", "high", "健全性の注記が削除または変更されている"))
    if "seal" not in cert:
        out.append(_f("RG07", "medium", "Jones 暗号による封印がない"))
    elif not check_seal(cert):
        out.append(_f("RG07", "high", "封印が内容と一致しない（封印後に書き換えられている）"))
    if base is not None:
        for label, path in (("零点検証の高さ", ("rh_bounded", "height")),
                            ("Schoenfeld 検査の上限", ("schoenfeld", "limit"))):
            old, new = _get(base, *path), _get(cert, *path)
            if old is not None and (new is None or new < old):
                out.append(_f("RG08", "medium", f"{label}が {old} から {new} へ縮小している"))
        if len(cert.get("drh_evidence", [])) < len(base.get("drh_evidence", [])):
            out.append(_f("RG09", "medium", "深リーマン予想の証拠が削除されている"))
    return out


def gate(findings: list[dict]) -> str:
    worst = max((SEVERITY[f["severity"]] for f in findings), default=-1)
    return "REJECT" if worst >= 2 else "REVIEW" if worst == 1 else "ACCEPT"


def check(stages: list[dict], recompute: bool = False) -> dict:
    """stages = [基, 後1, 後2, …]（1 つだけなら単体検査）。複数回の書き換えは折り畳み、
    正味の 基 → 最終 で判定する。各段の指摘は監査用に残す。"""
    run = sha(stages)[:12]
    tuples = [["cert", run, k, sha(c)] for k, c in enumerate(stages)]
    per_stage = []
    for k in range(1, len(stages)):
        patch = diff(stages[k - 1], stages[k])
        tuples.append(["patch", run, k, sha(stages[k - 1]), sha(stages[k]), len(patch)])
        per_stage.append(invariants(stages[k - 1], stages[k]))
    base = stages[0] if len(stages) > 1 else None
    net = invariants(base, stages[-1], recompute)
    net_ids = {(f["id"], f["why"]) for f in net}
    cancelled = [f for fs in per_stage[:-1] for f in fs if (f["id"], f["why"]) not in net_ids]
    for f in net:
        tuples.append(["finding", run, "net", f["id"], f["severity"], f["why"]])
    for f in cancelled:
        tuples.append(["finding", run, "cancelled", f["id"], f["severity"], f["why"]])
    verdict = gate(net)
    tuples.append(["gate", run, verdict])
    return {
        "run": run,
        "verdict": verdict,
        "findings": net,
        "cancelled": cancelled,
        "net_patch": {p: list(v) for p, v in diff(base, stages[-1]).items()} if base else {},
        "tuples": tuples,
    }
