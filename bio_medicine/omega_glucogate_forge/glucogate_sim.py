#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glucogate_sim.py — Ω-GlucoGate Forge (CLI 版)

形態形成場(Γ大域的部分積分多様体で変調した反応拡散場)から
「ドーパミン作動性 糖取り込み薬剤」を鍛造(forge)し、その薬剤を投与したときの
血糖 → 細胞内への糖取り込み(GLUT4 トランスロケーション)を数値シミュレーションする。

  形態形成場 φ(r)  ──記述子──▶  薬剤スペック(pKi/半減期/BBB/経口F/κ_ins/κ_GLUT4)
        │                                   │
        └─ Γカーネル e^{−x log x} で変調      ▼
                                      PK(1-コンパートメント経口) → D2受容体占有率
                                                 │
                                      PD: 血糖-インスリン-GLUT4 モデル
                                                 ▼
                              U_cell = Vmax·M·G/(Km+G)  ← 血中の糖が細胞内へ

⚠ 概念シミュレーション・非医療。実在の医薬品を設計/製造/評価するものではなく、
   本プログラムの出力を医療判断に用いることはできません。
   ドーパミン D2 作動薬(例: 徐放性でない速放性ブロモクリプチン)が 2 型糖尿病の
   血糖コントロールを改善しうるという知見に着想していますが、本モデルの係数は
   すべて概念的な仮想値です。

依存なし (Python 3.8+ 標準ライブラリのみ)。

  python3 glucogate_sim.py                     # 既定条件で鍛造 → 対照/投薬を比較
  python3 glucogate_sim.py --auto-forge 16     # 製造装置が最良の薬剤を自動探索
  python3 glucogate_sim.py --csv out.csv --json glucogate.spec.json

© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine — 概念実証(非医療)
"""

import argparse
import json
import math
import sys

# ---------------------------------------------------------------- Γ カーネル

def gamma_kernel(x: float) -> float:
    """Γ大域的部分積分多様体の核 e^{−x log x} (x>0)。x→0 で 1 に落ち着かせる。"""
    if x <= 1e-9:
        return 1.0
    return math.exp(-x * math.log(x))


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def sat(v):
    """[0,1] への飽和写像 (tanh)。"""
    return math.tanh(max(0.0, v))


# ------------------------------------------------- ① 形態形成場 (製造装置本体)

class MorphogenField:
    """Γカーネルで拡散係数を変調した Gray–Scott 反応拡散場。

    ∂u/∂t = Du(r)∇²u − uv² + F(1−u)
    ∂v/∂t = Dv(r)∇²v + uv² − (F+k)v
    Du(r) = Du0·(½ + ½·e^{−κr log κr})     ← Γ大域的部分積分多様体による空間変調

    収束した v の形態から薬剤記述子(充填率・分岐度・対称性・特徴長)を読み出す。
    """

    def __init__(self, n=48, feed=0.037, kill=0.060, kappa=1.0, seed=7, du=0.16, dv=0.08):
        self.n, self.feed, self.kill, self.kappa = n, feed, kill, kappa
        self.du, self.dv = du, dv
        self.seed = seed
        n2 = n * n
        self.u = [1.0] * n2
        self.v = [0.0] * n2
        # Γ変調した拡散係数マップ
        self.gu = [0.0] * n2
        self.gv = [0.0] * n2
        c = (n - 1) / 2.0
        for y in range(n):
            for x in range(n):
                r = math.hypot(x - c, y - c) / (c + 1e-9)
                g = 0.5 + 0.5 * gamma_kernel(kappa * r + 1e-6)
                i = y * n + x
                self.gu[i] = du * g
                self.gv[i] = dv * (1.0 - 0.35 * (g - 0.5))
        # 決定論的な種付け (線形合同法。seed が同じなら常に同じ薬剤が鍛造される)
        st = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        for _ in range(max(6, n // 4)):
            st = (st * 1664525 + 1013904223) & 0xFFFFFFFF
            sx = int(n * 0.2 + (st / 0x100000000) * n * 0.6)
            st = (st * 1664525 + 1013904223) & 0xFFFFFFFF
            sy = int(n * 0.2 + (st / 0x100000000) * n * 0.6)
            rad = max(2, n // 12)
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    if dx * dx + dy * dy > rad * rad:
                        continue
                    i = ((sy + dy) % n) * n + ((sx + dx) % n)
                    self.u[i] = 0.5
                    self.v[i] = 0.25

    def step(self, iters=500, dt=1.0):
        n, u, v, gu, gv = self.n, self.u, self.v, self.gu, self.gv
        F, k = self.feed, self.kill
        for _ in range(iters):
            nu = u[:]
            nv = v[:]
            for y in range(n):
                ym = ((y - 1) % n) * n
                yp = ((y + 1) % n) * n
                yc = y * n
                for x in range(n):
                    xm = (x - 1) % n
                    xp = (x + 1) % n
                    i = yc + x
                    lu = u[yc + xm] + u[yc + xp] + u[ym + x] + u[yp + x] - 4.0 * u[i]
                    lv = v[yc + xm] + v[yc + xp] + v[ym + x] + v[yp + x] - 4.0 * v[i]
                    uvv = u[i] * v[i] * v[i]
                    nu[i] = clamp(u[i] + dt * (gu[i] * lu - uvv + F * (1.0 - u[i])), 0.0, 1.0)
                    nv[i] = clamp(v[i] + dt * (gv[i] * lv + uvv - (F + k) * v[i]), 0.0, 1.0)
            u, v = nu, nv
        self.u, self.v = u, v
        return self

    def descriptors(self):
        """形態 → 4 記述子 (充填率 / 分岐度 / 点対称性 / 特徴長)。"""
        n, v = self.n, self.v
        n2 = n * n
        occ = sum(1 for t in v if t > 0.20) / n2                      # 充填率
        # 分岐度: 平均勾配 (輪郭の密度)
        g = 0.0
        for y in range(n):
            yc = y * n
            yp = ((y + 1) % n) * n
            for x in range(n):
                i = yc + x
                g += abs(v[yc + (x + 1) % n] - v[i]) + abs(v[yp + x] - v[i])
        edge = g / (2.0 * n2)
        # 点対称性 (180°回転との一致度)
        num = den = 0.0
        for y in range(n):
            for x in range(n):
                a = v[y * n + x]
                b = v[(n - 1 - y) * n + (n - 1 - x)]
                num += abs(a - b)
                den += abs(a) + abs(b)
        sym = 1.0 - (num / (den + 1e-9))
        # 特徴長: 各行のしきい値交差数から波長を推定
        cross = 0
        for y in range(n):
            yc = y * n
            prev = v[yc] > 0.2
            for x in range(1, n):
                cur = v[yc + x] > 0.2
                if cur != prev:
                    cross += 1
                prev = cur
        lam = (2.0 * n * n) / (cross + 1e-9) if cross else float(n)
        lamn = clamp(lam / n, 0.0, 1.0)
        return {
            "occupancy": occ,
            "branching": clamp(edge * 12.0, 0.0, 1.0),
            "symmetry": clamp(sym, 0.0, 1.0),
            "feature_length": lamn,
        }


# ------------------------------------------------- ② 薬剤スペック(鍛造の出力)

def forge_drug(desc, label="Ω-GG"):
    """形態記述子 → ドーパミン作動性 糖取り込み薬剤のスペック。

    すべて決定論的な単調写像。同じ形態形成場からは常に同じ薬剤が得られる。
    """
    occ = desc["occupancy"]
    br = desc["branching"]
    sym = desc["symmetry"]
    lam = desc["feature_length"]

    pki = 6.40 + 2.80 * sat(1.4 * br)                 # D2 親和性 pKi
    bbb = clamp(0.10 + 0.85 * lam, 0.05, 0.95)        # 血液脳関門 透過指数
    f_oral = clamp(0.22 + 0.62 * sym, 0.10, 0.92)     # 経口バイオアベイラビリティ
    t_half = clamp(2.0 + 20.0 * occ, 1.0, 26.0)       # 消失半減期 (h)
    k_ins = clamp(0.20 + 1.60 * br * sym, 0.0, 2.0)   # 中枢性インスリン感受性増強
    k_glut4 = clamp(0.10 + 1.20 * occ * br, 0.0, 1.5)  # インスリン非依存 GLUT4 動員
    mw = 280.0 + 240.0 * occ                          # 仮想分子量
    vd = 45.0 + 190.0 * bbb                           # 分布容積 (L) — 脂溶性が高いほど大
    ka = 0.010 + 0.030 * sym                          # 吸収速度定数 (1/min)

    ki_ngml = (10.0 ** (-pki)) * mw * 1e6             # Ki を ng/mL に換算
    uid = "%04X-%04X" % (
        int((pki * 1000 + t_half * 37 + bbb * 911) % 65536),
        int((k_ins * 3313 + k_glut4 * 7717 + f_oral * 1543) % 65536),
    )
    return {
        "name": "%s-%s" % (label, uid),
        "class": "dopamine D2/D3 partial agonist (conceptual, non-medical)",
        "pKi_D2": pki,
        "Ki_ng_per_mL": ki_ngml,
        "MW": mw,
        "t_half_h": t_half,
        "F_oral": f_oral,
        "ka_per_min": ka,
        "Vd_L": vd,
        "BBB_index": bbb,
        "kappa_insulin_sens": k_ins,
        "kappa_glut4": k_glut4,
        "descriptors": desc,
    }


# ------------------------------------------------- ③ 生理モデル (PK/PD シミュ)

PRESETS = {
    # Si: インスリン感受性, beta: β細胞応答性, kEGP: 肝糖放出のインスリン抑制, Gb/Ib: 空腹時基礎値
    "t2d":        dict(Si=0.00085, beta=0.35, kEGP=0.35, Gb=152.0, Ib=15.0, label="2型糖尿病(中等症)"),
    "t2d-severe": dict(Si=0.00050, beta=0.20, kEGP=0.22, Gb=196.0, Ib=13.0, label="2型糖尿病(重症・高血糖)"),
    "healthy":    dict(Si=0.00220, beta=1.00, kEGP=0.75, Gb=92.0,  Ib=8.0,  label="非糖尿病(対照)"),
}

# 生理定数 (体重 70 kg 相当・概念値)
BW = 70.0
VG = 1.6 * BW          # 血糖分布容積 dL
KM = 90.0              # GLUT4 の見かけ Km (mg/dL)
U_II = 70.0            # インスリン非依存の消費 (脳など) mg/min
EGP0 = 145.0           # 基礎肝糖放出 mg/min
P2 = 0.028             # インスリン作用の時定数 (1/min)
IZ = 2.0               # X を駆動しない下限インスリン (µU/mL)
N_CLR = 0.14           # インスリン消失速度 (1/min)
I_MIN = 1.5            # インスリンの下限 (µU/mL)
KD_X, HILL = 0.035, 2.0   # GLUT4 膜提示の半数動員インスリン作用 X と Hill 係数
TAU_M = 12.0              # GLUT4 トランスロケーションの時定数 (min)
M_MIN, M_MAX = 0.05, 1.0
SEC_GAIN = 6.0            # 追加インスリン分泌のゲイン (per +100 mg/dL)
KEO = 0.02             # 効果部位(中枢)への平衡化速度 (1/min)
TAU_SENS = 2880.0      # 感作(インスリン感受性改善)の時定数 = 2 日 (min)
ALPHA_HEP = 0.22       # 中枢D2占有 → 肝糖放出の抑制係数
IOTA_ISLET = 0.45      # 膵島D2占有 → インスリン分泌の抑制係数 (D2 は分泌を抑える)
TAU_MEAL = 45.0        # 食事吸収のピーク時間 (min)
F_MEAL = 0.90          # 摂取炭水化物の吸収率

DEFAULT_MEALS = [(7.0, 60.0), (12.0, 75.0), (19.0, 70.0)]   # (時刻 h, 炭水化物 g)


def m_target(drive):
    """インスリン作用(+薬剤によるインスリン非依存動員) → GLUT4 膜提示率の定常値。"""
    d = max(0.0, drive) ** HILL
    return M_MIN + (M_MAX - M_MIN) * d / (d + KD_X ** HILL)


def simulate(drug, preset="t2d", days=7, dose_mg=2.4, doses_per_day=1,
             first_dose_h=7.0, meals=None, treated=True, record=False):
    """血糖-インスリン-GLUT4 モデルを dt=1 min で積分する。

    戻り値: 最終 24 時間の指標 dict (record=True なら時系列も)
    """
    p = PRESETS[preset]
    meals = meals if meals is not None else DEFAULT_MEALS
    Si0, beta, kEGP, Gb, Ib = p["Si"], p["beta"], p["kEGP"], p["Gb"], p["Ib"]

    # --- 基礎状態からの自己校正 (基礎で収支が閉じるように Vmax と σ を決める)
    Xb = Si0 * (Ib - IZ)
    Mb = m_target(Xb)
    Vmax = (EGP0 - U_II) / max(1e-6, Mb * Gb / (KM + Gb))
    sec_basal = N_CLR * (Ib - I_MIN)

    # --- 薬剤 (無投薬なら全占有率 0)
    ki = drug["Ki_ng_per_mL"]
    ke = math.log(2.0) / (drug["t_half_h"] * 60.0)
    ka = drug["ka_per_min"]
    vd_ml = drug["Vd_L"] * 1000.0
    bbb = drug["BBB_index"]

    dose_times = set()
    if treated and dose_mg > 0:
        for d in range(days):
            for j in range(doses_per_day):
                t = int(round((d * 24 + first_dose_h + j * (24.0 / doses_per_day)) * 60))
                dose_times.add(t)

    # --- 状態
    G, I, X, M = Gb, Ib, Xb, Mb
    A_gut = A_c = C_e = Psi = 0.0
    uptake_cum = 0.0

    total = days * 1440
    day_start = total - 1440
    tir = tar = tbr = 0
    gsum = 0.0
    up_day = 0.0
    m_sum = 0.0
    occ_c_peak = 0.0
    occ_p_sum = 0.0
    clr_sum = 0.0
    g_peak = 0.0
    series = [] if record else None

    for t in range(total):
        if t in dose_times:
            A_gut += dose_mg

        # --- PK: 経口 1-コンパートメント + 効果部位(中枢)
        abs_rate = ka * A_gut
        A_gut += -abs_rate
        A_c += drug["F_oral"] * abs_rate - ke * A_c
        Cp = 1000.0 * A_c / vd_ml * 1000.0          # mg/mL → ng/mL
        occ_p = Cp / (Cp + ki)                       # 末梢(膵島を含む)占有率
        C_e += KEO * (bbb * Cp - C_e)
        occ_c = C_e / (C_e + ki)                     # 中枢(視床下部)占有率

        # --- 慢性感作 (中枢D2トーンのリセット: 日単位でゆっくり立ち上がる)
        Psi += (occ_c - Psi) / TAU_SENS

        # --- 食事による糖の出現速度 Ra(t)
        Ra = 0.0
        tod = t % 1440
        for (mh, carb) in meals:
            dtm = tod - mh * 60.0
            if dtm < 0:
                dtm += 1440.0
            if dtm < 600.0:
                Ra += carb * 1000.0 * F_MEAL * (dtm / (TAU_MEAL * TAU_MEAL)) * math.exp(-dtm / TAU_MEAL)

        # --- 肝糖放出 (インスリンで抑制・中枢D2でさらに抑制・低血糖で代償上昇)
        egp = EGP0 * (1.0 - ALPHA_HEP * Psi) / (1.0 + kEGP * (I - Ib) / max(1e-6, Ib))
        egp *= 1.0 + 2.5 * max(0.0, 85.0 - G) / 85.0   # 低血糖時の代償(グルカゴン等)
        egp = clamp(egp, 0.15 * EGP0, 2.2 * EGP0)

        # --- 細胞内への取り込み (GLUT4 依存) ← 本アプリの主目的
        U_cell = Vmax * M * G / (KM + G)
        dG = (Ra + egp - U_II - U_cell) / VG
        G = max(15.0, G + dG)

        # --- β細胞: 基礎分泌 + 応答性 β による追加分泌。膵島 D2 占有は分泌を抑制する
        sec = sec_basal * (1.0 + beta * SEC_GAIN * max(0.0, G - Gb) / 100.0)
        sec *= clamp((G - 40.0) / 30.0, 0.0, 1.0)      # 低血糖では分泌が止まる
        sec *= (1.0 - IOTA_ISLET * occ_p)
        I += sec - N_CLR * (I - I_MIN)
        I = max(I_MIN, I)

        # --- インスリン作用 X と GLUT4 膜提示率 M
        Si_eff = Si0 * (1.0 + drug["kappa_insulin_sens"] * Psi)
        X += P2 * (Si_eff * (I - IZ) - X)
        X = max(0.0, X)
        Xd = drug["kappa_glut4"] * 0.020 * occ_p      # インスリン非依存の動員
        M += (m_target(X + Xd) - M) / TAU_M
        M = clamp(M, M_MIN, M_MAX)

        uptake_cum += U_cell

        if t >= day_start:
            gsum += G
            tir += 1 if 70.0 <= G <= 180.0 else 0
            tar += 1 if G > 180.0 else 0
            tbr += 1 if G < 70.0 else 0
            up_day += U_cell
            m_sum += M
            clr_sum += U_cell / G          # 細胞内クリアランス (dL/min)
            g_peak = max(g_peak, G)
            occ_c_peak = max(occ_c_peak, occ_c)
            occ_p_sum += occ_p
            if record and t % 5 == 0:
                series.append(dict(t=(t - day_start) / 60.0, G=G, I=I, M=M,
                                   U=U_cell, Cp=Cp, occ_c=occ_c, occ_p=occ_p))

    mean_g = gsum / 1440.0
    hypo = 100.0 * tbr / 1440.0
    se = 100.0 * (0.55 * (occ_c_peak ** 1.2) + 0.30 * (occ_p_sum / 1440.0)) + 1.5 * hypo
    out = dict(
        preset=preset,
        mean_glucose=mean_g,
        eA1c=(mean_g + 46.7) / 28.7,
        TIR=100.0 * tir / 1440.0,
        TAR=100.0 * tar / 1440.0,
        TBR=hypo,
        uptake_g_per_day=up_day / 1000.0,
        cell_clearance_dL_min=clr_sum / 1440.0,
        peak_glucose=g_peak,
        mean_GLUT4=m_sum / 1440.0,
        peak_occ_central=occ_c_peak,
        mean_occ_peripheral=occ_p_sum / 1440.0,
        side_effect_index=clamp(se, 0.0, 100.0),
        total_uptake_g=uptake_cum / 1000.0,
    )
    if record:
        out["series"] = series
    return out


def score(res, base):
    """製造装置が最大化する目的関数 (無投薬の対照 base に対する改善度)。

      + 平均血糖の低下 (mg/dL)
      + 時間内割合 TIR の改善 (pt ×0.5)
      + 細胞内クリアランス(糖の取り込み能)の改善 (% ×0.30)
      − 低血糖時間 (% ×2.0)  − 副作用指標 (×0.30)
    """
    dclr = 100.0 * (res["cell_clearance_dL_min"] / max(1e-9, base["cell_clearance_dL_min"]) - 1.0)
    return ((base["mean_glucose"] - res["mean_glucose"])
            + 0.50 * (res["TIR"] - base["TIR"])
            + 0.30 * dclr
            - 2.00 * res["TBR"]
            - 0.30 * res["side_effect_index"])


# ------------------------------------------------------------------- CLI

NO_DRUG = dict(name="(無投薬)", **{k: v for k, v in dict(
    pKi_D2=9.0, Ki_ng_per_mL=1e9, MW=300.0, t_half_h=6.0, F_oral=0.0,
    ka_per_min=0.02, Vd_L=100.0, BBB_index=0.0, kappa_insulin_sens=0.0,
    kappa_glut4=0.0).items()})


def forge(args, n=None, feed=None, kill=None, kappa=None, seed=None, steps=None):
    fld = MorphogenField(n=n or args.grid, feed=feed if feed is not None else args.feed,
                         kill=kill if kill is not None else args.kill,
                         kappa=kappa if kappa is not None else args.kappa,
                         seed=seed if seed is not None else args.seed)
    fld.step(steps or args.rd_steps)
    d = forge_drug(fld.descriptors())
    d["forge"] = dict(grid=fld.n, feed=fld.feed, kill=fld.kill, kappa=fld.kappa,
                      seed=fld.seed, steps=steps or args.rd_steps)
    return d


def fmt_row(tag, r):
    return ("  %-14s 平均血糖 %6.1f | 最高 %6.1f mg/dL | eA1c %4.1f%% | TIR %5.1f%% | 低血糖 %4.1f%%\n"
            "  %-14s 細胞内取込 %6.1f g/日 | 細胞内クリアランス %5.3f dL/min | GLUT4膜提示 %4.1f%%") % (
        tag, r["mean_glucose"], r["peak_glucose"], r["eA1c"], r["TIR"], r["TBR"],
        "", r["uptake_g_per_day"], r["cell_clearance_dL_min"], 100.0 * r["mean_GLUT4"])


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Ω-GlucoGate Forge — 形態形成場によるドーパミン作動性 糖取り込み薬剤の製造装置シミュレータ (概念・非医療)")
    ap.add_argument("--preset", default="t2d", choices=sorted(PRESETS), help="病態プリセット")
    ap.add_argument("--days", type=int, default=7, help="投与日数 (最終24hで評価)")
    ap.add_argument("--dose", type=float, default=2.4, help="1回投与量 (mg)")
    ap.add_argument("--doses-per-day", type=int, default=1, help="1日投与回数")
    ap.add_argument("--first-dose", type=float, default=7.0, help="初回投与時刻 (時)")
    ap.add_argument("--grid", type=int, default=48, help="形態形成場の格子数")
    ap.add_argument("--rd-steps", type=int, default=500, help="反応拡散の反復数")
    ap.add_argument("--feed", type=float, default=0.037, help="Gray-Scott F (供給率)")
    ap.add_argument("--kill", type=float, default=0.060, help="Gray-Scott k (消滅率)")
    ap.add_argument("--kappa", type=float, default=1.0, help="Γカーネル κ (形態形成場の変調)")
    ap.add_argument("--seed", type=int, default=7, help="種 (同じ種は同じ薬剤を鍛造)")
    ap.add_argument("--auto-forge", type=int, default=0, metavar="N",
                    help="N 候補を自動鍛造して最良の薬剤を選ぶ")
    ap.add_argument("--csv", help="最終24hの時系列を CSV 出力")
    ap.add_argument("--json", help="薬剤スペック + 指標を JSON 出力")
    args = ap.parse_args(argv)

    print("Ω-GlucoGate Forge — 形態形成場 薬剤製造装置 (概念シミュレーション・非医療)")
    print("病態: %s / %d 日投与 / %.2f mg × %d 回/日" %
          (PRESETS[args.preset]["label"], args.days, args.dose, args.doses_per_day))

    if args.auto_forge > 0:
        print("\n[自動鍛造] %d 候補を探索中..." % args.auto_forge)
        sdays = min(args.days, 4)
        ctrl = simulate(NO_DRUG, args.preset, days=sdays, treated=False)
        best, best_s, st = None, -1e9, args.seed
        for i in range(args.auto_forge):
            st = (st * 1103515245 + 12345) & 0x7FFFFFFF
            f = 0.026 + (st % 1000) / 1000.0 * 0.032
            st = (st * 1103515245 + 12345) & 0x7FFFFFFF
            k = 0.055 + (st % 1000) / 1000.0 * 0.010
            st = (st * 1103515245 + 12345) & 0x7FFFFFFF
            kp = 0.2 + (st % 1000) / 1000.0 * 2.4
            d = forge(args, n=32, feed=f, kill=k, kappa=kp, seed=args.seed + i, steps=400)
            r = simulate(d, args.preset, days=sdays, dose_mg=args.dose,
                         doses_per_day=args.doses_per_day, first_dose_h=args.first_dose)
            s = score(r, ctrl)
            print("   候補%2d  F=%.3f k=%.3f κ=%.2f → pKi %.2f / t½ %.1fh / BBB %.2f / 得点 %.1f"
                  % (i + 1, f, k, kp, d["pKi_D2"], d["t_half_h"], d["BBB_index"], s))
            if s > best_s:
                best, best_s = d, s
        drug = best
    else:
        drug = forge(args)

    print("\n[鍛造された薬剤] %s" % drug["name"])
    print("  D2 親和性 pKi = %.2f (Ki %.2f ng/mL) / 分子量 %.0f" %
          (drug["pKi_D2"], drug["Ki_ng_per_mL"], drug["MW"]))
    print("  半減期 %.1f h / 経口F %.0f%% / Vd %.0f L / BBB透過指数 %.2f" %
          (drug["t_half_h"], 100 * drug["F_oral"], drug["Vd_L"], drug["BBB_index"]))
    print("  κ_インスリン感受性 %.2f / κ_GLUT4動員 %.2f" %
          (drug["kappa_insulin_sens"], drug["kappa_glut4"]))
    print("  形態記述子: " + ", ".join("%s=%.3f" % (k, v) for k, v in drug["descriptors"].items()))

    base = simulate(NO_DRUG, args.preset, days=args.days, treated=False)
    treat = simulate(drug, args.preset, days=args.days, dose_mg=args.dose,
                     doses_per_day=args.doses_per_day, first_dose_h=args.first_dose,
                     record=True)
    print("\n[最終24時間の指標]")
    print(fmt_row("対照(無投薬)", base))
    print(fmt_row("投薬", treat))
    print("  Δ平均血糖 %+.1f mg/dL / ΔTIR %+.1f pt / Δ細胞内クリアランス %+.1f %% / 副作用指標 %.0f/100"
          % (treat["mean_glucose"] - base["mean_glucose"], treat["TIR"] - base["TIR"],
             100.0 * (treat["cell_clearance_dL_min"] / base["cell_clearance_dL_min"] - 1.0),
             treat["side_effect_index"]))
    print("  中枢D2占有 ピーク %.0f%% / 末梢(膵島)D2占有 平均 %.0f%%"
          % (100 * treat["peak_occ_central"], 100 * treat["mean_occ_peripheral"]))

    if args.csv:
        with open(args.csv, "w", encoding="utf-8") as fp:
            fp.write("t_h,glucose_mg_dL,insulin_uU_mL,GLUT4_membrane,uptake_mg_min,"
                     "plasma_drug_ng_mL,occ_central,occ_peripheral\n")
            for s in treat["series"]:
                fp.write("%.4f,%.3f,%.4f,%.5f,%.4f,%.5f,%.5f,%.5f\n" %
                         (s["t"], s["G"], s["I"], s["M"], s["U"], s["Cp"], s["occ_c"], s["occ_p"]))
        print("\nCSV を書き出しました: %s" % args.csv)

    if args.json:
        blob = dict(app="omega_glucogate_forge", version="1.0.0",
                    disclaimer="概念シミュレーション・非医療。実在の医薬品ではありません。",
                    drug=drug, condition=PRESETS[args.preset],
                    regimen=dict(dose_mg=args.dose, doses_per_day=args.doses_per_day,
                                 first_dose_h=args.first_dose, days=args.days,
                                 meals=DEFAULT_MEALS),
                    metrics_control={k: v for k, v in base.items() if k != "series"},
                    metrics_treated={k: v for k, v in treat.items() if k != "series"})
        with open(args.json, "w", encoding="utf-8") as fp:
            json.dump(blob, fp, ensure_ascii=False, indent=1)
        print("スペックを書き出しました: %s" % args.json)

    print("\n⚠ 本結果は概念モデルの出力であり、医療上の判断には使用できません。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
