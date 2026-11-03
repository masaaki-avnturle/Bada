#!/bin/bash
# =============================================================================
# badaos-triboot-core.sh — Windows / Bada VM Pro / Linux の「トリプルブート」導入本体
#
#   ディスク構成 (Windows と後ろの Linux の「真ん中」に Bada VM Pro を入れる):
#
#   ┌─────┬──────────────┬───────────────────┬───────────────────┬──────────────┐
#   │(ESP)│ Windows (C:) │ ★ BADAVMBOOT ★    │ ★ BADAVMPRO ★     │ Linux (ext4) │
#   │     │    NTFS      │ FAT32 512MiB      │ ext4 (OS 本体)    │  既存のまま  │
#   │     │              │ Bada VM Pro 専用  │ Windows の下の    │              │
#   │     │              │ ブートローダ      │ 空き領域に作成    │              │
#   └─────┴──────────────┴───────────────────┴───────────────────┴──────────────┘
#     ↑ Windows の起動パーティション (ESP) と MBR の Windows 起動コードは
#       UEFI ではいっさい変更しない。Bada VM Pro のブートローダ (GRUB の EFI
#       ローダ・モジュール・grub.cfg) はすべて専用 FAT パーティションに入る。
#
#   起動方式:
#     UEFI   … 専用 FAT の \EFI\BadaVMPro\ と \EFI\BOOT\BOOTX64.EFI に GRUB(+shim)。
#              UEFI 起動メニュー「Bada VM Pro」を登録 (専用 FAT を指す)。
#     Legacy … 専用 FAT の /grub に GRUB (i386-pc) を置き、ディスク先頭 (MBR) に
#              GRUB の起動コードを書く。GPT ディスクでは 1MiB の BIOS 起動区画も作る。
#     どちらでも GRUB メニューから Bada VM Pro / Windows / Linux を選べる。
#
#   ・Windows → Linux の順に並んだディスクで、その間の未割り当て領域を使う
#   ・間に空きが無い場合は SHRINK_WINDOWS=1 で Windows(NTFS) の末尾を縮小して空ける
#   ・Windows / Linux の既存パーティションは消さない
#
#   環境変数:
#     TARGET_DISK     対象ディスク (例 /dev/sda, /dev/nvme0n1)          [必須]
#     BADA_SIZE_GB    Bada VM Pro に使う大きさ (GiB, ブート区画込み。既定: 空き全部)
#     SHRINK_WINDOWS  1 なら空きが無い時に Windows を縮小して作る (既定 0)
#     BOOT_MODE       uefi / bios (既定: 起動中のファームウェアから自動判定)
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
MIN_GB=12                  # OS 本体 (ext4) の最小サイズ
BOOT_MIB=512               # 専用ブートローダ FAT の大きさ
BOOT_ID="BadaVMPro"        # \EFI\BadaVMPro\ と UEFI 起動メニュー名
BOOT_LABEL="Bada VM Pro"
MNT="/mnt/badavmpro"

emit(){ [ "$PLAN_ONLY" = "1" ] || printf '%s\n# %s\n' "$1" "$2"; }
fail(){ echo "ERROR: $*" >&2; exit 1; }
log(){ echo "$*" >&2; }

GUID_ESP="C12A7328-F81F-11D2-BA4B-00A0C93EC93B"

# ---------------------------------------------------------------------------
# 1. パーティション表の読み取り (sfdisk -J) と各パーティションのファイルシステム判定
# ---------------------------------------------------------------------------
[ -e "$DISK" ] || fail "$DISK がありません"
JSON="$(sfdisk -J "$DISK" 2>/dev/null)" || fail "$DISK のパーティション表を読めません (GPT/MBR が必要)"

TABLE="$(printf '%s' "$JSON" | python3 -c '
import json,sys
t=json.load(sys.stdin)["partitiontable"]
print("#", t.get("label",""), t.get("sectorsize",512))
for p in t.get("partitions",[]):
    print(p["node"], p["start"], p["size"], str(p.get("type","")).upper(), sep="\t")
')"
LABEL="$(echo "$TABLE" | head -1 | awk '{print $2}')"
SECT="$(echo "$TABLE"  | head -1 | awk '{print $3}')"
PARTS="$(echo "$TABLE" | tail -n +2)"
[ -n "$PARTS" ] || fail "$DISK にパーティションがありません (Windows と Linux が入ったディスクを選んでください)"

fstype(){ blkid -p -o value -s TYPE  -O $(( $1 * SECT )) "$DISK" 2>/dev/null || true; }
fslabel(){ blkid -p -o value -s LABEL -O $(( $1 * SECT )) "$DISK" 2>/dev/null || true; }
pnum(){ echo "$1" | grep -o '[0-9]*$'; }

declare -a P_NODE P_START P_END P_TYPE P_FS
i=0
while IFS=$'\t' read -r node start size type; do
  [ -n "$node" ] || continue
  P_NODE[i]="$node"; P_START[i]="$start"; P_END[i]=$(( start + size - 1 ))
  P_TYPE[i]="$type"; P_FS[i]="$(fstype "$start")"
  i=$((i+1))
done <<< "$PARTS"
N=$i

# ---------------------------------------------------------------------------
# 2. Windows / Linux を見つける
# ---------------------------------------------------------------------------
WIN=-1; LIN=-1; EXT=-1; NPRIM=0
for ((k=0;k<N;k++)); do
  sz=$(( P_END[k] - P_START[k] ))
  [ "$LABEL" = "dos" ] && [ "$(pnum "${P_NODE[k]}")" -le 4 ] && NPRIM=$((NPRIM+1))
  case "${P_TYPE[k]}" in 5|F|85) EXT=$k; continue ;; esac     # MBR 拡張区画
  lb="$(fslabel "${P_START[k]}")"
  case "$lb" in BADAVMPRO|BADAVMBOOT) fail "既に Bada VM Pro のパーティション (${P_NODE[k]}: $lb) があります" ;; esac
  if [ "${P_FS[k]}" = "ntfs" ]; then
    # 最大の NTFS = Windows (C:)。回復/System Reserved (数百 MB) は除外される
    if [ $WIN -lt 0 ] || [ $sz -gt $(( P_END[WIN] - P_START[WIN] )) ]; then WIN=$k; fi
  fi
  case "${P_FS[k]}" in ext4|ext3|ext2|btrfs|xfs)
    if [ $LIN -lt 0 ] || [ $sz -gt $(( P_END[LIN] - P_START[LIN] )) ]; then LIN=$k; fi ;;
  esac
done
[ $WIN -ge 0 ] || fail "Windows (NTFS) パーティションが見つかりません"
[ $LIN -ge 0 ] || fail "Linux (ext4/btrfs/xfs) パーティションが見つかりません"
[ ${P_START[WIN]} -lt ${P_START[LIN]} ] || \
  fail "Linux が Windows より前にあります。Bada VM Pro は「Windows の下・Linux の上」に作るため、Windows → Linux の順のディスクが必要です"

# 起動方式
if [ -n "${BOOT_MODE:-}" ]; then FW="$BOOT_MODE"
elif [ -d /sys/firmware/efi ]; then FW="uefi"
elif [ "$PLAN_ONLY" = "1" ] && [ "$LABEL" = "gpt" ]; then FW="uefi"
else FW="bios"; fi
case "$FW" in uefi|bios) ;; *) fail "BOOT_MODE は uefi か bios" ;; esac
[ "$FW" = "uefi" ] && [ "$LABEL" != "gpt" ] && log "注意: MBR ディスクを UEFI で起動します (多くの PC で可。不可なら Legacy で起動してください)"

# GPT + Legacy は GRUB の埋め込み先として 1MiB の BIOS 起動区画 (EF02) が要る
NEED_BIOSGRUB=0; [ "$FW" = "bios" ] && [ "$LABEL" = "gpt" ] && NEED_BIOSGRUB=1
# MBR は基本区画が 4 つまで。空きが 2 つ以上 → 基本区画 2 つ、
# 1 つだけ (System Reserved + C: + Linux の典型例) → 拡張区画 1 つ + 論理区画 2 つ
USE_EXT=0
if [ "$LABEL" = "dos" ]; then
  [ $EXT -lt 0 ] || fail "MBR の拡張区画が既にあるディスクは未対応です (GParted で基本区画に空きを作ってください)"
  FREE_PRIM=$(( 4 - NPRIM ))
  [ $FREE_PRIM -ge 1 ] || fail "MBR の基本区画が 4 つとも使用中です (1 つ以上の空きが必要)"
  [ $FREE_PRIM -lt 2 ] && USE_EXT=1
fi

# ---------------------------------------------------------------------------
# 3. Windows と Linux の「間」の空き領域を計算 (1MiB 境界)
# ---------------------------------------------------------------------------
ALIGN=$(( 1048576 / SECT ))
GIB=$(( 1073741824 / SECT ))
LO=${P_END[WIN]}; HI=${P_START[LIN]}

# 間の区間から、既存パーティション (回復区画など) が占めていない最大の空きを探す
best_s=0; best_e=-1
cur=$(( LO + 1 ))
for idx in $(for ((k=0;k<N;k++)); do echo "${P_START[k]} $k"; done | sort -n | awk '{print $2}'); do
  [ $idx -eq $EXT ] && continue
  s=${P_START[idx]}; e=${P_END[idx]}
  [ $e -le $LO ] && continue
  [ $s -ge $HI ] && break
  if [ $s -gt $cur ] && [ $(( s - cur )) -gt $(( best_e - best_s + 1 )) ]; then best_s=$cur; best_e=$(( s - 1 )); fi
  [ $(( e + 1 )) -gt $cur ] && cur=$(( e + 1 ))
done
if [ $HI -gt $cur ] && [ $(( HI - cur )) -gt $(( best_e - best_s + 1 )) ]; then best_s=$cur; best_e=$(( HI - 1 )); fi

GAP_S=$(( (best_s + ALIGN - 1) / ALIGN * ALIGN ))
GAP_E=$(( (best_e + 1) / ALIGN * ALIGN - 1 ))
GAP_GB=0; [ $GAP_E -gt $GAP_S ] && GAP_GB=$(( (GAP_E - GAP_S + 1) / GIB ))

WANT=0; [ "$BADA_SIZE_GB" -gt 0 ] 2>/dev/null && WANT=$(( BADA_SIZE_GB * GIB ))
NEED_GB=$(( MIN_GB + 1 ))   # OS 最小 + ブート区画

SHRINK=0
if [ $GAP_GB -lt $NEED_GB ]; then
  if [ "$SHRINK_WINDOWS" = "1" ]; then
    [ $WANT -gt 0 ] || WANT=$(( 40 * GIB ))      # 縮小時の既定 40GiB
    SHRINK=1
    # Windows 末尾を WANT 分だけ縮める → Windows の直下に空きができる
    NEW_WIN_END=$(( (P_END[WIN] + 1 - WANT) / ALIGN * ALIGN - 1 ))
    GAP_S=$(( NEW_WIN_END + 1 )); GAP_E=$(( GAP_S + WANT - 1 ))
    [ $(( NEW_WIN_END - P_START[WIN] )) -gt $(( 30 * GIB )) ] || \
      fail "Windows を縮小すると 30GiB を下回ります。BADA_SIZE_GB を小さくしてください"
  else
    fail "Windows と Linux の間に ${NEED_GB}GiB 以上の空きがありません (現在 ${GAP_GB}GiB)。SHRINK_WINDOWS=1 で Windows を縮小するか、GParted (badaos-partition) で空きを作ってください"
  fi
elif [ $WANT -gt 0 ] && [ $WANT -lt $(( GAP_E - GAP_S + 1 )) ]; then
  GAP_E=$(( GAP_S + WANT / ALIGN * ALIGN - 1 ))
fi

# 空きを分割: [BIOS 起動 1MiB (GPT+Legacy のみ)] [専用ブート FAT] [OS 本体 ext4]
# 論理区画は前に 1MiB (EBR 用) 空ける
cur=$GAP_S; LGAP=0; [ $USE_EXT = 1 ] && LGAP=$ALIGN
cur=$(( cur + LGAP ))
if [ $NEED_BIOSGRUB = 1 ]; then BG_S=$cur; BG_E=$(( cur + ALIGN - 1 )); cur=$(( BG_E + 1 )); fi
BOOT_S=$cur; BOOT_E=$(( cur + BOOT_MIB * ALIGN - 1 )); cur=$(( BOOT_E + 1 + LGAP ))
ROOT_S=$cur; ROOT_E=$GAP_E
[ $(( (ROOT_E - ROOT_S + 1) / GIB )) -ge $MIN_GB ] || fail "OS 本体のパーティションが ${MIN_GB}GiB 未満になります"

# ---------------------------------------------------------------------------
# 4. 予定の表示
# ---------------------------------------------------------------------------
gib(){ awk -v s="$1" -v b="$SECT" 'BEGIN{ if (s*b < 1073741824) printf "%dMiB", s*b/1048576; else printf "%.1fGiB", s*b/1073741824 }'; }
{
  echo "=== Bada VM Pro トリプルブート計画 ==="
  echo "ディスク : $DISK  ($LABEL, ${SECT}B/セクタ)   起動方式: $( [ $FW = uefi ] && echo UEFI || echo Legacy BIOS )"
  echo "Windows  : ${P_NODE[WIN]}  $(gib $(( P_END[WIN]-P_START[WIN]+1 )))$( [ $SHRINK = 1 ] && echo " → 縮小後 $(gib $(( NEW_WIN_END-P_START[WIN]+1 ))) (ntfsresize)")"
  echo "Linux    : ${P_NODE[LIN]}  $(gib $(( P_END[LIN]-P_START[LIN]+1 )))  (変更なし)"
  echo "Windows の起動パーティション/起動コード: $( [ $FW = uefi ] && echo '変更しない' || echo 'MBR 先頭 440B を GRUB に (Windows は GRUB メニューから起動)')"
  echo "--- 予定のレイアウト (ディスク先頭から) ---"
  {
    for ((k=0;k<N;k++)); do
      e=${P_END[k]}; [ $SHRINK = 1 ] && [ $k -eq $WIN ] && e=$NEW_WIN_END
      printf '%012d  %-24s %-6s %9s\n' "${P_START[k]}" "${P_NODE[k]}" "${P_FS[k]:-?}" "$(gib $(( e-P_START[k]+1 )))"
    done
    [ $NEED_BIOSGRUB = 1 ] && printf '%012d  %-24s %-6s %9s  ★ GRUB 埋め込み用\n' "$BG_S" "(新規)BIOS起動" "-" "$(gib $(( BG_E-BG_S+1 )))"
    [ $USE_EXT = 1 ] && printf '%012d  %-24s %-6s %9s  ★ 拡張区画 (中に論理区画 2 つ)\n' "$GAP_S" "(新規)拡張区画" "-" "$(gib $(( GAP_E-GAP_S+1 )))"
    printf '%012d  %-24s %-6s %9s  ★ Bada VM Pro 専用ブートローダ\n' "$BOOT_S" "(新規)BADAVMBOOT" "vfat" "$(gib $(( BOOT_E-BOOT_S+1 )))"
    printf '%012d  %-24s %-6s %9s  ★ Bada VM Pro OS\n' "$ROOT_S" "(新規)BADAVMPRO" "ext4" "$(gib $(( ROOT_E-ROOT_S+1 )))"
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
  NEW_BYTES=$(( (NEW_WIN_END - P_START[WIN] + 1) * SECT ))
  ntfsresize --no-action --size "$NEW_BYTES" "$W" >&2 \
    || fail "Windows を縮小できません (chkdsk / 高速スタートアップ無効化 / BitLocker 解除が必要な場合があります)"
  emit 10 "Windows (NTFS) を縮小中…"
  ntfsresize --force --size "$NEW_BYTES" "$W" <<< "y" >&2 || fail "ntfsresize に失敗"
  echo ",$(( NEW_WIN_END - P_START[WIN] + 1 ))" | sfdisk --no-reread -N "$(pnum "$W")" "$DISK" >&2 \
    || fail "Windows パーティションの縮小 (sfdisk) に失敗"
  partprobe "$DISK" 2>/dev/null || true; sleep 1
fi

emit 14 "Windows の下に Bada VM Pro のパーティションを作成中"
if [ "$LABEL" = "gpt" ]; then
  [ $NEED_BIOSGRUB = 1 ] && { sgdisk -n "0:${BG_S}:${BG_E}" -t 0:EF02 -c "0:BadaVMPro-BIOS" "$DISK" >&2 || fail "BIOS 起動区画の作成に失敗"; }
  # 専用ブート FAT は EFI System 型 (Windows からは隠れる / UEFI から起動できる)
  sgdisk -n "0:${BOOT_S}:${BOOT_E}" -t 0:EF00 -c "0:BadaVMPro-Boot" "$DISK" >&2 || fail "ブート区画の作成に失敗"
  sgdisk -n "0:${ROOT_S}:${ROOT_E}" -t 0:8300 -c "0:BadaVMPro"      "$DISK" >&2 || fail "OS 区画の作成に失敗"
else
  # MBR: ブート FAT は type ef (Windows に隠れる)、OS は 83。アクティブ区画は変えない
  {
    [ $USE_EXT = 1 ] && printf '%s,%s,5\n' "$GAP_S" $(( GAP_E-GAP_S+1 ))
    printf '%s,%s,ef\n%s,%s,83\n' "$BOOT_S" $(( BOOT_E-BOOT_S+1 )) "$ROOT_S" $(( ROOT_E-ROOT_S+1 ))
  } | sfdisk --no-reread --append "$DISK" >&2 || fail "MBR にパーティションを追加できません"
fi
partprobe "$DISK" 2>/dev/null || true; udevadm settle 2>/dev/null || true; sleep 2

node_at(){ sfdisk -J "$DISK" | python3 -c '
import json,sys
s=int(sys.argv[1])
for p in json.load(sys.stdin)["partitiontable"]["partitions"]:
    if int(p["start"])==s: print(p["node"])' "$1"; }
BOOT_DEV="$(node_at "$BOOT_S")"; ROOT_DEV="$(node_at "$ROOT_S")"
[ -b "$BOOT_DEV" ] && [ -b "$ROOT_DEV" ] || fail "作成したパーティションのデバイスが見つかりません ($BOOT_DEV / $ROOT_DEV)"

emit 18 "フォーマット中 (専用ブート FAT32: $BOOT_DEV / OS ext4: $ROOT_DEV)"
mkfs.vfat -F32 -n BADAVMBOOT "$BOOT_DEV" >/dev/null
mkfs.ext4 -F -L BADAVMPRO "$ROOT_DEV" >/dev/null
mkdir -p "$MNT"; mount "$ROOT_DEV" "$MNT"

emit 22 "システムをコピー中… (数分かかります)"
unsquashfs -f -d "$MNT" "$SQUASH" >/dev/null

# 専用ブート FAT を /boot/efi に。GRUB 一式 (/boot/grub) も FAT 上に置く
mkdir -p "$MNT/boot/efi"; mount "$BOOT_DEV" "$MNT/boot/efi"
mkdir -p "$MNT/boot/efi/grub"
rm -rf "$MNT/boot/grub"; ln -s efi/grub "$MNT/boot/grub"

emit 70 "システム設定を書き込み中"
ROOT_UUID="$(blkid -s UUID -o value "$ROOT_DEV")"
BOOT_UUID="$(blkid -s UUID -o value "$BOOT_DEV")"
cat > "$MNT/etc/fstab" <<EOF
# /etc/fstab — Bada VM Pro OS (Windows | BADAVMBOOT | BADAVMPRO | Linux)
UUID=${ROOT_UUID} /         ext4 defaults,noatime,errors=remount-ro 0 1
# Bada VM Pro 専用ブートローダ (FAT32)。/boot/grub -> /boot/efi/grub
UUID=${BOOT_UUID} /boot/efi vfat umask=0077 0 1
EOF
echo "$HOST" > "$MNT/etc/hostname"
printf '127.0.0.1\tlocalhost\n127.0.1.1\t%s\n' "$HOST" > "$MNT/etc/hosts"

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
  || log "注意: 35_badavmpro_triboot が無いため os-prober のみで Windows/Linux を検出します"

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

emit 86 "専用 FAT パーティションに Bada VM Pro ブートローダを作成中"
# (a) UEFI 用: 専用 FAT の \EFI\BadaVMPro\ と \EFI\BOOT\BOOTX64.EFI (この FAT は Bada 専用なので
#     removable パスに置いても Windows には影響しない)。Legacy 起動中でも置いておく
#     (後で UEFI に切り替えても起動できるように)。
EFI_OK=0
if chroot "$MNT" grub-install --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot/efi \
     --bootloader-id="$BOOT_ID" --no-nvram --recheck >&2; then
  chroot "$MNT" grub-install --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot/efi \
     --removable --no-nvram --recheck >&2 || true
  EFI_OK=1
fi
[ "$FW" = "uefi" ] && [ $EFI_OK = 0 ] && fail "grub-install (x86_64-efi) に失敗"
# 署名済み GRUB (shim 経由) が自分のフォルダの grub.cfg を読むので、FAT 上の本設定へ誘導する
for d in "$MNT/boot/efi/EFI/$BOOT_ID" "$MNT/boot/efi/EFI/BOOT"; do
  [ -d "$d" ] && printf 'search --no-floppy --fs-uuid --set=root %s\nset prefix=($root)/grub\nconfigfile $prefix/grub.cfg\n' "$BOOT_UUID" > "$d/grub.cfg"
done

if [ "$FW" = "uefi" ]; then
  LOADER='\EFI\'"$BOOT_ID"'\grubx64.efi'
  [ -f "$MNT/boot/efi/EFI/$BOOT_ID/shimx64.efi" ] && LOADER='\EFI\'"$BOOT_ID"'\shimx64.efi'
  if command -v efibootmgr >/dev/null 2>&1 && [ -d /sys/firmware/efi/efivars ]; then
    for n in $(efibootmgr | grep -E "^Boot[0-9A-Fa-f]{4}\*? ${BOOT_LABEL}([[:space:]]|\$)" | cut -c5-8); do
      efibootmgr -q -b "$n" -B || true
    done
    # 起動メニュー「Bada VM Pro」→ 専用 FAT パーティションのローダ (起動順の先頭に入る)
    efibootmgr -q -c -d "$DISK" -p "$(pnum "$BOOT_DEV")" -L "$BOOT_LABEL" -l "$LOADER" >&2 \
      || log "注意: UEFI 起動エントリを登録できませんでした (起動メニューで BADAVMBOOT を選んでください)"
  fi
else
  # (b) Legacy BIOS 用: GRUB の core をディスク先頭 (MBR 後の隙間 / GPT は BIOS 起動区画) に、
  #     モジュールと grub.cfg は専用 FAT の /grub に置く
  emit 88 "Legacy BIOS 用 GRUB をディスク先頭に設置中 (モジュール/設定は専用 FAT)"
  dd if="$DISK" of="$MNT/boot/efi/grub/mbr-before-badavmpro.bin" bs=512 count=1 2>/dev/null || true
  chroot "$MNT" grub-install --target=i386-pc --boot-directory=/boot/efi --recheck "$DISK" >&2 \
    || fail "grub-install (i386-pc) に失敗"
fi

emit 93 "起動メニュー (Bada VM Pro / Windows / Linux) を生成中"
chroot "$MNT" grub-mkconfig -o /boot/efi/grub/grub.cfg >&2

emit 97 "後始末"
sync
umount -R "$MNT" 2>/dev/null || umount -lR "$MNT" 2>/dev/null || true
emit 100 "トリプルブートのインストール完了 (Windows / Bada VM Pro / Linux)"
