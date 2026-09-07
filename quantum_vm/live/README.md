# BadaOS Live — 実機で起動するブータブル ISO

**本物の PC の電源を入れると、本物の GRUB ブートローダに「BadaOS GNU/Quantum 12.0」が
表示され、Windows 無しで単独起動する** ための ISO イメージです。

- ブートローダは **実物の GRUB 2**(BIOS と UEFI の両対応ハイブリッド ISO)
- 中身は最小の Debian live システム(カーネル + squashfs)で、起動すると自動ログインし、
  BadaOS 環境(`dist/bada-vm-pro.html` — Bada 言語製ハイパーバイザ + BadaOS + BadaX Server)
  を **全画面キオスク**で自動起動します(`#autoboot` で VM も自動パワーオン)
- **Ubuntu と同じ操作感の GUI インストーラ**: GRUB メニューの「Install BadaOS」から
  日本語の親切なウィザード(種類選択 → 色分きパーティションバー → 確認 → 進捗バー →
  再起動)。既定は空き領域インストールで何も消しません
- **vim・emacs・sshd・xinetd・curl・wget・grub-install・update-grub・
  bluetoothctl (bluez)・lsusb (usbutils) を実物としてプリインストール** —
  Bluetooth・USB コネクタ・NAT (DHCP) を認識します
- **インストール済み BadaOS は、起動するとウィンドウマネージャだけのデスクトップに
  なります**: 既定は **w9wm**(実物。無ければ 9wm → openbox にフォールバック)が立ち上がり、
  その中に **mlterm** が 1 枚開くだけ — BadaX のキオスク画面ではありません。mlterm から
  `sudo apt install <なんでも>` で入れた **Ubuntu 向けアプリケーションをそのまま操作**できます
  (BadaX アプリを見たいときは mlterm で `badavm` と打つだけ)。
  `badaos.wm=w9wm|afterstep|wmaker|openbox` のカーネル引数か `WM=afterstep startx` で
  いつでも切替でき、**AfterStep(NeXT 風・Wharf 付き)と Window Maker も同梱**。
  Live USB のみ従来どおりキオスク起動(`badaos.session=kiosk` でインストール後も選択可)
- **マウスカーソル表示済み + デスクトップアプリ同梱**: xterm・x11-apps(xeyes /
  xclock / xcalc)・firefox-esr・pcmanfm・**nautilus(GNOME ファイル)**・
  galculator・l3afpad・gpicview
- **NAT インターネット接続が最初から動きます**: DHCP(systemd-networkd)+
  **DNS(systemd-resolved を同梱・有効化。DHCP が DNS を配らない環境でも
  9.9.9.9 / 1.1.1.1 / 8.8.8.8 のフォールバックで名前解決)** — QEMU/VMware/
  VirtualBox の NAT でも実機の LAN でも、起動するだけで apt・firefox が使えます
- **USB メモリの接続に対応**: udisks2 + gvfs 同梱 — 挿すと pcmanfm / nautilus
  からクリックでマウント。CLI は `udisksctl mount -b /dev/sdb1` か `pmount sdb1`
  (vfat / exFAT / NTFS 対応)
- **日本語環境が最初から整っています**: ロケール `ja_JP.UTF-8`・Noto CJK フォント・
  **mlterm(日本語対応ターミナル)**・**fcitx-mozc + fcitx-configtool**(Ctrl+Space で
  日本語入力 ON/OFF。スイートに fcitx4 が無ければ fcitx5-mozc に自動フォールバック)
- **pLaTeX 日本語組版 (texlive + texlive-lang-japanese)・screen・tmux も同梱**。
  フル構成が欲しければインストール後に `sudo apt install texlive-full` 一発です
  (ISO に texlive-full を焼くと配布上限を超えるため、日本語 TeX までを同梱)
- **実ディスクの「空きスペース」への本インストール対応**: `badaos-install` の既定モードは
  空き領域に新パーティションを 1 個作るだけで、**既存の OS・パーティションは消しません**
  (os-prober が既存 OS も GRUB メニューに登録)
- **BadaOS Commander** — System Commander 風のブートマネージャ: インストール後の GRUB
  メニューは白×青のカラーメニュー + 黄色のハイライトバーになり、os-prober の検出に加えて
  **他のブータブルパーティション (FAT/NTFS/exFAT, 55AA ブートレコード) ごとに
  チェインロードエントリ**を自動生成 — System Commander と同じ「この 1 画面にマシンの
  全 OS が並び、選ぶとその OS 自身のブートセクタへチェインする」方式です
  (`/etc/grub.d/25_badaos_commander`、`update-grub` のたびに再生成)
- **DHCP ネットワーク + 本物の Debian フルアーカイブ**: ネット接続があれば
  `sudo apt update && sudo apt install <なんでも>` で **6 万超パッケージ
  (Ubuntu と同級の規模)** をインストール可能。オフラインでも本体は完全動作
- 日本語フォント (Noto CJK) 同梱
- ISO は [Releases](https://github.com/masaaki-avnturle/Bada/releases) の
  `BadaOS-12.0-live-amd64.iso`(CI の `live-iso` ジョブがビルド)

QEMU での実起動検証済み — 電源投入直後の画面はこの通り GRUB メニューです:

```
                        GNU GRUB  version 2.12
 ┌──────────────────────────────────────────────────────────────┐
 │*BadaOS GNU/Quantum 12.0 (Live)                               │
 │ BadaOS GNU/Quantum 12.0 (Live, copy to RAM / toram)          │
 │ BadaOS console (text only -- sudo badaos-install for a real disk)
 └──────────────────────────────────────────────────────────────┘
```

## 使い方 1 — USB から起動(データを消さない・おすすめ)

1. Windows 10/11 で [Rufus](https://rufus.ie/) か balenaEtcher を使い、
   `BadaOS-12.0-live-amd64.iso` を USB メモリに書き込む(Linux なら
   `dd if=BadaOS-12.0-live-amd64.iso of=/dev/sdX bs=4M status=progress`)
2. PC を再起動し、ブートメニュー(メーカーにより F12 / F11 / Esc / F8)で USB を選択
3. **GRUB メニューに BadaOS が表示** → Enter で起動 → 全画面で BadaOS が立ち上がります
   (コンソールに落ちるには Ctrl+Alt+F2、ログイン `bada` / パスワード `badaos`)

## 使い方 2 — Ubuntu 風の GUI インストーラでインストール(いちばん簡単・おすすめ)

USB から起動して、GRUB メニューで **「Install BadaOS (friendly GUI installer, Ubuntu style)」**
を選ぶだけで、**Ubuntu のインストーラ(Ubiquity)と同じ操作感の親切な GUI ウィザード**が
全画面で立ち上がります:

1. **ようこそ** → 2. **インストールの種類**(空き領域=推奨 / **パーティションを削除して
   置き換え**〈Calamares の「置き換え」〉/ パーティション指定 / ディスク全体)→
   3. **ディスクの選択** — Ubuntu と同じ**色分きパーティションバー**で
   「どこが残り、どこに BadaOS が入るか」が一目で分かります → 4. **書き込み確認**
   (ここまで一切ディスクに書き込みません)→ 5. **進捗バー + BadaOS 紹介スライド** →
   6. **完了 → 今すぐ再起動**

既定の「空き領域にインストール」は**既存の OS・データを一切消しません**。日本語 UI、
キーボードだけでも操作可能(Enter で次へ)。中身は下記 `badaos-install` と同じ
検証済みエンジンです(GUI は `installer/` の HTML ウィザード + localhost バックエンド)。

## 使い方 2b — コマンドラインでインストール(同じエンジン)

**ディスク全体は消しません。** インストーラの既定モードは、選んだハードディスクの
**未割り当て(空き)領域に新しいパーティションを 1 個作るだけ**で、既存のパーティション
(Windows・Linux・データ)には一切触れません。

1. 使い方 1 の手順で USB から BadaOS Live を起動(「console (text only)」でも可)
2. (空き領域が無い場合)先に Windows の「ディスクの管理 → ボリュームの縮小」などで
   4 GiB 以上の空き領域を作っておく
3. ターミナルで:
   ```
   sudo badaos-install
   ```
4. 対象ディスク(例: `sda`)を入力 → モードで **1 (FREE SPACE・既定)** を選択 →
   最大の空き領域が表示されるので、確認のため `INSTALL FREE sda` とタイプ
   (モード **2** は Calamares 流の**パーティション置き換え** — 例えば既存の `sda4` を
   削除して置き換えるなら `sda4` を指定し `REPLACE sda4` で確認 → 空いた場所に BadaOS。
   モード **3** は既存パーティション 1 個だけをフォーマットして使用)

> **必要なパーティションサイズは自動計測されます**: インストーラは起動時に
> ライブシステムの実サイズを測り(`du`)、+20% の余裕を足した「この ISO が
> 実際に必要とするサイズ」で判定します(現行ビルドはアプリ同梱が増えたため
> 約 5〜6 GB)。小さすぎるパーティションを選ぶと、**書き込む前に**
> 「this BadaOS build needs about N MiB」と明確に断られます(以前は
> コピー途中で "No space left on device" エラーになっていました)。
> GUI インストーラの空き容量判定も同じ計測値を使います。

> 実ディスクの名前はどちらでも動きます: **SATA / USB / VMware の実ディスク (`sda`)** も
> QEMU/KVM の virtio (`vda`) も、NVMe (`nvme0n1`) も同じ手順です。GUI・CLI とも、
> **4 つのプライマリパーティションで満杯の MBR ディスクでも「置き換え」なら**削除で
> 空いた枠にそのままインストールできます(QEMU の SATA ディスク `/dev/sda` +
> `sda1`〜`sda4` 構成で、`sda4` の削除→置き換え→単独起動まで通しで検証済み)。
5. 新パーティション作成 → システムコピー → **ブートローダへの記銘**:
   - **BIOS 機**: `grub-install` が MBR に GRUB を書き込み(パーティションテーブルは保持)、
     `update-grub` + **os-prober が既存の Windows / Linux も GRUB メニューに登録**します
   - **UEFI 機**: **既存の EFI システムパーティションをフォーマットせずにそのまま使い**、
     ファームウェアのブートメニューに「BadaOS」エントリを追加するだけです
6. USB を抜いて再起動 → **GRUB メニューに「BadaOS GNU/Quantum」と元の OS が並び**、
   どちらも選んで起動できます
7. インストール済みパーティションは**実ディスクからも、バーチャルマシンからも**起動できます
   (VMware の物理ディスク割り当て / QEMU の `-drive file=/dev/sdX` など raw ディスクを
   VM に渡せば、同じ GRUB → BadaOS がそのまま VM 内で立ち上がります)

> `grub-install` と `update-grub` は Live システムにもインストール済み BadaOS にも
> **最初から入っています**(grub2-common / grub-pc-bin / grub-efi-amd64-bin)。

## インストール後の起動 — ウィンドウマネージャだけのデスクトップ

インストール済み BadaOS を起動すると、**BadaX のキオスク画面ではなく、
ウィンドウマネージャだけのシンプルなデスクトップ**が立ち上がります:

- 既定は **w9wm**(Plan 9 風。パッケージが無いアーキテクチャでは 9wm → openbox に
  自動フォールバック)。ルートで B3(右クリック)メニュー、4 仮想デスクトップ
- その中に **mlterm(日本語対応ターミナル)が 1 枚**開いた状態で始まります。
  fcitx-mozc 常駐済みなので Ctrl+Space でそのまま日本語入力できます
- **マウスカーソルは最初から表示されます**(素の X は最初のクライアントがカーソルを
  設定するまでルートカーソルを隠すため、セッション開始時に `xsetroot -cursor_name
  left_ptr` で古典的な矢印カーソルを設定しています)
- **X アプリ・一般アプリケーションを同梱**: `xterm`・**x11-apps(xeyes / xclock /
  xcalc / xlogo など)**・**firefox-esr(ウェブブラウザ)**・**pcmanfm
  (ファイルマネージャ)**・galculator(電卓)・l3afpad(テキストエディタ)・
  gpicview(画像ビューア)— mlterm から `xeyes &` `firefox &` `pcmanfm &` で起動
- mlterm から普通に **Ubuntu 向けアプリケーションを操作**: `sudo apt install gimp`
  など Debian フルアーカイブのアプリを入れて、そのまま
  ウィンドウとして使えます(`htop`・`mc`・`screen`・`tmux` は同梱済み)。
  **NAT + DNS が最初から通っている**ので `sudo apt install nautilus` も
  そのまま成功します(nautilus 自体もプリインストール済み)
- **USB メモリ**は挿すだけで pcmanfm / nautilus から開けます(udisks2 + gvfs。
  CLI: `udisksctl mount -b /dev/sdb1`)
- **WM の切替**: カーネル引数 `badaos.wm=afterstep` / `badaos.wm=wmaker` /
  `badaos.wm=w9wm`(GRUB メニューで `e` を押して追記)、またはコンソールから
  `WM=wmaker startx`。**AfterStep と Window Maker は実物を同梱**しています
- **BadaX(BadaVM Pro)を使いたいとき**は、mlterm で `badavm` と打つとアプリウィンドウ
  として立ち上がります(従来の全画面キオスクに戻すには `badaos.session=kiosk`)
- Live USB(この ISO そのもの)は従来どおりキオスク自動起動のままです

## 使い方 3 — バーチャルマシン経由で実ディスクへインストール(検証済み)

VMware / VirtualBox / QEMU の**仮想マシンに普通の OS と同じ手順でインストール**できます:
新規 VM を作成 → ISO を光学ドライブに割り当てて起動 → GRUB メニューの
**「Install BadaOS into FREE SPACE of /dev/vda (VM, keeps other partitions)」**
(空き領域へ・既存パーティション保持)か
**「Install BadaOS to /dev/vda (VIRTUAL MACHINE, unattended)」**(ディスク全体を消去)
を選ぶだけ(QEMU/KVM の virtio ディスク用・全自動)。VMware 等の sda ディスクでは
通常の Live 起動から `sudo badaos-install` → 完了後 ISO を外して再起動すると、
**VM がディスク単体から GRUB → BadaOS を起動**します。空き領域インストールも含め、
この一連の流れは QEMU 上で実際にインストール→ディスク単独起動まで通しで検証しています。

無人モードはコマンドでも使えます:
```
sudo badaos-install --auto-free /dev/vda   # 空き領域へ (既存パーティション保持)
sudo badaos-install --auto /dev/vda        # ディスク全体を消去
```
(確認なしでインストールし、完了後に自動で電源断 — VM 専用)

## 使い方 3b — ディスク全体を消して単独マシン化(明示モード)

> ⚠️ **モード 3 を選ぶと選んだディスクは完全に消去されます。** 消えて困るデータのある
> PC では実行しないでください。まずは古い PC・予備 PC・予備ディスクでどうぞ。

`sudo badaos-install` → モード **3 (WHOLE DISK)** → `INSTALL sda` とタイプ。
GPT/MBR を自動判別してパーティション作成 → システムコピー → GRUB を MBR/ESP へ →
再起動後は**その PC が BadaOS 単独起動マシン**になります。

## 使い方 4 — 既存 Linux とデュアルブート(何も消さない)

既に GRUB で起動している Linux マシンでは、ISO をループバック起動エントリとして
追加できます:

```
sudo bash badaos-add-grub-entry.sh BadaOS-12.0-live-amd64.iso
```

ISO が `/boot/badaos/` にコピーされ、`/etc/grub.d/40_custom` に
「BadaOS GNU/Quantum 12.0 (ISO)」エントリが追加され、`update-grub` 後の
再起動から GRUB メニューに BadaOS が並びます(削除は 40_custom の該当ブロックを
消して `update-grub`)。

## 自分でビルドする

```
node quantum_vm/tools/build-vm.js
sudo bash quantum_vm/live/build-live-iso.sh        # Debian/Ubuntu ホスト
# -> quantum_vm/dist/BadaOS-12.0-live-amd64.iso
```

必要パッケージ: `debootstrap debian-archive-keyring squashfs-tools xorriso mtools
grub-pc-bin grub-efi-amd64-bin grub-common`

| ファイル | 役割 |
|:--|:--|
| `build-live-iso.sh` | debootstrap → キオスク設定 → squashfs → `grub-mkrescue`(ISO 生成) |
| `grub-live.cfg` | 実機の電源投入時に表示される GRUB メニュー |
| `installer/` | **Ubuntu 風 GUI インストーラ** — `index.html`(日本語ウィザード: 種類選択・パーティションバー・確認・進捗)+ `badaos-installer-httpd.py`(localhost:7788 の root バックエンド、実作業は `badaos-install --run` に委譲) |
| `badaos-install` | Live 内から実ディスクへ本インストール — 既定は**空き領域へ**(何も消さない)、既存パーティション再利用 / ディスク全体消去も選択可(MBR/ESP へ `grub-install`、os-prober で既存 OS も GRUB メニューへ)。GUI から使う非対話 `--run` モード付き |
| `25_badaos_commander` | **BadaOS Commander** — System Commander 風ブートマネージャ (`/etc/grub.d/` スクリプト: カラーメニュー + 他 OS パーティションへのチェインロードエントリ生成) |
| `badaos-add-grub-entry.sh` | 既存 Linux の GRUB に ISO ループバックエントリを追加 |

> BadaVM Pro アプリ内の sysinst「rd0 実ディスク」はシミュレーションのままです。
> 実機の実ディスクに触るのは、この Live ISO の `badaos-install` だけです。
