# biofeedback_audio — バイオフィードバック 音ジェネレータ

名前付きプリセットそれぞれに **キャリア周波数** と **バイノーラルビート周波数**
を割り当て、16bit / 44.1kHz / ステレオ の **WAV** ファイルとしてサイン波の音を
生成する C 製コマンドラインツールです。

- 左チャンネル: `sin(2π·carrier·t)`
- 右チャンネル: `sin(2π·(carrier+beat)·t)`
- 左右の周波数差 `beat` が「うなり（binaural beat）」として知覚されます。
  これはリラクゼーション/集中などのバイオフィードバック用途で用いられる音響手法です。
- クリックノイズ抑制のためフェードイン/アウトのエンベロープを付与します。

## ⚠️ 重要な注意

本ツールは **音響トーン発生器** です。プリセット名（リスパダール、ジプレキサ等）は
単なる **ラベル** であり、薬剤そのものやその薬効・治療効果を再現・代替するもの
ではありません。**特定の周波数に医学的・治療的効果があるという主張は一切しません。**
体調・治療に関する判断は必ず医師・薬剤師に相談してください。
大音量・長時間の使用は避け、不快を感じたら直ちに中止してください。

## ビルド

```sh
make
# または
gcc -std=c99 -O2 -Wall -o biofeedback_audio biofeedback_audio.c -lm
```

## 使い方

```sh
./biofeedback_audio list                                  # プリセット一覧
./biofeedback_audio gen <preset|all> [seconds] [outdir]   # 生成
./biofeedback_audio custom <carrier_hz> <beat_hz> <sec> <out.wav>
```

### 例

```sh
./biofeedback_audio list
./biofeedback_audio gen risperdal 30          # risperdal.wav を 30 秒
./biofeedback_audio gen all 20 ./out          # 全プリセットを ./out に 20 秒ずつ
./biofeedback_audio custom 200 8 60 alpha.wav # carrier200Hz/beat8Hz を 60 秒
make demo                                     # 全プリセットを ./out に 10 秒で生成
```

生成した `.wav` は任意のプレイヤー（`aplay`, `ffplay`, `afplay`, メディアプレイヤー等）
で再生できます。**バイノーラルビートはヘッドホン/イヤホンでの再生を前提**とします
（左右の音が混ざらないため）。

## プリセットと周波数

| key | ラベル | carrier | beat | 帯域 |
|-----|--------|--------:|-----:|------|
| risperdal | リスパダール | 174.0Hz | 3.0Hz | delta |
| zyprexa | ジプレキサ | 185.0Hz | 3.5Hz | delta |
| silece | サイレース | 110.0Hz | 1.5Hz | delta |
| depas | デパス | 210.0Hz | 6.0Hz | theta |
| etizolam | エチゾラム | 216.0Hz | 6.5Hz | theta |
| brotizolam | ブロチゾラム | 128.0Hz | 2.0Hz | delta |
| rohypnol | ロヒプノール | 120.0Hz | 1.0Hz | delta |
| sancoba | サンコバ | 396.0Hz | 10.0Hz | alpha |
| hyaluronic | ヒアルロン酸 | 417.0Hz | 10.5Hz | alpha |
| lendormin | レンドルミン | 132.0Hz | 2.5Hz | delta |
| luran | ルーラン | 198.0Hz | 4.5Hz | theta |
| saphris | シクレスト | 222.0Hz | 5.0Hz | theta |
| sennoside | センノサイド | 288.0Hz | 9.0Hz | alpha |
| akineton | アキネトン | 256.0Hz | 8.0Hz | alpha |
| biperiden | ビペリデン | 264.0Hz | 8.5Hz | alpha |
| amel | アメル | 333.0Hz | 9.5Hz | alpha |
| benzalin | ベンザリン | 144.0Hz | 2.0Hz | delta |
| levotomin | レボトミン | 160.0Hz | 4.0Hz | theta |

> beat の目安: delta ~0.5–4Hz（深い休息）/ theta ~4–8Hz（深いリラックス）/
> alpha ~8–13Hz（リラックス）/ beta ~13–30Hz（覚醒・集中）。
> 周波数の割り当ては心地よい可聴域に分散させた**任意の設計値**であり、
> 各薬剤の物性や薬効に由来するものではありません。
