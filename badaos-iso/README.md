# 💿 Bada VM Pro OS — 起動可能 ISO(Ubuntu 22.04 ベース / w9wm)

**USB ブートして実ディスクにインストールできる、Bada VM Pro OS の本物の Linux ディストロ**です。
これまでの単一 HTML アプリを「ライブ CD の中で動く OS」として仕立てました。

**必要最小限の構成**です。事前に入っているのは「日本語・w9wm・NAT・プリンター・vim・emacs・apt」だけで、
mlterm・ssh・xinetd・texlive-full・screen などは**後から apt コマンドで入れる**方式にしました。

| 区分 | 内容 |
|:---|:---|
| ベース | Ubuntu 22.04 (jammy) を `debootstrap` で最小構築 |
| デスクトップ | **w9wm**(lightdm 自動ログイン)+ 端末 **xterm**(日本語フォント・日本語入力を設定済み) |
| 日本語 | ロケール ja_JP.UTF-8 / Noto CJK フォント / **fcitx-mozc**(Ctrl+Space / 半角全角 で ON/OFF)/ `fcitx-configtool` |
| NAT | NetworkManager(**NAT / DHCP がそのまま通る**)。`badaos-nat` で**この PC を NAT ルータ**にも(`on <外側IF> <内側IF>` / `share <内側IF>`) |
| プリンター | **CUPS** + `printer-driver-all`(Epson/Canon/HP/Brother…)。USB(ipp-usb)/ネットワーク(AirPrint・IPP Everywhere 自動検出)。デスクトップ「プリンターの設定」か `http://localhost:631`。ユーザーは `lpadmin` 所属 |
| エディタ (事前導入) | **vim** / gvim / **emacs**(emacs-mozc 付き) |
| apt | パッケージ索引を同梱 → **起動直後から** `sudo apt install <pkg>` が使える |
| インストーラ | トリプルブート導入 / Calamares / かんたんウィザード / GParted |

### 後から apt で入れるもの

```
badaos-extras mlterm ssh xinetd screen texlive      # まとめて (GUI: デスクトップ「追加ソフトを導入」)

# または apt コマンドで個別に
sudo apt update
sudo apt install mlterm mlterm-im-fcitx   # 日本語端末 (+ mozc 入力プラグイン。~/.mlterm は設定済み)
sudo apt install openssh-server           # ssh
sudo apt install xinetd                   # xinetd
sudo apt install screen                   # screen (~/.screenrc は UTF-8 設定済み)
sudo apt install texlive-full             # TeX 一式 (日本語 platex/uplatex 含む。数 GB)
```

その他のアプリは `badaos-apps`(GUI チェックリスト)か `sudo apt install <pkg>` で。
起動方式: GRUB による BIOS + UEFI ハイブリッド ISO(各ファイル 4GB 未満なので **Rufus の ISO イメージモード**で書けます)。

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
| **Legacy BIOS** (MBR) | **ディスク先頭 (MBR) = Windows の先頭ヘッダは書き換えません。** GRUB の起動コードを**専用 FAT パーティションの先頭セクタ (VBR)** に、GRUB 本体を FAT 直前の未使用 1MiB に置き、専用 FAT を**アクティブ**にします → Windows の MBR 起動コードがそのまま Bada VM Pro のブートローダを起動。基本区画の空きが 1 つだけ (System Reserved + C: + Linux) の場合は**拡張区画 + 論理区画**で作り、起動コードは拡張区画の先頭 (EBR) に置いてそれをアクティブに。元に戻す: `sudo sfdisk --activate /dev/sdX 1`(元のアクティブ区画番号)。書き換え前のセクタは `grub/*-before-badavmpro.bin` に退避 |
| **Legacy BIOS** (GPT) | (Windows では稀な構成) 保護 MBR の起動コード + GRUB 埋め込み用の 1MiB BIOS 起動区画を専用 FAT の前に作成 |

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

## 🛠 起動途中で止まる時

GRUB メニューは出るのにデスクトップまで行かない場合は、メニューで次を選んでください:

| メニュー | 用途 |
|:---|:---|
| **インストール: テキスト画面** | **画面が真っ黒でインストールできない PC はこれ。** 画面 (X / GPU) を使わず、文字の画面 (英語表示) でトリプルブート導入が自動で始まる。ディスク番号・サイズ・ユーザー名・パスワードを入れて `yes` で実行 |
| **セーフグラフィック** | 画面が真っ黒/固まる PC (グラフィックドライバの相性)。`nomodeset` で起動 |
| **詳細表示** | 起動メッセージをすべて表示。止まった所の最後の数行が原因の手がかり |
| **テキストモード** | 画面 (GUI) なしで起動。ユーザー `bada`(パスワードなし Enter)でログインし `sudo badaos-triboot-text` で同じトリプルブート導入ができる |

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
3. パーティション構成は **MBR**(BIOS/UEFI 両対応)または GPT(UEFI)。**書き込みモードは「ISO イメージモード」(推奨)** で OK。texlive-full 入りでもシステムを 4GB 未満の squashfs 3 つ(`filesystem.squashfs` / `filesystem-tex.squashfs` / `filesystem-fonts.squashfs`)に分けているので FAT32 の USB にそのまま入ります。UEFI 用ローダ `\efi\boot\bootx64.efi` は USB 上のファイルで起動ディスクを探すので、コピーした USB からも起動します(DD モードでも可)
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
