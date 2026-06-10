#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apriori_engine.py — Ω-Apriori Core : 未知事前エンジン CPU のテロメア進化エンジン

テロメア分裂細胞の原理で、FPGA 様ロジックファブリック (apriori_cpu.c) を
「全世代の人類」に見立てた個体群として進化させ、隠れた a-priori 目標関数
(未知事前: 事前には与えられない関数) を自己発見する AI エンジン CPU を構築する。

使い方:
    # C 中核 (libaprioricpu.so) を使う場合は先にビルド:
    #   cc -O2 -fPIC -shared -o libaprioricpu.so apriori_cpu.c
    python3 apriori_engine.py --generations 120 --pop 80 --out run.json
    # .so が無くても純Pythonフォールバックで動作する。

⚠ 概念実証・教育用。実在の人体/医療/余命予測/「人類の進化」とは無関係。
"""
import argparse, ctypes, json, os, random, sys

# ----------------------------------------------------------------------
# ファブリック定数 (C と一致させること)
LUT_INPUTS = 4
CELL_BYTES = 6

# ----------------------------------------------------------------------
# 隠れた a-priori 目標関数群 (未知事前: 進化前にはエンジンに与えない)
def target_popcount(x):           # ハミング重み (情報量)
    return bin(x & 0x3F).count("1")
def target_parity(x):             # パリティ
    return bin(x & 0x3F).count("1") & 1
def target_add(x):                # 3bit + 3bit 加算の下位3bit
    return ((x & 7) + ((x >> 3) & 7)) & 7
TARGETS = {"popcount": target_popcount, "parity": target_parity, "add": target_add}

# ======================================================================
# 純Python フォールバック・ファブリック (C の fab_eval と同一仕様)
# ======================================================================
class PyFabric:
    def __init__(self, inbits, layers, width, outbits, telo_init, hayflick):
        self.inbits, self.layers, self.width = inbits, layers, width
        self.outbits, self.telo_init, self.hayflick = outbits, telo_init, hayflick
        self.lut = [0] * (layers * width)
        self.insel = [[0]*LUT_INPUTS for _ in range(layers*width)]
        self.telo = [telo_init] * (layers * width)
        self.sen = [0] * (layers * width)

    def genome_size(self):
        return self.layers * self.width * CELL_BYTES

    def load(self, g):
        idx = 0
        for L in range(self.layers):
            src = self.inbits if L == 0 else self.width
            for w in range(self.width):
                p = g[idx*CELL_BYTES:(idx+1)*CELL_BYTES]
                self.insel[idx] = [p[k] % max(1, src) for k in range(LUT_INPUTS)]
                self.lut[idx] = p[4] | (p[5] << 8)
                idx += 1

    def eval(self, x):
        prev = x & ((1 << self.inbits) - 1)
        src_count = self.inbits
        cur = 0
        for L in range(self.layers):
            cur = 0
            for w in range(self.width):
                c = L*self.width + w
                addr = 0
                for k in range(LUT_INPUTS):
                    sel = self.insel[c][k]
                    if sel >= src_count:
                        sel = sel % src_count if src_count else 0
                    addr |= ((prev >> sel) & 1) << k
                if self.sen[c]:
                    sel = self.insel[c][0]
                    if src_count and sel >= src_count: sel %= src_count
                    out = (prev >> sel) & 1
                else:
                    out = (self.lut[c] >> addr) & 1
                cur |= out << w
            prev = cur
            src_count = self.width
        return cur & ((1 << self.outbits) - 1)

    def fitness(self, target, ncases):
        match = total = 0
        for x in range(ncases):
            y = self.eval(x)
            t = target(x) & ((1 << self.outbits) - 1)
            diff = y ^ t
            for b in range(self.outbits):
                total += 1
                if not ((diff >> b) & 1): match += 1
        return match / total if total else 0.0

    def telomere_tick(self, amount):
        for i in range(self.layers*self.width):
            if self.sen[i]: continue
            t = self.telo[i] - amount
            if t <= self.hayflick:
                self.telo[i] = self.hayflick; self.sen[i] = 1
            else:
                self.telo[i] = t

    def senescent_count(self):
        return sum(self.sen)

# ======================================================================
# C 中核 (libaprioricpu.so) ctypes ラッパ
# ======================================================================
class CFabric:
    def __init__(self, lib, inbits, layers, width, outbits, telo_init, hayflick):
        self.lib = lib
        self.h = lib.fab_create(inbits, layers, width, outbits, telo_init, hayflick)
        self.outbits = outbits
        self._gs = lib.fab_genome_size(self.h)
    def genome_size(self): return self._gs
    def load(self, g):
        buf = (ctypes.c_uint8 * len(g)).from_buffer_copy(bytes(g))
        self.lib.fab_load(self.h, buf, len(g))
    def eval(self, x): return self.lib.fab_eval(self.h, x) & ((1 << self.outbits)-1)
    def fitness_native(self, cfn, ncases):
        return self.lib.fab_fitness(self.h, cfn, ncases)
    def telomere_tick(self, n): self.lib.fab_telomere_tick(self.h, n)
    def senescent_count(self): return self.lib.fab_senescent_count(self.h)
    def __del__(self):
        try: self.lib.fab_destroy(self.h)
        except Exception: pass

def load_clib():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("libaprioricpu.so", "libaprioricpu.dylib", "aprioricpu.dll"):
        p = os.path.join(here, name)
        if os.path.exists(p):
            try:
                lib = ctypes.CDLL(p)
                lib.fab_create.restype = ctypes.c_void_p
                lib.fab_create.argtypes = [ctypes.c_int]*4 + [ctypes.c_uint16]*2
                lib.fab_genome_size.restype = ctypes.c_int
                lib.fab_genome_size.argtypes = [ctypes.c_void_p]
                lib.fab_load.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), ctypes.c_int]
                lib.fab_eval.restype = ctypes.c_uint32
                lib.fab_eval.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
                lib.fab_telomere_tick.argtypes = [ctypes.c_void_p, ctypes.c_int]
                lib.fab_senescent_count.restype = ctypes.c_int
                lib.fab_senescent_count.argtypes = [ctypes.c_void_p]
                lib.fab_destroy.argtypes = [ctypes.c_void_p]
                return lib
            except Exception as e:
                print(f"[warn] {name} load failed: {e}", file=sys.stderr)
    return None

# ======================================================================
# テロメア進化エンジン (世代 GA)
# ======================================================================
class Individual:
    __slots__ = ("genome", "telomere", "senescent", "fit")
    def __init__(self, genome, telomere):
        self.genome = genome; self.telomere = telomere
        self.senescent = False; self.fit = 0.0

class AprioriEvolver:
    def __init__(self, target_name="popcount", pop=80, seed=1,
                 inbits=6, layers=3, width=8, outbits=3,
                 telo_init=1000, hayflick=200, attrition=18, use_c=True):
        self.rng = random.Random(seed)
        self.target = TARGETS[target_name]
        self.target_name = target_name
        self.ncases = 1 << inbits
        self.pop = pop
        self.inbits, self.layers, self.width = inbits, layers, width
        self.outbits = outbits
        self.telo_init, self.hayflick, self.attrition = telo_init, hayflick, attrition
        self.lib = load_clib() if use_c else None
        self.backend = "C-core (libaprioricpu.so)" if self.lib else "pure-Python fallback"
        self._fab = self._new_fabric()
        self.gsize = self._fab.genome_size()
        self.population = [Individual(self._rand_genome(), telo_init) for _ in range(pop)]
        self.history = []

    def _new_fabric(self):
        if self.lib:
            return CFabric(self.lib, self.inbits, self.layers, self.width,
                           self.outbits, self.telo_init, self.hayflick)
        return PyFabric(self.inbits, self.layers, self.width,
                        self.outbits, self.telo_init, self.hayflick)

    def _rand_genome(self):
        return bytearray(self.rng.getrandbits(8) for _ in range(self.gsize))

    def _fitness(self, genome):
        self._fab.load(genome)
        # 適合度は両バックエンドで同一: 全入力に対する出力ビット一致率
        match = total = 0
        for x in range(self.ncases):
            y = self._fab.eval(x)
            t = self.target(x) & ((1 << self.outbits) - 1)
            diff = y ^ t
            for b in range(self.outbits):
                total += 1
                if not ((diff >> b) & 1): match += 1
        return match / total

    def _mutate(self, genome, telomere):
        # 変異率はテロメア残量に比例 (若い細胞ほど可塑的)。老化で凍結。
        if telomere <= self.hayflick:
            return genome  # senescent: 変異不能
        frac = (telomere - self.hayflick) / max(1, self.telo_init - self.hayflick)
        rate = 0.01 + 0.06 * frac
        g = bytearray(genome)
        for i in range(len(g)):
            if self.rng.random() < rate:
                g[i] = self.rng.getrandbits(8)
        return g

    def _crossover(self, a, b):
        cut = self.rng.randrange(1, len(a))
        return bytearray(a[:cut] + b[cut:])

    def _tournament(self, k=3):
        best = None
        for _ in range(k):
            ind = self.rng.choice(self.population)
            if best is None or ind.fit > best.fit: best = ind
        return best

    def step(self, gen):
        # 評価
        for ind in self.population:
            ind.fit = self._fitness(ind.genome)
        self.population.sort(key=lambda i: i.fit, reverse=True)
        best = self.population[0]
        mean = sum(i.fit for i in self.population) / len(self.population)
        telo_mean = sum(i.telomere for i in self.population) / len(self.population)
        sen_frac = sum(1 for i in self.population if i.telomere <= self.hayflick) / len(self.population)

        # エリート + テロメラーゼ (再活性化で「全世代」を継続)
        elite_n = max(2, self.pop // 10)
        elites = []
        for e in self.population[:elite_n]:
            ne = Individual(bytearray(e.genome), self.telo_init)  # telomerase rejuvenation
            ne.fit = e.fit; elites.append(ne)

        # 次世代生成 (分裂 = テロメア短縮)
        children = []
        while len(children) < self.pop - elite_n:
            p1, p2 = self._tournament(), self._tournament()
            child_telo = max(self.hayflick, min(p1.telomere, p2.telomere) - self.attrition)
            g = self._crossover(p1.genome, p2.genome)
            g = self._mutate(g, child_telo)
            ch = Individual(g, child_telo)
            ch.senescent = child_telo <= self.hayflick
            children.append(ch)
        self.population = elites + children

        rec = dict(gen=gen, best=round(best.fit, 5), mean=round(mean, 5),
                   telo_mean=round(telo_mean, 1), senescent_frac=round(sen_frac, 4))
        self.history.append(rec)
        return best, rec

    def run(self, generations, verbose=True):
        best_overall = None
        for g in range(generations):
            best, rec = self.step(g)
            if best_overall is None or best.fit > best_overall.fit:
                best_overall = Individual(bytearray(best.genome), best.telomere)
                best_overall.fit = best.fit
            if verbose and (g % max(1, generations//20) == 0 or g == generations-1):
                print(f"gen {g:4d}  best={rec['best']:.4f}  mean={rec['mean']:.4f}  "
                      f"telo={rec['telo_mean']:.0f}  senescent={rec['senescent_frac']*100:.0f}%")
        return best_overall

    def truth_table(self, genome):
        self._fab.load(genome)
        return [{"in": x, "out": self._fab.eval(x), "target": self.target(x)}
                for x in range(self.ncases)]

    def to_json(self, best, generations):
        return dict(
            engine="Omega-Apriori Core",
            note="conceptual/educational only — not a medical or predictive device",
            backend=self.backend,
            target=self.target_name,
            params=dict(inbits=self.inbits, layers=self.layers, width=self.width,
                        outbits=self.outbits, pop=self.pop, generations=generations,
                        telo_init=self.telo_init, hayflick=self.hayflick,
                        attrition=self.attrition, genome_bytes=self.gsize),
            best_fitness=round(best.fit, 5),
            best_genome_hex=bytes(best.genome).hex(),
            truth_table=self.truth_table(best.genome),
            history=self.history,
        )

# ======================================================================
def main():
    ap = argparse.ArgumentParser(description="Omega-Apriori Core telomere evolution engine")
    ap.add_argument("--generations", type=int, default=120)
    ap.add_argument("--pop", type=int, default=80)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--target", choices=list(TARGETS), default="popcount")
    ap.add_argument("--out", default="run.json")
    ap.add_argument("--no-c", action="store_true", help="C中核を使わず純Pythonで実行")
    args = ap.parse_args()

    ev = AprioriEvolver(target_name=args.target, pop=args.pop, seed=args.seed,
                        use_c=not args.no_c)
    print(f"Ω-Apriori Core  backend={ev.backend}  target={args.target}  "
          f"genome={ev.gsize}B  pop={args.pop}")
    best = ev.run(args.generations)
    data = ev.to_json(best, args.generations)
    with open(args.out, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"\nbest fitness = {best.fit:.4f}   -> wrote {args.out}")

if __name__ == "__main__":
    main()
