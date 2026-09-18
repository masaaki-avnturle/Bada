# ⚡ Bada UltraNetwork — 家のコンセントから NTT 回線を経て zone:// へ

**Panasonic HD-PLC の技術で家の電力線を物理層にして PC をインターネットにつなぎ、そのフレームを NTT の電話回線に写像し、そこに zone://url.or.jp のウルトラネットワークを通し、LINE と Instagram のメッセージ機能を取り込む — その全部を量子プログラミング言語 Bada で書いた通信システムです。層の組み方は AT&T ベル研究所の STREAMS と同じにしてあります。**

依存ゼロ・単一 HTML・オフライン動作。

---

## 🧩 AT&T ベル研究所と同じ組織化 — STREAMS

層を積む作法は、ベル研究所が UNIX の装置入出力に使った **STREAMS**(Dennis Ritchie の Streams I/O)に倣っています。下端の **driver** と上端の **stream head** の間にモジュールを **push** し、各モジュールは <code>wput</code>(下り)と <code>rput</code>(上り)の対**だけ**を持ちます。上位は下位を知らず、下位は上位を知りません。

```
        stream head   アプリケーション (統合受信箱)
             ↓ wput                    rput ↑
        ┌── msgmux ──┐  L4  LINE / Instagram メッセージ多重化
        ├── jones  ──┤  L3  Jones 多項式量子暗号 (AEAD + Bell 対 QKD)
        ├── zone   ──┤  L2  zone:// ウルトラネットワーク (P2P リング DHT)
        └── ntt    ──┘  L1  NTT 電話回線への写像 φ + 音声帯モデム
             ↓ put                      srv ↑
          driver  plc   L0  Panasonic HD-PLC (家のコンセント)
          ≈≈≈≈≈≈ 家の電力線 2–28 MHz ≈≈≈≈≈≈
```

下りで各層がしたことを、上りで対になる層がちょうど元に戻します。往路と復路を通した結果が**元のメッセージと完全に一致する**ことを、毎回検算しています。

---

## ✨ 各層でしていること

### L0 🔌 Panasonic HD-PLC — 家の電力線を物理層にする

分電盤から各部屋へ伸びる屋内配線を、そのまま通信路として使います。

- **2–28 MHz を 512 本のサブキャリア**に分割(Δf ≒ 50.78 kHz、シンボル長 19.69 µs)
- 変調は QAM ではなく **PAM + ウェーブレット変換**。ガードインターバルが要らないのが HD-PLC 方式の利点で、本実装では**正規化 Haar の多重解像度フィルタバンク**が DWMT の役を務めます(解析と合成は**厳密な逆変換**で、往復誤差は 10⁻¹⁵ 台)
- 電力線の伝達関数は **Zimmermann–Dostert の多重経路モデル**
  H(f) = Σ gᵢ · exp(−(a₀ + a₁ f^k) dᵢ) · exp(−j2πf dᵢ/v)
- 分岐点の**インピーダンス不整合損**は周波数とともに増える(帯域上端ほど損失が大きい)
- 雑音は**色付き背景雑音** N(f)[dBm/Hz] = a + b·f_MHz^c
- SNR から**適応ビットローディング** b = ⌊log₂(1 + SNR/Γ)⌋(Γ は BER 10⁻⁷ 相当のギャップ、上限 5 bit = 32-PAM)
- **アマチュア無線帯 9 本にノッチ**を入れて送信しない
- **IEEE 1901 のフレーム**(プリアンブル + フレーム制御 CRC-24 + 520 バイト PB ブロック CRC-32)
- **CSMA/CA の優先度解決**(PRS0 / PRS1 スロット + 競合窓バックオフ)

コンセント対を選ぶと回線特性が変わります。実測される PHY 速度の例:

| 区間 | PHY 速度 | 平均ビット |
|:---|---:|---:|
| ONU 脇 → 書斎 | 約 122 Mbps | 5.00 bit/本 |
| 居間 → 書斎 | 約 120 Mbps | 4.90 bit/本 |
| 居間 → 台所 | 約 51 Mbps | 2.75 bit/本 |

### L1 ☎ NTT 電話回線への写像

**写像 φ : zone:// アドレス ↦ NTT 番号。**

- リング上の位置 `zone_id` が**市外局番**を決めます(近い zone は近い収容局になる)。加入者番号は URL のハッシュから採ります
- 番号ポータビリティと同じ**割当表**を持つので、**φ⁻¹ は厳密な逆写像**になります(衝突は局内の空き番号を線形探索)
- 0AB-J(10 桁)・050(IP 電話)・090(携帯)に写せ、E.164 形式も出します

**ベアラ(実際に加入者線を通す部分)は 3 種類:**

| 回線種別 | 方式 |
|:---|:---|
| アナログ加入電話(メタル) | 300–3400 Hz の**音声帯 16-QAM ソフトモデム**。fs 8 kHz / 搬送波 2 kHz / 2000 baud / 8000 bps |
| INS ネット 64(ISDN) | B チャネル 64 kbps の**ディジタル透過**(HDLC フラグ) |
| ひかり電話(IP) | **G.711 µ-law** に符号化して **RTP**(PT=0 PCMU / 20 ms)で運ぶ |

音声帯モデムは搬送波が標本化周波数のちょうど 1/4 なので、cos/sin が `{1,0,−1,0}` と `{0,1,0,−1}` という**厳密な直交系**になります。相関復調に近似が入らず、**誤差なしで往復**します。

### L2 🌐 zone:// ウルトラネットワーク WWW

`https:` / `http:` に代わるスキームです。**中央サーバも DNS ルートもありません。**

- アドレスは**ピア自身のハッシュだけ**で作られたリング DHT(位数 4096)が解決します
- 貪欲ルーティング(+1 / −1 / +2 のフィンガ)で担当ピアへ到達します
- 全レコードは追記専用の **アカシック台帳**(tuplespace)にコミットされます
- 既存の [`bada_gui_ide/dist/zone-browser.html`](../bada_gui_ide/dist/zone-browser.html)(ウルトラネットワーク専用ブラウザ)が読む **`@@` ブロック**を出力します。鍵導出・封緘・リングの算法は [`bada_gui_ide/examples/zone.bada`](../bada_gui_ide/examples/zone.bada) と同一なので、**レコードは相互運用できます**(ピアの node-id も Jones 鍵も一致します)

### L3 🔐 Jones 多項式量子暗号

ゾーンの秘密は**結び目そのもの**です。

1. **鍵** — 結び目図の Kauffman ブラケット ⟨D⟩(A) = Σ A^(a−b) d^(loops−1) を複数の A で標本化してハッシュしたものが長期鍵。`url.or.jp` は三葉結び目(交点 3)、`bada.or.jp` は 8 の字結び目(交点 4)で、**異なる結び目は異なる鍵**を与えます
2. **QKD** — セッションソルトは **Bell 対**(H + CNOT + 測定)が合意します。禁止状態 |01⟩,|10⟩ の確率が**厳密に 0** であることが盗聴されていない証拠です。複製不可能定理により盗聴は相関を壊すので、そのときは鍵を破棄し**送信しません**
3. **AEAD** — (結び目鍵, ソルト)を種とする鍵ストリームで暗号化し、鍵付きタグで封緘します。16 bit 符号単位で動くので**日本語も絵文字も往復**します

### L4 💬 LINE / Instagram メッセージ多重化

取り込みは各社が公開している**公式 API の仕様どおり**に行います。

| | LINE | Instagram |
|:---|:---|:---|
| 受信 | Messaging API の Webhook イベント | Instagram Graph API の Webhook |
| 署名 | `X-Line-Signature` = Base64(HMAC-SHA256(channelSecret, 生の本文)) | `X-Hub-Signature-256` = `sha256=` + hex(HMAC-SHA256(appSecret, 生の本文)) |
| 送信 | `/v2/bot/message/reply` · `/v2/bot/message/push` | `/<IG_ID>/messages` |

**SHA-256 と HMAC-SHA256 は本物の実装**です(RFC 4231 のテストベクタで検証しています)。署名検証は定数時間比較で行い、不一致は 401 で拒否します。

> **資格情報について** — 実運用では各プラットフォームで発行した**チャネルシークレット / アクセストークン**が必要です。それが無いこの画面では、公式仕様と同じ形の Webhook 本文を組み立てて**署名経路まで本物を通す**ローカル模擬で動作します。非公開 API の解析や認証の迂回は一切行いません。

---

## 🛡 攻撃はそれぞれ別の層が弾く

| 攻撃 | 弾く層 | 状態符号 |
|:---|:---|:---|
| 回線上の信号を改竄する | L0 HD-PLC の CRC | `503 plc-pb-crc` |
| 電力線を 22 dB 劣化させる | L0 フレーム同期 | `503 plc-no-preamble` |
| 悪意あるピアがレコードを書き換える | L3 Jones AEAD | `409 zone-guard-reject` |
| 別の結び目で開封しようとする | L3 結び目鍵 | `409 zone-guard-reject` |
| 量子路を盗聴する | L3 Bell 対 QKD | `495 quantum-channel-compromised`(**送信そのものを止める**) |
| Webhook の署名を偽造する | L4 HMAC-SHA256 | `401` |

---

## 🚀 使い方

### 1 ファイルをダウンロードして開くだけ

### 👉 [**ultra_network/index.html をダウンロード**](index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要・依存なし・オフライン可)。

画面は 7 つ:

| タブ | 内容 |
|:---|:---|
| 🔌 **コンセント** | コンセント対を選んで回線を測定。SNR とサブキャリア割当ビットのスペクトル、CSMA/CA の競合 |
| ☎ **NTT 回線** | 写像表 φ と φ⁻¹ の検算、呼制御の状態機械、受信コンステレーション |
| 🌐 **zone://** | アドレスを解決。リング DHT の経路図、`@@` ブロック、アカシック台帳 |
| 🔐 **量子暗号** | Kauffman ブラケットの標本、Bell 対の測定、AEAD と 4 種類の攻撃試験 |
| 💬 **メッセージ** | LINE / Instagram の Webhook を受けて統合受信箱へ。署名検証の内訳と公式 API への送信要求 |
| 🧩 **STREAMS** | 層の図とメッセージブロックの流れ。攻撃を選んで 1 通流せる |
| 🧪 **自己診断** | 22 項目をその場で実際に計算して検証 |

### 📱💻 ネイティブ アプリ (APK / Windows 10・11 / Ubuntu)

| プラットフォーム | ファイル | 使い方 |
|:---|:---|:---|
| **Android** (APK) | `bada-ultranetwork-debug.apk` | 端末にコピーして開く(提供元不明のアプリの許可が必要) |
| **Windows 10 / 11** | `BadaUltraNetwork-1.0.0-x64.exe`(NSIS インストーラ)<br>`BadaUltraNetwork-1.0.0-portable.exe`(ポータブル) | インストーラは実行してインストール。ポータブル版はそのまま実行 |
| **Ubuntu** | `BadaUltraNetwork-1.0.0-x86_64.AppImage`<br>`BadaUltraNetwork-1.0.0-amd64.deb` | AppImage は `chmod +x` して実行。deb は `sudo apt install ./BadaUltraNetwork-*-amd64.deb` |

#### 🔽 GitHub Actions からダウンロードする

1. リポジトリの **[Actions タブ](https://github.com/masaaki-avnturle/Bada/actions/workflows/ultranet-app-build.yml)** を開く
2. **Bada UltraNetwork app build** の最新の実行(緑チェック)を選ぶ
3. ページ下部の **Artifacts** から取得する

| アーティファクト名 | 中身 |
|:---|:---|
| `ultranet-android` | APK |
| `ultranet-windows` | Windows の EXE 2 種 |
| `ultranet-linux` | AppImage と deb |

> Artifacts は zip で降ってくるので、展開してから実行してください。
> ダウンロードには GitHub へのログインが必要です(Actions の仕様)。
> 保存期間は既定で 90 日です。

ビルドは [`ultranet-app-build.yml`](../.github/workflows/ultranet-app-build.yml) が実行します。トリガーは 3 つ — 開発ブランチへの push(Actions アーティファクト)/ `workflow_dispatch`(ワークフローが既定ブランチに入ってから)/ `ultranet-v*` タグ([Releases](https://github.com/masaaki-avnturle/Bada/releases) へ添付)。

---

## 📜 Bada 言語による全ソースコード

**この通信システムは、全層を量子プログラミング言語 Bada 自身で書いてあります。** JavaScript 版(`index.html`)は同じ算法をブラウザで動かすためのもので、Bada 版が本体です。

### 📕 PDF — 全ソースコードを 1 冊に

### 👉 [**BadaUltraNetwork-source.pdf**](dist/BadaUltraNetwork-source.pdf)

表紙・目次・層の図に続けて、**12 ファイル 4,722 行**の全ソースを行番号つき・色分けで収録した **71 ページ**の PDF です(A4)。生成は `node ultra_network/tools/build-pdf.js`。

### 📂 モジュール構成 — `bada/`

| | ファイル | 内容 | 行 |
|---:|:---|:---|---:|
| 01 | [`01_core.bada`](bada/01_core.bada) | 基本演算 — 床関数・三角関数・**ニブル表によるビット演算**・16 進 / Base64 / UTF-8・32 ビット乗算・擬似乱数 | 432 |
| 02 | [`02_sha256.bada`](bada/02_sha256.bada) | **SHA-256 / HMAC-SHA256**(RFC 6234 / RFC 2104) | 198 |
| 03 | [`03_jones.bada`](bada/03_jones.bada) | L3 Jones 多項式量子暗号 — Kauffman ブラケット・Bell 対 QKD・AEAD | 206 |
| 04 | [`04_zone.bada`](bada/04_zone.bada) | L2 zone:// — URL 文法・リング DHT・アカシック台帳・`@@` ブロック・封筒 | 267 |
| 05 | [`05_ntt.bada`](bada/05_ntt.bada) | L1 NTT 写像 — φ と割当表・音声帯 16-QAM・G.711 µ-law・RTP・ISDN・呼制御 | 362 |
| 06 | [`06_plc.bada`](bada/06_plc.bada) | L0 HD-PLC — 多重経路伝達関数・適応ビットローディング・ウェーブレット OFDM・CRC-32/24・IEEE 1901・CSMA/CA | 518 |
| 07 | [`07_json.bada`](bada/07_json.bada) | JSON の再帰下降パーサと生成器(Webhook 本文用) | 321 |
| 08 | [`08_msgmux.bada`](bada/08_msgmux.bada) | L4 LINE / Instagram — 公式 API の取り込み・署名検証・送信要求・統合受信箱 | 308 |
| 09 | [`09_streams.bada`](bada/09_streams.bada) | AT&T ベル研究所式 STREAMS — wput / rput の対と全 5 層の往復 | 364 |
| 10 | [`10_main.bada`](bada/10_main.bada) | デモ本体 — `@reviser` で `SEND` / `LINK` を parser に足す | 188 |
| 11 | [`11_selftest.bada`](bada/11_selftest.bada) | 自己診断 **107 項目**(全合格) | 387 |
| 12 | [`ultra.bada`](ultra.bada) | 単一ファイル版(64 サブキャリアの縮小版) | 1171 |

### ▶ 走らせる

Bada にモジュール読み込みの仕組みは無いので、実行時は順に**連結して 1 本**にします。

```sh
# モジュールを連結し、実際に走らせて検査してから dist/ に書き出す
node ultra_network/tools/build-bada.js

# 出来上がった全層プログラムを走らせる
node ultra_network/tools/run-bada.js ultra_network/dist/ultra-full.bada
node ultra_network/tools/run-bada.js ultra_network/dist/ultra-selftest.bada

# 縮小版はそのまま bada-cli で動く
node bada_gui_ide/cli/bada-cli.js run ultra_network/ultra.bada
```

`build-bada.js` は出力に決められた印(`STATUS 200 zone-delivered` / `409` / `495` / `503` / `inverse ok: true` / `SELFTEST-RESULT 107 107`)が揃うまで `dist/*.bada` を書き出しません。

### ⚠ Bada で書くうえで踏んだところ

| | 対処 |
|:---|:---|
| **ビット演算子が無い** | 4 ビット(ニブル)の XOR / AND / OR 表を起動時に作り、32 ビット語を 8 ニブルに割って引く。SHA-256 の `ch` / `maj` はニブル 1 パスに融合 |
| **`\|\|` が無い** | `&&` と `!`、または入れ子の `if` で書く |
| **`for x in arr` が束縛されない** | `while` で回す |
| **`def` の中の `:=` は局所変数** | 書き換えたい値は配列の要素に置く(要素への代入は呼び出し側に届く) |
| **行頭の `[` は前行の添字と読まれる** | 台帳への追記は一度変数に束ねてから `>> tuplespace` |
| **`a * b` が 2^53 を超えると精度を失う** | `u_mul32` で 16 ビットずつに割って正確に計算(JS の `Math.imul` と同値) |
| **既定のステップ上限 2000 万** | 全層版は約 6,600 万ステップ要る(SHA-256 と HMAC をソフトウェアのビット演算で回すため)。`run-bada.js` で上限を上げる |

### 🔗 JavaScript 版との相互検証

Bada 版と `index.html` の JS 版は**同じ擬似乱数(FNV-1a + xorshift32、定数まで同一)**を使うので、同じ回線特性を出します。実測:

| コンセント対 | Bada 版 | JS 版 |
|:---|---:|---:|
| 居間 → 書斎 | 120.30 Mbps / 有効 483 本 / 2369 bit/シンボル | 同一 |
| ONU 脇 → 書斎 | 122.48 Mbps / 有効 483 本 / 2412 bit/シンボル | 同一 |
| 居間 → 台所 | 50.83 Mbps / 有効 364 本 | 50.78 Mbps / 有効 363 本 |

3 組目だけ 512 本中 1 本ずれます。`floor(log2(1 + SNR/Γ))` の閾値ちょうどに乗ったサブキャリアが、`Math.log2` と `log(x)/ln2` の丸め差で反対側に倒れるためで、両者とも正しい計算です。

結び目鍵(三葉 919492 / 8 の字 400638)とピアの node-id は既存の [`bada_gui_ide/examples/zone.bada`](../bada_gui_ide/examples/zone.bada) と一致するので、**ここで作ったレコードは ZoneBrowser がそのまま開けます**。

---

## 🧪 テスト

```sh
node ultra_network/tools/engine-test.js
```

**115 項目**を検証します(すべて合格):

1. **SHA-256 / HMAC-SHA256** — 既知答えと **RFC 4231 のテストベクタ #1・#2・#3・#6**、Base64、UTF-8 往復、**壊れた UTF-8 を投げずに吸収すること**(回線から来るバイト列は攻撃者に触られうるため)
2. **署名検証** — LINE と Instagram、正しい秘密は通り、誤った秘密・1 文字違いの本文は落ちる。送信要求が公式仕様の形であること
3. **HD-PLC** — ウェーブレット変換の厳密な逆変換、近いコンセントほど高 SNR、ノッチにビットを割り当てない、**ウェーブレット OFDM の完全往復**、設計 SNR では誤らず 22 dB 劣化させると誤る、CRC-32 / CRC-24 / プリアンブルの各破損検出、CSMA/CA の優先度
4. **NTT 写像** — **φ⁻¹ が厳密な逆写像**、番号の安定性と桁数、衝突時の線形探索、**メタル / ISDN / ひかり電話の 3 ベアラすべてで往復**、RTP の順序入替えからの復元、µ-law の量子化誤差が判定余裕の内側
5. **zone://** — 文法、リング DHT の到達性、`@@` ブロックの相互運用、封筒の符号化
6. **Jones 量子暗号** — 結び目ごとに異なる鍵、AEAD の往復(CJK + 絵文字)、改竄・タグ偽造・鍵違いがすべて 409、Bell 対の零保存と盗聴検出
7. **STREAMS** — **全 5 層を通した往復が完全一致**、下りと上りが各層を 1 回ずつ通ること、3 種の回線 × 3 種のコンセント対、4 種の攻撃がそれぞれ正しい状態符号で排除されること、LINE と Instagram が 1 つの受信箱に同居すること

---

## 📁 構成

```
ultra_network/
├── README.md                  # この文書
├── index.html                 # アプリ本体 (自己完結・依存ゼロ・オフライン可)
├── ultra.bada                 # 単一ファイル版の Bada 実装 (縮小版)
├── bada/                      # ★ 全層の Bada ソース (12 ファイル 4,722 行)
│   ├── 01_core.bada           #   基本演算・ビット演算・UTF-8
│   ├── 02_sha256.bada         #   SHA-256 / HMAC-SHA256
│   ├── 03_jones.bada          #   L3 Jones 多項式量子暗号
│   ├── 04_zone.bada           #   L2 zone:// リング DHT
│   ├── 05_ntt.bada            #   L1 NTT 写像・音声帯モデム・RTP
│   ├── 06_plc.bada            #   L0 HD-PLC ウェーブレット OFDM
│   ├── 07_json.bada           #   JSON 解析・生成
│   ├── 08_msgmux.bada         #   L4 LINE / Instagram
│   ├── 09_streams.bada        #   STREAMS の骨組み
│   ├── 10_main.bada           #   デモ本体
│   └── 11_selftest.bada       #   自己診断 107 項目
├── dist/                      # 生成物 (build-bada.js / build-pdf.js が作る)
│   ├── BadaUltraNetwork-source.pdf   # ★ 全ソースコードの PDF (71 ページ)
│   ├── ultra-full.bada        #   連結済みデモ本体
│   ├── ultra-selftest.bada    #   連結済み自己診断
│   └── *.out.txt              #   それぞれの実行結果
├── tools/
│   ├── engine-test.js         # JS エンジンの単体テスト (115 項目)
│   ├── build-bada.js          # Bada モジュールの連結と検証
│   ├── run-bada.js            # ステップ上限を上げて .bada を走らせる
│   └── build-pdf.js           # 全ソースコードの PDF を組む
└── app/
    ├── cordova/config.xml     # Android APK の設定
    └── electron/              # Windows EXE / Ubuntu AppImage・deb のラッパー
        ├── main.js
        ├── preload.js
        └── package.json
```

`app/www/` はビルド時に `index.html` から生成されるので、リポジトリには入れていません。

---

## 📚 関連

- [`bada_gui_ide/examples/zone.bada`](../bada_gui_ide/examples/zone.bada) — zone:// スキームの元になった Bada 実装
- [`bada_gui_ide/dist/zone-browser.html`](../bada_gui_ide/dist/zone-browser.html) — ウルトラネットワーク専用ブラウザ(本システムの `@@` ブロックと相互運用)
- [`bada_quantos/`](../bada_quantos/) — 擬似量子 OS(BB84 量子鍵配送・トポロジー写像)
