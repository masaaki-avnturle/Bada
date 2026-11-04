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
#     ↑ Windows の起動パーティション (ESP) と、ディスク先頭 (MBR) の Windows の
#       起動コードは変更しない (Windows の「先頭ヘッダ」には書かない)。
#       Bada VM Pro のブートローダはすべて真ん中の専用 FAT パーティション側に入る。
#
#   起動方式:
#     UEFI   … 専用 FAT の \EFI\BadaVMPro\ と \EFI\BOOT\BOOTX64.EFI に GRUB(+shim)。
#              UEFI 起動メニュー「Bada VM Pro」を登録 (専用 FAT を指す)。
#     Legacy (MBR ディスク) … GRUB の起動コードを「専用 FAT パーティションの先頭セクタ
#              (VBR)」に、GRUB 本体 (core.img) を FAT 直前の未使用 1MiB に置き、
#              専用 FAT をアクティブにする。Windows の MBR 起動コードがアクティブ区画
#              = Bada VM Pro のブートローダを起動する (MBR 先頭 440B は書き換えない)。
#              基本区画の空きが 1 つしか無い時は拡張区画の先頭セクタ (EBR) に起動コード
#              を置き、拡張区画をアクティブにする。元に戻す: sfdisk --activate <disk> <元の番号>
#     Legacy (GPT ディスク、Windows では稀) … 1MiB の BIOS 起動区画 + 保護 MBR の起動コード。
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
UBUNTU_SIZE_GB="${UBUNTU_SIZE_GB:-0}"   # Linux が無いディスク: Ubuntu 用に割り当てる大きさ (0 = 残り全部)
UBU_MIN=20                               # Ubuntu 用パーティションの最小 GiB
PLAN_ONLY="${PLAN_ONLY:-0}"
MIN_GB=20                  # OS 本体 (ext4) の最小サイズ (最小構成 約 6GiB + 後から apt で texlive-full 等を入れる余裕)
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
[ -n "$PARTS" ] || fail "$DISK にパーティションがありません (Windows が入ったディスクを選んでください)"
# ディスクの最後の使えるセクタ (Linux が無い時は Windows の後ろ〜ディスク末尾の空きを使う)
if [ -b "$DISK" ]; then TOT512=$(blockdev --getsz "$DISK"); else TOT512=$(( $(stat -c %s "$DISK") / 512 )); fi
DISK_SECTS=$(( TOT512 * 512 / SECT ))
LASTUSABLE=$(( DISK_SECTS - 1 )); [ "$LABEL" = gpt ] && LASTUSABLE=$(( DISK_SECTS - 34 ))

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
# Linux が無い → Windows の後ろの空きを [BADAVMBOOT FAT32][BADAVMPRO][UBUNTU] に割り当てる
NEWLINUX=0
if [ $LIN -lt 0 ]; then NEWLINUX=1
elif [ ${P_START[LIN]} -lt ${P_START[WIN]} ]; then LIN=-1; NEWLINUX=1   # Windows より前の Linux は使わない
fi
[ $NEWLINUX = 1 ] || [ ${P_START[WIN]} -lt ${P_START[LIN]} ] || \
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
# MBR + Legacy は MBR を書き換えず、専用 FAT (または拡張区画) の先頭セクタに起動コードを置く
VBR_MODE=0; [ "$FW" = "bios" ] && [ "$LABEL" = "dos" ] && VBR_MODE=1
USE_EXT=0   # MBR で論理区画を使うか (下の「MBR の作り方」で決める)

# ---------------------------------------------------------------------------
# 3. Windows と Linux の「間」の空き領域を計算 (1MiB 境界)
# ---------------------------------------------------------------------------
ALIGN=$(( 1048576 / SECT ))
GIB=$(( 1073741824 / SECT ))
LO=${P_END[WIN]}
if [ $NEWLINUX = 1 ]; then HI=$(( LASTUSABLE + 1 )); else HI=${P_START[LIN]}; fi

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
# MBR: 空き領域が既存の拡張区画の境界 (先頭の EBR 部分など) にまたがる時は、境界の外側に切り詰める
if [ "$LABEL" = "dos" ] && [ $EXT -ge 0 ]; then
  XS0=${P_START[EXT]}; XE0=${P_END[EXT]}
  if [ $GAP_S -lt $XS0 ] && [ $XS0 -le $GAP_E ]; then GAP_E=$(( XS0 / ALIGN * ALIGN - 1 )); fi
  if [ $GAP_S -le $XE0 ] && [ $XE0 -lt $GAP_E ] && [ $GAP_S -ge $XS0 ]; then GAP_S=$(( (XE0 + ALIGN) / ALIGN * ALIGN )); fi
fi
GAP_GB=0; [ $GAP_E -gt $GAP_S ] && GAP_GB=$(( (GAP_E - GAP_S + 1) / GIB ))

WANT=0; [ "$BADA_SIZE_GB" -gt 0 ] 2>/dev/null && WANT=$(( BADA_SIZE_GB * GIB ))
NEED_GB=$(( MIN_GB + 1 ))   # OS 最小 + ブート区画
[ $NEWLINUX = 1 ] && NEED_GB=$(( NEED_GB + UBU_MIN ))
BADA_WANT=$WANT

SHRINK=0
if [ $GAP_GB -lt $NEED_GB ]; then
  if [ "$SHRINK_WINDOWS" = "1" ]; then
    [ $WANT -gt 0 ] || WANT=$(( 40 * GIB ))      # 縮小時の既定 40GiB
    if [ $NEWLINUX = 1 ]; then                   # Bada + Ubuntu の分をまとめて空ける
      U=$(( UBUNTU_SIZE_GB > 0 ? UBUNTU_SIZE_GB : 40 )); WANT=$(( WANT + U * GIB ))
    fi
    SHRINK=1
    # Windows 末尾を WANT 分だけ縮める → Windows の直下に空きができる
    NEW_WIN_END=$(( (P_END[WIN] + 1 - WANT) / ALIGN * ALIGN - 1 ))
    GAP_S=$(( NEW_WIN_END + 1 )); GAP_E=$(( GAP_S + WANT - 1 ))
    [ $(( NEW_WIN_END - P_START[WIN] )) -gt $(( 30 * GIB )) ] || \
      fail "Windows を縮小すると 30GiB を下回ります。BADA_SIZE_GB を小さくしてください"
  else
    fail "Windows と Linux の間に ${NEED_GB}GiB 以上の空きがありません (現在 ${GAP_GB}GiB)。SHRINK_WINDOWS=1 で Windows を縮小するか、GParted (badaos-partition) で空きを作ってください"
  fi
elif [ $NEWLINUX = 0 ] && [ $WANT -gt 0 ] && [ $WANT -lt $(( GAP_E - GAP_S + 1 )) ]; then
  GAP_E=$(( GAP_S + WANT / ALIGN * ALIGN - 1 ))
fi

# ---------------------------------------------------------------------------
# MBR の作り方 (基本区画が何個使われていても入れられるように)
#   primary … 基本区画の空きが足りる → 基本区画で作る
#   newext  … 空きが 1 つ以上 → 新しい拡張区画を作り、中に論理区画
#   inext   … 空き領域が既存の拡張区画の中 → 論理区画を追加
#   growext … 既存の拡張区画が空き領域の隣 → 拡張区画を広げて論理区画を追加
#   convert … 基本区画が 4 つとも使用中 → 空き領域の隣の Linux/データ区画 (Windows 以外) を
#             論理区画に変え、その番号を拡張区画にする (位置・大きさ・中身はそのまま)
#   Windows の区画・ディスク署名 (label-id) はそのまま。MBR 先頭 440B は書き換えない。
# ---------------------------------------------------------------------------
MBRMODE=""; X_S=0; X_E=0; CONV=-1
prim_between(){ # $1..$2 の間に (拡張区画以外の) 基本区画があるか
  local k; for ((k=0;k<N;k++)); do
    [ $k -eq $EXT ] && continue; [ "$(pnum "${P_NODE[k]}")" -le 4 ] || continue
    [ ${P_START[k]} -gt $1 ] && [ ${P_START[k]} -lt $2 ] && return 0
  done; return 1; }
if [ "$LABEL" = "dos" ]; then
  FREE_PRIM=$(( 4 - NPRIM ))
  NEEDP=$(( 2 + NEWLINUX ))            # BADAVMBOOT + BADAVMPRO (+ UBUNTU)
  if [ $EXT -ge 0 ]; then
    XS=${P_START[EXT]}; XE=${P_END[EXT]}
    if [ $GAP_S -ge $XS ] && [ $GAP_E -le $XE ]; then MBRMODE=inext; X_S=$XS; X_E=$XE
      GAP_E=$(( GAP_E - ALIGN ))                       # 後ろの論理区画の EBR 用に 1MiB 残す
    elif [ $FREE_PRIM -ge $NEEDP ]; then MBRMODE=primary
    elif [ $XS -gt $GAP_E ] && ! prim_between $GAP_E $XS; then MBRMODE=growext; X_S=$GAP_S; X_E=$XE
    elif [ $XE -lt $GAP_S ] && ! prim_between $XE $GAP_S; then MBRMODE=growext; X_S=$XS; X_E=$GAP_E
    else fail "MBR: 拡張区画が空き領域から離れていて、基本区画の空きも足りません (GParted で空き領域を拡張区画の隣に作ってください)"; fi
  elif [ $FREE_PRIM -ge $NEEDP ]; then MBRMODE=primary
  elif [ $FREE_PRIM -ge 1 ]; then MBRMODE=newext; X_S=$GAP_S; X_E=$GAP_E
  else
    # 基本区画 4 つとも使用中: 空き領域のすぐ後ろ (または前) の Windows 以外の区画を論理区画へ
    for ((k=0;k<N;k++)); do
      [ "$(pnum "${P_NODE[k]}")" -le 4 ] || continue
      case "${P_FS[k]}" in ntfs|vfat|"") continue ;; esac            # Windows / ESP / 不明は動かさない
      [ $k -eq $WIN ] && continue
      if [ ${P_START[k]} -gt $GAP_E ] && ! prim_between $GAP_E ${P_START[k]}; then CONV=$k; break; fi
      if [ ${P_END[k]} -lt $GAP_S ] && ! prim_between ${P_END[k]} $GAP_S && \
         ! prim_between $(( P_START[k] - ALIGN )) ${P_START[k]}; then CONV=$k; break; fi
    done
    [ $CONV -ge 0 ] || fail "MBR の基本区画が 4 つとも使用中で、空き領域の隣に論理区画へ変えられる Linux/データ区画がありません"
    MBRMODE=convert
    if [ ${P_START[CONV]} -gt $GAP_E ]; then
      X_S=$GAP_S; X_E=${P_END[CONV]}
      GAP_E=$(( GAP_E - ALIGN ))                       # 変換する区画の EBR 用に 1MiB 残す
    else
      X_S=$(( P_START[CONV] - 1 )); X_E=$GAP_E
    fi
  fi
  [ "$MBRMODE" = primary ] || USE_EXT=1
fi

# 空きを分割: [BIOS 起動 1MiB (GPT+Legacy のみ)] [専用ブート FAT] [OS 本体 ext4]
# 論理区画は前に 1MiB (EBR 用) 空ける
#   VBR_MODE: GRUB 本体 (core.img) を FAT 直前の未使用 1MiB (EMB_S から) に埋め込む
#     拡張区画あり … EBR (GAP_S) の直後 = 最初の論理区画までの隙間
#     基本区画     … 専用 FAT の前に 1MiB の未割り当てを残す
cur=$GAP_S; LGAP=0; [ $USE_EXT = 1 ] && LGAP=$ALIGN
EMB_S=0
if [ $VBR_MODE = 1 ]; then
  if [ $USE_EXT = 1 ]; then EMB_S=-1; else EMB_S=$cur; cur=$(( cur + ALIGN )); fi   # -1: FAT 直前の隙間 (書き込み時に EBR を避けて決める)
fi
cur=$(( cur + LGAP ))
if [ $NEED_BIOSGRUB = 1 ]; then BG_S=$cur; BG_E=$(( cur + ALIGN - 1 )); cur=$(( BG_E + 1 )); fi
BOOT_S=$cur; BOOT_E=$(( cur + BOOT_MIB * ALIGN - 1 )); cur=$(( BOOT_E + 1 + LGAP ))
ROOT_S=$cur; ROOT_E=$GAP_E
UBU_S=0; UBU_E=-1
if [ $NEWLINUX = 1 ]; then
  # 指定があれば BadaVM Pro (ブート込み) をその大きさ、無ければ残りの半分。後ろは Ubuntu
  if [ $BADA_WANT -gt 0 ]; then ROOT_E=$(( (GAP_S + BADA_WANT) / ALIGN * ALIGN - 1 ))
  else ROOT_E=$(( ROOT_S + (GAP_E - ROOT_S + 1) / 2 / ALIGN * ALIGN - 1 )); fi
  [ $ROOT_E -lt $GAP_E ] || fail "Ubuntu 用の空きが残りません。BADA_SIZE_GB を小さくしてください"
  UBU_S=$(( ROOT_E + 1 + LGAP )); UBU_E=$GAP_E
  if [ "$UBUNTU_SIZE_GB" -gt 0 ] 2>/dev/null && [ $(( UBU_S + UBUNTU_SIZE_GB * GIB - 1 )) -lt $UBU_E ]; then
    UBU_E=$(( UBU_S + UBUNTU_SIZE_GB * GIB / ALIGN * ALIGN - 1 )); fi
  [ $(( (UBU_E - UBU_S + 1) / GIB )) -ge $UBU_MIN ] || fail "Ubuntu 用のパーティションが ${UBU_MIN}GiB 未満になります"
fi
[ $(( (ROOT_E - ROOT_S + 1) / GIB )) -ge $MIN_GB ] || fail "OS 本体のパーティションが ${MIN_GB}GiB 未満になります"

# ---------------------------------------------------------------------------
# 4. 予定の表示
# ---------------------------------------------------------------------------
gib(){ awk -v s="$1" -v b="$SECT" 'BEGIN{ if (s*b < 1073741824) printf "%dMiB", s*b/1048576; else printf "%.1fGiB", s*b/1073741824 }'; }
{
  echo "=== Bada VM Pro トリプルブート計画 ==="
  echo "ディスク : $DISK  ($LABEL, ${SECT}B/セクタ)   起動方式: $( [ $FW = uefi ] && echo UEFI || echo Legacy BIOS )"
  echo "Windows  : ${P_NODE[WIN]}  $(gib $(( P_END[WIN]-P_START[WIN]+1 )))$( [ $SHRINK = 1 ] && echo " → 縮小後 $(gib $(( NEW_WIN_END-P_START[WIN]+1 ))) (ntfsresize)")"
  if [ $NEWLINUX = 1 ]; then echo "Linux    : (無し) → 残りを Ubuntu 用 (UBUNTU) に割り当て"
  else echo "Linux    : ${P_NODE[LIN]}  $(gib $(( P_END[LIN]-P_START[LIN]+1 )))  (変更なし)"; fi
  if [ $FW = uefi ]; then echo "Windows の起動パーティション (ESP) / MBR: 変更しない"
  elif [ $VBR_MODE = 1 ]; then
    echo "Windows の MBR 起動コード: 変更しない (Bada VM Pro の起動コードは$( [ $USE_EXT = 1 ] && echo '拡張区画の先頭 (EBR)' || echo '専用 FAT の先頭 (VBR)')、それをアクティブに)"
  else echo "GPT + Legacy: 保護 MBR の起動コードと BIOS 起動区画を使用"; fi
  [ -n "$MBRMODE" ] && [ "$MBRMODE" != primary ] && \
    echo "MBR の作り方: $MBRMODE (論理区画を使用。既存の論理区画の番号が変わることがあります。区画表は事前に保存)"
  echo "--- 予定のレイアウト (ディスク先頭から) ---"
  {
    for ((k=0;k<N;k++)); do
      [ $k -eq $EXT ] && continue      # 拡張区画は下の「拡張区画」行で表示
      e=${P_END[k]}; [ $SHRINK = 1 ] && [ $k -eq $WIN ] && e=$NEW_WIN_END
      printf '%012d  %-24s %-6s %9s\n' "${P_START[k]}" "${P_NODE[k]}" "${P_FS[k]:-?}" "$(gib $(( e-P_START[k]+1 )))"
    done
    [ $NEED_BIOSGRUB = 1 ] && printf '%012d  %-24s %-6s %9s  ★ GRUB 埋め込み用\n' "$BG_S" "(新規)BIOS起動" "-" "$(gib $(( BG_E-BG_S+1 )))"
    [ $VBR_MODE = 1 ] && [ $USE_EXT = 0 ] && printf '%012d  %-24s %-6s %9s  ★ GRUB 本体 (未割り当て)\n' "$EMB_S" "(新規)GRUB 埋め込み" "-" "1MiB"
    case "$MBRMODE" in
      newext)  printf '%012d  %-24s %-6s %9s  ★ 拡張区画 (中に論理区画)\n' "$X_S" "(新規)拡張区画" "-" "$(gib $(( X_E-X_S+1 )))" ;;
      growext) printf '%012d  %-24s %-6s %9s  ★ 既存の拡張区画を広げる\n' "$X_S" "(拡張)拡張区画" "-" "$(gib $(( X_E-X_S+1 )))" ;;
      inext)   printf '%012d  %-24s %-6s %9s  ★ 既存の拡張区画の中に追加\n' "$X_S" "(既存)拡張区画" "-" "$(gib $(( X_E-X_S+1 )))" ;;
      convert) printf '%012d  %-24s %-6s %9s  ★ 拡張区画 (%s を論理区画へ)\n' "$X_S" "(新規)拡張区画" "-" "$(gib $(( X_E-X_S+1 )))" "${P_NODE[CONV]}" ;;
    esac
    printf '%012d  %-24s %-6s %9s  ★ Bada VM Pro 専用ブートローダ\n' "$BOOT_S" "(新規)BADAVMBOOT" "vfat" "$(gib $(( BOOT_E-BOOT_S+1 )))"
    printf '%012d  %-24s %-6s %9s  ★ Bada VM Pro OS\n' "$ROOT_S" "(新規)BADAVMPRO" "ext4" "$(gib $(( ROOT_E-ROOT_S+1 )))"
    if [ $NEWLINUX = 1 ]; then printf '%012d  %-24s %-6s %9s  ★ Ubuntu 用 (空き)\n' "$UBU_S" "(新規)UBUNTU" "ext4" "$(gib $(( UBU_E-UBU_S+1 )))"; fi
  } | sort | cut -c15- | sed 's/^/  /'
} >&2
[ "$PLAN_ONLY" = "1" ] && { echo "PLAN_ONLY=1: ディスクは変更していません" >&2; exit 0; }

# ---------------------------------------------------------------------------
# 5. 実行
# ---------------------------------------------------------------------------
[ -b "$DISK" ] || fail "$DISK はブロックデバイスではありません"
SQUASH=""   # ライブメディアの casper ディレクトリ (squashfs は複数レイヤ)
for c in /cdrom/casper /run/live/medium/casper /isodevice/casper; do
  [ -f "$c/filesystem.squashfs" ] && { SQUASH="$c"; break; }
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
  [ $NEWLINUX = 1 ] && { sgdisk -n "0:${UBU_S}:${UBU_E}" -t 0:8300 -c "0:Ubuntu" "$DISK" >&2 || fail "Ubuntu 区画の作成に失敗"; }
else
  # MBR: ブート FAT は type ef (Windows に隠れる)、OS は 83。アクティブ区画は変えない
  sfdisk --dump "$DISK" > /tmp/badaos-ptable-before.sfdisk 2>/dev/null || true
  if [ "$MBRMODE" = primary ]; then
    {
      printf '%s,%s,ef\n%s,%s,83\n' "$BOOT_S" $(( BOOT_E-BOOT_S+1 )) "$ROOT_S" $(( ROOT_E-ROOT_S+1 ))
      if [ $NEWLINUX = 1 ]; then printf '%s,%s,83\n' "$UBU_S" $(( UBU_E-UBU_S+1 )); fi
    } | sfdisk --no-reread --append "$DISK" >&2 || fail "MBR にパーティションを追加できません"
  else
    # 区画表を丸ごと組み直す: 既存の基本区画 (番号・位置) はそのまま、拡張区画を作る/広げる、
    # 論理区画 = 既存の論理区画 + 変換した区画 + BADAVMBOOT/BADAVMPRO/UBUNTU を位置順に
    NEWP="${BOOT_S}:$(( BOOT_E-BOOT_S+1 )):ef ${ROOT_S}:$(( ROOT_E-ROOT_S+1 )):83"
    [ $NEWLINUX = 1 ] && NEWP="$NEWP ${UBU_S}:$(( UBU_E-UBU_S+1 )):83"
    CONV_START=0; [ $CONV -ge 0 ] && CONV_START=${P_START[CONV]}
    sfdisk -J "$DISK" | python3 -c '
import json, re, sys
mode, xs, xe, conv_start = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
newp = [tuple(x.split(":")) for x in sys.argv[5].split()]
t = json.load(sys.stdin)["partitiontable"]
parts = t.get("partitions", [])
num = lambda p: int(re.search(r"(\d+)$", p["node"]).group(1))
prefix = re.sub(r"\d+$", "", parts[0]["node"])
EXT = {"5", "f", "85"}
prim = {num(p): p for p in parts if num(p) <= 4}
logi = [p for p in parts if num(p) >= 5]
xnum = None
for n, p in list(prim.items()):
    if str(p["type"]).lower() in EXT: xnum = n
    if mode == "convert" and int(p["start"]) == conv_start:
        logi.append(p); xnum = n
if mode == "newext":
    xnum = min(n for n in range(1, 5) if n not in prim)
out = ["label: dos"]
if t.get("id"): out.append("label-id: %s" % t["id"])
out += ["unit: sectors", ""]
for n in range(1, 5):
    if n == xnum:
        out.append("%s%d : start=%d, size=%d, type=5, bootable" % (prefix, n, xs, xe - xs + 1))
    elif n in prim:
        p = prim[n]
        out.append("%s%d : start=%s, size=%s, type=%s" % (prefix, n, p["start"], p["size"], p["type"]))
L = [(int(p["start"]), int(p["size"]), str(p["type"])) for p in logi]
L += [(int(a), int(b), c) for a, b, c in newp]
for i, (st, sz, ty) in enumerate(sorted(L)):
    out.append("%s%d : start=%d, size=%d, type=%s" % (prefix, 5 + i, st, sz, ty))
print("\n".join(out))' "$MBRMODE" "$X_S" "$X_E" "$CONV_START" "$NEWP" > /tmp/badaos-ptable-new.sfdisk \
      || fail "新しい区画表を作れません"
    cat /tmp/badaos-ptable-new.sfdisk >&2
    sfdisk --no-reread --force "$DISK" < /tmp/badaos-ptable-new.sfdisk >&2 || fail "MBR 区画表の書き込みに失敗 (元に戻す: sfdisk $DISK < /tmp/badaos-ptable-before.sfdisk)"
  fi
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
if [ $NEWLINUX = 1 ]; then
  UBU_DEV="$(node_at "$UBU_S")"; [ -b "$UBU_DEV" ] || fail "Ubuntu 区画のデバイスが見つかりません"
  mkfs.ext4 -F -L UBUNTU "$UBU_DEV" >/dev/null
fi
mkdir -p "$MNT"; mount "$ROOT_DEV" "$MNT"

emit 22 "システムをコピー中… (数分かかります)"
for sq in "$SQUASH"/filesystem.squashfs "$SQUASH"/filesystem-*.squashfs; do
  if [ -f "$sq" ]; then unsquashfs -f -d "$MNT" "$sq" >/dev/null || fail "$sq の展開に失敗"; fi
done

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
GRUB_CMDLINE_LINUX_DEFAULT="nomodeset"
GRUB_CMDLINE_LINUX=""
GRUB_DISABLE_OS_PROBER=false
GRUB_DISABLE_RECOVERY=false
EOF
# 既定は nomodeset (GPU ドライバを使わない汎用表示) で、どの PC でも通常起動できるようにする。
# GPU ドライバで高速表示する起動項目は 35_badavmpro_triboot が別に追加する。
install -Dm755 /usr/local/lib/badaos/35_badavmpro_triboot "$MNT/etc/grub.d/35_badavmpro_triboot" 2>/dev/null \
  || log "注意: 35_badavmpro_triboot が無いため os-prober のみで Windows/Linux を検出します"

for m in dev dev/pts proc sys run; do mkdir -p "$MNT/$m"; done
mount --bind /dev "$MNT/dev"; mount --bind /dev/pts "$MNT/dev/pts"
mount -t proc none "$MNT/proc"; mount -t sysfs none "$MNT/sys"
mount --bind /run "$MNT/run" 2>/dev/null || true
[ -d /sys/firmware/efi/efivars ] && mount -t efivarfs efivarfs "$MNT/sys/firmware/efi/efivars" 2>/dev/null || true
cp -f /etc/resolv.conf "$MNT/etc/resolv.conf" 2>/dev/null || true

emit 80 "ユーザー ${USER_NAME} を作成中"
chroot "$MNT" /bin/bash -e >&2 <<CHROOT
# 存在するグループだけに入れる (lpadmin=プリンタ管理, scanner=スキャナ)
GRPS=\$(for g in sudo adm cdrom dip plugdev netdev audio video lpadmin scanner; do getent group \$g >/dev/null && printf '%s,' \$g; done; true)
id "${USER_NAME}" >/dev/null 2>&1 || useradd -m -s /bin/bash -G "\${GRPS%,}" "${USER_NAME}"
echo "${USER_NAME}:${PASS}" | chpasswd
mkdir -p /etc/lightdm/lightdm.conf.d
printf '[Seat:*]\nautologin-user=%s\nautologin-user-timeout=0\nuser-session=badaos-w9wm\ngreeter-session=lightdm-gtk-greeter\n' "${USER_NAME}" > /etc/lightdm/lightdm.conf.d/50-badaos.conf
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
elif [ $VBR_MODE = 1 ]; then
  # (b) Legacy + MBR: ディスク先頭 (MBR) は書き換えない。GRUB は専用 FAT 側に設置し、
  #     起動時に BADAVMBOOT を UUID で探す core.img を使う (ディスク番号に依存しない)
  emit 88 "Legacy BIOS 用 GRUB を専用 FAT パーティション側に設置中 (MBR は変更しない)"
  cp -f /tmp/badaos-ptable-before.sfdisk "$MNT/boot/efi/grub/ptable-before-badavmpro.sfdisk" 2>/dev/null || true
  bash /usr/local/lib/badaos/badaos-legacy-boot "$DISK" "$MNT" >&2 || fail "Legacy 起動の設定に失敗"
else
  # (c) Legacy + GPT: GRUB の core を BIOS 起動区画に、モジュールと grub.cfg は専用 FAT の /grub に
  emit 88 "Legacy BIOS 用 GRUB をディスク先頭に設置中 (モジュール/設定は専用 FAT)"
  dd if="$DISK" of="$MNT/boot/efi/grub/mbr-before-badavmpro.bin" bs=512 count=1 2>/dev/null || true
  chroot "$MNT" grub-install --target=i386-pc --boot-directory=/boot/efi --recheck "$DISK" >&2 \
    || fail "grub-install (i386-pc) に失敗"
fi

emit 93 "起動メニュー (Bada VM Pro / Windows / Linux) を生成中"
# root=UUID=... にするため /dev/disk/by-uuid を用意 (udev が無い環境でも)。
# これが無いと grub-mkconfig が root=/dev/sdb6 のようなデバイス名を書き、
# USB を抜いて起動すると「/dev/sdb6 does not exist」で止まる
for d in "$ROOT_DEV" "$BOOT_DEV"; do
  u="$(blkid -s UUID -o value "$d" 2>/dev/null || true)"
  [ -n "$u" ] && { mkdir -p /dev/disk/by-uuid; ln -sf "$d" "/dev/disk/by-uuid/$u"; }
done
chroot "$MNT" grub-mkconfig -o /boot/efi/grub/grub.cfg >&2
grep -q 'root=UUID=' "$MNT/boot/efi/grub/grub.cfg" || fail "起動メニューに root=UUID= がありません"

emit 97 "後始末"
sync
umount -R "$MNT" 2>/dev/null || umount -lR "$MNT" 2>/dev/null || true
emit 100 "トリプルブートのインストール完了 (Windows / Bada VM Pro / Linux)"
