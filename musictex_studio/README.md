# 🎼 MusicTeX Studio — MusixTeX (texlive-music) 楽譜制作アプリ

**MusixTeX (texlive-music) の楽譜ソースを作成・プレビュー・試聴し、`.tex` として書き出す楽譜制作アプリ。**
依存ゼロ・単一 HTML・オフライン動作。レポート **「Δと」(Masaaki Yamaguchi, octave74)** の音階理論
(B♭・E♭ 長音階のとりうる音、2音階 = 2オクターブの考え方、G と A の和音、HANON 練習) を
テンプレートとして同梱しています。

## 📥 ダウンロード (APK / Windows 10・11 / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) の `musictex-v*` から:

| プラットフォーム | ファイル | インストール |
|:---|:---|:---|
| **Android** (APK) | `musictex-studio-debug.apk` | 端末に転送 →「提供元不明のアプリ」を許可してインストール |
| **Windows 10 / 11** | `MusicTeXStudio-*-x64.exe` (NSIS インストーラ) / `MusicTeXStudio-*-portable.exe` | ダブルクリック |
| **Ubuntu** | `MusicTeXStudio-*-x86_64.AppImage` / `MusicTeXStudio-*-amd64.deb` | AppImage は `chmod +x` して実行 / deb は `sudo apt install ./MusicTeXStudio-*-amd64.deb` |
| **楽譜サンプル PDF** | `octave74_scales.pdf` | texlive-music で実コンパイルした B♭ 長音階 + G・A 和音の楽譜 |

ブラウザで直接使うこともできます: [`index.html`](index.html) を「Download raw file」で保存してダブルクリック。

## ✨ 機能

- **MusixTeX ソースエディタ** — テンプレート読込、音符パレット (音価 ♩♪𝅗𝅥𝅝・♯♭♮・音高 a〜q・和音 `\zq`・小節線・休符)、調号セレクタ (E♭〜A)
- **ライブ楽譜プレビュー** — 入力と同時に SVG で五線譜を簡易組版 (ト音記号・調号・拍子・加線・和音・臨時記号・休符)
- **Web Audio 試聴** — ♩=96 で音階・和音をその場で再生 (調号・臨時記号を反映)
- **書き出し** — `.tex` ダウンロード / クリップボードコピー / `.tex` 読み込み / 自動保存 (localStorage)
- **コンパイルガイド** — texlive-music での PDF 組版手順を OS 別に表示

## 🖨 印刷用 PDF の作り方 (texlive-music)

アプリの「⬇ .tex 保存」で `score.tex` を書き出し、texlive-music でコンパイルします:

```bash
# Ubuntu
sudo apt update
sudo apt install texlive-music texlive-fonts-recommended
musixtex -p score.tex        # → score.pdf
```

- **Windows 10 / 11**: [MiKTeX](https://miktex.org/) か [TeX Live](https://tug.org/texlive/) をインストールし、同じく `musixtex -p score.tex`。
- **Android**: アプリで作成・試聴し、`.tex` を書き出して PC の texlive-music (または Overleaf 等) でコンパイル。

同梱サンプル [`scores/octave74_scales.tex`](scores/octave74_scales.tex) は CI で毎回
texlive-music により実コンパイル検証され、生成 PDF が Release に添付されます。

## 🎵 テンプレート (レポート octave74 の題材)

| テンプレート | 内容 |
|:---|:---|
| B♭ 長音階 | フラット2つ。B♭ の音階のとりうる音を上行・下行で |
| E♭ 長音階 | フラット3つ |
| G と A の和音 | G (g-i-k)・A (h-j-l) の三和音、F♯ (`\sh f`) を重ねる例 |
| 2音階 = 2オクターブ | 1オクターブ + またその上の1オクターブ (c → j → q) |
| HANON 風練習 | HANON 第1番型 (do-mi-fa-sol-la-sol-fa-mi) の8分音符パターン |
| 空の楽譜 | 最小の MusixTeX ドキュメント |

すべてのテンプレートは完全な MusixTeX ドキュメントで、そのまま `musixtex -p` でコンパイルできます
(CI で全曲を実コンパイル検証済み)。

## 📝 MusixTeX 早見表 (プレビュー対応サブセット)

| 記法 | 意味 |
|:---|:---|
| `\NOtes … \en` | 音符グループ |
| `\qu{c}` / `\ql{c}` | 4分音符 (符幹 上/下) |
| `\cu{c}` / `\cl{c}` | 8分音符 |
| `\hu{c}` / `\hl{c}` | 2分音符 |
| `\wh{c}` | 全音符 |
| `\zq{c}` | 和音の構成音 (次の音符に重ねる) |
| `\sh c` `\fl c` `\na c` | ♯ / ♭ / ♮ (直後の音に) |
| `\qp` `\hpause` `\pause` | 4分 / 2分 / 全休符 |
| `\bar` | 小節線 |
| `\generalsignature{-2}` | 調号 (負 = ♭ の数、正 = ♯ の数) |
| `\generalmeter{\meterfrac44}` | 拍子 |

音高は MusixTeX 表記: `a`=A3, `b`=B3, `c`=中央C (C4), … `h`=A4, `i`=B4, `j`=C5, … `q`=C6。
大文字は 1 オクターブ下。

## 🔧 ビルド (メンテナ向け)

ビルドは [`musictex-app-build.yml`](../.github/workflows/musictex-app-build.yml) が実行します:

1. **test-core** — inline JS の構文検査 + エンジンテスト ([`tools/engine-test.js`](tools/engine-test.js)) +
   **texlive-music を実際に導入して全テンプレート・サンプル楽譜を `musixtex -p` で実コンパイル検証**
2. **android-apk** — Cordova 12 + cordova-android 12.0.1 (Gradle 7.6.4) で APK
3. **windows-exe** — Electron + electron-builder で NSIS / ポータブル EXE
4. **linux-app** — Electron + electron-builder で AppImage / deb

`musictex-v*` タグを push すると Release に全成果物が添付されます。
`workflow_dispatch` (release_tag 空欄) なら Actions アーティファクトのみ。

## ライセンス

MIT — © Masaaki Yamaguchi
