# 💿 Bada VM Pro OS — 起動可能 ISO(Ubuntu 22.04 ベース / w9wm)

**USB ブートして実ディスクにインストールできる、Bada VM Pro OS の本物の Linux ディストロ**です。
これまでの単一 HTML アプリを「ライブ CD の中で動く OS」として仕立てました。

- **ベース**: Ubuntu 22.04 (jammy) を `debootstrap` で最小構築
- **ウィンドウマネージャ**: **w9wm**(lightdm 自動ログイン)+ **日本語端末 mlterm**
- **日本語環境**: ロケール ja_JP.UTF-8 / Noto CJK フォント / 入力メソッド **fcitx-mozc**(Ctrl+Space で ON/OFF)+ **fcitx-configtool**
- **プリインストール**: Bada VM Pro / Laevateinn + 単一 HTML アプリ(`/opt/bada`)。**エディタ vim(gvim)/emacs/neovim**、git/tmux/htop、ファイルマネージャ等の定番も同梱
- **Ubuntu アプリを簡単導入**: `badaos-apps`（GUI チェックリスト）で LibreOffice/GIMP/VLC/Firefox 系/ブラウザ等を apt でワンクリック導入
- **実ディスクへインストール**: **Calamares(日本語 GUI)** + **パーティションマネージャ GParted**(使いたい HDD を初期化・作成)。うまく動かない時の代替として自作 zenity ウィザードも同梱
- **ネットワーク**: NetworkManager(**NAT / DHCP がそのまま通る**)→ `apt` が使える
- **あなたのリポジトリの apt リポジトリ**: `deb [trusted=yes] <release>/ ./` を登録済み。`apt install` で Bada アプリを取得
- **起動方式**: GRUB (grub-mkrescue) による BIOS + UEFI ハイブリッド ISO。`search` でカーネルのある ISO を確実に検出 → **Rufus でそのまま USB に書ける**

## 🪟🜁🐧 トリプルブート: Windows | Bada VM Pro | Linux

Windows と Linux が入っている PC で、**その「間」に Bada VM Pro 用のパーティション**を作り、
**Windows の起動パーティション (EFI System Partition) に Bada VM Pro のブートローダ**を作ります。

```
┌─────┬──────────────┬─────────────────┬──────────────┐
│ ESP │ Windows (C:) │ ★ BadaVMPro ★   │ Linux (ext4) │   ← 既存の Windows / Linux は消さない
│FAT32│    NTFS      │  ext4 (新規作成) │   そのまま   │
└──┬──┴──────────────┴─────────────────┴──────────────┘
   └─ \EFI\BadaVMPro\grubx64.efi (+ Secure Boot 用 shimx64.efi) を追加
      → UEFI 起動メニュー「Bada VM Pro」→ GRUB で Bada VM Pro / Windows / Linux を選択
```

使い方:

1. Windows で **高速スタートアップを無効化**、BitLocker を一時停止、データをバックアップ
2. ISO から起動し、GRUB で **「トリプルブート導入: Windows | BadaVMPro | Linux」** を選ぶ
   (またはデスクトップの「トリプルブート導入」/ 端末で `install-badaos-triboot`)
3. ディスクとサイズ (GiB, 空欄 = 間の空き全部) を選ぶ → **計画 (予定のレイアウト) を確認** → 実行
4. 間に空きが無い場合は、ウィザードが **Windows (NTFS) の末尾を縮小** して空きを作るか尋ねます
   (Windows → Linux の順に並んでいる時。逆順なら GParted = `badaos-partition` で空けてください)

仕組み (`installer/badaos-triboot-core.sh`):

- `sfdisk -J` / `blkid` で ESP・Windows(最大の NTFS)・Linux(ext4/btrfs/xfs)を検出し、Windows と Linux の**間の未割り当て領域**を 1MiB 境界で計算
- `sgdisk` で GPT 名 `BadaVMPro` / ラベル `BADAVMPRO` の ext4 を作成 → ライブの squashfs を展開
- Windows の ESP を `/boot/efi` にマウント (作業前に `/var/backups/esp-before-badavmpro.tar` へ退避)
- `grub-install --bootloader-id=BadaVMPro` で `\EFI\BadaVMPro\` を作成。**`\EFI\Microsoft\` と `\EFI\BOOT\BOOTX64.EFI` は上書きしない**
- `efibootmgr` で UEFI 起動エントリ **「Bada VM Pro」** を登録 (起動順の先頭)
- `/etc/grub.d/35_badavmpro_triboot` + os-prober が GRUB メニューに **Windows Boot Manager / Linux / UEFI 設定** を追加
- Windows 側から登録したい場合は ESP の `\EFI\BadaVMPro\add-badavmpro-bootentry.bat` を管理者で実行 (`bcdedit`)
- 変更前の確認だけ: `sudo TARGET_DISK=/dev/nvme0n1 PLAN_ONLY=1 /usr/local/lib/badaos/badaos-triboot-core.sh`

## ⬇️ ダウンロード

[Releases](https://github.com/masaaki-avnturle/Bada/releases) の `badaos-v*` から:

| ファイル | 内容 |
|:---|:---|
| `BadaVMPro-OS-1.1.0-amd64.iso` | 起動可能 ISO 本体 |
| `BadaVMPro-OS-1.1.0-amd64.iso.sha256` | 検証用チェックサム |
| `Packages` / `Packages.gz` / `Release` | apt リポジトリ索引(flat) |
| `*.deb` | apt で配布される Bada アプリ |

## 🔥 Rufus で USB ブートを作る手順(Windows)

1. [Rufus](https://rufus.ie/) を起動し、USB メモリ(8GB 以上)を挿す
2. **「選択」**で `BadaVMPro-OS-1.1.0-amd64.iso` を指定
3. パーティション構成は **MBR**(BIOS/UEFI 両対応)または GPT(UEFI)。**書き込みモードは「ISO イメージモード」**
4. **「スタート」** →(確認が出たら)そのまま書き込み
5. 対象 PC を USB から起動(BIOS/UEFI のブートメニューで USB を選択)

> macOS / Linux では `sudo dd if=BadaVMPro-OS-1.1.0-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync` でも可(ISO は isohybrid)。

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
3. `debootstrap` → chroot 設定(`config/setup-inside.sh`)→ `mksquashfs` → GRUB/isolinux → `xorriso` で ISO 生成
4. `tools/make-apt-repo.sh` が flat な apt 索引を生成
5. ISO・チェックサム・apt 索引・`.deb` を Release に添付

---

⚠️ 注記
- ISO ビルドは実際の Ubuntu パッケージを取得して行う**本物のディストロビルド**です(サイズ 1〜2GB 程度)。
- `w9wm` は最小構成のためデスクトップ環境(パネル等)はありません。`xterm` からアプリを起動できます。
- Laevateinn の実車 BLE 接続は読取専用・操縦対象はシミュレーション車両のまま(以前の設計を踏襲)。
- ライブ環境の既定ユーザーは `bada`(sudo 可)。インストール時に任意のユーザーを作成できます。
