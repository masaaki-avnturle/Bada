#!/usr/bin/env python3
"""論文「アメリカ合衆国大統領選挙の統計的構造」の検算。標準ライブラリのみ。"""
import math, itertools, random
from fractions import Fraction

EV = dict(AL=9, AK=3, AZ=11, AR=6, CA=54, CO=10, CT=7, DE=3, DC=3, FL=30, GA=16,
          HI=4, ID=4, IL=19, IN=11, IA=6, KS=6, KY=8, LA=8, ME=4, MD=10, MA=11,
          MI=15, MN=10, MS=6, MO=10, MT=4, NE=5, NV=6, NH=4, NJ=14, NM=5, NY=28,
          NC=16, ND=3, OH=17, OK=7, OR=8, PA=19, RI=4, SC=9, SD=3, TN=11, TX=40,
          UT=6, VT=3, VA=13, WA=12, WV=4, WI=10, WY=3)
W = sum(EV.values()); Q = 270
assert W == 538 and len(EV) == 51
H = {k: v - 2 for k, v in EV.items()}          # 下院議席 (DC は 1)

# [1] 命題2.1: x^x = e^{x log x}, log_x(x^n) = n
for x in (2, 3, 4, 5):
    assert abs(math.exp(x * math.log(x)) - x ** x) < 1e-9 * x ** x
    assert abs(math.log(x ** 7, x) - 7) < 1e-12
print("[1] 2^2,3^3,4^4,5^5 =", [x ** x for x in (2, 3, 4, 5)], " log_x(x^n)=n 確認")

# [2] 定理4.1: n^n / prod n_j^{n_j} = e^{nH},  (n+1)^{-k} e^{nH} <= 多項係数 <= e^{nH}
def ent(ns):
    n = sum(ns); return -sum(a / n * math.log(a / n) for a in ns if a)
ok = True
for n in range(1, 31):
    for k in (2, 3):
        for ns in itertools.product(range(n + 1), repeat=k):
            if sum(ns) != n: continue
            lhs = n ** n / math.prod(a ** a for a in ns)          # 0^0 = 1
            ok &= abs(math.log(lhs) - n * ent(ns)) < 1e-9
            mult = math.factorial(n) // math.prod(math.factorial(a) for a in ns)
            ok &= (n + 1) ** (-k) * lhs <= mult * (1 + 1e-12) and mult <= lhs * (1 + 1e-12)
print("[2] 定理4.1 (n<=30, k=2,3 で全数検査):", ok)

# [3] 母関数 G(z) = prod (1 + z^{w_s}) と連立の数
def poly(ws):
    c = [0] * (W + 1); c[0] = 1
    for w in ws:
        for e in range(W, w - 1, -1): c[e] += c[e - w]
    return c
c = poly(EV.values())
assert sum(c) == 2 ** 51
ties = c[269]; wins = sum(c[Q:])
assert 2 * wins + ties == 2 ** 51
print(f"[3] 連立の総数 2^51 = {2**51}")
print(f"    270 以上の連立 = {wins}  (割合 {wins/2**51:.6f})")
print(f"    269 対 269 の連立 = {ties}  (割合 {ties/2**51:.6f})")

# [4] 定理4.3: エントロピーの下降 (公平な硬貨の模型, N = 1.5e8 を議席に比例配分)
N = 150_000_000; tot = sum(H.values())
Hx = N
Htau = sum(0.5 * math.log2(math.pi * math.e * (N * h / tot) / 2) for h in H.values())
Hsig = 51.0
p0 = ties / 2 ** 51; p1 = wins / 2 ** 51
HE = -(p0 * math.log2(p0) + 2 * p1 * math.log2(p1))
print(f"[4] H(X) = {Hx:.3e} bit, H(tau) ~ {Htau:.1f} bit, H(sigma) = {Hsig} bit, H(E) = {HE:.4f} bit")

# [5] 定理5.1: コンドルセ=チェルノフ  P(X <= n/2) <= (4p(1-p))^{n/2}
def tail(n, p):
    lg = lambda k: (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                    + k * math.log(p) + (n - k) * math.log(1 - p))
    return sum(math.exp(lg(k)) for k in range(0, n // 2 + 1))
for n, p in [(101, 0.55), (1001, 0.52), (1001, 0.55), (10001, 0.51)]:
    t = tail(n, p); b = (4 * p * (1 - p)) ** (n / 2)
    assert t <= b
    print(f"[5] n={n}, p={p}: 誤り確率 {t:.3e} <= 上界 {b:.3e}")
# 1 州 30 万人, p = 0.505 の上界
print(f"    n=300001, p=0.505: 上界 {(4*0.505*0.495)**(300001/2):.3e}")

# [6] 定理6.1: prod_p (1 + p^{-2}) = zeta(2)/zeta(4) = 15/pi^2
def primes(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\0\0"
    for i in range(2, int(n ** .5) + 1):
        if s[i]: s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(n + 1) if s[i]]
P = primes(2_000_000)
prod = 1.0
for p in P: prod *= 1 + p ** -2
print(f"[6] prod(1+p^-2) = {prod:.6f},  15/pi^2 = {15/math.pi**2:.6f};  51 番目の素数 = {P[50]}")
# 連立 -> 平方因子のない整数 の単射性 (m = 12 で全数検査)
m = 12; codes = set()
for S in itertools.product((0, 1), repeat=m):
    codes.add(math.prod(P[i] for i in range(m) if S[i]))
assert len(codes) == 2 ** m
print("    連立の符号化は単射 (m=12 で全数検査)")

# [7] 命題6.3: バンザフ指数と 1 票の力 (模型: 州の投票者数は議席に比例)
swing = {}
for st, w in EV.items():
    co = poly([v for k, v in EV.items() if k != st])
    swing[st] = sum(co[Q - w:Q]) / 2 ** 50
tb = sum(swing.values())
power = {st: swing[st] / math.sqrt(H[st]) for st in EV}      # 相対値
mx = max(power, key=power.get); mn = min(power, key=power.get)
for st in ("CA", "TX", "FL", "PA", "WY", "DC"):
    print(f"[7] {st}: 選挙人 {EV[st]:2d}, 決定確率 {swing[st]:.4f}, 正規化バンザフ {swing[st]/tb:.4f}, "
          f"選挙人比 {EV[st]/W:.4f}, 1 票の力(最小=1) {power[st]/power[mn]:.2f}")
print(f"    1 票の力: 最大 {mx}, 最小 {mn}, 比 = {power[mx]/power[mn]:.2f}")

# [8] 定理7.1: 重み付き中央値が唯一のナッシュ均衡 (格子上の全数検査)
random.seed(7)
def check_ne(m, grid=41):
    mus = random.sample(range(1, grid - 1), m); ws = [random.randint(1, 9) for _ in range(m)]
    if sum(ws) % 2 == 0: ws[0] += 1
    q = sum(ws) // 2 + 1
    def pay(a, b):
        A = sum(w for mu, w in zip(mus, ws) if abs(a - mu) < abs(b - mu))
        B = sum(w for mu, w in zip(mus, ws) if abs(b - mu) < abs(a - mu))
        return 1 if A >= q else (0 if B >= q else 0.5)
    ne = [(a, b) for a in range(grid) for b in range(grid)
          if all(pay(x, b) <= pay(a, b) for x in range(grid))
          and all(pay(y, a) <= pay(b, a) for y in range(grid))]
    order = sorted(zip(mus, ws)); cum = 0
    for mu, w in order:
        cum += w
        if cum >= q: M = mu; break
    return ne == [(M, M)]
print("[8] 定理7.1 (乱数で作った 200 例, 格子 41 点):", all(check_ne(random.randint(1, 7)) for _ in range(200)))
