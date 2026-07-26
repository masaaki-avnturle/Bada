/* lib/em_field.c — electromagnetic levitation and the coil-power budget.
 *
 * This file is ordinary electromagnetism: an EMS (electromagnetic-suspension)
 * pole develops an attractive force  F = B^2 A / (2 mu0)  across the air gap,
 * with  B = mu0 (N I) / g  for N*I amp-turns and gap g. Balancing that force
 * against the car weight is what makes a maglev car float. The rest of the
 * package calls the balancing field the "anti-gravity field", but physically
 * it is just a servo-controlled magnetic force — see README.
 */
#include <math.h>
#include "../include/omega_maglev.h"

double om_flux_density(double amp_turns, double gap_m)
{
    if (gap_m < 1e-4) gap_m = 1e-4;          /* clamp: never zero gap  */
    return OM_MU0 * amp_turns / gap_m;        /* B = mu0 N I / g  [T]   */
}

double om_levitation_force(double flux_T, double coil_area)
{
    /* F = B^2 A / (2 mu0)  — Maxwell stress on the pole face. */
    return (flux_T * flux_T * coil_area) / (2.0 * OM_MU0);
}

double om_levitation_amp_turns(const MaglevState *s)
{
    /* Solve  F(NI) = m g  for the amp-turns, consistent with
       B = mu0 (NI)/g  and  F = B^2 A / (2 mu0) = mu0 (NI)^2 A / (2 g^2).
       => NI = g * sqrt( 2 m g0 / (mu0 A) ).                            */
    double weight = s->mass_kg * OM_G0;
    double denom  = OM_MU0 * s->coil_area;
    if (denom < 1e-12) denom = 1e-12;
    return s->gap_m * sqrt(2.0 * weight / denom);
}

double om_coil_ohmic_power(double amp_turns, double resistance_ohm)
{
    /* Treat amp-turns with a nominal 400-turn winding, P = I^2 R.
       A superconductor would give R -> 0 (P -> 0); the OS reports this
       so it can pick a normal-conductor "superconductor alternative"
       operating point that keeps P within the on-board power budget.   */
    double turns = 400.0;
    double current = amp_turns / turns;
    return current * current * resistance_ohm;
}
