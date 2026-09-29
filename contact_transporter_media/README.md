# contact_transporter_media

`contact_blueprint.pdf`（Bada: contact_transporter の生成レポート）を解析し、
**映画『コンタクト』の異次元輸送機** と **ChatGPT** の 2 つについて、
「方程式 → 部品 → 平面図 → 3D → 組み立て → 使用」の順に描いた動画 (mp4) と設計図 PDF を生成します。

## 成果物 (`output/`)

| ファイル | 内容 |
|---|---|
| `contact_transporter.mp4` | 輸送機の動画 (1280×720, 30fps, 約 112 秒, 音声付き) |
| `contact_transporter_blueprint.pdf` | 輸送機の設計図 9 葉 (パラメータ・部品↔方程式対応表・三面図・3D 等角図・分解組立図・動作シーケンス・方程式抜粋) |
| `chatgpt_blueprint.mp4` | ChatGPT (GPT 系 Transformer) の動画 (約 106 秒, 音声付き) |
| `chatgpt_blueprint.pdf` | ChatGPT の設計図 7 葉 (パラメータ・部品↔方程式対応表・ブロック図/立面図・3D/分解組立図・推論フロー) |

## 動画の構成

1. 設計パラメータ（レポート 1 章の Bada 実行結果）
2. 方程式 → 部品への対応（輸送機: 全 2111 本を先頭タグで 8 部品へ／ChatGPT: 18 本を 10 部品へ）
3. 平面図（三面図／ブロック図・立面図）を描き進める
4. 平面図 → 3D 変換（z を 0 から方程式由来の実寸へ持ち上げ、視点を 90°→20° に回転）
5. 組み立て（部品ごとに支配方程式カードを表示しながら所定位置へ）
6. 使用（輸送機: ポッド降下 → 環の回転 → 共鳴 → n̂ 方向へ輸送、地球時間 1 s = 搭乗者 18 h／
   ChatGPT: プロンプト → トークン → 各層の注意 → softmax → 次トークン生成）

## 数値の根拠と検算

- 輸送機の寸法・角速度・Jones 値はすべて `contact_blueprint.pdf` の値。
  θ(φ) = −2.58136, Z(φ) = −1.33415, V_K(t*) は mpmath で再計算しレポートと一致。
- 共鳴窓の角度は |V_K(e^{iα})| の極小から算出。
- 方程式レジストリ（2111 本）は `data/equations.json` に抽出済み。
- ChatGPT 実機の内部構成は非公開のため、GPT-3 論文の公開値を参照した図解モデル。
  注意行列は小型のランダム初期化モデルで `softmax(QKᵀ/√d + M)` を実計算した例、生成候補の確率は例示値。

> ※ 輸送機は論文の方程式に基づく思索的・フィクションの設計図（幾何的な可視化）であり、
> 工学的に検証された装置ではなく、異次元への輸送を可能にするものではありません。

## 再生成

```sh
pip install numpy matplotlib mpmath imageio-ffmpeg pillow
python3 transporter_video.py   # output/contact_transporter.mp4
python3 chatgpt_video.py       # output/chatgpt_blueprint.mp4
python3 blueprint_pdf.py       # output/*.pdf
```
