/*
 * core.js — Ω-Canis DNA の計算コア (ブラウザ / Node 共用)
 * Masaaki Yamaguchi / Bada — bio_medicine/omega_canis_dna
 *
 * 1) 実DNA配列の種判別: k-mer 照合で「イヌ (Canis lupus familiaris)」由来の
 *    配列リードが試料中に存在するかを数える。これが本アプリで唯一「戌のDNAの有無」を
 *    判断に使う実計算。参照は NCBI の mtDNA 全長 (イヌ NC_002008 / ヒト NC_012920)。
 * 2) Γ×Jones 熱エネルギー (概念): Kauffman ブラケットの状態和で Jones 多項式を
 *    厳密に計算し、Γ大域的部分積分多様体の核 e^{-x log x} から作った「熱」パラメータ t で
 *    評価する。計算自体は本物の数学だが、生体データへの意味づけは概念モデルであり、
 *    種判定には使わない。
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CanisCore = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  /* ---------------- 配列入出力 ---------------- */

  // FASTA / FASTQ / 生配列テキストをリード配列に分解する。
  function parseSequences(text) {
    const lines = text.replace(/\r/g, "").split("\n");
    const reads = [];
    let i = 0;
    const first = lines.find((l) => l.trim() !== "") || "";
    if (first.startsWith("@")) {
      // FASTQ: 4行1組
      while (i < lines.length) {
        if (!lines[i].startsWith("@")) { i++; continue; }
        const seq = (lines[i + 1] || "").trim();
        if (seq) reads.push(cleanSeq(seq));
        i += 4;
      }
    } else if (first.startsWith(">")) {
      let cur = [];
      for (const l of lines) {
        if (l.startsWith(">")) {
          if (cur.length) reads.push(cleanSeq(cur.join("")));
          cur = [];
        } else cur.push(l.trim());
      }
      if (cur.length) reads.push(cleanSeq(cur.join("")));
    } else {
      for (const l of lines) {
        const s = cleanSeq(l);
        if (s) reads.push(s);
      }
    }
    return reads.filter((r) => r.length > 0);
  }

  function cleanSeq(s) {
    return s.toUpperCase().replace(/U/g, "T").replace(/[^ACGTN]/g, "");
  }

  // 23andMe / AncestryDNA 等の SNP 生データ形式か (種判別には使えない)
  function looksLikeSnpArray(text) {
    const head = text.slice(0, 4000);
    return /^\s*#.*rsid/im.test(head) || /^rs\d+\s+\S+\s+\d+\s+[ACGTID-]{1,2}\s*$/m.test(head);
  }

  function revComp(s) {
    const m = { A: "T", C: "G", G: "C", T: "A", N: "N" };
    let o = "";
    for (let i = s.length - 1; i >= 0; i--) o += m[s[i]] || "N";
    return o;
  }

  /* ---------------- k-mer 種判別 ---------------- */

  function kmerSet(seq, k) {
    const set = new Set();
    const both = [seq, revComp(seq)];
    for (const s of both) {
      for (let i = 0; i + k <= s.length; i++) {
        const km = s.substr(i, k);
        if (km.indexOf("N") === -1) set.add(km);
      }
    }
    return set;
  }

  // 参照 (name -> 配列) から、各種に固有な k-mer 索引を作る。
  function buildIndex(refs, k) {
    const sets = {};
    for (const name of Object.keys(refs)) sets[name] = kmerSet(refs[name], k);
    const names = Object.keys(sets);
    const index = new Map(); // kmer -> 種名 (固有のもののみ)
    for (const n of names) {
      for (const km of sets[n]) {
        let shared = false;
        for (const o of names) if (o !== n && sets[o].has(km)) { shared = true; break; }
        if (!shared) index.set(km, n);
      }
    }
    return { k, names, index };
  }

  // 各リードを、固有 k-mer のヒット数で種に割り当てる。
  function classifyReads(reads, idx, opts) {
    const minHits = (opts && opts.minHits) || 3;
    const k = idx.k;
    const counts = { unassigned: 0 };
    for (const n of idx.names) counts[n] = 0;
    const hitsTotal = {};
    for (const n of idx.names) hitsTotal[n] = 0;
    for (const r of reads) {
      const h = {};
      for (const n of idx.names) h[n] = 0;
      for (let i = 0; i + k <= r.length; i++) {
        const sp = idx.index.get(r.substr(i, k));
        if (sp) h[sp]++;
      }
      let best = null, bestV = 0, second = 0;
      for (const n of idx.names) {
        hitsTotal[n] += h[n];
        if (h[n] > bestV) { second = bestV; bestV = h[n]; best = n; }
        else if (h[n] > second) second = h[n];
      }
      if (best && bestV >= minHits && bestV >= 4 * second) counts[best]++;
      else counts.unassigned++;
    }
    return { total: reads.length, counts, hitsTotal };
  }

  // イヌ由来リード数から判定文を作る (統計的に控えめな閾値)。
  function verdict(res, dogName) {
    const dog = res.counts[dogName] || 0;
    const assigned = res.total - res.counts.unassigned;
    const frac = assigned > 0 ? dog / assigned : 0;
    let level, text;
    if (res.total === 0) {
      level = "none"; text = "配列がありません。";
    } else if (assigned === 0) {
      level = "none"; text = "どの参照種にも割り当てられるリードがありません (参照範囲外、または品質不足)。判定不能です。";
    } else if (dog === 0) {
      level = "neg"; text = "イヌ由来の配列は検出されませんでした。";
    } else if (dog < 3 || frac < 0.01) {
      level = "trace"; text = "ごく少量のイヌ由来配列を検出 (痕跡)。ペットの毛・唾液、器具や試薬からの混入 (コンタミネーション) が最も考えられます。再採取・陰性対照での確認が必要です。";
    } else if (frac < 0.5) {
      level = "mixed"; text = "イヌ由来配列が有意に含まれます。混合試料 (ヒト＋イヌ) です。ヒトのゲノムにイヌの DNA が遺伝的に組み込まれることは生物学的にありえないため、試料への付着・混入と解釈してください。";
    } else {
      level = "dog"; text = "試料の大部分がイヌ由来です。この試料自体がイヌから採取された可能性が高いです。";
    }
    return { level, text, dog, assigned, frac };
  }

  // 参照配列から検証用の合成リードを作る (点変異率 err、混合比 dogFrac)。
  function simulateReads(refs, dogName, humanName, n, len, dogFrac, err, seed) {
    let s = seed >>> 0 || 12345;
    const rnd = () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296);
    const bases = "ACGT";
    const reads = [];
    for (let i = 0; i < n; i++) {
      const src = rnd() < dogFrac ? refs[dogName] : refs[humanName];
      const p = Math.floor(rnd() * (src.length - len));
      let r = src.substr(p, len).split("");
      for (let j = 0; j < r.length; j++) if (rnd() < err) r[j] = bases[Math.floor(rnd() * 4)];
      r = r.join("");
      reads.push(rnd() < 0.5 ? r : revComp(r));
    }
    return reads;
  }

  /* ---------------- Γ大域的部分積分多様体 ---------------- */

  // ∫Γ(γ)' dx_m = 2 e^{-x log x}  (x→0 で 2、x=1 で 2、x=1/e で最大)
  function gammaKernel(x) {
    if (x <= 0) return 2;
    return 2 * Math.exp(-x * Math.log(x));
  }

  /* ---------------- Jones 多項式 (Kauffman ブラケット) ---------------- */

  // 多項式 = { 指数: 係数 } (変数 A)
  function padd(p, q, sc) {
    const o = Object.assign({}, p);
    for (const e in q) {
      o[e] = (o[e] || 0) + (sc || 1) * q[e];
      if (o[e] === 0) delete o[e];
    }
    return o;
  }
  function pmul(p, q) {
    const o = {};
    for (const a in p) for (const b in q) {
      const e = +a + +b;
      o[e] = (o[e] || 0) + p[a] * q[b];
      if (o[e] === 0) delete o[e];
    }
    return o;
  }
  function ppow(p, n) { let o = { 0: 1 }; for (let i = 0; i < n; i++) o = pmul(o, p); return o; }

  // PD 符号 (KnotTheory 規約 X[i,j,k,l]) から Kauffman ブラケット <K> を状態和で計算。
  function kauffmanBracket(pd) {
    const n = pd.length;
    const d = { 2: -1, "-2": -1 }; // d = -A^2 - A^-2
    let total = {};
    for (let s = 0; s < 1 << n; s++) {
      // Union-Find で輪の数を数える
      const par = new Map();
      const find = (x) => { while (par.get(x) !== x) { par.set(x, par.get(par.get(x))); x = par.get(x); } return x; };
      const add = (x) => { if (!par.has(x)) par.set(x, x); };
      const uni = (a, b) => { add(a); add(b); par.set(find(a), find(b)); };
      let a = 0;
      for (let c = 0; c < n; c++) {
        const [i, j, k, l] = pd[c];
        if ((s >> c) & 1) { uni(i, l); uni(j, k); }      // B 平滑化
        else { a++; uni(i, j); uni(k, l); }              // A 平滑化
      }
      const roots = new Set();
      for (const x of par.keys()) roots.add(find(x));
      const loops = roots.size;
      const term = pmul({ [a - (n - a)]: 1 }, ppow(d, loops - 1));
      total = padd(total, term);
    }
    return total;
  }

  function writhe(pd) {
    let w = 0;
    for (const [, j, , l] of pd) w += (j - l === 1 || l - j > 1) ? 1 : -1;
    return w;
  }

  // Jones 多項式 V(t) を { t の指数 (4倍して整数化せず有理数): 係数 } で返す。
  function jones(pd) {
    const br = kauffmanBracket(pd);
    const w = writhe(pd);
    const f = pmul({ [-3 * w]: (w % 2 === 0 ? 1 : -1) }, br); // (-A^3)^{-w} <K>
    const v = {};
    for (const e in f) v[-(+e) / 4] = f[e]; // A = t^{-1/4}
    return v;
  }

  function evalPoly(v, t) {
    let s = 0;
    for (const e in v) s += v[e] * Math.pow(t, +e);
    return s;
  }

  function polyToString(v) {
    const es = Object.keys(v).map(Number).sort((a, b) => a - b);
    if (!es.length) return "0";
    return es.map((e, i) => {
      const c = v[e];
      const sign = c < 0 ? "−" : i ? "+" : "";
      const ac = Math.abs(c);
      const coef = ac === 1 && e !== 0 ? "" : String(ac);
      const tt = e === 0 ? "" : e === 1 ? "t" : "t^" + (Number.isInteger(e) ? e : e.toFixed(2));
      return (i ? " " : "") + sign + (i ? " " : "") + coef + tt;
    }).join("");
  }

  const KNOTS = {
    "3_1 (三葉結び目)": [[1, 4, 2, 5], [3, 6, 4, 1], [5, 2, 6, 3]],
    "4_1 (8の字結び目)": [[4, 2, 5, 1], [8, 6, 1, 5], [6, 3, 7, 4], [2, 7, 3, 8]],
    "5_1 (五葉結び目)": [[1, 6, 2, 7], [3, 8, 4, 9], [5, 10, 6, 1], [7, 2, 8, 3], [9, 4, 10, 5]],
  };

  /* ---------------- Γ×Jones 熱エネルギー統合 (概念指標) ---------------- */

  // 各モダリティの正規化値 x∈(0,1] を Γ核で熱重みに変換し、
  // その平均から t = e^{-β} (β = 平均熱重み) を作って |V(t)| を「熱エネルギー」として返す。
  // ※ 概念指標。DNA の種を判別する情報は含まない。
  function thermalIndex(modalities, pd) {
    const keys = Object.keys(modalities);
    const w = {};
    let sum = 0;
    for (const k of keys) {
      const x = Math.min(1, Math.max(1e-6, modalities[k]));
      w[k] = gammaKernel(x);
      sum += w[k];
    }
    const beta = keys.length ? sum / keys.length : 2;
    const t = Math.exp(-beta);
    const v = jones(pd);
    return { weights: w, beta, t, V: evalPoly(v, t), poly: v };
  }

  return {
    parseSequences, looksLikeSnpArray, revComp, buildIndex, classifyReads, verdict, simulateReads,
    gammaKernel, kauffmanBracket, writhe, jones, evalPoly, polyToString, KNOTS, thermalIndex,
  };
});
