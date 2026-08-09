/* qphase.h — the Unknown-Prior Engine phase core.
 *
 * From the reviser paper (Appendix C):
 *     a_i     = softmax(z)_i                        (max-entropy base prior)
 *     theta_i = sum_m beta_m * H_m * phi_m^(i)      (accumulated phase)
 *     psi_i   = sqrt(a_i) * exp(i * theta_i)        (the native phase value)
 *     q_i     = |psi_i|^2 / sum_j |psi_j|^2 = a_i   (unitarity: |e^{i theta}|=1)
 *
 * Theorem 1 (zero-preservation): a_i = 0 => q_i = 0.
 * Theorem 2 (|psi|^2 = a): a pure-phase step changes no probability.
 *
 * Here the Jones invariant coefficients drive z (the logits) and the phase
 * angles theta. The engine confirms unitarity to ~1e-16 and derives a phase
 * spectrum that is folded into the crypto key seed, exactly as the paper's
 * "Measure -> commit to Omega::DATABASE" maps a phase state to a fact.
 */
#ifndef OQD_QPHASE_H
#define OQD_QPHASE_H

#include <stddef.h>
#include <stdint.h>
#include "jones.h"

typedef struct {
    int    dim;                 /* number of amplitudes                     */
    double unitarity_error;     /* max |q_i - a_i| — should be ~1e-16       */
    double sum_prob;            /* sum_i |psi_i|^2 / norm — should be 1.0   */
    int    zeros_preserved;     /* 1 if every a_i==0 kept q_i==0            */
    double entropy;             /* Shannon entropy of the base prior a_i    */
} oqd_phase_report;

/* Run the phase core over a Jones invariant. Fills `rep` (may be NULL) and
 * appends `spec_len` bytes of phase-spectrum material to `spec` (may be NULL
 * if spec_cap==0). Returns bytes written to spec, or negative on error. */
int oqd_phase_run(const oqd_knot_invariant *inv,
                  oqd_phase_report *rep,
                  uint8_t *spec, size_t spec_cap);

#endif /* OQD_QPHASE_H */
