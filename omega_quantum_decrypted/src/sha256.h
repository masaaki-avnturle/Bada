/* sha256.h — self-contained SHA-256, HMAC-SHA256, and SHA256-CTR keystream.
 *
 * Part of omega_quantum_decrypted (Bada / Yamaguchi framework).
 * Pure C, no external libraries. Implements FIPS 180-4 SHA-256 and
 * RFC 2104 HMAC so the whole application builds with nothing but gcc.
 */
#ifndef OQD_SHA256_H
#define OQD_SHA256_H

#include <stddef.h>
#include <stdint.h>

#define OQD_SHA256_DIGEST 32
#define OQD_SHA256_BLOCK  64

typedef struct {
    uint32_t state[8];
    uint64_t bitlen;
    uint8_t  buf[OQD_SHA256_BLOCK];
    size_t   buflen;
} oqd_sha256_ctx;

void oqd_sha256_init(oqd_sha256_ctx *c);
void oqd_sha256_update(oqd_sha256_ctx *c, const void *data, size_t len);
void oqd_sha256_final(oqd_sha256_ctx *c, uint8_t out[OQD_SHA256_DIGEST]);

/* One-shot convenience. */
void oqd_sha256(const void *data, size_t len, uint8_t out[OQD_SHA256_DIGEST]);

/* HMAC-SHA256 (RFC 2104). */
void oqd_hmac_sha256(const uint8_t *key, size_t keylen,
                     const uint8_t *msg, size_t msglen,
                     uint8_t out[OQD_SHA256_DIGEST]);

/* PBKDF-style stretch: derive `outlen` bytes from (seed,salt) with `iters`
 * rounds of HMAC-SHA256 (HKDF/PBKDF2-flavoured, deterministic). */
void oqd_kdf(const uint8_t *seed, size_t seedlen,
             const uint8_t *salt, size_t saltlen,
             uint32_t iters,
             uint8_t *out, size_t outlen);

/* SHA256-CTR keystream: XOR `len` bytes of in->out using a counter-mode
 * keystream keyed by `key` (32 bytes) and `nonce` (16 bytes). Symmetric:
 * the same call both encrypts and decrypts. */
void oqd_ctr_xor(const uint8_t key[32], const uint8_t nonce[16],
                 const uint8_t *in, uint8_t *out, size_t len);

/* Constant-time comparison; returns 1 if equal, 0 otherwise. */
int oqd_ct_equal(const uint8_t *a, const uint8_t *b, size_t len);

#endif /* OQD_SHA256_H */
