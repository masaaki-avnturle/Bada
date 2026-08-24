# BadaGPT — ζ-Entropy 未知事前予知エンジン

**Bada 言語 (v3 作用素環) × リーマンゼータ関数のエントロピー**による、ChatGPT 型の
「未知事前予知(a-priori prediction)」言語生成アプリ。
Android **APK**・Windows 10/11 **EXE**・Ubuntu **AppImage/deb** をビルドできます。

> ⚠ 概念シミュレーション / 研究アートです。実在の予言・医療・投資助言ではありません。
> ζ-Entropy コアは解析数論(ゼータ分布のエントロピー)を実装した**決定論的**言語生成器です。

---

## ✨ 機能

| # | 機能 | 説明 |
|:-:|:-----|:-----|
| ⓪ | **思考入力 (Silent-Talk 超え)** | 発声せずに意図を入力。Γ関数の大域的部分積分多様体 + Bada 5-qubit 量子デコード + Jones 多項式熱観察で思考記号列を復号し、信頼度が silent-talk 基準 **0.62** を超えたときのみ質問欄へ反映(`www/silent.js`)。 |
| ① | **資料を投稿(どのファイルでも可)** | 拡張子不問 — 中身のシグネチャで自動判別。`%PDF-` を検出すれば拡張子が違っても PDF として抽出、`PK` なら docx/xlsx/pptx 等の ZIP 文書として XML テキスト抽出、テキストは UTF-8/Shift_JIS を自動判定、その他バイナリも印字可能文字列を救済抽出(失敗しない)。 |
| ② | **2つの生成モード** | ・**ζ-Entropy ローカル**(完全オフライン)<br>・**Claude API + ζ-Entropy**(自分の API キーを入力) |
| ③ | **ζテレメトリ表示** | s, ζ(s), H(s)[nat/bit], 温度 τ, γ, seed をリアルタイム表示。 |
| ①′ | **変換テキストの確認/保存** | アップロードした各ファイル(PDF 含む)は自動でテキスト形式へ変換され、👁 でその場でプレビュー、⬇txt で個別に `.txt` 保存(`report.pdf` → `report.txt`)、「一括 .txt」で全ファイル連結保存ができる。 |
| ④ | **成果物をダウンロード** | 生成解答を **PDF** / .txt / .md / **単一ファイル HTML アプリ**(```html ブロックは実行可能アプリとして埋込)/ **抽出ソースコード**として端末(タブレット)に保存。ファイル名は要望の種類(paper / app / code / summary …)+ 要望ごとの一意タグで自動命名。 |

### ⓪ 思考入力の仕組み

`omega_silent_talk_pkg` のパイプラインを入力機能として移植したものです。8 種の意図
(要約 / 論文執筆 / HTML アプリ作成 / Python 実装 / 数式説明 / 英語要約 / 続きの予知 /
批判レビュー)を思考記号 0–7 に符号化し、Hadamard 干渉 + Γ/ζ 位相ゲートの 5-qubit
量子デコード(または古典 greedy 復号)で回復します。信頼度は
`0.55·path_certainty + 0.20·Jones熱意図 + 0.15·多様体質量 + 0.10·Shannon` で、
「集中した思考」は基準超え(+13%)、「雑念」は未達になります。

> ⚠ 思考入力は**概念シミュレーション**です。実際の脳計測は行わず、
> 思考信号はモード選択で生成される合成信号です(非医療・非読心)。

### 🔑 Claude API キー
- キーは**この端末の `localStorage` にのみ**保存され、送信先は **Anthropic API のみ**です。
- ブラウザ直接呼び出しのため `anthropic-dangerous-direct-browser-access` ヘッダを付与します。
- **既定モデルは Claude Fable 5 (`claude-fable-5`)** — Anthropic の最上位モデル。候補
  (`claude-fable-5` / `claude-opus-5` / `claude-sonnet-5` / `claude-haiku-4-5`)から選択、
  または自由入力で変更できます。旧既定値 `claude-sonnet-4-5` が保存されていた場合は
  自動で Fable 5 へ移行します。
- Fable 5 / Opus 5 では、安全分類器による拒否 (`stop_reason: "refusal"`) に備えて
  **サーバ側フォールバック** `fallbacks: "default"`
  (beta `server-side-fallback-2026-07-01`) を既定で有効化 — 拒否時はカテゴリに応じた
  代替モデルが自動応答し、UI に「フォールバック応答 (要求 → 実際)」と表示されます。
  代替も実行できなかった場合のみ拒否理由と推奨代替モデルをエラー表示します。
- Fable 5 は thinking 常時オンのため `thinking` パラメータは送信しません。
- キーを入力しなくても、**ローカル ζ-Entropy エンジン**だけで解答とコードを生成できます。

---

## 🧮 エンジン原理(すべて実在の解析数論)

ゼータ分布 `P(n) = n^-s / ζ(s)` のシャノンエントロピー

```
H(s) = s · (−ζ'(s)/ζ(s)) + log ζ(s)        [nat]
```

を温度 `τ` に写像し、**π-softmax**(Bada の非可換 `π(χ,x)` 作用素)で投稿コーパスから
次トークンを事前予知します。語の a-priori 重みには **Bada 中核演算子**

```
ζ(s) = β(p,q) / log x ,   β(p,q) = Γ(p)Γ(q)/Γ(p+q)
```

を用います。`γ = 0.5772156649…`(オイラー・マスケローニ定数)。

| ファイル | 役割 |
|:---------|:-----|
| `www/engine.js` | ζ-Entropy 未知事前予知エンジン本体(ζ, β, H(s), π-softmax) |
| `www/fileio.js` | PDF→テキスト抽出 / PDF 書き出し / コード抽出 |
| `www/claude.js` | Claude Messages API 連携(任意) |
| `www/index.html` | UI(自己完結・外部依存なし) |

---

## 📦 ビルド & ダウンロード

このリポジトリの GitHub Actions がビルドします。

### Actions アーティファクト(いつでも)
1. GitHub → **Actions** → **「Ω apps build (APK + Windows EXE)」**
2. **Run workflow**(`workflow_dispatch`)を実行
3. 完了後、成果物をダウンロード:
   - `omega_badagpt-android` … **`omega_badagpt-debug.apk`**
   - `omega_badagpt-windows` … **`BadaGPT-1.0.0-x64.exe`**(NSIS インストーラ + portable)

### Release に添付(タグ push 時)
```bash
git tag apps-v1.0.0
git push origin apps-v1.0.0
```
→ APK と EXE が **Releases** に自動添付され、誰でもダウンロードできます。

### ローカルで試す
```bash
# デスクトップ(Electron)
cd bio_medicine/omega_badagpt/electron && npm install && npm start

# ブラウザ
# www/index.html をそのまま開く(file:// でも動作、PDF出力・ローカル生成可)
```

---

## 🚀 使い方

1. アプリを起動
2. **① 資料を投稿**:調べたい PDF やソースコードをドロップ
3. **② 質問**を入力し、モードを選択(必要なら Claude API キーを入力)
4. **⚡ 解答を生成**
5. **④** で解答を **PDF / ソースコード**としてダウンロード

---

© Masaaki Yamaguchi — [github.com/masaaki-avnturle/Bada](https://github.com/masaaki-avnturle/Bada)
概念シミュレーション / 研究アート・非医療。
