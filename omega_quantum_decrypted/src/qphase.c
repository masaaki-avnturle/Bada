/* qphase.c — Unknown-Prior Engine phase core over the Jones invariant. */
#include "qphase.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int oqd_phase_run(const oqd_knot_invariant *inv,
                  oqd_phase_report *rep,
                  uint8_t *spec, size_t spec_cap) {
    const oqd_lpoly *J = &inv->jones;
    int dim = (int)J->n;
    if (dim <= 0) return -1;

    double *z   = malloc(sizeof(double) * dim);   /* logits            */
    double *a   = malloc(sizeof(double) * dim);   /* base prior a_i    */
    double *th  = malloc(sizeof(double) * dim);   /* accumulated phase */
    if (!z || !a || !th) { free(z); free(a); free(th); return -1; }

    /* logits from Jones coefficients; phase from exponent position + writhe */
    for (int i = 0; i < dim; i++) {
        long long c = J->coeff[i];
        int e = J->lo + i;
        /* z_i: a bounded log-magnitude signal of the coefficient */
        z[i] = (c == 0) ? -1e30 : log1p((double)llabs(c)) * (c < 0 ? -1.0 : 1.0);
        /* theta_i = sum_m beta_m H_m phi_m : here beta*H folded into the
         * exponent lattice, phi from the writhe-normalised angle */
        double phi = (double)e * (M_PI / 6.0);
        double beta = (double)(inv->writhe + 1);
        th[i] = beta * phi + (double)c * 0.0; /* coeff enters via z, angle via e */
    }

    /* softmax over z with the max-subtraction trick; a zero coefficient maps
     * to z=-inf => a_i=0 exactly (Theorem 1's confident zero). */
    double zmax = -1e300;
    for (int i = 0; i < dim; i++) if (z[i] > zmax) zmax = z[i];
    double denom = 0.0;
    for (int i = 0; i < dim; i++) {
        double e = (z[i] <= -1e29) ? 0.0 : exp(z[i] - zmax);
        a[i] = e; denom += e;
    }
    if (denom <= 0.0) denom = 1.0;
    for (int i = 0; i < dim; i++) a[i] /= denom;

    /* psi_i = sqrt(a_i) exp(i theta_i);  q_i = |psi_i|^2 (should equal a_i) */
    double sumsq = 0.0, uerr = 0.0, entropy = 0.0;
    int zeros_ok = 1;
    for (int i = 0; i < dim; i++) {
        double re = sqrt(a[i]) * cos(th[i]);
        double im = sqrt(a[i]) * sin(th[i]);
        double q  = re*re + im*im;               /* = a_i * |e^{i th}|^2 = a_i */
        sumsq += q;
        double d = fabs(q - a[i]);
        if (d > uerr) uerr = d;
        if (a[i] == 0.0 && q != 0.0) zeros_ok = 0;
        if (a[i] > 0.0) entropy -= a[i] * log(a[i]);
    }

    if (rep) {
        rep->dim = dim;
        rep->unitarity_error = uerr;
        rep->sum_prob = sumsq;   /* sumsq already normalised since sum a_i = 1 */
        rep->zeros_preserved = zeros_ok;
        rep->entropy = entropy;
    }

    /* Phase spectrum -> key material: quantise psi_i into bytes. This is the
     * "Measure -> commit" step: the continuous phase state is collapsed into
     * a deterministic byte trace folded into the seed. */
    int written = 0;
    if (spec && spec_cap > 0) {
        for (int i = 0; i < dim && (size_t)written + 4 <= spec_cap; i++) {
            double re = sqrt(a[i]) * cos(th[i]);
            double im = sqrt(a[i]) * sin(th[i]);
            /* map [-1,1] amplitudes to 16-bit fixed point, big-endian pairs */
            int32_t ri = (int32_t)lround(re * 32767.0);
            int32_t ii = (int32_t)lround(im * 32767.0);
            spec[written++] = (uint8_t)((ri >> 8) & 0xff);
            spec[written++] = (uint8_t)(ri & 0xff);
            spec[written++] = (uint8_t)((ii >> 8) & 0xff);
            spec[written++] = (uint8_t)(ii & 0xff);
        }
    }

    free(z); free(a); free(th);
    return written;
}
