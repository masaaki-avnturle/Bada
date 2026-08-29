# 🜁 Bada VM Pro — 量子 Bada 言語のオペレーティングシステム(w9wm デスクトップ版)

**デスクトップは window manager「w9wm」(9wm + 仮想スクリーン)、ベース(カーネル)は BadaGPT。**
Ubuntu 風ユーザーランド(bash / apt / vim / emacs / ssh / xinetd / texlive-full / screen /
fcitx-mozc)を**事前インストール**し、日本語入力対応のターミナル(xterm /
x-terminal-emulator / terminal)を載せた、依存ゼロの **単一 HTML** (`index.html`) OS です。

## ⬇️ ダウンロード

| 方法 | 手順 |
|:---|:---|
| **一番かんたん** | [`index.html`](index.html) を開き **「Download raw file」(⬇)** → 保存したファイルをダブルクリック(インストール不要・オフライン可) |
| **Android APK** | [Releases](https://github.com/masaaki-avnturle/Bada/releases) から `bada-vm-pro-debug.apk`(提供元不明アプリの許可が必要) |
| **Windows 10/11** | Releases から `BadaVMPro-*-x64.exe`(NSIS インストーラ / ポータブル) |
| **Ubuntu** | Releases から `BadaVMPro-*-x86_64.AppImage` / `BadaVMPro-*-amd64.deb` |
| **ライブ CD / USB (ISO)** | Releases / Actions アーティファクトから `BadaVMPro-live.iso` — **本物の isolinux (syslinux) で組んだブータブル ISO** (El Torito + isohybrid MBR)。**Rufus の「ISO イメージモード」**で USB ブートディスクを作成できます (下記)。マウントして `INDEX.HTM` をブラウザで開けば OS が起動、CD/USB からブートすると isolinux が案内バナーを表示。ISO は [`tools/build-iso.sh`](tools/build-iso.sh) (xorriso + isolinux) が生成 |

### 🔥 Rufus で USB 起動メディアを作る (ISO イメージモード)

`BadaVMPro-live.iso` は**本物の isolinux ブートローダ**を含む標準的なブータブル ISO
なので、Rufus がディスクを認識し **「ISO イメージモード」**でブート USB を作成できます
(DD モードは不要):

1. [Releases](https://github.com/masaaki-avnturle/Bada/releases) / [Actions](https://github.com/masaaki-avnturle/Bada/actions) の `badavmpro-iso` から `BadaVMPro-live.iso` を入手
2. [Rufus](https://rufus.ie) を起動 → USB メモリを選択 → 「選択」で ISO を指定
3. Rufus が「ISOHybrid…」と尋ねたら **「ISO イメージモードで書き込む」を選択**して「スタート」
4. 書き込んだ USB からブート → isolinux が起動して案内バナーを表示。中の
   `INDEX.HTM` を任意の PC のブラウザで開けば w9wm デスクトップの OS が起動します

> QEMU での実ブート検証済み: 本物の **ISOLINUX 6.04** が起動しバナーを表示することを
> スクリーンショットで確認。isohybrid MBR も残してあるので、Rufus が DD モードを選んでも
> USB からブートできます。

ネイティブ版は [`badavmpro-app-build.yml`](../.github/workflows/badavmpro-app-build.yml) がビルドします
(`badavmpro-v*` タグを push するか、Actions の `workflow_dispatch` で `release_tag` を指定)。

## 🖥 w9wm デスクトップの操作

9wm の流儀そのまま + w9wm の仮想スクリーン。**ウィンドウにタイトルバーはありません**:

| 操作 | 動作 |
|:---|:---|
| **右クリック (B3)** | WM メニュー — `New`(新しい xterm)/ `Reshape`(掃引で枠を引き直す)/ `Move` / `Delete` / `Hide` + 隠したウィンドウ一覧 + 仮想スクリーン 0-3 |
| **左クリック (B1)** ルート | アプリケーションメニュー(左上 ☰ ボタンでも可 — タッチ端末向け) |
| **Ctrl+Alt+← / →** | 仮想スクリーン切替(4 面) |
| 枠(4px ボーダー)ドラッグ | ウィンドウ移動 / 右下角ドラッグでリサイズ |

## 📦 事前インストール済みパッケージ(Ubuntu 風ユーザーランド)

`apt list --installed` で確認できます:

**bash · apt · vim · emacs · openssh-client/server (ssh) · xinetd · texlive-full ·
screen · fcitx-mozc · xterm · x-terminal-emulator · terminal · w9wm · coreutils**

| コマンド | 内容 |
|:---|:---|
| `apt update / upgrade / install / remove / list --installed` | パッケージ管理(`apt upgrade` は BadaGPT の OS ライブパッチと連動) |
| `vim <file>` | モーダルエディタ — `i` 挿入 / `Esc` / `:w` `:q` `:wq` / `dd` `yy` `p` `x` / `hjkl` `gg` `G` `0` `$` |
| `emacs <file>` | `C-x C-s` 保存 / `C-x C-c` 終了 / `C-k` / `C-y` / `C-a` `C-e` / `C-n` `C-p` |
| `ssh user@bada.or.jp` | zone:// Bell 対 QKD ハンドシェイク付きで接続(`exit` で戻る)。既知ホスト: bada.or.jp / url.or.jp / localhost |
| `xinetd status` `service xinetd start\|stop` | スーパーサーバー。`/etc/xinetd.d`(echo / daytime / zoneqkd)を管理 |
| `screen` `screen -ls` `screen -r` | 端末多重化 — `Ctrl+a d` でデタッチ |
| `pdflatex file.tex` | texlive-full 同梱。`\section` 等を処理して `.pdf` を VFS に出力(`~/letter.tex` がサンプル) |
| `fcitx-mozc status` | 日本語入力の状態と使い方 |
| `ls cd cat echo> mkdir touch rm cp mv grep ps man uname lsb_release dpkg -l …` | ふつうの Ubuntu コマンド(永続 VFS 上で動作) |
| `mount` / `eject` | 💿 **ISO マウント** — アプリメニュー「ISO をマウント」で `.iso` (自分自身のライブ CD `BadaVMPro-live.iso` を含む) を `/mnt/cdrom` に読み込み。`ls /mnt/cdrom`・`cat /mnt/cdrom/README.TXT` で閲覧、`eject` で取り出し |

## ⌨️ ターミナルの日本語入力

3 種のターミナル(**xterm**=白 / **x-terminal-emulator**=黒 / **terminal**=GNOME 風)すべてで:

1. **OS の IME でそのまま入力** — 変換中の文字列は下線付きで表示され、確定でコマンドラインに入ります(Android の IME も可)
2. **内蔵 fcitx-mozc** — `Ctrl+Space` でオン(右上に「Mozc あ」)。ローマ字がひらがなに逐次変換され、`Enter`/`Space` 確定・`F7` カタカナ・`Esc` 取消。`gakkou → がっこう`、`kyouto → きょうと` など促音・拗音・「ん」に対応

## 何ができるか(アプリ)

| アプリ (bada:// URL) | 内容 |
|:---|:---|
| `bada://terminal` | **xterm** — 上記ユーザーランド + 量子 Bada REPL(`qubit q0 q1; H q0; CNOT q0 q1; measure`) |
| `bada://gpt` | **BadaGPT** — OS のベース。**`os update` / `os upgrade` は BadaGPT が実行**し、changelog を刻む |
| `bada://rails` | **Bada on Rails** — `rails generate scaffold Post title:string body:text` 一発で `bada://rails/post` に CRUD |
| `bada://studio` | **GUI プログラミング** — フォームデザイナ → Bada コード自動生成 → ▶ 実行 |
| `bada://transformer` | **トランスフォーマー・スタジオ** — self-attention 順伝播 + 学習、attention 可視化 |
| `bada://voice` | **合い言葉コマンド** — silent talk(決定論的)+ 音声(類似度照合)。「バダ、起動 ターミナル」 |
| `bada://settings` | OS バージョン・WM・プリインストール一覧・changelog |

## テスト

```
node bada_vm_pro/tools/engine-test.js
```

ベル状態・attention・Rails CRUD・合い言葉・OS 台帳に加えて、
**apt 事前インストール一覧 / VFS(echo→cat)/ ssh 接続と復帰 / xinetd /
pdflatex コンパイル / fcitx-mozc ローマ字→かな変換** など 53 項目を検証します
(CI の `test-core` ジョブでも実行)。

---

⚠️ Bada VM Pro はブラウザー/WebView 上で動く**自己完結のOS体験(シミュレーション)**です。
apt / ssh / xinetd 等は VFS 上のシミュレーションで、実端末のシステムや実ネットワークには
一切触れません。状態は localStorage に永続化されます。
