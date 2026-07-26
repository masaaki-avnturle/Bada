/* lib/omega_interp.c — command interpreter for the Bluebird EV OS.
 *
 * Commands:
 *   boot                              perceive->generate->drive loop
 *   codegen <infile> [outfile]        synthesize Bada driving source from the
 *                                     gamma-manifold entropy of <infile>
 *   entropy <infile>                  print the entropy equation invariants
 *   viz-env <infile> [out.ppm]        environment visualization
 *   viz-sound <knot> <A> <T> [w.wav]  sound visualization from Jones(thermal)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega_bluebird.h"

static unsigned char *slurp(const char *path, size_t *n)
{
    FILE *f = fopen(path, "rb"); if (!f) return NULL;
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    if (sz < 0) { fclose(f); return NULL; }
    unsigned char *b = malloc((size_t)sz + 1);
    if (!b) { fclose(f); return NULL; }
    size_t got = fread(b, 1, (size_t)sz, f); fclose(f);
    b[got] = 0; if (n) *n = got; return b;
}

static int cmd_entropy(const char *in)
{
    size_t n; unsigned char *b = slurp(in, &n);
    if (!b) { printf("entropy: cannot read '%s'\n", in); return 2; }
    ManifoldEntropy me = ob_manifold_entropy(b, n); free(b);
    printf("gamma-manifold entropy equation for '%s':\n", in);
    printf("  H  (Shannon)        = %.6f bits\n", me.entropy);
    printf("  M  (∬1/(x log x)^2) = %.6f\n", me.manifold_integral);
    printf("  N  (symbol extent)  = %.0f\n", me.extent);
    printf("  Xi (invariant)      = %.6f   [beta(H+1,M+1)/log(N+2)]\n", me.invariant);
    return 0;
}

static int cmd_codegen(const char *in, const char *out)
{
    size_t n; unsigned char *b = slurp(in, &n);
    if (!b) { printf("codegen: cannot read '%s'\n", in); return 2; }
    ManifoldEntropy me = ob_manifold_entropy(b, n); free(b);
    BluebirdState s = ob_default_bluebird();
    /* Fold in a Jones-thermal invariant if the default knot is present. */
    double bracket = 0, jt = 0;
    ob_thermal_jones("examples/thermal_body.knot", 1.2, s.body_temp_k, &bracket, &jt);
    int rc = ob_generate_bada_source(&me, jt, &s, out);
    if (out && rc == 0) printf("codegen: wrote Bada source -> %s (Xi=%.4f, Jones=%.4f)\n",
                               out, me.invariant, jt);
    return rc;
}

static int cmd_viz_env(const char *in, const char *ppm)
{
    size_t n; unsigned char *b = slurp(in, &n);
    if (!b) { printf("viz-env: cannot read '%s'\n", in); return 2; }
    ManifoldEntropy me = ob_manifold_entropy(b, n); free(b);
    BluebirdState s = ob_default_bluebird();
    int rc = ob_visualize_env(&me, &s, 320, 180, ppm);
    if (ppm && rc == 0) printf("viz-env: wrote %s\n", ppm);
    return rc;
}

static int cmd_viz_sound(const char *knot, double A, double T, const char *wav)
{
    double bracket = 0, jt = 0;
    if (ob_thermal_jones(knot, A, T, &bracket, &jt) != 0) {
        printf("viz-sound: cannot read knot '%s'\n", knot); return 2;
    }
    printf("Jones(thermal body): <D>@A=%.2f = %.4f, thermal invariant = %.4f\n", A, bracket, jt);
    int rc = ob_visualize_sound(bracket, jt, 2.0, wav);
    if (wav && rc == 0) printf("viz-sound: wrote %s\n", wav);
    return rc;
}

static int cmd_boot(void)
{
    BluebirdState s = ob_default_bluebird();
    printf("=== BadaOS · Bluebird EV autonomous-driving kernel ===\n");
    printf("body: Bluebird %.2fx%.2fx%.2f m · %.0f kW · %.0f kWh · Cd %.2f\n\n",
           s.length_m, s.width_m, s.height_m, s.motor_kw, s.battery_kwh, s.drag_coeff);
    for (int step = 1; step <= 8; step++) {
        double probs[DRV_COUNT];
        DriveAction a = ob_kernel_step(&s, probs);
        ob_kernel_apply(&s, a);
        printf("[t=%d] policy -> %s\n", step, OB_DRIVE_NAME[a]);
        ob_akashic_log("speed_mps", s.speed_mps);
        ob_akashic_log("lane_offset_m", s.lane_offset_m);
        ob_akashic_log("obstacle_dist_m", s.obstacle_dist_m);
        printf("\n");
    }
    printf("boot complete: lane centered, obstacle cleared.\n");
    return 0;
}

int omega_interp(const char *script)
{
    if (!script) return -1;
    char cmd[64]={0}, a1[512]={0}, a2[512]={0}, a3[512]={0}, a4[512]={0};
    int nargs = sscanf(script, "%63s %511s %511s %511s %511s", cmd, a1, a2, a3, a4);

    if (strcmp(cmd,"boot")==0) return cmd_boot();
    if (strcmp(cmd,"entropy")==0 && nargs>=2) return cmd_entropy(a1);
    if (strcmp(cmd,"codegen")==0 && nargs>=2) return cmd_codegen(a1, nargs>=3?a2:NULL);
    if (strcmp(cmd,"viz-env")==0 && nargs>=2) return cmd_viz_env(a1, nargs>=3?a2:NULL);
    if (strcmp(cmd,"viz-sound")==0 && nargs>=2)
        return cmd_viz_sound(a1, nargs>=3?atof(a2):1.2, nargs>=4?atof(a3):300.0,
                             nargs>=5?a4:NULL);

    printf("BadaOS · Bluebird EV commands:\n"
           "  boot\n"
           "  entropy   <infile>\n"
           "  codegen   <infile> [out.bada]\n"
           "  viz-env   <infile> [out.ppm]\n"
           "  viz-sound <knot> <A> <temp_k> [out.wav]\n");
    return -1;
}
