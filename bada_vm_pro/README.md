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
| **ライブ CD / USB (ISO)** | Releases / Actions アーティファクトから `BadaVMPro-live.iso` — **レガシー BIOS の GRUB (i386-pc) マルチブート ISO**。ブートすると GRUB メニューで複数 OS を選べます。マウントして `INDEX.HTM` をブラウザで開けば OS が起動。ISO は [`tools/build-iso.sh`](tools/build-iso.sh) (grub-mkrescue) が生成 |

### 🧩 他の OS と共存させる — 裏表デュアルブート (専用 BOOT 区画)

Bada VM Pro を**先頭ヘッダを占有せず**、Windows と「裏表(front/back)」のデュアルブートで
共存インストールできます。Bada 用パーティションを作るとき、**Windows と Bada の「間」に
WIN 属性(FAT・ブートフラグ付き)のブートローダー専用パーティション**も同時に作り、
そこへ GRUB 本体を置きます:

```
ハードディスク (MBR / レガシー BIOS)
 ┌──────────┬─────────────────────┬──────────────────────┬────────────────┐
 │ MBR      │ Windows             │ BOOT 専用パーティション │ Bada VM Pro    │
 │ (最小    │ (前方・表/おもて)    │ (中間・WIN属性/boot旗)  │ (末尾・裏/うら) │
 │ ブート   │ そのまま chainload  │ GRUB 本体 + grub.cfg    │ INDEX.HTM      │
 │ ストラップ)│                     │ (ラベル BADABOOT)       │ (BADAVMPRO)    │
 └──────────┴─────────────────────┴──────────────────────┴────────────────┘
   起動時に GRUB メニューで Windows(表) / Bada VM Pro(裏) / 既存OS を選択
```

- **GRUB 本体・モジュール・`grub.cfg` は専用 BOOT パーティション**(Windows と Bada の間)に
  置きます。先頭ヘッダや Windows/Bada の中には入れません。
  ※ レガシー BIOS では MBR 先頭 440B に GRUB の**最小ブートストラップ**だけが入ります
  (BIOS の仕様上これは避けられません)。設定・本体は専用パーティション側です。
- 専用 BOOT パーティションには **WIN 属性(ブートフラグ / FAT 型)** を付けます。
- **Windows は前方パーティション(表)のまま**残し、GRUB が `chainloader` で起動します。
- **Bada VM Pro はディスク末尾(裏)の新規パーティション**(ラベル `BADAVMPRO`)。
  既存パーティションは一切消しません。
- **VMware Workstation Pro 16** の仮想ディスクでも同じレイアウトでデュアルブートできます。

インストールは既存の Ubuntu などから(**既定は下見・非破壊**、`--apply` で実行):

```
sudo bash bada_vm_pro/tools/install-grub-multiboot.sh            # 下見 (何も書き込まない)
sudo bash bada_vm_pro/tools/install-grub-multiboot.sh --apply    # 実行
   オプション: --disk /dev/sdX  --size <MiB(既定512)>  --boot-size <MiB(既定128)>
```

インストーラは「ディスク末尾の空きに **① WIN 属性の BOOT 専用パーティション(fat16・boot旗)**
→ **② Bada パーティション(fat32・BADAVMPRO)** の順で 2 区画を作成 → ① に GRUB(i386-pc /
レガシー)本体と `grub.cfg` を導入(MBR は最小ブートストラップのみ)→ ② に `INDEX.HTM` を配置 →
Windows(表)/ Bada VM Pro(裏)/ 既存 OS を選べる `grub.cfg` を生成」します。OS 本体は
`INDEX.HTM` なので、起動後はどの PC のブラウザで開いても w9wm デスクトップが動きます。

> QEMU での実ブート検証済み(裏表 3 区画のインストール済みディスク): **中間の専用 BOOT
> パーティション上の GNU GRUB 2.12** が裏表メニューを表示し、「Windows(表)」を選ぶと前方
> パーティションを `chainloader +1` で起動することをスクリーンショットで確認。ライブ ISO 単体でも
> GRUB メニューが出ます。

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
