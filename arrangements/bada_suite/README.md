# Bada Suite — 自作素材だけで編曲した組曲 (mp4)

アップロードされた自作の音源・MIDI だけを素材にして、一本の組曲 (約 11 分 30 秒, 1280x720, 30 fps) に編曲する生成スクリプト。

## 構成

楽章間は 4 秒の等パワー・クロスフェード。調性でつながるように並べている。
手持ちの音源 (WMA) が素材ディレクトリに無ければ、その楽章は自動的に省かれる。

| 楽章 | 素材 | 処理 |
|---|---|---|
| I. Ave (SATB, D) | `ave_satb.mid` | MIDI を numpy の加算合成で新規レンダリング。母音「ア」のフォルマントを持つ合唱シンセ (3 声デチューン + ビブラート) と減衰ピアノ層を重ね、S/A/T/B を左右に定位 |
| II. Requiem in F minor | `requiem_piano.mp3` | 原音ピアノ + 1 オクターブ下 (rubberband) をローパスした「ゴースト層」 + ホール残響。映像は SoundFilm 版からピアノロール版へ途中で切替 |
| III. トラック 18 (Fm) | `18______18.wma` (任意) | 同上。映像はスペクトラム (fire) |
| IV. Contrapunctus 14 (Dm) | `La_Japonaise_Contrapunctus14.mp4` | 同上 (La Japonaise の映像) |
| V. トラック 8 (Gm) | `08______8.wma` (任意) | 同上。映像はスペクトラム (cool) |
| VI. MOTHER — LUNA SEA (Gm) | `10_MOTHER.wma` (任意) | 原曲の歌声をそのまま使い、軽い残響のみ。映像はスペクトラム (magma) |
| VII. Coda | `20260920_154001.mp4`, `20260920_154118.mp4` | ハイパス + 残響で包む |

残響は合成インパルス応答 (RT60 ≈ 2.6 s) の畳み込み。各楽章を RMS で揃え、最後にソフトリミッタでまとめている。

## 注意

- 坂本龍一の楽曲 (Sweet Revenge / A Flower Is Not a Flower / Little Buddha / The Last Emperor) と LUNA SEA「Ray」は音源が無いため入れていない。
- 歌声は「MOTHER」の原曲録音そのもので、歌手の声を合成・模倣してはいない。
- 市販音源を含む出力は私的利用の範囲にとどめること。公開・配布には権利者の許諾が要る。

## 使い方

```sh
pip install numpy scipy mido pillow imageio-ffmpeg
python3 make_suite.py <素材ディレクトリ> <出力ディレクトリ>
# 音声を再利用して映像だけ作り直す場合
REUSE_AUDIO=1 python3 make_suite.py <素材ディレクトリ> <出力ディレクトリ>
# 配布用 540p を指定した楽章の頭で前半/後半に分ける場合 (例: track8)
SPLIT_AT=track8 python3 make_suite.py <素材ディレクトリ> <出力ディレクトリ>
```

出力: `<出力ディレクトリ>/Bada_Suite.mp4` (720p 本体), `Bada_Suite_540p.mp4` または `Bada_Suite_part1_540p.mp4` / `Bada_Suite_part2_540p.mp4` (配布用 2 パス), `Bada_Suite_audio.mp3`, `bada_suite_master.wav`, タイトルカード PNG。
日本語フォントは IPA ゴシック (`/usr/share/fonts/truetype/fonts-japanese-gothic.ttf`) を使う。
