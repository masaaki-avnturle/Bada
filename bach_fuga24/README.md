# 🎼 Fuga XXIV — J. S. Bach《コントラプンクトゥス XIV》による 24 のフーガ

**アップロードされた 16 本の録音を実音源(サンプラー)として、J. S. Bach《フーガの技法》の未完の四重フーガ
Contrapunctus XIV (BWV 1080/19) の主題を 12 音階の全 12 調 × {正行, 反行} = 24 曲のフーガに展開し、
ピアノロール付き MP4 (1280×720 / 30 fps / H.264 + AAC) として書き出す。** 外部の音源・音楽ライブラリは使わない。
音を出しているのは録音から切り出した 1,700 余りの断片だけである。

## 🜂 音階の秘密の原理 (the secret principle of the scale)

24 曲は次の 3 つの原理だけから機械的に導かれる。

1. **B-A-C-H が 12 音階を敷き詰める。** B-A-C-H = {B♭, A, C, B} は半音 4 つの塊 {9, 10, 11, 0} である。
   これを長 3 度 (4 半音) ずつ 3 回並べると
   **{B♭ A C B} + {D C♯ E E♭} + {F♯ F A♭ G} = 12 音すべてが一度ずつ** 現れる。
   バッハの署名がそのまま 12 音列 (BACH 列) になる。この列をエピソードと最終ストレッタの素材に使う。
2. **B♭ と C♯ は鏡像である。** ニ短調の和声的音階 D E F G A B♭ C♯ を第 3 音 F を軸に鏡映すると
   D↔A, E↔G, F↔F, **B♭↔C♯**。この鏡映を「反行 (inversus)」の定義にする(Cp. XII / XIII の rectus–inversus と同じ発想)。
   B-A-C-H 主題を反行させると C♯-D-B-C になり、C♯ が現れる。
3. **完全 5 度 (7 半音) は 12 と互いに素。** D から 5 度ずつ上がれば 12 の調をすべて一周する:
   D → A → E → B → F♯ → C♯ → A♭ → E♭ → B♭ → F → C → G。各調に正行と反行の 2 曲 → **24 曲**。

## 🎹 主題と構成

各曲は 72 小節 (alla breve、4 分音符 = 100)、約 2 分 56 秒。4 声 (Bass / Tenor / Alto / Soprano)。

| 記号 | 主題 | 出典 |
|:--|:--|:--|
| **S1** | D–A–F–E–D–**C♯**–D–E–F | Cp. XIV 第 1 主題 |
| **S2** | 8 分音符の走句 (S1 と S3 に対して拍ごとに協和するよう設計) | Cp. XIV 第 2 主題 |
| **S3** | **B♭**–A–C–B (B-A-C-H) + 尾部 | Cp. XIV 第 3 主題 |
| **S4** | D–A–F–D–C♯–D–E–F–G–F–E–D | 《フーガの技法》主題 — Cp. XIV に書かれなかった第 4 主題 |

| 小節 | 区分 |
|:--|:--|
| 1–16 | 提示部 I — S1 を Bass → Tenor (属調応答) → Alto → Soprano |
| 17–20 | エピソード 1 — BACH 12 音列の模倣 |
| 21–36 | 提示部 II — S2、S1 との二重結合 (声部配置は不協和最小で探索) |
| 37–40 | エピソード 2 — BACH 列の逆行と原形の交差 |
| 41–56 | 提示部 III — B-A-C-H、S1 との結合、S1 + S2 + S3 の三重結合 (原曲 233 小節以降に相当) |
| 57–61 | エピソード 3 — 12 音列の 4 声ストレッタ |
| 62–69 | **完結部** — S1 + S3 + S2 の上に Bass が 2 小節休んで S4 (《フーガの技法》主題) が入る四重結合。Soprano の S1 ストレッタ |
| 70–72 | 終止 — iv – V – I (ピカルディの 3 度) |

正行曲では応答は属調 (+7)、反行曲では下属調 (−5)。自由声部は規則ベースの対位法生成器
(拍上の協和 / 並行 5・8 度の回避 / 声部交差の回避 / 導音の解決 / 音域) で埋める。

## 🔊 実音源 (サンプラー)

1. `segment.py` — 16 本の録音を自己相関でピッチ追跡し、音高が 0.6 半音以内に安定した 0.18 秒以上の断片を切り出す (1,788 断片、E1〜B♭5)。
2. `render.py` — 各音符に対して、目標音高に最も近い断片 (声部ごとに担当録音を割り当て) を選び、
   再サンプリングでピッチシフト (±9 半音以内)、足りない長さは中間部をクロスフェードでループして伸ばし、
   包絡・定位・簡易残響をかけて 4 声をミックスする。合成音・楽器音源は一切使わない。

## 🎬 生成

```
./run_all.sh <16 本の mp3 があるディレクトリ> <作業ディレクトリ>
```

`compose.py` (作曲) → `midi.py` (MIDI) → `render.py` (実音源で演奏、WAV) → `video.py` (ピアノロール MP4)。
依存: Python 3.11, numpy, scipy, pillow, imageio-ffmpeg。`fugues.json` に 24 曲の全音符 (声部 / 開始拍 / 長さ / 音高 / 役割) を保存、
`midi/` に 24 曲の Standard MIDI File を同梱する。MP4 は `out/` に生成される (サイズが大きいためリポジトリには含めない)。

## 📜 24 曲

| # | 調 | 形 | shift | ファイル |
|:--|:--|:--|--:|:--|
| 01 | ニ短調 (D minor) | 正行 rectus | +0 | `Fuga01_D_minor_rectus.mp4` |
| 02 | ニ短調 (D minor) | 反行 inversus | +0 | `Fuga02_D_minor_inversus.mp4` |
| 03 | イ短調 (A minor) | 正行 rectus | -5 | `Fuga03_A_minor_rectus.mp4` |
| 04 | イ短調 (A minor) | 反行 inversus | -5 | `Fuga04_A_minor_inversus.mp4` |
| 05 | ホ短調 (E minor) | 正行 rectus | +2 | `Fuga05_E_minor_rectus.mp4` |
| 06 | ホ短調 (E minor) | 反行 inversus | +2 | `Fuga06_E_minor_inversus.mp4` |
| 07 | ロ短調 (B minor) | 正行 rectus | -3 | `Fuga07_B_minor_rectus.mp4` |
| 08 | ロ短調 (B minor) | 反行 inversus | -3 | `Fuga08_B_minor_inversus.mp4` |
| 09 | 嬰ヘ短調 (F# minor) | 正行 rectus | +4 | `Fuga09_Fs_minor_rectus.mp4` |
| 10 | 嬰ヘ短調 (F# minor) | 反行 inversus | +4 | `Fuga10_Fs_minor_inversus.mp4` |
| 11 | 嬰ハ短調 (C# minor) | 正行 rectus | -1 | `Fuga11_Cs_minor_rectus.mp4` |
| 12 | 嬰ハ短調 (C# minor) | 反行 inversus | -1 | `Fuga12_Cs_minor_inversus.mp4` |
| 13 | 変イ短調 (Ab minor) | 正行 rectus | +6 | `Fuga13_Ab_minor_rectus.mp4` |
| 14 | 変イ短調 (Ab minor) | 反行 inversus | +6 | `Fuga14_Ab_minor_inversus.mp4` |
| 15 | 変ホ短調 (Eb minor) | 正行 rectus | +1 | `Fuga15_Eb_minor_rectus.mp4` |
| 16 | 変ホ短調 (Eb minor) | 反行 inversus | +1 | `Fuga16_Eb_minor_inversus.mp4` |
| 17 | 変ロ短調 (Bb minor) | 正行 rectus | -4 | `Fuga17_Bb_minor_rectus.mp4` |
| 18 | 変ロ短調 (Bb minor) | 反行 inversus | -4 | `Fuga18_Bb_minor_inversus.mp4` |
| 19 | ヘ短調 (F minor) | 正行 rectus | +3 | `Fuga19_F_minor_rectus.mp4` |
| 20 | ヘ短調 (F minor) | 反行 inversus | +3 | `Fuga20_F_minor_inversus.mp4` |
| 21 | ハ短調 (C minor) | 正行 rectus | -2 | `Fuga21_C_minor_rectus.mp4` |
| 22 | ハ短調 (C minor) | 反行 inversus | -2 | `Fuga22_C_minor_inversus.mp4` |
| 23 | ト短調 (G minor) | 正行 rectus | +5 | `Fuga23_G_minor_rectus.mp4` |
| 24 | ト短調 (G minor) | 反行 inversus | +5 | `Fuga24_G_minor_inversus.mp4` |
