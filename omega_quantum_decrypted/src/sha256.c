/* sha256.c — FIPS 180-4 SHA-256 + RFC 2104 HMAC + CTR keystream.
 * Self-contained reference implementation (no OpenSSL). */
#include "sha256.h"
#include <string.h>

static const uint32_t K[64] = {
    0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,
    0x923f82a4u,0xab1c5ed5u,0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,
    0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,0xe49b69c1u,0xefbe4786u,
    0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
    0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,
    0x06ca6351u,0x14292967u,0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,
    0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,0xa2bfe8a1u,0xa81a664bu,
    0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
    0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,
    0x5b9cca4fu,0x682e6ff3u,0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,
    0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
};

#define ROR(x,n) (((x) >> (n)) | ((x) << (32 - (n))))

static void sha256_compress(uint32_t state[8], const uint8_t block[64]) {
    uint32_t w[64];
    for (int i = 0; i < 16; i++) {
        w[i] = ((uint32_t)block[i*4] << 24) | ((uint32_t)block[i*4+1] << 16) |
               ((uint32_t)block[i*4+2] << 8) | ((uint32_t)block[i*4+3]);
    }
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = ROR(w[i-15],7) ^ ROR(w[i-15],18) ^ (w[i-15] >> 3);
        uint32_t s1 = ROR(w[i-2],17) ^ ROR(w[i-2],19) ^ (w[i-2] >> 10);
        w[i] = w[i-16] + s0 + w[i-7] + s1;
    }
    uint32_t a=state[0],b=state[1],c=state[2],d=state[3];
    uint32_t e=state[4],f=state[5],g=state[6],h=state[7];
    for (int i = 0; i < 64; i++) {
        uint32_t S1 = ROR(e,6) ^ ROR(e,11) ^ ROR(e,25);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t t1 = h + S1 + ch + K[i] + w[i];
        uint32_t S0 = ROR(a,2) ^ ROR(a,13) ^ ROR(a,22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t t2 = S0 + maj;
        h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }
    state[0]+=a; state[1]+=b; state[2]+=c; state[3]+=d;
    state[4]+=e; state[5]+=f; state[6]+=g; state[7]+=h;
}

void oqd_sha256_init(oqd_sha256_ctx *c) {
    c->state[0]=0x6a09e667u; c->state[1]=0xbb67ae85u;
    c->state[2]=0x3c6ef372u; c->state[3]=0xa54ff53au;
    c->state[4]=0x510e527fu; c->state[5]=0x9b05688cu;
    c->state[6]=0x1f83d9abu; c->state[7]=0x5be0cd19u;
    c->bitlen = 0; c->buflen = 0;
}

void oqd_sha256_update(oqd_sha256_ctx *c, const void *data, size_t len) {
    const uint8_t *p = (const uint8_t *)data;
    c->bitlen += (uint64_t)len * 8u;
    while (len > 0) {
        size_t take = OQD_SHA256_BLOCK - c->buflen;
        if (take > len) take = len;
        memcpy(c->buf + c->buflen, p, take);
        c->buflen += take; p += take; len -= take;
        if (c->buflen == OQD_SHA256_BLOCK) {
            sha256_compress(c->state, c->buf);
            c->buflen = 0;
        }
    }
}

void oqd_sha256_final(oqd_sha256_ctx *c, uint8_t out[OQD_SHA256_DIGEST]) {
    uint64_t bl = c->bitlen;
    uint8_t pad = 0x80;
    oqd_sha256_update(c, &pad, 1);
    uint8_t zero = 0x00;
    while (c->buflen != 56) oqd_sha256_update(c, &zero, 1);
    uint8_t lenbuf[8];
    for (int i = 0; i < 8; i++) lenbuf[i] = (uint8_t)(bl >> (56 - i*8));
    /* update() adds to bitlen; write length bytes directly instead */
    memcpy(c->buf + c->buflen, lenbuf, 8);
    sha256_compress(c->state, c->buf);
    for (int i = 0; i < 8; i++) {
        out[i*4]   = (uint8_t)(c->state[i] >> 24);
        out[i*4+1] = (uint8_t)(c->state[i] >> 16);
        out[i*4+2] = (uint8_t)(c->state[i] >> 8);
        out[i*4+3] = (uint8_t)(c->state[i]);
    }
}

void oqd_sha256(const void *data, size_t len, uint8_t out[OQD_SHA256_DIGEST]) {
    oqd_sha256_ctx c; oqd_sha256_init(&c);
    oqd_sha256_update(&c, data, len);
    oqd_sha256_final(&c, out);
}

void oqd_hmac_sha256(const uint8_t *key, size_t keylen,
                     const uint8_t *msg, size_t msglen,
                     uint8_t out[OQD_SHA256_DIGEST]) {
    uint8_t k[OQD_SHA256_BLOCK];
    uint8_t ipad[OQD_SHA256_BLOCK], opad[OQD_SHA256_BLOCK];
    uint8_t inner[OQD_SHA256_DIGEST];
    memset(k, 0, sizeof k);
    if (keylen > OQD_SHA256_BLOCK) {
        oqd_sha256(key, keylen, k);
    } else {
        memcpy(k, key, keylen);
    }
    for (int i = 0; i < OQD_SHA256_BLOCK; i++) {
        ipad[i] = k[i] ^ 0x36;
        opad[i] = k[i] ^ 0x5c;
    }
    oqd_sha256_ctx c;
    oqd_sha256_init(&c);
    oqd_sha256_update(&c, ipad, OQD_SHA256_BLOCK);
    oqd_sha256_update(&c, msg, msglen);
    oqd_sha256_final(&c, inner);
    oqd_sha256_init(&c);
    oqd_sha256_update(&c, opad, OQD_SHA256_BLOCK);
    oqd_sha256_update(&c, inner, OQD_SHA256_DIGEST);
    oqd_sha256_final(&c, out);
}

void oqd_kdf(const uint8_t *seed, size_t seedlen,
             const uint8_t *salt, size_t saltlen,
             uint32_t iters,
             uint8_t *out, size_t outlen) {
    if (iters == 0) iters = 1;
    uint8_t prk[OQD_SHA256_DIGEST];
    /* extract: prk = HMAC(salt, seed) */
    oqd_hmac_sha256(salt, saltlen, seed, seedlen, prk);
    /* iterate to stretch (PBKDF2-style over prk) */
    uint8_t t[OQD_SHA256_DIGEST];
    uint8_t u[OQD_SHA256_DIGEST];
    size_t done = 0;
    uint32_t block = 1;
    while (done < outlen) {
        uint8_t ctr[4] = {
            (uint8_t)(block >> 24), (uint8_t)(block >> 16),
            (uint8_t)(block >> 8),  (uint8_t)(block)
        };
        /* U1 = HMAC(prk, salt || block) */
        oqd_sha256_ctx hc; (void)hc;
        uint8_t msg[64];
        size_t ml = 0;
        if (saltlen > 60) saltlen = 60;
        memcpy(msg, salt, saltlen); ml = saltlen;
        memcpy(msg + ml, ctr, 4); ml += 4;
        oqd_hmac_sha256(prk, sizeof prk, msg, ml, u);
        memcpy(t, u, OQD_SHA256_DIGEST);
        for (uint32_t i = 1; i < iters; i++) {
            oqd_hmac_sha256(prk, sizeof prk, u, OQD_SHA256_DIGEST, u);
            for (int j = 0; j < OQD_SHA256_DIGEST; j++) t[j] ^= u[j];
        }
        size_t take = outlen - done;
        if (take > OQD_SHA256_DIGEST) take = OQD_SHA256_DIGEST;
        memcpy(out + done, t, take);
        done += take;
        block++;
    }
}

void oqd_ctr_xor(const uint8_t key[32], const uint8_t nonce[16],
                 const uint8_t *in, uint8_t *out, size_t len) {
    uint8_t block[OQD_SHA256_BLOCK];
    uint8_t ks[OQD_SHA256_DIGEST];
    uint64_t counter = 0;
    size_t off = 0;
    while (off < len) {
        /* keystream block = HMAC(key, nonce || counter) */
        memcpy(block, nonce, 16);
        for (int i = 0; i < 8; i++)
            block[16 + i] = (uint8_t)(counter >> (56 - i*8));
        oqd_hmac_sha256(key, 32, block, 24, ks);
        size_t take = len - off;
        if (take > OQD_SHA256_DIGEST) take = OQD_SHA256_DIGEST;
        for (size_t i = 0; i < take; i++) out[off + i] = in[off + i] ^ ks[i];
        off += take;
        counter++;
    }
}

int oqd_ct_equal(const uint8_t *a, const uint8_t *b, size_t len) {
    uint8_t diff = 0;
    for (size_t i = 0; i < len; i++) diff |= (uint8_t)(a[i] ^ b[i]);
    return diff == 0;
}
