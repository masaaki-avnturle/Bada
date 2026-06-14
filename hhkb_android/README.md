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
- **日本語入力キー**：`無変換` `変換`、および `あ/A`（日本語⇔英語切り替え）。
  辞書不要のローマ字かな入力を内蔵（詳細は下記）。
- **スティッキー修飾キー**：
  - 1回タップ … 次の1キーだけ有効（ワンショット、薄い金色）
  - 2回タップ … ロック（固定、金色反転）
  - 3回タップ … 解除
  これにより `Ctrl+C` などの同時押しを片手・順次タップで実現します。
- **フローティング＆ドラッグ移動**：上部の `⠿ ハンドル` バーをドラッグすると
  キーボードごと画面の好きな位置へ移動。`Dock` ボタンで画面下中央に戻ります。

---

## APK の入手（ビルド済みパッケージ）

このリポジトリには **GitHub Actions による自動APKビルド**（`.github/workflows/android.yml`）が
含まれており、`hhkb_android/` への push ごとに APK が生成されます。

### ① Actions の成果物からダウンロード（最も簡単）

1. GitHub の **Actions** タブ →「Build HHKB APK」の最新の成功した実行を開く。
2. 画面下部 **Artifacts** の `BadaHHKB-debug-apk` をダウンロード（zip）。
3. zip を展開すると `app-debug.apk` が得られます。

### ② Release から直接ダウンロード

GitHub で **Release を作成**すると、同じワークフローが APK を Release に添付します
（単一ファイルとして直接ダウンロード可能）。

### APK のインストール

1. `app-debug.apk` を Android 12 端末へ転送。
2. 「提供元不明のアプリ／このソースを許可」を有効にしてインストール。
   （デバッグ署名済みなので、そのままインストールできます。）

## 自分でビルドする場合

> JDK 17 と Android SDK（platform 34 / build-tools 34）が必要です。
> Gradle Wrapper を同梱しているので Gradle の事前インストールは不要です。

- **Android Studio**：`hhkb_android/` を開く → Gradle 同期 → Run。
- **コマンドライン**：

```bash
cd hhkb_android
./gradlew assembleDebug   # app/build/outputs/apk/debug/app-debug.apk
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
 ◇  Alt  無変換   [   Space   ]   変換   あ/A   ◇
```

### 日本語入力（変換 / 無変換 / 日英切り替え）

| キー | 動作 |
|:--|:--|
| `あ/A` | 日本語(かな)モード ⇔ 英語モードを切り替え（押すとラベルが あ/A に変化、日本語時は金色） |
| （日本語モードで英字） | ローマ字 → ひらがなにリアルタイム変換（未確定文字列として表示） |
| `変換` | 未確定文字列を **ひらがな → カタカナ → 全角英字** の順に循環変換 |
| `無変換` | 未確定文字列をそのまま **ひらがなで確定** |
| `Space` / `Return` | 未確定文字列があれば確定（無ければ通常のスペース／改行） |
| `Delete` | 未確定文字列があれば1文字削除（無ければ通常の削除） |

- ローマ字例：`nihongo`→にほんご、`konnichiha`→こんにちは、`kya`→きゃ、
  `tte`→って、`gakkou`→がっこう、`pen`→ぺん、`annai`→あんない。
- `ん` は単独 `n`（語末）／`n`＋子音／`nn` で入力できます（例 `shinbun`→しんぶん）。
- `変換`/`無変換` は **未確定文字列が無いとき** は本物の HENKAN / MUHENKAN
  キーイベントを送出するので、他社IMEと併用する物理JISキーボード的な使い方も可能です。
- 辞書を内蔵しないため**漢字変換は行いません**（ひらがな/カタカナ/全角英字の確定変換）。
  漢字が必要な場合は本キーボードで読みを入力し、別途漢字変換IMEと併用してください。

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
