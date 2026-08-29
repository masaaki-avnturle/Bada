/*
 * dsp.js — 音色リストア (Sound Restore Studio) の信号処理コア
 *
 * 変調(ボイスチェンジ / ピッチ・音色改変)された 声・楽器 の録音を、
 * 逆変換して元の質音に近づけるための純粋関数群。
 *
 * UMD: ブラウザ(Cordova/Android WebView 含む)では <script src="dsp.js"> で
 * グローバル `VRDSP` を生やし、Node からは default import で使える。
 * すべて Float32Array / Float64Array 上で完結し Web Audio API に依存しない
 * ので単体テストが可能。
 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api; // Node (CommonJS)
  if (root) root.VRDSP = api;                                                // ブラウザ global
})(typeof self !== "undefined" ? self : (typeof globalThis !== "undefined" ? globalThis : this), function () {
  "use strict";

  // -------------------------------------------------------------------------
  // 基本ユーティリティ
  // -------------------------------------------------------------------------

  /** ハン窓を生成 */
  function hann(n) {
    const w = new Float64Array(n);
    for (let i = 0; i < n; i++) w[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / n);
    return w;
  }

  /** 反復基数2 FFT(in-place)。inverse=true で逆変換(1/n 正規化つき)。長さは2の冪。 */
  function fft(re, im, inverse) {
    const n = re.length;
    for (let i = 1, j = 0; i < n; i++) {
      let bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) {
        const tr = re[i]; re[i] = re[j]; re[j] = tr;
        const ti = im[i]; im[i] = im[j]; im[j] = ti;
      }
    }
    for (let len = 2; len <= n; len <<= 1) {
      const ang = ((inverse ? 2 : -2) * Math.PI) / len;
      const wr = Math.cos(ang), wi = Math.sin(ang);
      const half = len >> 1;
      for (let i = 0; i < n; i += len) {
        let cr = 1, ci = 0;
        for (let k = 0; k < half; k++) {
          const ar = re[i + k], ai = im[i + k];
          const br = re[i + k + half], bi = im[i + k + half];
          const tr = br * cr - bi * ci, ti = br * ci + bi * cr;
          re[i + k] = ar + tr; im[i + k] = ai + ti;
          re[i + k + half] = ar - tr; im[i + k + half] = ai - ti;
          const ncr = cr * wr - ci * wi, nci = cr * wi + ci * wr;
          cr = ncr; ci = nci;
        }
      }
    }
    if (inverse) for (let i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
  }

  /** 線形補間リサンプル。factor 倍の長さにする(factor<1 で短く=再生速度アップ)。 */
  function resampleLinear(x, factor) {
    const outLen = Math.max(1, Math.round(x.length * factor));
    const out = new Float32Array(outLen);
    for (let i = 0; i < outLen; i++) {
      const pos = i / factor;
      const i0 = Math.floor(pos);
      const frac = pos - i0;
      const a = x[i0] || 0;
      const b = i0 + 1 < x.length ? x[i0 + 1] : a;
      out[i] = a + (b - a) * frac;
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // フェーズボコーダによるタイムストレッチ / ピッチシフト
  // -------------------------------------------------------------------------

  const N = 2048;   // FFT フレーム長
  const HA = 512;   // 分析ホップ

  /** タイムストレッチ(音程は保ったまま長さを stretch 倍にする)。 */
  function timeStretch(x, stretch) {
    if (x.length < N) return x.slice();
    const HS = Math.max(1, Math.round(HA * stretch));
    const win = hann(N);
    const half = N / 2;
    // 末尾フレームが窓長を超える分はゼロ詰めして、伸張後の長さを保つ
    const numFrames = Math.floor(x.length / HA) + 1;
    const outLen = (numFrames - 1) * HS + N;
    const out = new Float32Array(outLen);
    const winSum = new Float32Array(outLen);
    const lastPhase = new Float64Array(half + 1);
    const sumPhase = new Float64Array(half + 1);
    const re = new Float64Array(N), im = new Float64Array(N);
    const omega = new Float64Array(half + 1);
    for (let k = 0; k <= half; k++) omega[k] = (2 * Math.PI * HA * k) / N;
    const TWO_PI = 2 * Math.PI;

    for (let f = 0; f < numFrames; f++) {
      const start = f * HA;
      for (let i = 0; i < N; i++) {
        const idx = start + i;
        re[i] = (idx < x.length ? x[idx] : 0) * win[i];
        im[i] = 0;
      }
      fft(re, im, false);
      for (let k = 0; k <= half; k++) {
        const mag = Math.hypot(re[k], im[k]);
        const phase = Math.atan2(im[k], re[k]);
        if (f === 0) {
          sumPhase[k] = phase; // 初フレームは分析位相を採用しビン間の位相関係を保つ
        } else {
          let delta = phase - lastPhase[k] - omega[k];
          delta -= TWO_PI * Math.round(delta / TWO_PI); // -π..π へ折り返し
          const trueFreq = omega[k] + delta;
          sumPhase[k] += (trueFreq * HS) / HA;
        }
        lastPhase[k] = phase;
        re[k] = mag * Math.cos(sumPhase[k]);
        im[k] = mag * Math.sin(sumPhase[k]);
      }
      for (let k = 1; k < half; k++) { re[N - k] = re[k]; im[N - k] = -im[k]; }
      im[0] = 0; im[half] = 0;
      fft(re, im, true);
      const outStart = f * HS;
      for (let i = 0; i < N; i++) {
        out[outStart + i] += re[i] * win[i];
        winSum[outStart + i] += win[i] * win[i];
      }
    }
    for (let i = 0; i < outLen; i++) if (winSum[i] > 1e-6) out[i] /= winSum[i];
    return out;
  }

  /** ピッチシフト。semitones 半音だけ音程を変える(長さは維持)。フォルマントも一緒に動く。 */
  function pitchShift(x, semitones) {
    if (Math.abs(semitones) < 1e-4) return x.slice();
    const ratio = Math.pow(2, semitones / 12);
    const stretched = timeStretch(x, ratio);
    const shifted = resampleLinear(stretched, 1 / ratio);
    const out = new Float32Array(x.length);
    out.set(shifted.subarray(0, Math.min(shifted.length, x.length)));
    return out;
  }

  // -------------------------------------------------------------------------
  // ケプストラム包絡によるフォルマント / 音色シフト
  // -------------------------------------------------------------------------

  function spectralEnvelope(logmagFull, lifter) {
    const n = logmagFull.length;
    const re = new Float64Array(n);
    const im = new Float64Array(n);
    for (let i = 0; i < n; i++) { re[i] = logmagFull[i]; im[i] = 0; }
    fft(re, im, false);                       // ケプストラム(実)へ
    for (let q = lifter; q <= n - lifter; q++) { re[q] = 0; im[q] = 0; } // 高ケフレンシー除去
    fft(re, im, true);
    const env = new Float64Array(n);
    for (let i = 0; i < n; i++) env[i] = Math.exp(re[i]);
    return env;
  }

  /**
   * フォルマント/音色シフト。ピッチ(基本周波数)は保ったままスペクトル包絡だけを
   * 周波数軸方向に ratio 倍する。ratio>1 で高域へ(明るい/細い音色)、<1 で低域へ。
   */
  function formantShift(x, ratio, lifter) {
    if (lifter === undefined) lifter = 40;
    if (Math.abs(ratio - 1) < 1e-4) return x.slice();
    if (x.length < N) return x.slice();
    const win = hann(N);
    const half = N / 2;
    const numFrames = Math.floor(x.length / HA) + 1;
    const outLen = (numFrames - 1) * HA + N;
    const out = new Float32Array(outLen);
    const winSum = new Float32Array(outLen);
    const re = new Float64Array(N), im = new Float64Array(N);
    const mag = new Float64Array(half + 1);
    const phase = new Float64Array(half + 1);
    const logmag = new Float64Array(N);

    for (let f = 0; f < numFrames; f++) {
      const start = f * HA;
      for (let i = 0; i < N; i++) {
        const idx = start + i;
        re[i] = (idx < x.length ? x[idx] : 0) * win[i];
        im[i] = 0;
      }
      fft(re, im, false);
      for (let k = 0; k <= half; k++) {
        mag[k] = Math.hypot(re[k], im[k]);
        phase[k] = Math.atan2(im[k], re[k]);
      }
      for (let k = 0; k <= half; k++) logmag[k] = Math.log(mag[k] + 1e-8);
      for (let k = 1; k < half; k++) logmag[N - k] = logmag[k];
      const env = spectralEnvelope(logmag, lifter);
      for (let k = 0; k <= half; k++) {
        const srcPos = k / ratio;
        let warped;
        if (srcPos <= 0) warped = env[0];
        else if (srcPos >= half) warped = env[half];
        else {
          const i0 = Math.floor(srcPos), frac = srcPos - i0;
          warped = env[i0] + (env[i0 + 1] - env[i0]) * frac;
        }
        const e = env[k] > 1e-8 ? env[k] : 1e-8;
        const newMag = (mag[k] / e) * warped;
        re[k] = newMag * Math.cos(phase[k]);
        im[k] = newMag * Math.sin(phase[k]);
      }
      for (let k = 1; k < half; k++) { re[N - k] = re[k]; im[N - k] = -im[k]; }
      im[0] = 0; im[half] = 0;
      fft(re, im, true);
      const outStart = f * HA;
      for (let i = 0; i < N; i++) {
        out[outStart + i] += re[i] * win[i];
        winSum[outStart + i] += win[i] * win[i];
      }
    }
    for (let i = 0; i < outLen; i++) if (winSum[i] > 1e-6) out[i] /= winSum[i];
    const trimmed = new Float32Array(x.length);
    trimmed.set(out.subarray(0, Math.min(out.length, x.length)));
    return trimmed;
  }

  // -------------------------------------------------------------------------
  // スペクトル3バンド EQ(楽器の音色変調を戻す)
  // -------------------------------------------------------------------------

  /**
   * 低/中/高の3バンドをそれぞれ dB でブースト/カットする(STFT 領域)。
   * 楽器のトーン(イコライザ)改変を逆補正する用途。lowF/highF はクロスオーバー Hz。
   */
  function spectralEQ(x, sampleRate, lowDb, midDb, highDb, lowF, highF) {
    if (lowF === undefined) lowF = 300;
    if (highF === undefined) highF = 3000;
    if (Math.abs(lowDb) < 1e-3 && Math.abs(midDb) < 1e-3 && Math.abs(highDb) < 1e-3) return x.slice();
    if (x.length < N) return x.slice();
    const win = hann(N);
    const half = N / 2;
    const numFrames = Math.floor(x.length / HA) + 1;
    const outLen = (numFrames - 1) * HA + N;
    const out = new Float32Array(outLen);
    const winSum = new Float32Array(outLen);
    const re = new Float64Array(N), im = new Float64Array(N);
    const gLow = Math.pow(10, lowDb / 20), gMid = Math.pow(10, midDb / 20), gHigh = Math.pow(10, highDb / 20);
    // 各ビンの周波数に応じた滑らかなゲイン曲線を事前計算
    const gain = new Float64Array(half + 1);
    for (let k = 0; k <= half; k++) {
      const fHz = (k * sampleRate) / N;
      let g;
      if (fHz <= lowF) {
        const t = Math.min(1, fHz / lowF);          // low→mid へ半分の帯域でクロスフェード
        g = gLow * (1 - t * 0.5) + gMid * (t * 0.5);
      } else if (fHz >= highF) {
        g = gHigh;
      } else {
        const t = (fHz - lowF) / (highF - lowF);
        g = gMid * (1 - t) + gHigh * t;
      }
      gain[k] = g;
    }
    for (let f = 0; f < numFrames; f++) {
      const start = f * HA;
      for (let i = 0; i < N; i++) {
        const idx = start + i;
        re[i] = (idx < x.length ? x[idx] : 0) * win[i];
        im[i] = 0;
      }
      fft(re, im, false);
      for (let k = 0; k <= half; k++) { re[k] *= gain[k]; im[k] *= gain[k]; }
      for (let k = 1; k < half; k++) { re[N - k] = re[k]; im[N - k] = -im[k]; }
      im[0] = 0; im[half] = 0;
      fft(re, im, true);
      const outStart = f * HA;
      for (let i = 0; i < N; i++) {
        out[outStart + i] += re[i] * win[i];
        winSum[outStart + i] += win[i] * win[i];
      }
    }
    for (let i = 0; i < outLen; i++) if (winSum[i] > 1e-6) out[i] /= winSum[i];
    const trimmed = new Float32Array(x.length);
    trimmed.set(out.subarray(0, Math.min(out.length, x.length)));
    return trimmed;
  }

  // -------------------------------------------------------------------------
  // 復元パイプライン
  // -------------------------------------------------------------------------

  /**
   * 変調された音を元の質音に近づける汎用パイプライン。opts:
   *   pitchSemitones : ピッチ復元量(半音)
   *   formantRatio   : フォルマント/音色包絡の復元倍率(1で無変更)
   *   eq             : {lowDb, midDb, highDb} 楽器トーンの逆補正(任意)
   *   sampleRate     : eq を使う場合に必要
   * 順序: EQ → 音色包絡 → ピッチ。
   */
  function restoreSound(x, opts) {
    opts = opts || {};
    let y = x;
    const eq = opts.eq;
    if (eq && (eq.lowDb || eq.midDb || eq.highDb)) {
      y = spectralEQ(y, opts.sampleRate || 44100, eq.lowDb || 0, eq.midDb || 0, eq.highDb || 0);
    }
    const fr = opts.formantRatio == null ? 1 : opts.formantRatio;
    if (Math.abs(fr - 1) > 1e-4) y = formantShift(y, fr);
    const ps = opts.pitchSemitones || 0;
    if (Math.abs(ps) > 1e-4) y = pitchShift(y, ps);
    return y;
  }

  /** 旧 API 互換: 声の復元(ピッチ + フォルマント)。 */
  function restoreVoice(x, pitchSemitones, formantRatio) {
    return restoreSound(x, { pitchSemitones, formantRatio });
  }

  // -------------------------------------------------------------------------
  // ピッチ推定 / チューニング
  // -------------------------------------------------------------------------

  /** 有声/発音区間の代表基本周波数(中央値)を自己相関で推定。無ければ 0。 */
  function estimateMedianF0(x, sampleRate, fmin, fmax) {
    if (fmin === undefined) fmin = 70;
    if (fmax === undefined) fmax = 400;
    const frame = 2048, hop = 1024;
    const minLag = Math.floor(sampleRate / fmax);
    const maxLag = Math.floor(sampleRate / fmin);
    const f0s = [];
    for (let start = 0; start + frame <= x.length; start += hop) {
      let rms = 0;
      for (let i = 0; i < frame; i++) { const v = x[start + i]; rms += v * v; }
      rms = Math.sqrt(rms / frame);
      if (rms < 0.01) continue;
      let energy = 0;
      for (let i = 0; i < frame; i++) energy += x[start + i] * x[start + i];
      if (energy <= 0) continue;
      let bestLag = -1, bestVal = 0;
      for (let lag = minLag; lag <= maxLag; lag++) {
        let sum = 0;
        for (let i = 0; i + lag < frame; i++) sum += x[start + i] * x[start + i + lag];
        const norm = sum / energy;
        if (norm > bestVal) { bestVal = norm; bestLag = lag; }
      }
      if (bestLag > 0 && bestVal > 0.3) f0s.push(sampleRate / bestLag);
    }
    if (f0s.length === 0) return 0;
    f0s.sort((a, b) => a - b);
    return f0s[Math.floor(f0s.length / 2)];
  }

  /** fromHz → toHz にするための半音数 */
  function semitonesBetween(fromHz, toHz) {
    if (fromHz <= 0 || toHz <= 0) return 0;
    return 12 * Math.log2(toHz / fromHz);
  }

  /**
   * 平均律 A=refHz(既定440)基準で、f0 が最も近い音名からどれだけずれているかを返す。
   * { note, targetHz, cents, semitoneCorrection } 。cents>0 は f0 が高い(シャープ)。
   * semitoneCorrection は「正しい音高へ戻すための」ピッチシフト量(半音, ずれの符号反転)。
   */
  function tuningToEqualTemperament(f0, refHz) {
    if (refHz === undefined) refHz = 440;
    if (f0 <= 0) return { note: "-", targetHz: 0, cents: 0, semitoneCorrection: 0 };
    const names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    // A4=refHz は MIDI 69
    const midiFloat = 69 + 12 * Math.log2(f0 / refHz);
    const midi = Math.round(midiFloat);
    const targetHz = refHz * Math.pow(2, (midi - 69) / 12);
    const cents = (midiFloat - midi) * 100;
    const name = names[((midi % 12) + 12) % 12] + (Math.floor(midi / 12) - 1);
    return { note: name, targetHz, cents, semitoneCorrection: -(midiFloat - midi) };
  }

  // -------------------------------------------------------------------------
  // WAV エンコード(16bit PCM)
  // -------------------------------------------------------------------------

  function encodeWav(channels, sampleRate) {
    const numCh = channels.length;
    const numFrames = channels[0].length;
    const bytesPerSample = 2;
    const blockAlign = numCh * bytesPerSample;
    const dataSize = numFrames * blockAlign;
    const buffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(buffer);
    const wr = (off, s) => { for (let i = 0; i < s.length; i++) view.setUint8(off + i, s.charCodeAt(i)); };
    wr(0, "RIFF"); view.setUint32(4, 36 + dataSize, true); wr(8, "WAVE");
    wr(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, numCh, true); view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true); view.setUint16(32, blockAlign, true);
    view.setUint16(34, 16, true); wr(36, "data"); view.setUint32(40, dataSize, true);
    let off = 44;
    for (let i = 0; i < numFrames; i++) {
      for (let c = 0; c < numCh; c++) {
        let s = channels[c][i];
        s = Math.max(-1, Math.min(1, s));
        view.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7fff, true);
        off += 2;
      }
    }
    return buffer;
  }

  return {
    hann, fft, resampleLinear, timeStretch, pitchShift,
    formantShift, spectralEnvelope, spectralEQ,
    restoreSound, restoreVoice,
    estimateMedianF0, semitonesBetween, tuningToEqualTemperament,
    encodeWav,
  };
});
