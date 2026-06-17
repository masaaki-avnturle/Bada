# Bada XP — ChatGPT モバイルアプリ（ダウンロード／APK）

Bada XP（ChatGPT 分派）を**スマホアプリ**として持ち運べるようにしたものです。中身は
`www/` の自己完結 PWA（HTML/JS）で、Ruby 版 `OmegaChat` の中核（シャノン不変量
Ξ＝β(H+1,M+1)/log(N+1)、大域的部分積分多様体、理論テンプレート）を**忠実に移植**し、
**バージョン・ダウングレード**（Fable 5 → ムートス → Opus 4.7 → … → ローカル分派）と、
**任意の本物 LLM 接続**（Anthropic／端末内に鍵を保存）を備えています。

入手方法は 3 つあります。

## 0. URL から APK を直接ダウンロード（GitHub Releases）

GitHub Actions が APK を自動ビルドして Releases に公開します。**安定 URL**:

```
https://github.com/masaaki-avnturle/Bada/releases/latest/download/bada-xp.apk
```

この URL を Android 端末のブラウザで開けば `bada-xp.apk` がダウンロードされます
（「提供元不明のアプリ」を許可してインストール）。リリースは、`v*` タグの push、または
GitHub の Actions タブで **「Build Bada XP APK」→ Run workflow** を実行すると生成されます
（`.github/workflows/build-apk.yml`）。

## 1. すぐ使う：PWA としてインストール（最短）

サーバ不要の純 Ruby 配信を使います。PC とスマホを**同じ Wi-Fi** に繋いで:

```bash
cd bada_ruby
bin/bada serve            # 例: http://192.168.x.x:8787/ が表示される
```

表示された URL をスマホのブラウザ（Android Chrome / iOS Safari）で開き、
メニューから **「ホーム画面に追加」** を選ぶと、アプリとしてインストールされます
（オフラインでもローカル分派で動作）。

> どこでも配るなら、`www/` をそのまま静的ホスティング（GitHub Pages 等）に置けば
> URL を共有するだけでインストール可能な Web アプリになります（HTTPS 推奨）。

## 2. APK を生成する（Android インストーラ）

`www/` を WebView でくるむ Android プロジェクト（`android/`）を同梱しています。

必要なもの: **JDK 17+** / **Gradle 8.7+**（または Android Studio）/ **Android SDK**
（platform-34＋build-tools、`ANDROID_HOME` を設定）。

```bash
cd bada_ruby
bin/bada apk             # = bash mobile/build_apk.sh
# 出力: mobile/android/app/build/outputs/apk/debug/app-debug.apk
adb install -r mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

Android Studio を使う場合は `mobile/android` を開いて Run するだけです。生成された
`app-debug.apk` を端末に転送し（「提供元不明のアプリ」を許可して）インストールします。

## 構成

| パス | 役割 |
|:--|:--|
| `www/index.html` | アプリ本体（エンジン＋UI＋版台帳＋ファイル添付＋本物LLM、自己完結） |
| `www/manifest.webmanifest` / `service-worker.js` | PWA（インストール・オフライン） |
| `www/icon.svg` | アイコン（不変量 Ξ のグリフ） |
| `android/` | WebView ラッパー（Gradle）→ APK |
| `build_apk.sh` | `www` を assets に同梱して `assembleDebug` |

## ファイルのアップロード（OneDrive / 任意ファイル）

下部の **📎** ボタンで、**OneDrive・Google ドライブ・端末**の任意のファイルを添付できます
（Android の WebView から `onShowFileChooser` 経由でシステムのドキュメント・ピッカーを開くため、
OneDrive アプリが入っていればその中のファイルも選べます）。添付後:

- **「送信」**: 添付内容を文脈に含めて質問できます（要約・説明など）。本物の LLM が有効なら
  ファイル本文をプロンプトに添付し、無ければローカル分派が添付の統計（トークン数 N・エントロピー
  H・不変量 Ξ）を踏まえて応答します。
- **「⚙ アプリ生成」**: 添付（と要求文）から、**実行可能な Bada のソースコード**を生成して
  **ダウンロード**できます（`bada lang` で実行可能）。生成アプリの Ξ/H/N は添付ファイルから
  計算した実数が埋め込まれます。本物の LLM が有効なら LLM がコードを生成します。

添付ファイルはアプリ内（端末）でのみ処理され、本物の LLM を使う場合のみ本文が Anthropic に
送られます（鍵が無ければ送信されません）。

## API キーの代わり＝未知事前エンジン（鍵なしの内蔵頭脳）

API キーが無いときは、**未知事前エンジン**が頭脳として働きます。これは
**ガンマ関数の大域的部分積分多様体**で質問を配置し（Ξ＝β(H+1,M+1)/log(N+1)）、
**大脳基底核の熱選択ネットワーク**で応答戦略を選び、**FPGA 回路（Orch-OR 微小管＋NPU）**
や**健全な証明**を端末内で生成します（すべてオフライン・鍵不要）。

- **健全な証明**: 「予想を証明して」→ 決定可能クラスのみ proved／反例は disproved（例：n²−n+41 は n=41 で合成数）／未確定は open。嘘の証明はしません。
- **FPGA 回路生成**: 「FPGA回路を生成」→ 微小管発振器＋NPU MAC の Verilog SoC。
- **情報生成**: 自由質問 → 多様体配置（H・M・N・Ξ・β を実計算）で説明を生成。
- **方程式**: 「方程式」→ β/ζ ゲージ系の式を提示。

さらに、定型文ではない**実用ツール**も同梱（ネット不要）。

- **計算機**: 「2+2」「sqrt(2)」「Γ(7)」「5!」「log2(8)」「beta(2,3)」「(3^4-1)/5」「5の階乗」「3の平方根」
- **要約**: 「要約 〈文章〉」、または 📎 でファイルを添付して「要約」
- **キーワード抽出**: 「キーワード 〈文章/添付〉」
- **文字数・トークン数**: 「文字数 〈文章/添付〉」
- **エントロピー / 不変量 Ξ**: 「エントロピー 〈文章/添付〉」→ H・Ξ・N を実計算
- **Bada/数学の Q&A**: 「Ξとは」「ガンマ関数とは」「Bada とは」など
- **アプリ生成**: 「⚙ アプリ生成」で実行可能な Bada コードを生成・ダウンロード

ヘッダーの engine 表示は鍵なし時「オフライン(計算/解析)」です。本物の AI に切り替えると
「本物:〈model〉」になります。

## 本物の ChatGPT にする（任意）

**既定では応答は「デモ・エンジン（定型文＝テンプレート）」です。** これは鍵が無くても動く
オフラインのフォールバックで、実在の AI ではありません。**本物の AI 応答には、ご自身の API
キーが必要**です（公開アプリに秘密鍵を埋め込むことはできないため）。

手順:
1. 右上 **「設定」** を開く
2. **提供元**を選ぶ（Anthropic = Claude 推奨／OpenAI = ChatGPT・互換）
3. **API キー**を入力（必要ならモデルや OpenAI 互換のベース URL も）
4. **「接続テスト」** で確認（成功/失敗の理由を表示）→ **保存**

これで選択中の版（`local` 以外）で実在の AI が応答します。ヘッダーの `engine` 表示が
`本物:<model>` になります。接続に失敗した場合は**理由を表示**し（HTTP ステータス／CORS／
refusal 等）、その後オフラインのデモ応答に切り替えます（黙ってテンプレートにはしません）。

キーは**この端末の localStorage だけ**に保存され、ブラウザから直接、選んだ提供元へ送られます
（Anthropic は `anthropic-dangerous-direct-browser-access` を使用）。個人利用向けです。共有端末や
配布ビルドに鍵を入れないでください。
