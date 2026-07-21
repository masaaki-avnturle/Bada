/* gamma_thermal.h
 *
 * ガンマ関数の「大域的部分積分多様体」の熱エネルギー核
 * Global integration-by-parts manifold thermal-energy core (Yamaguchi framework).
 *
 * 中核方程式 / core equation (explorerfiles, l.148):
 *      T' = ∫ Γ(γ)' dx_m
 * 統一場との同型 / unified-field isomorphism (explorerfiles, l.334):
 *      E = m c^2 - 1/2 m v^2 = ||ds^2|| = ∫ Γ(γ)' dx_m
 *
 * 本モジュールは教育・可視化のための数値モデルである。実在の診断・治療には用いない。
 * This is an educational numerical model only — not for real diagnosis or therapy.
 */
#ifndef OMEGA_GAMMA_THERMAL_H
#define OMEGA_GAMMA_THERMAL_H

/* Γ(x) — Lanczos 近似 */
double om_gamma(double x);

/* lnΓ(x) — 対数ガンマ（オーバーフロー回避用） */
double om_lgamma(double x);

/* ψ(x) — ディガンマ関数 (Γ'(x)/Γ(x)) */
double om_digamma(double x);

/* Γ'(x) = Γ(x)·ψ(x) — ガンマ関数の微分（被積分関数） */
double om_gamma_prime(double x);

/*
 * 大域的部分積分多様体の熱エネルギー
 *   T' = ∫_{gamma_lo}^{gamma_hi} Γ(γ)' dx_m
 * を合成シンプソン則で数値積分する。steps は偶数の分割数。
 * 戻り値は無次元の熱エネルギー量 [Ω-thermal units]。
 */
double om_thermal_energy(double gamma_lo, double gamma_hi, int steps);

/*
 * 熱エネルギー量を摂氏温度へ写像する（多様体スケーリング）。
 *   T(°C) = baseline + scale * tanh(energy / scale)
 * tanh により生理的レンジに飽和させる（暴走を抑える大域的境界）。
 */
double om_thermal_to_celsius(double energy, double baseline, double scale);

#endif /* OMEGA_GAMMA_THERMAL_H */
