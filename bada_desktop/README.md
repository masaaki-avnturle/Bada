# NoemaKey — 未知事前予知 予測入力 (Windows デスクトップ / EXE)

**コンパクト 60% 配列のオンスクリーンキーボード**に、**未知事前予知エンジン**による
**英語・日本語の単語補完と次単語の先読み**を組み込んだ Windows 10/11 用デスクトップアプリ
です。エンジンは `bada_apk` の Kotlin エンジンを**共有**しています
（`sourceSets` で `../bada_apk/.../engine` を参照）。

## 特長

- ⌨ **コンパクト 60% 配列**のオンスクリーンキーボード（Control 位置）。
- 🔮 **予測バー** — 入力中の単語を補完（例：`man`→`manifold`、`多様`→`多様体`）、
  区切りの後は次単語を先読み（英語・日本語）。候補クリックで挿入。
- 📂 **複数コーパスの読み込み**（ファイル→コーパス読み込み）で予測が賢くなる。
- ♻️ **オンライン学習** — 入力した単語を append-only にモデルへ取り込む（リバイザ学習ループ）。
- 🔐 **量子暗号クレジット保護** — BB84 量子鍵配送で導出した鍵＋HMAC-SHA256 で著者クレジットを
  改ざん検知可能に封印。メニュー「クレジット保護」→「量子暗号クレジット（BB84）を表示・検証」で
  証明書・鍵指紋・QBER・検証結果を表示、本文へのシール付与も可能。

予測は Unknown-Prior Engine（`com.yamaguchi.bada.engine.Predictor`）が担当し、n-gram
証拠を `softmax` で基底分布 `a` にし、エントロピー位相で再重み付け（確率不変・定理2）します。

## ダウンロード（GitHub）

GitHub Actions（`.github/workflows/build-apk.yml`）の **windows-exe** ジョブが
`windows-latest` ランナーで EXE をビルドします。

- **Actions の成果物**：リポジトリの **Actions** → 最新の成功実行 → **Artifacts** の
  **`noemakey-windows-exe`**（`noemakey-windows.zip` を含む。解凍すると
  `NoemaKey/NoemaKey.exe`。`.msi` インストーラも作成できれば同梱）。
- **Releases**：`v` で始まるタグを push、または GitHub UI で Release を発行すると、
  Windows パッケージが Release に添付されます。

### 「競合してインストールできない」ときは

- **一番簡単＝インストール不要**：`noemakey-windows.zip` を解凍し、`NoemaKey/NoemaKey.exe`
  を直接ダブルクリックで起動できます（**ポータブル版**。インストール不要なので競合しません）。
- **MSI で「別バージョンが既にインストール済み」と出る場合**：MSI は**固定 UpgradeCode**と
  **ユーザー単位インストール**にしたので、新しい MSI は前の版を**上書き更新**します。それでも
  競合するときは、いったん「アプリと機能」から旧 **NoemaKey** をアンインストール →
  新しい MSI を実行してください。

## 手元でビルド／実行

```bash
cd bada_desktop
./gradlew run                    # そのまま起動（開発用）
./gradlew run --args=--selftest  # 予測エンジンのヘッドレス自己テスト
./gradlew installDist            # build/install/NoemaKey/ に配布物

# EXE 化（Windows で。JDK 17+ 同梱の jpackage）
jpackage --type app-image \
  --input build/install/NoemaKey/lib \
  --main-jar NoemaKey.jar \
  --main-class com.yamaguchi.bada.desktop.MainKt \
  --name NoemaKey --app-version 0.2.0 --dest build/jpackage
#   -> build/jpackage/NoemaKey/NoemaKey.exe
```

必要環境：JDK 17 以上（`jpackage` は EXE/MSI 生成に使用）。

> 名称について：本アプリは独自コードネーム **NoemaKey** を用います（「Happy Hacking
> Keyboard / HHKB」は PFU Limited の商標、「Bada」は別 OS 名のため、製品名としては
> 使用していません。内部のエンジン名前空間 `com.yamaguchi.bada.engine` は Bada
> フレームワーク本体です）。

---

*© 2025–2026 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
