/* sensors.c — see sensors.h */
#include "sensors.h"
#include <math.h>
#include <stdlib.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* Box-Muller による標準正規乱数 */
static double gauss(unsigned *seed)
{
    double u1 = (rand_r(seed) + 1.0) / ((double)RAND_MAX + 2.0);
    double u2 = (rand_r(seed) + 1.0) / ((double)RAND_MAX + 2.0);
    return sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);
}

double ir_sensor_read(double object_temp_c, double emissivity,
                      double ambient_c, double noise_sigma, unsigned *seed)
{
    if (emissivity <= 0.0) emissivity = 0.95; /* 皮膚の典型値 */
    double T = object_temp_c + 273.15;
    double Ta = ambient_c + 273.15;
    /* 検出される正味放射出力 (物体放射 - 背景放射の反射分) */
    double M = emissivity * OM_SIGMA * (T * T * T * T)
             + (1.0 - emissivity) * OM_SIGMA * (Ta * Ta * Ta * Ta);
    /* 放射輝度から温度へ逆算 (検出器は ε で較正済みと仮定) */
    double T_est = pow(M / (OM_SIGMA), 0.25);
    double t_c = T_est - 273.15;
    if (seed && noise_sigma > 0.0) t_c += noise_sigma * gauss(seed);
    return t_c;
}

double thermometer_read(double true_temp_c, double prev, double tau,
                        double noise_sigma, unsigned *seed)
{
    if (tau < 0.0) tau = 0.0;
    if (tau > 1.0) tau = 1.0;
    /* 一次遅れ: y = (1-tau)*true + tau*prev */
    double y = (1.0 - tau) * true_temp_c + tau * prev;
    if (seed && noise_sigma > 0.0) y += noise_sigma * gauss(seed);
    return y;
}

double sensor_fuse(double ir_c, double ir_var,
                   double th_c, double th_var, double *fused_var)
{
    if (ir_var <= 0.0) ir_var = 1e-6;
    if (th_var <= 0.0) th_var = 1e-6;
    double wi = 1.0 / ir_var;
    double wt = 1.0 / th_var;
    double fused = (wi * ir_c + wt * th_c) / (wi + wt);
    if (fused_var) *fused_var = 1.0 / (wi + wt);
    return fused;
}
