# BADA グラビトン電信 — GRAVITON TELEGRAPH

**ガンマ関数の大域的部分積分多様体 × Jones多項式の量子テレポーテーション × 不確定性原理**を土台に、
**グラビトン↔電磁波変換**によって**携帯電話・固定電話**へ電信通信する **Bada 言語**アプリ。

宛先の電話番号（携帯 070/080/090・固定 03… などを自動判定）とメッセージを入力して送信すると、
アプリ内蔵の **Bada インタプリタが `telegraph.bada` を実行**し、次のパイプラインを駆動します:

1. **符号化** `Tele::encode` — メッセージのシャノンエントロピー H と、ガンマ/ベータ関数による
   大域的部分積分多様体不変量 **Ξ = β(H+1, M+1)/log(N+1)**、およびモールス符号を生成。
2. **量子チャンネル結び目** `Tele::knot n` — **Jones 多項式**（(2,n) トーラス結び目・Kauffman 括弧 TL2）で
   量子通信路の結び目を作り、⟨K⟩ と V(2) を算出。
3. **量子テレポーテーション** `Tele::teleport` — Bell 測定によるテレポート忠実度と、
   **不確定性原理 Δx·Δp ≥ ½ħ** を提示。
4. **グラビトン→電磁波変換** `Tele::graviton` — 重力波ひずみ h を、携帯なら GHz 帯、
   固定電話なら音声帯域（Hz）の**電磁波搬送波**へ変換。
5. **送信** `Tele::send` — 相手の電話（携帯/固定）へ信号がテレポートし、受信文が届く。

キャンバスに、**重力波（+/× 偏光）→ Jones 量子チャンネル → 電磁波搬送波 → 受信電話**の流れを可視化。
モールス音（WebAudio）も鳴ります。画面下の **BADA コンソール**に実行された Bada 命令が表示されます。

> ⚠️ **物理・数式（グラビトン↔電磁波変換・量子テレポーテーション・ガンマ/ベータ・Jones多項式・不確定性関係）は
> 山口フレームワークに基づく創作・思考実験の可視化です。** 一方、次の **⑥ NTT回線・音響通信は実際に動作します。**

---

## 📶 ⑥ NTT回線・音響通信 — アプリ ⇄ スマフォ の実データ送受信

**音響カプラ方式（電信＝音）で、アプリとスマフォが実際に文字データを送受信します。**
メッセージを **FSK 変調音**（音声帯域の2周波：space 1000 Hz / mark 1600 Hz・100 baud）にして鳴らし、
相手側はマイクで**復調**して文字に戻します（フレーム＝プリアンブル＋SOF 0x7E＋長さ＋UTF-8＋チェックサム、
Goertzel 検波の UART 型 FSK）。

- **🔊 音響送信** — 本文を FSK 変調音として再生。
- **🎙 受信開始（マイク）** — マイク入力をリアルタイム復調（`getUserMedia` → Goertzel）。**⏹ 停止してデコード**。

**▶ NTT の回線を介す場合：** アプリのある端末とスマフォで、通常どおり **NTT の電話（音声通話）**をつなぎ、
両方をスピーカーホンにします。送信側で「音響送信」すると、変調音が **NTT の音声回線を通って**相手のマイクへ
届き、復調されます。**同室**ならスピーカー↔マイクで直接。

> ※ アプリ単体で NTT の電話網へ**直接ダイヤルはしません**（通信事業者のゲートウェイ／SIP が必要）。
> 本方式は、実在の NTT 通話の**音声チャンネルにデータを載せる**、実際に動作する音響電信です。
> `Tele::modulate`（送信）・`Tele::listen`（受信）・`Tele::hangup`（停止）として Bada 言語から実行します。

---

## 🅱 Bada 言語で書いた制御（`www/telegraph.bada`）

`bada_ruby` の `Interpreter` と同じ演算子・名前空間文法（`set / <- / -< / >- / Omega::push / print`）を
JS に移植した内蔵インタプリタが実行します。`Tele::` は電信トランスポートの拡張命令です。

```bada
set entropy   = 3.20     # メッセージのエントロピー H（送信時に注入）
set crossings = 5        # Jones ブレイドの交差数 n（送信時に注入）
line <- "graviton electromagnetic teletransport"   # 左作用 π(χ,x)
line -< 1.0                                         # 多様体積分 ∬1/(x·log x)²
line >- line                                        # 右量子作用 e^{-x·log x}
Omega::push line as channel_node                     # Akashic TupleSpace へ
Tele::encode          # 符号化      Tele::knot crossings  # Jones 結び目
Tele::teleport        # 量子転送    Tele::graviton        # グラビトン→電磁波
Tele::send            # 携帯/固定電話へ送信
```

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は **[Releases](../../releases)** および GitHub Actions の Artifacts から。

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `BadaGravitonTelegraph-x.y.z-debug.apk` |
| **Windows 10/11** | `BadaGravitonTelegraph Setup x.y.z.exe`（インストーラ） / `BadaGravitonTelegraph-x.y.z-portable.exe`（ポータブル） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します（完全オフライン）。

---

## 🛠 自分でビルド

```bash
cd bada_telegraph
npm install
npm start                 # Electron でデスクトップ起動
npm run dist:win          # Windows 10/11 用 EXE
npx cap add android && npx cap sync android && cd android && ./gradlew assembleDebug
```

## 🤖 GitHub Actions

`Actions` → **Build Bada Graviton Telegraph** → Run workflow で APK / EXE を自動生成。
タグ `telegraph-v1.0.0` を push すると Releases に添付されます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
