"""demo.py — 重複リスクの検出例. `python examples/demo.py`"""
from omega_medsafe import check, format_report

print(format_report(check([
    "フルニトラゼパム", "エチゾラム", "ブロチゾラム",
    "アムロジピン", "カンデサルタン", "セレネース", "リスパダール", "アメル",
])))
