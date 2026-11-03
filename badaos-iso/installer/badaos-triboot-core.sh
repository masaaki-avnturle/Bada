#!/bin/bash
# =============================================================================
# badaos-triboot-core.sh — Windows / Bada VM Pro / Linux の「トリプルブート」導入本体
#
#   ディスク構成 (例):
#
#     ┌─────┬──────────────┬────────────────┬──────────────┐
#     │ ESP │ Windows (C:) │ ★ BadaVMPro ★  │ Linux (ext4) │
#     │FAT32│    NTFS      │   ext4 (新規)  │   既存のまま │
#     └──┬──┴──────────────┴────────────────┴──────────────┘
#        └─ Windows の起動パーティション (EFI System Partition) に
#           \EFI\BadaVMPro\ (GRUB) を追加し、UEFI 起動メニュー
#           「Bada VM Pro」を作る。GRUB から Windows / Linux も選べる。
#
#   ・Windows と Linux の「間」にある未割り当て領域に BadaVMPro パーティションを作る
#   ・間に空きが無い場合は SHRINK_WINDOWS=1 で Windows(NTFS) の末尾を縮小して空ける
#     (Windows → Linux の順に並んでいる時のみ。縮小前に ntfsresize で検査)
#   ・Windows / Linux の既存パーティションは消さない。ESP の既存ファイルも上書きしない
#     (\EFI\Microsoft\ と \EFI\BOOT\BOOTX64.EFI はそのまま。作業前に ESP を tar で退避)
#
#   環境変数:
#     TARGET_DISK     対象ディスク (例 /dev/sda, /dev/nvme0n1)          [必須]
#     BADA_SIZE_GB    BadaVMPro パーティションの大きさ (GiB, 既定: 空き全部)
#     SHRINK_WINDOWS  1 なら空きが無い時に Windows を縮小して作る (既定 0)
#     NEW_HOST / NEW_USER / NEW_PASS   ホスト名 / ユーザー / パスワード
#     PLAN_ONLY       1 なら検出結果と作成予定のレイアウトを表示して終了 (変更なし)
#
#   出力: 「NN<改行># メッセージ」形式 (zenity --progress 用)。エラーは標準エラー。
#   PLAN_ONLY=1 はディスクイメージファイルにも使える (sfdisk/blkid -O で読むだけ)。
# =============================================================================
set -euo pipefail

DISK="${TARGET_DISK:?TARGET_DISK 未指定}"
HOST="${NEW_HOST:-badaos}"
USER_NAME="${NEW_USER:-bada}"
PASS="${NEW_PASS:-bada}"
BADA_SIZE_GB="${BADA_SIZE_GB:-0}"
SHRINK_WINDOWS="${SHRINK_WINDOWS:-0}"
PLAN_ONLY="${PLAN_ONLY:-0}"
MIN_GB=12                 # 展開後のシステムが収まる最小サイズ
BOOT_ID="BadaVMPro"       # \EFI\BadaVMPro\ と UEFI 起動メニュー名
BOOT_LABEL="Bada VM Pro"
MNT="/mnt/badavmpro"

emit(){ [ "$PLAN_ONLY" = "1" ] || printf '%s\n# %s\n' "$1" "$2"; }
fail(){ echo "ERROR: $*" >&2; exit 1; }
log(){ echo "$*" >&2; }

GUID_ESP="C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
GUID_MSR="E3C9E316-0B5C-4DB8-817D-F92DF00215AE"
GUID_LINUX="0FC63DAF-8483-4772-8E79-3D69D8477DE4"

# ---------------------------------------------------------------------------
# 1. パーティション表の読み取り (sfdisk -J) と各パーティションのファイルシステム判定
# ---------------------------------------------------------------------------
[ -e "$DISK" ] || fail "$DISK がありません"
JSON="$(sfdisk -J "$DISK" 2>/dev/null)" || fail "$DISK のパーティション表を読めません (GPT/MBR が必要)"

# 「node start size type name」の TSV に整形 (python3 は live にもある)
TABLE="$(printf '%s' "$JSON" | python3 -c '
import json,sys
t=json.load(sys.stdin)["partitiontable"]
print("#", t.get("label",""), t.get("sectorsize",512), t.get("lastlba",0) or 0)
for p in t.get("partitions",[]):
    print(p["node"], p["start"], p["size"], str(p.get("type","")).upper(), (p.get("name") or "-").replace(" ","_"), sep="\t")
')"
LABEL="$(echo "$TABLE" | head -1 | awk '{print $2}')"
SECT="$(echo "$TABLE"  | head -1 | awk '{print $3}')"
LASTLBA="$(echo "$TABLE" | head -1 | awk '{print $4}')"
[ "$LASTLBA" -gt 0 ] 2>/dev/null || LASTLBA=$(( $(blockdev --getsz "$DISK" 2>/dev/null || echo $(( $(stat -c %s "$DISK") / 512 ))) * 512 / SECT - 34 ))
PARTS="$(echo "$TABLE" | tail -n +2)"
[ -n "$PARTS" ] || fail "$DISK にパーティションがありません (Windows と Linux が入ったディスクを選んでください)"

fstype(){ # $1=start sector → ファイルシステム種別 (ディスク先頭からのオフセットで判定)
  blkid -p -o value -s TYPE -O $(( $1 * SECT )) "$DISK" 2>/dev/null || true; }
fslabel(){ blkid -p -o value -s LABEL -O $(( $1 * SECT )) "$DISK" 2>/dev/null || true; }

declare -a P_NODE P_START P_END P_TYPE P_FS P_NAME
i=0
while IFS=$'\t' read -r node start size type name; do
  [ -n "$node" ] || continue
  P_NODE[i]="$node"; P_START[i]="$start"; P_END[i]=$(( start + size - 1 ))
  P_TYPE[i]="$type"; P_NAME[i]="$name"; P_FS[i]="$(fstype "$start")"
  i=$((i+1))
done <<< "$PARTS"
N=$i

# ---------------------------------------------------------------------------
# 2. Windows / Linux / ESP を見つける
# ---------------------------------------------------------------------------
WIN=-1; LIN=-1; ESPI=-1
for ((k=0;k<N;k++)); do
  sz=$(( P_END[k] - P_START[k] ))
  case "${P_TYPE[k]}" in "$GUID_ESP"|EF) [ $ESPI -lt 0 ] && ESPI=$k ;; esac
  if [ "${P_FS[k]}" = "ntfs" ]; then
    # 最大の NTFS = Windows (C:)。回復パーティション (数百 MB) は除外される
    if [ $WIN -lt 0 ] || [ $sz -gt $(( P_END[WIN] - P_START[WIN] )) ]; then WIN=$k; fi
  fi
  case "${P_FS[k]}" in ext4|ext3|ext2|btrfs|xfs)
    lb="$(fslabel "${P_START[k]}")"
    [ "$lb" = "BADAVMPRO" ] && fail "既に BadaVMPro パーティション (${P_NODE[k]}) があります"
    if [ $LIN -lt 0 ] || [ $sz -gt $(( P_END[LIN] - P_START[LIN] )) ]; then LIN=$k; fi ;;
  esac
done
[ $WIN -ge 0 ] || fail "Windows (NTFS) パーティションが見つかりません"
[ $LIN -ge 0 ] || fail "Linux (ext4/btrfs/xfs) パーティションが見つかりません"

if [ -d /sys/firmware/efi ]; then FW="uefi"
elif [ "$PLAN_ONLY" = "1" ] && [ "$LABEL" = "gpt" ]; then FW="uefi"   # イメージ検査時は GPT=UEFI とみなす
else FW="bios"; fi
if [ "$FW" = "uefi" ]; then
  [ "$LABEL" = "gpt" ] || fail "UEFI 起動なのにディスクが GPT ではありません"
  [ $ESPI -ge 0 ] || fail "Windows の起動パーティション (EFI System Partition) が見つかりません"
fi

# ---------------------------------------------------------------------------
# 3. Windows と Linux の「間」の空き領域を計算 (1MiB 境界)
# ---------------------------------------------------------------------------
ALIGN=$(( 1048576 / SECT ))
if [ ${P_START[WIN]} -lt ${P_START[LIN]} ]; then A=$WIN; B=$LIN; ORDER="Windows → Linux"; else A=$LIN; B=$WIN; ORDER="Linux → Windows"; fi
LO=${P_END[A]}; HI=${P_START[B]}

# 間の区間 [LO+1, HI-1] から、既存パーティションが占めていない最大の空きを探す
best_s=0; best_e=-1
cur=$(( LO + 1 ))
for idx in $(for ((k=0;k<N;k++)); do echo "${P_START[k]} $k"; done | sort -n | awk '{print $2}'); do
  s=${P_START[idx]}; e=${P_END[idx]}
  [ $e -le $LO ] && continue
  [ $s -ge $HI ] && break
  if [ $s -gt $cur ] && [ $(( s - cur )) -gt $(( best_e - best_s + 1 )) ]; then best_s=$cur; best_e=$(( s - 1 )); fi
  [ $(( e + 1 )) -gt $cur ] && cur=$(( e + 1 ))
done
if [ $HI -gt $cur ] && [ $(( HI - cur )) -gt $(( best_e - best_s + 1 )) ]; then best_s=$cur; best_e=$(( HI - 1 )); fi

GAP_S=$(( (best_s + ALIGN - 1) / ALIGN * ALIGN ))
GAP_E=$(( (best_e + 1) / ALIGN * ALIGN - 1 ))
GAP_GB=0; [ $GAP_E -gt $GAP_S ] && GAP_GB=$(( (GAP_E - GAP_S + 1) * SECT / 1073741824 ))

want_sectors(){ # 作成するサイズ (セクタ)
  if [ "$BADA_SIZE_GB" -gt 0 ] 2>/dev/null; then echo $(( BADA_SIZE_GB * 1073741824 / SECT )); else echo 0; fi; }
WANT=$(want_sectors)

SHRINK=0
if [ $GAP_GB -lt $MIN_GB ]; then
  if [ "$SHRINK_WINDOWS" = "1" ] && [ $A -eq $WIN ]; then
    [ $WANT -gt 0 ] || WANT=$(( 40 * 1073741824 / SECT ))   # 縮小時の既定 40GiB
    SHRINK=1
    # Windows 末尾を WANT 分だけ縮める → Windows 直後に空きができる (= Linux との間)
    NEW_WIN_END=$(( (P_END[WIN] + 1 - WANT) / ALIGN * ALIGN - 1 ))
    GAP_S=$(( NEW_WIN_END + 1 )); GAP_E=$(( GAP_S + WANT - 1 ))
    # 縮小で空く領域の後ろに既に空きがあれば加算されるが、ここでは WANT 分のみ使う
    [ $(( NEW_WIN_END - P_START[WIN] )) -gt $(( 30 * 1073741824 / SECT )) ] || \
      fail "Windows を縮小すると 30GiB を下回ります。BADA_SIZE_GB を小さくしてください"
  elif [ "$SHRINK_WINDOWS" = "1" ]; then
    fail "Linux が Windows より前にあるため Windows の縮小では「間」に空きを作れません。GParted で Linux を縮小してから再実行してください"
  else
    fail "Windows と Linux の間に ${MIN_GB}GiB 以上の空きがありません (現在 ${GAP_GB}GiB)。SHRINK_WINDOWS=1 で Windows を縮小するか、GParted (badaos-partition) で空きを作ってください"
  fi
else
  if [ $WANT -gt 0 ] && [ $WANT -lt $(( GAP_E - GAP_S + 1 )) ]; then
    GAP_E=$(( GAP_S + WANT / ALIGN * ALIGN - 1 ))
  fi
fi
BADA_S=$GAP_S; BADA_E=$GAP_E
BADA_GB=$(( (BADA_E - BADA_S + 1) * SECT / 1073741824 ))
[ $BADA_GB -ge $MIN_GB ] || fail "BadaVMPro パーティションが ${MIN_GB}GiB 未満になります (${BADA_GB}GiB)"

# ---------------------------------------------------------------------------
# 4. 予定の表示
# ---------------------------------------------------------------------------
gib(){ awk -v s="$1" -v b="$SECT" 'BEGIN{printf "%.1f", s*b/1073741824}'; }
{
  echo "=== Bada VM Pro トリプルブート計画 ==="
  echo "ディスク      : $DISK  ($LABEL, ${SECT}B/セクタ, 起動方式 $FW)"
  echo "並び          : $ORDER"
  [ $ESPI -ge 0 ] && echo "Windows 起動区画 (ESP): ${P_NODE[ESPI]}  → \\EFI\\${BOOT_ID}\\ を追加"
  echo "Windows       : ${P_NODE[WIN]}  $(gib $(( P_END[WIN]-P_START[WIN]+1 )))GiB"
  [ $SHRINK = 1 ] && echo "  └ 縮小後     : $(gib $(( NEW_WIN_END-P_START[WIN]+1 )))GiB (ntfsresize)"
  echo "★ BadaVMPro    : 新規 ext4  セクタ ${BADA_S}-${BADA_E}  $(gib $(( BADA_E-BADA_S+1 )))GiB"
  echo "Linux         : ${P_NODE[LIN]}  $(gib $(( P_END[LIN]-P_START[LIN]+1 )))GiB  (変更なし)"
  echo "--- 予定のレイアウト (ディスク先頭から) ---"
  {
    for ((k=0;k<N;k++)); do
      e=${P_END[k]}; [ $SHRINK = 1 ] && [ $k -eq $WIN ] && e=$NEW_WIN_END
      printf '%012d  %-22s %-6s %8sGiB\n' "${P_START[k]}" "${P_NODE[k]}" "${P_FS[k]:-?}" "$(gib $(( e-P_START[k]+1 )))"
    done
    printf '%012d  %-22s %-6s %8sGiB  ★\n' "$BADA_S" "(新規)BadaVMPro" "ext4" "$(gib $(( BADA_E-BADA_S+1 )))"
  } | sort | cut -c15- | sed 's/^/  /'
} >&2
[ "$PLAN_ONLY" = "1" ] && { echo "PLAN_ONLY=1: ディスクは変更していません" >&2; exit 0; }

# ---------------------------------------------------------------------------
# 5. 実行
# ---------------------------------------------------------------------------
[ -b "$DISK" ] || fail "$DISK はブロックデバイスではありません"
SQUASH=""
for c in /cdrom/casper/filesystem.squashfs /run/live/medium/casper/filesystem.squashfs /isodevice/casper/filesystem.squashfs; do
  [ -f "$c" ] && { SQUASH="$c"; break; }
done
[ -n "$SQUASH" ] || fail "ライブシステム (filesystem.squashfs) が見つかりません"

emit 3 "対象ディスクのパーティションをアンマウント中"
umount -R "$MNT" 2>/dev/null || true
for p in $(lsblk -ln -o NAME "$DISK" | tail -n +2); do umount "/dev/$p" 2>/dev/null || true; done

if [ $SHRINK = 1 ]; then
  W="${P_NODE[WIN]}"
  emit 6 "Windows (NTFS) を検査中 — 高速スタートアップ/休止状態は無効にしておいてください"
  ntfsresize --info --force --no-action "$W" >/dev/null 2>&1 || true
  NEW_BYTES=$(( (NEW_WIN_END - P_START[WIN] + 1) * SECT ))
  ntfsresize --no-action --size "$NEW_BYTES" "$W" >&2 \
    || fail "Windows を縮小できません (chkdsk / 高速スタートアップ無効化 / BitLocker 解除が必要な場合があります)"
  emit 10 "Windows (NTFS) を縮小中…"
  ntfsresize --force --size "$NEW_BYTES" "$W" <<< "y" >&2 || fail "ntfsresize に失敗"
  # パーティション表のエントリも縮める (開始位置はそのまま)
  WNUM="$(echo "$W" | grep -o '[0-9]*$')"
  echo ",$(( NEW_WIN_END - P_START[WIN] + 1 ))" | sfdisk --no-reread -N "$WNUM" "$DISK" >&2 \
    || fail "Windows パーティションの縮小 (sfdisk) に失敗"
  partprobe "$DISK" 2>/dev/null || true; sleep 1
fi

emit 14 "Windows と Linux の間に BadaVMPro パーティションを作成中"
if [ "$LABEL" = "gpt" ]; then
  sgdisk -n "0:${BADA_S}:${BADA_E}" -t 0:8300 -c "0:${BOOT_ID}" "$DISK" >&2 \
    || fail "sgdisk でパーティションを作成できません"
else
  echo "${BADA_S},$(( BADA_E - BADA_S + 1 )),83" | sfdisk --no-reread --append "$DISK" >&2 \
    || fail "MBR に空きスロットがありません (基本パーティションは 4 つまで)"
fi
partprobe "$DISK" 2>/dev/null || true; udevadm settle 2>/dev/null || true; sleep 2

BADA_DEV="$(sfdisk -J "$DISK" | python3 -c '
import json,sys
s=int(sys.argv[1])
for p in json.load(sys.stdin)["partitiontable"]["partitions"]:
    if int(p["start"])==s: print(p["node"])' "$BADA_S")"
[ -b "$BADA_DEV" ] || fail "作成した BadaVMPro パーティションのデバイスが見つかりません"

emit 18 "BadaVMPro パーティションをフォーマット中 (ext4: $BADA_DEV)"
mkfs.ext4 -F -L BADAVMPRO "$BADA_DEV" >/dev/null
mkdir -p "$MNT"; mount "$BADA_DEV" "$MNT"

emit 22 "システムをコピー中… (数分かかります)"
unsquashfs -f -d "$MNT" "$SQUASH" >/dev/null

if [ "$FW" = "uefi" ]; then
  ESP_DEV="${P_NODE[ESPI]}"
  emit 70 "Windows の起動パーティション ($ESP_DEV) を退避中"
  mkdir -p "$MNT/boot/efi"; mount "$ESP_DEV" "$MNT/boot/efi"
  mkdir -p "$MNT/var/backups"
  tar -C "$MNT/boot/efi" -cf "$MNT/var/backups/esp-before-badavmpro.tar" . 2>/dev/null || true
  [ -f "$MNT/boot/efi/EFI/Microsoft/Boot/bootmgfw.efi" ] || log "注意: ESP に Windows Boot Manager が見つかりません"
fi

emit 74 "システム設定を書き込み中"
ROOT_UUID="$(blkid -s UUID -o value "$BADA_DEV")"
{
  echo "# /etc/fstab — Bada VM Pro OS (Windows / BadaVMPro / Linux トリプルブート)"
  echo "UUID=${ROOT_UUID} / ext4 defaults,noatime,errors=remount-ro 0 1"
  [ "$FW" = "uefi" ] && echo "UUID=$(blkid -s UUID -o value "$ESP_DEV") /boot/efi vfat umask=0077 0 1"
} > "$MNT/etc/fstab"
echo "$HOST" > "$MNT/etc/hostname"
printf '127.0.0.1\tlocalhost\n127.0.1.1\t%s\n' "$HOST" > "$MNT/etc/hosts"

# GRUB: Windows / Linux を自動検出 (os-prober) + 明示的なチェーンロード項目
cat > "$MNT/etc/default/grub" <<'EOF'
GRUB_DEFAULT=0
GRUB_TIMEOUT_STYLE=menu
GRUB_TIMEOUT=10
GRUB_DISTRIBUTOR="Bada VM Pro"
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX=""
GRUB_DISABLE_OS_PROBER=false
EOF
install -Dm755 /usr/local/lib/badaos/35_badavmpro_triboot "$MNT/etc/grub.d/35_badavmpro_triboot" 2>/dev/null \
  || log "注意: 35_badavmpro_triboot が見つからないため os-prober のみで Windows/Linux を検出します"

for m in dev dev/pts proc sys run; do mkdir -p "$MNT/$m"; done
mount --bind /dev "$MNT/dev"; mount --bind /dev/pts "$MNT/dev/pts"
mount -t proc none "$MNT/proc"; mount -t sysfs none "$MNT/sys"
mount --bind /run "$MNT/run" 2>/dev/null || true
[ -d /sys/firmware/efi/efivars ] && mount -t efivarfs efivarfs "$MNT/sys/firmware/efi/efivars" 2>/dev/null || true
cp -f /etc/resolv.conf "$MNT/etc/resolv.conf" 2>/dev/null || true

emit 80 "ユーザー ${USER_NAME} を作成中"
chroot "$MNT" /bin/bash -e <<CHROOT
id "${USER_NAME}" >/dev/null 2>&1 || useradd -m -s /bin/bash -G sudo,adm,cdrom,plugdev,netdev,audio,video "${USER_NAME}"
echo "${USER_NAME}:${PASS}" | chpasswd
mkdir -p /etc/lightdm/lightdm.conf.d
printf '[Seat:*]\nautologin-user=%s\nautologin-user-timeout=0\nuser-session=w9wm\ngreeter-session=lightdm-gtk-greeter\n' "${USER_NAME}" > /etc/lightdm/lightdm.conf.d/50-badaos.conf
apt-get -y purge casper 2>/dev/null || true
systemctl enable NetworkManager 2>/dev/null || true
systemctl enable lightdm 2>/dev/null || true
CHROOT

emit 88 "Windows の起動パーティションに Bada VM Pro ブートローダを作成中"
if [ "$FW" = "uefi" ]; then
  # \EFI\BadaVMPro\ に GRUB (署名済み shim があればそれも) を置く。
  # --removable は使わない (\EFI\BOOT\BOOTX64.EFI = Windows のフォールバックを守る)
  chroot "$MNT" grub-install --target=x86_64-efi --efi-directory=/boot/efi \
      --bootloader-id="$BOOT_ID" --recheck --no-nvram >&2 \
    || fail "grub-install (x86_64-efi) に失敗"
  LOADER='\EFI\'"$BOOT_ID"'\grubx64.efi'
  [ -f "$MNT/boot/efi/EFI/$BOOT_ID/shimx64.efi" ] && LOADER='\EFI\'"$BOOT_ID"'\shimx64.efi'
  # 起動メニュー「Bada VM Pro」を UEFI NVRAM に登録し、起動順の先頭に
  if command -v efibootmgr >/dev/null 2>&1 && [ -d /sys/firmware/efi/efivars ]; then
    for n in $(efibootmgr | grep -E "^Boot[0-9A-Fa-f]{4}\*? ${BOOT_LABEL}([[:space:]]|\$)" | cut -c5-8); do
      efibootmgr -q -b "$n" -B || true     # 古い同名エントリを掃除
    done
    ESPNUM="$(echo "$ESP_DEV" | grep -o '[0-9]*$')"
    efibootmgr -q -c -d "$DISK" -p "$ESPNUM" -L "$BOOT_LABEL" -l "$LOADER" >&2 \
      || log "注意: UEFI 起動エントリを登録できませんでした (ファームウェアの起動メニューで \\EFI\\$BOOT_ID を選んでください)"
  fi
  # Windows 側からも登録できるよう、手順バッチを ESP に置く
  install -Dm644 /usr/local/lib/badaos/add-badavmpro-bootentry.bat \
    "$MNT/boot/efi/EFI/$BOOT_ID/add-badavmpro-bootentry.bat" 2>/dev/null || true
else
  chroot "$MNT" grub-install --target=i386-pc --recheck "$DISK" >&2 || fail "grub-install (i386-pc) に失敗"
fi
emit 93 "起動メニュー (Bada VM Pro / Windows / Linux) を生成中"
chroot "$MNT" update-grub >&2 2>/dev/null || chroot "$MNT" grub-mkconfig -o /boot/grub/grub.cfg >&2

emit 97 "後始末"
sync
umount -R "$MNT" 2>/dev/null || umount -lR "$MNT" 2>/dev/null || true
emit 100 "トリプルブートのインストール完了 (Windows / Bada VM Pro / Linux)"
