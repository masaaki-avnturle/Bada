/* jones.h — Kauffman bracket -> Jones polynomial, and key-seed derivation.
 *
 * The knot key file lists crossings, one per line:
 *     id  a b c d  sign
 * where a,b,c,d are the four edge labels around the crossing (counter-
 * clockwise from the incoming under-strand) and sign is +1 / -1.
 * Lines beginning with '#' are comments.
 *
 * The Kauffman bracket <D> is computed as a state sum and stored as a
 * Laurent polynomial in A. Writhe normalisation gives the Jones-polynomial
 * invariant f(A) = (-A)^(-3w) <D>, which is invariant under Reidemeister
 * moves II and III (and, after normalisation, I) — so the derived key
 * depends on the *knot type*, not on how the diagram happens to be drawn.
 */
#ifndef OQD_JONES_H
#define OQD_JONES_H

#include <stddef.h>
#include <stdint.h>

#define OQD_MAX_CROSSINGS 24   /* 2^24 states upper bound for the state sum */

typedef struct {
    int lo;              /* lowest A exponent stored at coeff[0] */
    int hi;              /* highest A exponent */
    long long *coeff;    /* coeff[i] is the coefficient of A^(lo+i) */
    size_t n;            /* number of coefficients (hi-lo+1) */
} oqd_lpoly;

typedef struct {
    int n_crossings;
    int writhe;
    int n_states;        /* 2^n_crossings actually evaluated */
    oqd_lpoly bracket;   /* Kauffman bracket <D>(A) */
    oqd_lpoly jones;     /* writhe-normalised invariant (-A)^-3w <D> */
    double span;         /* jones.hi - jones.lo (Laurent span, a knot signal) */
} oqd_knot_invariant;

/* Parse a knot key file and compute the invariant.
 * Returns 0 on success, negative on error (see oqd_jones_strerror). */
int oqd_jones_from_file(const char *path, oqd_knot_invariant *out);

/* Free polynomials held by an invariant. */
void oqd_jones_free(oqd_knot_invariant *inv);

/* Serialise the invariant (exponents + coefficients + writhe + span) into a
 * canonical little-endian byte seed suitable for the KDF. Writes up to
 * `cap` bytes and returns the number of bytes written (>0), or negative. */
int oqd_jones_seed(const oqd_knot_invariant *inv, uint8_t *out, size_t cap);

const char *oqd_jones_strerror(int code);

#endif /* OQD_JONES_H */
