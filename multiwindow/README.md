# Bada MultiWindow — Samsung フリーフォーム対応マルチウィンドウ アプリ

Samsung タブレットの**フリーフォーム機能(ポップアップ表示 / Samsung DeX)**を使って、
**タブレットの画面上に直接**、複数の独立したウィンドウを開くマルチウィンドウ
アプリケーションです。

アプリの画面「内部」に擬似ウィンドウを描くのではありません。各ツール(メモ・電卓・
時計・空き容量モニター)は **OS が管理する本物のフリーフォーム ウィンドウ**として
開き、ホーム画面や他のアプリの上でドラッグ移動・リサイズ・重ね合わせができます。

## ✨ 特徴

| 特徴 | 内容 |
|:---|:---|
| **本物のマルチウィンドウ** | 各ツールは独立した Android タスク。Samsung ポップアップ表示 / DeX / Android freeform でタブレット画面上に浮かぶウィンドウとして開く |
| **マルチインスタンス** | 同じツールを何枚でも(メモを 3 枚並べる等)。`documentLaunchMode="always"` + `FLAG_ACTIVITY_NEW_DOCUMENT \| FLAG_ACTIVITY_MULTIPLE_TASK` |
| **カスケード配置** | `ActivityOptions#setLaunchBounds()` で新しいウィンドウを少しずつずらして配置 |
| **超軽量** | 依存ライブラリゼロ・WebView 不使用・純フレームワーク API のみ。APK は約 100 KB 未満で、**ストレージ(内部ディスク)やメモリの空きが少ないタブレットでも動作** |
| **低メモリ耐性** | 非表示ウィンドウは更新を停止。空き容量不足でメモが保存できない場合もクラッシュせず警告表示 |
| **空き容量モニター** | 内部ストレージと RAM の使用率をリアルタイム表示する専用ウィンドウを同梱 |

## 🪟 同梱ウィンドウ

- **📝 メモ** — 自動保存の付箋メモ。何枚でも開ける(ウィンドウごとに別ファイル)
- **🧮 電卓** — 四則演算・±・%・⌫。小さくリサイズしても崩れないレイアウト
- **🕐 時計** — 大きな時刻表示。非表示中は更新停止で省電力
- **📊 空き容量モニター** — 内部ストレージ / RAM の空きを 2 秒ごとに表示、90% 超で赤字警告

## 📱 使い方

1. APK をダウンロードしてインストール(提供元不明アプリの許可が必要です)。
   - **Actions から**: [Actions の実行一覧](https://github.com/masaaki-avnturle/Bada/actions/workflows/multiwindow-app-build.yml)
     で最新の実行を開き、ページ下部 **Artifacts** の `multiwindow-android` を
     ダウンロード(zip 内に `bada-multiwindow-debug.apk`)。
     `multiwindow/` を変更する PR や main への push のたびに自動ビルドされます。
   - **Releases から**: `multiwindow-v*` タグ作成後は
     [Releases](https://github.com/masaaki-avnturle/Bada/releases) の
     `bada-multiwindow-debug.apk` を直接ダウンロード。
2. 「Bada MultiWindow」を起動し、開きたいツールのボタンを押す。
3. フリーフォーム対応端末(Samsung DeX、または freeform が有効な One UI)では、
   そのままタブレット画面上に独立ウィンドウとして開きます。
   通常モードの Samsung 端末では、**最近使ったアプリ**画面で各ウィンドウの
   アイコンをタップ →「**ポップアップ表示で開く**」を選ぶとフリーフォームになります。
4. ウィンドウはタイトルバーのドラッグで移動、端のドラッグでサイズ変更できます。

> 💡 Samsung One UI の設定 →「便利な機能」→「マルチウィンドウ」から
> 「ポップアップ表示で起動」ジェスチャー(画面の隅から中央へスワイプ)を
> 有効にすると、どのウィンドウもすぐフリーフォーム化できます。

## 🔧 技術構成(なぜ「別の画面の内部」ではないのか)

- `AndroidManifest.xml` の全アクティビティに `android:resizeableActivity="true"` と
  `<layout defaultWidth/defaultHeight/minWidth/minHeight>`(freeform 既定サイズ)を宣言
- `<uses-feature android:name="android.software.freeform_window_management" required="false"/>`
- Samsung 旧 MultiWindow SDK 世代の端末向け `meta-data`
  (`com.samsung.android.sdk.multiwindow.enable` ほか)も併記
- ランチャーは `ActivityOptions.makeBasic().setLaunchBounds(Rect)` を付けて
  `startActivity()` するため、フリーフォーム環境では**指定位置・サイズの
  OS ウィンドウ**として起動します(ウィンドウ管理は完全に OS 側 = Samsung の
  フリーフォーム機能が担当)
- 各ツールは `documentLaunchMode="always"` なので起動のたびに新規タスク
  = 新規ウィンドウ

## 🏗️ ビルド

GitHub Actions [`multiwindow-app-build.yml`](../.github/workflows/multiwindow-app-build.yml)
が自動ビルドします:

- `multiwindow/` を変更する **PR / main への push** → Actions 実行ページの
  **Artifacts** から `multiwindow-android` をダウンロード
- `multiwindow-v*` タグを push → APK を GitHub Release に添付
- Actions の `workflow_dispatch` → アーティファクトとしてダウンロード
  (`release_tag` を指定すると Release にも添付)

ローカルでビルドする場合(Android SDK + JDK 17 + Gradle 8.9):

```bash
cd multiwindow/app-android
gradle assembleDebug
# → app/build/outputs/apk/debug/app-debug.apk
```
