# Ω-SilentTalk → BadaGPT — 無音・非キーボード入力でアプリ&論文を生成

Ω-Telepathy の思考入力と「サイレントトーク」（音声なしの口・顔の動き感知）を取り入れ、
**Γ大域的部分積分多様体 + Jones多項式**を「熱エネルギー経路」として特徴をルーティングし、
**本物の self-attention(transformer)** で語列を組み立て、**BadaGPT** が受けて対象者のイメージを
**APK / Windows10,11 / Linux のアプリ**と**論文PDF**として生成・ダウンロードできる統合アプリです。

---

## ⚠⚠ 重要 — 概念デモ/アート・非医療・非読心
- **思考も無音発話も読み取れません。** カメラは口の動きの**エネルギーを疑似記号化**するだけで、
  実際の**読唇・読心・サイレント音声認識・サーモグラフィではありません**。
- 生成物は**雛形/概念**です。OpenAIキーを入れた場合のみ送信先は `api.openai.com`（端末内のみ）。

## 入力（すべて音声なし・キーボード/ペン不要の代替）
- **サイレントトーク**: Webカメラで口付近ROIの暗部率(openness)＋フレーム差分(motion)から feat∈[0,1] を得て候補語を提示（熱エネルギー風オーバーレイ表示）。
- **思考入力(ドウェル)**: 注視グリッド（ホバー滞留で確定）。
- **イメージ入力**: 画像を特徴量化して候補語に。

## 認識（実在の計算）
- Jones多項式 `V_{T(2,n)}`（`n=3+2·round(7·feat)`）の `|V(e^{2πi/5})|` で候補をゲート（熱エネルギー経路）。
- self-attention `softmax(QKᵀ/√d)`（各行の和=1、行列を可視化）で語列を構成。

## 生成（BadaGPT）
認識した仕様から、ターゲット別にソース一式＋**論文PDF**を生成・ダウンロード:
| ターゲット | 生成物 |
|:--|:--|
| Web | 単一HTML |
| APK | `www/` + `config.xml` + `BUILD.md`（Cordova）|
| Windows | `www/` + `electron/`（main.js/package.json）+ `BUILD.md`|
| Linux | 上記 + `dist:linux`（AppImage/deb）|
| 論文PDF | 実 `.pdf`（純JS最小PDF, ASCII）+ `paper.html`（日本語は印刷→PDF保存）|
オフライン決定論生成。OpenAIキーありで実ChatGPT生成に切替。

## 使い方・配布
```bash
cd www && python3 -m http.server 8000   # カメラは https/localhost が必要
```
`omega_silenttalk` はビルドマトリクスに追加済み（APK / Windows EXE / Linux）。
Actions「Ω apps build」の成果物、または `apps-v*` タグで Releases からDL。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念デモ/アート・非医療・非読心*
