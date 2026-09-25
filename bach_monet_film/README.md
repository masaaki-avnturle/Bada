# 🎼 Bada Contrapunctus — 未完のフーガ × 祈るカミーユ 動画工房

**楽曲ファイルを J.S. バッハ「コントラプンクトゥス XIV(未完)」の気配に編曲し、オーケストラのような平行トラックで作曲・編集して、クロード・モネ風の筆致で描いた「祈りを捧げるカミーユ」の動画に仕立てるソフト。** 依存ゼロ・単一 HTML・完全オフライン動作。Android APK / Windows 10・11 / Ubuntu のアプリとしても配布します。

## ✨ できること

- **どの拡張子の楽曲でも取り込み** — MP3 / WAV / AIFF / FLAC / OGG / Opus / M4A / AAC / WMA / WebM / MP4 … ブラウザが復号できる音声はすべて。復号できなかった WAV / AIFF は自前の PCM パーサ(8/16/24/32 bit, float, EXTENSIBLE, 80-bit 浮動小数のサンプルレート)で読み、**MIDI (.mid)** は音符として「取り込んだ MIDI」トラックに載せます(拡張子は見ません)
- **調性解析と移調** — クロマ × Krumhansl–Schmuckler 調プロファイルで調を判定し、短調なら **D 短調**、長調なら平行長調の **F 長調**(どちらも ♭1 = バッハの声部と同じ調号)へ、位相ボコーダ + 再標本化で**長さを変えずに**移調
- **大聖堂の残響** — 合成インパルス応答(RT60 ≈ 3.8 s、初期反射 6 本、時間とともに高域が減る)による畳み込み残響
- **コントラプンクトゥス XIV の対位法** — 第 1 主題(D–A–F–D–C♯–D …)/ 第 2 主題(走句)/ 第 3 主題 **B–A–C–H** を、アルト → ソプラノ(5 度上の応答)→ バス → テノール の順に主題提示と応答で重ねる 4 声のオルガン声部
- **未完の終止** — 自筆譜が第 239 小節で途切れるように、曲の 90 % の地点で**全声部を途中で断ち切る**。映像ではその瞬間から絵が剥がれて画布と下描きだけが残る
- **平行ミックス画面(オーケストラ)** — **11 行**の平行トラック(元の音楽 + オルガン 4 声 + 弦楽 / 合唱 / フルート / チェンバロ / コントラバス / ティンパニ)。各行に 楽器・役割・**トラック固有のコード進行**・音量・定位・ミュート・ソロ・タイムライン
- **コード進行から平行に演奏** — `Dm | Gm A7 | B♭maj7 | …` のように小節を `|` で区切って書くと、各トラックが役割(**持続和音 / 分散和音 / 低音 / 旋律 / 拍打ち**)に従って同じ進行を平行に演奏。空欄なら調から自動生成(短調: i–iv–V–i–VI–iv–V7–i)
- **作曲・編集** — 行をクリックするとピアノロール(C2–C7 × 拍)が開き、クリックで音符を置く / 消す。音符の長さ(1/2・1・2・4 拍)と強さを指定。役割からの生成し直し、全消去、トラックの追加・削除・改名
- **保存** — 動画(MP4 / WebM)、編曲後の音声(WAV)、**MIDI(format 1、楽器ごとのプログラムチェンジ付き)**、プロジェクト(JSON: コード進行 + 全トラック + 設定)、静止画(PNG)
- **9 種の楽器** — オルガン / 弦楽 / 合唱 / フルート / オーボエ / チェンバロ / ハープ / コントラバス / ティンパニ(加算合成 + 包絡 + フィルタ + ビブラート、ティンパニはピッチ下降の打撃 + ノイズ)
- **祈るカミーユ** — 下絵(窓・蝋燭・祈祷台・芥子の花・跪く白いドレスの女性)から色と輪郭勾配を標本化し、大 → 中 → 細の 1 万本超の筆致を輪郭に沿って置く印象派レンダリング。光は編曲後の音量包絡に呼吸し、声部の入りで光がうねる。冒頭は顔から外へ描き進み、断ち切りの後は外から顔へ向かって絵が消える

## 🎥 出力形式

環境が対応していれば **MP4 (H.264 + AAC)**、それ以外は **WebM (VP9/VP8 + Opus)**。ブラウザ版の変換は **リアルタイム録画**(曲の長さと同じ時間)。決定的な書き出し(同じ入力 → 同じ動画)は下の `tools/render.js` で。

## 🚀 使い方

1. [`index.html`](index.html) を「Download raw file」で保存 → ダブルクリック(インストール不要)
2. 楽曲をドロップ → 調性が表示される → コード進行を書く(または「調から自動」)→ ミュート(M)を外して楽器を鳴らす → 行をクリックしてピアノロールで編集
3. **🎼 編曲**(数秒)→ **▶ 試聴** → **🎬 動画に変換** → **💾 動画を保存**(🎵 WAV / 🎹 MIDI / 📁 プロジェクト も保存できます)

または [Releases](https://github.com/masaaki-avnturle/Bada/releases) / [Actions](https://github.com/masaaki-avnturle/Bada/actions/workflows/contrapunctus-app-build.yml) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-contrapunctus-debug.apk` |
| **Windows 10 / 11** | `BadaContrapunctus-*-x64.exe`(NSIS インストーラ)/ `BadaContrapunctus-*-portable.exe` |
| **Ubuntu** | `BadaContrapunctus-*-x86_64.AppImage` / `BadaContrapunctus-*-amd64.deb` |

ビルドは [`contrapunctus-app-build.yml`](../.github/workflows/contrapunctus-app-build.yml) が実行します(`bach_monet_film/` への push と `workflow_dispatch` で Actions アーティファクト、`contrapunctus-v*` タグ / `release_tag` 指定で Release に添付)。Actions → 該当の実行 → 画面下の **Artifacts** から `contrapunctus-android` / `contrapunctus-windows` / `contrapunctus-linux` をダウンロードしてください。

## 🎬 作例 — `works/`

アップロードされた 2 本の録音(F 短調と判定 → D 短調へ −3 半音)を、既定の編曲(オルガン 4 声 + 大聖堂残響 + 未完の終止)で仕立てたもの。`tools/render.js` で決定的に書き出しています。

| ファイル | 内容 |
|:---|:---|
| `works/20260920_154001 (Contrapunctus XIV).mp4` / `.m4a` | 録音 1(1:13)→ 動画 1:18(1280×720, 30 fps)/ 編曲後の音声 |
| `works/20260920_154118 (Contrapunctus XIV).mp4` / `.m4a` | 録音 2(1:20)→ 動画 1:25 / 編曲後の音声 |

## 🖥 決定的な書き出し — `tools/render.js`

```
npm i playwright-core            # Chromium は既存のものを CHROMIUM= で指定可
FFMPEG=/path/to/ffmpeg node bach_monet_film/tools/render.js input.mp3 out.mp4 \
    --w 1920 --h 1080 --fps 30 --title "曲名" --audio-out out.m4a [--no-transpose --voice 0.55 --reverb 0.5 --tempo 72 --finished]
```

ヘッドレス Chromium で `index.html?headless=1` を開き、`window.__fuga`(load → arrange → setup → frame)で 1 フレームずつ JPEG を描いて ffmpeg(libx264 + aac)に流し込みます。入力は ffmpeg で一度 WAV にするので、Chromium が AAC を復号できなくても構いません。

## ⚙ 仕組み

1. **取り込み** `decodeAny`: `decodeAudioData` → 失敗なら `decodeWav` / `decodeAiff` → 先頭が `MThd` なら `decodeMidi`(可変長数量・ランニングステータス・テンポメタ)
2. **解析** `detectKey`: 4096 点 STFT → 55–2200 Hz のビンを音名に集計 → 24 の調プロファイルと相関
3. **移調** `pitchShift`: `timeStretch`(位相ボコーダ, N=4096, 真の周波数推定)→ 折返し抑制のローパス → `resample`(4 点 Hermite)
4. **譜面** `planScore`: 曲長 × 90 % を 42 % / 24 % / 34 % に分け、主題ごとに半分の長さ間隔で 4 声が入る。最後の主題は cutoff で切る
5. **作曲** `generateRoleNotes`: コード進行(`parseProgression` / `chordAt`)と役割から拍単位の音符を生成。`voicing` は基準音付近のクローズボイシング
6. **合成** `arrangeTrack`: `OfflineAudioContext` に 元の音楽(HPF 70 Hz / LPF 9 kHz / フェード)+ 各トラック(`playNote`: PeriodicWave × 2 デチューン、ADSR、LPF、ビブラート LFO、ブレス)→ 定位 → マスター(tanh ソフトリミッタ)+ 畳み込み残響
7. **絵** `buildPainting`: 480 px の下絵 → `buildStrokes`(勾配で向き、顔からの距離で順位)→ 12 段の累積レイヤ(下塗り + 筆致)/ 麻布 / 下描き / ゆらぐ筆致 → `drawFrame` が完成度・音量包絡・声部の入りに応じて描く
8. **録画** `canvas.captureStream` + `MediaStreamAudioDestinationNode` → `MediaRecorder`

## 🧪 テスト

```
node bach_monet_film/tools/engine-test.js
```

FFT、調性解析(合成クロマ・合成波形)、移調量の選択、位相ボコーダ(移調後の周波数と長さ)、残響 IR、譜面計画(応答の 5 度、未完の断ち切り)、音量包絡、WAV / AIFF(16/24 bit)の往復、コード記号・進行、役割ごとの音符生成(和声音のみ・決定性・トラック固有進行)、MIDI の往復、整形・録画形式を Node 単体テストで検証します。

## 📖 メモ

- モネに「祈るカミーユ」という作品は存在しません。妻カミーユ・ドンシューを描いた連作(『緑衣の女』『日傘をさす女』『死の床のカミーユ』)への敬意として、本作は完全に手続き的に生成したオマージュです。
- 自筆譜の末尾には C. P. E. バッハの手で「BACH の名が対主題に現れるこのフーガの途中で、作曲者は世を去った」と書き込まれています(BWV 1080/19)。映像の最後の一文はこれです。
