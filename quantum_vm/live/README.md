# BadaOS Live — 実機で起動するブータブル ISO

**本物の PC の電源を入れると、本物の GRUB ブートローダに「BadaOS GNU/Quantum 12.0」が
表示され、Windows 無しで単独起動する** ための ISO イメージです。

- ブートローダは **実物の GRUB 2**(BIOS と UEFI の両対応ハイブリッド ISO)
- 中身は最小の Debian live システム(カーネル + squashfs)で、起動すると自動ログインし、
  BadaOS 環境(`dist/bada-vm-pro.html` — Bada 言語製ハイパーバイザ + BadaOS + BadaX Server)
  を **全画面キオスク**で自動起動します(`#autoboot` で VM も自動パワーオン)
- **vim・emacs・sshd・xinetd・curl・wget を実物としてプリインストール**
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

## 使い方 2 — バーチャルマシン経由で実ディスクへインストール(検証済み)

VMware / VirtualBox / QEMU の**仮想マシンに普通の OS と同じ手順でインストール**できます:
新規 VM を作成 → ISO を光学ドライブに割り当てて起動 → GRUB メニューの
**「Install BadaOS to /dev/vda (VIRTUAL MACHINE, unattended)」**(QEMU/KVM の
virtio ディスク用・自動)か、通常の Live 起動から `sudo badaos-install`(VMware 等の
sda ディスク)→ 完了後 ISO を外して再起動すると、**VM がディスク単体から GRUB →
BadaOS を起動**します。この一連の流れは QEMU 上で実際にインストール→ディスク単独起動まで
通しで検証しています(下のスクリーンショット参照)。

無人モードはコマンドでも使えます: `sudo badaos-install --auto /dev/vda`
(確認なしで消去・インストールし、完了後に自動で電源断 — VM 専用)

## 使い方 3 — 実 PC の実ディスクへ本インストール(単独起動マシン化)

> ⚠️ **選んだディスクは完全に消去されます。** 消えて困るデータのある PC では実行しないでください。
> まずは古い PC・予備 PC・予備ディスクでどうぞ。

1. USB から BadaOS Live を起動(3 番目の「console (text only)」でも可)
2. ターミナルで:
   ```
   sudo badaos-install
   ```
3. 対象ディスク(例: `sda`)を入力し、確認のため `INSTALL sda` とタイプ
4. インストーラが GPT/MBR を自動判別してパーティション作成 → システムコピー →
   **BIOS 機なら `grub-install` が実ディスクの MBR に GRUB を書き込み**、
   **UEFI 機なら EFI ブートメニューに「BadaOS」エントリを登録**します
5. USB を抜いて再起動 → **その PC の GRUB メニューが「BadaOS GNU/Quantum」を表示し、
   ハードディスクから単独起動**します

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
| `badaos-install` | Live 内から実ディスクへ本インストール(MBR/ESP へ `grub-install`) |
| `badaos-add-grub-entry.sh` | 既存 Linux の GRUB に ISO ループバックエントリを追加 |

> BadaVM Pro アプリ内の sysinst「rd0 実ディスク」はシミュレーションのままです。
> 実機の実ディスクに触るのは、この Live ISO の `badaos-install` だけです。
