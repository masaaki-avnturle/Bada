# YamaguchiHealth

呼吸誘導・瞑想・セルフケアの **ウェルネス学習用アプリ**（C言語・コンソール）。
A breathing / meditation / self-care **wellness demo** written in C.

> ## ⚠️ 重要 / Important — これは医療機器ではありません
>
> - **血液検査値は測定しません。** 外部の温度・赤外線センサーで GPT(ALT)・
>   白血球(WBC)・赤血球(RBC)・クレアチニンなどの血液成分を測ることは
>   **物理的に不可能**です。ダッシュボードの数値はすべて **デモ(模擬)** で、
>   実測ではありません。
> - **薬の効果は再現・投与できません。** 音や光の「周波数」で
>   エチゾラム・ブロチゾラム・フルニトラゼパム（サイレース/ロヒプノール）・
>   リスペリドン・オランザピン・リチウム等の薬理作用を再現することは
>   できません。本アプリは薬を投与・模擬・代替しません。
> - **サイレントトークは手入力のメモ記録**です。赤外線で思考や唇の動きを
>   読み取る機能ではありません。
> - 本アプリは診断・治療・服薬指導を行いません。体調がすぐれない時は
>   医師・薬剤師にご相談ください。
>   日本: いのちの電話 **0570-783-556** / 緊急 **119**。

This program does **not** measure blood chemistry, does **not** deliver any
medication effect, and is **not** a medical device. All sensor values are
clearly-labelled simulated demo data.

---

## 機能 / Features

| メニュー | 内容 |
|:--|:--|
| 1. センサー ダッシュボード | 体表温・室温・心拍の **模擬(SIMULATED)** 表示。血液値は表示しない |
| 2. サイレントトーク | `start` / `stop` / `record` で手入力メモを記録・保存 |
| 3. 呼吸誘導 / 瞑想 | 秘伝功・養生功・Super Reading System(瞑想法/呼吸法/活夢法)・太平洋クジラ瞑想。タイマー付きの吸う/止める/吐くガイド。`record` でセッション保存 |
| 4. ウェルネス情報 | リシン(L-lysine) 等の一般的な栄養情報（情報提供のみ） |
| 5. About / 免責事項 | 注意事項 |

保存先 / saved logs: `yh_logs/` ディレクトリ（テキストファイル）。

---

## ビルドと実行 / Build & Run (Linux / macOS)

```sh
make          # コンパイル
make run      # 実行
# または
cc -O2 -o yamaguchi_health yamaguchi_health.c && ./yamaguchi_health
```

---

## Android / APK について（正直な説明）

ご要望は「C言語で作って .apk でインストール」でしたが、ここは正確にお伝えします。

- 純粋な C のプログラムは **Android NDK** でクロスコンパイルすれば、Android
  端末上で動く **ネイティブ実行ファイル**（例: `aarch64-linux-android`）に
  できます。Termux 等のターミナル環境ならそのまま実行可能です。
- ただし、タップでインストールできる本物の **`.apk` には Android SDK による
  パッケージング**（`AndroidManifest.xml`、リソース、`classes.dex`、署名）が
  必要で、C のソースだけからは生成できません。この実行環境には Android SDK が
  無いため、**署名済み APK の生成はここでは行えません**。

### NDK でのネイティブビルド例（端末側に NDK がある場合）

```sh
$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android24-clang \
    -O2 -o yamaguchi_health yamaguchi_health.c
# 生成された yamaguchi_health を Android 端末(Termux 等)に転送して実行
```

GUI 付きの本物の APK が必要な場合は、この C ロジックを土台に
Android Studio (Kotlin/Java + NDK の JNI) でラップする構成をおすすめします。
ご希望があれば、その雛形（`build.gradle` / `MainActivity` / `Activity` レイアウト）
を別途用意します。
