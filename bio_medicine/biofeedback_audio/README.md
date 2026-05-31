# biofeedback_audio — バイオフィードバック 音アプリ（IRセンサー + 温度計 + GUI）

名前付きプリセットそれぞれに **キャリア周波数** と **バイノーラルビート周波数**
を割り当て、サイン波の音（16bit/44.1kHz/ステレオ WAV）を生成するアプリです。
**赤外線(IR)センサー**と**温度計**のライブ表示を備え、**CLI / ncurses GUI /
X11 GUI / GTK+3 GUI** の4つのフロントエンドを持ちます。

- 左チャンネル: `sin(2π·carrier·t)` / 右チャンネル: `sin(2π·(carrier+beat)·t)`
- 左右差 `beat` が「うなり（binaural beat）」として知覚される音響手法（ヘッドホン推奨）
- **リアルタイム連続再生（ALSA）**: WAV を介さず ALSA へ直接ストリーム出力。
  再生中もセンサー値に追従して音が滑らかに変化（位相連続でクリックノイズ無し）。
- **バイオフィードバックモード**: センサー値で周波数をリアルタイム変調
  - **温度計 → beat 周波数**（基準24℃、±1℃ごとに±0.5Hz、0.5〜30Hzにクランプ）
  - **IR対象温度 → carrier 周波数**（基準30℃、+1℃ごとに+10Hz、80〜1200Hzにクランプ）

## ⚠️ 重要な注意

本アプリは **音響トーン発生器 + センサー表示** です。プリセット名（リスパダール、
ジプレキサ等）は単なる **ラベル** であり、薬剤やその薬効・治療効果を再現・代替する
ものではありません。**特定の周波数に医学的・治療的効果があるという主張はしません。**
治療・服薬の判断は必ず医師・薬剤師に相談してください。大音量・長時間使用は避けてください。

## 構成

| ファイル | 役割 |
|---|---|
| `audio_core.{c,h}` | プリセット定義・WAV合成・波形サンプル・センサー→周波数マッピング（共有コア） |
| `sensors.{c,h}` | 赤外線センサー + 温度計 の抽象化（実機/シミュレーション） |
| `rt_audio.{c,h}` | リアルタイム音声出力（ALSA直結、別スレッドで連続再生） |
| `biofeedback_audio.c` | **CLI** フロントエンド |
| `gui_ncurses.c` → `bfa_tui` | **端末GUI**（ncurses） |
| `gui_x11.c` → `bfa_gui` | **X11 グラフィカルGUI** |
| `gui_gtk.c` → `bfa_gtk` | **GTK+3 グラフィカルGUI** |

## ビルド

```sh
make            # 全部 (CLI/TUI/X11、gtk+-3.0 があれば GTK も)
make cli        # CLI のみ
make tui        # ncurses GUI のみ
make gui        # X11 GUI のみ
make gtk        # GTK GUI のみ
make info       # ALSA / GTK 検出状況を表示
make selftest   # GUIを開かず内部ロジック(センサー+合成+ALSA有無)を検証
```

依存:
- 必須: `gcc`, `-lm`
- `bfa_tui` → `-lncurses` / `bfa_gui` → `-lX11` / `bfa_gtk` → `gtk+-3.0`
- 任意: **`libasound`(ALSA)** … 見つかれば Makefile が自動検出して
  `-DBFA_HAVE_ALSA` を付け、**リアルタイム連続再生**を有効化（`-lasound -lpthread`）。
  無い環境では自動的に WAV 生成へフォールバックし、GUI は通常どおり動作します。

## 使い方

### CLI
```sh
./biofeedback_audio list
./biofeedback_audio gen <preset|all> [seconds] [outdir]
./biofeedback_audio play <preset> [seconds]
./biofeedback_audio custom <carrier_hz> <beat_hz> <seconds> <out.wav>
```

### ncurses GUI（端末で動作）
```sh
./bfa_tui
#  ↑↓/jk: 選択   p/Enter: WAV再生   s: WAV保存
#  r: リアルタイム連続再生(ALSA) ON/OFF   b: バイオフィードバック ON/OFF   q: 終了
./bfa_tui --selftest    # 画面を開かず検証
```

### X11 GUI（Xディスプレイのあるデスクトップで動作）
```sh
DISPLAY=:0 ./bfa_gui
#  プリセット行/ボタンをクリック、または ↑↓ P S R B Q キー
#  ボタン: Play / Save / Realtime / BioFB / Quit
./bfa_gui --selftest    # ディスプレイを開かず検証
```

### GTK+3 GUI（Xディスプレイのあるデスクトップで動作）
```sh
DISPLAY=:0 ./bfa_gtk
#  ツリービューで選択、ボタン: Play / Save / Realtime / BioFB / Quit
./bfa_gtk --selftest    # ディスプレイを開かず検証
```
> リモート/ヘッドレス環境ではディスプレイが無いため X11/GTK ウィンドウは表示
> できません。その場合は `--selftest` か `bfa_tui` を使ってください。

### リアルタイム連続再生（ALSA）について
`r` キー / Realtime ボタンで、WAVファイルを介さず ALSA へ直接ストリーム再生します。
別スレッドが位相連続でサイン波を生成し続けるため、`Realtime` + `BioFB` を両方 ON に
すると、**温度計・IRセンサーの値に追従して音程（carrier/beat）がリアルタイムに変化**
します。サウンドデバイスが無い環境では開始に失敗し、安全に WAV 生成へ戻れます。

## 赤外線センサー + 温度計

`sensors.c` がハードウェアを抽象化し、2つのバックエンドを自動選択します。

| バックエンド | 条件 | 内容 |
|---|---|---|
| **FILE/sysfs（実機）** | 環境変数で指定したファイルが読める | ファイル/sysfs から数値を読む |
| **SIM（シミュレーション）** | 上記が無い/読めない | ダミー値を生成（ハード無し環境用） |

### 実機での使い方（例: Raspberry Pi + MLX90614 IR放射温度計）

センサー値を数値テキストとしてファイル/sysfs に出しておき、環境変数で指すだけです。

```sh
# 温度計ソース（sysfs の thermal_zone は millidegC 形式でも自動換算: 36500 -> 36.5C）
export BFA_TEMP_PATH=/sys/class/thermal/thermal_zone0/temp
# IR センサー（物体温度[摂氏] か生値を出力するファイル/デーモン）
export BFA_IR_PATH=/run/mlx90614_object_temp
./bfa_tui     # または ./bfa_gui
```

読み取り項目（`SensorReading`）:
- `ambient_c` … 温度計（周囲温度）→ バイオFB時は **beat 周波数**に写像
- `ir_object_c` … IRが捉えた対象物体温度 → バイオFB時は **carrier 周波数**に写像
- `ir_raw` … IR生値（0..1正規化）
- `present` … IR近接検知（体温域なら検知）

写像式（`audio_core.c`）:
- `bfa_feedback_beat(base, ambient)   = clamp(base + (ambient-24)*0.5, 0.5, 30)`
- `bfa_feedback_carrier(base, ir_obj) = clamp(base + (ir_obj-30)*10, 80, 1200)`

## プリセットと周波数

| key | ラベル | carrier | beat | 帯域 |
|-----|--------|--------:|-----:|------|
| risperdal | リスパダール | 174.0 | 3.0 | delta |
| zyprexa | ジプレキサ | 185.0 | 3.5 | delta |
| silece | サイレース | 110.0 | 1.5 | delta |
| depas | デパス | 210.0 | 6.0 | theta |
| etizolam | エチゾラム | 216.0 | 6.5 | theta |
| brotizolam | ブロチゾラム | 128.0 | 2.0 | delta |
| rohypnol | ロヒプノール | 120.0 | 1.0 | delta |
| sancoba | サンコバ | 396.0 | 10.0 | alpha |
| hyaluronic | ヒアルロン酸 | 417.0 | 10.5 | alpha |
| lendormin | レンドルミン | 132.0 | 2.5 | delta |
| luran | ルーラン | 198.0 | 4.5 | theta |
| saphris | シクレスト | 222.0 | 5.0 | theta |
| sennoside | センノサイド | 288.0 | 9.0 | alpha |
| akineton | アキネトン | 256.0 | 8.0 | alpha |
| biperiden | ビペリデン | 264.0 | 8.5 | alpha |
| amel | アメル | 333.0 | 9.5 | alpha |
| benzalin | ベンザリン | 144.0 | 2.0 | delta |
| levotomin | レボトミン | 160.0 | 4.0 | theta |

> beat の目安: delta ~0.5–4Hz / theta ~4–8Hz / alpha ~8–13Hz / beta ~13–30Hz。
> 周波数は心地よい可聴域に分散させた**任意の設計値**であり、各薬剤の物性・薬効に
> 由来するものではありません。
