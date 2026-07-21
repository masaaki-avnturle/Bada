/* gamma_thermal.c — see gamma_thermal.h */
#include "gamma_thermal.h"
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* Lanczos g=7, n=9 coefficients */
static const double LANCZOS_G = 7.0;
static const double LANCZOS_C[9] = {
    0.99999999999980993,
    676.5203681218851,
   -1259.1392167224028,
    771.32342877765313,
   -176.61502916214059,
    12.507343278686905,
   -0.13857109526572012,
    9.9843695780195716e-6,
    1.5056327351493116e-7
};

double om_lgamma(double x)
{
    /* reflection for x < 0.5 */
    if (x < 0.5) {
        /* lnΓ(x) = ln(π/sin(πx)) - lnΓ(1-x) */
        return log(M_PI / fabs(sin(M_PI * x))) - om_lgamma(1.0 - x);
    }
    x -= 1.0;
    double a = LANCZOS_C[0];
    double t = x + LANCZOS_G + 0.5;
    for (int i = 1; i < 9; ++i)
        a += LANCZOS_C[i] / (x + (double)i);
    return 0.5 * log(2.0 * M_PI) + (x + 0.5) * log(t) - t + log(a);
}

double om_gamma(double x)
{
    if (x < 0.5)
        return M_PI / (sin(M_PI * x) * om_gamma(1.0 - x));
    return exp(om_lgamma(x));
}

double om_digamma(double x)
{
    double result = 0.0;
    /* reflection for x <= 0 */
    if (x <= 0.0 && x == floor(x))
        return NAN; /* poles at non-positive integers */
    if (x < 0.0)
        return om_digamma(1.0 - x) - M_PI / tan(M_PI * x);
    /* recurrence to push x up >= 6 */
    while (x < 6.0) {
        result -= 1.0 / x;
        x += 1.0;
    }
    /* asymptotic series */
    double inv = 1.0 / x;
    double inv2 = inv * inv;
    result += log(x) - 0.5 * inv
            - inv2 * (1.0/12.0
                    - inv2 * (1.0/120.0
                            - inv2 * (1.0/252.0)));
    return result;
}

double om_gamma_prime(double x)
{
    return om_gamma(x) * om_digamma(x);
}

double om_thermal_energy(double gamma_lo, double gamma_hi, int steps)
{
    if (steps < 2) steps = 2;
    if (steps % 2 != 0) steps += 1; /* Simpson needs even intervals */

    double h = (gamma_hi - gamma_lo) / (double)steps;
    double sum = om_gamma_prime(gamma_lo) + om_gamma_prime(gamma_hi);

    for (int i = 1; i < steps; ++i) {
        double x = gamma_lo + i * h;
        double w = (i % 2 == 0) ? 2.0 : 4.0;
        sum += w * om_gamma_prime(x);
    }
    return (h / 3.0) * sum;
}

double om_thermal_to_celsius(double energy, double baseline, double scale)
{
    if (scale <= 0.0) scale = 1.0;
    return baseline + scale * tanh(energy / scale);
}
