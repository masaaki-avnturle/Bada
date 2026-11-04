#!/bin/bash
# =============================================================================
# badaos-legacy-boot DISK MNT — Legacy BIOS + MBR ディスク用に、Bada VM Pro の GRUB を
#   「専用 FAT (BADAVMBOOT) 側」に設置する。ディスク先頭 (MBR) は書き換えない。
#
#   前提: MNT に BADAVMPRO (/) と BADAVMBOOT (/boot/efi) がマウント済み、
#         MNT/dev, /proc, /sys が bind 済み (chroot できる状態)。
#
#   1. grub-install --no-bootsector で GRUB モジュールを FAT の /grub に置く
#   2. GRUB の core.img を自前で作る: 起動時に BADAVMBOOT を
#        UUID で探す → 見つからなければ目印ファイル /grub/badavmpro.id で探す
#      (ディスク番号 hd0/hd1 に依存しない。インストール時に USB が刺さっていても OK)
#   3. core.img を FAT 直前の未使用 1MiB に、boot.img を FAT の VBR
#      (論理区画の時は拡張区画の先頭 EBR) に書く (BPB・区画表・署名は保持)
#   4. その区画をアクティブにする → Windows の MBR 起動コードがここを起動
# =============================================================================
set -euo pipefail
DISK="${1:?DISK}"; MNT="${2:?MNT}"
fail(){ echo "ERROR: $*" >&2; exit 1; }
pnum(){ echo "$1" | grep -o '[0-9]*$'; }

BOOT_DEV="$(findmnt -no SOURCE "$MNT/boot/efi")" || fail "$MNT/boot/efi がマウントされていません"
BOOT_UUID="$(blkid -s UUID -o value "$BOOT_DEV")"
[ -n "$BOOT_UUID" ] || fail "BADAVMBOOT の UUID を読めません"
GEOM="$(sfdisk -J "$DISK" | python3 -c '
import json, sys
t = json.load(sys.stdin)["partitiontable"]; dev = sys.argv[1]
b = [p for p in t["partitions"] if p["node"] == dev][0]
x = [p for p in t["partitions"] if str(p["type"]).lower() in ("5", "f", "85")]
print(t.get("sectorsize", 512), b["start"], x[0]["start"] if x else 0)' "$BOOT_DEV")"
read -r SECT BOOT_S X_S <<< "$GEOM"
[ -n "$BOOT_S" ] || fail "BADAVMBOOT の位置を読めません"
ALIGN=$(( 1048576 / SECT ))
if [ "$(pnum "$BOOT_DEV")" -ge 5 ]; then
  LOGICAL=1; VBR_LBA=$X_S
  ACT_NUM="$(sfdisk -J "$DISK" | python3 -c '
import json, re, sys
for p in json.load(sys.stdin)["partitiontable"]["partitions"]:
    if str(p["type"]).lower() in ("5", "f", "85"): print(re.search(r"(\d+)$", p["node"]).group(1))')"
else
  LOGICAL=0; VBR_LBA=$BOOT_S; ACT_NUM="$(pnum "$BOOT_DEV")"
fi

BACK="$MNT/boot/efi/grub"; mkdir -p "$BACK"
dd if="$DISK" of="$BACK/mbr-before-badavmpro.bin" bs=512 count=1 2>/dev/null || true
echo "Bada VM Pro boot partition" > "$BACK/badavmpro.id"

# 1. モジュール (i386-pc) を FAT の /grub に
chroot "$MNT" grub-install --target=i386-pc --boot-directory=/boot/efi --no-bootsector --recheck "$DISK" >&2 \
  || fail "grub-install (i386-pc, --no-bootsector) に失敗"

# 2. ディスク番号に依存しない core.img
cat > "$MNT/tmp/badaos-early.cfg" <<EOF
search --no-floppy --fs-uuid --set=root $BOOT_UUID
if [ -z "\$root" ]; then search --no-floppy --file --set=root /grub/badavmpro.id; fi
set prefix=(\$root)/grub
EOF
chroot "$MNT" grub-mkimage -O i386-pc -d /usr/lib/grub/i386-pc -o /tmp/badaos-core.img \
  -c /tmp/badaos-early.cfg -p /grub \
  biosdisk part_msdos part_gpt fat search search_fs_uuid search_fs_file test echo normal configfile \
  || fail "grub-mkimage (core.img) に失敗"
TMPG="$(mktemp -d)"
cp "$MNT/tmp/badaos-core.img" "$TMPG/core.img"; cp "$MNT/usr/lib/grub/i386-pc/boot.img" "$TMPG/boot.img"
cp "$MNT/tmp/badaos-early.cfg" "$BACK/badaos-early.cfg"

# 3. FAT を外して VBR/EBR と core.img を書く
sync; umount "$MNT/boot/efi"
python3 - "$DISK" "$TMPG/boot.img" "$TMPG/core.img" "$VBR_LBA" "$SECT" "$(( BOOT_S - ALIGN ))" "$(( BOOT_S - 1 ))" "$X_S" "$LOGICAL" <<'PY' >&2 \
  || { mount "$BOOT_DEV" "$MNT/boot/efi"; fail "GRUB 起動コードの書き込みに失敗"; }
import json, struct, subprocess, sys
disk, bootimg, coreimg = sys.argv[1:4]
vbr, sect, reg_s, reg_e, xs, logical = map(int, sys.argv[4:10])
busy = set()
if logical:   # 拡張区画の EBR チェーン (避ける)
    with open(disk, 'rb') as f:
        e = xs
        for _ in range(128):
            busy.add(e); f.seek(e * sect); b = f.read(512)
            if b[0x1d2] not in (0x05, 0x0f, 0x85): break
            nxt = struct.unpack_from('<I', b, 0x1d6)[0]
            if nxt == 0: break
            e = xs + nxt
for p in json.loads(subprocess.check_output(['sfdisk', '-J', disk]))['partitiontable']['partitions']:
    if str(p['type']).lower() in ('5', 'f', '85'): continue
    s, n = int(p['start']), int(p['size'])
    for x in range(max(s, reg_s), min(s + n, reg_e + 1)): busy.add(x)   # 既存区画とも重ねない
best = (0, -1); run = None
for x in range(reg_s, reg_e + 2):
    free = x <= reg_e and x not in busy
    if free and run is None: run = x
    if not free and run is not None:
        if x - run > best[1] - best[0] + 1: best = (run, x - 1)
        run = None
emb, room = best[0], best[1] - best[0] + 1
core = bytearray(open(coreimg, 'rb').read())
n = (len(core) + 511) // 512
assert n <= room, f"core.img ({n} sectors) が FAT 直前の空き ({room} sectors) に入りません"
core += b'\0' * (n * 512 - len(core))
struct.pack_into('<QH', core, 0x200 - 12, emb + 1, n - 1)        # diskboot の blocklist (絶対 LBA)
boot = open(bootimg, 'rb').read()
with open(disk, 'r+b') as f:
    f.seek(vbr * sect); old = bytearray(f.read(512))
    open(coreimg + '.vbr-before', 'wb').write(old)
    new = bytearray(old)
    new[0:3] = boot[0:3]                     # jmp (FAT の BPB 0x03-0x59 は保持)
    new[0x5a:0x1b8] = boot[0x5a:0x1b8]       # 起動コード (区画表 0x1be- は保持)
    struct.pack_into('<Q', new, 0x5c, emb)   # kernel_sector = core.img の先頭
    new[0x1fe:0x200] = b'\x55\xaa'
    f.seek(emb * sect); f.write(core)
    f.seek(vbr * sect); f.write(new)
print(f"GRUB: boot.img -> LBA {vbr}, core.img ({n} sectors) -> LBA {emb} (free {room})")
PY
mount "$BOOT_DEV" "$MNT/boot/efi"
cp -f "$TMPG/core.img.vbr-before" "$BACK/vbr-before-badavmpro.bin" 2>/dev/null || true
cp -f "$TMPG/core.img" "$BACK/i386-pc/core-badavmpro.img" 2>/dev/null || true
rm -rf "$TMPG"

# 4. アクティブ区画 (Windows の MBR 起動コードが起動する区画)
sfdisk --activate "$DISK" "$ACT_NUM" >&2 || fail "アクティブ区画の設定に失敗"
echo "Legacy boot: OK (boot code in partition $ACT_NUM, BADAVMBOOT UUID $BOOT_UUID)"
