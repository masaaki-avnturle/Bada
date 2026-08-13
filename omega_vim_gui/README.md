# Ω-Vim GUI — Bada言語エディタの GUI アプリ

**Ω-Vim を GUI アプリケーションとして、Android APK / Windows 10・11 / Linux(Ubuntu) 向けに**
ビルド・配布します。モーダル編集・**文法チェッカー**・**パーサー補完**・**インデント補完**、
そして**特殊相対性理論の複素回転コマ（独楽）の可積分系**によるソースコードのエラー修正を、
グラフィカルに操作できます。

*Ω-Vim as a graphical app for Android (APK), Windows 10/11, and Linux/Ubuntu.
A modal editor with a grammar checker, parser completion, indent completion, and
the complex-rotation spinning-top (koma) integrable-system code fix.*

山口 (Yamaguchi) フレームワーク / Bada language ·
Part of the [Bada](https://masaaki-avnturle.github.io/Bada/) repository.

> ⚠️ **研究・概念実装 (proof-of-concept).** 括弧・引用符・コメント・空白・ブロック構造を
> 普遍原理で扱います。エンジンは**このページ内で完結**（サーバも Ruby も不要）。

---

## これは何か / What it is

CLI 版の [`omega_vim_bada`](../omega_vim_bada/) と同じエンジンを **JavaScript に移植**し
（`www/omega-engine.js` は Ruby 版 `Bada::CodeFix` / `Bada::Grammar` / `Bada::Manifold` /
`Bada::ErrorCorrection` の忠実な移植）、`<textarea>` ベースの GUI エディタに載せたものです。
リポジトリの他アプリ（bio_medicine の APK+EXE 群）と同じ **www + electron + cordova** 構成で、
Android / Windows / Linux のネイティブ・パッケージにビルドします。

### 機能
- **モーダル編集**（`vim: on` トグルで Normal/Insert/Command、`hjkl` `i a o` `x` `dd` `:` コマンド）
- **∮ Fix** — 複素回転の軌道を閉じる**エラー修正＋インデント補完**（全言語）
- **Check** — **文法チェッカー**（括弧・引用符・コメント＋ブロックキーワード対応）。結果は
  クリックで該当行へジャンプ
- **▸ Complete**（挿入モードで **Tab**）— **パーサー補完**（現在のパース状態から期待トークン）
- **⇥ Indent** — **インデント補完**（パース深さから再インデント）
- **Enter で自動インデント**、行番号ガター、言語自動判定（C / JS / Python / Ruby / Shell / Lisp / JSON）
- **Open / Save**（端末上のファイルを開く・ダウンロード保存）

### 幾何（レポート由来）
```
□ = cos(i x log x) − i sin(i x log x) = e^{−i(x log x)}     (複素回転体)
∮ e^{−□} d□ = π e                                          (閉軌道 = 可積分条件)
```
括弧の入れ子は回転体上の歩み。**正しいコードは位相 0 に戻る閉軌道**で、その「開きトークン
のスタック＝巻き数」が、修正・文法チェック・補完・インデントのすべてを駆動します。

---

## ダウンロード / Download

GitHub Actions の **Actions アーティファクト**、または `ovim-gui-v*` タグ時の **Release** から
取得できます（ワークフロー: `.github/workflows/omega-vim-gui.yml`）。

| プラットフォーム | 成果物 | 入手・実行 |
|:--|:--|:--|
| **Android** | `omega-vim-debug.apk` | 端末にコピーしてインストール（提供元不明アプリを許可） |
| **Windows 10/11** | `Omega-Vim-1.0.0-x64.exe`（NSIS インストーラ＋ポータブル） | ダブルクリックで実行 |
| **Linux/Ubuntu** | `Omega-Vim-1.0.0-x86_64.AppImage` / `Omega-Vim-1.0.0-amd64.deb` | `chmod +x *.AppImage && ./*.AppImage` もしくは `sudo apt install ./Omega-Vim-1.0.0-amd64.deb` |

タグを打って Release にまとめて添付：
```sh
git tag ovim-gui-v1.0.0 && git push origin ovim-gui-v1.0.0
```

### ブラウザで即試す（ビルド不要）
`www/index.html` をブラウザで開くだけで全機能が動きます（完全自己完結）。

---

## ローカルでビルド / Build locally

### Windows EXE / Linux AppImage・deb（Electron）
```sh
cd omega_vim_gui/electron
npm install
npm run dist:win      # Windows: dist/*.exe   （windows-latest 上で）
npm run dist:linux    # Linux:   dist/*.AppImage, dist/*.deb
npm start             # デスクトップで起動（開発）
```

### Android APK（Cordova）
CI と同じ手順（`cordova create` → `www` と `config.xml` を投入 → `cordova build android`）。
詳細は `.github/workflows/omega-vim-gui.yml` を参照。

---

## 使い方 / Usage

1. **Open** で編集したいソースを開く（または直接入力／**Sample** ボタン）。
2. 壊れたコードは **∮ Fix** で軌道を閉じ、インデントも整えます。
3. **Check** で文法診断（未閉ブロック・不整合）。行をクリックでジャンプ。
4. 入力中に **Tab** で**パーサー補完**（期待される閉じ括弧・`end` などを挿入）。
5. **⇥ Indent** でバッファ全体を再インデント。**Enter** は自動インデント。
6. `vim: on` にすると Normal/Insert/Command のモーダル操作（`hjkl` `i a o` `x` `dd` `:w :fix :check :indent`）。

---

## 構成 / Layout

```
omega_vim_gui/
├── www/
│   ├── index.html          # GUI（ツールバー・エディタ・診断パネル・ステータス）
│   ├── omega-engine.js     # Bada エンジンの JS 移植（codefix/grammar/manifold/error-correction）
│   └── omega-editor.js     # エディタ本体（自動インデント・Tab補完・vimモーダル）
├── electron/               # Windows EXE / Linux AppImage・deb
│   ├── package.json        # electron-builder 設定
│   └── main.js
├── cordova/
│   └── config.xml          # Android APK
└── README.md
```

CLI 版・Bada言語本体は [`../omega_vim_bada`](../omega_vim_bada/) を参照。

## ライセンス / License
リポジトリの LICENSE（MIT）に従います。© Masaaki Yamaguchi — Bada / Yamaguchi framework.
