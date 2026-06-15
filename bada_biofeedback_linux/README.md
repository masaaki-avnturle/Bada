# Bada Biofeedback — Linux native (ELF)

`bada_biofeedback_app`（Android / Kotlin + Compose）のコアを、**Linux のネイティブ実行
ファイル（ELF）**として動く C アプリに移植したものです。APK が要らず、ターミナルで直接
動きます。

> ⚠️ これはリラクゼーション用のシミュレーションです。薬効の再現・代替や、身体の物理量の
> 測定では一切ありません。処方薬の指示に従ってください。

## 移植したコア
- **BadaMath** — Lanczos のガンマ関数 Γ(x)、オイラー＝マスケローニ定数 γ、Shannon の
  「熱エントロピー」、ガンマ多様体のセッション包絡線（`session_envelope`）
- **Bada DSL** — `.bada` プリセット言語の小さなインタプリタ（`preset "id" { k = v }`）
- **ToneSynth** — リラクゼーション音風景（搬送波＋呼吸AM＋warmth ローパス＋包絡線）を
  **16bit ステレオ WAV** に書き出し
- **部位グロー / 手続き的 EEG・ECG** を ANSI/ASCII で表示

## ビルド

```bash
# 方法1: make
make            # → bin/bada_biofeedback
make run

# 方法2: Gradle（リポジトリ共通の assembleDebug）
./gradlew assembleDebug                       # フォルダ内から
# または リポジトリのルートから:
#   ./gradlew :bada_biofeedback_linux:assembleDebug
```

## 使い方

```bash
./bin/bada_biofeedback                 # インタラクティブ・メニュー（14プリセット）
./bin/bada_biofeedback --list          # プリセット一覧
./bin/bada_biofeedback risperdal       # 指定プリセットを表示＋WAV生成
./bin/bada_biofeedback levotomin 30    # 30 秒の音風景を生成
./bin/bada_biofeedback --presets medications.bada --wav out.wav --seconds 60 zyprexa
```

生成された `bada_soundscape.wav`（既定）は任意のプレイヤーで再生できます
（`aplay` / `paplay` があればコマンドも表示します）。

プリセット定義は `medications.bada`（Android アプリと同じ 14 個）を同梱しています。
