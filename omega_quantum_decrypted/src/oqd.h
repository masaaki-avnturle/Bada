/* oqd.h — the Omega-Quantum-Decrypted container format and key schedule.
 *
 * Container layout (all integers little-endian):
 *   0   4   magic  "OQD1"
 *   4   1   version (=1)
 *   5   1   flags  (bit0: passphrase mixed into key)
 *   6   2   reserved (0)
 *   8   16  salt   (random per file)
 *   24  16  nonce  (random per file, CTR nonce)
 *   40  8   fingerprint = first 8 bytes of SHA256(jones||phase seed)
 *   48  N   ciphertext = plaintext XOR SHA256-CTR keystream
 *   48+N 32 tag = HMAC-SHA256(mac_key, bytes[0 .. 48+N))
 *
 * The 32-byte master key is derived from the *topology* of the knot key file
 * (its Jones polynomial) plus the quantum phase spectrum, optionally salted
 * with a passphrase, then stretched with oqd_kdf.
 */
#ifndef OQD_OQD_H
#define OQD_OQD_H

#include <stddef.h>
#include <stdint.h>

#define OQD_MAGIC0 'O'
#define OQD_MAGIC1 'Q'
#define OQD_MAGIC2 'D'
#define OQD_MAGIC3 '1'
#define OQD_VERSION 1
#define OQD_HEADER_LEN 48
#define OQD_TAG_LEN 32
#define OQD_KDF_ITERS 120000u

enum {
    OQD_OK              =  0,
    OQD_E_KEYFILE      = -10,  /* knot key derivation failed          */
    OQD_E_IO           = -11,  /* file read/write error               */
    OQD_E_FORMAT       = -12,  /* bad magic / truncated container      */
    OQD_E_VERSION      = -13,  /* unsupported version                  */
    OQD_E_AUTH         = -14,  /* HMAC tag mismatch (wrong key/tamper) */
    OQD_E_FINGERPRINT  = -15,  /* knot key does not match this file    */
    OQD_E_NOMEM        = -16,  /* allocation failure                  */
    OQD_E_RANDOM       = -17   /* could not obtain randomness         */
};

typedef struct {
    /* derived key-schedule diagnostics, filled by encrypt/decrypt */
    int    n_crossings;
    int    writhe;
    double jones_span;
    double unitarity_error;
    int    zeros_preserved;
    double entropy;
    uint8_t fingerprint[8];
} oqd_keyinfo;

/* Derive the master key + fingerprint from a knot key file (and optional
 * passphrase, may be NULL). Fills keyinfo (may be NULL). */
int oqd_derive(const char *knot_path, const char *passphrase,
               const uint8_t salt[16],
               uint8_t master_out[32], uint8_t fingerprint_out[8],
               oqd_keyinfo *info);

/* Encrypt in_path -> out_path using the knot key file. */
int oqd_encrypt(const char *knot_path, const char *passphrase,
                const char *in_path, const char *out_path,
                oqd_keyinfo *info);

/* Decrypt (解読) in_path -> out_path using the knot key file. */
int oqd_decrypt(const char *knot_path, const char *passphrase,
                const char *in_path, const char *out_path,
                oqd_keyinfo *info);

/* Inspect a container without decrypting the payload. */
int oqd_inspect(const char *in_path, uint8_t salt[16], uint8_t nonce[16],
                uint8_t fingerprint[8], long *cipher_len);

const char *oqd_strerror(int code);

#endif /* OQD_OQD_H */
