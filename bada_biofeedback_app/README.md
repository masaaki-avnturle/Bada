# Bada Biofeedback — `bada_biofeedback_app/`

Bada言語ミニランタイムで駆動する **教育・リラクゼーション用 Android アプリ**。
脳トポグラフィー / fMRI・MRI / 脳波(EEG) / 心電図(ECG) / 薬「ほっと」バイオフィードバック /
サイレントトーク（無声コミュニケーション盤） / 血液成分・血圧 を一つにまとめています。

> ## ⚠️ 重要な免責事項 / Disclaimer
> このアプリは **シミュレーションと可視化のデモ** です。
> - 脳波・MRI・fMRI・血液・血圧・体温・思考を **実測しません**（心拍PPGを除く）。
> - 薬（リスパダール／レボトミン／ブロチゾラム等）の **薬効を再現・代替しません**。
>   各プリセットは「その薬の名にちなんだ “ほっとする” 音風景と対象部位」です。
> - **医療機器ではなく、診断・治療・投薬判断には使えません。** 処方は必ず主治医の指示に従ってください。
>
> 唯一の実測機能は **カメラPPGによる心拍数の目安**（指を背面カメラに当てる）で、
> これも消費者向けの参考値です。

---

## 機能一覧

| 画面 | 内容 | 実測/シミュレーション |
|:----|:----|:----|
| 脳トポグラフィー | 10-20電極のEEGトポマップ + バンドパワー | 手続き的シミュレーション |
| fMRI / MRI ビューア | 断層スライス + 賦活オーバーレイ（スライダー操作） | 手続き的シミュレーション |
| 脳波計 (EEG) | 10チャンネル合成波形 | 手続き的シミュレーション |
| 心電図 (ECG) + 心拍 | 合成PQRST波形 + **カメラPPG実測** | ECGは擬似 / 心拍は実測 |
| 薬バイオフィードバック | 薬名プリセットの音風景 + 部位「ほっと」ハイライト | リラクゼーション音（薬効ではない） |
| サイレントトーク | **無声コミュニケーション盤**（タップで意思表示）+ 多様体テレメトリ演出 | 思考読取ではない |
| 血液成分・血圧 | 手入力 + 基準範囲判定 | 手入力（実測不可） |

---

## Bada言語（プリセット DSL）

`app/src/main/assets/presets/*.bada` に音風景プリセットを宣言します。

```bada
preset "risperdal" {
    label     = "リスパダール"
    feeling   = "気持ちが安静に"
    region    = limbic        // ほっとする対象部位
    base_hz   = 96.0          // キャリア音
    beat_hz   = 7.5           // 呼吸(振幅変調)レート — θ波帯=安静
    waveform  = soft
    warmth    = 0.75          // 音のやわらかさ 0..1
    color     = "#7ec8e3"
    narration = "胸と脳がゆっくりほどけ、気持ちが安静へ向かいます。"
}
```

- パーサ実装: `lang/BadaInterpreter.kt`
- 数学コア（ガンマ関数 / オイラー定数 / 熱エントロピー envelope）: `lang/BadaMath.kt`
  - `Γ(x)` Lanczos近似、`gammaEnvelope` を「大域的部分積分多様体」envelope として、
    `thermalEntropy` を音の明るさ・トポマップ輝度の駆動に使用（演出であり実測ではありません）。
- 音合成（AudioTrack）: `audio/ToneSynth.kt`
- カメラPPG心拍（実測）: `sensor/PpgHeartRate.kt`

---

## ビルド方法

### 1) GitHub Actions（推奨・APK成果物を自動生成）
`.github/workflows/build-apk.yml` がこのフォルダの変更で起動し、`assembleDebug` を実行、
**APKを成果物 (artifact) としてアップロード**します。Actions タブの
`bada-biofeedback-debug-apk` からダウンロードできます。手動実行も可能（workflow_dispatch）。

### 2) ローカル
Android Studio（Hedgehog以降）でこのフォルダを開く、または:

```bash
cd bada_biofeedback_app
gradle assembleDebug        # Gradle 8.7+ / JDK 17 / Android SDK 34
# → app/build/outputs/apk/debug/app-debug.apk
```

- minSdk 26 / targetSdk 34 / Kotlin 1.9.24 / Compose BOM 2024.06 / AGP 8.5.2

---

© Masaaki Yamaguchi · 山口雅旭 · Bada Language
