"""
drug_classes.py — 薬効クラスとリスクタグの辞書
===============================================

薬剤名を **薬効クラス** と **リスクタグ** に対応づける。用量・配合比・製造法は
一切扱わない。本モジュールが答えるのは「この薬とこの薬は、同じ種類の負担を
体にかけるか？」という一点のみである。

⚠️ 教育目的の参考情報であり、医療上の助言ではない。実際の判断は必ず
   主治医・薬剤師に相談すること。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


# --------------------------------------------------------------------------- #
#  リスクタグ（重複すると相加的に危険が増す作用）
# --------------------------------------------------------------------------- #
RISK_LABELS: Dict[str, str] = {
    "CNS_DEPRESSION": "中枢神経抑制（眠気・意識レベル低下）",
    "RESPIRATORY_DEPRESSION": "呼吸抑制（呼吸が浅く・遅くなる）",
    "HYPOTENSION": "血圧低下（ふらつき・失神）",
    "QT_PROLONGATION": "QT延長（重篤な不整脈）",
    "EPS_NMS": "錐体外路症状・悪性症候群",
    "ANTICHOLINERGIC": "抗コリン作用（口渇・便秘・尿閉・せん妄）",
    "FALL_RISK": "転倒リスク（特に高齢者）",
    "DEPENDENCE": "依存・耐性形成、急な中断による離脱症状",
    "SEROTONERGIC": "セロトニン症候群",
    "BLEEDING": "出血傾向",
    "HYPERKALEMIA": "高カリウム血症",
    "RENAL": "腎機能への負担",
}

# 重複時に特に危険度が高いタグ
CRITICAL_TAGS = {"RESPIRATORY_DEPRESSION", "QT_PROLONGATION", "SEROTONERGIC"}


@dataclass(frozen=True)
class DrugClass:
    """薬効クラス。individual な用量情報は持たない。"""

    name: str                      # クラス名（日本語）
    risks: tuple                   # リスクタグ
    note: str = ""


CLASSES: Dict[str, DrugClass] = {
    "benzodiazepine": DrugClass(
        "ベンゾジアゼピン系（抗不安・催眠）",
        ("CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "FALL_RISK", "DEPENDENCE"),
        "アルコールや他の中枢抑制薬との併用で呼吸抑制が相加的に強まる。",
    ),
    "thienodiazepine": DrugClass(
        "チエノジアゼピン系（抗不安・催眠）",
        ("CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "FALL_RISK", "DEPENDENCE"),
        "薬理学的にベンゾジアゼピン系とほぼ同じ働き方をする。",
    ),
    "z_drug": DrugClass(
        "非ベンゾジアゼピン系睡眠薬（Z薬）",
        ("CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "FALL_RISK", "DEPENDENCE"),
    ),
    "antipsychotic_typical": DrugClass(
        "定型抗精神病薬",
        ("CNS_DEPRESSION", "QT_PROLONGATION", "EPS_NMS", "HYPOTENSION",
         "ANTICHOLINERGIC", "FALL_RISK"),
        "QT延長・悪性症候群のリスクがあり、定期的なモニタリングを要する。",
    ),
    "antipsychotic_atypical": DrugClass(
        "非定型抗精神病薬",
        ("CNS_DEPRESSION", "QT_PROLONGATION", "EPS_NMS", "HYPOTENSION",
         "FALL_RISK"),
    ),
    "ccb_dihydropyridine": DrugClass(
        "カルシウム拮抗薬（ジヒドロピリジン系・降圧）",
        ("HYPOTENSION", "FALL_RISK"),
        "グレープフルーツジュースで血中濃度が上がることがある。",
    ),
    "arb": DrugClass(
        "アンジオテンシンII受容体拮抗薬（ARB・降圧）",
        ("HYPOTENSION", "HYPERKALEMIA", "RENAL"),
    ),
    "acei": DrugClass(
        "ACE阻害薬（降圧）",
        ("HYPOTENSION", "HYPERKALEMIA", "RENAL"),
    ),
    "diuretic": DrugClass(
        "利尿薬",
        ("HYPOTENSION", "RENAL", "FALL_RISK"),
    ),
    "beta_blocker": DrugClass(
        "β遮断薬",
        ("HYPOTENSION", "FALL_RISK"),
    ),
    "ssri": DrugClass(
        "SSRI（抗うつ）",
        ("SEROTONERGIC", "BLEEDING"),
    ),
    "snri": DrugClass(
        "SNRI（抗うつ）",
        ("SEROTONERGIC", "BLEEDING"),
    ),
    "tricyclic": DrugClass(
        "三環系抗うつ薬",
        ("CNS_DEPRESSION", "ANTICHOLINERGIC", "QT_PROLONGATION",
         "SEROTONERGIC", "FALL_RISK"),
    ),
    "opioid": DrugClass(
        "オピオイド系鎮痛薬",
        ("CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "DEPENDENCE", "FALL_RISK"),
    ),
    "antihistamine_1st": DrugClass(
        "第一世代抗ヒスタミン薬",
        ("CNS_DEPRESSION", "ANTICHOLINERGIC", "FALL_RISK"),
    ),
    "mood_stabilizer": DrugClass(
        "気分安定薬",
        ("CNS_DEPRESSION", "RENAL"),
    ),
    "anticoagulant": DrugClass(
        "抗凝固薬",
        ("BLEEDING",),
    ),
    "alcohol": DrugClass(
        "アルコール",
        ("CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "FALL_RISK", "DEPENDENCE"),
        "薬剤ではないが、中枢抑制薬との併用は特に危険。",
    ),
}


# --------------------------------------------------------------------------- #
#  薬剤名 → クラス（一般名・代表的な商品名・カタカナ表記）
# --------------------------------------------------------------------------- #
DRUG_TO_CLASS: Dict[str, str] = {
    # ベンゾジアゼピン系
    "フルニトラゼパム": "benzodiazepine",
    "サイレース": "benzodiazepine",
    "ジアゼパム": "benzodiazepine",
    "セルシン": "benzodiazepine",
    "ロラゼパム": "benzodiazepine",
    "ワイパックス": "benzodiazepine",
    "アルプラゾラム": "benzodiazepine",
    "ソラナックス": "benzodiazepine",
    "トリアゾラム": "benzodiazepine",
    "ハルシオン": "benzodiazepine",
    "ニトラゼパム": "benzodiazepine",
    "クロナゼパム": "benzodiazepine",
    # チエノジアゼピン系
    "エチゾラム": "thienodiazepine",
    "デパス": "thienodiazepine",
    "ブロチゾラム": "thienodiazepine",
    "レンドルミン": "thienodiazepine",
    # Z薬
    "ゾルピデム": "z_drug",
    "マイスリー": "z_drug",
    "エスゾピクロン": "z_drug",
    "ルネスタ": "z_drug",
    "ゾピクロン": "z_drug",
    # 抗精神病薬
    "ハロペリドール": "antipsychotic_typical",
    "セレネース": "antipsychotic_typical",
    "クロルプロマジン": "antipsychotic_typical",
    "リスペリドン": "antipsychotic_atypical",
    "リスパダール": "antipsychotic_atypical",
    "オランザピン": "antipsychotic_atypical",
    "ジプレキサ": "antipsychotic_atypical",
    "クエチアピン": "antipsychotic_atypical",
    "アリピプラゾール": "antipsychotic_atypical",
    "エビリファイ": "antipsychotic_atypical",
    # 降圧薬
    "アムロジピン": "ccb_dihydropyridine",
    "アムロジン": "ccb_dihydropyridine",
    "ノルバスク": "ccb_dihydropyridine",
    "ニフェジピン": "ccb_dihydropyridine",
    "カンデサルタン": "arb",
    "ブロプレス": "arb",
    "ロサルタン": "arb",
    "バルサルタン": "arb",
    "テルミサルタン": "arb",
    "エナラプリル": "acei",
    "フロセミド": "diuretic",
    "ラシックス": "diuretic",
    "カルベジロール": "beta_blocker",
    "ビソプロロール": "beta_blocker",
    # 抗うつ薬
    "セルトラリン": "ssri",
    "ジェイゾロフト": "ssri",
    "エスシタロプラム": "ssri",
    "レクサプロ": "ssri",
    "パロキセチン": "ssri",
    "パキシル": "ssri",
    "デュロキセチン": "snri",
    "サインバルタ": "snri",
    "アミトリプチリン": "tricyclic",
    # その他
    "トラマドール": "opioid",
    "コデイン": "opioid",
    "モルヒネ": "opioid",
    "ジフェンヒドラミン": "antihistamine_1st",
    "炭酸リチウム": "mood_stabilizer",
    "ワルファリン": "anticoagulant",
    "アルコール": "alcohol",
    "飲酒": "alcohol",
}

# 薬剤名ではなく後発品のブランド接尾辞（例: リスペリドン錠「アメル」）
BRAND_SUFFIXES: Dict[str, str] = {
    "アメル": "共和薬品工業のジェネリック医薬品ブランド名です。"
              "薬剤そのものの名前ではないため、"
              "「リスペリドン錠〈アメル〉」のように前についている一般名で調べてください。",
    "サワイ": "沢井製薬のジェネリック医薬品ブランド名です（薬剤名ではありません）。",
    "トーワ": "東和薬品のジェネリック医薬品ブランド名です（薬剤名ではありません）。",
    "日医工": "日医工のジェネリック医薬品ブランド名です（薬剤名ではありません）。",
}


def normalize(name: str) -> str:
    """全角スペース・記号を落として照合しやすくする。"""
    return name.strip().strip("「」〈〉（）()錠 　").replace(" ", "")


def lookup(name: str):
    """
    薬剤名からクラスを引く。
    戻り値: (kind, payload)
      ("class", DrugClass)   — クラスが判明
      ("brand", str)         — ブランド接尾辞（薬剤名ではない）の説明
      ("unknown", None)      — 辞書にない
    """
    key = normalize(name)
    if key in DRUG_TO_CLASS:
        return "class", CLASSES[DRUG_TO_CLASS[key]]
    if key in BRAND_SUFFIXES:
        return "brand", BRAND_SUFFIXES[key]
    return "unknown", None
