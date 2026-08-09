/* oqd.c — Omega-Quantum-Decrypted container + key schedule. */
#include "oqd.h"
#include "sha256.h"
#include "jones.h"
#include "qphase.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char *oqd_strerror(int code) {
    switch (code) {
        case OQD_OK:             return "ok";
        case OQD_E_KEYFILE:      return "knot key derivation failed";
        case OQD_E_IO:           return "file read/write error";
        case OQD_E_FORMAT:       return "not an OQD container (bad magic or truncated)";
        case OQD_E_VERSION:      return "unsupported container version";
        case OQD_E_AUTH:         return "authentication failed: wrong knot key, wrong passphrase, or tampered file";
        case OQD_E_FINGERPRINT:  return "knot key does not match this file";
        case OQD_E_NOMEM:        return "out of memory";
        case OQD_E_RANDOM:       return "could not obtain secure randomness";
        default:                 return "unknown error";
    }
}

static int read_all(const char *path, uint8_t **buf, long *len) {
    FILE *f = fopen(path, "rb");
    if (!f) return OQD_E_IO;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return OQD_E_IO; }
    long sz = ftell(f);
    if (sz < 0) { fclose(f); return OQD_E_IO; }
    if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return OQD_E_IO; }
    uint8_t *b = malloc(sz > 0 ? (size_t)sz : 1);
    if (!b) { fclose(f); return OQD_E_NOMEM; }
    if (sz > 0 && fread(b, 1, (size_t)sz, f) != (size_t)sz) { free(b); fclose(f); return OQD_E_IO; }
    fclose(f);
    *buf = b; *len = sz;
    return OQD_OK;
}

static int write_all(const char *path, const uint8_t *buf, size_t len) {
    FILE *f = fopen(path, "wb");
    if (!f) return OQD_E_IO;
    if (len > 0 && fwrite(buf, 1, len, f) != len) { fclose(f); return OQD_E_IO; }
    fclose(f);
    return OQD_OK;
}

static int get_random(uint8_t *out, size_t len) {
    FILE *f = fopen("/dev/urandom", "rb");
    if (!f) return OQD_E_RANDOM;
    size_t r = fread(out, 1, len, f);
    fclose(f);
    return (r == len) ? OQD_OK : OQD_E_RANDOM;
}

int oqd_derive(const char *knot_path, const char *passphrase,
               const uint8_t salt[16],
               uint8_t master_out[32], uint8_t fingerprint_out[8],
               oqd_keyinfo *info) {
    oqd_knot_invariant inv;
    int rc = oqd_jones_from_file(knot_path, &inv);
    if (rc != 0) return OQD_E_KEYFILE;

    /* seed = jones_seed || phase_spectrum [|| passphrase] */
    uint8_t seed[8192];
    int jlen = oqd_jones_seed(&inv, seed, sizeof seed);
    if (jlen < 0) { oqd_jones_free(&inv); return OQD_E_KEYFILE; }

    oqd_phase_report prep;
    int plen = oqd_phase_run(&inv, &prep,
                             seed + jlen,
                             (jlen < (int)sizeof seed) ? sizeof seed - jlen : 0);
    if (plen < 0) plen = 0;
    size_t seedlen = (size_t)jlen + (size_t)plen;

    if (passphrase && passphrase[0]) {
        size_t pl = strlen(passphrase);
        if (seedlen + pl < sizeof seed) {
            memcpy(seed + seedlen, passphrase, pl);
            seedlen += pl;
        }
    }

    /* fingerprint = first 8 bytes of SHA256(seed) — lets us reject a wrong
     * knot key fast, before touching the ciphertext */
    uint8_t fp[32];
    oqd_sha256(seed, seedlen, fp);
    if (fingerprint_out) memcpy(fingerprint_out, fp, 8);

    /* master = KDF(seed, salt, iters) */
    oqd_kdf(seed, seedlen, salt, 16, OQD_KDF_ITERS, master_out, 32);

    if (info) {
        info->n_crossings = inv.n_crossings;
        info->writhe = inv.writhe;
        info->jones_span = inv.span;
        info->unitarity_error = prep.unitarity_error;
        info->zeros_preserved = prep.zeros_preserved;
        info->entropy = prep.entropy;
        memcpy(info->fingerprint, fp, 8);
    }

    /* wipe seed */
    memset(seed, 0, sizeof seed);
    oqd_jones_free(&inv);
    return OQD_OK;
}

static void subkeys(const uint8_t master[32], uint8_t enc[32], uint8_t mac[32]) {
    oqd_hmac_sha256(master, 32, (const uint8_t *)"oqd-enc-key", 11, enc);
    oqd_hmac_sha256(master, 32, (const uint8_t *)"oqd-mac-key", 11, mac);
}

int oqd_encrypt(const char *knot_path, const char *passphrase,
                const char *in_path, const char *out_path,
                oqd_keyinfo *info) {
    uint8_t salt[16], nonce[16];
    int rc = get_random(salt, 16); if (rc) return rc;
    rc = get_random(nonce, 16);    if (rc) return rc;

    uint8_t master[32], fp[8];
    rc = oqd_derive(knot_path, passphrase, salt, master, fp, info);
    if (rc) return rc;

    uint8_t *plain = NULL; long plen = 0;
    rc = read_all(in_path, &plain, &plen);
    if (rc) { memset(master, 0, 32); return rc; }

    uint8_t enc[32], mac[32];
    subkeys(master, enc, mac);

    size_t total = OQD_HEADER_LEN + (size_t)plen + OQD_TAG_LEN;
    uint8_t *out = malloc(total);
    if (!out) { free(plain); memset(master,0,32); return OQD_E_NOMEM; }

    out[0]=OQD_MAGIC0; out[1]=OQD_MAGIC1; out[2]=OQD_MAGIC2; out[3]=OQD_MAGIC3;
    out[4]=OQD_VERSION;
    out[5]=(passphrase && passphrase[0]) ? 0x01 : 0x00;
    out[6]=0; out[7]=0;
    memcpy(out + 8,  salt, 16);
    memcpy(out + 24, nonce, 16);
    memcpy(out + 40, fp, 8);

    oqd_ctr_xor(enc, nonce, plain, out + OQD_HEADER_LEN, (size_t)plen);

    uint8_t tag[32];
    oqd_hmac_sha256(mac, 32, out, OQD_HEADER_LEN + (size_t)plen, tag);
    memcpy(out + OQD_HEADER_LEN + plen, tag, OQD_TAG_LEN);

    rc = write_all(out_path, out, total);

    memset(master,0,32); memset(enc,0,32); memset(mac,0,32);
    free(plain); free(out);
    return rc;
}

int oqd_decrypt(const char *knot_path, const char *passphrase,
                const char *in_path, const char *out_path,
                oqd_keyinfo *info) {
    uint8_t *buf = NULL; long len = 0;
    int rc = read_all(in_path, &buf, &len);
    if (rc) return rc;
    if (len < OQD_HEADER_LEN + OQD_TAG_LEN) { free(buf); return OQD_E_FORMAT; }
    if (buf[0]!=OQD_MAGIC0||buf[1]!=OQD_MAGIC1||buf[2]!=OQD_MAGIC2||buf[3]!=OQD_MAGIC3) {
        free(buf); return OQD_E_FORMAT;
    }
    if (buf[4] != OQD_VERSION) { free(buf); return OQD_E_VERSION; }

    uint8_t salt[16], nonce[16], filefp[8];
    memcpy(salt,  buf + 8,  16);
    memcpy(nonce, buf + 24, 16);
    memcpy(filefp, buf + 40, 8);

    uint8_t master[32], fp[8];
    rc = oqd_derive(knot_path, passphrase, salt, master, fp, info);
    if (rc) { free(buf); return rc; }

    if (!oqd_ct_equal(fp, filefp, 8)) {
        memset(master,0,32); free(buf); return OQD_E_FINGERPRINT;
    }

    uint8_t enc[32], mac[32];
    subkeys(master, enc, mac);

    long cipher_len = len - OQD_HEADER_LEN - OQD_TAG_LEN;
    uint8_t tag[32];
    oqd_hmac_sha256(mac, 32, buf, (size_t)(OQD_HEADER_LEN + cipher_len), tag);
    if (!oqd_ct_equal(tag, buf + OQD_HEADER_LEN + cipher_len, OQD_TAG_LEN)) {
        memset(master,0,32); memset(enc,0,32); memset(mac,0,32);
        free(buf); return OQD_E_AUTH;
    }

    uint8_t *plain = malloc(cipher_len > 0 ? (size_t)cipher_len : 1);
    if (!plain) { memset(master,0,32); free(buf); return OQD_E_NOMEM; }
    oqd_ctr_xor(enc, nonce, buf + OQD_HEADER_LEN, plain, (size_t)cipher_len);

    rc = write_all(out_path, plain, (size_t)cipher_len);

    memset(master,0,32); memset(enc,0,32); memset(mac,0,32);
    free(plain); free(buf);
    return rc;
}

int oqd_inspect(const char *in_path, uint8_t salt[16], uint8_t nonce[16],
                uint8_t fingerprint[8], long *cipher_len) {
    uint8_t *buf = NULL; long len = 0;
    int rc = read_all(in_path, &buf, &len);
    if (rc) return rc;
    if (len < OQD_HEADER_LEN + OQD_TAG_LEN ||
        buf[0]!=OQD_MAGIC0||buf[1]!=OQD_MAGIC1||buf[2]!=OQD_MAGIC2||buf[3]!=OQD_MAGIC3) {
        free(buf); return OQD_E_FORMAT;
    }
    if (buf[4] != OQD_VERSION) { free(buf); return OQD_E_VERSION; }
    if (salt) memcpy(salt, buf + 8, 16);
    if (nonce) memcpy(nonce, buf + 24, 16);
    if (fingerprint) memcpy(fingerprint, buf + 40, 8);
    if (cipher_len) *cipher_len = len - OQD_HEADER_LEN - OQD_TAG_LEN;
    free(buf);
    return OQD_OK;
}
