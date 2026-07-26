/* lib/omega_interp.c — tiny command interpreter for the maglev OS.
 *
 * Commands:
 *   boot                                  run the full OS boot + control loop
 *   levitate <mass_kg> <gap_m>            report the levitation field/force
 *   drag <speed> <rho>                    report aerodynamic drag & reduction
 *   gravity <steps> <cancel>              manifold integral & residual gravity
 *   thermal <diagram> <A> <temp_k>        Jones polynomial of the thermal body
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega_maglev.h"

static MaglevState default_state(void)
{
    MaglevState s;
    s.mass_kg      = 45000.0;     /* one loaded L0-class car (~45 t)        */
    s.speed_mps    = 138.9;       /* 500 km/h                               */
    s.gap_m        = 0.010;       /* 10 mm levitation gap                   */
    s.frontal_area = 12.0;        /* m^2                                    */
    s.drag_coeff   = 0.30;
    s.coil_area    = 0.25;        /* effective pole area  [m^2]             */
    s.air_density  = OM_RHO_AIR;
    s.body_temp_k  = 300.0;
    return s;
}

static int cmd_levitate(double mass, double gap)
{
    MaglevState s = default_state();
    if (mass > 0) s.mass_kg = mass;
    if (gap  > 0) s.gap_m   = gap;
    double ni = om_levitation_amp_turns(&s);
    double B  = om_flux_density(ni, s.gap_m);
    double F  = om_levitation_force(B, s.coil_area);
    double P  = om_coil_ohmic_power(ni, /*R=*/0.02);
    printf("levitation field (\"anti-gravity field\", EM balancing):\n");
    printf("  weight            = %.1f N\n", s.mass_kg * OM_G0);
    printf("  amp-turns  N*I    = %.1f A-turns\n", ni);
    printf("  flux       B      = %.4f T\n", B);
    printf("  lift force F      = %.1f N   (matches weight => float)\n", F);
    printf("  coil ohmic power  = %.1f W   (superconductor alt.: normal coil)\n", P);
    return 0;
}

static int cmd_drag(double speed, double rho)
{
    MaglevState s = default_state();
    if (speed > 0) s.speed_mps = speed;
    if (rho >= 0)  s.air_density = rho;
    double d = om_aero_drag(&s);
    double red = om_drag_reduction(s.air_density);
    printf("aerodynamics (\"no air resistance\" via evacuated tube):\n");
    printf("  speed             = %.1f m/s (%.0f km/h)\n", s.speed_mps, s.speed_mps * 3.6);
    printf("  ambient density   = %.4f kg/m^3\n", s.air_density);
    printf("  drag force        = %.1f N\n", d);
    printf("  drag removed      = %.1f %% vs sea level\n", red * 100.0);
    return 0;
}

static int cmd_gravity(int steps, double cancel)
{
    MaglevState s = default_state();
    double integ = om_manifold_integral(steps);
    double resid = om_residual_gravity(&s, cancel);
    printf("general-relativity manifold layer (conceptual/simulation):\n");
    printf("  manifold integral = %.6f   (∬ 1/(x log x)^2 dx_m, %d steps)\n", integ, steps);
    printf("  cancel ratio      = %.3f\n", cancel);
    printf("  residual gravity  = %.4f m/s^2\n", resid);
    return 0;
}

static int cmd_thermal(const char *diagram, double A, double temp)
{
    double bracket = 0, jt = 0;
    if (om_thermal_jones(diagram, A, temp, &bracket, &jt) != 0) {
        printf("thermal: cannot read diagram '%s'\n", diagram);
        return 2;
    }
    printf("Jones polynomial of the thermal-energy body:\n");
    printf("  Kauffman <D> @A=%.2f = %.6f\n", A, bracket);
    printf("  body temperature     = %.1f K\n", temp);
    printf("  gamma-global-partial thermal invariant = %.6f\n", jt);
    return 0;
}

static int cmd_boot(void)
{
    MaglevState s = default_state();
    double cancel = 0.0;
    printf("=== BadaOS · Linear Shinkansen generative-AI kernel ===\n");
    printf("boot: loading Omega::DATABASE (Akashic TupleSpace)...\n\n");

    for (int step = 1; step <= 8; step++) {
        double probs[ACT_COUNT];
        MaglevAction a = om_kernel_step(&s, cancel, probs);
        om_kernel_apply(&s, a, &cancel);

        double ni   = om_levitation_amp_turns(&s);
        double B    = om_flux_density(ni, s.gap_m);
        double lift = om_levitation_force(B, s.coil_area);
        double drag = om_aero_drag(&s);
        double resid= om_residual_gravity(&s, cancel);

        printf("[step %d] policy -> %s\n", step, OM_ACTION_NAME[a]);
        om_akashic_log("levitation_force_N", lift);
        om_akashic_log("air_drag_N", drag);
        om_akashic_log("gap_m", s.gap_m);
        om_akashic_log("cancel_ratio", cancel);
        om_akashic_log("residual_gravity", resid);
        printf("\n");
    }
    printf("boot complete: field balanced, tube evacuated, manifold trimmed.\n");
    return 0;
}

int omega_interp(const char *script)
{
    if (!script) return -1;
    char cmd[64] = {0}, a1[512] = {0}, a2[512] = {0}, a3[512] = {0};
    int nargs = sscanf(script, "%63s %511s %511s %511s", cmd, a1, a2, a3);

    if (strcmp(cmd, "boot") == 0)      return cmd_boot();
    if (strcmp(cmd, "levitate") == 0)  return cmd_levitate(nargs > 1 ? atof(a1) : 0,
                                                           nargs > 2 ? atof(a2) : 0);
    if (strcmp(cmd, "drag") == 0)      return cmd_drag(nargs > 1 ? atof(a1) : 0,
                                                       nargs > 2 ? atof(a2) : -1);
    if (strcmp(cmd, "gravity") == 0)   return cmd_gravity(nargs > 1 ? atoi(a1) : 64,
                                                          nargs > 2 ? atof(a2) : 0.0);
    if (strcmp(cmd, "thermal") == 0 && nargs >= 2)
        return cmd_thermal(a1, nargs > 2 ? atof(a2) : 1.0, nargs > 3 ? atof(a3) : 300.0);

    printf("BadaOS commands:\n"
           "  boot\n"
           "  levitate <mass_kg> <gap_m>\n"
           "  drag <speed_mps> <rho>\n"
           "  gravity <steps> <cancel_ratio>\n"
           "  thermal <diagram> <A> <temp_k>\n");
    return -1;
}
