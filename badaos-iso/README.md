# 💿 Bada VM Pro OS — 起動可能 ISO(Ubuntu 22.04 ベース / w9wm)

**USB ブートして実ディスクにインストールできる、Bada VM Pro OS の本物の Linux ディストロ**です。
これまでの単一 HTML アプリを「ライブ CD の中で動く OS」として仕立てました。

- **ベース**: Ubuntu 22.04 (jammy) を `debootstrap` で最小構築
- **ウィンドウマネージャ**: **w9wm**(lightdm 自動ログイン)+ **日本語端末 mlterm**
- **日本語環境**: ロケール ja_JP.UTF-8 / Noto CJK フォント / 入力メソッド **fcitx-mozc**(Ctrl+Space / 半角全角 で ON/OFF)+ 設定ツール **fcitx-configtool**(fcitx-config-gtk)
- **プリインストール**: Bada VM Pro / Laevateinn + 単一 HTML アプリ(`/opt/bada`)。**エディタ vim(gvim)/emacs/neovim**、git/tmux/htop、ファイルマネージャ等の定番も同梱
- **Ubuntu アプリを簡単導入**: `badaos-apps`（GUI チェックリスト）で LibreOffice/GIMP/VLC/Firefox 系/ブラウザ等を apt でワンクリック導入
- **実ディスクへインストール**: **Calamares(日本語 GUI)** + **パーティションマネージャ GParted**(使いたい HDD を初期化・作成)。うまく動かない時の代替として自作 zenity ウィザードも同梱
- **ネットワーク**: NetworkManager(**NAT / DHCP がそのまま通る**)→ `apt` が使える。`badaos-nat` で**この PC を NAT ルータ**にもできる(`on <外側IF> <内側IF>` = iptables マスカレード / `share <内側IF>` = NetworkManager の DHCP+NAT 共有)
- **ssh**: `openssh-server` を有効化。ホスト鍵は ISO に焼き込まず、**初回起動時にその PC 固有の鍵を生成**(ライブ環境では先に `passwd` でパスワードを設定)
- **xinetd**: 有効化済み。サンプルサービス `/etc/xinetd.d/bada-info`(TCP 7777, 既定は無効)
- **apt**: 起動時に `badaos-apt-check` が Bada の apt リポジトリの到達確認(未公開なら自動で無効化しエラーを出さない)→ `apt update`。`sudo apt install <pkg>` / `badaos-apps`(GUI)でアプリを追加
- **TeX**: **texlive-full**(日本語 platex / uplatex / lualatex-ja 含む全パッケージ。PDF マニュアル texlive-doc のみ容量のため未展開 → `/etc/dpkg/dpkg.cfg.d/01-badaos-texlive-nodoc` を消して再インストールで追加可)
- **エディタ**: **vim** / **gvim** / **emacs**(AUCTeX・emacs-mozc 付き)/ neovim / vim-latexsuite
- **端末/アプリ**: **mlterm**(日本語 UTF-8)・**screen**(UTF-8 設定済み)・xterm、ブラウザ **Falkon**、PDF **Evince**、動画 **mpv**、画像 Ristretto/GPicView、ファイル PCManFM、エディタ Mousepad/vim/emacs/neovim、電卓、アーカイバ、タスクマネージャ、ネットワーク設定 (nm-applet / nm-connection-editor)
- **あなたのリポジトリの apt リポジトリ**: `deb [trusted=yes] <release>/ ./` を登録済み。`apt install` で Bada アプリを取得
- **起動方式**: GRUB (grub-mkrescue) による BIOS + UEFI ハイブリッド ISO。`search` でカーネルのある ISO を確実に検出 → **Rufus でそのまま USB に書ける**

## 🪟🜁🐧 トリプルブート: Windows | Bada VM Pro | Linux (UEFI / Legacy 両対応)

Windows と後ろの Linux が入っている PC で、その**真ん中**に Bada VM Pro を入れます。
Windows の**すぐ下**に **Bada VM Pro 専用ブートローダの FAT パーティション**を作り、
その下の空き領域に **Bada VM Pro OS** をインストールします。**Windows の起動パーティションは触りません。**

```
┌───────┬──────────────┬──────────────────┬───────────────────┬──────────────┐
│ (ESP) │ Windows (C:) │ ★ BADAVMBOOT ★   │ ★ BADAVMPRO ★     │ Linux (ext4) │
│ 変更  │    NTFS      │ FAT32 512MiB     │ ext4 = Bada VM    │  既存のまま  │
│ しない│              │ 専用ブートローダ │ Pro OS 本体       │              │
└───────┴──────────────┴──────────────────┴───────────────────┴──────────────┘
                         ├ EFI/BadaVMPro/   (UEFI: shimx64.efi + grubx64.efi)
                         ├ EFI/BOOT/BOOTX64.EFI (このFAT専用のフォールバック)
                         └ grub/            (GRUB モジュール + grub.cfg, Legacy/UEFI 共通)
```

| 起動方式 | Bada VM Pro のブートローダ |
|:---|:---|
| **UEFI** (GPT) | 専用 FAT の `\EFI\BadaVMPro\` を UEFI 起動メニュー **「Bada VM Pro」** に登録 (起動順の先頭)。Windows の ESP・`\EFI\Microsoft\` は無変更 |
| **Legacy BIOS** (MBR) | GRUB の起動コードをディスク先頭に、モジュールと `grub.cfg` は専用 FAT の `/grub` に。基本区画が足りない (System Reserved + C: + Linux) 場合は**拡張区画 + 論理区画**で作成。元の MBR は `grub/mbr-before-badavmpro.bin` に退避 |
| **Legacy BIOS** (GPT) | 上と同じ + GRUB 埋め込み用の 1MiB BIOS 起動区画を専用 FAT の前に作成 |

どちらの方式でも GRUB メニューで **Bada VM Pro / Windows / Linux** を選べます。
(Windows は UEFI なら `bootmgfw.efi`、Legacy なら `bootmgr` を起動時に探して起動。後ろの Linux は os-prober が検出)

**ISO は BIOS(El Torito) + UEFI のハイブリッド**なので、Legacy の PC でも UEFI の PC でも USB/DVD から起動してインストールできます。

使い方:

1. Windows で **高速スタートアップを無効化**、BitLocker を一時停止、データをバックアップ
2. ISO から (Legacy でも UEFI でも) 起動し、GRUB で **「トリプルブート導入: Windows | BadaVMPro | Linux」** を選ぶ
   (またはデスクトップの「トリプルブート導入」/ 端末で `install-badaos-triboot`)
3. ディスクとサイズ (GiB, 空欄 = 間の空き全部) を選ぶ → **予定のレイアウトを確認** → 実行
4. 間に空きが無い場合は、ウィザードが **Windows (NTFS) の末尾を縮小** して空きを作るか尋ねます

確認だけ (ディスクは変更しない):
`sudo TARGET_DISK=/dev/sda PLAN_ONLY=1 /usr/local/lib/badaos/badaos-triboot-core.sh`
(`BOOT_MODE=bios` / `uefi` で起動方式を指定可)

## ⬇️ ダウンロード

[Releases](https://github.com/masaaki-avnturle/Bada/releases) の `badaos-v*` から:

| ファイル | 内容 |
|:---|:---|
| `BadaVMPro-OS-1.2.0-amd64.iso` | 起動可能 ISO 本体 |
| `BadaVMPro-OS-1.2.0-amd64.iso.sha256` | 検証用チェックサム |
| `Packages` / `Packages.gz` / `Release` | apt リポジトリ索引(flat) |
| `*.deb` | apt で配布される Bada アプリ |

## 🔥 Rufus で USB ブートを作る手順(Windows)

1. [Rufus](https://rufus.ie/) を起動し、USB メモリ(8GB 以上)を挿す
2. **「選択」**で `BadaVMPro-OS-1.2.0-amd64.iso` を指定
3. パーティション構成は **MBR**(BIOS/UEFI 両対応)または GPT(UEFI)。**書き込みモードは「ISO イメージモード」(推奨)** で OK。texlive-full 入りでもシステムを 4GB 未満の squashfs 3 つ(`filesystem.squashfs` / `filesystem-tex.squashfs` / `filesystem-fonts.squashfs`)に分けているので FAT32 の USB にそのまま入ります。UEFI 用に `\EFI\BOOT\BOOTX64.EFI` も ISO 内に置いてあります(DD モードでも可)
4. **「スタート」** →(確認が出たら)そのまま書き込み
5. 対象 PC を USB から起動(BIOS/UEFI のブートメニューで USB を選択)

> macOS / Linux では `sudo dd if=BadaVMPro-OS-1.2.0-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync` でも可(ISO は isohybrid)。

## 🖥 起動後

1. GRUB メニューで **Bada VM Pro OS** を選択 → w9wm デスクトップに自動ログイン(ユーザー `bada`)
2. **Bada VM Pro** が自動起動します
3. **実ディスクへインストール**（端末 mlterm が自動で1枚開きます / 日本語入力は Ctrl+Space）:
   - `badaos-partition` … **GParted** で使いたい HDD を初期化・パーティション作成
   - `install-badaos` … **Calamares（日本語）** で実ディスクへインストール
   - `install-badaos-simple` … Calamares が動かない場合の代替ウィザード
   - `fcitx-configtool` … 日本語入力(mozc)の設定（mozc は既定で有効。Ctrl+Space で切替）
   - `badaos-apps` … **Ubuntu 向けアプリを GUI で簡単導入**（vim/emacs/LibreOffice/GIMP など）
   - `vim` / `gvim` / `emacs` / `neovim` … エディタ
4. ネットワークは NAT/DHCP で自動接続。ターミナル(xterm)から:

```
sudo apt update
sudo apt install laevateinn bada-vm-pro   # ← あなたのリポジトリの apt リポジトリから取得
```

## 🏗 ビルドの仕組み

`.github/workflows/badaos-iso-build.yml` が(`badaos-v*` タグ / `workflow_dispatch`)で:

1. `badaos-iso/build-iso.sh` を **root** で実行(GitHub Actions の ubuntu-latest)
2. 既存アプリ Release から `.deb` を取得して同梱
3. `debootstrap` → chroot 設定(`config/setup-inside.sh`)→ `mksquashfs`(4GB 未満の 3 レイヤに分割)→ GRUB → `xorriso` で ISO 生成
4. `tools/make-apt-repo.sh` が flat な apt 索引を生成
5. ISO・チェックサム・apt 索引・`.deb` を Release に添付

---

⚠️ 注記
- ISO ビルドは実際の Ubuntu パッケージを取得して行う**本物のディストロビルド**です(texlive-full 込みで 3〜5GB 程度。各ファイルは 4GB 未満なので Rufus の ISO イメージモードで書けます)。
- `w9wm` は最小構成のためデスクトップ環境(パネル等)はありません。`xterm` からアプリを起動できます。
- Laevateinn の実車 BLE 接続は読取専用・操縦対象はシミュレーション車両のまま(以前の設計を踏襲)。
- ライブ環境の既定ユーザーは `bada`(sudo 可)。インストール時に任意のユーザーを作成できます。
