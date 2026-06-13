/* bada_resonance.h — Bada language (C port) for resonance-driven
 * assembly-precision tuning in durability / fracture mechanics.
 *
 * This is the C realisation of the Yamaguchi / TupleSpace framework that the
 * `bada_ruby` library expresses in Ruby:
 *
 *   Bada::Special          -> beta(p,q), zeta_gauge, x_log_x, box (rotation)
 *   Bada::Manifold         -> global partial integral manifold  1/(x log x)^2
 *   Bada::ErrorCorrection  -> complex rotational body / spinning-top SR
 *
 * On top of that base it adds the engineering layer the dialog application
 * needs: the secular (characteristic) polynomial of a shear-building whose
 * roots are the modal eigen-frequencies, the Galois-invariant symmetric
 * functions of those roots, the resonance dynamic-amplification factor, a
 * linear-elastic fracture-mechanics durability check, and the arithmetic-
 * geometric mean (AGM, 相加相乗平均) retuning that yields the required
 * assembly-precision adjustment.
 *
 * Pure C11 + libm, so it compiles and runs anywhere — exactly like the Ruby
 * library is "pure stdlib so it runs anywhere".
 *
 *  (c) 2025 Masaaki Yamaguchi — Global Differential Manifold Research.
 */
#ifndef BADA_RESONANCE_H
#define BADA_RESONANCE_H

#include <complex.h>
#include <stddef.h>

#define BADA_C_LIGHT 299792458.0   /* speed of light, m/s */
#define BADA_MAX_MODES 256

/* ----------------------------------------------------------------------
 *  Bada::Special  — the framework's special functions, ported to C.
 * -------------------------------------------------------------------- */

/* Gamma via the Lanczos approximation (g = 7, n = 9), reflection for x<0.5. */
double bada_gamma(double x);

/* Euler beta  B(p,q) = Gamma(p)Gamma(q)/Gamma(p+q) — the heart of
 * "Beta function reveal with global differential manifold". */
double bada_beta(double p, double q);

/* The signature gauge  zeta(s) = beta(p,q) / log(x). */
double bada_zeta_gauge(double p, double q, double x);

/* x log x — the Napier ("neipa") circle step. */
double bada_x_log_x(double x);

/* Manifold line element  dmu(x) = 1 / (x log x)^2, safe at x -> 1. */
double bada_manifold_element(double x);

/* ----------------------------------------------------------------------
 *  Bada operators (README §"演算子一覧"), as C functions.
 *
 *     <-   bada_op_left  : pi(chi,x) = [i pi, f(x)]   non-commutative left
 *     -<   bada_op_mid   : integral of the manifold element (curvature)
 *     >-   bada_op_right : (+)(i hbar grad)^L  = e^{-x log x}  quantum right
 * -------------------------------------------------------------------- */
double complex bada_op_left(double chi, double x);  /* <-  */
double          bada_op_mid(double x);              /* -<  */
double          bada_op_right(double x);            /* >-  */

/* ----------------------------------------------------------------------
 *  Arithmetic-Geometric Mean  (相加相乗平均).
 *  agm(a,b): a<-(a+b)/2, b<-sqrt(a*b) until they coincide.
 * -------------------------------------------------------------------- */
double bada_agm(double a, double b);

/* ----------------------------------------------------------------------
 *  Complex rotational body — special-relativity error correction.
 *  (Bada::ErrorCorrection: the spinning-top geometry of SR.)
 * -------------------------------------------------------------------- */
double bada_lorentz_gamma(double v_over_c);            /* gamma = 1/sqrt(1-b^2) */
double complex bada_rotate(double value, double theta);/* value * e^{i theta} */

typedef struct {
    double v;           /* tangential speed at radius (m/s)      */
    double beta;        /* v / c                                  */
    double gamma;       /* Lorentz factor                         */
    double f_observed;  /* frequency read in the rotating frame   */
    double f_proper;    /* gamma-corrected proper frequency       */
    double df;          /* f_proper - f_observed                  */
    double complex phasor; /* rotation phasor e^{i Omega t}       */
} BadaRelCorrection;

/* Correct a frequency measured on a body spinning at angular rate omega_rot
 * (rad/s) at radius R (m), sampled at time t (s). */
BadaRelCorrection bada_rel_correct(double f_observed,
                                   double omega_rot,
                                   double radius,
                                   double t);

/* ----------------------------------------------------------------------
 *  Secular polynomial / modal frequencies of an N-storey shear building.
 *
 *  Equal storey mass m, equal storey stiffness k:
 *      omega_j = 2 sqrt(k/m) sin( (2j-1) pi / (2(2N+1)) ),  j = 1..N
 *  These are the roots of the tridiagonal stiffness/mass secular polynomial.
 *  The Galois group of that polynomial permutes the roots; the elementary
 *  symmetric functions (sum, product) are the Galois-invariants.
 * -------------------------------------------------------------------- */
typedef struct {
    int    n_modes;                  /* = storeys                     */
    double f[BADA_MAX_MODES];        /* modal frequencies (Hz), sorted ascending */
    double sum_eig;                  /* sum of omega_j^2  (Galois invariant, = trace) */
    double prod_eig;                 /* product of omega_j^2 (Galois invariant, = det) */
    double xi_manifold;              /* manifold entropy invariant Xi over the modes  */
} BadaModalSpectrum;

BadaModalSpectrum bada_modal_spectrum(int storeys, double mass, double stiffness);

/* Index (0-based) of the mode whose frequency is closest to f_exc. */
int bada_nearest_mode(const BadaModalSpectrum *s, double f_exc);

/* ----------------------------------------------------------------------
 *  Resonance + fracture-mechanics durability diagnosis.
 * -------------------------------------------------------------------- */
typedef struct {
    char   name[64];

    /* structure / modal */
    int    storeys;          /* N                                      */
    double mass;             /* modal storey mass (kg)                 */
    double stiffness;        /* storey stiffness k (N/m)               */
    double damping;          /* damping ratio zeta (-)                 */
    double exc_freq;         /* excitation / resonance frequency (Hz)  */

    /* fracture mechanics (LEFM) */
    double crack_a;          /* existing crack/flaw size a (m)         */
    double Y_factor;         /* geometry factor Y (-)                  */
    double sigma_static;     /* static membrane stress (MPa)           */
    double Kic;              /* fracture toughness K_IC (MPa*sqrt(m))  */

    /* rotating body (special-relativity correction) */
    double rot_radius;       /* rotation radius R (m)                  */
    double rot_omega;        /* angular velocity Omega (rad/s)         */

    /* assembly geometry, for translating dk/k -> dimensional tolerance */
    double member_dim;       /* nominal governing member dimension h (mm) */
    double target_ratio;     /* safe detuning ratio r* = f_exc/f_mode  */
} BadaTarget;

typedef struct {
    /* resonance */
    int    mode_index;       /* 0-based dangerous mode                 */
    double f_mode;           /* its natural frequency (Hz)             */
    double ratio;            /* r = f_exc / f_mode                     */
    double daf;              /* dynamic amplification factor           */
    double sigma_dyn;        /* DAF * sigma_static (MPa)               */

    /* fracture / durability */
    double Ki;               /* stress intensity K_I (MPa*sqrt(m))     */
    double a_crit;           /* critical crack length (m)              */
    double safety_factor;    /* K_IC / K_I                             */
    int    safe;             /* 1 if SF >= 1 and r away from 1         */

    /* assembly-precision adjustment (AGM) */
    double k_target;         /* stiffness for the safe ratio (N/m)     */
    double k_arith;          /* arithmetic-mean candidate              */
    double k_geom;           /* geometric-mean candidate               */
    double k_agm;            /* AGM-blended target stiffness (N/m)     */
    double dk_rel;           /* (k_agm - k)/k                          */
    double dh_mm;            /* required member-dimension adjustment (mm) */

    /* relativistic correction of the excitation reading */
    BadaRelCorrection rel;

    /* framework gauges */
    BadaModalSpectrum spectrum;
    double xi_invariant;     /* certified manifold invariant Xi        */
} BadaDiagnosis;

/* Run the full diagnosis for a target. */
BadaDiagnosis bada_diagnose(const BadaTarget *t);

/* A sane default target (used by the dialog form and the demo). */
BadaTarget bada_default_target(void);

#endif /* BADA_RESONANCE_H */
