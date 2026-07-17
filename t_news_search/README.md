# Ch.T — TupleSpace News 速報検索

**マスメディア「T」局のニュース速報を検索する報道アプリ（Bada 熱エントロピー多様体エンジン製）**

これまでの Bada アプリ群（ガンマ関数 大域的部分積分多様体 × 世界熱エントロピー、および
「アプリを作る」Bada Foundry 方式）を使って作った、**ニュース速報の検索アプリ**です。
TV 報道（架空局 **Ch.T ／ TupleSpace News**）のブロードキャスト UI で、
**探したいニュースを検索**すると、関連する「速報」が生成・絞り込み表示されます。

> ⚠️ 本アプリの「速報」は **Bada 熱エントロピー多様体エンジンが生成する架空のニュース**です。
> 実在の報道機関・団体・人物・出来事とは一切関係ありません。**Ch.T は架空の放送局**です。

---

## 📺 機能

- **速報検索** — 「地震」「経済」「宇宙」「選挙」など、探したい語を入力すると、
  その語を織り込んだ速報が生成され、緊急度順に表示されます。
- **カテゴリ絞り込み** — 速報 / 政治 / 経済 / 災害 / 国際 / 科学 / 気象 / 社会。
- **緊急度 Ξ** — 各速報の緊急度を、**ガンマ関数に基づく ζ ゲージ**
  `Ξ = β(H+1, M+1)/log(N+1)` と大域的部分積分多様体 `1/(x·logx)²` で算出。
  多様体幾何（サーストン8幾何）が速報のカテゴリ・色を決定します。
- **ON AIR パネル** — 熱エントロピー球の放送ビジュアル＋トップ速報の下部テロップ。
- **速報ティッカー** — 画面下部に最新速報が流れます。
- **記事** — 速報カードをタップで本文（生成記事）を展開。

数理エンジンは山口フレームワーク（`bada_ruby`）の `Manifold` / `Special`（ガンマ・ベータ・ζ）
と同一の考え方を、オフラインで動く JS に移植しています。

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は **[Releases](../../releases)** および GitHub Actions の Artifacts から。

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `ChTNewsSearch-x.y.z-debug.apk` |
| **Windows 10/11** | `ChTNewsSearch Setup x.y.z.exe`（インストーラ） / `ChTNewsSearch-x.y.z-portable.exe`（ポータブル） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します（オフライン）。

---

## 🛠 自分でビルド

```bash
cd t_news_search
npm install
npm start              # デスクトップ起動
npm run dist:win       # Windows 10/11 EXE を dist/ に生成

npx cap add android
npx cap sync android
cd android && ./gradlew assembleDebug   # app-debug.apk
```

## 🤖 GitHub Actions

`Actions` → **Build Ch.T News Search** → Run workflow で APK / EXE を自動生成。
タグ `tnews-v1.0.0` を push すると Releases に添付されます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
