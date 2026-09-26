# Bada Requiem — 手持ちの録音をレクイエムに作り換える

坂本龍一「Libera me」や LUNA SEA「MOTHER」の *requiem* が醸し出す、包み込む(all-round)音楽像を目標に、
自分の録音 (mp3 など) を素材として一本のレクイエム (約 10 分) に再構成し、**mp4** で書き出すスクリプトです。

```
python3 build_requiem.py --src <録音ディレクトリ> --out output
#   → output/requiem.wav, output/requiem.mp4, output/chords.txt
python3 build_requiem.py --src <録音ディレクトリ> --out output --quick   # 40 秒だけ確認用
python3 build_requiem.py --src <録音ディレクトリ> --out output --no-video
```

依存: `pip install numpy scipy librosa soundfile pillow imageio-ffmpeg`
(ffmpeg 本体は imageio-ffmpeg が同梱するものを使うので、別途インストール不要)

## 仕組み

| 段階 | 内容 |
|---|---|
| 1. 解析 | 各素材の調を Krumhansl プロファイルで推定し、F minor 一族 (Fm / B♭m / A♭ / D♭) に **±1 半音以内**で移調 |
| 2. 引き伸ばし | 旋律用はフェーズボコーダ (×1.0〜1.5)、残響雲用は **Paulstretch** (×2〜5)。左右で別乱数の位相を使い自然なステレオに |
| 3. ハーモニー層 | オクターブ上下・五度の層をリサンプリングで作り、ローパスして聖歌隊のように重ねる |
| 4. 楽章配置 | Introitus / Kyrie / Dies irae / Lacrimosa / Libera me / Lux aeterna の六楽章に素材を割り当て |
| 5. 和音追従 | 配置済み素材の Chroma から**小節ごとに和音を推定**し、聖歌隊パッド・弦・オルガン・ピアノがそれを追いかける (素材と伴奏が衝突しない)。終止はピカルディ (F major) |
| 6. 打楽器・鐘 | 鐘 (非整数倍音) が楽章の入口を告げ、怒りの日にはティンパニの ♩♪♪♩ が入る |
| 7. マスタリング | 楽章ごとのダイナミクス曲線 → 大聖堂リバーブ (RT60 ≈ 5.5 s) → ソフトリミッタ |
| 8. 映像 | ffmpeg `showcqt` の CQT スペクトラムを鏡像合成して大聖堂の柱のように描き、楽章タイトル (ラテン典礼文 + 和訳) をフェードで重ねて H.264 / AAC の mp4 に |

## 楽章構成 (既定)

| 楽章 | 時間 | 素材の使い方 |
|---|---|---|
| I. Introitus — Requiem aeternam | 0:00–1:40 | 鐘、オルガンのドローン、素材を 4 倍に引き伸ばした雲 |
| II. Kyrie | 1:40–3:15 | B♭ minor の素材群、弦が加わる |
| III. Dies irae | 3:15–5:00 | 密度と緊張、ティンパニ、原速に近い素材 |
| IV. Lacrimosa | 5:00–6:40 | 長調の素材で光が差す、ピアノのアルペジオ |
| V. Libera me | 6:40–8:40 | F minor 回帰、最大の厚み |
| VI. Lux aeterna | 8:40–10:20 | 極端に引き伸ばした光、F major で終止 |

素材が 16 本より少ない場合は巡回して割り当てます。`SECTIONS` / `put(...)` の行を編集すれば配置を変えられます。

## 出力

- `requiem.wav` — 44.1 kHz / 16 bit ステレオ
- `requiem.mp4` — 1280×720 / 30 fps / H.264 + AAC 224 kbps
- `chords.txt` — 推定した和音進行 (開始秒, 終了秒, 和音, 楽章)

生成物のうち、圧縮版 `output/requiem_compact.mp4` (960×540, 24 MB) と `output/chords.txt` だけをリポジトリに含めています。フル解像度版 (1280×720, 65 MB) はスクリプトを実行して生成してください。
