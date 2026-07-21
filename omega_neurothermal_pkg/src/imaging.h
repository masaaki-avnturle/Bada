/* imaging.h
 *
 * 画像診断装置の機能モデル（シミュレーション）。
 *   - MRI  : T1/T2 緩和に基づくボクセル信号強度
 *   - fMRI : 神経活動 → BOLD 血行動態応答(HRF)
 *   - Brain topography : 線源(基底核エネルギー)の頭皮電極投影
 *   - CT   : Beer-Lambert 減衰による Hounsfield 値(脳→末端パス)
 *
 * すべて合成データに対する数値モデルであり、実画像診断には用いない。
 */
#ifndef OMEGA_IMAGING_H
#define OMEGA_IMAGING_H

#include <stddef.h>

/* ---- MRI: スピンエコー信号 S = ρ(1-e^{-TR/T1}) e^{-TE/T2} ---- */
double mri_spin_echo(double proton_density, double t1_ms, double t2_ms,
                     double tr_ms, double te_ms);

/* 組織プリセット名から (T1,T2) を引く。未知なら 0 を返す。 */
int mri_tissue_params(const char *tissue, double *t1_ms, double *t2_ms);

/* ---- fMRI: 正準HRF (二重ガンマ) を t 秒で評価 ---- */
double fmri_hrf(double t_sec);

/* 神経活動列 act[n] (Δt秒間隔) を HRF と畳み込み、BOLD 列 out[n] を返す */
void fmri_bold(const double *act, double *out, int n, double dt_sec);

/* ---- 脳トポグラフィ: 線源強度を電極へ 1/r^2 投影 ---- */
/* sources: 線源強度配列(基底核など)、src_pos: 各線源の角度[rad]
 * electrodes 個の頭皮電極(円周上等配置)の電位 out[] を返す。 */
void topography_project(const double *sources, const double *src_angle,
                        int n_src, double *out, int electrodes);

/* ---- CT: Beer-Lambert ---- */
/* mu[] (各層の線減弱係数 cm^-1) と thickness[] (cm) からパス全体の
 * 透過率と平均 Hounsfield 値を計算する。 */
double ct_path_transmission(const double *mu, const double *thickness, int layers);
double ct_hounsfield(double mu_tissue, double mu_water);

#endif /* OMEGA_IMAGING_H */
