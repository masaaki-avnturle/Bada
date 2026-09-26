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

## 🎻 Requiem BADA VIII — Concerto (for Piano and Orchestra, B♭ minor, ♩=30)

Dialogo 版をピアノ協奏曲に作り換えた版。バロック協奏曲のリトルネッロ形式と重ね、
**トゥッティ** (前奏・回帰句・終結 = 嘆きのパッサカリア) では弦 5 部・オーボエ・フルート・ホルン・ティンパニが
ピアノの全声部を重ね、**ソロ** (三重フーガ) ではピアノ独奏が主体で弦は主題の入りだけをそっと重ねる。
テンポは ♩=30 (1 小節 8 秒)。

- 🎬 **[concerto.mp4](concerto.mp4)** — 9 分 59 秒 · 1280×720 · 30fps

| 小節 | 内容 |
|:--|:--|
| 1–6 | **I. Introitus — Tutti** |
| 7–28 | **II. Solo — Fuga** (主題 I の 4 声提示) |
| 29–34 | **Ritornello — Tutti** |
| 35–60 | **III. Solo — Fuga a tre soggetti** (三重結合 ×3、休止) |
| 61–74 | **IV. Lacrimosa — Tutti** (嘆きのパッサカリア ×4、ティンパニと低弦の上で消える) |

```bash
python3 compose_concerto.py score_concerto.json
python3 synth.py score_concerto.json concerto.wav
python3 video.py score_concerto.json concerto.wav concerto.mp4
```

- 管弦楽の音色: 弦は鋸歯波の波形テーブルを 5 本デチューンで重ねビブラートと弓圧のうねりを付けたもの (Va/Vc/Cb は暗め)、
  オーボエは奇数倍音を強めた明るい音、フルートは少ない倍音+息の雑音、ホルンは丸い倍音構成、ティンパニは音程の落ちる打音のロール。
- `compose.main(..., post=...)`: 自由声部の生成後に全声部を見て管弦楽の重ねを追加するフック。

## 🎼🎻 Symphony BADA — 交響曲 ニ短調 (4 楽章)

協奏曲版を交響曲に作り換えた版。独奏はなく、弦 5 部 (Vn I / Vn II / Va / Vc+Cb) がフーガの 4 声を担い、
木管 (Fl / Ob / Cl) が主題の入りを重ね、金管 (Hn / Tp / Tb) は終楽章とコーダで加わる。楽章ごとにテンポが変わる。

- 🎬 **[symphony.mp4](symphony.mp4)** — 1280×720 · 30fps

| 楽章 | 小節 | テンポ | 内容 |
|:--|:--|:--|:--|
| I. Grave — Allegro moderato | 1–50 | ♩=40 → 76 | 嘆きのパッサカリアの序奏 → 主題 I 〈MOTHER〉の 4 声フーガ |
| II. Adagio — Lamento | 51–64 | ♩=40 | 嘆きのバスのパッサカリア ×4、B-A-D-A のカノン、木管 |
| III. Scherzo | 65–105 | ♩=126 | 主題 II 〈トラック18〉の提示と主題 I との二重結合 ×3、スタッカート気味の弦とティンパニ |
| IV. Finale — Maestoso | 106–156 | ♩=84 → 60 | B-A-D-A 主題と三重結合 ×3、休止、D 長調のコーダ (金管の和音、B♮-A-D-A、ティンパニ) |

```bash
python3 compose_symphony.py score_symphony.json
python3 synth.py score_symphony.json symphony.wav
python3 video.py score_symphony.json symphony.wav symphony.mp4
```

- `compose.py`: 小節ごとのテンポ (`P.tempo`) と奏法 (`P.det`, 音の長さの比率) を指定できるテンポ・マップを追加。
  `score.json` に各小節の開始時刻 (`bar_times`) を出力し、動画もそれに従う。

## 🎹🎻 Piano Concerto BADA — ピアノ協奏曲 ニ短調 (3 楽章)

交響曲版の素材を、独奏ピアノと管弦楽のための 3 楽章の協奏曲に作り換えた版。
小節ごとに **solo** (ピアノ) / **tutti** (管弦楽) / **both** (合奏) / **cadenza** (ピアノのみ) の役割を切り替える。

- 🎬 **[pconcerto.mp4](pconcerto.mp4)** — 1280×720 · 30fps

| 楽章 | 小節 | テンポ | 内容 |
|:--|:--|:--|:--|
| I. Allegro moderato | 1–58 | ♩=40 → 76 → 52 → 76 | 管弦楽の序奏 (嘆きのパッサカリア) → 主題 I のフーガ (提示はピアノ、エピソードは管弦楽) → **カデンツァ** (左手に主題 I、右手に B-A-D-A、半音階の走句とトリル) → 管弦楽の結び |
| II. Adagio — Lamento | 59–72 | ♩=40 | 嘆きのバス ×4 を 管弦楽 → ピアノ → 合奏 → ピアノ と交替 |
| III. Finale — Maestoso | 73–123 | ♩=84 → 60 | B-A-D-A 主題の提示 (ピアノ) → 三重結合 ×3 (ピアノ → ピアノ → 合奏)、エピソードは管弦楽、休止、D 長調のコーダ |

```bash
python3 compose_pconcerto.py score_pconcerto.json
python3 synth.py score_pconcerto.json pconcerto.wav
python3 video.py score_pconcerto.json pconcerto.wav pconcerto.mp4
```

- `P.role` (小節 → 役割) を追加。合成側は役割に応じて同じ声部をピアノ / 弦 / 両方で鳴らし、動画はトゥッティの小節を弦の色で描く。

## ❤️ Requiem BADA · Cor — 心臓のレクイエム (ニ短調, ♩=心拍数)

- 🎬 **[heart.mp4](heart.mp4)** — 1280×720 · 30fps · 約 7 分 21 秒

これまでのレクイエムとフーガを、心臓の鼓動「ドックン (I 音) – ドックン (II 音)」を音楽の流れの芯にして作り換えた版。

- **1 拍 = 1 心拍** — 心拍数がそのままテンポになり、曲の起伏とともに 安静 56 → フーガ I で 72 → 嘆きで 58 → 三重フーガの頂点で 84 → Lux aeterna で 44 へ静まる
- **鼓動は和声に溶ける** — 「ドッ」(I 音) はその拍の和音の低音、「クン」(II 音) はその 5 度上に調律。収縮期 (I 音 → II 音の間) は心拍が速いほど短い
- **総休止で心臓も止まる** — フーガの総休止 (バッハの自筆譜が途切れる箇所へのオマージュ) では鼓動が 2 拍止まり、強く打ち直す
- 動画の下に **心電図** (QRS の山 = ドッ、T 波 = クン、止まった拍は平らな線) と、脈打つ心臓・心拍数を表示

| 部分 | 小節 | 心拍 (♩) | 内容 |
|:--|:--|:--|:--|
| I. Introitus — Cor | 1–8 | 56 → 60 | 鼓動だけ → D のドローン → Requiem aeternam の聖歌 → B-A-D-A |
| II. Fuga | 9–52 | 62 → 72 | 主題 I 〈MOTHER〉の 4 声フーガ (第 I 部) |
| Lamento | 53–58 | 66 → 58 | 歌う嘆きのバスと B-A-D-A のカノン、鼓動が深く落ち着く |
| III. Fuga a tre soggetti | 59–103 | 64 → 84 → 60 | B-A-D-A の提示と三重結合 ×3、総休止、ピカルディ終止 |
| IV. Lux aeterna | 104–119 | 60 → 44 | B-A-D-A のマントラ、D 長調の和音の中で鼓動が安らぐ |

```bash
python3 compose_heart.py score_heart.json
python3 synth.py score_heart.json heart.wav
python3 video.py score_heart.json heart.wav heart.mp4
```

- `synth.py` の `heart_tone` — I 音 (音高が落ちる低い打音 + 22 ms 後の 2 つ目の弁の山 + 胴の低いノイズ) と II 音 (短く明るい)。鼓動はほぼ乾いた音で近くに置き、ごく一部だけ大聖堂の響きへ送る。

## 🛤 Requiem BADA — Long Distance (不整脈の旅)

- 🎬 **[journey.mp4](journey.mp4)** — 1280×720 · 30fps · 約 8 分 16 秒

Cor — Mantra から倍音 (倍音シンセ・倍音ドローン) と心臓の鼓動を外し、ロックバンドのドラムを「不整脈流」の洗脳的なビートにして、レクイエムとフーガを、提出された 7 曲をたどる長い旅に作り換えた版。1 曲 = 1 区間、区間の長さは原曲の長さに比例 (合計 31:29 → 約 8 分)、主音とテンポは原曲に合わせる (120 を超える曲はテンポを半分に)。

| 区間 | 原曲 (長さ) | 調 · ♩ | 素材 | 不整脈のドラム |
|:--|:--|:--|:--|:--|
| ① | 01 LOVELESS (5:36) | ト短調 · 81 | Introitus → B-A-D-A のマントラ + Dies irae | 期外収縮 — 早すぎる一打のあと 1 拍抜ける |
| ② | トラック 8 (4:09) | イ短調 · 99 | 嘆きのバス ×9 | 房室ブロック — 3 小節ごとに脈が抜ける |
| ③ | 10 MOTHER (5:19) | ホ短調 · 68 | フーガ — 主題 I の提示 | 二段脈 — 短い・長いの対 |
| ④ | トラック 17 (4:35) | イ短調 · 86 | フーガ — 音階のエピソード | 心房細動 — 不規則に不規則 |
| ⑤ | トラック 18 (2:29) | ニ短調 · 62 | フーガ — 主題 II の提示 | 頻脈発作 — 小節の終わりの 16 分の連打 |
| ⑥ | 録音 090146 (7:35) | ト短調 · 96 | 二重結合 ×3 → 主題 III 〈B-A-D-A〉 | 位相のずれ — キックは 5 つおき |
| ⑦ | 録音 090933 (1:46) | ロ短調 · 63 | 三重フーガの終結 → 総休止 → ピカルディ終止 | 心停止 → 再開 |

- 不規則な型そのものが毎回まったく同じに繰り返されるので、崩れたループが洗脳的に回り続ける。脈が抜ける所ではシンセ・ベースも一緒に止まる
- 全体をニ短調で作曲し、出力の段階で区間ごとに原曲の主音へ移調 (`transpose_sections`)
- 動画の下の帯はドラムの打点 (キック = 赤、スネア = 白、ハイハット = 灰、タム = 橙、クラッシュ = 金)。抜けた脈が空白として見える

```bash
python3 compose_journey.py score_journey.json
python3 synth.py score_journey.json journey.wav
python3 video.py score_journey.json journey.wav journey.mp4
```

## 🌀 Requiem BADA · Cor — Mantra (ニ短調, ♩=心拍数)

- 🎬 **[mantra.mp4](mantra.mp4)** — 1280×720 · 30fps · 約 7 分 21 秒

Cor — Rock から流れるアルペジオ (とギター・パッド) を外し、ドラムを洗脳的に反復するビートにして、曲全体をシンセサイザーの倍音が鳴り響く洗脳の曲に作り換えた版。曲・テンポ・マップ・総休止はそのまま。

- **倍音シンセ** — 4 声 (S A T B) を合唱・オルガンではなく倍音列の加算合成で鳴らす。狭い共鳴が 2 小節ごとに 300 → 3000 → 300 Hz を往復し、倍音唱法のように倍音を 1 本ずつ鳴らす (共鳴は拍に同期)
- **倍音ドローン** — 低い D と A の倍音列が、同じ共鳴に合わせて全曲で鳴り響く。動画では、いま共鳴している倍音を光る線で表示
- **洗脳的なドラム** — 毎拍の鼓動キック (ドッ・クン)、2・4 拍のスネア、同じアクセントを繰り返す 16 分のハイハット、毎小節同じ位置の低いタムのオスティナート。フィルもタム回しもなく、同じ型だけが続く
- **流れ** — Lamento はハーフタイム、総休止で全員止まって打ち直し、Lux aeterna でドラムは 1 つずつ消えて鼓動のキックだけが残る

```bash
python3 compose_mantra.py score_mantra.json
python3 synth.py score_mantra.json mantra.wav
python3 video.py score_mantra.json mantra.wav mantra.mp4
```

- `synth.py` の `overtone_tone` — 倍音列の加算合成 + 拍に同期して動く狭い共鳴 (`formant_log2`)。動画も同じ式で共鳴している倍音を描く。

## 🥁🎛 Requiem BADA · Cor — Rock (ニ短調, ♩=心拍数)

- 🎬 **[rock.mp4](rock.mp4)** — 1280×720 · 30fps · 約 7 分 21 秒

Cor の心臓の鼓動を、ロックバンドのドラムとシンセサイザーのビートに作り換えた版。合唱 + オルガンのレクイエムとフーガ、テンポ・マップ (心拍 56 → 72 → 58 → 84 → 44)、総休止はそのまま。

- **鼓動がキックになる** — 「ドッ・クン」はキックの 2 連打 (本打 + 収縮期ぶん後の弱い打) としてビートの中に残る。動画の心電図もキックで打つ
- **ドラム** — スネアのバックビート、ハイハット (8 分 / 16 分)、クラッシュ、区切りの前のタム回し
- **シンセ** — キックで沈むシンセ・ベース (8 分)、16 分のアルペジオ、パッド。三重フーガでは歪んだギターのパワーコード
- **流れ** — Introitus はキックの鼓動だけ → バンドが入る ／ Fuga I はロックのビート ／ Lamento はハーフタイム ／ 三重フーガは 8 分のキックとギターで疾走し、総休止で全員止まって打ち直す ／ Lux aeterna でドラムは減り、キックの鼓動だけに戻る

```bash
python3 compose_rock.py score_rock.json
python3 synth.py score_rock.json rock.wav
python3 video.py score_rock.json rock.wav rock.mp4
```

- `synth.py` に `rock_drum` (キック / スネア / ハイハット / クラッシュ / ライド / タム)、`synth_bass`、`arp_pluck`、`guitar_power` を追加。バンドは乾いた音で前に置き、少しだけ大聖堂の響きへ送る。

## 🎹🎛 BADA 528 — Sweet Trio (ホ短調, ♩=72)

- 🎬 **[sweet.mp4](sweet.mp4)** — 1280×720 · 30fps · 約 5 分 13 秒

これまでの主題 (I・II・B-A-D-A・嘆きのバス・三重フーガ) を、BWV 528 (トリオ・ソナタ第 4 番 ホ短調) の
「2 上声 + バス」のトリオ書法で集大成し、坂本龍一「Sweet Revenge」風の循環コード (Em7–Cmaj7–Am7–B7)・
エレピ・シンセパッド・シンセリード・ブラシの上に置いた版 (旋律は引用せず)。

```bash
python3 compose_sweet.py score_sweet.json
python3 synth.py score_sweet.json sweet.wav
python3 video.py score_sweet.json sweet.wav sweet.mp4
```

## 🎻🪈 BADA 528 — Acceptance (ホ短調, ♩=54–63)

- 🎬 acceptance.mp4 — 1280×720 · 30fps · 約 6 分 47 秒 (作曲者のタブレット録音の実音を含むため、リポジトリには置いていません。下の手順で元の録音から作り直せます)

BWV 528 を、坂本龍一『リトル・ブッダ』の「Acceptance」を思わせる哀愁の弦楽に作り換え、
作曲者のタブレット録音 (20260922_090933 / 090146) と合わせた版 (旋律は引用せず、雰囲気と編成だけを参照)。

- Sweet Trio 冒頭の金属的な高音 (エレピの FM 倍音・ブラシのハイハット — トライアングルのように聞こえた音) を、**コントラバスの独奏**に置き換えた。
- タブレット録音の**実音**を 2 か所 (Tablet I / Tablet II) で流し、採譜した低音をコントラバス、内声を弦が追って伴奏する。録音の音はピアノロールに水色で表示。
- 録音の最上声と和声 (Em7–D–Dsus4–A–Gmaj7/F#…) から**タブレットの主題 T** を作り、Adagio と頂点 (Acceptance) で弦が歌う。

| 部分 | 小節 | テンポ | 内容 |
|:--|:--|:--|:--|
| Prologo | 1–3 | ♩=60 | コントラバス独奏 (E1 → B1 E2 → G2 F#2 D2)、タンプーラの E–B |
| Tablet I | 4–11 | ♩=60 | 録音 090933 (Gmaj7–Em–Bm7–F#m7–C–Am7–Em7–Dsus4) の実音 + Cb・弦 |
| Adagio | 12–19 | ♩=56 | 主題 T の弦のコラール、下行する低音 |
| Andante — Trio | 20–31 | ♩=60 | BWV 528 風トリオ: ピアノ + オーボエ (主題 I)、フルート (主題 II)、Cb のピッツィカート |
| Lamento | 32–43 | ♩=58 | 嘆きのバス + B-A-D-A のカノン (バンスリ・ピアノ)、弦が満ちる |
| Fugato → 三重結合 | 44–66 | ♩=63 → 60 | 主題 I の 4 声提示 (ピアノ → ピアノ + 弦) → 主題 I + II + III |
| Acceptance | 67–82 | ♩=54 | 主題 T ×2 を厚い弦がオクターヴで、ピアノの分散和音、2 回目はバンスリ |
| Tablet II → Fine | 83–97 | ♩=60 → 50 | 録音 090146 (B7–D–Bm–C–Em–F#m7–Am–Bm–D7–Em) の実音、録音自身の Em で終わり、B-A-D-A |

```bash
python3 extract_tablet.py 20260922_090933.mp3 20260922_090146.mp3   # samples/ に抜粋 (FLAC) と採譜 (JSON)
python3 compose_acceptance.py score_acceptance.json
python3 synth.py score_acceptance.json acceptance.wav
python3 video.py score_acceptance.json acceptance.wav acceptance.mp4
```

- `synth.py` に コントラバス (arco / pizz)・タンプーラ (ジャワリの倍音の開き)・バンスリ (下からの滑り込み + 息) と、録音の抜粋を鳴らす `REC` を追加。

## 🎙 Requiem BADA — Tablet Sessions (ロ短調 → ホ短調 → 変ロ短調 → ロ短調, 約 7 分)

タブレット録音 5 本 (20260922_174820 / 175717 / 175951, 20260923_080607 / 080918) を
レクイエムとフーガにしたため、**録音の音そのもの**で鳴らし、最後に全部を 1 つのフーガに合わせる。
録音と、録音を含む mp4・サンプル・採譜は個人の録音なのでリポジトリには入れていない (コードのみ)。

| 区間 | 内容 |
|---|---|
| ①〜⑤ 各録音 | 実音の抜粋 (約 20 秒) → その最上声から作った主題の 4 声フーガ (主唱・答唱・コデッタ) → 抜粋の和音進行のコラール。各区間は録音の調へ移調 |
| Finale — Fuga a cinque soggetti | 5 つの主題が 1 小節おきに重なり (2 周目は 5 度上)、各主題は自分の録音の音で鳴る |
| Lux aeterna | B-A-D-A ×2 → ピカルディ終止 (ロ長調) → 最初の録音 (17:48) の実音で閉じる |

- 4 声は **サンプラー**: 録音から 1 音だけが鳴っている区間を切り出し (pyin で音高、倍音の純度で選別)、
  最も近い音を移調・持続部をループして鳴らす。ピアノロールの色は「どの録音の音か」を表す。

```bash
python3 build_sampler.py bank 20260922_174820.mp3 20260922_175717.mp3 20260922_175951.mp3 20260923_080607.mp3 20260923_080918.mp3
python3 compose_tablet.py bank/bank.json score_tablet.json
python3 synth.py score_tablet.json tablet.wav
python3 video.py score_tablet.json tablet.wav tablet.mp4
```

## 🌀🎙 Requiem BADA — Tablet Sessions II · Mantra lento (ヘ短調 → ホ短調, ♩=52→48, 約 6 分)

タブレット録音 2 本 (20260924_084937 / 085314) の、ゆったりとした洗脳的なレクイエムとフーガ。鳴るのは録音の音だけ
(録音・mp4 は個人の録音を含むのでリポジトリに入れていない)。

| 区間 | 内容 |
|---|---|
| ①② 各録音 | 実音の抜粋 → 抜粋の最初の 1 小節のテープ・ループ + 持続音 + 鼓動 → 4 声フーガ (下で実録音のオスティナートが根音・5 度・3 度・5 度を刻み続ける) → 抜粋の和音のコラール ×2 (2 回目はループが戻る) |
| Finale — Fuga doppia | 2 つの主題の二重フーガ、最後は 2 つの主題が同時に (ホ短調) |
| Mantra → Lux aeterna | 2 つの録音のループが交互に回る中で B-A-D-A ×4 (08:49 はテープのように半音下げて) → ピカルディ終止 → ループが消えていく |

- 鼓動は録音の低い打鍵を 2 オクターヴ下げて 160 Hz 以下だけ残した音 (毎拍、1 拍目を強く)。持続音は打鍵を消してループで伸ばしたサンプラーの音。
- `synth.py`: `REC` に `semis` (テープのような移調)、`recsampler` に `OS` / `DN` / `PK` を追加。

```bash
python3 build_sampler.py bank2 20260924_084937.mp3 20260924_085314.mp3
python3 compose_tablet2.py bank2/bank.json score_tablet2.json
python3 synth.py score_tablet2.json tablet2.wav
python3 video.py score_tablet2.json tablet2.wav tablet2.mp4
```

## 🌀🎙🎙 Requiem BADA — Tablet Sessions III · Mantra of All (♩=56 のまま, 約 7 分 50 秒)

録音 11 本 (09-20 15:40 / 15:41 の動画 2 本の音、09-22 09:01 / 17:40 / 17:48 / 17:57 / 17:59、09-23 08:06 / 08:09、09-24 08:49 / 08:53)
を全部合わせた、止まらない鼓動の上の洗脳的なレクイエムとフーガ。鳴るのは録音の音だけ (録音・mp4 はリポジトリに入れていない)。

| 区間 | 内容 |
|---|---|
| Introitus | 鼓動と持続音だけ (鼓動は最後まで ♩=56 で止まらない) |
| Requiem — 11 の祈り | 録音順に各 7 小節: 実音の抜粋 3 小節 → ループが回る中、抜粋の最上声から作った主題を上声 → 低音が歌う (下でオスティナート)。調は各録音の調 |
| Fuga — 11 の主題 | 11 の主題が 1 小節おきに 4 声へ次々に入る。各主題は自分の録音の音で (ホ短調) |
| Mantra | 11 本のループが 1 小節ずつ回り (テープのように速さごと移調してホ短調へ)、B-A-D-A ×6 |
| Lux aeterna | ピカルディ終止 → 最後の録音のループが消えていく |

- 新しい録音の調は音高の分布 (Krumhansl のプロファイル) から推定した短調。抜粋の音量は録音全体との比から自動で合わせる。
- `video.py`: 録音が 6 本以上のときは色相を等分し、録音の凡例を 2 段目に出す。

```bash
python3 build_sampler.py bank3 20260920_154001.mp4 20260920_154118.mp4 20260922_090146.mp3 ... 20260924_085314.mp3
python3 compose_tablet3.py bank3/bank.json score_tablet3.json
python3 synth.py score_tablet3.json tablet3.wav
python3 video.py score_tablet3.json tablet3.wav tablet3.mp4
```

## 🎚🎙 Requiem BADA — Tablet Sessions IV · Mix (ホ短調, ♩=60, 約 5 分)

録音 11 本 (09-20 15:40 / 15:41、09-22 09:09 / 17:45 / 17:51 / 17:54 / 17:59、09-23 08:06 / 08:09、09-24 08:49 / 08:53) を
順に並べるのではなく**同時に重ねてミックス**した、洗脳的なレクイエムとフーガ。全部の録音をテープのように速さごと移調して
ホ短調にそろえ、止まらない鼓動の上で重ねる。鳴るのは録音の音だけ (録音・mp4 はリポジトリに入れていない)。

| 区間 | 内容 |
|---|---|
| Introitus | 鼓動と持続音、最初の録音のループが立ち上がる |
| Mix — 11 本の実音 | 11 本の抜粋 (各 2 小節) をクロスフェードでつなぐ |
| Kyrie — ループの重ね | 2 小節ごとに次の録音のループが入り 3 本が常に重なる。入るたびにその録音の主題を 1 声がその録音の音で歌う |
| Fuga — 2 つずつ | 2 つの主題を同時に (上声と低音)、それぞれ自分の録音の音で。下で 2 本のループ |
| Mantra — 全部のミックス | ループが 1 小節ごとに 1 本ずつ増え、最後は 11 本全部が同時に回る。B-A-D-A ×6 |
| Lux aeterna | ピカルディ終止 → 最後の録音のループが消えていく |

```bash
python3 build_sampler.py bank4 20260920_154001.mp3 ... 20260924_085314.mp3
python3 compose_tablet4.py bank4/bank.json score_tablet4.json
python3 synth.py score_tablet4.json tablet4.wav
python3 video.py score_tablet4.json tablet4.wav tablet4.mp4
```

## 🎙🎚 Requiem BADA — Tablet Sessions V · Mix (実音) (ヘ短調 → ホ短調, ♩=60, 約 7 分)

ループを使わず、録音 5 本 (09-22 17:57 / 17:59、09-23 08:09、09-24 08:49 / 08:53) を**実音のまま (速さも音高も元のまま)** 40〜64 秒ずつ流し、
長いクロスフェードでつないだレクイエムとフーガ。各録音から、その調にいちばん合う区間を自動で選ぶ。
実音の後半は 4 声 (録音の 1 音のサンプラー) が録音の和音 (小節でいちばん長く鳴る和音) を全音符で静かに支える。
(録音・mp4 はリポジトリに入れていない)

| 区間 | 内容 |
|---|---|
| Introitus | 08:49 (ヘ短調) の実音 64 秒 |
| Fuga I | 08:49 の主題の 4 声フーガ → ヘ長調の終止 → ナポリの和音 (F) → B7 でホ短調へ |
| Kyrie — ミックス | 17:59 → 08:53 → 08:09 (ホ短調) の実音を 8 秒のクロスフェードで重ねてつなぐ |
| Fuga II | 3 本の主題の三重フーガ → 属和音で止まる |
| Lacrimosa | 17:57 (ロ短調) の実音 48 秒 |
| Finale → In paradisum | 5 つの主題のフーガ → 08:09 の本当の終わり 20 秒 (録音自身のホ短調の終止) |

- `synth.py`: `REC` に `fin` / `fout` (フェードの長さ、クロスフェード用)。

```bash
python3 build_sampler.py bank5 20260922_175951.mp3 20260922_175717.mp3 20260923_080918.mp3 20260924_084937.mp3 20260924_085314.mp3
python3 compose_tablet5.py bank5/bank.json score_tablet5.json
python3 synth.py score_tablet5.json tablet5.wav
python3 video.py score_tablet5.json tablet5.wav tablet5.mp4
```

## 🌀🎙 Requiem BADA — Tablet Sessions VI · Lento ipnotico (♩=50, 約 8 分 40 秒)

録音 5 本 (09-24 08:49 / 08:53 / 11:18 / 11:21 / 11:23) の、ゆったりとした洗脳的なレクイエムとフーガ。
録音はループせず実音のまま流し、その下で録音の低い打鍵から作った鼓動が最後まで止まらない。
各録音: 実音 8 小節 (後半は 4 声が録音の和音を支える) → その主題の 4 声フーガ (下で実録音のオスティナートと持続音) → 次の調の属和音。
調は 11:18 (変ロ短調) → 08:49 · 11:21 (ヘ短調) → 08:53 · 11:23 (ホ短調)。Finale は 5 つの主題のフーガ → 11:23 の実音 → ピカルディ終止。

```bash
python3 build_sampler.py bank6 20260924_084937.mp3 20260924_085314.mp3 20260924_111846.mp3 20260924_112131.mp3 20260924_112313.mp3
python3 compose_tablet6.py bank6/bank.json score_tablet6.json && python3 synth.py score_tablet6.json tablet6.wav && python3 video.py score_tablet6.json tablet6.wav tablet6.mp4
```

## 🎹🔥 Fantaisie-Révolution — Tablet Sessions (ハ短調 → 嬰ハ短調 → 変ニ長調 → 嬰ハ長調, 約 2 分 45 秒)

同じ録音 5 本を、ショパンの**革命のエチュード** (Op.10-12) と**幻想即興曲** (Op.66) の書法でリメイクしたピアノ曲。
鳴る音はすべて録音の 1 音 (サンプラー、新しい声 `PF`)。旋律は各録音の最上声から作った主題。

| 区間 | 内容 |
|---|---|
| Preludio | 11:18 の実音 |
| Rivoluzione (ハ短調, ♩=144) | 属和音 G7♭9 の強打と左手の 16 分音符の奔流 (音階を駆け下り、和音を駆け上がる) → 右手のオクターヴで主題 (11:18, 08:49) |
| Ponte | G7 → G♯7 と半音ずり上げて嬰ハ短調へ |
| Fantaisie (嬰ハ短調, ♩=152) | 左手の 3 連符 (根音-5 度-根音-10 度-根音-5 度) に右手の 16 分音符 (4 対 3)、拍の頭が主題 (11:21, 08:53) |
| Moderato cantabile (変ニ長調, ♩=66) | 11:23 の主題を長調にして歌う、左手は広い分散和音 |
| ripresa → Coda → Fine | 幻想即興曲が戻り、革命の奔流で強奏 → 低音に歌の旋律が静かに戻り嬰ハ長調で消える |

```bash
python3 compose_tablet_chopin.py bank6/bank.json score_chopin.json && python3 synth.py score_chopin.json chopin.wav && python3 video.py score_chopin.json chopin.wav chopin.mp4
```

## 🎤 Requiem BADA — Vox (わたしの声のレクイエムとフーガ, イ短調, ♩=60, 約 4 分)

2025 年の録音 9 本 (01-08 と 04-20 の歌) から**作曲者の歌声を取り出し**、2026-09-24 のタブレットのピアノ録音 5 本とミックスした、
洗脳的で安心感のあるレクイエムとフーガ。♩=60 (安静時の心拍) の柔らかい鼓動が最後まで止まらない。
(録音・取り出した歌声・mp4 は個人の録音なのでリポジトリに入れていない)

- `extract_voice.py`: UVR の MDX-Net ボーカル分離モデル (Kim_Vocal_2.onnx, GitHub の model_repo から) を onnxruntime で動かし、
  numpy/librosa の STFT で歌声を取り出す。歌っている区間 (フレーズ) と音高を測る。2026 年のピアノ録音には歌声はなかった。
- `voice_bank.py`: 歌声の伸ばした音 (±0.3 半音以内に 0.35 秒以上) を切り出して歌声のサンプラーにする (rid `VOX`)。
- `compose_vox.py`: 歌声の音の分布から調を決め (歌は長調 → 平行短調でレクイエム)、録音ごとに速さを変えずに移調してそろえる。
  合唱の下 2 声は歌声の 1 音 = 作曲者の声の合唱、上 2 声・持続音・オスティナート・鼓動はピアノ録音の 1 音。

| 区間 | 内容 |
|---|---|
| Introitus | 歌声だけ (持続音と鼓動の上で) |
| Kyrie | 歌声の音に合う和音を 1 小節ごとに選び、合唱が全音符で包む |
| Mix | タブレットのピアノ録音の実音に歌声が重なる |
| Fuga | 歌声から作った主題の 4 声フーガ (テノールとバスは歌声で歌う) |
| Sanctus | 歌声のフレーズが次々に、下でオスティナート |
| Agnus Dei → Lux aeterna | B-A-D-A と歌声 → 最後の歌声 → 長調の和音で安らかに |

```bash
python3 extract_voice.py Kim_Vocal_2.onnx voice 2025-01-08_*.wav 2025-04-20_*.wav recording_20250108-144205*.mp3
python3 voice_bank.py voice/voice.json vbank
python3 compose_vox.py bank6/bank.json vbank/bank.json score_vox.json && python3 synth.py score_vox.json vox.wav && python3 video.py score_vox.json vox.wav vox.mp4
```

## 🎸🎤 Requiem BADA — Vox · Rock (イ短調, ♩=80, 約 3 分)

9/23・9/24 のタブレットのピアノ録音 7 本の旋律を、ロックバンド (ドラム・シンセベース・ギター) とシンセサイザー (パッド・リード) の上の
洗脳的なレクイエムとフーガに。作曲者の歌声 (2025-01-08 20:00 / 20:15 から取り出したもの) を**残響をかけず**乾いたきれいな声で前に置く。
(録音・歌声・mp4 はリポジトリに入れていない)

- `feminize_voice.py`: WORLD ボコーダー (pyworld) で、大げさにせず女性的に — f0 を 1 オクターヴ上げ、フォルマントは 1.12 倍だけ。
  伸ばした音だけ音階へ 60% 寄せる控えめな音程補正、歌っていない所のゲート。残響は足さない。
- 後ろのコーラス (`BV`) は同じ歌声の 1 音を 3 声で正確な音程に重ねたもの (プロの歌手の録音は使っていない)。
- `synth.py`: `REC` の `dry` (残響なし)、`BV` (コーラス)、`recsampler` でも `PD` / `LD` (シンセ)。`VOX…` のサンプルは同じ印のものだけから選ぶ。

| 区間 | 内容 |
|---|---|
| Intro | ピアノ録音 11:23 の実音 → 鼓動のようなキックとパッド |
| Verse I / II | 歌声とバンド (8 分音符の同じ刻み)、和音は歌声に合わせて |
| Chorus I | 9/23 08:09 の旋律の 4 声フーガ + ギター + コーラス |
| Chorus II | 7 本の旋律が 1 小節おきに (上の声にシンセのリード) |
| Bridge | 08:09 の実音、キックだけ |
| Mantra | B-A-D-A ×4 (コーラスと 4 声)、バンド全開、歌声 → イ長調 |

- **Instrumental 版** (`--instrumental`): 声・歌声・コーラスを消し、Verse はシンセのリフが毎小節同じ形を刻み
  Am - F - Dm - E7 の 4 小節が回り続ける洗脳的な版 (約 3 分)。`python3 compose_rockvox.py bank7/bank.json score_rockinst.json --instrumental`

```bash
python3 feminize_voice.py voice/voice.json fem 0 12 1.12 -- 20250108_201532 20250108_200038
python3 voice_bank.py fem/voice.json fbank --tag=VOXF
python3 compose_rockvox.py bank7/bank.json fbank/bank.json score_rockvox.json && python3 synth.py score_rockvox.json rockvox.wav && python3 video.py score_rockvox.json rockvox.wav rockvox.mp4
```

## 🎹🎛 Requiem BADA — Tablet Sessions VII · Piano & Synth (ホ短調 → 変ロ短調 → ヘ短調, ♩=60, 約 5 分)

2026-09-24 の録音 5 本を実音のまま (ループなし・速さも音高も元のまま) つなぎ、その旋律で作ったレクイエムとフーガを混ぜた自分流のミックス。
11:21 はピアノとシンセサイザーを 1 曲にした録音 (音が減衰せず明るい — 0.45 秒後の残り 0.91、ほかは 0.58〜0.71) なので、
フーガの旋律もピアノの音にシンセサイザーのリード (`LD`) を重ね、シンセのパッド (`PD`) が和音を支える。(録音・mp4 はリポジトリに入れていない)

| 区間 | 内容 |
|---|---|
| Introitus — Mix | 11:23 → 08:53 (ホ短調) の実音をクロスフェードで |
| Fuga I | 11:23 と 08:53 の主題の二重フーガ (ピアノ + シンセ) → B7 → F7 で変ロ短調へ |
| Lacrimosa | 11:18 (変ロ短調) の実音 |
| Sanctus — Mix | 08:49 → 11:21 (ピアノとシンセの曲, ヘ短調) の実音 |
| Finale | 5 つの主題が 2 小節ごとに (ピアノ + シンセ) |
| In paradisum | 11:21 の本当の終わりの実音 |

```bash
python3 build_sampler.py bank8 20260924_084937.mp3 20260924_085314.mp3 20260924_111846.mp3 20260924_112131.mp3 20260924_112313.mp3
python3 compose_tablet7.py bank8/bank.json score_tablet7.json && python3 synth.py score_tablet7.json tablet7.wav && python3 video.py score_tablet7.json tablet7.wav tablet7.mp4
```

## 🌀🎹 Requiem BADA — Tablet Sessions VIII · Ipnotico (ホ短調 → 変ロ短調 → ヘ短調 → ヘ長調, ♩=60, 約 4 分 30 秒)

Tablet Sessions VII から、シンセサイザーの「正義の味方」のような明るく勇ましい部分 (シンセのリード・パッド、ピアノとシンセの録音 11:21 の実音と主題) を消し、
ピアノ録音 4 本 (09-24 08:49 / 08:53 / 11:18 / 11:23) の実音と、その旋律のレクイエムとフーガだけにした、人に聞かせられる洗脳的な版。
♩=60 の柔らかい鼓動 (録音の低い打鍵) が最後まで止まらず、フーガの下では録音の音のオスティナートと持続音が回り続ける。
最後は 08:49 の本当の終わり (属和音で止まる) → ヘ長調の和音。(録音・mp4 はリポジトリに入れていない)

```bash
python3 compose_tablet8.py bank8/bank.json score_tablet8.json && python3 synth.py score_tablet8.json tablet8.wav && python3 video.py score_tablet8.json tablet8.wav tablet8.mp4
```

## 🌀🎹 Requiem BADA — Tablet Sessions IX · Ipnotico (警笛のような持続音を消した版, 約 4 分 30 秒)

VIII から、電車の警笛のように聞こえる「伸ばしたまま鳴り続ける和音・持続音」を消した版。
サンプラーはピアノ録音の 1 音の持続部をループで伸ばすため、長い音や和音がオルガンや警笛のように鳴り続けていた。
- 低い持続音 (`DN`) をなくし、サンプラーの音はループで伸ばさずピアノのように自然に減衰させる (`synth.py` の meta `piano_decay`、ここでは 1.4 秒)
- 調の変わり目と最後の全音符の和音 → 自然に消えていくピアノの分散和音 (`PF`)
- 実音の区間の下で和音を伸ばす 4 声をなくし、実音だけを流す (鼓動とオスティナートは残す)

```bash
python3 compose_tablet9.py bank8/bank.json score_tablet9.json && python3 synth.py score_tablet9.json tablet9.wav && python3 video.py score_tablet9.json tablet9.wav tablet9.mp4
```

## 🎹✨ Requiem BADA — Tablet Sessions X · Alto e basso (ホ短調 → 変ロ短調 → ヘ短調 → ヘ長調, ♩=60, 約 5 分 20 秒)

IX から、近い音を上下する警笛のようなオスティナートを外し、2026-09-23 / 09-24 のピアノ録音 6 本 (ピアノとシンセの 11:21 は除く) の
実音とそのレクイエムとフーガに、高音と低音が大きく離れたやさしいシンセサイザーを重ねた版。
- 高音 (`GL`, ガラスのような柔らかい正弦波): 大きく跳ぶ分散和音を毎小節同じ形で (隣り合う音へは動かない)。実音の区間では 1・3 拍目だけ
- 低音 (`SUB`, やさしい正弦波): 和音の根音をゆっくり。中音域に実音のピアノと 4 声 (自然に減衰)
- `synth.py`: `glass_tone` / `sub_tone`。`piano_decay` のときはバスの 1 オクターヴ下の持続する正弦波を足さない (伸び続ける低音をなくす)

```bash
python3 compose_tablet10.py bank7/bank.json score_tablet10.json && python3 synth.py score_tablet10.json tablet10.wav && python3 video.py score_tablet10.json tablet10.wav tablet10.mp4
```

## 🎼🕯 Requiem BADA — Tablet Sessions XI · Adagio in tre bemolli (ハ短調 → 変ロ短調 → 変ホ短調 → 変ト長調 → ハ短調, ♩=48, 約 7 分 15 秒)

X から高音のガラスのシンセを消し、2026-09-23 / 09-24 のピアノ録音 6 本の実音とその旋律をもとに、Adagio のバッハ風フーガで再構築した荘厳で洗脳的なレクイエム。
- **3 つの♭ B♭・E♭・G♭ をめぐる調**: ハ短調 (導音は白鍵の B♮) → 変ロ短調 → 変ホ短調 → 変ト長調 (pp のコラール) → ハ短調 → ハ長調
- **バッハ風フーガ** (`bach_fugue`): 提示 (主唱・答唱 ×2) → エピソード (ゼクエンツ) → 下属調の入り → ストレッタ → 拍ごとに打ち直す保続低音
- **降圧剤**: 高音で pp の実音のピアノが、その調の♭の音階 (B♭ → A♭ → G♭ → F → E♭ …) を 2 小節で 1 巡、ゆっくり降り続ける
- ホ短調の録音 (08:09 / 08:53 / 11:23) は速さを変えずに半音下げて変ホ短調に、ヘ短調の 08:49 は 2 半音下げ (`passage(..., pshift=)`)。
  08:06 の本当の終わり (B♭7) を変ホ短調への属和音として使う
- 鼓動は T2 より小さく (pp)、低音はやさしい正弦波。ステムごとに測って合唱・実音・鼓動・降りる音階の釣り合いを取った

```bash
python3 compose_tablet11.py bank7/bank.json score_tablet11.json && python3 synth.py score_tablet11.json tablet11.wav && python3 video.py score_tablet11.json tablet11.wav tablet11.mp4
```

## 🎹🎛 Requiem BADA — Tablet Sessions XII · Risonanza (ホ短調 → 変ロ短調 → ヘ短調 → ヘ長調, ♩=60, 約 6 分 20 秒)

XI の pianissimo の降りる音階を消し、2026-09-24 のピアノ録音 5 本 (08:49 / 08:53 / 11:18 / 11:21 / 11:23、速さも音高も元のまま) の実音と
その旋律のレクイエムとフーガに、**本格的なアナログ風シンセサイザー**を重ねた版。
- `synth.reso_synth`: デチューンした鋸歯波 3 本 + サブ (矩形波) を、共鳴する 2 次ローパス (RBJ biquad, Q 6〜8、512 サンプルごとに係数を更新) に通し、
  カットオフが立ち上がりで開いて LFO でゆっくり往復する (共鳴のうねり)。鍵盤追従、軽い飽和
- `RS` (パッド): 和音の根音・5 度・3 度を 2 小節ごとに、うねりは 2 小節で 1 往復。実音の下では控えめ
- `RL` (主題に共鳴するリード): フーガの主題の入り (ラベル付きの音) を同じ音で重ねて響かせる (post で events から)
- 形は VII と同じ (Introitus → Fuga I (バッハ風, 08:53) → Lacrimosa → Fuga II (二重) → Sanctus (08:49 → ピアノとシンセの 11:21) → Finale (ストレッタ) → 11:21 の終わり → ヘ長調)
- ステムごとに測って、ピアノ (合唱) がいちばん前、パッドとリードはその下、鼓動は pp に

```bash
python3 compose_tablet12.py bank8/bank.json score_tablet12.json && python3 synth.py score_tablet12.json tablet12.wav && python3 video.py score_tablet12.json tablet12.wav tablet12.mp4
```

## 🎹🎛 Requiem BADA — Tablet Sessions XIII · Risonanza senza onda (うねりなし, 約 6 分 27 秒)

XII から、シンセの「共鳴するうねり」(LFO でカットオフが往復するパッド `RS`) を消した版。残るのはフーガの主題の入りに同じ音で重なる
共鳴シンセ (`RL`) だけで、そのフィルターは一度開いて固定 (`lfo=0, phase=π, open=0.03`)。最後のヘ長調の和音は一度だけゆっくり開く (`open=3.0`)。
`synth.reso_synth` に `open_t` (フィルターの開く速さ) を追加。

```bash
python3 compose_tablet13.py bank8/bank.json score_tablet13.json && python3 synth.py score_tablet13.json tablet13.wav && python3 video.py score_tablet13.json tablet13.wav tablet13.mp4
```

## 🎹 Requiem BADA — Tablet Sessions XIV · Senza risonanza (「ビュー」なし, 約 6 分 27 秒)

XIII から、シンセの「ビュー」という音 — 共鳴するフィルターが開くときの音 (主題に重なるシンセの音ごとの開き、最後の和音のゆっくりした開き) — を消した版。
フィルターの共鳴をなくし (`q=0.8`)、開き方も最初から固定 (`open=0.002`)。残るのは主題の入りに同じ音で重なる、共鳴しないシンセだけ。
`synth.py`: `RS` / `RL` は event の `q` を受ける。`video.py`: meta `vname` で声部名を上書き。

```bash
python3 compose_tablet14.py bank8/bank.json score_tablet14.json && python3 synth.py score_tablet14.json tablet14.wav && python3 video.py score_tablet14.json tablet14.wav tablet14.mp4
```

## 🎻 Requiem BADA — Tablet Sessions XV · Violino (約 6 分 27 秒)

XIV から、主題の入り (11:23 の主題を含む) に重なっていたシンセサイザーを**バイオリン**に置き換えた版。本物のバイオリンの録音はないので、
`synth.violin_tone` で物理に近い合成: 弓で弾く弦の倍音列 (鋸歯波、わずかな揺れ、0.3 秒遅れて入るビブラート、薄い弓の摩擦音) →
胴の共鳴 (275 / 450 / 1000 / 1900 Hz のピーク、`_biquad` の RBJ ピーキング) → 4.2 kHz のローパスと 3.2 kHz からのハイシェルフで
切り裂かない音に。A5 より上は音量を抑え、高揚しても耳障りにならない。最後のヘ長調の和音にはバイオリンの重音 (C5・A5)。
ステムを測ってバイオリンはピアノの約 3.5 dB 下に。

```bash
python3 compose_tablet15.py bank8/bank.json score_tablet15.json && python3 synth.py score_tablet15.json tablet15.wav && python3 video.py score_tablet15.json tablet15.wav tablet15.mp4
```

## 🎹🎛 Requiem BADA — Tablet Sessions XVI · Sintetizzatore reale (約 6 分 27 秒)

XV のバイオリンを、2026-09-24 の 11:21 (ピアノとシンセサイザーを重ねた録音) から切り出した**シンセの持続音の実音**に置き換えた版。
主題はピアノ (録音の 1 音) のまま、フーガのまま、レクイエム。
- `build_synthbank.py`: pyin で ±0.3 半音以内に伸びる音を探し、ピアノの打鍵から 0.2 秒あとの、減衰せず一定に伸びている部分 (= シンセ) を切り出す
  (11:21 から C♯2〜G♯3 の 8 音、持続部の音量比 0.66〜1.03)。rid `VOXSY` — `sampler_tone` はこの印のサンプルだけから選び、減衰させない
- `synth.py`: `SP` (録音のシンセの持続音、80 ms のフェードイン)。ステムを測ってピアノの約 4 dB 下に
- 使い方は XV と同じ (`bank16.json` は bank8 と sybank を結合したもの)

```bash
python3 build_synthbank.py 20260924_112131.mp3 sybank 0.4 0.2
python3 compose_tablet16.py bank16.json score_tablet16.json && python3 synth.py score_tablet16.json tablet16.wav && python3 video.py score_tablet16.json tablet16.wav tablet16.mp4
```

## 🎹⛪ Requiem BADA — Tablet Sessions XVII · Organo (ホ短調 → 変ロ短調 → ヘ短調 → ヘ長調, ♩=60, 約 7 分 45 秒)

XVI から、合成していた側の楽器 = フーガの 4 声を**パイプオルガンのシンセ**に置き換え、11:21 の録音のシンセサイザーの実音は主題に重ねたまま。
2026-09-23 の録音 2 本 (08:06 / 08:09) を実音のミックスと主題に加え、9/24 の 5 本と合わせて 7 本。
- `synth.organ_tone`: ストップ (8 フィートのプリンシパルに 4・2⅔・2 フィート、低音は 16 フィート) ごとにプリンシパルの倍音列 (1/k^0.9、わずかな不揃い) を重ね、
  減衰せず鳴り続ける。入りに短いチフ (息の雑音と一瞬のオクターヴ)、送風のごくわずかな揺れ。meta `choir: 'organ'` で 4 声がオルガンになる
- Introitus は 3 本 (11:23 → 08:53 → 9/23 08:09)、Lacrimosa は 9/23 08:06 → 11:18、Finale は 7 つの主題 (最後の 3 つはストレッタ)
- ステムを測って、オルガンは実音と同じくらい、11:21 のシンセの実音はその約 7 dB 下、鼓動は約 13 dB 下

```bash
python3 compose_tablet17.py bank17.json score_tablet17.json && python3 synth.py score_tablet17.json tablet17.wav && python3 video.py score_tablet17.json tablet17.wav tablet17.mp4
```

## 🎛🕯 Requiem BADA — Tablet Sessions XVIII · Lacrimosa (ホ短調 → 変ロ短調 → ヘ短調, Adagio ♩=52, 約 5 分)

XVII からピアノをすべて消した版: 実音のピアノの録音、ピアノの 1 音のサンプラー、ピアノの低音から作った鼓動、パイプオルガン。
残る楽器は 2026-09-24 の 2 曲目 (11:21) から切り出した**シンセサイザーの持続音の実音**だけ。4 声のフーガをこの実音が歌い (すべての音の
`src` を `VOXSY` に)、下では同じ実音の低い持続音 (`SP`) が支える。旋律は 9/23・9/24 の 7 本から作った主題。
悲しみのレクイエム: Adagio、短調のまま終わる (ピカルディ終止なし)、最後は半音ずつ下がる嘆きの低音 (D → C♯ → C → B → B♭ → A)。
Introitus (持続音) → Kyrie: Fuga I (08:53, バッハ風) → Lacrimosa: Fuga II (11:23 · 11:18) · Fuga III (9/23 08:06 · 08:09) → Finale (7 つの主題のストレッタ) → Lamento。
`video.py`: meta `src_name` で `VOX…` の凡例の名前を指定。

```bash
python3 compose_tablet18.py bank17.json score_tablet18.json && python3 synth.py score_tablet18.json tablet18.wav && python3 video.py score_tablet18.json tablet18.wav tablet18.mp4
```

## 🎹🌟 Requiem BADA — Tablet Sessions XIX · Pastorale della Natività (ト短調 / ト長調, ♩=66, 約 4 分 40 秒)

XVIII から、シンセサイザーの全音 (4 声・持続音) を**実録音のピアノ一色** (9/23・9/24 の録音から切り出した 1 音、自然に減衰) に置き換え、
「悲しみの正義の味方」のような勇ましい旋律を消して、曲調をキリスト生誕を哀れみで描く**牧歌 (パストラーレ)** に書き換えた版。
- `gentle()`: 主題の 5 半音より大きな跳躍をオクターヴに畳んでなだらかにし、同じ長さの 2 音をシチリアーナの長短 (1.5 + 0.5) に
- 低音で開いた 5 度 (羊飼いの笛のドローン) が長短のリズムで静かに繰り返す (ピアノの 1 音、`PF`)
- ト短調 (哀れみ) とト長調 (生誕の光) を行き来: Pastorale (Fuga I, 08:53) → Kyrie (Fuga II) → Gloria (ト長調、08:09 の主題を長調に) →
  Misericordia (Fuga III, 9/23 08:06 · 08:49) → Finale (7 つの主題) → Wiegenlied (子守歌、ト長調で pp に消える)
- 長調の区間は `harm_major` で主題の音に合う長調の和音を選ぶ (固定の和音では主題とぶつかった)

```bash
python3 compose_tablet19.py bank17.json score_tablet19.json && python3 synth.py score_tablet19.json tablet19.wav && python3 video.py score_tablet19.json tablet19.wav tablet19.mp4
```

## 🎛🌟 Requiem BADA — Tablet Sessions XX · Pastorale sintetica (ト短調 / ト長調, ♩=66, 約 4 分 25 秒)

XIX から、始めの出だしの伴奏 (羊飼いの笛のドローンの 4 小節と、その後のドローン) を消し、4 声すべてを 2026-09-24 11:21 の録音から切り出した
**シンセサイザーの持続音の実音** (rid `VOXSY`) にした版。伴奏はなく、フーガの 4 声だけが曲になる。主題・調・形は XIX のまま
(跳躍を畳んだなだらかな主題、シチリアーナの揺れ、ト短調とト長調、Gloria と Wiegenlied は主題から選んだ長調の和音)。
Fuga I (08:53) → Kyrie: Fuga II (11:23 · 11:18) → Gloria (ト長調) → Misericordia: Fuga III (9/23 08:06 · 08:49) → Finale (7 つの主題) → Wiegenlied (ト長調)。

```bash
python3 compose_tablet20.py bank17.json score_tablet20.json && python3 synth.py score_tablet20.json tablet20.wav && python3 video.py score_tablet20.json tablet20.wav tablet20.mp4
```

## 🎹🌟 Requiem BADA — Tablet Sessions XXI · Pastorale pianistica (ト短調 / ト長調, ♩=66, 約 4 分 25 秒)

XX (出だしの伴奏なし、フーガの 4 声だけ) の全音を、9/23・9/24 の録音から切り出した**実録音のピアノの 1 音** (自然に減衰) に置き換えた版。
4 声の音はその主題の元の録音のピアノの音 (動画の色で示す)。最後のト長調の和音もピアノの分散和音。

```bash
python3 compose_tablet21.py bank17.json score_tablet21.json && python3 synth.py score_tablet21.json tablet21.wav && python3 video.py score_tablet21.json tablet21.wav tablet21.mp4
```

## 🎹🕯 Requiem BADA — Tablet Sessions XXII · Summa (集大成, ホ短調 → 変ロ短調 → ヘ短調 → ヘ長調, ♩=56, 約 8 分)

VI〜XXI の集大成。合成の楽器 (ガラスの高音、共鳴シンセ、リード、パッド、低音の正弦波、ロックバンド、パイプオルガン) をすべて消し、
鳴る音は 2026-09-23 / 09-24 の録音 7 本の**実録音のピアノだけ**: 実音の抜粋 (8 秒のクロスフェード)、切り出した 1 音による 4 声のフーガ、
ピアノの低い打鍵から作った柔らかい鼓動。荘厳: Adagio、短調、拍ごとに打ち直す保続低音。洗脳的: 止まらない鼓動、ストレッタ、B-A-D-A の繰り返し。

| 区間 | 内容 |
|---|---|
| Introitus | 11:23 → 08:53 (ホ短調) の実音 |
| Kyrie — Fuga I | 08:53 のバッハ風フーガ (提示 → エピソード → 下属調 → ストレッタ → 保続低音) |
| Graduale | 9/23 08:06 → 11:18 (変ロ短調) の実音 |
| Dies irae — Fuga II | 11:23 と 11:18 の二重フーガ |
| Offertorium | 08:49 (ヘ短調) の実音 |
| Sanctus — Fuga III | 9/23 08:06 と 08:09 の二重フーガ |
| Agnus Dei | B-A-D-A ×2、保続低音の上で |
| Finale | 7 つの主題のストレッタ → 保続低音 |
| In paradisum | 08:49 の本当の終わり → ヘ長調の和音 (pp) |

ステムを測って、フーガと実音を同じくらいに、鼓動はその約 12 dB 下に。

```bash
python3 compose_tablet22.py bank17.json score_tablet22.json && python3 synth.py score_tablet22.json tablet22.wav && python3 video.py score_tablet22.json tablet22.wav tablet22.mp4
```

## 🎛🕯 Requiem BADA — Tablet Sessions XXIII · Summa sintetica (集大成をシンセの実音一色で, ♩=56, 約 8 分)

XXII (Summa) と同じ形式・同じ主題を、**ピアノの音をすべて 2026-09-24 11:21 の録音から切り出したシンセサイザーの持続音 (実音) 一色**に
置き換えたもの。4 声のフーガ、鼓動、分散和音、すべてが VOXSY の 1 つの音色 (`build_synthbank.py` で切り出した 8 音を移調)。
XXII で実音の抜粋だった区間は、その録音の採譜 (打鍵ごとの和音と長さ) をシンセの実音で鳴らし直す (`synth_passage`、和声も録音の和音)。
洗脳的: 減衰しない同じ音色が 8 分間途切れず、鼓動 (シンセの低い音) が最後まで止まらない。

| 区間 | 内容 |
|---|---|
| Introitus | 11:23 → 08:53 (ホ短調) の採譜をシンセで |
| Kyrie — Fuga I | 08:53 のバッハ風フーガ (提示 → エピソード → 下属調 → ストレッタ → 保続低音) |
| Graduale | 9/23 08:06 → 11:18 (変ロ短調) の採譜をシンセで |
| Dies irae — Fuga II | 11:23 と 11:18 の二重フーガ |
| Offertorium | 08:49 (ヘ短調) の採譜をシンセで |
| Sanctus — Fuga III | 9/23 08:06 と 08:09 の二重フーガ |
| Agnus Dei | B-A-D-A ×2、保続低音の上で |
| Finale | 7 つの主題のストレッタ → 保続低音 |
| In paradisum | 08:49 の本当の終わり → ヘ長調の和音をシンセが静かに分散 |

シンセのサンプルは減衰しないので、ピアノ用の強弱 (1.15〜1.3) のままでは合唱がシンセの抜粋より 14 dB 大きくなった。
ステムを測って強弱を 0.7〜0.78 に下げ、フーガ ≈ 抜粋 (RMS 0.06〜0.08)、鼓動はその約 13 dB 下に。

```bash
python3 compose_tablet23.py bank17.json score_tablet23.json && python3 synth.py score_tablet23.json tablet23.wav && python3 video.py score_tablet23.json tablet23.wav tablet23.mp4
```

## 🎛🎹 Requiem BADA — Tablet Sessions XXIV · Attrito (擦れ) — sintetico / pianistico (2 曲, ♩=56, 各約 8 分)

XXII / XXIII と同じ形式・同じ主題 (レクイエム、主題はフーガ) を、**音と音が合わさるときの擦れの微妙なニュアンス**を曲の中で表現するように
作り換えた 2 曲。`compose_tablet24.py <bank> <score> synth|piano` — synth は 11:21 のシンセの実音一色 (XXIII の音)、piano は実録音のピアノ一色 (XXII の音)。

擦れ (attrito) の表現:

1. **掛留 (suspension)** — 自由声部が強拍で 2 度下がるところで、前の音を 1 拍 (短い音なら半拍) 引き伸ばして強拍に持ち越す。
   強拍で他の声部と 2 度・7 度・4 度で擦れ、次の拍で解決する (バッハの「擦れて、ほどける」)。主題と保続低音の音は動かさない。1 曲に 20 か所。
2. **B-A-D-A の 1 拍遅れのカノン** (Agnus Dei) — テノールが 1 拍遅れて同じ動機を追うので、B♭ と A、A と D が常に擦れ合う。
3. **うなるユニゾン** (`synth.py` の `unison_detune`) — 1 音ごとに数セントずらした同じ音を重ね、ゆっくりうなる。
   シンセは 7 セント (C4 で約 1 Hz のうなり)、ピアノは 3 セント (調律のわずかにずれたユニゾン弦のように)。

```bash
python3 compose_tablet24.py bank17.json score_synth.json synth && python3 synth.py score_synth.json synth.wav && python3 video.py score_synth.json synth.wav synth.mp4
python3 compose_tablet24.py bank17.json score_piano.json piano && python3 synth.py score_piano.json piano.wav && python3 video.py score_piano.json piano.wav piano.mp4
```

## 🎹✋✋✋✋ Requiem BADA — Tablet Sessions XXV · A quattro mani impossibili (4 手でなければ不可能, ♩=56, 約 6 分 30 秒)

2026-09-23 / 09-24 の 7 本の録音 (主題と和声) をもとに、**2 本の手では物理的に弾けない不協和音と分散和音**でレクイエムとフーガを作り換えた。
音はすべて録音から切り出したピアノの 1 音 (実音、自然に減衰)。

- **不協和音の塊** — 根音の上に短 2 度・増 4 度・短 9 度・長 7 度を積んだ 12 音を 4〜5 オクターヴにわたって同時に打つ。フーガの入りと Dies irae の各小節の頭で。
- **分散和音の波** — 1 拍 6 音の分散和音が A0 付近から C8 付近までの 6 オクターヴを休みなく往復する。和音の構成音に ♭9・長 7・♭13 を足した不協和な分散和音。
  2 本の波が反行 (片方が上り、片方が下り) で同時に走り、その上に 4 声のフーガ、鼓動、保続低音 — 手が 4 本あってはじめて可能。
- **録音の和声** — Introitus / Graduale / Offertorium では 11:23、08:06、08:49 の採譜の和音進行をそのまま使い、波と塊で鳴らす (`rec_harmony`)。

| 区間 | 内容 |
|---|---|
| Introitus | 11:23 の和声を反行する 2 本の波と 2 小節ごとの塊で |
| Kyrie — Fuga I | 08:53 のバッハ風フーガ、ストレッタから下からの波 |
| Graduale | 9/23 08:06 の和声を 2 本の波と塊で |
| Dies irae — Fuga II | 11:23 と 11:18 の二重フーガ、各小節の頭に 12 音の塊、後半は反行する波 |
| Offertorium | 08:49 の和声を上りの波 1 本で |
| Sanctus — Fuga III | 9/23 08:06 と 08:09 の二重フーガ、下りの波の上で |
| Agnus Dei | B-A-D-A の 1 拍遅れのカノン、保続低音、反行する波 |
| Finale | 7 主題のストレッタ、入りごとに塊、反行する波 → 保続低音 |
| In paradisum | ヘ長調の波が 6 オクターヴを上って遅くなり、12 音の長和音にほどける |

ステムを測って、波と塊は抜粋の区間で RMS ≈ 0.06、フーガの下では −4〜−7 dB、鼓動はその −12 dB に (`GW`)。

```bash
python3 compose_tablet25.py bank17.json score_tablet25.json && python3 synth.py score_tablet25.json tablet25.wav && python3 video.py score_tablet25.json tablet25.wav tablet25.mp4
```

## 🎹📜 Requiem BADA — Tablet Sessions XXVI · Contrapunctus (Contrapunctus XIV のように, ニ短調, ♩=56, 約 4 分)

XXV から分散和音の波を消し、バッハ『フーガの技法』の未完の三重フーガ Contrapunctus XIV の形で作り換えたレクイエム。
Contrapunctus XIV の第 2 主題 (駆け足の 8 分音符) は入れず、代わりに 9/23 の主題をゆっくり歌う。音はすべて実録音のピアノ。

| Sectio | 内容 |
|---|---|
| I | 第 1 主題 = 9/24 08:53 の主題: 4 声の提示 → エピソード → 反行形 (S, T) → 低音の拡大形 (2 倍の長さ) |
| II | 第 2 主題 = 9/23 08:06 の主題 (ゆっくり): 4 声の提示 → 第 1 主題と重なる二重フーガ |
| III | 第 3 主題 = B-A-D-A (バッハの B-A-C-H の代わり): 4 声の提示 → 3 つの主題を同時に重ねる三重フーガ (2 回目は第 1 主題を拡大で低音に) → 2 回目の途中、小節の 2 拍目で楽譜が途切れる → 鼓動だけが 8 小節かけて消える |

各 Sectio の頭に XXV の 12 音の塊をひとつ (弔鐘)。主題の入りはすべてオクターヴ (属調の答唱は使わない)。
`post` が途切れる位置 (`CUT`) 以降の音を切り、鼓動の音量を `TAIL` で下げていく。

```bash
python3 compose_tablet26.py bank17.json score_tablet26.json && python3 synth.py score_tablet26.json tablet26.wav && python3 video.py score_tablet26.json tablet26.wav tablet26.mp4
```

## 🎹🌀 Requiem BADA — Tablet Sessions XXVII · Contrapunctus turbato (乱れる三重フーガ + 9/23・9/24 の実音, ♩=56, 約 7 分)

XXVI (Contrapunctus XIV の形) をもとに、フーガの入りを「乱し」、9/23・9/24 の実音の抜粋をミックスした。音はすべて実録音のピアノ。

- **乱れる入り (turbato)** — 主題が小節の頭ではなく拍の途中で、不揃いな間隔 (1.5 小節、3 拍、半小節、1 拍) で崩れ込むように入る。
  原形・反行形・拡大形 (2 倍)・縮小形 (半分) が同じ小節の中で同時に走る。B-A-D-A は 2 拍ごとの密なストレッタ。三重フーガでも 3 つの主題が拍をずらして重なる。
- **実音の抜粋** — 各 Sectio の前に 8 秒のクロスフェードでミックス: Introitus 11:23 → 08:53 (ホ短調)、Interludium I 9/23 08:06 → 9/24 11:18 (変ロ短調)、
  Interludium II 08:49 → 11:21 (ヘ短調)。フーガはその抜粋の調で歌う (`CT.LAYOUT`)。
- 最後は XXVI と同じく、2 度目の三重の重なりの途中、小節の 2 拍目で楽譜が途切れ、鼓動だけが 8 小節かけて消える。

```bash
python3 compose_tablet27.py bank17.json score_tablet27.json && python3 synth.py score_tablet27.json tablet27.wav && python3 video.py score_tablet27.json tablet27.wav tablet27.mp4
```

## 🎹🎛 Requiem BADA — Tablet Sessions XXVIII · Lento ipnotico (2026-09-25 の 3 本, ♩=42, 約 5 分)

2026-09-25 の録音 3 本 — 12:46:43 (ヘ短調、途中にシンセサイザーの実音)、12:50:53 (ロ短調)、13:04:31 (変ホ短調、ゆっくり) — から。
速さは 13:04 に合わせて ♩=42 (Contrapunctus XIV より遅い)。レクイエムとフーガが交互に雰囲気を変える:

- **Requiem** — 実音の抜粋 (録音そのもの) の下で、12:46 の途中から切り出したシンセの持続音 (実音、`build_synthbank.py`、29 音) が
  録音の和音を 1 小節ずつ静かに支える (`PAD`)。鼓動は最後まで止まらない。
- **Fuga** — その録音の主題 (`CT.make_subject`、♩=42 なので 3〜6 音のゆっくりした主題) を、録音から切り出したピアノの 1 音で 4 声のフーガに。
  主題の入りにシンセの実音が 1 オクターヴ上で重なる。

| 区間 | 内容 |
|---|---|
| Requiem I | 13:04 の実音 (変ホ短調) |
| Fuga I | 13:04 の主題の提示 → ストレッタ |
| Requiem II | 12:46 の途中、シンセが鳴っている実音 (ヘ短調) |
| Fuga II | 12:46 と 13:04 の二重フーガ |
| Requiem III | 12:50 の実音 (ロ短調) |
| Fuga III | 12:50 の主題の提示 → 3 つの主題が同時に重なる三重フーガ → ストレッタ |
| Requiem finale | 13:04 の本当の終わり → シンセの和音が残り、鼓動とともに消える |

ステム: 実音 ≈ フーガ ≈ 0.05、シンセの支え −5 dB、鼓動 −13 dB。

```bash
python3 build_sampler.py bank25 20260925_124643.mp3 20260925_125053.mp3 20260925_130431.mp3
python3 build_synthbank.py 20260925_124643.mp3 sybank25 0.4 0.2      # bank26.json = bank25 + sybank25 の samples
python3 compose_tablet28.py bank26.json score_tablet28.json && python3 synth.py score_tablet28.json tablet28.wav && python3 video.py score_tablet28.json tablet28.wav tablet28.mp4
```

## 🎌🕯 Requiem BADA — Tablet Sessions XXIX · Kimigayo (君が代をハ短調で — アステールプラザの国歌斉唱, ♩=48, 約 4 分 30 秒)

2026-09-25 の 3 本の録音をミックスし、日本国歌「君が代」(林廣守の旋律、公有) を B♭ 版の高さ (主音 C) で **ハ短調 (C minor) の上に**置いた。
和声は Cm に **E♭・G♭・B♭ の長三和音** (i・♭III・♭V・♭VII) — 旋律の D・F・G が E♭・G♭ と擦れ、荘厳で洗脳的な響きになる (`harm_flat`)。
情景: 小学校 6 年生の剣道試合、アステールプラザの国歌斉唱。**冷たい外気** = 高い E♭6・G♭5・B♭5 のシンセの実音 (12:46 から切り出した) が細く持続する (`COLD`)。
**子孫とご先祖様への眼差し** = ゆっくり ♩=48、止まらない鼓動、最後は全声部がユニゾンの C に集まる (国歌の終わりと同じ)。

| 区間 | 内容 |
|---|---|
| Introitus | 13:04 の実音を C minor に移調 (`pshift`) → 冷たい外気のシンセ、鼓動 |
| Kimigayo I — 斉唱 | 「君が代は」を 4 声がオクターヴのユニゾンで → 続く 4 句はテノールの定旋律、上に自由声部 |
| Fuga | 第 1 句 D D C D E G E D (→ C C B♭ C D F D C) を主題に、A → S → T → B の提示 → 拍をずらしたストレッタ |
| Interludium | 12:46 のシンセの部分の実音を C minor に |
| Kimigayo II — 荘厳 | 全旋律をソプラノに、拍ごとに打ち直す保続低音の C、シンセの和音 E♭・G♭・B♭ → ユニゾンの C |
| Coda | 13:04 の本当の終わり (C minor に) → ユニゾンの C と冷たいシンセが鼓動とともに消える |

ニ短調の枠で書いて `CT.LAYOUT` で −2 半音 (旋律は主音 D で書き、C になる)。表示の和音名は G♭・A♭ に直す。

```bash
python3 compose_tablet29.py bank26.json score_tablet29.json && python3 synth.py score_tablet29.json tablet29.wav && python3 video.py score_tablet29.json tablet29.wav tablet29.mp4
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
