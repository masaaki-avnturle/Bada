# 🜁 Bada VM Pro — 量子 Bada 言語のオペレーティングシステム(今までの集大成)

**シェルはウェブブラウザーのデザイン、ベース(カーネル)は BadaGPT。**
量子プログラミング言語 Bada / Bada on Rails / 合い言葉コマンド / トランスフォーマー補完 /
GUI・CUI プログラミングを、依存ゼロの **単一 HTML** (`index.html`) に統合しました。

## ⬇️ ダウンロード

| 方法 | 手順 |
|:---|:---|
| **一番かんたん** | [`index.html`](index.html) を開き **「Download raw file」(⬇)** → 保存したファイルをダブルクリック(インストール不要・オフライン可) |
| **Android APK** | [Releases](https://github.com/masaaki-avnturle/Bada/releases) から `bada-vm-pro-debug.apk`(提供元不明アプリの許可が必要) |
| **Windows 10/11** | Releases から `BadaVMPro-*-x64.exe`(NSIS インストーラ / ポータブル) |
| **Ubuntu** | Releases から `BadaVMPro-*-x86_64.AppImage` / `BadaVMPro-*-amd64.deb` |

ネイティブ版は [`badavmpro-app-build.yml`](../.github/workflows/badavmpro-app-build.yml) がビルドします
(`badavmpro-v*` タグを push するか、Actions の `workflow_dispatch` で `release_tag` を指定)。

## 何ができるか

| アプリ (bada:// URL) | 内容 |
|:---|:---|
| `bada://gpt` | **BadaGPT** — OS のベース。**`os update` / `os upgrade` は BadaGPT が実行**し、changelog を刻む。scaffold 生成・量子コード実行・補完も会話で |
| `bada://terminal` | **CUI プログラミング** — シェル + 量子 Bada REPL(`qubit q0 q1; H q0; CNOT q0 q1; measure`) |
| `bada://rails` | **Bada on Rails** — `rails generate scaffold Post title:string body:text` 一発で `bada://rails/post` に CRUD が立つ |
| `bada://studio` | **GUI プログラミング** — フォームデザイナに部品を置く → Bada コード自動生成 → ▶ 実行(ボタンで量子測定) |
| `bada://transformer` | **トランスフォーマー・スタジオ** — 16 次元 1 ヘッド self-attention の本物の順伝播で次トークン予測。attention 行列を可視化し、コードを与えて**学習**させられる |
| `bada://voice` | **合い言葉コマンド** — silent talk(無音テキスト)は正規化一致で**決定論的 = silent talk 以上の精度**。音声(Web Speech API)も同じ照合エンジン(カナ折りたたみ + レーベンシュタイン類似度)を通す |
| `bada://settings` | OS バージョン・changelog・BadaGPT への update/upgrade 依頼 |

### 合い言葉の使い方

既定の合い言葉は **「バダ、起動」**。アドレスバー・silent talk 欄・🎙 音声のどこからでも:

```
バダ、起動 ターミナル      → CUI を開く
バダ、起動 アップデート    → BadaGPT が OS update を実行
バダ、起動 レールズ        → Bada on Rails
```

変更はターミナルで `aikotoba <新しい合い言葉>`、または `bada://voice` から。

### 量子 Bada 言語(このアプリに載る実行系)

状態ベクトル・シミュレータ(最大 8 qubit)。`qubit` / `H` / `X` / `Z` / `CNOT` / `measure` / `state` / `let` / `print`。

```
qubit q0 q1
H q0
CNOT q0 q1     # ベル状態 (|00⟩+|11⟩)/√2
state
measure        # |00⟩ か |11⟩ に相関して収縮
```

## テスト

```
node bada_vm_pro/tools/engine-test.js
```

ベル状態の振幅・attention の softmax 正規化・Rails CRUD・合い言葉照合・
OS バージョン台帳など 18 項目を検証します(CI の `test-core` ジョブでも実行)。

---

⚠️ Bada VM Pro はブラウザー/WebView 上で動く**自己完結のOS体験(シミュレーション)**です。
実端末のファームウェアを書き換えるものではありません。状態は localStorage に永続化されます。
