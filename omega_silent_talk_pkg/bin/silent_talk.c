/* ============================================================================
 *  bin/silent_talk.c
 *  omega_silent_talk_pkg — CLI ドライバ
 *
 *  使い方:
 *    ./bin/silent_talk --demo
 *    ./bin/silent_talk --decode neuro.txt thermal.txt [vocab]
 *    ./bin/silent_talk --frame  neuro.txt out.pgm
 *    ./bin/silent_talk --gamma  s
 *    ./bin/silent_talk --zeta   s
 * ==========================================================================*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/omega_silent.h"

static int read_series(const char *path, double **out) {
    FILE *f = fopen(path, "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", path); return -1; }
    int cap = 64, n = 0;
    double *buf = (double *)malloc(sizeof(double) * cap);
    double v;
    while (fscanf(f, "%lf", &v) == 1) {
        if (n >= cap) { cap *= 2; buf = (double *)realloc(buf, sizeof(double) * cap); }
        buf[n++] = v;
    }
    fclose(f);
    *out = buf;
    return n;
}

static void run_demo(void) {
    printf("== omega_silent_talk :: DEMO ==\n");
    printf("Gamma-function Global Partial-Integration Manifold AGI\n\n");

    /* 合成した脳信号:
     * 「一貫した無発声思考(集中した意図)」を模した明瞭な二値パターン。
     * 焦点が定まった思考ほど信号は安定し、観測ノイズは小さい。 */
    int N = 24;
    double neuro[24];
    for (int i = 0; i < N; i++)
        neuro[i] = ((i % 2) ? 1.0 : -1.0) + 0.03 * ((i * 37) % 5 - 2);

    /* 体内/脳 熱エネルギー時系列:
     * 集中時は緩やかで構造的なゆらぎ (秩序ある熱 = 高い意図性)。 */
    int T = 16;
    double thermal[16];
    for (int i = 0; i < T; i++)
        thermal[i] = 36.9 + 0.15 * sin(0.5 * i);

    silent_input_t in;
    memset(&in, 0, sizeof(in));
    in.neuro = neuro;       in.neuro_len = N;
    in.thermal = thermal;   in.thermal_len = T;
    in.vocab = 8;           in.s_temp = 2.0;   in.kT = 0.5;

    silent_output_t o = silent_decode(&in);

    printf("復号記号列 (thought symbols):\n  ");
    for (int i = 0; i < o.len; i++) printf("%d ", o.symbols ? o.symbols[i] : -1);
    printf("\n\n");
    printf("confidence (信頼度)      : %.4f\n", o.confidence);
    printf("silent-talk baseline     : %.4f\n", 0.62);
    printf("precision gain over base : %+.1f%%\n", 100.0 * silent_precision_gain(o.confidence));
    printf("thermal intent (Jones)   : %.4f\n", o.intent);
    printf("decode entropy (Shannon) : %.4f bits\n", o.entropy);
    printf("\nΓ(0.5)=%.6f  (=√π=%.6f)\n", gamma_eval(0.5), sqrt(M_PI));
    printf("ζ(2)  =%.6f  (=π²/6=%.6f)\n", zeta_eval(2.0), M_PI * M_PI / 6.0);
    printf("manifold ∬(2..%d) = %.6f\n", 2 + N, gpi_manifold(2.0, 2.0 + N, N));

    silent_output_free(&o);
}

static void write_pgm(const char *path, unsigned char *frame, int w, int h) {
    FILE *f = fopen(path, "wb");
    if (!f) { fprintf(stderr, "cannot write %s\n", path); return; }
    fprintf(f, "P5\n%d %d\n255\n", w, h);
    fwrite(frame, 1, (size_t)w * h, f);
    fclose(f);
    printf("wrote %s (%dx%d PGM)\n", path, w, h);
}

int main(int argc, char **argv) {
    if (argc < 2 || strcmp(argv[1], "--demo") == 0) {
        run_demo();
        return 0;
    }
    if (strcmp(argv[1], "--gamma") == 0 && argc >= 3) {
        printf("Gamma(%s) = %.10f\n", argv[2], gamma_eval(atof(argv[2])));
        return 0;
    }
    if (strcmp(argv[1], "--zeta") == 0 && argc >= 3) {
        printf("Zeta(%s)  = %.10f\n", argv[2], zeta_eval(atof(argv[2])));
        return 0;
    }
    if (strcmp(argv[1], "--decode") == 0 && argc >= 4) {
        double *neuro = NULL, *thermal = NULL;
        int nn = read_series(argv[2], &neuro);
        int nt = read_series(argv[3], &thermal);
        int vocab = (argc >= 5) ? atoi(argv[4]) : 8;
        if (nn <= 0) { fprintf(stderr, "no neuro data\n"); return 1; }
        silent_input_t in; memset(&in, 0, sizeof(in));
        in.neuro = neuro; in.neuro_len = nn;
        in.thermal = thermal; in.thermal_len = (nt > 0) ? nt : 0;
        in.vocab = (vocab > 1) ? vocab : 8; in.s_temp = 2.0; in.kT = 0.5;
        silent_output_t o = silent_decode(&in);
        printf("symbols: ");
        for (int i = 0; i < o.len; i++) printf("%d ", o.symbols[i]);
        printf("\nconfidence=%.4f gain=%+.1f%% intent=%.4f entropy=%.4f\n",
               o.confidence, 100.0 * silent_precision_gain(o.confidence),
               o.intent, o.entropy);
        silent_output_free(&o);
        free(neuro); free(thermal);
        return 0;
    }
    if (strcmp(argv[1], "--frame") == 0 && argc >= 4) {
        double *neuro = NULL;
        int nn = read_series(argv[2], &neuro);
        if (nn <= 0) { fprintf(stderr, "no neuro data\n"); return 1; }
        int d_model = 8, seq_len = 4;
        xformer_t *xf = xformer_create(d_model, 2);
        double toks[4 * 8], lat[4 * 8];
        for (int i = 0; i < seq_len * d_model; i++) toks[i] = neuro[i % nn];
        xformer_forward(xf, toks, seq_len, lat);
        int w = 64, h = 64;
        unsigned char *frame = (unsigned char *)malloc((size_t)w * h);
        xformer_render(xf, lat, seq_len, frame, w, h);
        write_pgm(argv[3], frame, w, h);
        free(frame); xformer_free(xf); free(neuro);
        return 0;
    }

    fprintf(stderr,
        "usage:\n"
        "  %s --demo\n"
        "  %s --decode neuro.txt thermal.txt [vocab]\n"
        "  %s --frame  neuro.txt out.pgm\n"
        "  %s --gamma  s\n"
        "  %s --zeta   s\n",
        argv[0], argv[0], argv[0], argv[0], argv[0]);
    return 1;
}
