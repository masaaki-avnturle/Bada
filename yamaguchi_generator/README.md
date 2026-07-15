# 山口フレームワーク — 方程式↔抽象画 生成器

**Yamaguchi Framework — Equation ↔ Abstract-Art Bidirectional Generator**

高感度タッチ描画に対応した、方程式と抽象画を双方向に生成するアプリです。
Web版に加えて **Android APK** と **Windows 10 / 11 用 EXE** を配布できます。

---

## 📥 ダウンロード（アプリ）

ビルド済みの APK / EXE は本リポジトリの **[Releases](../../releases)** から入手できます。

| プラットフォーム | ファイル | 説明 |
|:---|:---|:---|
| **Android** | `YamaguchiGenerator-x.y.z-debug.apk` | 端末にそのままインストール可能（提供元不明のアプリを許可） |
| **Windows 10/11** | `YamaguchiGenerator Setup x.y.z.exe` | インストーラ版（スタートメニュー／デスクトップにショートカット作成） |
| **Windows 10/11** | `YamaguchiGenerator-x.y.z-portable.exe` | ポータブル版（インストール不要・単体EXE） |

> Web版は `www/index.html` をブラウザで開くだけでも動作します。

---

## ✍️ タッチパネル感度の改善点

方程式や図形をきちんと描けるよう、描画エンジンを刷新しました。

- **Pointer Events + `setPointerCapture`** — 指／スタイラスがキャンバス外に出ても描画が途切れない
- **中点二次ベジェによる真のスムージング** — 手ブレを吸収し、なめらかな曲線・直線を描画
- **`getCoalescedEvents()` による高サンプリング取得** — 速いストロークでも点が飛ばず線が繋がる
- **筆圧の指数移動平均** — スタイラス／対応タッチの筆圧で線幅が自然に変化（ジッタ除去）
- **`devicePixelRatio` 補正** — 高DPI / Retina 端末でも座標がずれず鮮明
- **プライマリポインタのみ描画** — マルチタッチ・手のひらの誤爆を抑制（パームリジェクション）
- **`touch-action:none` / スクロール・ズーム抑止** — 描画中に画面が動かない
- **Undo / Redo・スムージング/筆圧トグル** — 描画を細かく調整可能
- **オフライン動作** — APK / EXE ではネットワークなしでもローカル推定で方程式↔図形を生成

---

## 🛠 自分でビルドする

### 前提
- Node.js 20 以上
- Windows EXE を作る場合: Windows 環境（または後述の GitHub Actions）
- APK を作る場合: JDK 17 + Android SDK（または後述の GitHub Actions）

### Web / デスクトップ（Electron）
```bash
cd yamaguchi_generator
npm install
npm start              # デスクトップアプリとして起動
npm run dist:win       # Windows 10/11 用 EXE を dist/ に生成
```

### Android APK（Capacitor）
```bash
cd yamaguchi_generator
npm install
npx cap add android    # android/ プロジェクトを生成
npx cap sync android
cd android && ./gradlew assembleDebug
# → android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 🤖 GitHub Actions で自動ビルド（推奨）

ローカルに Android SDK や Windows が無くても、CI が APK と EXE を自動生成します。

**手動実行:**
`Actions` タブ → **Build Yamaguchi Generator** → **Run workflow**
→ 完了後、実行結果ページの Artifacts から APK / EXE をダウンロード。

**Release として配布（タグ push）:**
```bash
git tag yamaguchi-v1.0.0
git push origin yamaguchi-v1.0.0
```
→ APK と EXE（インストーラ + ポータブル）が自動で **Releases** に添付されます。

---

## 📂 構成

```
yamaguchi_generator/
├── www/index.html          # アプリ本体（高感度描画エンジン + 生成ロジック）
├── electron/main.js        # Windows/デスクトップ用 Electron エントリ
├── package.json            # electron-builder / Capacitor 設定
├── capacitor.config.json   # Android 設定
├── resources/icon.ico|png  # アプリアイコン
└── README.md
.github/workflows/build-yamaguchi.yml   # APK + EXE 自動ビルド
```

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
