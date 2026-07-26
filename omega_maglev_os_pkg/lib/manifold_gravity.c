/* lib/manifold_gravity.c — general-relativity manifold integral layer.
 *
 * CONCEPTUAL / SIMULATION (house style of this repo). In real general
 * relativity a freely moving body follows a geodesic and feels no "gravity
 * resistance" to cancel; you cannot switch gravity off with a field. What
 * this file computes is the Yamaguchi "global partial-integral manifold"
 * element  d mu = 1 / (x log x)^2  integrated along a curvature coordinate,
 * normalised into a dimensionless cancellation ratio in [0,1). The OS uses
 * that ratio only to trim how much of the vehicle weight the EM levitation
 * field must still carry — i.e. it is a control-gain knob, not new physics.
 */
#include <math.h>
#include "../include/omega_maglev.h"

double om_manifold_element(double x)
{
    /* d mu(x) = 1 / (x log x)^2 , with a safe value at the Napier step x->1. */
    if (x <= 1.0) return 1.0;
    double xl = x * log(x);
    if (fabs(xl) < 1e-9) return 1.0;
    return 1.0 / (xl * xl);
}

double om_manifold_integral(int n_steps)
{
    /* ∬ 1/(x log x)^2 dx_m  approximated as a Riemann sum over rank
       coordinates x = 2 .. n+1 (log x > 0 throughout). Converges quickly. */
    if (n_steps < 1) n_steps = 1;
    double sum = 0.0;
    for (int i = 0; i < n_steps; i++) {
        double x = i + 2.0;
        sum += om_manifold_element(x);
    }
    return sum;
}

double om_residual_gravity(const MaglevState *s, double cancel_ratio)
{
    /* Net downward acceleration after (a) EM field balances weight and
       (b) the manifold model absorbs a `cancel_ratio` share of residual.
       With a correctly trimmed field this returns ~0. `s` is accepted so
       future models can scale residual by mass/gap; unused for now.       */
    (void)s;
    if (cancel_ratio < 0.0) cancel_ratio = 0.0;
    if (cancel_ratio > 1.0) cancel_ratio = 1.0;
    /* Start from 1 g of "resistance", remove the cancel share. */
    return OM_G0 * (1.0 - cancel_ratio);
}
