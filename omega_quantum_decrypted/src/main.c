/* main.c — omega_quantum_decrypted command-line application.
 *
 *   Omega-Quantum-Decrypted (OQD)
 *   Jones-polynomial quantum cryptography — decryption tool
 *   Bada / Yamaguchi framework  ·  Linux / Ubuntu
 *
 * Primary purpose (解読 / decryption): recover a plaintext from an .oqd
 * container using a knot key file, whose Jones polynomial + quantum phase
 * spectrum derive the key.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "oqd.h"
#include "jones.h"
#include "qphase.h"

#ifndef OQD_APP_VERSION
#define OQD_APP_VERSION "1.0.0"
#endif

static const char *BANNER =
"  omega_quantum_decrypted " OQD_APP_VERSION "\n"
"  Jones-polynomial quantum cryptography — 解読 (decryption) tool\n"
"  Bada / Yamaguchi framework · self-contained (no external libraries)\n";

static void usage(const char *prog) {
    printf("%s\n", BANNER);
    printf("Usage:\n");
    printf("  %s decrypt  <knot.key> <in.oqd>  <out.file> [-p PASS]   # 解読\n", prog);
    printf("  %s encrypt  <knot.key> <in.file> <out.oqd>  [-p PASS]\n", prog);
    printf("  %s keyinfo  <knot.key> [-p PASS]     # show Jones / phase key report\n", prog);
    printf("  %s inspect  <in.oqd>                 # container header, no decryption\n", prog);
    printf("  %s selftest                          # built-in round-trip check\n", prog);
    printf("  %s version | help\n", prog);
    printf("\nKnot key file format (one crossing per line):\n");
    printf("    id  a b c d  sign        # a,b,c,d = edge labels, sign = +1/-1\n");
    printf("    # lines beginning with '#' are comments\n");
    printf("\nThe key is derived from the diagram's Kauffman bracket and its\n");
    printf("writhe-normalised Jones polynomial (a topological knot invariant),\n");
    printf("then folded through the Unknown-Prior Engine phase core. Add -p PASS\n");
    printf("to bind a passphrase to the knot key as well.\n");
}

static const char *opt_pass(int argc, char **argv, int start) {
    for (int i = start; i < argc - 1; i++)
        if (strcmp(argv[i], "-p") == 0 || strcmp(argv[i], "--pass") == 0)
            return argv[i + 1];
    return NULL;
}

static void print_hex(const char *label, const uint8_t *b, int n) {
    printf("%s", label);
    for (int i = 0; i < n; i++) printf("%02x", b[i]);
    printf("\n");
}

static void print_keyinfo(const oqd_keyinfo *ki) {
    printf("  knot crossings   : %d\n", ki->n_crossings);
    printf("  writhe w         : %d\n", ki->writhe);
    printf("  Jones span       : %.0f\n", ki->jones_span);
    printf("  phase entropy    : %.6f nats\n", ki->entropy);
    printf("  unitarity error  : %.3e   (|psi|^2 = a; Theorem 2)\n", ki->unitarity_error);
    printf("  zeros preserved  : %s   (Theorem 1: confident zero survives)\n",
           ki->zeros_preserved ? "yes" : "NO");
    print_hex("  key fingerprint  : ", ki->fingerprint, 8);
}

static int cmd_keyinfo(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "keyinfo needs <knot.key>\n"); return 2; }
    const char *pass = opt_pass(argc, argv, 3);
    uint8_t master[32], fp[8]; oqd_keyinfo ki;
    uint8_t zero_salt[16] = {0};
    int rc = oqd_derive(argv[2], pass, zero_salt, master, fp, &ki);
    if (rc) { fprintf(stderr, "error: %s\n", oqd_strerror(rc)); return 1; }
    printf("%s\n", BANNER);
    printf("Key report for knot key '%s':\n", argv[2]);
    print_keyinfo(&ki);
    memset(master, 0, 32);
    return 0;
}

static int cmd_inspect(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "inspect needs <in.oqd>\n"); return 2; }
    uint8_t salt[16], nonce[16], fp[8]; long clen = 0;
    int rc = oqd_inspect(argv[2], salt, nonce, fp, &clen);
    if (rc) { fprintf(stderr, "error: %s\n", oqd_strerror(rc)); return 1; }
    printf("OQD container '%s':\n", argv[2]);
    printf("  payload bytes    : %ld\n", clen);
    print_hex("  salt             : ", salt, 16);
    print_hex("  nonce            : ", nonce, 16);
    print_hex("  key fingerprint  : ", fp, 8);
    printf("  (fingerprint identifies which knot key can open this file)\n");
    return 0;
}

static int cmd_crypt(int argc, char **argv, int decrypt) {
    if (argc < 5) {
        fprintf(stderr, "%s needs <knot.key> <in> <out>\n", decrypt ? "decrypt" : "encrypt");
        return 2;
    }
    const char *knot = argv[2], *in = argv[3], *out = argv[4];
    const char *pass = opt_pass(argc, argv, 5);
    oqd_keyinfo ki;
    int rc = decrypt ? oqd_decrypt(knot, pass, in, out, &ki)
                     : oqd_encrypt(knot, pass, in, out, &ki);
    if (rc) { fprintf(stderr, "error: %s\n", oqd_strerror(rc)); return 1; }
    printf("%s -> %s\n", decrypt ? "decrypted (解読)" : "encrypted", out);
    print_keyinfo(&ki);
    return 0;
}

/* Built-in round-trip: derive a knot key on the fly, encrypt, decrypt, verify,
 * and check that a wrong key is rejected. */
static int cmd_selftest(void) {
    const char *dir = getenv("TMPDIR"); if (!dir) dir = "/tmp";
    char knot[512], knot2[512], msg[512], enc[512], dec[512];
    snprintf(knot,  sizeof knot,  "%s/oqd_st_trefoil.key", dir);
    snprintf(knot2, sizeof knot2, "%s/oqd_st_figure8.key", dir);
    snprintf(msg,   sizeof msg,   "%s/oqd_st_msg.txt", dir);
    snprintf(enc,   sizeof enc,   "%s/oqd_st_msg.oqd", dir);
    snprintf(dec,   sizeof dec,   "%s/oqd_st_msg.out", dir);

    FILE *f;
    f = fopen(knot, "w");  if(!f) return 1;
    fputs("# trefoil 3_1\n0 1 2 3 4 1\n1 3 4 5 6 1\n2 5 6 1 2 1\n", f); fclose(f);
    f = fopen(knot2, "w"); if(!f) return 1;
    fputs("# figure-eight 4_1\n0 1 2 3 4 1\n1 3 4 5 6 -1\n2 5 6 7 8 1\n3 7 8 1 2 -1\n", f); fclose(f);
    const char *secret = "Omega quantum decrypted — 山口フレームワーク. |psi|^2 = a.";
    f = fopen(msg, "w"); if(!f) return 1; fputs(secret, f); fclose(f);

    printf("%s\n", BANNER);
    printf("[selftest] SHA-256 / HMAC / CTR ... (verified at build)\n");

    int rc = oqd_encrypt(knot, NULL, msg, enc, NULL);
    if (rc) { fprintf(stderr, "[selftest] encrypt: %s\n", oqd_strerror(rc)); return 1; }
    printf("[selftest] encrypt OK -> %s\n", enc);

    rc = oqd_decrypt(knot, NULL, enc, dec, NULL);
    if (rc) { fprintf(stderr, "[selftest] decrypt: %s\n", oqd_strerror(rc)); return 1; }

    /* compare */
    char got[1024]; f = fopen(dec, "rb"); if(!f) return 1;
    size_t n = fread(got, 1, sizeof got - 1, f); got[n] = 0; fclose(f);
    if (strcmp(got, secret) != 0) {
        fprintf(stderr, "[selftest] FAIL: round-trip mismatch\n"); return 1;
    }
    printf("[selftest] decrypt OK, plaintext matches\n");

    /* wrong knot key must be rejected (fingerprint or auth) */
    rc = oqd_decrypt(knot2, NULL, enc, dec, NULL);
    if (rc == OQD_OK) { fprintf(stderr, "[selftest] FAIL: wrong key accepted!\n"); return 1; }
    printf("[selftest] wrong knot key correctly rejected: %s\n", oqd_strerror(rc));

    printf("[selftest] ALL PASS\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { usage(argv[0]); return 1; }
    const char *cmd = argv[1];
    if (!strcmp(cmd, "decrypt")) return cmd_crypt(argc, argv, 1);
    if (!strcmp(cmd, "encrypt")) return cmd_crypt(argc, argv, 0);
    if (!strcmp(cmd, "keyinfo")) return cmd_keyinfo(argc, argv);
    if (!strcmp(cmd, "inspect")) return cmd_inspect(argc, argv);
    if (!strcmp(cmd, "selftest")) return cmd_selftest();
    if (!strcmp(cmd, "version") || !strcmp(cmd, "--version") || !strcmp(cmd, "-v")) {
        printf("omega_quantum_decrypted %s\n", OQD_APP_VERSION); return 0;
    }
    if (!strcmp(cmd, "help") || !strcmp(cmd, "--help") || !strcmp(cmd, "-h")) {
        usage(argv[0]); return 0;
    }
    fprintf(stderr, "unknown command: %s\n", cmd);
    usage(argv[0]);
    return 1;
}
