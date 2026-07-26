/* lib/badaev_os.c — autonomous-driving OS kernel + Bluebird body design.
 *
 * A pi-softmax generative controller (README: pi_softmax) that perceives the
 * road state and emits a driving action each tick. It is a simulated autopilot
 * — the generative-AI analogue of a driving policy — not a trained large model.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "../include/omega_bluebird.h"

const char *OB_DRIVE_NAME[DRV_COUNT] = {
    "HOLD_LANE", "STEER_LEFT", "STEER_RIGHT", "BRAKE", "ACCEL"
};

BluebirdState ob_default_bluebird(void)
{
    BluebirdState s;
    /* Bluebird-styled 3-box sedan, EV drivetrain */
    s.length_m = 4.60; s.width_m = 1.69; s.height_m = 1.40;
    s.drag_coeff = 0.29; s.frontal_area = 2.16;
    s.battery_kwh = 62.0; s.motor_kw = 110.0;
    s.speed_mps = 14.0;                 /* ~50 km/h */
    s.steer_rad = 0.0; s.lane_offset_m = 0.35;
    s.obstacle_ahead = 1; s.obstacle_dist_m = 22.0;
    s.body_temp_k = 305.0;
    return s;
}

void ob_pi_softmax(const double *logits, int n, double hbar_eff, double *probs)
{
    double maxv = logits[0] * hbar_eff * OB_PI;
    for (int i = 1; i < n; i++){ double v=logits[i]*hbar_eff*OB_PI; if(v>maxv) maxv=v; }
    double sum = 0.0;
    for (int i = 0; i < n; i++){ probs[i]=exp(logits[i]*hbar_eff*OB_PI-maxv); sum+=probs[i]; }
    if (sum <= 0.0) sum = 1.0;
    for (int i = 0; i < n; i++) probs[i] /= sum;
}

DriveAction ob_kernel_step(const BluebirdState *s, double probs_out[DRV_COUNT])
{
    double brake_env = 8.0 + 0.6 * s->speed_mps;      /* braking distance ~v */
    double logits[DRV_COUNT];
    logits[DRV_HOLD_LANE]  = 0.4;
    logits[DRV_STEER_LEFT] = (s->lane_offset_m >  0.20) ? 0.5 + s->lane_offset_m : 0.0;
    logits[DRV_STEER_RIGHT]= (s->lane_offset_m < -0.20) ? 0.5 - s->lane_offset_m : 0.0;
    logits[DRV_BRAKE]      = (s->obstacle_ahead && s->obstacle_dist_m < brake_env)
                              ? 1.0 + (brake_env - s->obstacle_dist_m) / brake_env : 0.0;
    logits[DRV_ACCEL]      = (!s->obstacle_ahead && s->speed_mps < 27.0) ? 0.6 : 0.0;

    double probs[DRV_COUNT];
    ob_pi_softmax(logits, DRV_COUNT, 0.4, probs);
    if (probs_out) for (int i=0;i<DRV_COUNT;i++) probs_out[i]=probs[i];
    int best = 0; for (int i=1;i<DRV_COUNT;i++) if(probs[i]>probs[best]) best=i;
    return (DriveAction)best;
}

void ob_kernel_apply(BluebirdState *s, DriveAction a)
{
    switch (a) {
        case DRV_STEER_LEFT:  s->lane_offset_m -= 0.15; s->steer_rad -= 0.03; break;
        case DRV_STEER_RIGHT: s->lane_offset_m += 0.15; s->steer_rad += 0.03; break;
        case DRV_BRAKE:       s->speed_mps *= 0.80; s->obstacle_dist_m -= s->speed_mps*0.2; break;
        case DRV_ACCEL:       s->speed_mps += 1.0; break;
        case DRV_HOLD_LANE:   default: break;
    }
    if (s->obstacle_dist_m < 0) { s->obstacle_ahead = 0; s->obstacle_dist_m = 60.0; }
}

void ob_akashic_log(const char *key, double value)
{
    printf("  Omega::push  %-20s = %.6g\n", key, value);
}
