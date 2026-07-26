/* lib/codegen.c — Bada SOURCE-CODE generator.
 *
 * This is the requested "ソースコード生成機能": a deterministic program
 * synthesizer that emits a *Bada-language* autonomous-driving policy. Every
 * literal in the generated code (thresholds, gains, speed caps, rule order) is
 * derived from the gamma-manifold entropy invariant Xi and from the Jones
 * polynomial of the thermal-energy body, so the same road/thermal context
 * always regenerates the same source, and different contexts synthesize
 * different — but valid — Bada programs.
 *
 * It is a generative grammar seeded by an invariant, not a trained model; see
 * README.md.
 */
#include <stdio.h>
#include <math.h>
#include "../include/omega_bluebird.h"

/* Fold a double into a stable unsigned seed. */
static unsigned seed_of(double x)
{
    double m = fabs(x) < 1e-12 ? 1e-12 : fabs(x);
    /* use mantissa bits via frexp for portability */
    int e; double frac = frexp(m, &e);
    unsigned s = (unsigned)(frac * 4294967296.0);
    s ^= (unsigned)(e * 2654435761u);
    return s ? s : 0x9e3779b9u;
}

/* xorshift so the grammar can draw several correlated-but-distinct values. */
static unsigned xs(unsigned *st){ unsigned x=*st; x^=x<<13; x^=x>>17; x^=x<<5; return *st=x; }
static double  frnd(unsigned *st, double lo, double hi){ return lo + (xs(st)/4294967295.0)*(hi-lo); }

int ob_generate_bada_source(const ManifoldEntropy *me, double jones_thermal,
                            const BluebirdState *s, const char *out_path)
{
    unsigned st = seed_of(me->invariant) ^ seed_of(jones_thermal);

    /* Derive policy parameters from the entropy equation + Jones invariant. */
    double v_cap   = 8.0  + frnd(&st, 0.0, 14.0) + 6.0 * me->invariant;   /* m/s */
    double brake_d = 6.0  + frnd(&st, 0.0, 10.0) + 20.0 * me->manifold_integral;
    double steer_k = 0.15 + 0.25 * (me->entropy / 8.0);                    /* gain */
    double caution = (jones_thermal < 0.0) ? 1.0 : 0.6;  /* Jones sign = risk post. */
    int    rule_order = (int)(seed_of(me->invariant) % 2);/* which rule is first */

    FILE *f = out_path ? fopen(out_path, "w") : stdout;
    if (!f) return -1;

    fprintf(f,
"# GENERATED Bada source — autonomous-driving policy for the Bluebird EV.\n"
"# Synthesized by omega_bluebird codegen from the gamma-manifold entropy\n"
"# equation and the Jones polynomial of the thermal-energy body.\n"
"#   Xi (entropy invariant) = %.6f\n"
"#   H  (Shannon entropy)   = %.6f\n"
"#   M  (manifold integral) = %.6f\n"
"#   Jones(thermal body)    = %.6f\n"
"#   body design            = Bluebird %.2fx%.2fx%.2f m, %.0f kW, %.0f kWh\n"
"\n"
"class BluebirdAutopilot <- TupleSpace {\n"
"  set v_cap    = %.3f      # top speed [m/s] from Xi\n"
"  set brake_d  = %.3f      # braking distance trigger [m] from M\n"
"  set steer_k  = %.3f      # steering gain from H\n"
"  set caution  = %.2f      # risk posture from sign of Jones(thermal)\n"
"\n"
"  operator <- (percept) {\n"
"    # left non-commutative act: fuse perception into the manifold\n"
"    return pi(chi, percept) -< brake_d;\n"
"  }\n"
"\n"
"  operator -< (scene) {\n",
        me->invariant, me->entropy, me->manifold_integral, jones_thermal,
        s->length_m, s->width_m, s->height_m, s->motor_kw, s->battery_kwh,
        v_cap, brake_d, steer_k, caution);

    /* Emit the two safety rules in an order chosen by the invariant. */
    const char *rule_brake =
"    if scene.obstacle_dist < brake_d * caution {\n"
"      return DRV_BRAKE;                 # obstacle inside braking envelope\n"
"    }\n";
    const char *rule_steer =
"    if abs(scene.lane_offset) > 0.20 {\n"
"      return scene.lane_offset > 0 ? DRV_STEER_LEFT : DRV_STEER_RIGHT;\n"
"    }\n";
    if (rule_order == 0) { fputs(rule_brake, f); fputs(rule_steer, f); }
    else                 { fputs(rule_steer, f); fputs(rule_brake, f); }

    fprintf(f,
"    if scene.speed < v_cap { return DRV_ACCEL; }\n"
"    return DRV_HOLD_LANE;\n"
"  }\n"
"\n"
"  operator >- (state) {\n"
"    # quantum right act: commit steering with gain steer_k\n"
"    return state.steer + steer_k * state.lane_offset * e(-state.speed);\n"
"  }\n"
"}\n"
"\n"
"# drive loop — regenerated whenever the entropy/thermal context shifts\n"
"set car = BluebirdAutopilot\n"
"loop every 20ms {\n"
"  set a = car -< perceive()\n"
"  Omega::push a as drive_action\n"
"  actuate(a)\n"
"}\n");

    if (out_path) fclose(f);
    return 0;
}
