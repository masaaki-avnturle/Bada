# Omega-Gamma Agent

**ガンマ関数における大域的部分積分多様体を核にしたローカル・エージェント**

ガンマ関数
Γ(s) = ∫₀^∞ t^{s-1} e^{-t} dt
に部分積分（integration by parts）を施すと、大域的な漸化関係

```
Γ(s + 1) = s · Γ(s)
```

が得られます。本パッケージは、この「局所的な微小変化 dt を大域的な状態の
再帰関係へ畳み込む」構造を **状態遷移＝思考ステップの核** として実装し、
知識片への注意（attention）の重み付けに用いる小さなエージェントです。

---

## ⚠️ 正直な位置づけ（重要）

- これは **AGI ではありません**。ChatGPT のような大規模言語モデルでも
  ありません。学習済みニューラルネットも、外部 API も、クラウドも、
  ネットワーク接続も **一切使いません**。
- 実体は「完全にローカルで動く**決定論的な検索＋テンプレート応答エンジン**」です。
- 独自点は、応答候補（知識片）への注意重みを、ニューラルな softmax ではなく
  **ガンマ関数の部分積分漸化 Γ(s+1)=s·Γ(s)** から生成するところにあります。
  研究・教育・アート目的の骨組みとして作られています。

現在の科学技術では、真の意味での AGI を作る方法は確立されていません。
本リポジトリの数式的世界観を、実際に動く小さなコードとして体験できる形に
落とし込んだのが本パッケージです。

---

## インストール

```bash
cd omega_gamma_agent_pkg
pip install -e .
```

依存ライブラリはゼロ（標準ライブラリの `math` のみ）。Python 3.8+ で動きます。

## 使い方

### コマンドライン（対話）

```bash
omega-gamma-agent
# または
python -m omega_gamma_agent.cli "ガンマ関数の部分積分について教えて"
```

### Python から

```python
from omega_gamma_agent import OmegaGammaAgent

agent = OmegaGammaAgent()
print(agent.ask("ガンマ関数の部分積分と多様体について"))
print(agent.explain("これはAGI？"))   # 注意分布つきで根拠を表示
```

### 数学核を直接使う

```python
from omega_gamma_agent import GammaManifold, gamma, self_check

assert self_check()            # Γ(s+1)=s·Γ(s) の数値検証

m = GammaManifold()
m.register(1.0, "reason")
m.register(2.0, "recall")
for _ in range(3):
    m.step()                   # 部分積分漸化で全状態を前進
print(m.softmax(temperature=2.0))   # 注意分布
```

## テスト

```bash
pip install -e ".[test]"
pytest -q
```

## 構成

```
omega_gamma_agent_pkg/
├── pyproject.toml
├── README.md
├── LICENSE
├── omega_gamma_agent/
│   ├── __init__.py
│   ├── gamma_manifold.py   # Γ(s+1)=s·Γ(s) 漸化と多様体
│   ├── agent.py            # 検索＋テンプレート応答エンジン
│   └── cli.py              # 対話CLI
├── examples/
│   └── demo.py
└── tests/
    └── test_agent.py
```

## ライセンス

MIT License（リポジトリ本体に準拠）
