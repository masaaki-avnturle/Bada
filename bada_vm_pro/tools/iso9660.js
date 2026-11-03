/*
 * iso9660.js — 依存ゼロの ISO 9660 (+ El Torito / isohybrid) ビルダー / パーサー
 *
 * 主な用途は Bada VM Pro 自身が ISO を /mnt/cdrom にマウントするための
 * パーサー (parseIso) と、その単体テスト用の合成 ISO ビルダー (buildIso)。
 * 配布用ライブ CD/USB (BadaVMPro-live.iso) は Rufus の「ISO イメージモード」
 * 対応のため、本物の isolinux を用いる tools/build-iso.sh が生成します
 * (このパーサーはその実物 ISO も読めることをテストで確認)。
 * ISO 9660 Level 1 (8.3 大文字名) + El Torito + isohybrid MBR に対応。
 */
"use strict";

const SECTOR = 2048;

/* ── 数値エンコード ── */
function le16(buf, off, v){ buf[off] = v & 255; buf[off + 1] = (v >> 8) & 255; }
function be16(buf, off, v){ buf[off] = (v >> 8) & 255; buf[off + 1] = v & 255; }
function both16(buf, off, v){ le16(buf, off, v); be16(buf, off + 2, v); }
function le32(buf, off, v){ buf[off] = v & 255; buf[off+1] = (v >>> 8) & 255; buf[off+2] = (v >>> 16) & 255; buf[off+3] = (v >>> 24) & 255; }
function be32(buf, off, v){ buf[off] = (v >>> 24) & 255; buf[off+1] = (v >>> 16) & 255; buf[off+2] = (v >>> 8) & 255; buf[off+3] = v & 255; }
function both32(buf, off, v){ le32(buf, off, v); be32(buf, off + 4, v); }
function ascii(buf, off, str, len, pad){
  pad = pad === undefined ? 0x20 : pad;
  for (let i = 0; i < len; i++) buf[off + i] = i < str.length ? str.charCodeAt(i) & 255 : pad;
}

/* ── 8.3 大文字 ISO 名 ── */
function isoName(name){
  const dot = name.lastIndexOf(".");
  let base = (dot > 0 ? name.slice(0, dot) : name), ext = dot > 0 ? name.slice(dot + 1) : "";
  base = base.toUpperCase().replace(/[^A-Z0-9_]/g, "_").slice(0, 8) || "FILE";
  ext = ext.toUpperCase().replace(/[^A-Z0-9_]/g, "_").slice(0, 3);
  return ext ? base + "." + ext : base;
}

/* ── ディレクトリレコード ── */
function dirRecord(nameBytes, extentLBA, size, flags, date){
  const nameLen = nameBytes.length;
  let len = 33 + nameLen;
  if (len % 2 === 1) len++;
  const r = new Uint8Array(len);
  r[0] = len;
  both32(r, 2, extentLBA);
  both32(r, 10, size);
  r[18] = date.getUTCFullYear() - 1900; r[19] = date.getUTCMonth() + 1; r[20] = date.getUTCDate();
  r[21] = date.getUTCHours(); r[22] = date.getUTCMinutes(); r[23] = date.getUTCSeconds(); r[24] = 0;
  r[25] = flags;
  both16(r, 28, 1);
  r[32] = nameLen;
  r.set(nameBytes, 33);
  return r;
}

/* ── El Torito ブートセクタ (512B): BIOS teletype でバナー表示 → halt ── */
function bootSector(message){
  const img = new Uint8Array(512);
  /* org 0x7C00:
     mov si, 0x7C14 / lodsb / test al,al / jz halt / mov ah,0x0E /
     mov bx,7 / int 0x10 / jmp lodsb / halt: hlt / jmp halt */
  const code = [0xBE, 0x14, 0x7C, 0xAC, 0x84, 0xC0, 0x74, 0x09,
                0xB4, 0x0E, 0xBB, 0x07, 0x00, 0xCD, 0x10, 0xEB,
                0xF2, 0xF4, 0xEB, 0xFD];
  img.set(code, 0);
  const msg = message.replace(/\n/g, "\r\n") + "\0";
  for (let i = 0; i < msg.length && 0x14 + i < 510; i++) img[0x14 + i] = msg.charCodeAt(i) & 255;
  img[510] = 0x55; img[511] = 0xAA;   /* 慣例のブート署名 (no-emulation では必須ではない) */
  return img;
}

/* ── ハイブリッド MBR (LBA 0) ──────────────────────────────────────
 * ISO の先頭 512B (システム領域内 = ISO 9660 が無視する領域) に、
 * ・BIOS teletype でバナー表示 → halt するブートコード
 * ・イメージ全体を覆う 1 パーティションの MBR パーティションテーブル
 * ・0x55AA 署名
 * を置く。これで「isohybrid」ISO になり、Rufus が DD イメージモードで
 * USB に書き込め、USB からも (CD からも) BIOS ブートできる。 */
function hybridMbr(message, total512){
  const mbr = new Uint8Array(512);
  const code = [0xBE, 0x14, 0x7C, 0xAC, 0x84, 0xC0, 0x74, 0x09,
                0xB4, 0x0E, 0xBB, 0x07, 0x00, 0xCD, 0x10, 0xEB,
                0xF2, 0xF4, 0xEB, 0xFD];
  mbr.set(code, 0);
  const msg = message.replace(/\n/g, "\r\n") + "\0";
  for (let i = 0; i < msg.length && 0x14 + i < 440; i++) mbr[0x14 + i] = msg.charCodeAt(i) & 255;
  /* パーティションテーブル (offset 446): 1 エントリ, イメージ全体 (LBA0..) */
  const p = 446;
  mbr[p] = 0x80;                                  /* bootable フラグ */
  mbr[p + 1] = 0x00; mbr[p + 2] = 0x01; mbr[p + 3] = 0x00;  /* 開始 CHS = 0/0/1 */
  mbr[p + 4] = 0x17;                              /* パーティションタイプ (isohybrid 慣例) */
  mbr[p + 5] = 0xFE; mbr[p + 6] = 0xFF; mbr[p + 7] = 0xFF;  /* 終了 CHS = 最大 (LBA 使用の合図) */
  le32(mbr, p + 8, 0);                            /* 開始 LBA = 0 */
  le32(mbr, p + 12, total512 >>> 0);              /* セクタ数 (512B 単位) */
  mbr[510] = 0x55; mbr[511] = 0xAA;
  return mbr;
}

/*
 * buildIso({ volumeId, files: [{name, data(Uint8Array|string)}], bootMessage, hybrid })
 *   → Uint8Array (ISO イメージ)。hybrid !== false なら Rufus 対応の
 *     ハイブリッド ISO (先頭に MBR + パーティションテーブル) を生成。
 */
function buildIso(opts){
  const volumeId = (opts.volumeId || "BADAVMPRO").toUpperCase().slice(0, 32);
  const now = new Date();
  const files = (opts.files || []).map(function(f){
    const data = typeof f.data === "string" ? new TextEncoder().encode(f.data) : f.data;
    return { name: isoName(f.name), data: data };
  });

  /* レイアウト (LBA):
     0-15 システム領域 / 16 PVD / 17 Boot Record VD / 18 終端 VD /
     19 Lパステーブル / 20 Mパステーブル / 21 ルートディレクトリ /
     22 ブートカタログ / 23 ブートイメージ / 24- ファイルデータ */
  const LBA_PVD = 16, LBA_BOOTVD = 17, LBA_TERM = 18,
        LBA_PT_L = 19, LBA_PT_M = 20, LBA_ROOT = 21,
        LBA_BOOTCAT = 22, LBA_BOOTIMG = 23, LBA_DATA = 24;

  let nextLBA = LBA_DATA;
  files.forEach(function(f){
    f.lba = f.data.length ? nextLBA : LBA_DATA;
    nextLBA += Math.max(1, Math.ceil(f.data.length / SECTOR));
  });
  const totalSectors = nextLBA;
  const iso = new Uint8Array(totalSectors * SECTOR);
  function sector(lba){ return lba * SECTOR; }

  /* ── ルートディレクトリ ── */
  {
    const off = sector(LBA_ROOT);
    let p = off;
    const dot = dirRecord(new Uint8Array([0]), LBA_ROOT, SECTOR, 2, now);
    const dotdot = dirRecord(new Uint8Array([1]), LBA_ROOT, SECTOR, 2, now);
    iso.set(dot, p); p += dot.length;
    iso.set(dotdot, p); p += dotdot.length;
    files.forEach(function(f){
      const nb = new TextEncoder().encode(f.name + ";1");
      const rec = dirRecord(nb, f.lba, f.data.length, 0, now);
      if (p + rec.length > off + SECTOR) throw new Error("ルートディレクトリが 1 セクタに収まりません");
      iso.set(rec, p); p += rec.length;
    });
  }

  /* ── パステーブル (ルートのみ) ── */
  const PT_SIZE = 10;
  {
    let o = sector(LBA_PT_L);
    iso[o] = 1; iso[o + 1] = 0; le32(iso, o + 2, LBA_ROOT); le16(iso, o + 6, 1); iso[o + 8] = 0; iso[o + 9] = 0;
    o = sector(LBA_PT_M);
    iso[o] = 1; iso[o + 1] = 0; be32(iso, o + 2, LBA_ROOT); be16(iso, o + 6, 1); iso[o + 8] = 0; iso[o + 9] = 0;
  }

  /* ── PVD (第一ボリューム記述子) ── */
  {
    const o = sector(LBA_PVD);
    iso[o] = 1; ascii(iso, o + 1, "CD001", 5); iso[o + 6] = 1;
    ascii(iso, o + 8, "BADA VM PRO", 32);
    ascii(iso, o + 40, volumeId, 32);
    both32(iso, o + 80, totalSectors);
    both16(iso, o + 120, 1);            /* volume set size */
    both16(iso, o + 124, 1);            /* volume sequence number */
    both16(iso, o + 128, SECTOR);       /* logical block size */
    both32(iso, o + 132, PT_SIZE);      /* path table size */
    le32(iso, o + 140, LBA_PT_L);
    be32(iso, o + 148, LBA_PT_M);
    const rootRec = dirRecord(new Uint8Array([0]), LBA_ROOT, SECTOR, 2, now);
    iso.set(rootRec.subarray(0, 34), o + 156);
    ascii(iso, o + 190, "BADA", 128);
    ascii(iso, o + 318, "MASAAKI-AVNTURLE/BADA", 128);
    ascii(iso, o + 446, "BADA VM PRO BUILD-ISO.JS", 128);
    ascii(iso, o + 574, "BADA VM PRO (W9WM DESKTOP, QUANTUM BADA OS)", 128);
    ascii(iso, o + 702, "", 37); ascii(iso, o + 739, "", 37); ascii(iso, o + 776, "", 37);
    function vdate(off, d){
      const s = d
        ? String(d.getUTCFullYear()).padStart(4, "0") + String(d.getUTCMonth() + 1).padStart(2, "0") +
          String(d.getUTCDate()).padStart(2, "0") + String(d.getUTCHours()).padStart(2, "0") +
          String(d.getUTCMinutes()).padStart(2, "0") + String(d.getUTCSeconds()).padStart(2, "0") + "00"
        : "0000000000000000";
      ascii(iso, off, s, 16, 0x30); iso[off + 16] = 0;
    }
    vdate(o + 813, now); vdate(o + 830, now); vdate(o + 847, null); vdate(o + 864, null);
    iso[o + 881] = 1;
  }

  /* ── Boot Record VD (El Torito) ── */
  {
    const o = sector(LBA_BOOTVD);
    iso[o] = 0; ascii(iso, o + 1, "CD001", 5); iso[o + 6] = 1;
    ascii(iso, o + 7, "EL TORITO SPECIFICATION", 32, 0x00);
    le32(iso, o + 0x47, LBA_BOOTCAT);
  }

  /* ── 終端 VD ── */
  {
    const o = sector(LBA_TERM);
    iso[o] = 255; ascii(iso, o + 1, "CD001", 5); iso[o + 6] = 1;
  }

  /* ── ブートカタログ ── */
  {
    const o = sector(LBA_BOOTCAT);
    iso[o] = 0x01; iso[o + 1] = 0x00;                 /* validation entry, x86 */
    ascii(iso, o + 4, "BADAVMPRO", 24, 0x00);
    iso[o + 30] = 0x55; iso[o + 31] = 0xAA;
    let sum = 0;
    for (let i = 0; i < 32; i += 2) sum = (sum + iso[o + i] + (iso[o + i + 1] << 8)) & 0xffff;
    le16(iso, o + 28, (0x10000 - sum) & 0xffff);      /* 全ワード和 ≡ 0 */
    const e = o + 32;                                  /* initial/default entry */
    iso[e] = 0x88;                                     /* bootable */
    iso[e + 1] = 0x00;                                 /* no emulation */
    le16(iso, e + 2, 0);                               /* load segment (既定 0x7C0) */
    iso[e + 4] = 0;
    le16(iso, e + 6, 4);                               /* 512B 単位で 4 = 2048B */
    le32(iso, e + 8, LBA_BOOTIMG);
  }

  /* ── ブートイメージ ── */
  const bootMsg = opts.bootMessage ||
    "\nBada VM Pro Live CD/USB (w9wm desktop / quantum Bada OS)\n" +
    "This medium carries the Bada VM Pro OS as a data volume.\n" +
    "Open INDEX.HTM from it in any web browser to boot the OS,\n" +
    "or install the native app from github.com/masaaki-avnturle/Bada Releases.\n" +
    "System halted.\n";
  iso.set(bootSector(bootMsg), sector(LBA_BOOTIMG));

  /* ── ファイルデータ ── */
  files.forEach(function(f){ if (f.data.length) iso.set(f.data, sector(f.lba)); });

  /* ── ハイブリッド MBR (Rufus / USB ブート対応) を LBA 0 に ── */
  if (opts.hybrid !== false){
    iso.set(hybridMbr(bootMsg, totalSectors * 4), 0);   /* 2048B → 512B は ×4 */
  }

  return iso;
}

/* ── パーサー: parseIso(Uint8Array) → { volumeId, files: [{name, lba, size, data}] } ── */
function parseIso(iso){
  function rd32le(off){ return (iso[off] | (iso[off+1] << 8) | (iso[off+2] << 16) | (iso[off+3] << 24)) >>> 0; }
  const pvd = 16 * SECTOR;
  if (!(iso[pvd] === 1 && iso[pvd+1] === 0x43 && iso[pvd+2] === 0x44 && iso[pvd+3] === 0x30 && iso[pvd+4] === 0x30 && iso[pvd+5] === 0x31)){
    throw new Error("ISO 9660 ではありません (PVD/CD001 が見つかりません)");
  }
  let volumeId = "";
  for (let i = 0; i < 32; i++) volumeId += String.fromCharCode(iso[pvd + 40 + i]);
  volumeId = volumeId.trim();
  const rootOff = pvd + 156;
  const rootLBA = rd32le(rootOff + 2), rootSize = rd32le(rootOff + 10);
  const files = [];
  function walk(lba, size, prefix){
    let off = lba * SECTOR;
    const end = off + size;
    while (off < end){
      const len = iso[off];
      if (len === 0){                              /* セクタ境界へ */
        off = (Math.floor(off / SECTOR) + 1) * SECTOR;
        continue;
      }
      const flags = iso[off + 25];
      const nameLen = iso[off + 32];
      let name = "";
      for (let i = 0; i < nameLen; i++) name += String.fromCharCode(iso[off + 33 + i]);
      const extent = rd32le(off + 2), fsize = rd32le(off + 10);
      if (!(nameLen === 1 && (name.charCodeAt(0) === 0 || name.charCodeAt(0) === 1))){
        const clean = name.replace(/;1$/, "");
        if (flags & 2) walk(extent, fsize, prefix + clean + "/");
        else files.push({ name: prefix + clean, lba: extent, size: fsize,
                          data: iso.slice(extent * SECTOR, extent * SECTOR + fsize) });
      }
      off += len;
    }
  }
  walk(rootLBA, rootSize, "");
  /* El Torito 情報 (あれば) */
  let bootable = false;
  const bvd = 17 * SECTOR;
  if (iso[bvd] === 0 && iso[bvd+1] === 0x43){
    let id = "";
    for (let i = 0; i < 23; i++) id += String.fromCharCode(iso[bvd + 7 + i]);
    if (id === "EL TORITO SPECIFICATION") bootable = true;
  }
  /* ハイブリッド MBR (isohybrid) 情報 */
  let hybrid = null;
  if (iso[510] === 0x55 && iso[511] === 0xAA){
    const p = 446;
    const type = iso[p + 4];
    const startLBA = rd32le(p + 8), sectors = rd32le(p + 12);
    if (type !== 0 && sectors > 0){
      hybrid = { bootFlag: iso[p], type: type, startLBA: startLBA, sectors: sectors };
    }
  }
  return { volumeId: volumeId, files: files, bootable: bootable, hybrid: hybrid };
}

if (typeof module !== "undefined" && module.exports) module.exports = { buildIso: buildIso, parseIso: parseIso, isoName: isoName, SECTOR: SECTOR };
if (typeof globalThis !== "undefined") globalThis.BadaISO = { buildIso: buildIso, parseIso: parseIso };
