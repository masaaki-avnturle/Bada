# 💿 Bada VM Pro OS — 起動可能 ISO(Ubuntu 22.04 ベース / w9wm)

**USB ブートして実ディスクにインストールできる、Bada VM Pro OS の本物の Linux ディストロ**です。
これまでの単一 HTML アプリを「ライブ CD の中で動く OS」として仕立てました。

- **ベース**: Ubuntu 22.04 (jammy) を `debootstrap` で最小構築
- **ウィンドウマネージャ**: **w9wm**(lightdm 自動ログイン)+ **日本語端末 mlterm**
- **日本語環境**: ロケール ja_JP.UTF-8 / Noto CJK フォント / 入力メソッド **fcitx-mozc**(Ctrl+Space で ON/OFF)+ **fcitx-configtool**
- **プリインストール**: Bada VM Pro / Laevateinn(`.deb` があれば)+ 単一 HTML アプリを `/opt/bada` に
- **実ディスクへインストール**: **Calamares(日本語 GUI)** + **パーティションマネージャ GParted**(使いたい HDD を初期化・作成)。うまく動かない時の代替として自作 zenity ウィザードも同梱
- **ネットワーク**: NetworkManager(**NAT / DHCP がそのまま通る**)→ `apt` が使える
- **あなたのリポジトリの apt リポジトリ**: `deb [trusted=yes] <release>/ ./` を登録済み。`apt install` で Bada アプリを取得
- **起動方式**: GRUB (grub-mkrescue) による BIOS + UEFI ハイブリッド ISO。`search` でカーネルのある ISO を確実に検出 → **Rufus でそのまま USB に書ける**

## ⬇️ ダウンロード

[Releases](https://github.com/masaaki-avnturle/Bada/releases) の `badaos-v*` から:

| ファイル | 内容 |
|:---|:---|
| `BadaVMPro-OS-1.0.4-amd64.iso` | 起動可能 ISO 本体 |
| `BadaVMPro-OS-1.0.4-amd64.iso.sha256` | 検証用チェックサム |
| `Packages` / `Packages.gz` / `Release` | apt リポジトリ索引(flat) |
| `*.deb` | apt で配布される Bada アプリ |

## 🔥 Rufus で USB ブートを作る手順(Windows)

1. [Rufus](https://rufus.ie/) を起動し、USB メモリ(8GB 以上)を挿す
2. **「選択」**で `BadaVMPro-OS-1.0.4-amd64.iso` を指定
3. パーティション構成は **MBR**(BIOS/UEFI 両対応)または GPT(UEFI)。**書き込みモードは「ISO イメージモード」**
4. **「スタート」** →(確認が出たら)そのまま書き込み
5. 対象 PC を USB から起動(BIOS/UEFI のブートメニューで USB を選択)

> macOS / Linux では `sudo dd if=BadaVMPro-OS-1.0.4-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync` でも可(ISO は isohybrid)。

## 🖥 起動後

1. GRUB メニューで **Bada VM Pro OS** を選択 → w9wm デスクトップに自動ログイン(ユーザー `bada`)
2. **Bada VM Pro** が自動起動します
3. **実ディスクへインストール**（端末 mlterm が自動で1枚開きます / 日本語入力は Ctrl+Space）:
   - `badaos-partition` … **GParted** で使いたい HDD を初期化・パーティション作成
   - `install-badaos` … **Calamares（日本語）** で実ディスクへインストール
   - `install-badaos-simple` … Calamares が動かない場合の代替ウィザード
   - `fcitx-configtool` … 日本語入力(mozc)の設定
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
