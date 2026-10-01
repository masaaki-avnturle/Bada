/*
 * exporters.js — 作ったアプリを配布できる形にする (ブラウザ / Android WebView / Electron / Node 共通)
 *
 *   standaloneHtml(runnerHtml, payload)       単体で動く HTML アプリ (Bada 処理系 + 生成した .bada を同梱)
 *   buildApk(templateApk, html, key)           Android APK: ランナー APK の assets/www/index.html を差し替えて
 *                                              JAR 署名 (APK v1 署名: MANIFEST.MF / CERT.SF / CERT.RSA)
 *   buildDeb(opts)                             Linux 用 .deb パッケージ (ar + control.tar.gz + data.tar.gz)
 *   imagePdf(pages)                            JPEG 画像のページから PDF を作る (設計書 PDF)
 *   readZip / writeZip                          ZIP の読み書き (deflate は CompressionStream / zlib)
 */
(function (root) {
  "use strict";
  const isNode = typeof process !== "undefined" && process.versions && process.versions.node && typeof window === "undefined";
  const te = new TextEncoder(), td = new TextDecoder();
  const enc = (s) => te.encode(s);
  const concat = (parts) => {
    let n = 0; for (const p of parts) n += p.length;
    const o = new Uint8Array(n); let k = 0; for (const p of parts) { o.set(p, k); k += p.length; } return o;
  };

  // ------------------------------------------------------------ 圧縮・ハッシュ
  async function streamThrough(u8, ts) {
    const s = new Blob([u8]).stream().pipeThrough(ts);
    return new Uint8Array(await new Response(s).arrayBuffer());
  }
  async function deflateRaw(u8) {
    if (isNode) return new Uint8Array(require("zlib").deflateRawSync(u8, { level: 9 }));
    return streamThrough(u8, new CompressionStream("deflate-raw"));
  }
  async function inflateRaw(u8) {
    if (isNode) return new Uint8Array(require("zlib").inflateRawSync(u8));
    return streamThrough(u8, new DecompressionStream("deflate-raw"));
  }
  async function gzip(u8) {
    if (isNode) return new Uint8Array(require("zlib").gzipSync(u8, { level: 9 }));
    return streamThrough(u8, new CompressionStream("gzip"));
  }
  const subtle = () => (root.crypto && root.crypto.subtle) || (isNode ? require("crypto").webcrypto.subtle : null);
  async function sha256(u8) { return new Uint8Array(await subtle().digest("SHA-256", u8)); }
  function b64(u8) {
    if (isNode) return Buffer.from(u8).toString("base64");
    let s = ""; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    return btoa(s);
  }
  function unb64(s) {
    if (isNode) return new Uint8Array(Buffer.from(s, "base64"));
    const b = atob(s), o = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) o[i] = b.charCodeAt(i); return o;
  }
  const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(u8) { let c = 0xffffffff; for (let i = 0; i < u8.length; i++) c = CRC[(c ^ u8[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }

  // ------------------------------------------------------------ ZIP
  function readZip(u8) {
    const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
    let eocd = -1;
    for (let i = u8.length - 22; i >= Math.max(0, u8.length - 65557); i--) if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    if (eocd < 0) throw new Error("ZIP ではありません");
    const count = dv.getUint16(eocd + 10, true); let off = dv.getUint32(eocd + 16, true);
    const out = [];
    for (let k = 0; k < count; k++) {
      if (dv.getUint32(off, true) !== 0x02014b50) throw new Error("壊れた ZIP (central directory)");
      const method = dv.getUint16(off + 10, true), crc = dv.getUint32(off + 16, true), csize = dv.getUint32(off + 20, true), usize = dv.getUint32(off + 24, true);
      const nlen = dv.getUint16(off + 28, true), xlen = dv.getUint16(off + 30, true), clen = dv.getUint16(off + 32, true), lho = dv.getUint32(off + 42, true);
      const name = td.decode(u8.subarray(off + 46, off + 46 + nlen));
      const lnlen = dv.getUint16(lho + 26, true), lxlen = dv.getUint16(lho + 28, true);
      const start = lho + 30 + lnlen + lxlen;
      out.push({ name, method, crc, csize, usize, raw: u8.subarray(start, start + csize) });
      off += 46 + nlen + xlen + clen;
    }
    return out;
  }
  async function entryData(e) { return e.method === 0 ? e.raw : inflateRaw(e.raw); }
  // entries: [{ name, data (無圧縮), store?: true }] または readZip のエントリ (raw をそのまま再利用)
  async function writeZip(entries, opts) {
    opts = opts || {};
    const parts = [], central = []; let off = 0;
    const dosTime = 0, dosDate = (2026 - 1980) << 9 | 1 << 5 | 1;
    for (const e of entries) {
      let method, raw, crc, usize;
      if (e.raw && e.data === undefined) { method = e.method; raw = e.raw; crc = e.crc; usize = e.usize; }
      else {
        const data = e.data; usize = data.length; crc = crc32(data);
        if (e.store || data.length < 64) { method = 0; raw = data; } else { method = 8; raw = await deflateRaw(data); if (raw.length >= data.length) { method = 0; raw = data; } }
      }
      const name = enc(e.name);
      // 無圧縮エントリは 4 バイト境界に揃える (zipalign 相当)
      let pad = 0;
      if (method === 0 && opts.align) pad = (4 - ((off + 30 + name.length) % 4)) % 4;
      const lh = new Uint8Array(30 + name.length + pad), lv = new DataView(lh.buffer);
      lv.setUint32(0, 0x04034b50, true); lv.setUint16(4, 20, true); lv.setUint16(6, 0x0800, true); lv.setUint16(8, method, true);
      lv.setUint16(10, dosTime, true); lv.setUint16(12, dosDate, true); lv.setUint32(14, crc, true); lv.setUint32(18, raw.length, true); lv.setUint32(22, usize, true);
      lv.setUint16(26, name.length, true); lv.setUint16(28, pad, true); lh.set(name, 30);
      const ch = new Uint8Array(46 + name.length), cv = new DataView(ch.buffer);
      cv.setUint32(0, 0x02014b50, true); cv.setUint16(4, 20, true); cv.setUint16(6, 20, true); cv.setUint16(8, 0x0800, true); cv.setUint16(10, method, true);
      cv.setUint16(12, dosTime, true); cv.setUint16(14, dosDate, true); cv.setUint32(16, crc, true); cv.setUint32(20, raw.length, true); cv.setUint32(24, usize, true);
      cv.setUint16(28, name.length, true); cv.setUint32(42, off, true); ch.set(name, 46);
      parts.push(lh, raw); central.push(ch); off += lh.length + raw.length;
    }
    const cd = concat(central), end = new Uint8Array(22), ev = new DataView(end.buffer);
    ev.setUint32(0, 0x06054b50, true); ev.setUint16(8, entries.length, true); ev.setUint16(10, entries.length, true);
    ev.setUint32(12, cd.length, true); ev.setUint32(16, off, true);
    return concat(parts.concat([cd, end]));
  }

  // ------------------------------------------------------------ DER (ASN.1)
  function derLen(n) { if (n < 128) return [n]; const b = []; while (n) { b.unshift(n & 0xff); n >>= 8; } return [0x80 | b.length].concat(b); }
  const der = (tag, ...contents) => { const body = concat(contents); return concat([new Uint8Array([tag].concat(derLen(body.length))), body]); };
  function derOid(s) {
    const p = s.split(".").map(Number), out = [40 * p[0] + p[1]];
    for (const v of p.slice(2)) { const b = []; let x = v; b.unshift(x & 0x7f); x = Math.floor(x / 128); while (x) { b.unshift(0x80 | (x & 0x7f)); x = Math.floor(x / 128); } out.push(...b); }
    return der(0x06, new Uint8Array(out));
  }
  const NULL = new Uint8Array([0x05, 0x00]);
  // TLV を読む: { tag, start, hstart, end } (start = 値の先頭)
  function tlv(u8, at) {
    const tag = u8[at]; let len = u8[at + 1], p = at + 2;
    if (len & 0x80) { const n = len & 0x7f; len = 0; for (let k = 0; k < n; k++) len = len * 256 + u8[p++]; }
    return { tag, hstart: at, start: p, end: p + len };
  }
  function children(u8, node) { const out = []; let p = node.start; while (p < node.end) { const c = tlv(u8, p); out.push(c); p = c.end; } return out; }

  // PKCS#7 SignedData (署名対象は CERT.SF、内容は外部) — JAR 署名ブロック CERT.RSA
  function pkcs7(certDer, signature) {
    const cert = tlv(certDer, 0), tbs = children(certDer, cert)[0], tk = children(certDer, tbs);
    const off = tk[0].tag === 0xa0 ? 1 : 0;
    const serial = certDer.subarray(tk[off].hstart, tk[off].end), issuer = certDer.subarray(tk[off + 2].hstart, tk[off + 2].end);
    const sha256Alg = der(0x30, derOid("2.16.840.1.101.3.4.2.1"), NULL);
    const signerInfo = der(0x30, der(0x02, new Uint8Array([1])), der(0x30, issuer, serial), sha256Alg,
      der(0x30, derOid("1.2.840.113549.1.1.1"), NULL), der(0x04, signature));
    const signedData = der(0x30, der(0x02, new Uint8Array([1])), der(0x31, sha256Alg), der(0x30, derOid("1.2.840.113549.1.7.1")),
      der(0xa0, certDer), der(0x31, signerInfo));
    return der(0x30, derOid("1.2.840.113549.1.7.2"), der(0xa0, signedData));
  }

  // ------------------------------------------------------------ JAR (APK v1) 署名
  // マニフェストの行は 72 バイトまで (続きは空白 1 個で始まる行)
  function mfLine(s) {
    const b = enc(s); if (b.length <= 70) return s + "\r\n";
    let out = "", cur = "", first = true;
    for (const ch of Array.from(s)) {
      const lim = first ? 70 : 69;
      if (enc(cur + ch).length > lim) { out += (first ? "" : " ") + cur + "\r\n"; cur = ""; first = false; }
      cur += ch;
    }
    return out + (first ? "" : " ") + cur + "\r\n";
  }
  async function signJar(entries, key) {
    const body = entries.filter((e) => !/^META-INF\/(MANIFEST\.MF|.*\.(SF|RSA|DSA|EC))$/i.test(e.name) && !e.name.endsWith("/"));
    let mf = "Manifest-Version: 1.0\r\nCreated-By: 1.0 (Bada Contact Transporter Studio)\r\n\r\n";
    const sections = [];
    for (const e of body) {
      const d = e.data !== undefined ? e.data : await entryData(e);
      const sec = mfLine("Name: " + e.name) + "SHA-256-Digest: " + b64(await sha256(d)) + "\r\n\r\n";
      sections.push([e.name, sec]); mf += sec;
    }
    const mfBytes = enc(mf);
    let sf = "Signature-Version: 1.0\r\nCreated-By: 1.0 (Bada Contact Transporter Studio)\r\nSHA-256-Digest-Manifest: " + b64(await sha256(mfBytes)) + "\r\n";
    sf += "SHA-256-Digest-Manifest-Main-Attributes: " + b64(await sha256(enc("Manifest-Version: 1.0\r\nCreated-By: 1.0 (Bada Contact Transporter Studio)\r\n\r\n"))) + "\r\n\r\n";
    for (const [name, sec] of sections) sf += mfLine("Name: " + name) + "SHA-256-Digest: " + b64(await sha256(enc(sec))) + "\r\n\r\n";
    const sfBytes = enc(sf);
    const k = await subtle().importKey("pkcs8", key.pk8, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
    const sig = new Uint8Array(await subtle().sign("RSASSA-PKCS1-v1_5", k, sfBytes));
    return [
      { name: "META-INF/MANIFEST.MF", data: mfBytes },
      { name: "META-INF/CERT.SF", data: sfBytes },
      { name: "META-INF/CERT.RSA", data: pkcs7(key.cert, sig) },
    ].concat(body);
  }

  // ランナー APK の index.html を差し替えて署名し直す
  async function buildApk(templateApk, html, key) {
    const tpl = readZip(templateApk);
    if (!tpl.some((e) => e.name === "AndroidManifest.xml")) throw new Error("APK のひな形ではありません");
    const page = /cordova\.js/.test(html) ? html : html.replace("</head>", '<script src="cordova.js"></script>\n</head>');
    const entries = [];
    for (const e of tpl) {
      if (/^META-INF\//.test(e.name)) continue;
      if (e.name === "assets/www/index.html") entries.push({ name: e.name, data: enc(page) });
      else entries.push(e);
    }
    return writeZip(await signJar(entries, key), { align: true });
  }

  // ------------------------------------------------------------ tar / ar / .deb
  function tarHeader(name, size, mode, type) {
    const h = new Uint8Array(512);
    const put = (s, at, len) => { const b = enc(s); h.set(b.subarray(0, len), at); };
    const oct = (n, len) => n.toString(8).padStart(len - 1, "0") + "\0";
    put(name, 0, 100); put(oct(mode, 8), 100, 8); put(oct(0, 8), 108, 8); put(oct(0, 8), 116, 8);
    put(oct(size, 12), 124, 12); put(oct(Math.floor(Date.UTC(2026, 0, 1) / 1000), 12), 136, 12);
    h.fill(32, 148, 156); h[156] = type.charCodeAt(0); put("ustar\0", 257, 6); put("00", 263, 2);
    put("root", 265, 32); put("root", 297, 32);
    let sum = 0; for (const b of h) sum += b; put(sum.toString(8).padStart(6, "0") + "\0 ", 148, 8);
    return h;
  }
  // files: [{ path: "./usr/bin/x", data, mode }] — 親ディレクトリは自動で作る
  function tar(files) {
    const parts = [], dirs = new Set();
    for (const f of files) {
      const segs = f.path.split("/");
      for (let i = 1; i < segs.length; i++) {
        const d = segs.slice(0, i).join("/") + "/";
        if (!dirs.has(d)) { dirs.add(d); parts.push(tarHeader(d, 0, 0o755, "5")); }
      }
      const data = typeof f.data === "string" ? enc(f.data) : f.data;
      parts.push(tarHeader(f.path, data.length, f.mode || 0o644, "0"), data, new Uint8Array((512 - (data.length % 512)) % 512));
    }
    parts.push(new Uint8Array(1024));
    return concat(parts);
  }
  function ar(members) {
    const parts = [enc("!<arch>\n")];
    for (const m of members) {
      const hdr = (m.name + "/").padEnd(16) + "0".padEnd(12) + "0".padEnd(6) + "0".padEnd(6) + "100644".padEnd(8) + String(m.data.length).padEnd(10) + "`\n";
      parts.push(enc(hdr), m.data);
      if (m.data.length % 2) parts.push(enc("\n"));
    }
    return concat(parts);
  }
  // opts: { pkg, version, title, description, html, bada: {name, src}, maintainer }
  async function buildDeb(o) {
    const pkg = o.pkg.toLowerCase().replace(/[^a-z0-9+.-]+/g, "-").replace(/^-+|-+$/g, "") || "bada-app";
    const dir = `/usr/share/bada-apps/${pkg}`;
    const launcher = `#!/bin/sh
# ${o.title} — Bada アプリ (論文 PDF から生成) を開く
APP="${dir}/index.html"
for b in chromium chromium-browser google-chrome google-chrome-stable microsoft-edge brave-browser; do
  if command -v "$b" >/dev/null 2>&1; then exec "$b" --app="file://$APP" "$@"; fi
done
if command -v firefox >/dev/null 2>&1; then exec firefox "$APP"; fi
exec xdg-open "$APP"
`;
    const desktop = `[Desktop Entry]
Type=Application
Name=${o.title.replace(/\n/g, " ").slice(0, 60)}
Comment=${(o.description || "").replace(/\n/g, " ").slice(0, 120)}
Exec=/usr/bin/${pkg}
Terminal=false
Categories=Education;Science;
`;
    const files = [
      { path: `.${dir}/index.html`, data: o.html },
      { path: `./usr/bin/${pkg}`, data: launcher, mode: 0o755 },
      { path: `./usr/share/applications/${pkg}.desktop`, data: desktop },
    ];
    if (o.bada) files.push({ path: `.${dir}/${o.bada.name}`, data: o.bada.src });
    if (o.pdf) files.push({ path: `.${dir}/${o.pdf.name}`, data: o.pdf.data });
    const size = Math.ceil(files.reduce((s, f) => s + (typeof f.data === "string" ? enc(f.data).length : f.data.length), 0) / 1024);
    const control = `Package: ${pkg}
Version: ${o.version || "1.0.0"}
Architecture: all
Maintainer: ${o.maintainer || "masaaki-avnturle <masaaki.tabu4@gmail.com>"}
Installed-Size: ${size}
Recommends: xdg-utils, chromium | firefox
Section: science
Priority: optional
Homepage: https://github.com/masaaki-avnturle/Bada
Description: ${o.title.replace(/\n/g, " ").slice(0, 70)}
 ${(o.description || "Bada application").replace(/\n/g, " ")}
 Generated by Contact Transporter Studio (Bada).
`;
    const controlTar = await gzip(tar([{ path: "./control", data: control }]));
    const dataTar = await gzip(tar(files));
    return { pkg, bytes: ar([{ name: "debian-binary", data: enc("2.0\n") }, { name: "control.tar.gz", data: controlTar }, { name: "data.tar.gz", data: dataTar }]) };
  }

  // ------------------------------------------------------------ PDF (JPEG ページ)
  // pages: [{ jpeg: Uint8Array, w: px, h: px }]  → A4 / A3 横など、画像の縦横比に合わせたページ
  function imagePdf(pages, title) {
    const objs = [], add = (s) => { objs.push(s); return objs.length; };
    const catalog = add(null), pagesObj = add(null), kids = [];
    for (const p of pages) {
      const W = p.w > p.h ? 842 : 595, H = Math.round(W * p.h / p.w);
      const img = add({ dict: `<< /Type /XObject /Subtype /Image /Width ${p.w} /Height ${p.h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${p.jpeg.length} >>`, stream: p.jpeg });
      const cs = enc(`q ${W} 0 0 ${H} 0 0 cm /Im0 Do Q`);
      const content = add({ dict: `<< /Length ${cs.length} >>`, stream: cs });
      kids.push(add(`<< /Type /Page /Parent ${pagesObj} 0 R /MediaBox [0 0 ${W} ${H}] /Resources << /XObject << /Im0 ${img} 0 R >> >> /Contents ${content} 0 R >>`));
    }
    objs[catalog - 1] = `<< /Type /Catalog /Pages ${pagesObj} 0 R >>`;
    objs[pagesObj - 1] = `<< /Type /Pages /Kids [${kids.map((k) => k + " 0 R").join(" ")}] /Count ${kids.length} >>`;
    const info = add(`<< /Producer (Bada Contact Transporter Studio) /Title <FEFF${Array.from(String(title || "Bada")).map((c) => c.charCodeAt(0).toString(16).padStart(4, "0")).join("")}> >>`);
    const parts = [enc("%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")], offs = []; let off = parts[0].length;
    objs.forEach((o, i) => {
      offs.push(off);
      const chunk = typeof o === "string" ? [enc(`${i + 1} 0 obj\n${o}\nendobj\n`)] : [enc(`${i + 1} 0 obj\n${o.dict}\nstream\n`), o.stream, enc("\nendstream\nendobj\n")];
      for (const c of chunk) { parts.push(c); off += c.length; }
    });
    let x = `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n`;
    for (const o of offs) x += String(o).padStart(10, "0") + " 00000 n \n";
    x += `trailer\n<< /Size ${objs.length + 1} /Root ${catalog} 0 R /Info ${info} 0 R >>\nstartxref\n${off}\n%%EOF\n`;
    parts.push(enc(x));
    return concat(parts);
  }

  // ------------------------------------------------------------ 単体 HTML アプリ
  // runnerHtml の /*@@PAYLOAD@@*/null を { title, main, files } に置き換える
  function standaloneHtml(runnerHtml, payload) {
    const json = JSON.stringify(payload).replace(/<\/(script)/gi, "<\\/$1").replace(/<!--/g, "<\\!--");
    const k = "/*@@PAYLOAD@@*/null";
    if (!runnerHtml.includes(k)) throw new Error("ランナー HTML ではありません");
    let html = runnerHtml.replace(k, () => json);
    if (payload.title) html = html.replace(/<title>[^<]*<\/title>/, () => `<title>${String(payload.title).replace(/[<&]/g, "")} — Bada</title>`);
    return html;
  }

  const api = { readZip, writeZip, entryData, signJar, buildApk, buildDeb, tar, ar, imagePdf, standaloneHtml, crc32, sha256, b64, unb64, deflateRaw, inflateRaw, gzip, pkcs7 };
  root.CTExport = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
