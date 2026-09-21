# Bada Suite — 自作素材だけで編曲した組曲 (mp4)

アップロードされた自作の音源・MIDI だけを素材にして、一本の組曲 (約 11 分 30 秒, 1280x720, 30 fps) に編曲する生成スクリプト。

## 構成

| 楽章 | 素材 | 処理 |
|---|---|---|
| I. Ave (SATB) | `ave_satb.mid` | MIDI を numpy の加算合成で新規レンダリング。母音「ア」のフォルマントを持つ合唱シンセ (3 声デチューン + ビブラート) と減衰ピアノ層を重ね、S/A/T/B を左右に定位 |
| II. Requiem in F minor | `requiem_piano.mp3` | 原音ピアノ + 1 オクターブ下 (rubberband) をローパスした「ゴースト層」 + ホール残響。映像は SoundFilm 版からピアノロール版へ途中で切替 |
| III. Contrapunctus 14 | `La_Japonaise_Contrapunctus14.mp4` | 同上 (La Japonaise の映像) |
| IV. Coda | `20260920_154001.mp4`, `20260920_154118.mp4` | ハイパス + 残響で包む |

楽章間は 4 秒の等パワー・クロスフェード。残響は合成インパルス応答 (RT60 ≈ 2.6 s) の畳み込み。
各楽章を RMS で揃え、最後にソフトリミッタでまとめている。

## 含めなかったもの

- 坂本龍一 (Sweet Revenge / A Flower Is Not a Flower / Little Buddha / The Last Emperor)、LUNA SEA (Ray) の楽曲は、音源が手元になく、著作権のある楽曲を再現する形になるため入れていない。
- 実在の歌手 (LUNA SEA の RYUICHI) の声の再現は行っていない。

## 使い方

```sh
pip install numpy scipy mido pillow imageio-ffmpeg
python3 make_suite.py <素材ディレクトリ> <出力ディレクトリ>
# 音声を再利用して映像だけ作り直す場合
REUSE_AUDIO=1 python3 make_suite.py <素材ディレクトリ> <出力ディレクトリ>
```

出力: `<出力ディレクトリ>/Bada_Suite.mp4` (ほかに `bada_suite_master.wav`, タイトルカード PNG)。
日本語フォントは IPA ゴシック (`/usr/share/fonts/truetype/fonts-japanese-gothic.ttf`) を使う。
