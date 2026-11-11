/* imaging.c — see imaging.h */
#include "imaging.h"
#include "gamma_thermal.h"   /* om_gamma を HRF に再利用 */
#include <math.h>
#include <string.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double mri_spin_echo(double proton_density, double t1_ms, double t2_ms,
                     double tr_ms, double te_ms)
{
    if (t1_ms <= 0.0 || t2_ms <= 0.0) return 0.0;
    return proton_density
         * (1.0 - exp(-tr_ms / t1_ms))
         * exp(-te_ms / t2_ms);
}

struct tissue { const char *name; double t1; double t2; };
static const struct tissue TISSUES[] = {
    {"gray",  1100.0,  90.0},   /* 灰白質 */
    {"white",  560.0,  80.0},   /* 白質   */
    {"csf",   4000.0, 2000.0},  /* 脳脊髄液 */
    {"fat",    340.0,  80.0},
    {"muscle", 900.0,  50.0},
    {"blood", 1500.0, 200.0},
};

int mri_tissue_params(const char *tissue, double *t1_ms, double *t2_ms)
{
    for (size_t i = 0; i < sizeof(TISSUES)/sizeof(TISSUES[0]); ++i) {
        if (strcmp(tissue, TISSUES[i].name) == 0) {
            if (t1_ms) *t1_ms = TISSUES[i].t1;
            if (t2_ms) *t2_ms = TISSUES[i].t2;
            return 1;
        }
    }
    return 0;
}

double fmri_hrf(double t_sec)
{
    if (t_sec < 0.0) return 0.0;
    /* 正準二重ガンマHRF: peak gamma(6,1) - 1/6 * undershoot gamma(16,1) */
    double a1 = 6.0, a2 = 16.0, b = 1.0, c = 1.0 / 6.0;
    double g1 = pow(t_sec, a1 - 1.0) * exp(-t_sec / b)
                / (pow(b, a1) * om_gamma(a1));
    double g2 = pow(t_sec, a2 - 1.0) * exp(-t_sec / b)
                / (pow(b, a2) * om_gamma(a2));
    return g1 - c * g2;
}

void fmri_bold(const double *act, double *out, int n, double dt_sec)
{
    for (int i = 0; i < n; ++i) {
        double acc = 0.0;
        for (int j = 0; j <= i; ++j)
            acc += act[j] * fmri_hrf((i - j) * dt_sec) * dt_sec;
        out[i] = acc;
    }
}

void topography_project(const double *sources, const double *src_angle,
                        int n_src, double *out, int electrodes)
{
    for (int e = 0; e < electrodes; ++e) {
        double ang = 2.0 * M_PI * e / (double)electrodes;
        double ex = cos(ang), ey = sin(ang);
        double v = 0.0;
        for (int s = 0; s < n_src; ++s) {
            /* 線源は半径0.6の同心円上に配置 */
            double sx = 0.6 * cos(src_angle[s]);
            double sy = 0.6 * sin(src_angle[s]);
            double dx = ex - sx, dy = ey - sy;
            double r2 = dx*dx + dy*dy + 0.05; /* 正則化 */
            v += sources[s] / r2;
        }
        out[e] = v;
    }
}

double ct_path_transmission(const double *mu, const double *thickness, int layers)
{
    double tau = 0.0; /* 光学的厚み Σ μ·x */
    for (int i = 0; i < layers; ++i)
        tau += mu[i] * thickness[i];
    return exp(-tau); /* I/I0 */
}

double ct_hounsfield(double mu_tissue, double mu_water)
{
    if (mu_water <= 0.0) return 0.0;
    return 1000.0 * (mu_tissue - mu_water) / mu_water;
}
