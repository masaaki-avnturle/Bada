#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf2text.py — BadaGPT PDF→テキスト変換ツール (Python 標準ライブラリのみ)

ブラウザ内抽出で読めない PDF (日本語 CID フォント / ASCII85 / 多段フィルタ) を
コンピュータが読めるプレーンテキストへ変換する。変換した .txt を BadaGPT に
アップロードすれば、資料として質問・要望に使える。

対応:
  · フィルタ連鎖: FlateDecode / ASCII85Decode / ASCIIHexDecode / RunLengthDecode / LZWDecode
  · 文字列表示: (…) Tj / ' / " と <hex> Tj、TJ 配列 (両形式混在可)
  · 日本語 CID フォント: ToUnicode CMap (bfchar / bfrange) を解析して Unicode 復元
  · UTF-16BE (BOM 付き) 16進文字列

使い方:
  python3 pdf2text.py input.pdf                 # 標準出力へ
  python3 pdf2text.py input.pdf -o output.txt   # ファイルへ
  python3 pdf2text.py *.pdf --dir out/          # 一括変換 (out/название.txt)

依存: なし (Python 3.8+)
© Masaaki Yamaguchi — https://github.com/masaaki-avnturle/Bada
"""
import re
import sys
import zlib
import base64
import argparse

# ---------------------------------------------------------------------------
#  フィルタ復号
# ---------------------------------------------------------------------------

def _flate(data: bytes) -> bytes:
    for wbits in (15, -15, 47):
        try:
            return zlib.decompressobj(wbits).decompress(data)
        except zlib.error:
            continue
    raise ValueError("FlateDecode failed")


def _ascii85(data: bytes) -> bytes:
    body = data.strip()
    if body.startswith(b"<~"):
        body = body[2:]
    end = body.find(b"~>")
    if end >= 0:
        body = body[:end]
    return base64.a85decode(re.sub(rb"\s+", b"", body))


def _asciihex(data: bytes) -> bytes:
    h = re.sub(rb"[^0-9A-Fa-f]", b"", data.split(b">")[0])
    if len(h) % 2:
        h += b"0"
    return bytes.fromhex(h.decode("ascii"))


def _runlength(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        n = data[i]
        if n == 128:
            break
        if n < 128:
            out += data[i + 1: i + 2 + n]
            i += 2 + n
        else:
            out += data[i + 1: i + 2] * (257 - n)
            i += 2
    return bytes(out)


def _lzw(data: bytes) -> bytes:
    # PDF LZWDecode (MSB-first, 9..12bit 可変長, EarlyChange=1)
    out = bytearray()
    table = {i: bytes([i]) for i in range(256)}
    next_code = 258
    width = 9
    prev = None
    buf = 0
    nbits = 0
    for byte in data:
        buf = (buf << 8) | byte
        nbits += 8
        while nbits >= width:
            nbits -= width
            code = (buf >> nbits) & ((1 << width) - 1)
            if code == 256:                       # Clear
                table = {i: bytes([i]) for i in range(256)}
                next_code = 258
                width = 9
                prev = None
                continue
            if code == 257:                       # EOD
                return bytes(out)
            if prev is None:
                entry = table[code]
            elif code in table:
                entry = table[code]
            elif code == next_code:
                entry = prev + prev[:1]
            else:
                raise ValueError("bad LZW code")
            out += entry
            if prev is not None:
                table[next_code] = prev + entry[:1]
                next_code += 1
                if next_code + 1 >= (1 << width) and width < 12:
                    width += 1
            prev = entry
    return bytes(out)


FILTERS = {
    b"FlateDecode": _flate, b"Fl": _flate,
    b"ASCII85Decode": _ascii85, b"A85": _ascii85,
    b"ASCIIHexDecode": _asciihex, b"AHx": _asciihex,
    b"RunLengthDecode": _runlength, b"RL": _runlength,
    b"LZWDecode": _lzw, b"LZW": _lzw,
}
SKIP_FILTERS = (b"DCTDecode", b"JPXDecode", b"CCITTFaxDecode", b"JBIG2Decode")


def get_filters(dict_bytes: bytes):
    m = re.search(rb"/Filter\s*(\[(?:[^\[\]])*\]|/[A-Za-z0-9]+)", dict_bytes)
    if not m:
        return []
    return re.findall(rb"/([A-Za-z0-9]+)", m.group(1))


def decode_stream(dict_bytes: bytes, raw: bytes):
    data = raw
    for f in get_filters(dict_bytes) or [b""]:
        if f in SKIP_FILTERS:
            return None                            # 画像等は対象外
        fn = FILTERS.get(f)
        if fn is None:
            if f == b"":
                break
            return None
        try:
            data = fn(data)
        except Exception:
            return None
    return data

# ---------------------------------------------------------------------------
#  オブジェクト / ストリーム走査
# ---------------------------------------------------------------------------

def iter_streams(pdf: bytes):
    """(dict_bytes, stream_bytes) を順に返す (xref 非依存の力任せ走査)。"""
    pos = 0
    while True:
        s = pdf.find(b"stream", pos)
        if s < 0:
            return
        # dict は直前の << ... >> (最大 2KB 遡る)
        head = pdf[max(0, s - 2048): s]
        d0 = head.rfind(b"<<")
        dict_bytes = head[d0:] if d0 >= 0 else b""
        p = s + 6
        if pdf[p:p + 2] == b"\r\n":
            p += 2
        elif pdf[p:p + 1] in (b"\n", b"\r"):
            p += 1
        e = pdf.find(b"endstream", p)
        if e < 0:
            return
        yield dict_bytes, pdf[p:e]
        pos = e + 9

# ---------------------------------------------------------------------------
#  ToUnicode CMap (bfchar / bfrange)
# ---------------------------------------------------------------------------

def parse_cmap(text: bytes, cmap: dict):
    def u16(hexs: bytes) -> str:
        b = bytes.fromhex(hexs.decode("ascii"))
        if len(b) % 2:
            b += b"\x00"
        return b.decode("utf-16-be", "ignore")

    for m in re.finditer(rb"beginbfchar(.*?)endbfchar", text, re.S):
        for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", m.group(1)):
            cmap[(len(src) // 2, int(src, 16))] = u16(dst)
    for m in re.finditer(rb"beginbfrange(.*?)endbfrange", text, re.S):
        body = m.group(1)
        for lo, hi, dst in re.findall(
                rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", body):
            n = len(lo) // 2
            lo_i, hi_i = int(lo, 16), int(hi, 16)
            base = int(dst, 16)
            width = len(dst) // 2
            for c in range(lo_i, min(hi_i, lo_i + 65535) + 1):
                cmap[(n, c)] = u16(("%0*x" % (width * 2, base + c - lo_i)).encode())
        for lo, hi, arr in re.findall(
                rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", body, re.S):
            n = len(lo) // 2
            dsts = re.findall(rb"<([0-9A-Fa-f]+)>", arr)
            for i, d in enumerate(dsts):
                cmap[(n, int(lo, 16) + i)] = u16(d)

# ---------------------------------------------------------------------------
#  コンテンツストリームからのテキスト抽出
# ---------------------------------------------------------------------------

PDFDOC_ESC = {b"n": b"\n", b"r": b"", b"t": b" ", b"b": b"", b"f": b"",
              b"(": b"(", b")": b")", b"\\": b"\\"}


def unescape_paren(body: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(body):
        c = body[i:i + 1]
        if c == b"\\":
            nxt = body[i + 1:i + 2]
            if nxt in PDFDOC_ESC:
                out += PDFDOC_ESC[nxt]
                i += 2
            elif nxt.isdigit():
                oct_m = re.match(rb"[0-7]{1,3}", body[i + 1:i + 4])
                out.append(int(oct_m.group(0), 8))
                i += 1 + len(oct_m.group(0))
            else:
                i += 2
        else:
            out += c
            i += 1
    return bytes(out)


def _score(s: str) -> float:
    """可読性スコア: CJK・かな・ASCII 印字可能の比率 (高いほど自然言語らしい)。"""
    if not s:
        return 0.0
    good = 0
    for ch in s:
        o = ord(ch)
        if (0x20 <= o < 0x7F) or ch in "\n\t" or \
           (0x3000 <= o <= 0x30FF) or (0x4E00 <= o <= 0x9FFF) or \
           (0xFF01 <= o <= 0xFFEF) or (0x2000 <= o <= 0x22FF):
            good += 1
    return good / len(s)


def cmap_decode(b: bytes, cmap: dict) -> str:
    out = []
    i = 0
    while i < len(b):
        if i + 1 < len(b):
            hit = cmap.get((2, (b[i] << 8) | b[i + 1]))
            if hit is not None:
                out.append(hit)
                i += 2
                continue
        hit = cmap.get((1, b[i]))
        out.append(hit if hit is not None else "")
        i += 1
    return "".join(out)


def bytes_to_text(b: bytes, cmap: dict) -> str:
    """バイト列 → 最良候補のテキスト。
    latin-1 / UTF-16BE / ToUnicode CMap の 3 通りを可読性スコアで比較する。
    (日本語 PDF は Identity-H で CID=Unicode の UTF-16BE 相当が多い)"""
    if not b:
        return ""
    if b[:2] == b"\xfe\xff":
        return b[2:].decode("utf-16-be", "ignore")
    cands = [(b.decode("latin-1"), 0.05)]          # 同点なら latin-1 を優先
    if len(b) >= 2 and len(b) % 2 == 0:
        cands.append((b.decode("utf-16-be", "ignore"), 0.0))
        if cmap:
            cands.append((cmap_decode(b, cmap), 0.10))  # CMap 命中は最優先
    best, best_sc = "", -1.0
    for s, bonus in cands:
        sc = _score(s) + bonus if s else 0.0
        if sc > best_sc:
            best, best_sc = s, sc
    return best


def decode_paren(body: bytes, cmap: dict) -> str:
    return bytes_to_text(unescape_paren(body), cmap)


def decode_hex(hexs: bytes, cmap: dict) -> str:
    h = re.sub(rb"\s+", b"", hexs)
    if len(h) % 2:
        h += b"0"
    return bytes_to_text(bytes.fromhex(h.decode("ascii")), cmap)


# 文字列トークン: (…) / <…> を順に拾い、直後の演算子を見る
TOK = re.compile(rb"\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]*>|\[|\]|[A-Za-z'\"]{1,3}|.", re.S)


def extract_text(content: bytes, cmap: dict) -> str:
    out = []
    pend = []           # 未確定の文字列トークン (直後の演算子で確定)
    for m in TOK.finditer(content):
        t = m.group(0)
        if t.startswith(b"("):
            pend.append(("p", t[1:-1]))
        elif t.startswith(b"<") and t != b"<<":
            pend.append(("h", t[1:-1]))
        elif t in (b"Tj", b"'", b'"', b"TJ"):
            for kind, body in pend:
                out.append(decode_paren(body, cmap) if kind == "p" else decode_hex(body, cmap))
            if t != b"TJ":
                out.append("")
            pend = []
            out.append(" ")
        elif t in (b"TD", b"Td", b"T*", b"BT", b"ET"):
            pend = []
            out.append("\n" if t in (b"TD", b"Td", b"T*") else "")
        elif t == b"]":
            continue
        elif t == b"[":
            continue
        elif len(t) > 3 or t.isalpha():
            pend = []
    return "".join(out)


def cleanup(t: str) -> str:
    t = t.replace("\x00", "")
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    # 制御文字除去
    t = "".join(ch for ch in t if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return t.strip()

# ---------------------------------------------------------------------------
#  変換本体
# ---------------------------------------------------------------------------

def pdf_to_text(pdf: bytes) -> str:
    if b"/Encrypt" in pdf[:4096] or b"/Encrypt" in pdf[-4096:]:
        sys.stderr.write("warning: encrypted PDF — extraction may fail\n")

    cmap: dict = {}
    contents = []
    for dict_bytes, raw in iter_streams(pdf):
        data = decode_stream(dict_bytes, raw)
        if data is None:
            continue
        if b"beginbfchar" in data or b"beginbfrange" in data:
            parse_cmap(data, cmap)
        elif b"Tj" in data or b"TJ" in data or b"BT" in data:
            contents.append(data)

    text = "\n".join(extract_text(c, cmap) for c in contents)
    text = cleanup(text)
    if len(re.sub(r"\s", "", text)) < 8:
        # 最後の手段: 生バイトから括弧文字列を拾う
        text = cleanup(extract_text(pdf, cmap))
    return text


def main():
    ap = argparse.ArgumentParser(description="PDF → plain text (BadaGPT companion tool)")
    ap.add_argument("inputs", nargs="+", help="input PDF file(s)")
    ap.add_argument("-o", "--output", help="output .txt (single input only)")
    ap.add_argument("--dir", help="output directory for batch conversion")
    args = ap.parse_args()

    for path in args.inputs:
        with open(path, "rb") as f:
            pdf = f.read()
        if not pdf.lstrip()[:5].startswith(b"%PDF-") and b"%PDF-" not in pdf[:1024]:
            sys.stderr.write(f"{path}: not a PDF (no %PDF- header) — trying anyway\n")
        text = pdf_to_text(pdf)
        if args.dir:
            import os
            os.makedirs(args.dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(path))[0] + ".txt"
            out = os.path.join(args.dir, base)
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"{path} -> {out} ({len(text)} chars)")
        elif args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"{path} -> {args.output} ({len(text)} chars)")
        else:
            sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
