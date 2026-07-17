# Entropia Visor — 大域予知ゴーグル

**ガンマ関数 大域的部分積分多様体 × 世界熱エントロピー で、世界の出来事を振り返り・予知する装置**

アニメ『リコリス・リコイル』のエンジニアの少女が、終幕にゴーグル越しに世界の出来事を
振り返る──あの装置へのオマージュです（原作の画像・ロゴ・キャラクターは使用していません）。
Vision Pro 風のバイザー UI で、山口フレームワークの **ガンマ関数に基づく大域的部分積分多様体**と
**世界の熱エントロピー**から、世界の出来事を「見て」いきます。

> 表示される「出来事」は、熱エントロピー予知エンジンが生成する**抽象的・詩的なオラクル**です
> （実在の報道の再現・捏造ではありません）。

---

## 🥽 使い方

- **世界（球体）** — 世界の熱エントロピー場を、大域的部分積分多様体の光線で描いた球体。
  フォーカス中の出来事の Ξ・幾何で脈動・変色します。
- **タイムライン** — 下部の帯。**◀ 過去（振り返り） · 今 · 予知（未来）▶**。タップ/ドラッグで時相を選択。
- **◀◀ 振り返る / 予知 ▶▶** — 過去/未来へ時相を送る。**今 / NOW** で現在へ。**⏸/▶** で自動再生。
- **世界の熱エントロピー** — スライダーで熱エントロピーのエネルギーを上げると、
  多様体が揺らぎ、未来の出来事が変化します（第二法則: 未来ほどエントロピー増大）。
- **出来事カード** — フォーカス中の出来事（領域・様相・Ξ・多様体幾何・熱エネルギー・多様体グリフ）。

### 数理（Bada エンジン）
- Ξ（予知不変量）= `β(H+1, M+1) / log(N+1)`  ← **ガンマ関数** β に基づく ζ ゲージ
- M = 大域的部分積分多様体の線素 `1/(x·logx)²`
- 幾何 = サーストン8幾何（球体の色相・出来事の様相を決定）
- 熱エントロピー = 世界のエネルギー（未来へ向かって増大）

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は **[Releases](../../releases)** および GitHub Actions の Artifacts から。

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `EntropiaVisor-x.y.z-debug.apk` |
| **Windows 10/11** | `EntropiaVisor Setup x.y.z.exe`（インストーラ） / `EntropiaVisor-x.y.z-portable.exe`（ポータブル） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します（オフライン）。

---

## 🛠 自分でビルド

```bash
cd entropia_visor
npm install
npm start              # デスクトップ起動
npm run dist:win       # Windows 10/11 EXE を dist/ に生成

npx cap add android
npx cap sync android
cd android && ./gradlew assembleDebug   # app-debug.apk
```

## 🤖 GitHub Actions

`Actions` → **Build Entropia Visor** → Run workflow で APK / EXE を自動生成。
タグ `visor-v1.0.0` を push すると Releases に添付されます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
