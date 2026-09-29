/*
 * viewer.js — WebGL 3D ビューア (オービット操作・影付き陰影・ワイヤ・地面グリッド)
 *
 *   const v = new CTViewer(canvas);
 *   v.setParts(parts)          // { id, color, mesh, matrix } — mesh は初回だけ GPU へ転送
 *   v.setMatrices(parts)       // アニメーション: 行列だけ更新
 *   v.frame(bounds)            // カメラを合わせる
 *   v.screenshot() → dataURL
 */
(function (root) {
  "use strict";
  const CAD = root.CTCad;
  const { m4, v3 } = CAD;

  const VS = `
attribute vec3 aPos; attribute vec3 aNor;
uniform mat4 uProj, uView, uModel;
varying vec3 vN; varying vec3 vW;
void main(){
  vec4 w = uModel * vec4(aPos,1.0);
  vW = w.xyz;
  vN = mat3(uModel) * aNor;
  gl_Position = uProj * uView * w;
}`;
  const FS = `
precision mediump float;
uniform vec3 uColor; uniform vec3 uEye; uniform float uAlpha; uniform float uBlue;
varying vec3 vN; varying vec3 vW;
void main(){
  vec3 n = normalize(vN);
  vec3 vdir = normalize(uEye - vW);
  if (dot(n, vdir) < 0.0) n = -n;
  vec3 L1 = normalize(vec3(0.5, -0.6, 0.9)), L2 = normalize(vec3(-0.7, 0.4, 0.3));
  float d = max(dot(n,L1),0.0)*0.75 + max(dot(n,L2),0.0)*0.25;
  vec3 h = normalize(L1 + vdir);
  float s = pow(max(dot(n,h),0.0), 40.0) * 0.35;
  float rim = pow(1.0 - max(dot(n, vdir), 0.0), 3.0) * 0.35;
  vec3 c = uColor * (0.28 + d) + vec3(s) + rim * vec3(0.4,0.7,1.0);
  if (uBlue > 0.5) { float g = dot(c, vec3(0.3,0.5,0.2)); c = mix(vec3(0.05,0.2,0.55), vec3(0.85,0.95,1.0), g); }
  gl_FragColor = vec4(c, uAlpha);
}`;
  const LVS = `attribute vec3 aPos; uniform mat4 uProj, uView; void main(){ gl_Position = uProj*uView*vec4(aPos,1.0); }`;
  const LFS = `precision mediump float; uniform vec4 uColor; void main(){ gl_FragColor = uColor; }`;

  function compile(gl, vs, fs) {
    const p = gl.createProgram();
    for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      gl.attachShader(p, s);
    }
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }

  class CTViewer {
    constructor(canvas, opts) {
      this.canvas = canvas;
      this.opts = Object.assign({ background: [0.03, 0.05, 0.1, 1], grid: 200, gridStep: 10 }, opts || {});
      const gl = canvas.getContext("webgl", { antialias: true, preserveDrawingBuffer: true })
        || canvas.getContext("experimental-webgl");
      if (!gl) throw new Error("WebGL が利用できません");
      this.gl = gl;
      this.ext32 = gl.getExtension("OES_element_index_uint");
      this.prog = compile(gl, VS, FS);
      this.lprog = compile(gl, LVS, LFS);
      this.buffers = new Map();
      this.parts = [];
      this.yaw = -0.7; this.pitch = 0.45; this.dist = 300; this.target = [0, 0, 40];
      this.wire = false; this.blueprint = false; this.showGrid = true; this.selected = null;
      this.extraLines = [];
      this._bindControls();
      this._ro = new ResizeObserver(() => this.draw());
      this._ro.observe(canvas);
    }

    setParts(parts) {
      const gl = this.gl;
      this.parts = parts;
      for (const p of parts) {
        if (this.buffers.has(p.mesh)) continue;
        const m = p.mesh, nor = m.vertexNormals();
        const pos = new Float32Array(m.pos.length * 3), nn = new Float32Array(m.pos.length * 3);
        m.pos.forEach((q, i) => { pos.set(q, i * 3); nn.set(nor[i], i * 3); });
        const big = m.pos.length > 65535;
        const idx = big ? new Uint32Array(m.idx) : new Uint16Array(m.idx);
        // ワイヤ用の稜線インデックス
        const eset = [];
        for (let t = 0; t < m.idx.length; t += 3) eset.push(m.idx[t], m.idx[t + 1], m.idx[t + 1], m.idx[t + 2]);
        const eidx = big ? new Uint32Array(eset) : new Uint16Array(eset);
        const b = {
          pos: gl.createBuffer(), nor: gl.createBuffer(), idx: gl.createBuffer(), eidx: gl.createBuffer(),
          n: idx.length, en: eidx.length, type: big ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT,
        };
        gl.bindBuffer(gl.ARRAY_BUFFER, b.pos); gl.bufferData(gl.ARRAY_BUFFER, pos, gl.STATIC_DRAW);
        gl.bindBuffer(gl.ARRAY_BUFFER, b.nor); gl.bufferData(gl.ARRAY_BUFFER, nn, gl.STATIC_DRAW);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, b.idx); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, b.eidx); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, eidx, gl.STATIC_DRAW);
        this.buffers.set(p.mesh, b);
      }
      // 使われなくなったバッファを解放
      const live = new Set(parts.map((p) => p.mesh));
      for (const [mesh, b] of this.buffers) if (!live.has(mesh)) {
        for (const k of ["pos", "nor", "idx", "eidx"]) gl.deleteBuffer(b[k]);
        this.buffers.delete(mesh);
      }
      this.draw();
    }

    frame(bounds, keepAngles) {
      const c = [0, 1, 2].map((k) => (bounds.min[k] + bounds.max[k]) / 2);
      const r = Math.hypot(bounds.max[0] - bounds.min[0], bounds.max[1] - bounds.min[1], bounds.max[2] - bounds.min[2]) / 2;
      this.target = c; this.dist = r * 2.4;
      this.opts.grid = Math.max(20, Math.ceil(r * 1.4 / 10) * 10);
      this.opts.gridStep = Math.pow(10, Math.floor(Math.log10(r / 2)));
      if (!keepAngles) { this.yaw = -0.7; this.pitch = 0.45; }
      this.draw();
    }
    setView(name) {
      const V = { iso: [-0.7, 0.45], top: [0, 1.5607], front: [0, 0.0], side: [Math.PI / 2, 0.0] }[name];
      if (V) { this.yaw = V[0]; this.pitch = V[1]; this.draw(); }
    }

    eye() {
      const cp = Math.cos(this.pitch);
      return [this.target[0] + this.dist * cp * Math.sin(this.yaw), this.target[1] - this.dist * cp * Math.cos(this.yaw), this.target[2] + this.dist * Math.sin(this.pitch)];
    }

    draw() {
      if (this._raf) return;
      this._raf = requestAnimationFrame(() => { this._raf = 0; this._draw(); });
    }
    _draw() {
      const gl = this.gl, cv = this.canvas, dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.max(1, Math.round(cv.clientWidth * dpr)), h = Math.max(1, Math.round(cv.clientHeight * dpr));
      if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
      gl.viewport(0, 0, w, h);
      const bg = this.blueprint ? [0.04, 0.2, 0.5, 1] : this.opts.background;
      gl.clearColor(bg[0], bg[1], bg[2], bg[3]);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST);
      const eye = this.eye();
      const proj = m4.perspective(45 * Math.PI / 180, w / h, this.dist * 0.01, this.dist * 20);
      const view = m4.lookAt(eye, this.target, [0, 0, 1]);
      this._pv = { proj, view, w, h };

      // グリッド
      const lines = [];
      if (this.showGrid) {
        const G = this.opts.grid, s = this.opts.gridStep;
        for (let x = -G; x <= G + 1e-9; x += s) lines.push([x, -G, 0, x, G, 0]);
        for (let y = -G; y <= G + 1e-9; y += s) lines.push([-G, y, 0, G, y, 0]);
        this._lines(lines, this.blueprint ? [0.6, 0.8, 1, 0.25] : [0.3, 0.45, 0.7, 0.35], proj, view);
        this._lines([[0, 0, 0, G, 0, 0]], [1, 0.3, 0.3, 0.9], proj, view);
        this._lines([[0, 0, 0, 0, G, 0]], [0.3, 1, 0.3, 0.9], proj, view);
        this._lines([[0, 0, 0, 0, 0, G]], [0.3, 0.6, 1, 0.9], proj, view);
      }
      for (const L of this.extraLines) this._lines(L.segs, L.color, proj, view);

      gl.useProgram(this.prog);
      const P = this.prog, loc = (n) => gl.getUniformLocation(P, n);
      gl.uniformMatrix4fv(loc("uProj"), false, proj);
      gl.uniformMatrix4fv(loc("uView"), false, view);
      gl.uniform3fv(loc("uEye"), eye);
      gl.uniform1f(loc("uBlue"), this.blueprint ? 1 : 0);
      const aPos = gl.getAttribLocation(P, "aPos"), aNor = gl.getAttribLocation(P, "aNor");
      gl.enableVertexAttribArray(aPos); gl.enableVertexAttribArray(aNor);
      const I = m4.ident();
      for (const p of this.parts) {
        if (p.hidden) continue;
        const b = this.buffers.get(p.mesh); if (!b) continue;
        gl.bindBuffer(gl.ARRAY_BUFFER, b.pos); gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, b.nor); gl.vertexAttribPointer(aNor, 3, gl.FLOAT, false, 0, 0);
        gl.uniformMatrix4fv(loc("uModel"), false, p.matrix || I);
        const col = CAD.hexToRgb(p.color).map((x) => x / 255);
        const sel = this.selected && (p.id === this.selected || p.id.startsWith(this.selected));
        gl.uniform3fv(loc("uColor"), sel ? [1, 1, 0.3] : col);
        const glass = p.id === "dome";
        gl.uniform1f(loc("uAlpha"), glass ? 0.55 : 1);
        if (glass) { gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false); }
        if (this.wire) {
          gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, b.eidx); gl.drawElements(gl.LINES, b.en, b.type, 0);
        } else {
          gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, b.idx); gl.drawElements(gl.TRIANGLES, b.n, b.type, 0);
        }
        if (glass) { gl.disable(gl.BLEND); gl.depthMask(true); }
      }
      gl.disableVertexAttribArray(aNor);
      if (this.onDraw) this.onDraw();
    }
    _lines(segs, color, proj, view) {
      if (!segs.length) return;
      const gl = this.gl;
      gl.useProgram(this.lprog);
      const buf = this._lbuf || (this._lbuf = gl.createBuffer());
      const arr = new Float32Array(segs.length * 6); segs.forEach((s, i) => arr.set(s, i * 6));
      gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, arr, gl.DYNAMIC_DRAW);
      const a = gl.getAttribLocation(this.lprog, "aPos");
      gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 3, gl.FLOAT, false, 0, 0);
      gl.uniformMatrix4fv(gl.getUniformLocation(this.lprog, "uProj"), false, proj);
      gl.uniformMatrix4fv(gl.getUniformLocation(this.lprog, "uView"), false, view);
      gl.uniform4fv(gl.getUniformLocation(this.lprog, "uColor"), color);
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.drawArrays(gl.LINES, 0, segs.length * 2);
      gl.disable(gl.BLEND);
    }
    // ワールド座標 → 画面 (CSS px)
    project(p) {
      if (!this._pv) return null;
      const { proj, view } = this._pv;
      const c = m4.apply(view, p);
      const x = proj[0] * c[0] + proj[8] * c[2], y = proj[5] * c[1] + proj[9] * c[2], w = -c[2];
      if (w <= 0) return null;
      return [(x / w * 0.5 + 0.5) * this.canvas.clientWidth, (1 - (y / w * 0.5 + 0.5)) * this.canvas.clientHeight];
    }
    screenshot() { this._draw(); return this.canvas.toDataURL("image/png"); }

    _bindControls() {
      const cv = this.canvas, pts = new Map();
      let last = null, pinch = null;
      cv.style.touchAction = "none";
      cv.addEventListener("pointerdown", (e) => { cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY, e.button, e.shiftKey]); last = null; });
      const up = (e) => { pts.delete(e.pointerId); pinch = null; last = null; };
      cv.addEventListener("pointerup", up); cv.addEventListener("pointercancel", up);
      cv.addEventListener("pointermove", (e) => {
        if (!pts.has(e.pointerId)) return;
        const p = pts.get(e.pointerId); p[0] = e.clientX; p[1] = e.clientY;
        if (pts.size === 2) {
          const [a, b] = Array.from(pts.values()), d = Math.hypot(a[0] - b[0], a[1] - b[1]);
          if (pinch) this.dist *= pinch / d;
          pinch = d; this.draw(); return;
        }
        if (last) {
          const dx = e.clientX - last[0], dy = e.clientY - last[1];
          if (p[2] === 2 || p[2] === 1 || p[3]) this._pan(dx, dy);
          else { this.yaw -= dx * 0.008; this.pitch = Math.max(-1.55, Math.min(1.56, this.pitch + dy * 0.008)); }
          this.draw();
        }
        last = [e.clientX, e.clientY];
      });
      cv.addEventListener("wheel", (e) => { e.preventDefault(); this.dist *= Math.exp(e.deltaY * 0.001); this.draw(); }, { passive: false });
      cv.addEventListener("contextmenu", (e) => e.preventDefault());
    }
    _pan(dx, dy) {
      const eye = this.eye(), f = v3.norm(v3.sub(this.target, eye)), r = v3.norm(v3.cross(f, [0, 0, 1])), u = v3.cross(r, f);
      const k = this.dist * 0.0015;
      this.target = v3.add(this.target, v3.add(v3.mul(r, -dx * k), v3.mul(u, dy * k)));
    }
  }

  root.CTViewer = CTViewer;
})(typeof window !== "undefined" ? window : globalThis);
