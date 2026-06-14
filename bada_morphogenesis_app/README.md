# Bada Morphogenesis Lab — `bada_morphogenesis_app/`

Bada言語の `.bada` プロトコルで駆動する **発生生物学シミュレーションの Android アプリ（→APK）**。
カタストロフィ理論（Thomのカスプ）による細胞運命の **不分岐→分岐**、反応拡散系（Gray–Scott /
Turing）による **円形容器内の形態形成場**、確率的分枝による **iPS細胞の系統樹**、そして
分化結果からの **薬製造シミュレーション（収率・純度・力価・規格合否）** を収録します。

> ## ⚠️ 重要な免責事項 / Disclaimer
> - これは **数学モデルのシミュレーションと可視化** です。
> - **反重力発生器・逆流電磁気・形態形成場の「実機」ではありません。** アプリ内の「場の強さ/向き」
>   は反応拡散を駆動する抽象パラメータにすぎません。
> - **実在の細胞培養プロトコル・iPS分化手順・医薬品製造ではありません。**
> - 収率/純度/力価/規格合否などの出力は **トイモデルの参考値** で、医療・製造・品質判定の
>   根拠には使えません。

---

## 画面

| 画面 | 理論 / モデル |
|:----|:----|
| 形態形成場 (反応拡散) | Gray–Scott `∂u/∂t=Du∇²u−uv²+f(1−u)`、円形マスク、Turingパターン |
| カタストロフィ分岐 | Thom カスプ `V(x)=x⁴/4+a·x²/2+b·x`、平衡点と双安定(分岐)領域 |
| iPS細胞 分岐シミュレーション | 確率的分枝過程による系統樹 + 増殖モデルによる構成比 |
| 薬製造シミュレーション | 分化結果 → 収率/純度/生存率/力価/規格合否（シミュレーション） |

---

## Bada プロトコル DSL

`app/src/main/assets/protocols/*.bada`:

```bada
protocol "cardio" {
    label          = "心筋細胞 分化"
    target         = "心筋細胞"
    field_strength = 0.65      // 抽象的な形態形成場の強さ 0..1
    cusp_a         = -1.4      // 負ほど双安定=分岐が活発
    cusp_b         = 0.0
    branch_prob    = 0.64      // 目的細胞への分化を steer
    feed           = 0.037     // Gray–Scott feed
    kill           = 0.060     // Gray–Scott kill
    drug           = "心筋再生候補 BX-1 (シミュレーション)"
    note           = "中胚葉経由の分岐を強める設定。"
}
```

- パーサ: `lang/ProtocolInterpreter.kt`
- 数学コア（カスプ・ポテンシャル / 三次方程式の実根 / 双安定判定）: `lang/MorphMath.kt`
- 反応拡散: `sim/ReactionDiffusion.kt`
- 系統樹・増殖モデル: `sim/LineageTree.kt`
- 製造メトリクス: `sim/DrugBatch.kt`

---

## ビルド方法

### GitHub Actions（推奨）
`.github/workflows/build-morpho-apk.yml` がこのフォルダの変更で起動し、APKを成果物
`bada-morphogenesis-debug-apk` としてアップロードします。手動実行も可（workflow_dispatch）。

### ローカル
```bash
cd bada_morphogenesis_app
gradle assembleDebug        # Gradle 8.7+ / JDK 17 / Android SDK 34
# → app/build/outputs/apk/debug/app-debug.apk
```

minSdk 26 / targetSdk 34 / Kotlin 1.9.24 / Compose BOM 2024.06 / AGP 8.5.2

---

© Masaaki Yamaguchi · 山口雅旭 · Bada Language
