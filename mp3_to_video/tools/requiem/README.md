# Requiem Piano — 録音した旋律をグランドピアノのレクイエムに編曲する

スマホなどで録った旋律(歌・口ずさみ・楽器)から音符を取り出し、ヘ短調のレクイエム調ピアノ独奏に編曲して、
暗い聖堂風の動画(写真を重ねることも可能)まで一気に作るツール群です。`Bada SoundFilm` の姉妹ツール。

## 出来上がり(2026-09-20 の録音 2 本から)

- [`../../requiem/requiem_piano.mp3`](../../requiem/requiem_piano.mp3) — 音楽(4 分 11 秒)
- [`../../requiem/requiem_piano.mp4`](../../requiem/requiem_piano.mp4) — 動画(1280×720 / 24 fps)

構成: 序奏(鐘と「怒りの日」の旋律)→ 第 1 楽章(録音 1 の旋律 + 分散和音)→ 間奏 → 第 2 楽章(録音 2 の旋律 + 賛美歌風の和音、クライマックス)→ 終結(ヘ長調のピカルディ終止)。

## 使い方

```sh
FF=ffmpeg                                      # ffmpeg のパス
sh fetch_piano_samples.sh piano "$FF"          # 1. 88 鍵ぶんのピアノ音源を取得(初回のみ・約 26 MB)
"$FF" -i 録音.m4a -ac 1 -ar 22050 rec.wav      # 2. 録音を WAV に
python3 melody_extract.py rec.wav              # 3. 旋律を音符 JSON に(rec_notes.json)
python3 requiem_piano.py --notes rec_notes.json 別の録音_notes.json --samples piano --out requiem.wav
                                               # 4. 編曲してレンダリング(requiem.wav と requiem.wav.events.json)
python3 requiem_video.py --audio requiem.wav --events requiem.wav.events.json \
    --photo 写真1.jpg 写真2.jpg --out requiem.mp4 --ffmpeg "$FF"
                                               # 5. 動画に(写真は任意・複数可。無ければろうそくの灯りだけ)
```

依存: Python 3 + `numpy` `scipy` `pillow`、ffmpeg。

## 仕組み

- **melody_extract.py** — 自己相関でピッチを追い、メディアンで平滑化して音符に区切る(短すぎる音・無音は捨てる)。
- **requiem_piano.py** — 音符をヘ短調(導音 E を含む)に吸着し、音域を折り畳み、8 分音符のグリッドへ量子化。
  4 拍(第 2 楽章は 2 拍)ごとに旋律へ最も合う和音(i / VI / iv / V / III / VII / ii° / v)を選び、
  分散和音・賛美歌風和音・鐘の低音・「怒りの日」動機を組み合わせて楽譜にする。
  ピアノは 88 鍵の実サンプルを使い、短く切れた尾を音高ごとの減衰でループ延長。ダンパーペダル・打鍵強さによる音色変化・
  音高に応じた定位・コンボリューションの残響・やわらかいリミッタでマスタリング。
- **requiem_video.py** — 暗い石壁のグラデーション + ろうそくの灯り + ボケ + 舞い上がる灰 + 演奏に合わせて金色に灯る
  88 鍵の鍵盤。写真を渡すとセピア寄りに落として、ゆっくりズーム・パン(ケン・バーンズ)しながらクロスフェードで重ねる。
