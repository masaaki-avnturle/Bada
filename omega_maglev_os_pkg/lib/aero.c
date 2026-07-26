/* lib/aero.c — aerodynamic drag and the "no air resistance" running mode.
 *
 * Drag is the textbook  F = 1/2 rho Cd A v^2 . The only physically real way
 * to run "without air resistance" is to remove the air: an evacuated tube
 * (as in vacuum-tube / Hyperloop concepts) drops rho toward zero, and the
 * drag falls with it. `om_drag_reduction` reports how much of the sea-level
 * drag a given ambient density has eliminated.
 */
#include "../include/omega_maglev.h"

double om_aero_drag(const MaglevState *s)
{
    double rho = s->air_density;
    if (rho < 0.0) rho = 0.0;
    return 0.5 * rho * s->drag_coeff * s->frontal_area * s->speed_mps * s->speed_mps;
}

double om_drag_reduction(double rho_ambient)
{
    if (rho_ambient <= 0.0) return 1.0;               /* perfect vacuum  */
    double r = 1.0 - (rho_ambient / OM_RHO_AIR);
    if (r < 0.0) r = 0.0;
    if (r > 1.0) r = 1.0;
    return r;                                          /* fraction removed */
}
