/* lib/manifold_entropy.c — the gamma-function global-partial-integral
 * manifold entropy equation.
 *
 *   dmu(x) = 1 / (x log x)^2                      (manifold line element)
 *   M      = ∬ 1/(x log x)^2 dμ                    (global partial integral)
 *   H      = -Σ p log p                            (Shannon entropy)
 *   Xi     = beta(H+1, M+1) / log(N+1)             (zeta = beta/log x gauge)
 *
 * Xi is the scalar the whole package treats as the "entropy equation output":
 * the source-code generator, the environment image and the sound are all
 * seeded from it. This is genuine mathematics (Lanczos Gamma, Shannon H); the
 * downstream *use* of Xi as a generative seed is the conceptual layer.
 */
#include <math.h>
#include <string.h>
#include "../include/omega_bluebird.h"

double ob_gamma(double x)
{
    static const double g = 7.0;
    static const double c[9] = {
        0.99999999999980993, 676.5203681218851, -1259.1392167224028,
        771.32342877765313, -176.61502916214059, 12.507343278686905,
        -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
    };
    if (x < 0.5) return OB_PI / (sin(OB_PI * x) * ob_gamma(1.0 - x));
    x -= 1.0;
    double a = c[0], t = x + g + 0.5;
    for (int i = 1; i < 9; i++) a += c[i] / (x + i);
    return sqrt(2.0 * OB_PI) * pow(t, x + 0.5) * exp(-t) * a;
}

double ob_beta(double a, double b)
{
    return ob_gamma(a) * ob_gamma(b) / ob_gamma(a + b);
}

double ob_manifold_element(double x)
{
    if (x <= 1.0) return 1.0;                 /* safe Napier step x->1  */
    double xl = x * log(x);
    if (fabs(xl) < 1e-9) return 1.0;
    return 1.0 / (xl * xl);
}

ManifoldEntropy ob_manifold_entropy(const unsigned char *buf, size_t n)
{
    ManifoldEntropy me = {0.0, 0.0, 0.0, 0.0};
    if (!buf || n == 0) return me;

    /* byte histogram -> probability measure */
    long hist[256]; memset(hist, 0, sizeof(hist));
    for (size_t i = 0; i < n; i++) hist[buf[i]]++;

    /* Shannon entropy H and a rank-sorted probability list */
    double H = 0.0; double p[256]; int m = 0;
    for (int i = 0; i < 256; i++) if (hist[i]) {
        double pi = (double)hist[i] / (double)n;
        H -= pi * log2(pi);
        p[m++] = pi;
    }
    /* sort probabilities high->low (small array, insertion sort) */
    for (int i = 1; i < m; i++) {
        double key = p[i]; int j = i - 1;
        while (j >= 0 && p[j] < key) { p[j + 1] = p[j]; j--; }
        p[j + 1] = key;
    }
    /* global partial integral of the manifold element against the measure */
    double M = 0.0;
    for (int i = 0; i < m; i++) {
        double x = i + 2.0;                   /* rank coordinate, log x>0 */
        M += p[i] * ob_manifold_element(x);
    }

    me.entropy           = H;
    me.manifold_integral = M;
    me.extent            = (double)m;         /* distinct-symbol extent   */
    me.invariant         = ob_beta(H + 1.0, M + 1.0) / log((double)m + 2.0);
    return me;
}
