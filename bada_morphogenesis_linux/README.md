# Bada Morphogenesis — Linux native (ELF)

`bada_morphogenesis_app`（Android / Kotlin + Compose）のシミュレーション・コアを、
**Linux のネイティブ実行ファイル（ELF）**として動く C アプリに移植したものです。
APK が要らず、ターミナルで直接動きます。

> ⚠️ これは数学シミュレーションです。実在の細胞培養プロトコル・医薬品・物理装置
> （反重力等）ではありません。パラメータと出力はすべて例示用です。

## 移植したコア
- **MorphMath** — Thom のカスプ・カタストロフィ ポテンシャル V(x)=x⁴/4+a·x²/2+b·x、
  三次方程式の実根ソルバ（三角関数法 / カルダノ）、双安定判定
- **Bada protocol DSL** — `.bada` プロトコル言語のインタプリタ（5プロトコル同梱）
- **ReactionDiffusion** — 円形容器上の Gray-Scott 反応拡散 → Turing 型の形態形成場
  （ASCII 描画）、分化フラクション
- **LineageTree** — iPS 分化の確率的分岐＋細胞集団モデル
- **DrugBatch** — 製造シミュレーション指標（収率・純度・生存率・力価・規格判定）

## ビルド

```bash
make                 # → bin/bada_morphogenesis
make run

# または Gradle（リポジトリ共通の assembleDebug）
./gradlew assembleDebug
#   または ルートから: ./gradlew :bada_morphogenesis_linux:assembleDebug
```

## 使い方

```bash
./bin/bada_morphogenesis              # インタラクティブ・メニュー（5プロトコル）
./bin/bada_morphogenesis --list
./bin/bada_morphogenesis cardio       # 心筋分化シミュレーションを実行
./bin/bada_morphogenesis --grid 96 --steps 4000 beta   # 高解像度・長時間
```

各プロトコルで、カタストロフィ平衡点、Gray-Scott 形態形成場（ASCII）、分化系譜樹、
細胞集団、製造シミュレーション指標を表示します。プロトコル定義は Android アプリと
同じ `lineages.bada`（5個）を同梱しています。
