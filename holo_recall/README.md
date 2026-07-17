# HOLO RECALL — 空間ホログラム再生

**Ch.T の速報を「動画」で振り返る、visionOS 参考のホログラフィック・ディスプレイ**

前アプリ **Ch.T News 速報検索** の出来事を、**動画として振り返れる**ように、
**Apple Vision Pro / visionOS の空間UI を参考**にした**ホログラフィック・ディスプレイ**へ
取り込んだアプリです（Apple のロゴ・商標・製品名は使用していません。オリジナルの空間UI）。

浮遊するホログラムの画面が奥行きをもって並び、視線（ポインタ）で注視すると拡大、
タップで手前に呼び出し、下部のトランスポートで**再生・一時停止・スクラブ・早送り**して
過去（振り返り）から未来（予知）までを**映像**として辿れます。

> ⚠️ ホログラム内の映像・速報は **Bada 熱エントロピー多様体エンジンが生成する架空のもの**です
> （実在の報道・団体・人物・出来事とは関係ありません）。

---

## 🥽 機能（visionOS 参考の空間UI）

- **浮遊ホログラム画面** — 出来事ごとの映像パネルが 3D 的な奥行き・視差で配置。
  注視（ポインタ）で拡大、タップで焦点化（Vision Pro のギャラリー配置を参考）。
- **動画で振り返る** — 下部トランスポート（⏮ ◀◀ ⏯ ▶▶ ⏭・速度 0.5〜4.0x）と
  タイムラインスクラブで、過去（振り返り）↔ 今 ↔ 未来（予知）を映像として再生。
- **ホログラフィック表現** — 走査線・エッジグロー・ちらつき・グラス透過・
  空間の床グリッド／浮遊ダスト・視線レティクル・ホームインジケータ。
- **映像（footage）** — 各パネルの映像は Bada エンジンが駆動（波形・球体・レーダー・
  ブルーム・データ流）。多様体幾何（サーストン8幾何）が映像種と色を決定。
- **焦点 Ξ** — 焦点中の出来事の緊急度を、**ガンマ関数ベースの ζ ゲージ**
  `Ξ = β(H+1, M+1)/log(N+1)` と大域的部分積分多様体 `1/(x·logx)²` で算出。

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は **[Releases](../../releases)** および GitHub Actions の Artifacts から。

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `HoloRecall-x.y.z-debug.apk` |
| **Windows 10/11** | `HoloRecall Setup x.y.z.exe`（インストーラ） / `HoloRecall-x.y.z-portable.exe`（ポータブル） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します（オフライン）。

---

## 🛠 自分でビルド

```bash
cd holo_recall
npm install
npm start              # デスクトップ起動
npm run dist:win       # Windows 10/11 EXE を dist/ に生成

npx cap add android
npx cap sync android
cd android && ./gradlew assembleDebug   # app-debug.apk
```

## 🤖 GitHub Actions

`Actions` → **Build Holo Recall** → Run workflow で APK / EXE を自動生成。
タグ `holo-v1.0.0` を push すると Releases に添付されます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
*visionOS / Apple Vision Pro の空間UIを参考にしたデザインです（Apple とは無関係）。*
