/* lib/badaos.c — the generative-AI operating-system kernel.
 *
 * The "OS" is a small generative controller. Each step it scores the control
 * actions from the current vehicle state, turns the scores into a policy with
 * the repo's pi-softmax (README: exp(logit * hbar_eff * pi)), and emits the
 * highest-probability action. It is a simulated closed-loop controller — the
 * generative-AI analogue of a train's autopilot — not a learned large model.
 */
#include <math.h>
#include <stdio.h>
#include "../include/omega_maglev.h"

const char *OM_ACTION_NAME[ACT_COUNT] = {
    "RAISE_FIELD", "LOWER_FIELD", "EVACUATE_TUBE", "TRIM_MANIFOLD", "HOLD"
};

void om_pi_softmax(const double *logits, int n, double hbar_eff, double *probs)
{
    /* Numerically stable softmax of  exp(logit * hbar_eff * pi). */
    double maxv = logits[0] * hbar_eff * OM_PI;
    for (int i = 1; i < n; i++) {
        double v = logits[i] * hbar_eff * OM_PI;
        if (v > maxv) maxv = v;
    }
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        probs[i] = exp(logits[i] * hbar_eff * OM_PI - maxv);
        sum += probs[i];
    }
    if (sum <= 0.0) sum = 1.0;
    for (int i = 0; i < n; i++) probs[i] /= sum;
}

MaglevAction om_kernel_step(const MaglevState *s, double cancel_ratio,
                            double probs_out[ACT_COUNT])
{
    /* Build logits from the physics error signals. */
    double need_ni = om_levitation_amp_turns(s);
    double have_B  = om_flux_density(need_ni, s->gap_m);
    double lift    = om_levitation_force(have_B, s->coil_area);
    double weight  = s->mass_kg * OM_G0;
    double lift_err = (lift - weight) / weight;         /* >0 too much lift */
    double drag     = om_aero_drag(s);
    double resid_g  = om_residual_gravity(s, cancel_ratio);

    /* Normalise every error to a comparable [0,1] scale so the argmax
       policy rotates across subsystems instead of fixating on one. */
    double logits[ACT_COUNT];
    logits[ACT_RAISE_FIELD]  = (lift_err < -0.02) ? 0.5 + (-lift_err)       : 0.0;
    logits[ACT_LOWER_FIELD]  = (lift_err >  0.02) ? 0.5 +   lift_err        : 0.0;
    logits[ACT_EVACUATE_TUBE]= (drag > 5.0e3)     ? 0.5 + drag / 1.0e5      : 0.0;
    logits[ACT_TRIM_MANIFOLD]= (resid_g > 0.05)   ? 0.5 + resid_g / OM_G0   : 0.0;
    logits[ACT_HOLD]         = 0.3;                     /* baseline bias    */

    double probs[ACT_COUNT];
    om_pi_softmax(logits, ACT_COUNT, /*hbar_eff=*/0.35, probs);
    if (probs_out) for (int i = 0; i < ACT_COUNT; i++) probs_out[i] = probs[i];

    int best = 0;
    for (int i = 1; i < ACT_COUNT; i++) if (probs[i] > probs[best]) best = i;
    return (MaglevAction)best;
}

void om_kernel_apply(MaglevState *s, MaglevAction a, double *cancel_ratio)
{
    switch (a) {
        case ACT_RAISE_FIELD:   s->gap_m *= 0.98; break;   /* tighter gap -> more lift */
        case ACT_LOWER_FIELD:   s->gap_m *= 1.02; break;
        case ACT_EVACUATE_TUBE: s->air_density *= 0.5; break;
        case ACT_TRIM_MANIFOLD: if (cancel_ratio) {
                                    *cancel_ratio += 0.1;
                                    if (*cancel_ratio > 0.999) *cancel_ratio = 0.999;
                                } break;
        case ACT_HOLD:
        default: break;
    }
}

void om_akashic_log(const char *key, double value)
{
    /* Omega::DATABASE[tuplespace].push(...) — telemetry sink. */
    printf("  Omega::push  %-22s = %.6g\n", key, value);
}
