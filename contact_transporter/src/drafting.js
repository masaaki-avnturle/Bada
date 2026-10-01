/*
 * drafting.js — 設計図面 (三面図 + 等角図 + 寸法 + 表題欄 + 部材表) 生成
 *
 * アセンブリ (焼き込み済み部品) の輪郭線・特徴稜線を正投影し、A3 横 (420×297 mm) の
 * SVG 図面と 2D DXF を作ります。第三角法: 平面図 (上) / 正面図 (下) / 右側面図 (右)。
 */
(function (root) {
  "use strict";
  const CAD = root.CTCad || (typeof require !== "undefined" ? require("./cad.js") : null);

  const VIEWS = {
    // [視線方向 (モデル→目), 横軸, 縦軸]
    top: { dir: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0], label: "平面図 (TOP)" },
    front: { dir: [0, -1, 0], u: [1, 0, 0], v: [0, 0, 1], label: "正面図 (FRONT)" },
    side: { dir: [1, 0, 0], u: [0, 1, 0], v: [0, 0, 1], label: "右側面図 (RIGHT)" },
    iso: { dir: [1, -1, 0.8], u: [0.7071, 0.7071, 0], v: [-0.3926, 0.3926, 0.8315], label: "等角図 (ISO)" },
  };
  const SCALES = [1, 2, 5, 10, 20, 25, 50, 100, 150, 200, 250, 300, 400, 500, 1000, 1500, 2000, 3000, 5000];

  // 部品ごとに投影線分を作る → { lines: [[x1,y1,x2,y2,color]], bounds }
  function projectView(parts, key, crease) {
    const V = VIEWS[key], dir = CAD.v3.norm(V.dir), u = V.u, v = V.v;
    const lines = []; let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const p of parts) {
      const m = p.mesh, pr = m.pos.map((q) => [CAD.v3.dot(q, u), CAD.v3.dot(q, v)]);
      for (const [a, b] of m.outlineEdges(dir, crease)) {
        const A = pr[a], B = pr[b];
        lines.push([A[0], A[1], B[0], B[1], p.color, p.id]);
        x0 = Math.min(x0, A[0], B[0]); x1 = Math.max(x1, A[0], B[0]);
        y0 = Math.min(y0, A[1], B[1]); y1 = Math.max(y1, A[1], B[1]);
      }
    }
    return { lines, bounds: { x0, y0, x1, y1 } };
  }

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  /*
   * sheet(opts) → { svg, dxf, scale }
   *   opts.parts   焼き込み済み部品
   *   opts.dims    寸法注記 [{view, type:'linear'|'radius', ...}]
   *   opts.title, opts.number, opts.author, opts.date, opts.bom [[no,name,material,qty]], opts.notes [..]
   *   opts.mono    true なら青焼き風 (白線) ではなく黒線
   */
  function sheet(opts) {
    const W = 420, H = 297, M = 10;
    const theme = opts.theme === "paper"
      ? { bg: "#ffffff", ink: "#111111", thin: "#333333", dim: "#c62828", grid: "#e0e0e0", part: false }
      : { bg: "#0b3d91", ink: "#e3f2fd", thin: "#bbdefb", dim: "#ffeb3b", grid: "#1565c0", part: false };
    const crease = opts.crease || 35;
    const views = {};
    for (const k of ["top", "front", "side", "iso"]) views[k] = projectView(opts.parts, k, crease);
    // レイアウト: 左上 top, 左下 front, 右下 side, 右上 iso。右端 110mm は表題欄・部材表
    const cells = {
      top: { x: M + 4, y: M + 4, w: 150, h: 130 },
      front: { x: M + 4, y: M + 140, w: 150, h: 120 },
      side: { x: M + 160, y: M + 140, w: 125, h: 120 },
      iso: { x: M + 160, y: M + 4, w: 125, h: 130 },
    };
    // 共通尺度 (平面・正面・側面で同一)
    const need = (k) => {
      const b = views[k].bounds, c = cells[k];
      return Math.max((b.x1 - b.x0) * 1000 / (c.w - 22), (b.y1 - b.y0) * 1000 / (c.h - 22));
    };
    const req = Math.max(need("top"), need("front"), need("side"));
    const scale = SCALES.find((s) => s >= req) || Math.ceil(req);
    const isoReq = need("iso"), isoScale = SCALES.find((s) => s >= isoReq) || Math.ceil(isoReq);
    const k = 1000 / scale; // m → mm (紙面)
    const out = [], dxf = [];
    out.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}mm" height="${H}mm" font-family="'Noto Sans JP','Hiragino Sans','Yu Gothic',sans-serif">`);
    out.push(`<rect width="${W}" height="${H}" fill="${theme.bg}"/>`);
    // 方眼
    let g = ""; for (let x = M; x <= W - M; x += 10) g += `M${x} ${M}V${H - M}`; for (let y = M; y <= H - M; y += 10) g += `M${M} ${y}H${W - M}`;
    out.push(`<path d="${g}" stroke="${theme.grid}" stroke-width="0.12" fill="none"/>`);
    out.push(`<rect x="${M}" y="${M}" width="${W - 2 * M}" height="${H - 2 * M}" fill="none" stroke="${theme.ink}" stroke-width="0.7"/>`);

    const place = (key, sc) => {
      const b = views[key].bounds, c = cells[key], kk = 1000 / sc;
      const cx = c.x + c.w / 2, cy = c.y + c.h / 2 + 4;
      const mx = (b.x0 + b.x1) / 2, my = (b.y0 + b.y1) / 2;
      return { tx: (x) => cx + (x - mx) * kk, ty: (y) => cy - (y - my) * kk, k: kk };
    };
    const layout = {};
    for (const key of Object.keys(views)) {
      const sc = key === "iso" ? isoScale : scale, P = place(key, sc), c = cells[key];
      layout[key] = P;
      out.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" fill="none" stroke="${theme.thin}" stroke-width="0.25" stroke-dasharray="2 1.5"/>`);
      out.push(`<text x="${c.x + 3}" y="${c.y + 6}" font-size="4" fill="${theme.ink}">${esc(VIEWS[key].label)}  1:${sc}</text>`);
      // 部品色ごとにパスをまとめる
      const byColor = new Map();
      for (const [x1, y1, x2, y2, col] of views[key].lines) {
        const d = `M${P.tx(x1).toFixed(2)} ${P.ty(y1).toFixed(2)}L${P.tx(x2).toFixed(2)} ${P.ty(y2).toFixed(2)}`;
        const cc = opts.colorLines ? col : theme.ink;
        byColor.set(cc, (byColor.get(cc) || "") + d);
        dxf.push(["LINE", key.toUpperCase(), P.tx(x1), H - P.ty(y1), P.tx(x2), H - P.ty(y2)]);
      }
      for (const [cc, d] of byColor) out.push(`<path d="${d}" stroke="${cc}" stroke-width="0.22" fill="none" stroke-linecap="round"/>`);
      // 中心線
      if (key !== "iso") {
        const x0 = P.tx(0), y0 = P.ty(0);
        out.push(`<path d="M${x0} ${c.y + 9}V${c.y + c.h - 2}${key === "top" ? `M${c.x + 2} ${y0}H${c.x + c.w - 2}` : ""}" stroke="${theme.dim}" stroke-width="0.18" stroke-dasharray="6 1.5 1 1.5" fill="none"/>`);
      }
    }
    // 寸法
    for (const dm of opts.dims || []) {
      const P = layout[dm.view]; if (!P) continue;
      if (dm.type === "linear") {
        const ax = P.tx(dm.a[0]), ay = P.ty(dm.a[1]), bx = P.tx(dm.b[0]), by = P.ty(dm.b[1]);
        const vert = Math.abs(ax - bx) < Math.abs(ay - by), o = (dm.off || 0) * P.k;
        let d, tx, ty, rot;
        if (vert) {
          const x = ax + o;
          d = `M${ax} ${ay}H${x + Math.sign(o || 1) * 1.5}M${bx} ${by}H${x + Math.sign(o || 1) * 1.5}M${x} ${ay}V${by}`;
          tx = x - 1.2; ty = (ay + by) / 2; rot = -90;
          out.push(arrow(x, ay, x, by, theme.dim), arrow(x, by, x, ay, theme.dim));
        } else {
          const y = ay - o;
          d = `M${ax} ${ay}V${y - Math.sign(o || 1) * 1.5}M${bx} ${by}V${y - Math.sign(o || 1) * 1.5}M${ax} ${y}H${bx}`;
          tx = (ax + bx) / 2; ty = y - 1.2; rot = 0;
          out.push(arrow(ax, y, bx, y, theme.dim), arrow(bx, y, ax, y, theme.dim));
        }
        out.push(`<path d="${d}" stroke="${theme.dim}" stroke-width="0.2" fill="none"/>`);
        out.push(`<text x="${tx}" y="${ty}" font-size="3.2" fill="${theme.dim}" text-anchor="middle" transform="rotate(${rot} ${tx} ${ty})">${esc(dm.text)}</text>`);
        dxf.push(["TEXT", "DIM", tx, H - ty, dm.text]);
      } else if (dm.type === "radius") {
        const cx = P.tx(dm.c[0]), cy = P.ty(dm.c[1]), a = dm.ang * Math.PI / 180;
        const ex = P.tx(dm.c[0] + dm.r * Math.cos(a)), ey = P.ty(dm.c[1] + dm.r * Math.sin(a));
        const lx = ex + 10 * Math.cos(a), ly = ey - 10 * Math.sin(a);
        out.push(`<path d="M${cx} ${cy}L${lx} ${ly}H${lx + (Math.cos(a) >= 0 ? 12 : -12)}" stroke="${theme.dim}" stroke-width="0.2" fill="none"/>`, arrow(cx, cy, ex, ey, theme.dim));
        out.push(`<text x="${lx + (Math.cos(a) >= 0 ? 1 : -1)}" y="${ly - 1}" font-size="3.2" fill="${theme.dim}" text-anchor="${Math.cos(a) >= 0 ? "start" : "end"}">${esc(dm.text)}</text>`);
        dxf.push(["TEXT", "DIM", lx, H - ly, dm.text]);
      }
    }
    // 表題欄 + 部材表 + 注記 (右端)
    const tbx = M + 290, tbw = W - M - tbx;
    let y = M + 4;
    const row = (label, val, h) => {
      h = h || 8;
      out.push(`<rect x="${tbx}" y="${y}" width="${tbw}" height="${h}" fill="none" stroke="${theme.ink}" stroke-width="0.3"/>`);
      out.push(`<text x="${tbx + 2}" y="${y + 3.2}" font-size="2.4" fill="${theme.thin}">${esc(label)}</text>`);
      out.push(`<text x="${tbx + 2}" y="${y + h - 1.6}" font-size="${h > 8 ? 5 : 3.4}" fill="${theme.ink}" font-weight="${h > 8 ? 700 : 400}">${esc(val)}</text>`);
      dxf.push(["TEXT", "TITLE", tbx + 2, H - (y + h - 1.6), `${label}: ${val}`]);
      y += h;
    };
    row("図面名 TITLE", opts.title || "設計図", 14);
    row("図番 DWG No.", opts.number || "CT-0001");
    row("尺度 SCALE", `1:${scale}  (等角図 1:${isoScale})  単位 m`);
    row("投影法", "第三角法");
    row("設計 DESIGNED BY", opts.author || "Bada Nexus");
    row("日付 DATE", opts.date || new Date().toISOString().slice(0, 10));
    y += 3;
    if (opts.bom && opts.bom.length) {
      out.push(`<text x="${tbx}" y="${y + 3}" font-size="3" fill="${theme.ink}" font-weight="700">部材表 BOM</text>`); y += 5;
      for (const r of opts.bom) {
        out.push(`<text x="${tbx + 1}" y="${y + 3}" font-size="2.3" fill="${theme.ink}">${esc(r[0])}. ${esc(r[1])}</text>`);
        out.push(`<text x="${tbx + tbw - 1}" y="${y + 3}" font-size="2.3" fill="${theme.ink}" text-anchor="end">×${esc(r[3])}</text>`);
        out.push(`<text x="${tbx + 4}" y="${y + 6}" font-size="2.1" fill="${theme.thin}">${esc(r[2])}</text>`);
        out.push(`<path d="M${tbx} ${y + 7.4}H${tbx + tbw}" stroke="${theme.thin}" stroke-width="0.15"/>`);
        y += 7.6;
      }
      y += 2;
    }
    if (opts.notes && opts.notes.length) {
      out.push(`<text x="${tbx}" y="${y + 3}" font-size="3" fill="${theme.ink}" font-weight="700">注記 NOTES</text>`); y += 5;
      for (const n of opts.notes) {
        for (const ln of wrap(n, 30)) {
          if (y > H - M - 4) break;
          out.push(`<text x="${tbx + 1}" y="${y + 3}" font-size="2.2" fill="${theme.ink}">${esc(ln)}</text>`); y += 3.2;
        }
        y += 0.8;
      }
    }
    out.push("</svg>");
    return { svg: out.join("\n"), dxf: toDXF2D(dxf, W, H), scale, isoScale };
  }

  function arrow(x1, y1, x2, y2, col) { // x2,y2 に矢じり
    const a = Math.atan2(y2 - y1, x2 - x1), L = 2, w = 0.6;
    const p1 = [x2 - L * Math.cos(a) + w * Math.sin(a), y2 - L * Math.sin(a) - w * Math.cos(a)];
    const p2 = [x2 - L * Math.cos(a) - w * Math.sin(a), y2 - L * Math.sin(a) + w * Math.cos(a)];
    return `<path d="M${x2} ${y2}L${p1[0]} ${p1[1]}L${p2[0]} ${p2[1]}Z" fill="${col}"/>`;
  }
  function wrap(s, n) {
    const out = []; let cur = "", w = 0;
    for (const ch of Array.from(s)) {
      const cw = /[　-鿿＀-￯]/.test(ch) ? 2 : 1;
      if (w + cw > n * 2 && cur) { out.push(cur); cur = ""; w = 0; }
      cur += ch; w += cw;
    }
    if (cur) out.push(cur);
    return out;
  }
  // 2D DXF (R12 互換: LINE / TEXT、レイヤ = ビュー名)
  function toDXF2D(items, W, H) {
    const L = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "9", "$EXTMIN", "10", "0", "20", "0", "9", "$EXTMAX", "10", String(W), "20", String(H), "0", "ENDSEC",
      "0", "SECTION", "2", "ENTITIES"];
    for (const it of items) {
      if (it[0] === "LINE") L.push("0", "LINE", "8", it[1], "10", it[2].toFixed(3), "20", it[3].toFixed(3), "30", "0", "11", it[4].toFixed(3), "21", it[5].toFixed(3), "31", "0");
      else L.push("0", "TEXT", "8", it[1], "10", it[2].toFixed(3), "20", it[3].toFixed(3), "30", "0", "40", "3", "1", String(it[4]));
    }
    L.push("0", "ENDSEC", "0", "EOF");
    return L.join("\n");
  }

  const api = { sheet, projectView, VIEWS, SCALES };
  root.CTDraft = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
