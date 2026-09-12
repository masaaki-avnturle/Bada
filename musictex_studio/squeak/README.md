# 🎼 MusicTeX Studio — Squeak 版 (音響制作 / スペクトルコード)

**Squeak Smalltalk の Morphic + サウンド合成で作った音響制作アプリ。**
HTML 版 MusicTeX Studio と同等の機能を、**Apple のデスクトップ専用ソフトに似たデザイン**
(信号機ボタン付きタイトルバー / トランスポート + LCD のツールバー / 左ライブラリ /
中央エディット領域 / 右インスペクタ) の Morphic ウィンドウとして実装しています。

## 📥 インストールと起動

1. [Squeak](https://squeak.org/downloads/) (6.0 以降推奨。5.x / Etoys 系でも動作するよう
   旧 API 互換で書かれています) をダウンロードして起動
2. [Releases](https://github.com/masaaki-avnturle/Bada/releases) から
   `MusicTeXStudio-Squeak.zip` を取得 (または本ディレクトリの
   [`MusicTeXStudio.st`](MusicTeXStudio.st) を「Download raw file」)
3. `MusicTeXStudio.st` を Squeak のウィンドウに**ドラッグ&ドロップ**して
   「file in entire file」を選ぶ (または FileList から fileIn)
4. ワークスペースで次を実行 (do it):

```smalltalk
MTSApp open
```

## ✨ 機能 (HTML 版と同等)

| 機能 | 実装 |
|:---|:---|
| 🎹 シンセサイザー (スペクトルコード) | 倍音1〜8の加算合成 (`MixedSound` + `FMSound`) + ADSR (`VolumeEnvelope`)。インスペクタの8本のフェーダーで音色を設計 |
| 楽器 17 種 | Piano / Organ / Violin / Cello / Flute / Trumpet / Clarinet / Guitar / Harp / MusicBox / Bell / Marimba / Bass + Sine / Triangle / Saw / Square (ライブラリから選択) |
| 🌈 モーツァルト・ビジョン | 音の周波数 ×2^≈40 = 可視光の対応で、楽譜を色の波長帯の映像として描画 (`MTSSpectralMorph`)。Play 中は鳴っている帯が白枠でハイライト。下端は 380〜780nm の波長ものさし |
| 五行コード線 | M / m / 7 / M7 / sus4 の5行 × 12音階のカラーパッド。クリックでシンセ演奏 + 調号を考慮した和音 (`\zq` + 臨時記号) を楽譜へ挿入 |
| 楽譜プレビュー | 五線譜の簡易描画 (`MTSStaffMorph`: ト音記号・調号・音符・加線・小節線) |
| MusixTeX | エディタで直接編集 (「更新」で反映)。`.tex保存` で書き出し → `musixtex -p score.tex` (texlive-music) で印刷用 PDF |
| 🎵 曲→楽譜 | **MIDI 取込** (Squeak 標準 `MIDIFileReader`) は和音対応、**WAV 取込** は自己相関ピッチ検出の単旋律採譜。取り込みは「置き換え / 重ねる」を切替可 (LCD の MODE 表示) |
| 🧩 コード化 | いまの楽譜を小節ごとに解析してコード進行を抽出し、伴奏として重ねる |
| octave74 テンプレート | B♭/E♭ 長音階・G と A の和音・2音階=2オクターブ・HANON 風・空の楽譜 |

## 🖥 画面構成 (Apple デスクトップ専用ソフト風)

```
┌──────────────────────────────────────────────────────┐
│ ●●●        MusicTeX Studio - Spectral Code           │ ← タイトルバー (信号機)
├──────────────────────────────────────────────────────┤
│ MIDI取込 WAV取込 置き換え | Stop Play | [LCD] | コード化 更新 .tex保存 │
├─────────┬─────────────────────────────┬──────────────┤
│ライブラリ│ モーツァルト・ビジョン       │インスペクタ  │
│ 楽器17種 │ (色の波長帯タイムライン)     │ スペクトル   │
│ ────── │ ──────────────────────────  │ コード       │
│ テンプレ │ 楽譜ライブプレビュー         │ (倍音1〜8)   │
│ ート6曲  │ ──────────────────────────  │ ──────────  │
│          │ MusixTeX エディタ            │ 五行コード線 │
└─────────┴─────────────────────────────┴──────────────┘
```

- 赤い信号機ボタンでウィンドウを閉じます
- LCD には KEY (調号) / 拍子 / NOTES / BARS / INST (楽器) / MODE (取り込み方法) を表示

## 検証

- 構造検証は CI ([`../tools/squeak-check.js`](../tools/squeak-check.js)) が毎回実行:
  チャンク形式・全81メソッドの括弧/引用符/セレクタ・主要 API の存在
- 旧 Squeak (4.x/Etoys) 互換のため、クラス定義は 5 キーワード形式、Canvas は
  `fillRectangle:color:` 系のみ、数値リテラルも旧形式で記述

## ライセンス

MIT — © Masaaki Yamaguchi
