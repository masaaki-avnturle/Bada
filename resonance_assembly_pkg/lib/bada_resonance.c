/* bada_resonance.c — engine implementation. See include/bada_resonance.h. */
#include "bada_resonance.h"

#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ====================================================================
 *  Bada::Special
 * ================================================================== */

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
#define LANCZOS_G 7

double bada_gamma(double x)
{
    if (x == 0.0) return INFINITY;
    if (x < 0.5) {
        /* Reflection: Gamma(x)Gamma(1-x) = pi / sin(pi x) */
        return M_PI / (sin(M_PI * x) * bada_gamma(1.0 - x));
    }
    x -= 1.0;
    double a = LANCZOS_C[0];
    double t = x + LANCZOS_G + 0.5;
    for (int i = 1; i < LANCZOS_G + 2; i++)
        a += LANCZOS_C[i] / (x + i);
    return sqrt(2.0 * M_PI) * pow(t, x + 0.5) * exp(-t) * a;
}

static double bada_log_gamma(double x) { return log(fabs(bada_gamma(x))); }

double bada_beta(double p, double q)
{
    return exp(bada_log_gamma(p) + bada_log_gamma(q) - bada_log_gamma(p + q));
}

double bada_zeta_gauge(double p, double q, double x)
{
    double lx = log(x);
    if (fabs(lx) < 1e-15) return INFINITY;
    return bada_beta(p, q) / lx;
}

double bada_x_log_x(double x)
{
    if (x <= 0.0) return 0.0;
    return x * log(x);
}

double bada_manifold_element(double x)
{
    if (x <= 1.0) return 1.0;
    double xl = bada_x_log_x(x);
    if (fabs(xl) < 1e-9) return 1.0;
    return 1.0 / (xl * xl);
}

/* ====================================================================
 *  Bada operators  <-  -<  >-
 * ================================================================== */

double complex bada_op_left(double chi, double x)
{
    /* pi(chi,x) = [i pi, f(x)] -> i*pi*chi*log(x) */
    if (x <= 0.0) x = 1e-12;
    return (0.0 + 1.0 * I) * M_PI * chi * log(x);
}

double bada_op_mid(double x) { return bada_manifold_element(x); }

double bada_op_right(double x)
{
    /* (+)(i hbar grad)^L = e^{-x log x} */
    return exp(-bada_x_log_x(x));
}

/* ====================================================================
 *  Arithmetic-Geometric Mean
 * ================================================================== */

double bada_agm(double a, double b)
{
    a = fabs(a);
    b = fabs(b);
    if (a == 0.0 || b == 0.0) return 0.0;
    for (int i = 0; i < 100; i++) {
        double an = 0.5 * (a + b);     /* arithmetic mean (相加平均) */
        double bn = sqrt(a * b);       /* geometric mean  (相乗平均) */
        a = an; b = bn;
        if (fabs(a - b) <= 1e-15 * a) break;
    }
    return 0.5 * (a + b);
}

/* ====================================================================
 *  Complex rotational body — special relativity error correction
 * ================================================================== */

double bada_lorentz_gamma(double v_over_c)
{
    double b = fabs(v_over_c);
    if (b > 0.999999999) b = 0.999999999;
    return 1.0 / sqrt(1.0 - b * b);
}

double complex bada_rotate(double value, double theta)
{
    return value * cexp((0.0 + 1.0 * I) * theta);
}

BadaRelCorrection bada_rel_correct(double f_observed, double omega_rot,
                                   double radius, double t)
{
    BadaRelCorrection r;
    r.v = fabs(omega_rot) * fabs(radius);
    r.beta = r.v / BADA_C_LIGHT;
    r.gamma = bada_lorentz_gamma(r.beta);
    r.f_observed = f_observed;
    /* Moving clock runs slow: proper frequency = gamma * observed frequency. */
    r.f_proper = r.gamma * f_observed;
    r.df = r.f_proper - r.f_observed;
    r.phasor = cexp((0.0 + 1.0 * I) * omega_rot * t);
    return r;
}

/* ====================================================================
 *  Modal spectrum / secular roots  (Galois invariants)
 * ================================================================== */

BadaModalSpectrum bada_modal_spectrum(int storeys, double mass, double stiffness)
{
    BadaModalSpectrum s;
    memset(&s, 0, sizeof s);
    if (storeys < 1) storeys = 1;
    if (storeys > BADA_MAX_MODES) storeys = BADA_MAX_MODES;
    if (mass <= 0.0) mass = 1.0;
    if (stiffness <= 0.0) stiffness = 1.0;

    s.n_modes = storeys;
    double base = sqrt(stiffness / mass);     /* sqrt(k/m) */
    double sum_eig = 0.0, prod_eig = 1.0;

    for (int j = 1; j <= storeys; j++) {
        double arg = (2.0 * j - 1.0) * M_PI / (2.0 * (2.0 * storeys + 1.0));
        double omega = 2.0 * base * sin(arg);          /* rad/s */
        double f = omega / (2.0 * M_PI);               /* Hz */
        s.f[j - 1] = f;
        double eig = omega * omega;                    /* eigenvalue omega^2 */
        sum_eig += eig;
        prod_eig *= eig;
    }
    s.sum_eig = sum_eig;     /* trace  (Galois-invariant, sum of roots) */
    s.prod_eig = prod_eig;   /* det    (Galois-invariant, product of roots) */

    /* Manifold entropy invariant Xi over the normalised modal "measure":
     * treat the modal energies as a probability distribution, integrate the
     * manifold element along the rank coordinate, and read the zeta gauge. */
    double H = 0.0, M = 0.0;
    if (sum_eig > 0.0) {
        for (int j = 0; j < storeys; j++) {
            double omega = 2.0 * M_PI * s.f[j];
            double p = (omega * omega) / sum_eig;
            if (p > 0.0) H -= p * log(p);          /* Shannon entropy */
            M += p * bada_manifold_element(j + 2.0);
        }
    }
    s.xi_manifold = bada_zeta_gauge(H + 1.0, M + 1.0, storeys + 1.0);
    return s;
}

int bada_nearest_mode(const BadaModalSpectrum *s, double f_exc)
{
    int best = 0;
    double bestd = INFINITY;
    for (int j = 0; j < s->n_modes; j++) {
        double d = fabs(s->f[j] - f_exc);
        if (d < bestd) { bestd = d; best = j; }
    }
    return best;
}

/* ====================================================================
 *  Full diagnosis
 * ================================================================== */

BadaTarget bada_default_target(void)
{
    BadaTarget t;
    memset(&t, 0, sizeof t);
    strncpy(t.name, "Sample Steel Frame", sizeof t.name - 1);
    t.storeys      = 12;
    t.mass         = 4.0e5;     /* 400 t modal storey mass */
    t.stiffness    = 8.0e8;     /* 800 MN/m storey stiffness */
    t.damping      = 0.02;      /* 2% structural damping */
    t.exc_freq     = 0.50;      /* Hz excitation (e.g. machinery / wind vortex) */
    t.crack_a      = 0.003;     /* 3 mm flaw */
    t.Y_factor     = 1.12;      /* edge-crack geometry factor */
    t.sigma_static = 120.0;     /* MPa static stress */
    t.Kic          = 80.0;      /* MPa*sqrt(m) toughness (structural steel) */
    t.rot_radius   = 1.5;       /* m rotating-joint radius */
    t.rot_omega    = 314.16;    /* rad/s ~ 3000 rpm */
    t.member_dim   = 400.0;     /* mm governing plate/section depth */
    t.target_ratio = 1.30;      /* detune so f_exc/f_mode = 1.30 (mode below) */
    return t;
}

BadaDiagnosis bada_diagnose(const BadaTarget *t)
{
    BadaDiagnosis d;
    memset(&d, 0, sizeof d);

    /* 1. Relativistic correction of the excitation reading FIRST, so the
     *    corrected (proper) frequency drives the resonance check. This is the
     *    "data alternately corrected" coupling. */
    d.rel = bada_rel_correct(t->exc_freq, t->rot_omega, t->rot_radius, 0.0);
    double f_exc = d.rel.f_proper;

    /* 2. Modal spectrum + dangerous (nearest) mode. */
    d.spectrum = bada_modal_spectrum(t->storeys, t->mass, t->stiffness);
    d.mode_index = bada_nearest_mode(&d.spectrum, f_exc);
    d.f_mode = d.spectrum.f[d.mode_index];
    d.xi_invariant = d.spectrum.xi_manifold;

    /* 3. Resonance dynamic amplification. */
    double r = (d.f_mode > 0.0) ? f_exc / d.f_mode : 0.0;
    d.ratio = r;
    double zeta = (t->damping > 0.0) ? t->damping : 1e-6;
    double denom = sqrt((1.0 - r * r) * (1.0 - r * r) + (2.0 * zeta * r) * (2.0 * zeta * r));
    d.daf = (denom > 1e-12) ? 1.0 / denom : 1.0 / (2.0 * zeta);
    d.sigma_dyn = d.daf * t->sigma_static;

    /* 4. Linear-elastic fracture mechanics durability check.
     *    K_I = Y * sigma * sqrt(pi a);  a_crit = (1/pi)(K_IC/(Y sigma))^2. */
    double Y = (t->Y_factor > 0.0) ? t->Y_factor : 1.0;
    d.Ki = Y * d.sigma_dyn * sqrt(M_PI * t->crack_a);             /* MPa*sqrt(m) */
    double denomK = Y * d.sigma_dyn;
    d.a_crit = (denomK > 1e-12)
               ? (1.0 / M_PI) * (t->Kic / denomK) * (t->Kic / denomK)
               : INFINITY;
    d.safety_factor = (d.Ki > 1e-12) ? t->Kic / d.Ki : INFINITY;
    d.safe = (d.safety_factor >= 1.0) && (fabs(r - 1.0) > 0.15);

    /* 5. Assembly-precision adjustment via AGM (相加相乗平均).
     *    Retarget stiffness so the dangerous mode sits at the safe ratio r*:
     *      omega ~ sqrt(k)  =>  k_target = k * (f_target / f_mode)^2
     *    with f_target = f_exc / r*.  Then blend the arithmetic-mean and
     *    geometric-mean stiffness candidates with the AGM to get a stable
     *    target, and translate dk/k into a dimensional tolerance via I ~ h^3
     *    (so dk/k ~ 3 dh/h). */
    double rstar = (t->target_ratio > 0.0) ? t->target_ratio : 1.30;
    double f_target = f_exc / rstar;                  /* desired modal freq */
    double scale = (d.f_mode > 0.0) ? (f_target / d.f_mode) : 1.0;
    d.k_target = t->stiffness * scale * scale;
    d.k_arith  = 0.5 * (t->stiffness + d.k_target);   /* 相加平均 */
    d.k_geom   = sqrt(t->stiffness * d.k_target);     /* 相乗平均 */
    d.k_agm    = bada_agm(d.k_arith, d.k_geom);       /* AGM-blended target */
    d.dk_rel   = (t->stiffness > 0.0) ? (d.k_agm - t->stiffness) / t->stiffness : 0.0;
    d.dh_mm    = (t->member_dim / 3.0) * d.dk_rel;    /* required precision adj. */

    return d;
}
