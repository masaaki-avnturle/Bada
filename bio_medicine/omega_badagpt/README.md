# BadaGPT 改良版 — 思考入力 → アプリ/PDF/ソースコード生成スタジオ

既存の **BadaGPT道場**（ChatGPTの技を教える学習アプリ）とは**別物**の、**chatGPT版 BadaGPT**（コード生成スタジオ）です。
「思考入力」（Ω-Telepathy の思考タイピング出力など）を仕様として受け取り、BadaGPT が
Bada言語パイプライン（トークン化→意図解析→計画→生成→検証）で処理して、対象の
**APK / Windows10,11 / PDF / 任意アプリのソースコード一式**を生成・ダウンロードします。

- 既定: **オフラインで決定論的に雛形生成**（依存ゼロ・単一HTML）
- 改良（chatGPT版）: **自分の OpenAI APIキー**を入れると**実際の ChatGPT**でコード生成

---

## ⚠ 重要 — 概念実証・正直な位置づけ
- 「思考入力」は**概念版 Ω-Telepathy のテキスト出力**であり、**実際の読心ではありません**。
- 生成物は**雛形/ボイラープレート**（そのまま or 加筆してビルド）。
- OpenAI キーは**端末内でのみ使用**し、送信先は `api.openai.com` のみ（空ならオフライン生成）。

## 使い方
```bash
cd www && python3 -m http.server 8000     # or www/index.html を直接開く
```
1. 左の「👁 思考入力」に Ω-Telepathy の出力やイメージ要件を入れ「仕様に取り込む」。
2. ターゲット（Web / APK / Windows / PDF）を選ぶ（依頼文からも自動判定）。
3. 「生成 ▶」→ 生成ファイルがチャットに出るので各ファイルを **⬇ DL**。
   - OpenAIキー有 → 実ChatGPTで生成 / 空 → Bada決定論生成。

## 生成されるもの（オフラインBada生成の例）
| ターゲット | 生成物 |
|:--|:--|
| Web | 動作する単一HTML（計算機/メモ・ToDo/タイマー/フォーム/汎用を意図判定） |
| APK | `www/index.html` ＋ `config.xml` ＋ `BUILD.md`（Cordova一式） |
| Windows | `www/index.html` ＋ `electron/main.js` ＋ `electron/package.json` ＋ `BUILD.md`（Electron一式） |
| PDF | 実際の `.pdf`（最小PDFを純JS生成, ASCII）＋ `print.html`（日本語は印刷→PDF保存） |

## このアプリ自体のダウンロード（APK / Windows EXE / Linux）
`bio_medicine/omega_badagpt` は既存のビルドマトリクスに追加済みです。
- **Actions** →「Ω apps build」→ Run workflow → 成果物 `omega_badagpt-android/-windows/-linux`
- タグ `apps-v*` を push すると **Releases** に `BadaGPT-*` の APK/EXE/AppImage/deb が添付されます。

## 関連
`bada_gpt_dojo`（道場・学習用） · `bio_medicine/omega_telepathy`（思考入力元） · `bio_medicine/omega_apriori_injector` ほか

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証*
