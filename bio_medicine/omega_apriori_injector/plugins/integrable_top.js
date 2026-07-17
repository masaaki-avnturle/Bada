/*
 * plugins/integrable_top.js — 複素回転体における相対論的コマの可積分系エラー修正
 *
 * 剛体回転(オイラーのコマ)は可積分系で、保存量 E=½Σ I_k ω_k² と |L|²=Σ(I_k ω_k)² を持つ。
 * 複素回転体(四元数 ≒ SU(2))上で姿勢を表現し、ノイズの乗った姿勢/角速度系列を
 *   ① 四元数ノルムを 1 へ射影(正規化)
 *   ② 角速度を保存量 |L|² の等位集合へ射影(可積分トーラスへ復元)
 *   ③ オイラー方程式の1ステップ予測と SLERP 融合(相補フィルタ的 誤り訂正)
 *   ④ 特殊相対論: ボーストを虚数角回転(ラピディティ φ=atanh(v/c))として扱い Thomas 歳差を補正
 *   ⑤ 未知事前エンジンAIで訂正の信頼度(blend)を学習的に重み付け
 * によって誤り訂正する。
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";

  // ---- 四元数演算 [w,x,y,z] ----
  function qmul(a, b) {
    return [
      a[0]*b[0]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3],
      a[0]*b[1]+a[1]*b[0]+a[2]*b[3]-a[3]*b[2],
      a[0]*b[2]-a[1]*b[3]+a[2]*b[0]+a[3]*b[1],
      a[0]*b[3]+a[1]*b[2]-a[2]*b[1]+a[3]*b[0]
    ];
  }
  function qnorm(q) { var n = Math.hypot(q[0], q[1], q[2], q[3]) || 1; return [q[0]/n, q[1]/n, q[2]/n, q[3]/n]; }
  function qdot(a, b) { return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3]; }
  function qangle(a, b) { return 2 * Math.acos(Math.min(1, Math.abs(qdot(qnorm(a), qnorm(b))))); }
  function slerp(a, b, t) {
    a = qnorm(a); b = qnorm(b);
    var d = qdot(a, b); if (d < 0) { b = b.map(function (x) { return -x; }); d = -d; }
    if (d > 0.9995) return qnorm(a.map(function (x, i) { return x + t * (b[i] - x); }));
    var th = Math.acos(d), s = Math.sin(th);
    var k0 = Math.sin((1 - t) * th) / s, k1 = Math.sin(t * th) / s;
    return [a[0]*k0+b[0]*k1, a[1]*k0+b[1]*k1, a[2]*k0+b[2]*k1, a[3]*k0+b[3]*k1];
  }

  // ---- 可積分系: オイラーのコマ ----
  function energy(I, w) { return 0.5 * (I[0]*w[0]*w[0] + I[1]*w[1]*w[1] + I[2]*w[2]*w[2]); }
  function angMom2(I, w) { var a=I[0]*w[0], b=I[1]*w[1], c=I[2]*w[2]; return a*a+b*b+c*c; }
  // オイラー方程式 1ステップ(前進): I_k ω_k' = (I_{k+1}-I_{k+2}) ω_{k+1} ω_{k+2}
  function eulerStep(I, w, dt) {
    var d0 = (I[1]-I[2])/I[0]*w[1]*w[2];
    var d1 = (I[2]-I[0])/I[1]*w[2]*w[0];
    var d2 = (I[0]-I[1])/I[2]*w[0]*w[1];
    return [w[0]+d0*dt, w[1]+d1*dt, w[2]+d2*dt];
  }
  // 角速度を保存量 |L|² の等位集合へ射影(可積分トーラス復元)
  function restoreL(I, w, L0) {
    var L2 = angMom2(I, w); if (L2 <= 0) return w; var s = Math.sqrt(L0 / L2);
    return [w[0]*s, w[1]*s, w[2]*s];
  }
  // 姿勢四元数の運動学: q' = ½ q ⊗ (0,ω)
  function propagate(q, w, dt) {
    var qd = qmul(q, [0, w[0], w[1], w[2]]).map(function (x) { return 0.5 * x; });
    return qnorm([q[0]+qd[0]*dt, q[1]+qd[1]*dt, q[2]+qd[2]*dt, q[3]+qd[3]*dt]);
  }
  // 特殊相対論: ボースト=虚数角回転。Thomas 歳差を |ω| 軸まわりの小回転で補正
  function thomas(q, w, v) {
    if (!v || v <= 0) return q;
    var b = Math.min(0.999999, v);            // v/c
    var gamma = 1 / Math.sqrt(1 - b*b);        // ローレンツ因子
    // rapidity φ = atanh(b)  (boost = rotation by imaginary angle i·φ)
    var phi = Math.atanh(b);
    var wn = Math.hypot(w[0], w[1], w[2]) || 1;
    var th = (gamma - 1) * 0.5 * phi;          // Thomas歳差角(簡略)
    var ax = [w[0]/wn, w[1]/wn, w[2]/wn], s = Math.sin(th/2);
    var rot = [Math.cos(th/2), ax[0]*s, ax[1]*s, ax[2]*s];
    return qnorm(qmul(rot, q));
  }

  var plugin = {
    name: "integrable_top",
    description: "複素回転体における相対論的コマの可積分系エラー修正",
    // run(engine, states, opt)
    //   states: ノイズを含む姿勢四元数列 [[w,x,y,z],...]
    //   opt: {omega:[wx,wy,wz], inertia:[I1,I2,I3], dt, velocity(=v/c), ai:true}
    run: function (engine, states, opt) {
      opt = opt || {};
      var I = opt.inertia || [2, 1, 1.5];
      var dt = opt.dt || 0.05;
      var w = (opt.omega || [1.0, 0.3, 0.2]).slice();
      var v = opt.velocity || 0;
      var useAI = opt.ai !== false;
      var L0 = angMom2(I, w), E0 = energy(I, w);
      var im = (1 << engine.cfg.inbits) - 1, om = (1 << engine.cfg.outbits) - 1;

      var corrected = [], errBefore = 0, errAfter = 0, ldriftBefore = 0, ldriftAfter = 0;
      var q = qnorm(states[0]);
      corrected.push(q);
      for (var n = 1; n < states.length; n++) {
        var obs = states[n];
        // 予測(可積分系)
        w = eulerStep(I, w, dt);
        ldriftBefore += Math.abs(angMom2(I, w) - L0);
        w = restoreL(I, w, L0);                       // ② 保存量へ射影
        ldriftAfter += Math.abs(angMom2(I, w) - L0);
        var pred = propagate(q, w, dt);               // ③ 予測姿勢
        pred = thomas(pred, w, v);                    // ④ 相対論補正

        // 観測の誤差(予測との測地角)
        var err = qangle(obs, pred); errBefore += qangle(qnorm(obs), pred);
        // ⑤ AIで信頼度(blend)を決定: 誤差を量子化してエンジン推論
        var blend = 0.5;
        if (useAI) {
          var code = Math.round((err / Math.PI) * im) & im;
          blend = 0.3 + 0.6 * (engine.infer(code) & om) / (om || 1); // 0.3..0.9
        }
        // 観測(正規化)と予測を SLERP 融合 = 誤り訂正
        var fixed = slerp(qnorm(obs), pred, blend);   // ① 正規化込み
        errAfter += qangle(fixed, pred);
        corrected.push(fixed);
        q = fixed;
      }
      var N = states.length - 1 || 1;
      return {
        corrected: corrected,
        invariants: { E0: E0, L0: L0 },
        error_geodesic_before: Math.round(errBefore / N * 1e4) / 1e4,
        error_geodesic_after:  Math.round(errAfter  / N * 1e4) / 1e4,
        L2_drift_before: Math.round(ldriftBefore / N * 1e4) / 1e4,
        L2_drift_after:  Math.round(ldriftAfter  / N * 1e4) / 1e4,
        relativistic: v > 0 ? { v_over_c: v, gamma: 1/Math.sqrt(1-v*v), rapidity: Math.atanh(Math.min(.999999,v)) } : null,
        summary: "可積分系エラー修正: 測地誤差 " +
          Math.round(errBefore/N*1e3)/1e3 + " → " + Math.round(errAfter/N*1e3)/1e3 +
          " | |L|²ドリフト " + Math.round(ldriftBefore/N*1e3)/1e3 + " → " + Math.round(ldriftAfter/N*1e3)/1e3 +
          (v > 0 ? " | γ=" + (Math.round(1/Math.sqrt(1-v*v)*1e3)/1e3) : "")
      };
    }
  };

  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).integrable_top = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
