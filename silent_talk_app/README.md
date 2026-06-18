# Silent Talk — 無音通信 Android アプリ

**neurothermal をベースにした「言葉を使わず信号で伝える」Android アプリ**です。
ガンマ関数の大域的部分積分多様体の熱エネルギー

```
T' = ∫ Γ(γ)' dx_m
```

を搬送波として、入力テキストを **熱・神経パルス列**（深部体温オフセット）へ符号化し、
同時に **赤外線センサーと温度計** の値を全画面常設バーでライブ表示します。
復号で元のテキストへ可逆に戻せます。

> ⚠️ 教育・可視化シミュレーションです。実在の医療機器・診断用途ではありません。

---

## 📲 APK のダウンロード（GitHub の URL から）

ビルド済み APK は **GitHub Releases** から配布されます。

1. リポジトリの **Releases** ページを開く
   → `https://github.com/masaaki-avnturle/Bada/releases`
2. 最新の **Silent Talk vX.Y** リリースを開き、添付の **`SilentTalk.apk`** をスマホでダウンロード
3. Android の「提供元不明のアプリ / 不明なアプリのインストール」を許可してインストール

> Release は **`v` で始まるタグを push** すると GitHub Actions が自動ビルド・公開します（下記）。
> タグなしの手動実行（workflow_dispatch）の場合は、Actions 実行ページの **Artifacts**
> （`SilentTalk-APK`）からダウンロードできます。

---

## 🚀 リリースの作り方（メンテナ向け）

APK ビルドは **GitHub Actions**（`.github/workflows/silent-talk-android.yml`）で行います。
この環境には Android SDK が無いためローカルビルドはせず、CI 上の SDK でビルドします。

```sh
# バージョンタグを打って push するだけで Release に APK が公開される
git tag v1.0
git push origin v1.0
```

ワークフローの流れ：
1. JDK 17 + Android SDK をセットアップ
2. 署名用 keystore を自動生成（デモ用の自己署名）
3. `./gradlew :app:assembleRelease` で署名済み APK をビルド
4. APK を Actions の Artifact にアップロード
5. タグ push の場合は **Releases に `SilentTalk.apk` を添付して公開**

---

## ⌨️ 他アプリへの文字入力（キーボード化 / IME）

Silent Talk は **入力メソッド（カスタムキーボード）** として動作します。
有効化すると、**どのアプリのテキスト欄でも** Silent Talk のダイアログ風の
小型パネルが立ち上がり、**タッチした文字がそのアプリへ直接入力**されます。
タブレット・スマホ共通で同じ GUI が使えます。

設定手順（アプリ内のボタンから誘導）:
1. **① Silent Talk キーボードを有効化** … 端末の「入力方法」設定で Silent Talk をオン
2. **② キーボードを Silent Talk に切替** … 入力方法ピッカーで Silent Talk を選択
3. 任意のアプリのテキスト欄をタップ → コンパクトな Silent Talk パネルで入力

パネル上部には赤外線センサー + 温度計の常設ライブバーがあり、各キー入力は
ガンマ熱多様体 `T'=∫Γ(γ)'dx_m` で無音信号化されて可視化されます。

> キーボードは入力された文字を端末外へ送信しません（ネットワーク権限なし）。

---

## アプリの機能

| 要素 | 内容 |
|:--|:--|
| 常設センサーバー | 🔴赤外線センサー / 🌡️温度計 / ⚖️融合体温 / Γ熱エネルギー T' を 2秒ごとにライブ更新 |
| 信号に符号化 | テキスト → ガンマ熱多様体で変調した無音パルス列（γ・温度・IR・コード） |
| 復号 | パルス列 → 元テキスト（往復検証つき） |
| クリア | 入力・出力のリセット |

### 内部構成（neurothermal の Kotlin 移植）

```
app/src/main/java/com/omega/silenttalk/
├── NeuroThermal.kt   Γ・ψ・Γ' と T'=∫Γ'dx_m、赤外線/温度計センサー、融合
├── SilentCodec.kt    テキスト⇄無音パルス列の可逆コーデック
└── MainActivity.kt   UI・常設センサーバー・エンコード/デコード操作
```

- **最小SDK**: API 24 (Android 7.0) / **ターゲット**: API 34
- **言語**: Kotlin / **UI**: Android View + ViewBinding + Material3 ダークテーマ
- 外部の実機センサーは使わず、`T'=∫Γ(γ)'dx_m` 由来の合成値を表示します。

---

## ローカル開発（任意）

Android SDK のある環境（Android Studio 等）では：

```sh
cd silent_talk_app
./gradlew :app:assembleDebug      # デバッグAPK
./gradlew :app:assembleRelease    # リリースAPK（署名引数は上記ワークフロー参照）
```
