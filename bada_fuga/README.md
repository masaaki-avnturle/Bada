# 🎼 Contrapunctus BADA — Fuga a tre soggetti (ニ短調)

アップロードされた 7 つの音源を解析し、そこから得たモチーフを主題として
J.S.バッハ《フーガの技法》**コントラプンクトゥス XIV (BWV 1080/19)** 風の
**三重フーガ**を自動作曲・合成し、ピアノロール動画 (mp4) にしたもの。

- 🎬 **[fuga.mp4](fuga.mp4)** — 5 分 29 秒 · 1280×720 · 30fps · AAC 192 kbps
- 🎵 演奏: 加算合成オルガン風 4 声 (Soprano / Alto / Tenore / Basso) + 合成リバーブ

## 素材 → 主題 の対応

| 素材 | 解析結果 (推定調 / テンポ) | 使いどころ |
|:--|:--|:--|
| MOTHER (LUNA SEA) | ホ短調 / ♩≈68 | **主題 I** — サビの旋律輪郭 (E F# G G# G F# G A …) をニ短調へ移して `D E F F# G A G F E D C# D` |
| トラック 18 | ニ短調 / ♩≈123 | **主題 II** — 反復音 + 順次進行の音型 (D D D D E / A A A G# G) → `F F F G A A G F / D A A A …` |
| 録音 20260922_090933 | ロ短調 / ♩≈63 | **主題 III** の後半 — 半音の隣接音型 (C B C A A# B) → `B♭ A G# A` |
| — | — | **主題 III** の頭は **B-A-D-A** (ドイツ音名: B♭ A D A) = このリポジトリ名。バッハの B-A-C-H に倣った署名主題 |
| LOVELESS (LUNA SEA) | ト長調 / ♩≈161 | エピソードの隣接音型 (G B A B G …) |
| トラック 17 | イ短調 / ♩≈172 | エピソードの上行音階 + 半音下行 (B C D E D# D) |
| トラック 8 | イ短調 / ♩≈99 | ため息音型 F–E (= ニ短調の B♭–A) |
| 録音 20260922_090146 | ト長調 / ♩≈96 | 半音の揺れ (A# C A# G#) → 隣接音の装飾 |

※ 元音源の音そのものは一切使っていない。旋律解析 (pyin) とクロマ解析から
得た音高の輪郭・音型・調性だけを材料に、まったく新しい 4 声の対位法曲として書き起こした。

## 構成 (130 小節, ♩=96)

| 小節 | 内容 |
|:--|:--|
| 1–44 | **第 I 部** 主題 I の 4 声提示 (A → S 答唱 → B → T 答唱) · エピソード · S の再提示 · T の下属調 (ト短調) 提示 |
| 45–85 | **第 II 部** 主題 II の提示 · 主題 I + II の二重結合 ×3 (B+S / イ短調で S+T の転回 / A+B) |
| 86–126 | **第 III 部** B-A-D-A 主題の提示 · **三主題の三重結合** ×3 (ニ短調 → イ短調 → ニ短調) |
| 127 | 休止 — バッハの自筆譜が第 239 小節で途切れる箇所へのオマージュ |
| 127–130 | コーダ: D ペダル上の Gm/D → B♭/D → A7 → **D 長三和音 (ピカルディ終止)** |

## 🕯 Requiem BADA — 荘厳で催眠的なレクイエム版

同じ三重フーガを、遅いテンポ (♩=66) の上で合唱+オルガンの音色・弔鐘・ドローン・大聖堂リバーブに
包み直し、前後に聖歌とマントラ部を加えた版。

- 🎬 **[requiem.mp4](requiem.mp4)** — 9 分 49 秒 · 1280×720 · 30fps

| 小節 | 内容 |
|:--|:--|
| 1–12 | **I. Introitus** — D のドローンと弔鐘の上に、グレゴリオ聖歌「ディエス・イレ」の冒頭句 (テノール) と B-A-D-A の唱え (アルト) |
| 13–142 | **II. Kyrie (Fuga)** — 三重フーガ本体。4 小節ごとに遠くの鐘が催眠的に打たれ、ニ短調の三重結合ではドローンが戻る |
| 143–158 | **III. Lux aeterna — Mantra** — D ペダルの上で B-A-D-A を 8 回反復し、鐘の残響とともに消えていく |
| 159–160 | D 長三和音 (ピカルディ終止) と最後の鐘 |

```bash
python3 compose_requiem.py score_requiem.json
python3 synth.py score_requiem.json requiem.wav
python3 video.py score_requiem.json requiem.wav requiem.mp4
```

- 合唱音色は母音「ア」のフォルマント (730/1090/2440/3400 Hz) で倍音を整形し、3 本のデチューン+ビブラートで重ねたもの。
- 弔鐘は非整数倍音 (0.56, 0.92, 1.19, 1.71, 2.0, 2.74 …) の減衰和で合成。ドローンは D1/D2 の倍音にゆっくりした揺れを付けたもの。

## 🕯🕯 Requiem BADA II — 荘厳な洗脳のレクイエム

レクイエム版をさらに催眠的にした版。全曲を通して心拍のような低い脈拍と弔鐘が続き、
B-A-D-A のマントラがフーガの各部の間に回帰句として戻ってくる。合唱は暗い母音「オ」。

- 🎬 **[requiem2.mp4](requiem2.mp4)** — 11 分 09 秒 · 1280×720 · 30fps

| 小節 | 内容 |
|:--|:--|
| 1–12 | **I. Introitus** — ドローン・心拍・弔鐘の上に、Requiem aeternam 風の聖歌 (S)、ディエス・イレ (T)、B-A-D-A の唱え (A) |
| 13–56 | **II. Kyrie** — 三重フーガ 第 I 部 (主題 I) |
| 57–64 | **Ritornello — Mantra I** — B-A-D-A の回帰句 (アルト → ソプラノ)、心拍と鐘 |
| 65–105 | 第 II 部 (主題 II と二重結合) |
| 106–113 | **Ritornello — Mantra II** — B-A-D-A の回帰句 (テノール → アルト) |
| 114–158 | 第 III 部 (B-A-D-A 主題と三重結合、休止、ピカルディ終止) |
| 159–182 | **III. Lux aeterna — Mantra ×12** — 声部交替でマントラを 12 回反復、うねる強弱で鐘の残響へ消える |

```bash
python3 compose_requiem2.py score_requiem2.json
python3 synth.py score_requiem2.json requiem2.wav
python3 video.py score_requiem2.json requiem2.wav requiem2.mp4
```

- 心拍は 80→38 Hz へ落ちる正弦波 + 短いノイズ。前奏・回帰句・コーダでは 1・3 拍目、フーガ中は各小節の 1 拍目に弱く。
- `compose.build_fugue(P, off, gaps)` でフーガ本体の第 II 部・第 III 部の前に回帰句用の隙間を空けている。

## 🎹 Requiem BADA III — Grave, for Grand Piano (à six mains et plus)

レクイエムを ♩=44 の極めて遅いテンポ (Grave) でグランドピアノ独奏に書き直した版。
フーガより安心感のある響き (分散和音のうねり、ニ長調への帰着) を保ちながら、
4 声のフーガの上下に 3 つの層を重ねて **7 層 (4 本の手を超える)** の多層書法にした。

- 🎬 **[piano.mp4](piano.mp4)** — 10 分 12 秒 · 1280×720 · 30fps

| 層 | 内容 |
|:--|:--|
| S / A / T / B | 三重フーガ (第 I 部 と、エピソード 7 以降の三重結合 ×3・休止・ピカルディ を抜粋) |
| H 鐘のカノン | 高音域 (B♭6 A6 D7 A6) で B-A-D-A を全音符で唱え、2 小節遅れに追走が重なる。フーガ中は 4 小節ごとに D7 の鐘 |
| W 分散和音 | 各拍の和音を 8 分音符で上下に洗い流す層 (安心感の源) |
| L 低音の心拍 | 和音の根音を C1〜B1 のオクターヴで打つ心拍 |

| 小節 | 内容 |
|:--|:--|
| 1–8 | **I. Introitus** — ニ長調と短調のあいだで、聖歌 Requiem aeternam と B-A-D-A |
| 9–52 | **II. Fuga** — 主題 I の 4 声フーガ (第 I 部) |
| 53–60 | **Ritornello** — B-A-D-A の回帰句 (中声の唱え + 鐘のカノン) |
| 61–93 | **III. Fuga a tre soggetti** — 三重結合 ×3、休止、ピカルディ |
| 94–111 | **IV. Lux aeterna** — B-A-D-A → ニ長調の B♮-A-D-A へ移り、鐘のカノンの中で消える |

```bash
python3 compose_piano.py score_piano.json
python3 synth.py score_piano.json piano.wav
python3 video.py score_piano.json piano.wav piano.mp4
```

- ピアノ音色: 弦の剛性による非整数倍音 (f_k = k·f₀·√(1+Bk²))、倍音ごとの二段減衰、2 本弦のうなり、
  ハンマー雑音、低音の胴鳴り、ペダルによる長い離鍵減衰を加算合成で再現。音高に応じて左右に定位。

## 🎼 Requiem BADA IV — Lamento (♩=36, 木琴シンセ + グランドピアノ)

ピアノ版の高音層を木琴系シンセサイザーに置き換え、テンポを ♩=36 まで落とし、
「悲しい出来事を想起させる」レクイエム・フーガにした版。悲しみの核は古来の **嘆きのバス**
(D C# C B B♭ A の半音下行) によるパッサカリアで、前奏・回帰句・終結に置いた。
ピカルディ終止を捨て、短調のまま空虚 5 度 (D–A) と木琴の残響で終わる。

- 🎬 **[lamento.mp4](lamento.mp4)** — 9 分 27 秒 · 1280×720 · 30fps

| 小節 | 内容 |
|:--|:--|
| 1–6 | **I. Introitus — Lamento** — 嘆きのバス ×2 周期、木琴シンセの刻み、B-A-D-A の唱えと木琴のカノン |
| 7–38 | **II. Fuga** — 主題 I の 4 声フーガ (第 I 部前半) |
| 39–44 | **Ritornello — Lamento** — 嘆きのバスの回帰、B-A-D-A をテノール → アルト |
| 45–70 | **III. Fuga a tre soggetti** — 三重結合 ×3、最後の休止で途切れる |
| 71–84 | **IV. Lacrimosa — Passacaglia** — 嘆きのバス ×4、B-A-D-A が声部を渡り、次第に消える |

```bash
python3 compose_lamento.py score_lamento.json
python3 synth.py score_lamento.json lamento.wav
python3 video.py score_lamento.json lamento.wav lamento.mp4
```

- 木琴シンセ: 木琴の非整数倍音 (1 : 3.93 : 9.5) の速い減衰に、正弦波の持続成分 (弱いトレモロ付き) を重ねたもの。
  高音の鐘 (H) は明るめ、刻み (W) は柔らかめの倍音構成。

## 🎹🎛 Requiem BADA V — Dolore (B♭ minor, ♩=36, ピアノの点描 + 電子シンセの不協和音)

Lamento 版から木琴シンセを外し、ピアノ演奏に戻した版。電子シンセサイザーは
根音 + 短 2 度 + 三全音 + 長 7 度 の **不協和音クラスター**を各小節で持続させ、
ピアノは各音符を半分の長さで切って間を空ける (点描)。その隙間をシンセの持続と 4.5 秒の残響がつなぎ、
離れているのに繋がっている悲哀感をつくる。全体を **B♭ 短調**へ移調 (B-A-D-A は G♭-F-B♭-F)。

- 🎬 **[grief.mp4](grief.mp4)** — 9 分 27 秒 · 1280×720 · 30fps

| 層 | 内容 |
|:--|:--|
| S / A / T / B | フーガ + 嘆きのバス (ピアノ、点描) |
| H | 高音の B-A-D-A (ピアノ、点描) |
| C | 電子シンセの不協和音クラスター (3 本のデチューン鋸歯波、遅い立ち上がり、ゆっくりした揺れ) |
| L | 低音オクターヴ (ピアノ) |

構成は Lamento 版と同じ (Introitus → Fuga → Ritornello → Fuga a tre soggetti → Lacrimosa)。

```bash
python3 compose_grief.py score_grief.json
python3 synth.py score_grief.json grief.wav
python3 video.py score_grief.json grief.wav grief.mp4
```

## 🎹 Requiem BADA VI — Elegia (B♭ minor, ♩=36, ピアノ独奏・シンセ不使用)

Dolore 版からシンセサイザーを完全に外し、ピアノ独奏だけにした版。
高音の B-A-D-A は B♭5–D6 に下げて長く保ち、打鍵雑音を抑え減衰を長くして木琴に聞こえないようにした。
音符の間は点描ではなく、ペダルの共鳴 (長い離鍵減衰)・声部ごとの打鍵の時間差 (低音が先)・
拍節に沿った強弱の起伏 (ルバート) と控えめな内声で、間そのものが音楽として聞こえるフレージングにした。

- 🎬 **[elegia.mp4](elegia.mp4)** — 9 分 27 秒 · 1280×720 · 30fps

構成は Lamento / Dolore 版と同じ (Introitus → Fuga → Ritornello → Fuga a tre soggetti → Lacrimosa)。

```bash
python3 compose_elegia.py score_elegia.json
python3 synth.py score_elegia.json elegia.wav
python3 video.py score_elegia.json elegia.wav elegia.mp4
```

## 🎹🎹 Requiem BADA VII — Dialogo (B♭ minor, ♩=36, ピアノ独奏・左手も主題を歌う)

Elegia 版の左手を「伴奏」から解放した版。

- 低音オクターヴの打音層を廃止
- 嘆きのバス (D C# C B B♭ A) は、各根音から音階を 2 音のぼる歌う音型 (D E F | C# D E | C D E | …) に
- 左手のテノールは右手のアルトの B-A-D-A と 1 小節遅れのカノンで対話 (前奏では左手が先に唱える)
- 持続和音 (全音符の保持) をやめ、自由声部はすべて動く対位法に
- 高音の B-A-D-A (B♭5–D6) は右手の最上声として残す

- 🎬 **[dialogo.mp4](dialogo.mp4)** — 9 分 27 秒 · 1280×720 · 30fps

```bash
python3 compose_dialogo.py score_dialogo.json
python3 synth.py score_dialogo.json dialogo.wav
python3 video.py score_dialogo.json dialogo.wav dialogo.mp4
```

## 作り方 (再現)

```bash
pip install numpy scipy soundfile librosa pillow imageio-ffmpeg
python3 compose.py score.json          # 作曲 (対位法チェック付き) → score.json
python3 synth.py score.json fuga.wav   # 合成 → fuga.wav
python3 video.py score.json fuga.wav fuga.mp4   # ピアノロール動画
```

- `compose.py` — 主題・和声進行・形式を定義し、自由声部を規則ベースで生成
  (和音構成音の選択、平行 5 度/8 度・声部交差・半音衝突の回避、経過音/隣接音の装飾)。
  強拍の不協和と平行進行を数えて報告する簡易チェッカー付き。
- `synth.py` — 声部ごとに倍音構成の違う加算合成音 (フルート系 / リード系 / 弦系 / プリンシパル+16')。
- `video.py` — 主題の入りを声部名付きで表示するピアノロール。和音名、小節番号、音量を表示。
