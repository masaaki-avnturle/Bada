#!/usr/bin/env python3
"""論文「アメリカ合衆国大統領選挙の位相的構造」の検算。標準ライブラリのみ。"""
import itertools, random
from fractions import Fraction

# 2024年・2028年選挙の選挙人配分(2020年国勢調査に基づく)
EV = dict(AL=9, AK=3, AZ=11, AR=6, CA=54, CO=10, CT=7, DE=3, DC=3, FL=30, GA=16,
          HI=4, ID=4, IL=19, IN=11, IA=6, KS=6, KY=8, LA=8, ME=4, MD=10, MA=11,
          MI=15, MN=10, MS=6, MO=10, MT=4, NE=5, NV=6, NH=4, NJ=14, NM=5, NY=28,
          NC=16, ND=3, OH=17, OK=7, OR=8, PA=19, RI=4, SC=9, SD=3, TN=11, TX=40,
          UT=6, VT=3, VA=13, WA=12, WV=4, WI=10, WY=3)
W = sum(EV.values())
assert len(EV) == 51 and W == 538
print("[1] 州等の数 =", len(EV), " 選挙人総数 =", W, " 過半数 =", W // 2 + 1)

def sgn(t):
    return (t > 0) - (t < 0)

def E(x, blocks, w, q):
    """二段階ルール。x: ±1 の列, blocks: 添字の分割, w: 重み, q: 当選に要する重み"""
    a = sum(wi for b, wi in zip(blocks, w) if sum(x[i] for i in b) > 0)
    b_ = sum(wi for b, wi in zip(blocks, w) if sum(x[i] for i in b) < 0)
    return 1 if a >= q else (-1 if b_ >= q else 0)

# [2] 定理4.2(反映の性質)を小さな模型で全数検査
def check_small(sizes, w):
    idx = list(range(sum(sizes))); blocks = []; k = 0
    for s in sizes:
        blocks.append(idx[k:k + s]); k += s
    q = sum(w) // 2 + 1
    n = len(idx); piv = [False] * n; cnt = {1: 0, 0: 0, -1: 0}
    for x in itertools.product((1, -1), repeat=n):
        e = E(x, blocks, w, q); cnt[e] += 1
        assert E(tuple(-t for t in x), blocks, w, q) == -e          # 中立性
        for i in range(n):
            if x[i] == -1:
                y = x[:i] + (1,) + x[i + 1:]
                e2 = E(y, blocks, w, q)
                assert e2 >= e                                        # 単調性
                if e2 != e: piv[i] = True
    assert E((1,) * n, blocks, w, q) == 1                              # 全員一致
    assert all(piv)                                                    # ダミーなし
    assert cnt[1] == cnt[-1]
    return cnt
print("[2] 小模型の全数検査 (3,3,3),w=(1,1,1):", check_small((3, 3, 3), (1, 1, 1)))
print("    小模型の全数検査 (1,3,5,3),w=(3,4,5,4):", check_small((1, 3, 5, 3), (3, 4, 5, 4)))

# [3] 定理4.2(iv): 実際の配分で、どの州も決定的になる配置がある
def subset_sums(ws):
    s = 1
    for x in ws: s |= s << x
    return s
for st, w in EV.items():
    others = [v for k, v in EV.items() if k != st]
    ss = subset_sums(others)
    assert any((ss >> t) & 1 for t in range(270 - w, 270)), st
print("[3] 51 の州等すべてが、ある配置で勝敗を決める(部分和で確認)")
print("    269 対 269 の同数は起こりうるか:", bool((subset_sums(EV.values()) >> 269) & 1))

# [4] 定理5.1: m 個の等しい州(各 n 人, m,n 奇数)での最小得票
def min_votes_brute(m, n):
    blocks = [list(range(j * n, (j + 1) * n)) for j in range(m)]
    best = None
    for x in itertools.product((1, -1), repeat=m * n):
        if E(x, blocks, [1] * m, m // 2 + 1) == 1:
            v = x.count(1); best = v if best is None else min(best, v)
    return best
for m, n in [(3, 3), (3, 5), (5, 3)]:
    f = (m + 1) // 2 * ((n + 1) // 2)
    assert min_votes_brute(m, n) == f
    print(f"[4] m={m}, n={n}: 最小得票 {f}/{m*n} = {f/(m*n):.4f} (公式と一致)")

# [5] 実際の配分での最小得票率(模型: 各州の投票者数は下院議席数に比例, DC は 1)
H = {k: v - 2 for k, v in EV.items()}
tot = sum(H.values()); assert tot == 436
INF = 10 ** 9
best = [INF] * (W + 1); best[0] = 0          # best[e] = 選挙人 e をちょうど得る最小の下院議席和
for st in EV:
    w, h = EV[st], H[st]
    for e in range(W, w - 1, -1):
        if best[e - w] + h < best[e]: best[e] = best[e - w] + h
hmin = min(best[270:])
print(f"[5] 270 人以上を得る州の組の最小の議席和 = {hmin}/436, "
      f"最小得票率 = {hmin}/{2*tot} = {hmin/(2*tot):.4f}")

# [6] 例5.3: 3 つの等しい州, 得票率が [0,1]^3 上一様のときの逆転確率 = 1/8
random.seed(1); N = 2_000_000; inv = 0
for _ in range(N):
    p = (random.random(), random.random(), random.random())
    ec = sum(t > 0.5 for t in p) >= 2
    if ec != (sum(p) > 1.5): inv += 1
print(f"[6] 逆転確率 モンテカルロ {inv/N:.4f}  (厳密値 1/8 = {float(Fraction(1,8))})")

# [7] 図1: p3 = 0.4 に固定したときの面積
area_inv_a = Fraction(1, 2) * Fraction(1, 10) ** 2      # 選挙人で勝ち得票で負ける三角形
print("[7] 図1 の小三角形の面積 =", area_inv_a)
