# 🎼 Bada Fusion Suite — Fuga · Requiem · Ave Verum · Acceptance

**バッハのフーガとレクイエム(パッサカリア)、モーツァルト《アヴェ・ベルム・コルプス》の「ほっと一安心」、
坂本龍一《Sweet Revenge》《鉄道員》《Acceptance (Little Buddha)》の様式を、アップロードされた 16 本の録音と合成した 6 楽章・約 7 分の組曲。**
依存最小(numpy / scipy / Pillow / ffmpeg)の加算合成シンセで作曲・演奏・録画まで自動生成する。

### 👉 [**bada_fusion_suite.mp4 をダウンロード**](bada_fusion_suite.mp4)(1280×720 / H.264 + AAC / 6:55)

> 旋律・和声はすべてオリジナル。バッハとモーツァルトは公有の「様式」(フーガ・パッサカリア・コラール)に倣い、
> 坂本龍一作品は旋律を引用せず、和声語法(add9・借用和音・ピアノと弦の書法)と「静けさ」の様式だけを参照している。

## 楽章構成

| # | 楽章 | 調 / テンポ | 内容 |
|:-:|:--|:--|:--|
| I | **前奏 — 瞑想** | A minor · ♩=60 | A のドローン + フーガ主題の 4 倍拡大形を疎らなピアノで。録音を半速・1 オクターブ下で「霧」に |
| II | **フーガ**(バッハ様式) | A minor · ♩=72 | 3 声。主題 → 属調の実応答 → 八度で転回可能な対主題 → 嬉遊部(Am–G–F–E)→ 平行長調 C の中間部 → 嬉遊部(Dm–Em–F–E7)→ 2 拍遅れのストレッタ → 属音保続 → ピカルディ終止(A major) |
| III | **レクイエム — パッサカリア** | A minor · ♩=60 | 半音階で下る「嘆きのバス」A–G♯–G–F♯–F–E–D–E–A を 6 周。合唱(母音フォルマント合成)・弦の哀歌・ピアノのアルペジオが周ごとに重なり、最終周は **E7 のまま止まる** |
| IV | **コラール — ほっと一安心**(アヴェ・ベルム・コルプス様式) | F major · ♩=58 | E7 → F の**偽終止**で光が差し込む。四声体コラール 16 小節、4–3 掛留、第 4 楽句でクライマックス |
| V | **バラード — 郷愁**(坂本龍一様式) | F major · ♩=66 | Fmaj9 – C/E – Dm9 – B♭maj7 – Gm7 – C7sus … E♭maj7(借用)– B♭m の和声にピアノ旋律。後半は鐘と弦が旋律を重ねる |
| VI | **コーダ — 受容**(Acceptance 様式の瞑想) | F major · ♩=50 | F のドローン、パッド、疎らなピアノ、鐘。息を吐き、静かに消える |

## アップロード音源の配置(調で振り分け)

推定調(クロマ相関)で楽章を決め、ローパス / ハイパス / ピッチシフト / タイムストレッチ(rubberband)/ フェード / リバーブ送りで溶け込ませている。

| 楽章 | 音源 | 処理 |
|:--|:--|:--|
| I 前奏 | 20260922_090933(A min)、20260922_090146(G maj) | 半速 + 1 オクターブ下、LPF 1.2 kHz / 500 Hz |
| II フーガ | 20260922_174527(A min) | LPF 2.5 kHz、遠景 |
| III レクイエム | 20260922_174820、20260922_174031、20260922_175717(A min)、20260922_175145(B♭ min) | LPF 2–2.5 kHz / B♭ min は半速・オクターブ下の霧 |
| IV コラール | 20260920_154001、20260920_154118(F maj) | LPF 2 kHz |
| V バラード | Bada_Suite_audio(F maj)、20260922_175429・175316(B♭ min) | LPF 4 kHz / 霧 |
| VI コーダ | 20260922_175644(息)、Bada_Suite_audio-1(C maj)、20260922_175951(G maj)、20260920_154001.mp4 音声 | 半速、LPF 1.5 kHz |

## 仕組み

- [`synth.py`](synth.py) — 加算合成の楽器(piano / strings / pad / organ / choir / bell / drone / harp)、ADSR、畳み込みリバーブ(合成インパルス応答)、パン付きミキサー
- [`compose.py`](compose.py) — 楽譜(拍 → 秒 のシーケンサ)と 6 楽章の作曲、録音レイヤーの配置、マスタリング(ソフトリミッタ)
- [`video.py`](video.py) — 対数周波数 64 バンドのスペクトラムを numpy で描画(短調は青紫、長調は琥珀色)、楽章カード(IPA ゴシック)、rawvideo → libx264 パイプ

## 再生成

```bash
pip install numpy scipy pillow imageio-ffmpeg
export FFMPEG=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
export UPLOADS=/path/to/recordings   # 省略すると録音レイヤーなしで合成だけ行う
export OUT=/tmp/fusion_out
python3 fusion_suite/compose.py                                  # → $OUT/bada_fusion_suite.wav + marks.json
python3 fusion_suite/video.py $OUT/bada_fusion_suite.wav $OUT/bada_fusion_suite.mp4
```

対位法の検査(強拍の不協和を列挙)は `compose.fugue` に記録用ミキサーを渡して行える(開発時に使用。残るのは属七・終止四六・4–3 掛留のみ)。
