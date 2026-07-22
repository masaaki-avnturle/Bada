# BadaGPT — ζ-Entropy 未知事前予知エンジン

**Bada 言語 (v3 作用素環) × リーマンゼータ関数のエントロピー**による、ChatGPT 型の
「未知事前予知(a-priori prediction)」言語生成アプリ。
Android **APK** と Windows 10/11 **EXE** の両方でビルドできます。

> ⚠ 概念シミュレーション / 研究アートです。実在の予言・医療・投資助言ではありません。
> ζ-Entropy コアは解析数論(ゼータ分布のエントロピー)を実装した**決定論的**言語生成器です。

---

## ✨ 機能

| # | 機能 | 説明 |
|:-:|:-----|:-----|
| ① | **資料を投稿** | PDF・ソースコード・テキストをドロップ/選択。PDF はブラウザ内(`DecompressionStream`)でテキスト抽出。 |
| ② | **2つの生成モード** | ・**ζ-Entropy ローカル**(完全オフライン)<br>・**Claude API + ζ-Entropy**(自分の API キーを入力) |
| ③ | **ζテレメトリ表示** | s, ζ(s), H(s)[nat/bit], 温度 τ, γ, seed をリアルタイム表示。 |
| ④ | **解答をダウンロード** | 生成解答を **PDF** / .txt / .md、**抽出したソースコード**をファイルとして保存。 |

### 🔑 Claude API キー
- キーは**この端末の `localStorage` にのみ**保存され、送信先は **Anthropic API のみ**です。
- ブラウザ直接呼び出しのため `anthropic-dangerous-direct-browser-access` ヘッダを付与します。
- モデル名(既定 `claude-sonnet-4-5`)は、ご自身のアカウントで利用可能な ID に編集してください。
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
