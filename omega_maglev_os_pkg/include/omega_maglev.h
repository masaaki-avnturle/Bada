/* include/omega_maglev.h
 *
 * omega_maglev — Linear Shinkansen operating system as a generative-AI kernel,
 * expressed in the conceptual "Bada" quantum-computer language and lowered to C.
 *
 * SCOPE / HONESTY NOTE (read README.md for the full statement):
 *   The electromagnetic levitation, aerodynamic drag and thermal-flow parts are
 *   ordinary, physically grounded models. The "anti-gravity field" and
 *   "gravity-resistance cancellation via a general-relativity manifold integral"
 *   are a SIMULATION / conceptual layer in the house style of this repository
 *   (cf. omega_jones_crypto_pkg, bio_medicine). Maglev floats because an EM
 *   field balances weight — it does not literally switch off gravity, and this
 *   package does not claim to. The Jones-polynomial "thermal energy body" and
 *   the beta/zeta gauge follow the Yamaguchi TupleSpace motif used throughout.
 */
#ifndef OMEGA_MAGLEV_H
#define OMEGA_MAGLEV_H

#include <stddef.h>

/* Physical constants (SI). */
#define OM_MU0      1.25663706212e-6   /* vacuum permeability  [H/m]   */
#define OM_G0       9.80665            /* standard gravity     [m/s^2] */
#define OM_RHO_AIR  1.225              /* sea-level air density [kg/m^3]*/
#define OM_PI       3.14159265358979323846

/* ------------------------------------------------------------------ */
/* Vehicle / guideway state                                            */
/* ------------------------------------------------------------------ */
typedef struct {
    double mass_kg;        /* loaded car mass                          */
    double speed_mps;      /* forward speed                            */
    double gap_m;          /* levitation air-gap (rail<->body)         */
    double frontal_area;   /* projected frontal area  [m^2]           */
    double drag_coeff;     /* aerodynamic Cd                           */
    double coil_area;      /* effective levitation pole area [m^2]     */
    double air_density;    /* ambient density (tube can be near-vacuum)*/
    double body_temp_k;    /* car-body / coil temperature [K]          */
} MaglevState;

/* ------------------------------------------------------------------ */
/* 1. Electromagnetic levitation  (real physics)                       */
/*    Reluctance/attraction force of an EMS pole:  F = B^2 * A / (2 mu0)*/
/* ------------------------------------------------------------------ */

/* Flux density B [T] produced by N*I amp-turns across a gap g. */
double om_flux_density(double amp_turns, double gap_m);

/* Vertical levitation force [N] for a given flux and pole area. */
double om_levitation_force(double flux_T, double coil_area);

/* Amp-turns the controller must command so the levitation force equals
   the car weight (the field that makes the car "float"). This is the
   honest core of what the marketing layer calls the "anti-gravity field". */
double om_levitation_amp_turns(const MaglevState *s);

/* ------------------------------------------------------------------ */
/* 2. Superconductor alternative — room-temperature coil budget        */
/*    Ohmic power for a normal (non-superconducting) coil; the OS uses  */
/*    it to decide whether the EM field is affordable without SC.       */
/* ------------------------------------------------------------------ */
double om_coil_ohmic_power(double amp_turns, double resistance_ohm);

/* ------------------------------------------------------------------ */
/* 3. Aerodynamics — "no air resistance" (evacuated tube / field sheath)*/
/*    Drag  F = 1/2 rho Cd A v^2 . Lowering rho (vacuum tube) is the     */
/*    physical route to the "no air resistance" running mode.           */
/* ------------------------------------------------------------------ */
double om_aero_drag(const MaglevState *s);

/* Fraction of atmospheric drag removed by running in density `rho`. */
double om_drag_reduction(double rho_ambient);

/* ------------------------------------------------------------------ */
/* 4. General-relativity manifold integral  (conceptual / simulation)  */
/*    Global partial-integral manifold element  d mu = 1/(x log x)^2 .   */
/*    We integrate it along the rank/curvature coordinate to obtain a    */
/*    dimensionless "gravity-resistance cancellation" ratio in [0,1).     */
/* ------------------------------------------------------------------ */
double om_manifold_element(double x);
double om_manifold_integral(int n_steps);

/* Net vertical acceleration left after the EM field balances weight and
   the manifold model absorbs residual "gravity resistance". Returns
   ~0 when the OS has trimmed the field correctly. */
double om_residual_gravity(const MaglevState *s, double cancel_ratio);

/* ------------------------------------------------------------------ */
/* 5. Jones polynomial of the thermal-energy body                      */
/*    Kauffman-bracket evaluation over a knot diagram whose crossings    */
/*    encode the thermal-flow topology, weighted by a gamma-function     */
/*    global partial integration factor.                                 */
/* ------------------------------------------------------------------ */
double om_gamma(double x);                 /* Lanczos Gamma(x)          */
double om_gamma_global_partial(double a, double b); /* beta-style weight */

/* Evaluate the Kauffman bracket <D> of the diagram at A, then fold in
   the gamma-global-partial thermal weight for body temperature T. */
int    om_thermal_jones(const char *diagram_path, double A, double body_temp_k,
                        double *bracket_out, double *jones_thermal_out);

/* ------------------------------------------------------------------ */
/* 6. Generative-AI OS kernel                                          */
/*    pi-softmax policy over control actions (README: pi_softmax).      */
/* ------------------------------------------------------------------ */
typedef enum {
    ACT_RAISE_FIELD = 0,   /* increase levitation amp-turns  */
    ACT_LOWER_FIELD,       /* decrease levitation amp-turns  */
    ACT_EVACUATE_TUBE,     /* drop ambient density           */
    ACT_TRIM_MANIFOLD,     /* raise gravity-cancel ratio     */
    ACT_HOLD,              /* steady state                   */
    ACT_COUNT
} MaglevAction;

extern const char *OM_ACTION_NAME[ACT_COUNT];

/* pi-softmax over logits with an effective-hbar temperature. */
void   om_pi_softmax(const double *logits, int n, double hbar_eff, double *probs);

/* One generative control step: score the actions from the current state,
   pick the argmax policy action, and return it (probs optional). */
MaglevAction om_kernel_step(const MaglevState *s, double cancel_ratio,
                            double probs_out[ACT_COUNT]);

/* Apply an action to the state (in place). */
void om_kernel_apply(MaglevState *s, MaglevAction a, double *cancel_ratio);

/* ------------------------------------------------------------------ */
/* Akashic TupleSpace telemetry log (Omega::DATABASE motif).           */
/* ------------------------------------------------------------------ */
void om_akashic_log(const char *key, double value);

#endif /* OMEGA_MAGLEV_H */
