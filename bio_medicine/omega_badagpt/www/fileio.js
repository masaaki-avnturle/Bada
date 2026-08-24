/* ============================================================================
 *  fileio.js — BadaGPT 入出力ユーティリティ
 *    · PDF / テキスト / ソースコードの読み込み (ブラウザ内, 外部ライブラリ非依存)
 *    · 生成解答の PDF 書き出し (純JS PDF ライタ)
 *    · 生成解答からのソースコード抽出 & ダウンロード
 *  Chromium (Electron / Android WebView) の DecompressionStream を用いて
 *  FlateDecode ストリームを展開し、PDF からテキストを取り出す。
 * ==========================================================================*/
"use strict";

const FileIO = (() => {

  // ---- FlateDecode (zlib) 展開: 標準 DecompressionStream を使用 ----------
  // DecompressionStream は末尾の余分バイト (endstream 直前の改行等) で
  // 全体をエラーにするため、途中まで復号できた部分を保持する寛容版。
  async function inflateWith(bytes, format) {
    try {
      const ds = new DecompressionStream(format);
      const writer = ds.writable.getWriter();
      writer.write(bytes).catch(() => {});
      writer.close().catch(() => {});
      const reader = ds.readable.getReader();
      const chunks = [];
      let total = 0;
      try {
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
          total += value.length;
        }
      } catch (e) { /* 部分復号を保持 */ }
      if (!total) return null;
      const out = new Uint8Array(total);
      let o = 0;
      for (const c of chunks) { out.set(c, o); o += c.length; }
      return out;
    } catch (e) { return null; }
  }
  async function inflate(bytes) {
    // 末尾の空白/改行を除去してから試す
    let end = bytes.length;
    while (end > 0 && (bytes[end - 1] === 0x0a || bytes[end - 1] === 0x0d ||
                       bytes[end - 1] === 0x20 || bytes[end - 1] === 0x09)) end--;
    const trimmed = bytes.subarray(0, end);
    return (await inflateWith(trimmed, "deflate")) ||
           (await inflateWith(trimmed, "deflate-raw"));
  }

  // ---- PDF → テキスト -----------------------------------------------------
  // 拡張抽出器 (tools/pdf2text.py の JS 移植):
  //   · フィルタ連鎖: FlateDecode / ASCII85Decode / ASCIIHexDecode / RunLengthDecode
  //   · (…) と <hex> の両文字列形式、Tj / ' / " / TJ 配列
  //   · 日本語 CID フォント: ToUnicode CMap (bfchar/bfrange) で Unicode 復元
  //   · UTF-16BE 自動判別 (latin-1 / UTF-16BE / CMap を可読性スコアで選択)
  const latin = (u8) => { let s = ""; for (let i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]); return s; };

  function ascii85Decode(u8) {
    let s = latin(u8).trim();
    if (s.startsWith("<~")) s = s.slice(2);
    const end = s.indexOf("~>");
    if (end >= 0) s = s.slice(0, end);
    s = s.replace(/\s+/g, "");
    const out = [];
    for (let i = 0; i < s.length;) {
      if (s[i] === "z") { out.push(0, 0, 0, 0); i++; continue; }
      const grp = s.slice(i, i + 5);
      const pad = 5 - grp.length;
      let v = 0;
      for (let j = 0; j < 5; j++) v = v * 85 + ((j < grp.length ? grp.charCodeAt(j) : 117) - 33);
      const b = [(v >>> 24) & 255, (v >>> 16) & 255, (v >>> 8) & 255, v & 255];
      for (let j = 0; j < 4 - pad; j++) out.push(b[j]);
      i += 5;
    }
    return new Uint8Array(out);
  }
  function asciiHexDecode(u8) {
    let h = latin(u8).split(">")[0].replace(/[^0-9A-Fa-f]/g, "");
    if (h.length % 2) h += "0";
    const out = new Uint8Array(h.length / 2);
    for (let i = 0; i < out.length; i++) out[i] = parseInt(h.substr(i * 2, 2), 16);
    return out;
  }
  function runLengthDecode(u8) {
    const out = [];
    for (let i = 0; i < u8.length;) {
      const n = u8[i];
      if (n === 128) break;
      if (n < 128) { for (let j = 0; j <= n; j++) out.push(u8[i + 1 + j]); i += 2 + n; }
      else { for (let j = 0; j < 257 - n; j++) out.push(u8[i + 1]); i += 2; }
    }
    return new Uint8Array(out);
  }
  const SKIP_F = ["DCTDecode", "JPXDecode", "CCITTFaxDecode", "JBIG2Decode"];
  async function decodeStream(dictStr, chunk) {
    const fm = dictStr.match(/\/Filter\s*(\[[^\]]*\]|\/[A-Za-z0-9]+)/);
    const filters = fm ? (fm[1].match(/\/([A-Za-z0-9]+)/g) || []).map(x => x.slice(1)) : [];
    let data = chunk;
    for (const f of filters) {
      if (SKIP_F.includes(f)) return null;
      try {
        if (f === "FlateDecode" || f === "Fl") {
          const inf = await inflate(data);
          if (!inf) return null;
          data = inf;
        } else if (f === "ASCII85Decode" || f === "A85") data = ascii85Decode(data);
        else if (f === "ASCIIHexDecode" || f === "AHx") data = asciiHexDecode(data);
        else if (f === "RunLengthDecode" || f === "RL") data = runLengthDecode(data);
        else return null;
      } catch (e) { return null; }
    }
    if (!filters.length) {
      const inf = await inflate(data);       // フィルタ不明時は Flate を試す
      if (inf) data = inf;
    }
    return data;
  }

  // --- ToUnicode CMap ------------------------------------------------------
  function parseCMap(s, cmap) {
    const u16 = hex => {
      let out = "";
      for (let i = 0; i + 3 < hex.length + 1; i += 4)
        out += String.fromCharCode(parseInt(hex.substr(i, 4), 16));
      return out;
    };
    let m;
    const reChar = /beginbfchar([\s\S]*?)endbfchar/g;
    while ((m = reChar.exec(s)) !== null) {
      const re = /<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>/g;
      let p;
      while ((p = re.exec(m[1])) !== null)
        cmap.set((p[1].length / 2) + ":" + parseInt(p[1], 16), u16(p[2]));
    }
    const reRange = /beginbfrange([\s\S]*?)endbfrange/g;
    while ((m = reRange.exec(s)) !== null) {
      const re3 = /<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>/g;
      let p;
      while ((p = re3.exec(m[1])) !== null) {
        const n = p[1].length / 2, lo = parseInt(p[1], 16),
              hi = Math.min(parseInt(p[2], 16), lo + 65535), base = parseInt(p[3], 16);
        for (let c = lo; c <= hi; c++)
          cmap.set(n + ":" + c, u16((base + c - lo).toString(16).padStart(p[3].length, "0")));
      }
      const reArr = /<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[([\s\S]*?)\]/g;
      while ((p = reArr.exec(m[1])) !== null) {
        const n = p[1].length / 2, lo = parseInt(p[1], 16);
        const dsts = p[3].match(/<([0-9A-Fa-f]+)>/g) || [];
        dsts.forEach((d, i) => cmap.set(n + ":" + (lo + i), u16(d.slice(1, -1))));
      }
    }
  }

  // --- 可読性スコアによる最良復号 -------------------------------------------
  function readScore(s) {
    if (!s) return 0;
    let good = 0;
    for (const ch of s) {
      const o = ch.codePointAt(0);
      if ((o >= 0x20 && o < 0x7f) || ch === "\n" || ch === "\t" ||
          (o >= 0x3000 && o <= 0x30ff) || (o >= 0x4e00 && o <= 0x9fff) ||
          (o >= 0xff01 && o <= 0xffef) || (o >= 0x2000 && o <= 0x22ff)) good++;
    }
    return good / [...s].length;
  }
  function cmapDecode(bytes, cmap) {
    let out = "";
    for (let i = 0; i < bytes.length;) {
      if (i + 1 < bytes.length) {
        const hit2 = cmap.get("2:" + ((bytes[i] << 8) | bytes[i + 1]));
        if (hit2 !== undefined) { out += hit2; i += 2; continue; }
      }
      const hit1 = cmap.get("1:" + bytes[i]);
      out += hit1 !== undefined ? hit1 : "";
      i++;
    }
    return out;
  }
  function bytesToText(bytes, cmap) {
    if (!bytes.length) return "";
    if (bytes[0] === 0xfe && bytes[1] === 0xff) {
      let out = "";
      for (let i = 2; i + 1 < bytes.length; i += 2)
        out += String.fromCharCode((bytes[i] << 8) | bytes[i + 1]);
      return out;
    }
    const cands = [[latin(bytes), 0.05]];
    if (bytes.length >= 2 && bytes.length % 2 === 0) {
      let u = "";
      for (let i = 0; i + 1 < bytes.length; i += 2)
        u += String.fromCharCode((bytes[i] << 8) | bytes[i + 1]);
      cands.push([u, 0.0]);
      if (cmap.size) cands.push([cmapDecode(bytes, cmap), 0.10]);
    }
    let best = "", bestSc = -1;
    for (const [s, bonus] of cands) {
      const sc = s ? readScore(s) + bonus : 0;
      if (sc > bestSc) { best = s; bestSc = sc; }
    }
    return best;
  }
  function unescapeParen(s) {
    const out = [];
    for (let i = 0; i < s.length;) {
      if (s[i] === "\\") {
        const n = s[i + 1];
        if (n === "n") { out.push(10); i += 2; }
        else if (n === "t") { out.push(32); i += 2; }
        else if (n === "r" || n === "b" || n === "f") i += 2;
        else if (n >= "0" && n <= "7") {
          const oct = (s.slice(i + 1).match(/^[0-7]{1,3}/) || ["0"])[0];
          out.push(parseInt(oct, 8) & 255);
          i += 1 + oct.length;
        } else { out.push(s.charCodeAt(i + 1) & 255); i += 2; }
      } else { out.push(s.charCodeAt(i) & 255); i++; }
    }
    return new Uint8Array(out);
  }
  function hexToBytes(h) {
    h = h.replace(/\s+/g, "");
    if (h.length % 2) h += "0";
    const out = new Uint8Array(h.length / 2);
    for (let i = 0; i < out.length; i++) out[i] = parseInt(h.substr(i * 2, 2), 16);
    return out;
  }

  // --- コンテンツストリームからのテキスト抽出 -------------------------------
  function extractTjText(s, cmap) {
    cmap = cmap || new Map();
    let out = "";
    const tok = /\((?:\\[\s\S]|[^\\()])*\)|<[0-9A-Fa-f\s]*>|\[|\]|[A-Za-z'"]{1,3}|[\s\S]/g;
    let pend = [], m;
    while ((m = tok.exec(s)) !== null) {
      const t = m[0];
      if (t[0] === "(") pend.push(["p", t.slice(1, -1)]);
      else if (t[0] === "<" && t !== "<<") pend.push(["h", t.slice(1, -1)]);
      else if (t === "Tj" || t === "'" || t === '"' || t === "TJ") {
        for (const [kind, body] of pend)
          out += kind === "p" ? bytesToText(unescapeParen(body), cmap) : bytesToText(hexToBytes(body), cmap);
        pend = [];
        out += " ";
      } else if (t === "TD" || t === "Td" || t === "T*") { pend = []; out += "\n"; }
      else if (t === "BT" || t === "ET") pend = [];
      else if (t.length > 1 && /^[A-Za-z]+$/.test(t)) pend = [];
    }
    return out;
  }

  async function pdfToText(arrayBuffer) {
    const data = new Uint8Array(arrayBuffer);
    const raw = latin(data);
    const cmap = new Map();
    const contents = [];
    let idx = 0;
    while (true) {
      const sPos = raw.indexOf("stream", idx);
      if (sPos < 0) break;
      let start = sPos + 6;
      if (raw[start] === "\r") start++;
      if (raw[start] === "\n") start++;
      const ePos = raw.indexOf("endstream", start);
      if (ePos < 0) break;
      idx = ePos + 9;
      // 直前 2KB から辞書 << … >> を取り出す
      const head = raw.slice(Math.max(0, sPos - 2048), sPos);
      const d0 = head.lastIndexOf("<<");
      const dictStr = d0 >= 0 ? head.slice(d0) : "";
      const decoded = await decodeStream(dictStr, data.subarray(start, ePos));
      if (!decoded) continue;
      const content = latin(decoded);
      if (content.includes("beginbfchar") || content.includes("beginbfrange")) parseCMap(content, cmap);
      else if (content.includes("Tj") || content.includes("TJ") || content.includes("BT")) contents.push(content);
    }
    let text = contents.map(c => extractTjText(c, cmap)).join("\n");
    // 何も取れなければ、生の (...) 文字列を最後の手段で拾う
    if (text.replace(/\s/g, "").length < 8) text = extractTjText(raw, cmap);
    text = cleanup(text);
    // 可読性が低い / 抽出量がファイルサイズに対して極端に少ない場合は
    // Python 変換ツールへの案内を先頭に付す
    const tooShort = data.length > 10000 && text.length < 800;
    if (text.length && (readScore(text) < 0.55 || tooShort)) {
      text = "⚠ この PDF はブラウザ内では十分に復号できませんでした " +
        "(ToUnicode 情報のないフォント等)。同梱の Python 変換ツール " +
        "(①の「Python変換ツールを保存」→ python3 pdf2text.py この.pdf -o 出力.txt) で変換した " +
        ".txt をアップロードしてください。\n\n--- 部分抽出結果 ---\n" + text;
    }
    return text;
  }

  function cleanup(t) {
    return t.replace(/ /g, "").replace(/[ \t]{2,}/g, " ")
            .replace(/\n{3,}/g, "\n\n").trim();
  }

  // ---- ファイル読み込み (内容シグネチャで自動判別) -----------------------
  // 拡張子が .pdf でなくても(あるいは拡張子が無くても)中身を見て処理する:
  //   · 先頭 1KB に "%PDF-"      → PDF としてテキスト抽出
  //   · 先頭が PK\x03\x04 (ZIP)  → docx/xlsx/pptx 等の OOXML から XML テキスト抽出
  //   · UTF-8 / Shift_JIS として妥当 → テキスト/コード
  //   · それ以外のバイナリ        → 印字可能文字列の救済抽出 (strings 相当)
  const TEXT_EXT = ["txt","md","markdown","js","ts","jsx","tsx","py","c","h","cpp","hpp",
    "cc","cs","java","rb","go","rs","php","swift","kt","scala","sh","bash","zsh","pl",
    "lua","r","m","sql","html","htm","css","scss","json","yaml","yml","toml","ini","cfg",
    "xml","csv","tex","bada","asm","f90","jl","dart","vue","svelte","gradle","make","cmake"];

  function findSig(data, sig, limit) {
    const n = Math.min(data.length - sig.length + 1, limit);
    outer:
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < sig.length; j++)
        if (data[i + j] !== sig[j]) continue outer;
      return i;
    }
    return -1;
  }

  function decodeAnyText(data) {
    try { return { text: new TextDecoder("utf-8", { fatal: true }).decode(data), enc: "utf-8" }; }
    catch (e) {}
    try { return { text: new TextDecoder("shift_jis", { fatal: true }).decode(data), enc: "shift_jis" }; }
    catch (e) {}
    return null;
  }

  // バイナリからの救済抽出: 4 文字以上の印字可能 ASCII 連続列を拾う
  function binaryStrings(data, cap = 20000) {
    let out = "", run = "";
    for (let i = 0; i < data.length && out.length < cap; i++) {
      const c = data[i];
      if (c === 9 || c === 10 || (c >= 32 && c < 127)) run += String.fromCharCode(c);
      else { if (run.length >= 4) out += run + "\n"; run = ""; }
    }
    if (run.length >= 4) out += run;
    return out.trim();
  }

  // ZIP (docx/xlsx/pptx/odt/jar…) → 中の XML/テキストエントリからテキスト抽出。
  // EOCD → 中央ディレクトリを辿り、deflate エントリは DecompressionStream で展開。
  async function zipToText(data) {
    // End of Central Directory (0x06054b50) を末尾から探す
    let eocd = -1;
    const min = Math.max(0, data.length - 65558);
    for (let i = data.length - 22; i >= min; i--) {
      if (data[i] === 0x50 && data[i+1] === 0x4b && data[i+2] === 0x05 && data[i+3] === 0x06) { eocd = i; break; }
    }
    if (eocd < 0) return "";
    const dv = new DataView(data.buffer, data.byteOffset, data.byteLength);
    const count = dv.getUint16(eocd + 10, true);
    let off = dv.getUint32(eocd + 16, true);
    const WANT = /\.(xml|txt|md|html?|json|csv|rels)$/i;
    let out = "";
    for (let e = 0; e < count && off + 46 <= data.length; e++) {
      if (dv.getUint32(off, true) !== 0x02014b50) break;      // central header sig
      const method   = dv.getUint16(off + 10, true);
      const csize    = dv.getUint32(off + 20, true);
      const nameLen  = dv.getUint16(off + 28, true);
      const extraLen = dv.getUint16(off + 30, true);
      const cmtLen   = dv.getUint16(off + 32, true);
      const lhOff    = dv.getUint32(off + 42, true);
      const name     = new TextDecoder().decode(data.subarray(off + 46, off + 46 + nameLen));
      off += 46 + nameLen + extraLen + cmtLen;
      if (!WANT.test(name) || csize === 0) continue;
      // ローカルヘッダから実データ位置を求める
      if (dv.getUint32(lhOff, true) !== 0x04034b50) continue;
      const lNameLen  = dv.getUint16(lhOff + 26, true);
      const lExtraLen = dv.getUint16(lhOff + 28, true);
      const start = lhOff + 30 + lNameLen + lExtraLen;
      const comp = data.subarray(start, start + csize);
      let raw = null;
      if (method === 0) raw = comp;
      else if (method === 8) {
        try {
          const ds = new DecompressionStream("deflate-raw");
          const buf = await new Response(new Blob([comp]).stream().pipeThrough(ds)).arrayBuffer();
          raw = new Uint8Array(buf);
        } catch (err) { continue; }
      } else continue;
      let t = new TextDecoder("utf-8").decode(raw);
      if (/\.xml$|\.rels$/i.test(name)) {
        // XML: タグを除去し、代表的な実体参照を戻す
        t = t.replace(/<[^>]*>/g, " ")
             .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
             .replace(/&apos;/g, "'").replace(/&amp;/g, "&")
             .replace(/[ \t]{2,}/g, " ");
      }
      t = t.trim();
      if (t) out += `\n[${name}]\n${t}\n`;
      if (out.length > 60000) break;
    }
    return out.trim();
  }

  async function readFile(file) {
    const name = file.name || "file";
    const ext = (name.split(".").pop() || "").toLowerCase();
    const buf = await file.arrayBuffer();
    const data = new Uint8Array(buf);

    // 1) PDF (拡張子に関係なく先頭 1KB のシグネチャで判定)
    if (findSig(data, [0x25, 0x50, 0x44, 0x46, 0x2d], 1024) >= 0) {  // "%PDF-"
      const txt = await pdfToText(buf);
      return { name, kind: "pdf", text: txt };
    }
    // 2) ZIP 系 (docx / xlsx / pptx / odt …)
    if (data.length > 4 && data[0] === 0x50 && data[1] === 0x4b &&
        (data[2] === 0x03 || data[2] === 0x05 || data[2] === 0x07)) {
      const txt = await zipToText(data);
      if (txt) return { name, kind: "doc", text: txt };
      const sal = binaryStrings(data);
      return { name, kind: "bin", text: sal || "(テキストを抽出できませんでした)" };
    }
    // 3) テキスト (UTF-8 → Shift_JIS の順に妥当性判定)
    const dec = decodeAnyText(data);
    if (dec) {
      const kind = TEXT_EXT.includes(ext) ? "code" : "text";
      return { name, kind, text: dec.text };
    }
    // 4) その他のバイナリ: 印字可能文字列を救済抽出 (絶対に失敗させない)
    const sal = binaryStrings(data);
    return { name, kind: "bin",
             text: sal || "(バイナリファイル: 抽出可能なテキストがありません)" };
  }

  // ========================================================================
  //  純JS PDF ライタ (Helvetica, 複数ページ, ASCII/latin1)
  // ========================================================================
  function escapePdf(s) { return s.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)"); }

  function wrapLine(line, maxChars) {
    if (line.length <= maxChars) return [line];
    const words = line.split(/(\s+)/);
    const out = []; let cur = "";
    for (const w of words) {
      if ((cur + w).length > maxChars && cur.length) { out.push(cur.replace(/\s+$/,"")); cur = w.replace(/^\s+/,""); }
      else cur += w;
      while (cur.length > maxChars) { out.push(cur.slice(0, maxChars)); cur = cur.slice(maxChars); }
    }
    if (cur.length) out.push(cur);
    return out.length ? out : [""];
  }

  // 非 latin1 文字(日本語等)は PDF 標準フォントで表示できないため、
  // 可読性のため近似表現へ置換する簡易処理(ASCII/記号は保持)。
  function toLatin1(s) {
    let out = "";
    for (const ch of s) {
      const c = ch.codePointAt(0);
      if (c === 10 || c === 9 || (c >= 32 && c < 256)) out += ch;
      else out += "?"; // non-latin1 (Japanese etc.) not in PDF base font
    }
    return out;
  }

  function textToPdf(title, body) {
    const fontSize = 10.5, lead = 14, margin = 54;
    const pageW = 595.28, pageH = 841.89; // A4
    const usableW = pageW - margin * 2;
    const maxChars = Math.floor(usableW / (fontSize * 0.5)); // Helvetica ≈0.5em/char
    const linesTop = pageH - margin;
    const linesPerPage = Math.floor((linesTop - margin) / lead);

    const src = (title ? (title + "\n" + "=".repeat(Math.min(title.length, 60)) + "\n\n") : "") + body;
    const rawLines = toLatin1(src).split("\n");
    const wrapped = [];
    for (const l of rawLines) for (const w of wrapLine(l.replace(/\t/g, "    "), maxChars)) wrapped.push(w);

    // ページ分割
    const pages = [];
    for (let i = 0; i < wrapped.length; i += linesPerPage) pages.push(wrapped.slice(i, i + linesPerPage));
    if (!pages.length) pages.push([""]);

    // PDF オブジェクト構築
    const objs = [];
    const fontObj = 2, resPages = 1; // 予約
    // 1: Pages, 2: Font
    const pageObjNums = [];
    const contentObjNums = [];
    let objNum = 3;
    for (let p = 0; p < pages.length; p++) { pageObjNums.push(objNum++); contentObjNums.push(objNum++); }

    // Catalog は最後に付ける
    const catalogNum = objNum++;

    function contentStream(lines) {
      let s = "BT\n/F1 " + fontSize + " Tf\n" + lead + " TL\n" + margin + " " + (linesTop - fontSize) + " Td\n";
      for (let i = 0; i < lines.length; i++) {
        s += "(" + escapePdf(lines[i]) + ") Tj\n";
        if (i < lines.length - 1) s += "T*\n";
      }
      s += "ET";
      return s;
    }

    const parts = [];
    const offsets = {};
    let pdf = "%PDF-1.4\n";

    function put(num, str) { offsets[num] = pdf.length; pdf += num + " 0 obj\n" + str + "\nendobj\n"; }

    // 1 Pages
    put(1, "<< /Type /Pages /Kids [" + pageObjNums.map(n => n + " 0 R").join(" ") + "] /Count " + pages.length + " >>");
    // 2 Font
    put(2, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>");
    // pages + contents
    for (let p = 0; p < pages.length; p++) {
      const cs = contentStream(pages[p]);
      put(pageObjNums[p], "<< /Type /Page /Parent 1 0 R /MediaBox [0 0 " + pageW + " " + pageH +
        "] /Resources << /Font << /F1 2 0 R >> >> /Contents " + contentObjNums[p] + " 0 R >>");
      put(contentObjNums[p], "<< /Length " + cs.length + " >>\nstream\n" + cs + "\nendstream");
    }
    // catalog
    put(catalogNum, "<< /Type /Catalog /Pages 1 0 R >>");

    // xref
    const xrefPos = pdf.length;
    const total = catalogNum + 1;
    pdf += "xref\n0 " + total + "\n0000000000 65535 f \n";
    for (let n = 1; n < total; n++) {
      const off = (offsets[n] || 0).toString().padStart(10, "0");
      pdf += off + " 00000 n \n";
    }
    pdf += "trailer\n<< /Size " + total + " /Root " + catalogNum + " 0 R >>\nstartxref\n" + xrefPos + "\n%%EOF";

    // latin1 → bytes
    const bytes = new Uint8Array(pdf.length);
    for (let i = 0; i < pdf.length; i++) bytes[i] = pdf.charCodeAt(i) & 0xff;
    return new Blob([bytes], { type: "application/pdf" });
  }

  // ---- ダウンロード補助 --------------------------------------------------
  // 5 段構え:
  //   1) Cordova (Android APK) 最優先: cordova-plugin-saf-mediastore で
  //      端末の共有「ダウンロード」フォルダへ MediaStore 経由で直接保存
  //      (Android 10+、権限プロンプト不要、ファイルアプリの Download に即表示)。
  //   2) 直接保存が使えない場合: cordova-plugin-save-dialog で Android 標準の
  //      「保存」ダイアログ (SAF) を開き、ユーザーが選んだ場所に保存。
  //   3) さらに代替: cordova-plugin-file でアプリの外部ストレージ領域へ直接
  //      書き込み (Android 11+ ではファイルアプリから見えないことがある)。
  //   4) 通常ブラウザ / Electron: <a download> + blob URL。
  //   5) それも失敗した場合: data: URI を新規タブで開く最終フォールバック。
  //   保存成功時は "fileio-saved" イベントで保存先を通知する。
  function notifySaved(filename, where) {
    try {
      document.dispatchEvent(new CustomEvent("fileio-saved",
        { detail: { filename, where } }));
    } catch (e) {}
  }

  function cordovaSave(blob, filename) {
    return new Promise((resolve, reject) => {
      const cf = window.cordova && window.cordova.file;
      if (!cf || !window.resolveLocalFileSystemURL) { reject(new Error("no file plugin")); return; }
      // 優先順: 外部データ領域 (権限不要・ファイルアプリから閲覧可) → 内部データ → キャッシュ
      const base = cf.externalDataDirectory || cf.dataDirectory || cf.cacheDirectory;
      if (!base) { reject(new Error("no writable dir")); return; }
      window.resolveLocalFileSystemURL(base, dir => {
        dir.getFile(filename, { create: true, exclusive: false }, entry => {
          entry.createWriter(writer => {
            writer.onwriteend = () => { notifySaved(filename, entry.nativeURL || base + filename); resolve(entry); };
            writer.onerror = reject;
            writer.write(blob);
          }, reject);
        }, reject);
      }, reject);
    });
  }

  function anchorSave(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 1500);
  }

  function dataUriFallback(blob, filename) {
    const reader = new FileReader();
    reader.onload = () => { try { window.open(reader.result, "_blank"); } catch (e) {} };
    reader.readAsDataURL(blob);
  }

  function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => {
        const s = String(r.result);
        resolve(s.slice(s.indexOf(",") + 1));
      };
      r.onerror = () => reject(r.error);
      r.readAsDataURL(blob);
    });
  }

  // 端末の共有「ダウンロード」フォルダへ直接保存 (cordova-plugin-saf-mediastore)
  function mediastoreSave(blob, filename) {
    const ms = window.cordova && window.cordova.plugins && window.cordova.plugins.safMediastore;
    if (!ms || typeof ms.writeFile !== "function") return Promise.reject(new Error("no mediastore plugin"));
    return blobToBase64(blob)
      .then(b64 => ms.writeFile({ filename, data: b64 }))
      .then(uri => {
        notifySaved(filename, "📂 ダウンロード フォルダに保存しました" + (uri ? " (" + uri + ")" : ""));
        return uri;
      });
  }

  // Android 標準の保存ダイアログ (cordova-plugin-save-dialog / SAF)
  function saveDialogSave(blob, filename) {
    const sd = window.cordova && window.cordova.plugins && window.cordova.plugins.saveDialog;
    if (!sd || typeof sd.saveFile !== "function") return Promise.reject(new Error("no save dialog"));
    return sd.saveFile(blob, filename).then(uri => {
      notifySaved(filename, uri || "選択した場所に保存しました");
      return uri;
    });
  }

  function download(blob, filename) {
    if (window.cordova) {
      mediastoreSave(blob, filename)
        .catch(() => saveDialogSave(blob, filename))
        .catch(() => cordovaSave(blob, filename))
        .catch(() => {
          try { anchorSave(blob, filename); } catch (e) { dataUriFallback(blob, filename); }
        });
      return;
    }
    try { anchorSave(blob, filename); }
    catch (e) { dataUriFallback(blob, filename); }
  }
  function downloadText(text, filename, mime = "text/plain") {
    download(new Blob([text], { type: mime + ";charset=utf-8" }), filename);
  }

  // ---- ZIP 生成 (無圧縮 STORE / 依存なし) ---------------------------------
  // 複数の生成ソースコードを 1 ファイルで確実にダウンロードするために使う。
  // (ブラウザ / WebView は 2 個目以降の自動ダウンロードをブロックするため、
  //  複数ファイルの連続ダウンロードは不可 — ZIP 1 個にまとめる)
  const CRC_TABLE = (() => {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[n] = c >>> 0;
    }
    return t;
  })();
  function crc32(u8) {
    let c = 0xFFFFFFFF;
    for (let i = 0; i < u8.length; i++) c = CRC_TABLE[(c ^ u8[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }
  // files: [{name: string, data: string|Uint8Array}] → Blob(application/zip)
  function makeZip(files) {
    const enc = new TextEncoder();
    const parts = [], central = [];
    let offset = 0;
    const u16 = v => new Uint8Array([v & 255, (v >> 8) & 255]);
    const u32 = v => new Uint8Array([v & 255, (v >> 8) & 255, (v >> 16) & 255, (v >>> 24) & 255]);
    for (const f of files) {
      const nameB = enc.encode(f.name);
      const data = typeof f.data === "string" ? enc.encode(f.data) : f.data;
      const crc = crc32(data);
      // local file header (method 0 = store, flag bit11 = UTF-8 name)
      const local = [u32(0x04034b50), u16(20), u16(0x0800), u16(0), u16(0), u16(0),
                     u32(crc), u32(data.length), u32(data.length),
                     u16(nameB.length), u16(0), nameB, data];
      const localLen = local.reduce((a, p) => a + p.length, 0);
      parts.push(...local);
      central.push([u32(0x02014b50), u16(20), u16(20), u16(0x0800), u16(0), u16(0), u16(0),
                    u32(crc), u32(data.length), u32(data.length),
                    u16(nameB.length), u16(0), u16(0), u16(0), u16(0), u32(0),
                    u32(offset), nameB]);
      offset += localLen;
    }
    let cdSize = 0;
    for (const c of central) { for (const p of c) { parts.push(p); cdSize += p.length; } }
    parts.push(u32(0x06054b50), u16(0), u16(0), u16(files.length), u16(files.length),
               u32(cdSize), u32(offset), u16(0));
    return new Blob(parts, { type: "application/zip" });
  }

  // ---- 解答からソースコードを抽出 (```lang ... ``` ブロック) -------------
  const LANG_EXT = { python:"py", py:"py", javascript:"js", js:"js", typescript:"ts", ts:"ts",
    c:"c", cpp:"cpp", "c++":"cpp", csharp:"cs", cs:"cs", java:"java", ruby:"rb", go:"go",
    rust:"rs", php:"php", swift:"swift", kotlin:"kt", scala:"scala", bash:"sh", sh:"sh",
    shell:"sh", html:"html", css:"css", json:"json", yaml:"yaml", yml:"yaml", sql:"sql",
    bada:"bada", lua:"lua", r:"r", dart:"dart", xml:"xml", markdown:"md", md:"md" };

  function extractCode(answer) {
    const blocks = [];
    const re = /```([A-Za-z0-9_+#-]*)\r?\n([\s\S]*?)```/g;
    let m, i = 0;
    while ((m = re.exec(answer)) !== null) {
      const lang = (m[1] || "").toLowerCase();
      const ext = LANG_EXT[lang] || (lang || "txt");
      blocks.push({ lang: lang || "text", ext, code: m[2].replace(/\s+$/,"") + "\n", index: ++i });
    }
    return blocks;
  }

  return { readFile, pdfToText, textToPdf, download, downloadText, extractCode, makeZip, LANG_EXT };
})();

if (typeof module !== "undefined" && module.exports) module.exports = FileIO;
