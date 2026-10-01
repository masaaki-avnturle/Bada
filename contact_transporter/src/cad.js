/*
 * cad.js — 3D CAD カーネル (メッシュ生成・変換・特徴稜線・STL / OBJ / DXF 書き出し)
 *
 * 形状はすべて頂点共有の三角形メッシュ。部品 (Part) = { name, color, mesh } の配列が
 * アセンブリ。ブラウザ (window.CTCad) / Node (module.exports) 両対応。
 */
(function (root) {
  "use strict";

  // ------------------------------------------------------------ vec3
  const v3 = {
    add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
    sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
    mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
    dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
    cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
    len: (a) => Math.hypot(a[0], a[1], a[2]),
    norm: (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; },
  };

  // ------------------------------------------------------------ mat4 (列優先)
  const m4 = {
    ident: () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    mul(a, b) {
      const o = new Array(16);
      for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
        let s = 0; for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k]; o[c * 4 + r] = s;
      }
      return o;
    },
    translate: (x, y, z) => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1],
    scale: (x, y, z) => [x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0, 0, 0, 0, 1],
    rot(axis, ang) {
      const [x, y, z] = v3.norm(axis), c = Math.cos(ang), s = Math.sin(ang), t = 1 - c;
      return [t * x * x + c, t * x * y + s * z, t * x * z - s * y, 0,
        t * x * y - s * z, t * y * y + c, t * y * z + s * x, 0,
        t * x * z + s * y, t * y * z - s * x, t * z * z + c, 0, 0, 0, 0, 1];
    },
    perspective(fovy, aspect, near, far) {
      const f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
      return [f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) * nf, -1, 0, 0, 2 * far * near * nf, 0];
    },
    ortho(l, r, b, t, n, f) {
      return [2 / (r - l), 0, 0, 0, 0, 2 / (t - b), 0, 0, 0, 0, -2 / (f - n), 0,
        -(r + l) / (r - l), -(t + b) / (t - b), -(f + n) / (f - n), 1];
    },
    lookAt(eye, at, up) {
      const z = v3.norm(v3.sub(eye, at)), x = v3.norm(v3.cross(up, z)), y = v3.cross(z, x);
      return [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0,
        -v3.dot(x, eye), -v3.dot(y, eye), -v3.dot(z, eye), 1];
    },
    apply(m, p) {
      return [m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
        m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
        m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]];
    },
    applyDir(m, p) {
      return [m[0] * p[0] + m[4] * p[1] + m[8] * p[2], m[1] * p[0] + m[5] * p[1] + m[9] * p[2], m[2] * p[0] + m[6] * p[1] + m[10] * p[2]];
    },
  };

  // ------------------------------------------------------------ Mesh
  class Mesh {
    constructor(pos, idx) { this.pos = pos || []; this.idx = idx || []; } // pos: [[x,y,z]], idx: [a,b,c,...]
    get triCount() { return this.idx.length / 3; }
    transform(m) { return new Mesh(this.pos.map((p) => m4.apply(m, p)), this.idx.slice()); }
    merge(o) { const off = this.pos.length; return new Mesh(this.pos.concat(o.pos), this.idx.concat(o.idx.map((i) => i + off))); }
    bounds() {
      const mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
      for (const p of this.pos) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], p[k]); mx[k] = Math.max(mx[k], p[k]); }
      return { min: mn, max: mx };
    }
    faceNormal(t) {
      const a = this.pos[this.idx[t * 3]], b = this.pos[this.idx[t * 3 + 1]], c = this.pos[this.idx[t * 3 + 2]];
      return v3.norm(v3.cross(v3.sub(b, a), v3.sub(c, a)));
    }
    vertexNormals() {
      const n = this.pos.map(() => [0, 0, 0]);
      for (let t = 0; t < this.triCount; t++) {
        const a = this.pos[this.idx[t * 3]], b = this.pos[this.idx[t * 3 + 1]], c = this.pos[this.idx[t * 3 + 2]];
        const f = v3.cross(v3.sub(b, a), v3.sub(c, a));
        for (let k = 0; k < 3; k++) { const q = n[this.idx[t * 3 + k]]; q[0] += f[0]; q[1] += f[1]; q[2] += f[2]; }
      }
      return n.map(v3.norm);
    }
    // 稜線 → 隣接面 (ドラフティング用: 特徴稜線 / 輪郭線)
    edgeFaces() {
      if (this._ef) return this._ef;
      const map = new Map(), N = this.pos.length;
      for (let t = 0; t < this.triCount; t++) for (let k = 0; k < 3; k++) {
        const a = this.idx[t * 3 + k], b = this.idx[t * 3 + (k + 1) % 3];
        const key = a < b ? a * N + b : b * N + a;
        let e = map.get(key); if (!e) { e = { a: Math.min(a, b), b: Math.max(a, b), f: [] }; map.set(key, e); }
        e.f.push(t);
      }
      const fn = []; for (let t = 0; t < this.triCount; t++) fn.push(this.faceNormal(t));
      this._ef = { edges: Array.from(map.values()), fn };
      return this._ef;
    }
    // 視線方向 view に対する 輪郭線 + 特徴稜線 (二面角 > creaseDeg)
    outlineEdges(view, creaseDeg) {
      const cosC = Math.cos((creaseDeg == null ? 35 : creaseDeg) * Math.PI / 180);
      const { edges, fn } = this.edgeFaces(), out = [];
      for (const e of edges) {
        if (e.f.length === 1) { out.push([e.a, e.b]); continue; }
        const n1 = fn[e.f[0]], n2 = fn[e.f[1]];
        const s1 = v3.dot(n1, view), s2 = v3.dot(n2, view);
        if ((s1 > 0) !== (s2 > 0) || v3.dot(n1, n2) < cosC) out.push([e.a, e.b]);
      }
      return out;
    }
  }

  // (u,v) グリッドから閉じた/開いたメッシュを作る共通関数
  function grid(nu, nv, fn, wrapU, wrapV) {
    const pos = [], idx = [];
    const cu = wrapU ? nu : nu + 1, cv = wrapV ? nv : nv + 1;
    for (let i = 0; i < cu; i++) for (let j = 0; j < cv; j++) pos.push(fn(i / nu, j / nv));
    const id = (i, j) => (i % cu) * cv + (j % cv);
    for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
      const a = id(i, j), b = id(i + 1, j), c = id(i + 1, j + 1), d = id(i, j + 1);
      idx.push(a, b, c, a, c, d);
    }
    return new Mesh(pos, idx);
  }

  const TAU = Math.PI * 2;
  const shapes = {
    // z 軸まわりのトーラス
    torus(R, r, nu, nv) {
      return grid(nu || 96, nv || 16, (u, v) => {
        const a = u * TAU, b = v * TAU, w = R + r * Math.cos(b);
        return [w * Math.cos(a), w * Math.sin(a), r * Math.sin(b)];
      }, true, true);
    },
    sphere(r, nu, nv) {
      nu = nu || 48; nv = nv || 24;
      return shapes.lathe(Array.from({ length: nv + 1 }, (_, j) => {
        const b = Math.PI * (1 - j / nv) - Math.PI / 2; return [r * Math.cos(b), r * Math.sin(b)];
      }).reverse(), nu);
    },
    // profile: [[radius, z], ...] を z 軸まわりに回転 (半径 0 の点は極として 1 点に縮退)
    lathe(profile, seg) {
      seg = seg || 64;
      const pos = [], idx = [], rings = [];
      for (const [r, z] of profile) {
        if (r <= 1e-9) { rings.push([pos.length]); pos.push([0, 0, z]); continue; }
        const ring = [];
        for (let i = 0; i < seg; i++) { const a = i / seg * TAU; ring.push(pos.length); pos.push([r * Math.cos(a), r * Math.sin(a), z]); }
        rings.push(ring);
      }
      for (let k = 0; k + 1 < rings.length; k++) {
        const A = rings[k], B = rings[k + 1];
        for (let i = 0; i < seg; i++) {
          const i2 = (i + 1) % seg;
          if (A.length === 1 && B.length === 1) continue;
          if (A.length === 1) idx.push(A[0], B[i2], B[i]);
          else if (B.length === 1) idx.push(A[i], A[i2], B[0]);
          else idx.push(A[i], A[i2], B[i2], A[i], B[i2], B[i]);
        }
      }
      // 巻き方向を外向きに揃える (profile を下→上に与えた場合に外向き)
      return new Mesh(pos, idx);
    },
    cylinder(r, h, seg, capped) {
      const prof = capped === false ? [[r, 0], [r, h]] : [[0, 0], [r, 0], [r, h], [0, h]];
      return shapes.lathe(prof, seg || 32);
    },
    cone(r1, r2, h, seg) { return shapes.lathe([[0, 0], [r1, 0], [r2, h], [0, h]], seg || 32); },
    box(sx, sy, sz) {
      const x = sx / 2, y = sy / 2, z = sz / 2;
      const P = [[-x, -y, -z], [x, -y, -z], [x, y, -z], [-x, y, -z], [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z]];
      const F = [0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7];
      return new Mesh(P, F);
    },
    // 空間曲線 c(t), t∈[0,1) に沿った閉じたチューブ (平行移動フレーム)
    tube(curve, r, nu, nv) {
      nu = nu || 240; nv = nv || 12;
      const pts = [], T = [];
      for (let i = 0; i < nu; i++) pts.push(curve(i / nu));
      for (let i = 0; i < nu; i++) T.push(v3.norm(v3.sub(pts[(i + 1) % nu], pts[(i - 1 + nu) % nu])));
      let N = v3.norm(v3.cross(T[0], Math.abs(T[0][2]) < 0.9 ? [0, 0, 1] : [1, 0, 0]));
      const Ns = [];
      for (let i = 0; i < nu; i++) {
        if (i > 0) { N = v3.norm(v3.sub(N, v3.mul(T[i], v3.dot(N, T[i])))); }
        Ns.push(N);
      }
      // 閉曲線の捩れ補正: 一周後のずれ角を全周に分配
      const Nend = v3.norm(v3.sub(Ns[nu - 1], v3.mul(T[0], v3.dot(Ns[nu - 1], T[0]))));
      let tw = Math.acos(Math.max(-1, Math.min(1, v3.dot(Nend, Ns[0]))));
      if (v3.dot(v3.cross(Nend, Ns[0]), T[0]) < 0) tw = -tw;
      return grid(nu, nv, (u, v) => {
        const i = Math.round(u * nu) % nu, t = T[i];
        let n = Ns[i], b = v3.cross(t, n);
        const ang = -v * TAU + tw * u;
        const c = Math.cos(ang), s = Math.sin(ang);
        const p = pts[i];
        return [p[0] + r * (c * n[0] + s * b[0]), p[1] + r * (c * n[1] + s * b[1]), p[2] + r * (c * n[2] + s * b[2])];
      }, true, true);
    },
    // (p,q) トーラス結び目: 3_1 = (2,3), 5_1 = (2,5)
    torusKnot(R, r, p, q, tubeR) {
      return shapes.tube((t) => {
        const a = t * TAU, w = R + r * Math.cos(p * a);
        return [w * Math.cos(q * a), w * Math.sin(q * a), r * Math.sin(p * a)];
      }, tubeR, 360, 12);
    },
    // 4_1 (8 の字結び目) のパラメトリック表示
    figureEight(scale, tubeR) {
      return shapes.tube((t) => {
        const a = t * TAU, w = 2 + Math.cos(2 * a);
        return [scale * w * Math.cos(3 * a), scale * w * Math.sin(3 * a), scale * Math.sin(4 * a)];
      }, tubeR, 360, 12);
    },
  };

  // ------------------------------------------------------------ exporters
  function partsTris(parts) {
    const tris = [];
    for (const p of parts) {
      const m = p.mesh;
      for (let t = 0; t < m.triCount; t++) tris.push([m.pos[m.idx[t * 3]], m.pos[m.idx[t * 3 + 1]], m.pos[m.idx[t * 3 + 2]], m.faceNormal(t)]);
    }
    return tris;
  }
  function toSTLBinary(parts, name) {
    const tris = partsTris(parts);
    const buf = new ArrayBuffer(84 + tris.length * 50), dv = new DataView(buf);
    const head = (name || "Bada CAD").slice(0, 79);
    for (let i = 0; i < head.length; i++) dv.setUint8(i, head.charCodeAt(i) & 0x7f);
    dv.setUint32(80, tris.length, true);
    let o = 84;
    for (const [a, b, c, n] of tris) {
      for (const v of [n, a, b, c]) { dv.setFloat32(o, v[0], true); dv.setFloat32(o + 4, v[1], true); dv.setFloat32(o + 8, v[2], true); o += 12; }
      dv.setUint16(o, 0, true); o += 2;
    }
    return buf;
  }
  function toSTLAscii(parts, name) {
    const f = (x) => x.toExponential(6);
    const L = [`solid ${name || "bada"}`];
    for (const [a, b, c, n] of partsTris(parts)) {
      L.push(` facet normal ${f(n[0])} ${f(n[1])} ${f(n[2])}`, "  outer loop");
      for (const v of [a, b, c]) L.push(`   vertex ${f(v[0])} ${f(v[1])} ${f(v[2])}`);
      L.push("  endloop", " endfacet");
    }
    L.push(`endsolid ${name || "bada"}`);
    return L.join("\n");
  }
  function toOBJ(parts, name) {
    const L = [`# ${name || "Bada CAD"} — generated by Bada Nexus`, "mtllib parts.mtl"];
    let off = 1;
    for (const p of parts) {
      L.push(`o ${p.name.replace(/\s+/g, "_")}`, `usemtl ${p.id || p.name.replace(/\s+/g, "_")}`);
      for (const v of p.mesh.pos) L.push(`v ${v[0].toFixed(4)} ${v[1].toFixed(4)} ${v[2].toFixed(4)}`);
      for (let t = 0; t < p.mesh.triCount; t++) L.push(`f ${p.mesh.idx[t * 3] + off} ${p.mesh.idx[t * 3 + 1] + off} ${p.mesh.idx[t * 3 + 2] + off}`);
      off += p.mesh.pos.length;
    }
    return L.join("\n");
  }
  function toMTL(parts) {
    const L = [];
    for (const p of parts) {
      const c = hexToRgb(p.color);
      L.push(`newmtl ${p.id || p.name.replace(/\s+/g, "_")}`, `Kd ${c.map((x) => (x / 255).toFixed(3)).join(" ")}`, "");
    }
    return L.join("\n");
  }
  // 3D DXF (3DFACE、部品ごとのレイヤ)
  function toDXF3D(parts) {
    const L = ["0", "SECTION", "2", "ENTITIES"];
    for (const p of parts) {
      const layer = (p.id || p.name).replace(/[^A-Za-z0-9_]/g, "_");
      const m = p.mesh;
      for (let t = 0; t < m.triCount; t++) {
        const a = m.pos[m.idx[t * 3]], b = m.pos[m.idx[t * 3 + 1]], c = m.pos[m.idx[t * 3 + 2]];
        L.push("0", "3DFACE", "8", layer);
        [a, b, c, c].forEach((v, k) => L.push(String(10 + k), v[0].toFixed(4), String(20 + k), v[1].toFixed(4), String(30 + k), v[2].toFixed(4)));
      }
    }
    L.push("0", "ENDSEC", "0", "EOF");
    return L.join("\n");
  }
  function hexToRgb(h) {
    const s = h.replace("#", "");
    return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
  }

  const api = { v3, m4, Mesh, shapes, grid, toSTLBinary, toSTLAscii, toOBJ, toMTL, toDXF3D, hexToRgb };
  root.CTCad = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
