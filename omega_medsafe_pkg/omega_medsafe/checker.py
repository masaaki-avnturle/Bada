"""
checker.py — 服薬リスク重複チェッカー
=====================================

薬剤名のリストを受け取り、**同じ種類の負担が重なっていないか**だけを調べる。

このモジュールが決してしないこと:
  - 用量・配合比・服用スケジュールの提案
  - 「この組み合わせなら安全」という判定
  - 薬剤の製造・合成・配合に関する情報の提供

できるのは「重なっているリスクを指摘し、相談を促す」ことだけである。
安全な組み合わせを決められるのは、あなたの状態を知っている主治医と薬剤師だけ。

⚠️ 教育目的の参考情報であり、医療上の助言ではない。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .drug_classes import (
    CLASSES, CRITICAL_TAGS, RISK_LABELS, lookup,
)


@dataclass
class Finding:
    """重複しているリスク 1 件。"""

    tag: str
    label: str
    drugs: List[str]
    severity: str          # "重大" / "注意"

    @property
    def count(self) -> int:
        return len(self.drugs)


@dataclass
class Report:
    resolved: Dict[str, str]        # 薬剤名 -> クラス名
    brand_notes: Dict[str, str]     # ブランド接尾辞への注記
    unknown: List[str]              # 辞書にない入力
    findings: List[Finding]

    @property
    def has_critical(self) -> bool:
        return any(f.severity == "重大" for f in self.findings)


def check(drug_names: List[str]) -> Report:
    """薬剤名リストのリスク重複を調べる。"""
    resolved: Dict[str, str] = {}
    brand_notes: Dict[str, str] = {}
    unknown: List[str] = []
    tag_map: Dict[str, List[str]] = {}

    for raw in drug_names:
        kind, payload = lookup(raw)
        if kind == "class":
            resolved[raw] = payload.name
            for tag in payload.risks:
                tag_map.setdefault(tag, []).append(raw)
        elif kind == "brand":
            brand_notes[raw] = payload
        else:
            unknown.append(raw)

    findings: List[Finding] = []
    for tag, drugs in tag_map.items():
        if len(drugs) < 2:
            continue          # 重複していなければ指摘しない
        severity = "重大" if (tag in CRITICAL_TAGS or len(drugs) >= 3) else "注意"
        findings.append(Finding(tag, RISK_LABELS.get(tag, tag), drugs, severity))

    # 重大 → 件数の多い順
    findings.sort(key=lambda f: (f.severity != "重大", -f.count))
    return Report(resolved, brand_notes, unknown, findings)


def format_report(report: Report) -> str:
    """人が読める形に整形する。"""
    out: List[str] = []
    out.append("=== 服薬リスク重複チェック（教育用・医療助言ではありません） ===")
    out.append("")

    if report.resolved:
        out.append("■ 判別できた薬剤と薬効クラス")
        for name, cls in report.resolved.items():
            out.append(f"  ・{name} → {cls}")
        out.append("")

    if report.brand_notes:
        out.append("■ 薬剤名ではない入力")
        for name, note in report.brand_notes.items():
            out.append(f"  ・{name}: {note}")
        out.append("")

    if report.unknown:
        out.append("■ 辞書に無く判別できなかった入力")
        out.append("  " + "、".join(report.unknown))
        out.append("  （綴りをご確認ください。判別できない薬は評価に含まれていません）")
        out.append("")

    if not report.findings:
        out.append("■ 重複しているリスクは見つかりませんでした。")
        out.append("  ただしこれは『安全』を意味しません。本ツールは薬効クラスの")
        out.append("  重なりしか見ておらず、個別の相互作用・あなたの体質・腎肝機能・")
        out.append("  併存疾患は一切考慮していません。")
    else:
        out.append("■ 重なっているリスク")
        for f in report.findings:
            mark = "🔴" if f.severity == "重大" else "🟡"
            out.append(f"  {mark} [{f.severity}] {f.label}")
            out.append(f"       該当 {f.count} 剤: " + "、".join(f.drugs))
        out.append("")
        if report.has_critical:
            out.append("  ⚠ 「重大」は、重なることで生命に関わりうる作用です。")
            out.append("    自己判断で足したり、まとめて飲んだりしないでください。")

    out.append("")
    out.append("─" * 60)
    out.append("このツールができるのは『重なりの指摘』だけです。")
    out.append("安全な組み合わせや量を決められるのは、あなたの状態を知っている")
    out.append("主治医と薬剤師だけです。お薬手帳を持って相談してください。")
    out.append("")
    out.append("眠れない・気持ちが休まらないなど、しんどさが続くときは")
    out.append("処方元に率直に伝えるのがいちばん確実です。夜間や緊急時は:")
    out.append("  よりそいホットライン 0120-279-338（24時間・無料）")
    out.append("  いのちの電話       0570-783-556")
    return "\n".join(out)


if __name__ == "__main__":
    r = check(["フルニトラゼパム", "エチゾラム", "ブロチゾラム",
               "アムロジピン", "カンデサルタン", "セレネース", "リスパダール",
               "アメル"])
    print(format_report(r))
