# Bada HHKB Pro — 未知事前予知 予測入力 (Windows デスクトップ / EXE)

**Happy Hacking Keyboard Professional 風のオンスクリーンキーボード**に、**未知事前予知
エンジン**による**英語・日本語の単語補完と次単語の先読み**を組み込んだ Windows 10/11 用
デスクトップアプリです。エンジンは `bada_apk` の Kotlin エンジンを**共有**しています
（`sourceSets` で `../bada_apk/.../engine` を参照）。

## 特長

- ⌨ **HHKB 風レイアウト**のオンスクリーンキーボード（60% コンパクト配列・Control 位置）。
- 🔮 **予測バー** — 入力中の単語を補完（例：`man`→`manifold`、`多様`→`多様体`）、
  区切りの後は次単語を先読み（英語・日本語）。候補クリックで挿入。
- 📂 **複数コーパスの読み込み**（ファイル→コーパス読み込み）で予測が賢くなる。
- ♻️ **オンライン学習** — 入力した単語を append-only にモデルへ取り込む（リバイザ学習ループ）。

予測は Unknown-Prior Engine（`com.yamaguchi.bada.engine.Predictor`）が担当し、n-gram
証拠を `softmax` で基底分布 `a` にし、エントロピー位相で再重み付け（確率不変・定理2）します。

## ダウンロード（GitHub）

GitHub Actions（`.github/workflows/build-apk.yml`）の **windows-exe** ジョブが
`windows-latest` ランナーで EXE をビルドします。

- **Actions の成果物**：リポジトリの **Actions** → 最新の成功実行 → **Artifacts** の
  **`bada-hhkb-windows-exe`**（`bada-hhkb-windows.zip` を含む。解凍すると
  `BadaHhkb/BadaHhkb.exe`。`.msi` インストーラも作成できれば同梱）。
- **Releases**：`v` で始まるタグを push、または GitHub UI で Release を発行すると、
  Windows パッケージが Release に添付されます。

## 手元でビルド／実行

```bash
cd bada_desktop
./gradlew run                    # そのまま起動（開発用）
./gradlew run --args=--selftest  # 予測エンジンのヘッドレス自己テスト
./gradlew installDist            # build/install/BadaHhkb/ に配布物

# EXE 化（Windows で。JDK 17+ 同梱の jpackage）
jpackage --type app-image \
  --input build/install/BadaHhkb/lib \
  --main-jar BadaHhkb.jar \
  --main-class com.yamaguchi.bada.desktop.MainKt \
  --name BadaHhkb --app-version 0.2.0 --dest build/jpackage
#   -> build/jpackage/BadaHhkb/BadaHhkb.exe
```

必要環境：JDK 17 以上（`jpackage` は EXE/MSI 生成に使用）。

---

*© 2025–2026 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
