# Bada MultiWindow — Windows 風デスクトップ & Samsung フリーフォーム マルチウィンドウ

Samsung タブレットの**フリーフォーム機能(ポップアップ表示 / Samsung DeX)**を使って、
**タブレットの画面上に直接**、複数の独立したウィンドウを開くマルチウィンドウ
アプリケーションです。

**Microsoft Windows 風のデスクトップ**(ティール色デスクトップ + タスクバー +
スタートメニュー)から、**タブレットにインストールされている全アプリ**をタップ
ひとつでフリーフォーム ウィンドウとして起動でき、Windows のように複数のアプリを
画面上で重ねたり、並べたり、ドラッグ移動・リサイズできます。

アプリの画面「内部」に擬似ウィンドウを描くのではありません。起動した各アプリ・
各ツールは **OS が管理する本物のフリーフォーム ウィンドウ**として開きます。

## ✨ 特徴

| 特徴 | 内容 |
|:---|:---|
| **Windows 風デスクトップ** | ティール色デスクトップにインストール済みアプリのアイコンを一覧表示。下部タスクバーに ⊞ スタートボタン・内蔵ツール クイック起動・時計 |
| **スタートメニュー** | ⊞ スタートで開閉。インストール済み全アプリの一覧 + 🔍 検索ボックス |
| **インストール済みアプリをウィンドウ起動** | アイコンをタップすると `getLaunchIntentForPackage()` + `setLaunchBounds()` でそのアプリをフリーフォーム ウィンドウとして起動。**長押しすると通常の全画面起動** |
| **本物のマルチウィンドウ** | 起動したアプリは独立した Android タスク。Samsung ポップアップ表示 / DeX / Android freeform でタブレット画面上に浮かぶウィンドウとして開き、Windows と同じように重ね合わせできる |
| **🗄 ファイルキャビネット** | タブレット内のアプリとファイルを、横スライドではなく**札束をペラペラめくるように**上下ドラッグで 1 枚ずつ 3D フリップして閲覧。速くはじくと連続リッフルめくり。タップでアプリはウィンドウ起動、フォルダは中へ、ファイルは対応アプリのウィンドウで表示 |
| **マルチインスタンス** | 内蔵ツールは同じものを何枚でも(メモを 3 枚並べる等)。`documentLaunchMode="always"` + `FLAG_ACTIVITY_NEW_DOCUMENT \| FLAG_ACTIVITY_MULTIPLE_TASK` |
| **カスケード配置** | 新しいウィンドウは少しずつずらして配置(Windows と同じカスケード) |
| **超軽量** | 依存ライブラリゼロ・WebView 不使用・純フレームワーク API のみ。APK は極小で、**ストレージ(内部ディスク)やメモリの空きが少ないタブレットでも動作**。アプリ一覧は背景スレッドで読み込み、アイコンは表示時に遅延ロード |
| **低メモリ耐性** | 非表示ウィンドウは更新を停止。空き容量不足でメモが保存できない場合もクラッシュせず警告表示 |
| **空き容量モニター** | 内部ストレージと RAM の使用率をリアルタイム表示する専用ウィンドウを同梱 |

## 🪟 内蔵ツール ウィンドウ

- **📝 メモ** — 自動保存の付箋メモ。何枚でも開ける(ウィンドウごとに別ファイル)
- **🧮 電卓** — 四則演算・±・%・⌫。小さくリサイズしても崩れないレイアウト
- **🕐 時計** — 大きな時刻表示。非表示中は更新停止で省電力
- **📊 空き容量モニター** — 内部ストレージ / RAM の空きを 2 秒ごとに表示、90% 超で赤字警告
- **🗄 ファイルキャビネット** — アプリ / ファイルを 1 件 = 1 枚のマニラフォルダ風カードにして、
  **上下ドラッグで札束のようにペラペラめくる**ブラウザ(横スライドなし)。
  速くはじくと連続めくり。「📁 ファイル」タブは内部ストレージをフォルダ単位でめくれます
  (Android 11+ では初回に「すべてのファイルへのアクセス」の許可が必要。案内カードを
  タップすると設定画面が開きます)

## 📱 使い方

1. APK をダウンロードしてインストール(提供元不明アプリの許可が必要です)。
   - **Actions から**: [Actions の実行一覧](https://github.com/masaaki-avnturle/Bada/actions/workflows/multiwindow-app-build.yml)
     で最新の実行を開き、ページ下部 **Artifacts** の `multiwindow-android` を
     ダウンロード(zip 内に `bada-multiwindow-debug.apk`)。
     `multiwindow/` を変更する PR や main への push のたびに自動ビルドされます。
   - **Releases から**: `multiwindow-v*` タグ作成後は
     [Releases](https://github.com/masaaki-avnturle/Bada/releases) の
     `bada-multiwindow-debug.apk` を直接ダウンロード。
2. 「Bada MultiWindow」を起動すると **Windows 風デスクトップ**が表示されます。
   - デスクトップのアプリ アイコンを**タップ** → そのアプリをフリーフォーム
     ウィンドウとして起動(**長押し**で通常の全画面起動)
   - **⊞ スタート** → 全アプリ一覧 + 検索
   - タスクバーの 📝🧮🕐📊 → 内蔵ツールを何枚でもウィンドウ起動
3. フリーフォーム対応端末(Samsung DeX、または freeform が有効な One UI)では、
   そのままタブレット画面上に独立ウィンドウとして開き、**Windows のように
   複数のアプリを重ねて**使えます。
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
- インストール済みアプリの起動も同じ仕組み:
  `PackageManager#getLaunchIntentForPackage()` + `FLAG_ACTIVITY_NEW_TASK` +
  `setLaunchBounds()`。アプリ一覧の取得には Android 11+ のパッケージ可視性
  (`<queries>` の MAIN/LAUNCHER インテント)を宣言
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
