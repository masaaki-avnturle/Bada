# Bada HHKB Pro — フローティング Android キーボード

Happy Hacking Keyboard **Pro** 風のレイアウトを再現し、**画面上を自由にドラッグ
移動できる** Android 12（API 31）対応のソフトウェアキーボード（IME）です。

Esc / Tab / Control / Shift / Alt / Meta(◇) / Fn など特殊キーをすべて搭載し、
Fn レイヤーで矢印・ファンクションキー・ナビゲーションキーも入力できます。

---

## 特長

- **Android の「入力方法（IME）」として登録可能**
  設定 → システム → 言語と入力 → 画面キーボード から有効化できます。
- **HHKB Pro (US) 配列を忠実に再現**（60キー / 5段）。
- **特殊キー一式**：`Esc` `Tab` `Control` `Shift` `Alt` `◇(Meta/Super)` `Fn`
  `Return` `Delete` `Space`。
- **スティッキー修飾キー**：
  - 1回タップ … 次の1キーだけ有効（ワンショット、薄い金色）
  - 2回タップ … ロック（固定、金色反転）
  - 3回タップ … 解除
  これにより `Ctrl+C` などの同時押しを片手・順次タップで実現します。
- **フローティング＆ドラッグ移動**：上部の `⠿ ハンドル` バーをドラッグすると
  キーボードごと画面の好きな位置へ移動。`Dock` ボタンで画面下中央に戻ります。

---

## ビルド方法

> Android SDK（API 31）と JDK 11 が必要です。**Android Studio で開くのが最も簡単**です。

1. Android Studio で `hhkb_android/` フォルダを開く（`File → Open`）。
2. Gradle 同期が完了したら、実機 / エミュレータ（Android 12 推奨）へ Run。

コマンドラインの場合（Gradle 7.3+ がインストール済みなら）:

```bash
cd hhkb_android
gradle wrapper          # 初回のみ gradlew を生成
./gradlew assembleDebug # app/build/outputs/apk/debug/app-debug.apk が生成される
```

---

## 使い方

1. アプリ「**Bada HHKB**」を起動。
2. **① 入力方法の設定を開く** → 『Bada HHKB Pro Keyboard』を ON。
3. **② キーボードを切り替える** → 一覧から Bada HHKB を選択。
4. 任意のアプリの入力欄で HHKB キーボードが表示されます。
   - ハンドルバーをドラッグして移動。
   - `Dock` で下中央へ復帰。

---

## キー配列（HHKB Pro US）

```
 Esc  1! 2@ 3# 4$ 5% 6^ 7& 8* 9( 0) -_ =+ \| `~
 Tab    Q  W  E  R  T  Y  U  I  O  P  [{ ]}   Delete
 Ctrl     A  S  D  F  G  H  J  K  L  ;: '"      Return
 Shift      Z  X  C  V  B  N  M  ,< .> /?    Shift  Fn
 ◇   Alt   [        Space        ]   Alt   ◇
```

### Fn レイヤー早見表

| Fn + キー | 機能 |
|:--|:--|
| `1`〜`9` `0` | F1〜F9, F10 |
| `-` `=` | F11, F12 |
| `[` | ↑ (Up) |
| `/` | ↓ (Down) |
| `;` | ← (Left) |
| `'` | → (Right) |
| `,` | Home |
| `.` | End |
| `]` | Page Up |
| `Space` | Page Down |
| `\` | Insert |
| `Tab` | Caps Lock |
| `Delete` | 前方削除 (Forward Delete) |

> `Ctrl` / `Alt` / `◇(Meta)` を有効にした状態で文字キーを押すと、
> `Ctrl+C` / `Alt+Tab` / `Meta+L` などのキーイベントとしてアプリへ送信されます。

---

## 構成

| ファイル | 役割 |
|:--|:--|
| `HhkbImeService.java` | IME 本体。レイアウト生成・修飾キー処理・キー送信・ドラッグ移動。 |
| `SetupActivity.java` | 有効化案内とキーボード切替ボタンを持つ起動画面。 |
| `res/xml/method.xml` | IME ディスクリプタ（サブタイプ定義）。 |
| `AndroidManifest.xml` | IME サービスと起動 Activity の登録。 |

外部依存なし（Android フレームワークの `InputMethodService` のみ）。
