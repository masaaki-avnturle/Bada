/* main.c — omega_neurothermal
 *
 * ガンマ関数の大域的部分積分多様体の熱エネルギー (T' = ∫Γ(γ)'dx_m) を起点に、
 * 大脳基底核を通って体末端へ流れる「エネルギー体」をモデル化し、
 * 赤外線センサー/温度計/MRI/fMRI/脳トポグラフィ/血液検査/CT/DNA・RNA解析の
 * 各装置機能(シミュレーション)を統合する CLI アプリケーション。
 *
 *  ビルド: make            (または: gcc -std=c99 -O2 src(slash)*.c -o omega_neurothermal -lm)
 *  実行  : ./omega_neurothermal <command> [args]
 *
 *  注意: 本ソフトウェアは教育・可視化・理論探求のための数値シミュレーションです。
 *        実在の医療機器制御・診断・治療の用途には使用しないでください。
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "gamma_thermal.h"
#include "basal_ganglia.h"
#include "sensors.h"
#include "imaging.h"
#include "labanalysis.h"

static const char *BANNER =
"==============================================================\n"
"  omega_neurothermal — Gamma-Manifold Neuro-Thermal Workbench\n"
"  T' = INTEGRAL Gamma(gamma)' dx_m   (Yamaguchi framework)\n"
"  [Educational simulation — not a medical device]\n"
"==============================================================\n";

static double bar_fill(double v, double vmax, char *buf, int width)
{
    int n = (int)((v / (vmax <= 0 ? 1 : vmax)) * width);
    if (n < 0) n = 0;
    if (n > width) n = width;
    int i = 0;
    for (; i < n; ++i) buf[i] = '#';
    for (; i < width; ++i) buf[i] = '.';
    buf[width] = 0;
    return v;
}

/* ---- subcommands ---- */

static int cmd_gamma(int argc, char **argv)
{
    double lo = (argc > 0) ? atof(argv[0]) : 1.0;
    double hi = (argc > 1) ? atof(argv[1]) : 5.0;
    int steps = (argc > 2) ? atoi(argv[2]) : 2000;

    double E = om_thermal_energy(lo, hi, steps);
    double Tc = om_thermal_to_celsius(E, 37.0, 1.5);

    printf("[GAMMA THERMAL MANIFOLD]\n");
    printf("  integrand : Gamma'(g) = Gamma(g)*psi(g)\n");
    printf("  domain    : g in [%.3f, %.3f], steps=%d\n", lo, hi, steps);
    printf("  T' = INT Gamma'(g) dx_m = %.6f  [Omega-thermal units]\n", E);
    printf("  mapped core temperature  = %.3f C\n", Tc);
    printf("  sample table:\n");
    for (double g = lo; g <= hi + 1e-9; g += (hi - lo) / 8.0)
        printf("    g=%.3f  Gamma=%.5g  psi=%.5g  Gamma'=%.5g\n",
               g, om_gamma(g), om_digamma(g), om_gamma_prime(g));
    return 0;
}

static int cmd_basal(int argc, char **argv)
{
    double E   = (argc > 0) ? atof(argv[0]) : om_thermal_energy(1.0, 5.0, 2000);
    double dop = (argc > 1) ? atof(argv[1]) : 0.6;

    bg_state_t st; memset(&st, 0, sizeof(st));
    bg_propagate(&st, fabs(E), dop);

    printf("[BASAL GANGLIA ENERGY FLOW]  source=%.4f  dopamine=%.2f\n", E, dop);
    char bar[41];
    double nmax = 0; for (int i=0;i<BG_NUCLEI_COUNT;i++) if (st.nucleus[i]>nmax) nmax=st.nucleus[i];
    for (int i = 0; i < BG_NUCLEI_COUNT; ++i) {
        bar_fill(st.nucleus[i], nmax, bar, 30);
        printf("  %-22s |%s| %.4f\n", bg_nucleus_name(i), bar, st.nucleus[i]);
    }
    printf("  --- propagation brain -> extremities ---\n");
    double smax = 0; for (int i=0;i<SEG_COUNT;i++) if (st.segment[i]>smax) smax=st.segment[i];
    for (int i = 0; i < SEG_COUNT; ++i) {
        bar_fill(st.segment[i], smax, bar, 30);
        printf("  %-22s |%s| %.4f\n", bg_segment_name(i), bar, st.segment[i]);
    }
    printf("  total peripheral output = %.4f\n", bg_total_output(&st));
    return 0;
}

static int cmd_sensor(int argc, char **argv)
{
    double true_c = (argc > 0) ? atof(argv[0]) : 36.8;
    double emiss  = (argc > 1) ? atof(argv[1]) : 0.97;
    unsigned seed = 12345u;

    printf("[IR SENSOR + THERMOMETER]  true=%.2f C  emissivity=%.2f\n", true_c, emiss);
    double prev = true_c;
    double s_ir = 0, s_th = 0, s_ir2 = 0, s_th2 = 0; int N = 8;
    for (int k = 0; k < N; ++k) {
        double ir = ir_sensor_read(true_c, emiss, 25.0, 0.15, &seed);
        double th = thermometer_read(true_c, prev, 0.4, 0.08, &seed);
        prev = th;
        double fvar, fused = sensor_fuse(ir, 0.15*0.15, th, 0.08*0.08, &fvar);
        printf("  t=%d  IR=%.3f  Thermo=%.3f  -> fused=%.3f (+/-%.3f)\n",
               k, ir, th, fused, sqrt(fvar));
        s_ir += ir; s_ir2 += ir*ir; s_th += th; s_th2 += th*th;
    }
    printf("  IR mean=%.3f sd=%.3f | Thermo mean=%.3f sd=%.3f\n",
           s_ir/N, sqrt(s_ir2/N - (s_ir/N)*(s_ir/N)),
           s_th/N, sqrt(s_th2/N - (s_th/N)*(s_th/N)));
    return 0;
}

static int cmd_mri(int argc, char **argv)
{
    const char *tissue = (argc > 0) ? argv[0] : "gray";
    double t1, t2;
    if (!mri_tissue_params(tissue, &t1, &t2)) {
        printf("unknown tissue '%s' (try: gray white csf fat muscle blood)\n", tissue);
        return 1;
    }
    printf("[MRI SPIN-ECHO]  tissue=%s  T1=%.0fms T2=%.0fms\n", tissue, t1, t2);
    printf("    TR(ms)   TE(ms)   signal\n");
    double TRs[] = {500, 2000, 4000};
    double TEs[] = {15, 80, 120};
    for (int a = 0; a < 3; ++a)
        for (int b = 0; b < 3; ++b)
            printf("    %7.0f  %7.0f  %.4f\n", TRs[a], TEs[b],
                   mri_spin_echo(1.0, t1, t2, TRs[a], TEs[b]));
    return 0;
}

static int cmd_fmri(int argc, char **argv)
{
    (void)argc; (void)argv;
    int n = 30; double dt = 1.0;
    double act[30] = {0};
    act[3] = act[4] = act[5] = 1.0;   /* 刺激ブロック */
    act[15] = act[16] = 1.0;
    double bold[30];
    fmri_bold(act, bold, n, dt);
    printf("[fMRI BOLD]  double-gamma HRF, dt=%.1fs\n", dt);
    double bmax = 0; for (int i=0;i<n;i++) if (bold[i]>bmax) bmax=bold[i];
    char bar[41];
    for (int i = 0; i < n; ++i) {
        bar_fill(bold[i] < 0 ? 0 : bold[i], bmax, bar, 30);
        printf("  t=%2ds act=%.0f |%s| %.4f\n", i, act[i], bar, bold[i]);
    }
    return 0;
}

static int cmd_topo(int argc, char **argv)
{
    (void)argc; (void)argv;
    /* 基底核エネルギーを線源として頭皮 16 電極へ投影 */
    double E = om_thermal_energy(1.0, 5.0, 2000);
    bg_state_t st; memset(&st, 0, sizeof(st));
    bg_propagate(&st, fabs(E), 0.6);
    double src[4] = { st.nucleus[BG_CAUDATE], st.nucleus[BG_PUTAMEN],
                      st.nucleus[BG_GPI],     st.nucleus[BG_STN] };
    double ang[4] = { 0.3, 1.9, 3.4, 5.0 };
    int E_N = 16; double pot[16];
    topography_project(src, ang, 4, pot, E_N);
    printf("[BRAIN TOPOGRAPHY]  %d scalp electrodes\n", E_N);
    double pmax = 0; for (int i=0;i<E_N;i++) if (pot[i]>pmax) pmax=pot[i];
    char bar[41];
    for (int i = 0; i < E_N; ++i) {
        bar_fill(pot[i], pmax, bar, 30);
        printf("  E%02d (%3.0f deg) |%s| %.4f\n",
               i, 360.0*i/E_N, bar, pot[i]);
    }
    return 0;
}

static int cmd_ct(int argc, char **argv)
{
    (void)argc; (void)argv;
    /* 脳 -> 体末端パス: 各層の線減弱係数(cm^-1)と厚み(cm) */
    const char *layer[] = {"scalp/fat","skull/bone","gray matter",
                           "white matter","muscle","cortical bone(limb)"};
    double mu[]  = {0.020, 0.048, 0.021, 0.020, 0.023, 0.050};
    double thk[] = {0.6,   0.7,   2.0,   3.0,   4.0,   0.5};
    const double mu_water = 0.019;
    int L = 6;
    printf("[CT SCAN]  brain -> extremity path  (Beer-Lambert)\n");
    printf("    %-22s mu(cm-1)  thick(cm)   HU\n", "layer");
    for (int i = 0; i < L; ++i)
        printf("    %-22s %7.4f   %7.2f   %+7.1f\n",
               layer[i], mu[i], thk[i], ct_hounsfield(mu[i], mu_water));
    printf("  path transmission I/I0 = %.6e\n",
           ct_path_transmission(mu, thk, L));
    return 0;
}

static int cmd_blood(int argc, char **argv)
{
    double bias = (argc > 0) ? atof(argv[0]) : 1.0;
    unsigned seed = 2026u;
    blood_marker_t m[16];
    int n = blood_panel(m, 16, bias, &seed);
    printf("[BLOOD PANEL]  thermal_bias=%.2f\n", bias);
    printf("    %-12s %10s %8s   range            flag\n", "marker", "value", "unit");
    for (int i = 0; i < n; ++i) {
        char f = blood_flag(&m[i]);
        printf("    %-12s %10.2f %8s   [%6.1f-%6.1f]   %c\n",
               m[i].name, m[i].value, m[i].unit, m[i].lo, m[i].hi, f);
    }
    return 0;
}

static int cmd_dna(int argc, char **argv)
{
    const char *seq = (argc > 0) ? argv[0]
                    : "ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG";
    dna_stats_t s = dna_analyze(seq);
    printf("[DNA ANALYSIS]\n  seq      : %s\n", seq);
    printf("  length   : %zu  (valid=%s)\n", s.length, s.valid ? "yes":"no");
    printf("  A=%zu C=%zu G=%zu T=%zu  GC=%.1f%%\n",
           s.count[0], s.count[1], s.count[2], s.count[3], 100.0*s.gc_content);
    char km[8]; int kc;
    dna_top_kmer(seq, 3, km, sizeof(km), &kc);
    printf("  top 3-mer: %s (x%d)\n", km, kc);
    return 0;
}

static int cmd_rna(int argc, char **argv)
{
    const char *dna = (argc > 0) ? argv[0]
                    : "ATGGCCATTGTAATGGGCCGCTGA";
    char rna[8192], aa[4096];
    rna_transcribe(dna, rna, sizeof(rna));
    rna_translate(rna, aa, sizeof(aa));
    printf("[RNA ANALYSIS]\n  DNA sense : %s\n", dna);
    printf("  mRNA      : %s\n", rna);
    printf("  peptide   : %s\n", aa);
    return 0;
}

/* end-to-end pipeline: gamma -> temp -> sensors -> basal ganglia -> labs */
static int cmd_pipeline(int argc, char **argv)
{
    (void)argc; (void)argv;
    fputs(BANNER, stdout);
    double E  = om_thermal_energy(1.0, 5.0, 4000);
    double Tc = om_thermal_to_celsius(E, 37.0, 1.5);
    printf("\n[1] Gamma manifold thermal energy  T' = %.4f -> core %.2f C\n", E, Tc);

    unsigned seed = 777u;
    double ir = ir_sensor_read(Tc, 0.97, 25.0, 0.1, &seed);
    double th = thermometer_read(Tc, Tc, 0.3, 0.05, &seed);
    double fvar, fused = sensor_fuse(ir, 0.01, th, 0.0025, &fvar);
    printf("[2] Sensors  IR=%.3f  Thermo=%.3f  -> fused core=%.3f C\n", ir, th, fused);

    bg_state_t st; memset(&st, 0, sizeof(st));
    bg_propagate(&st, fabs(E), 0.6);
    printf("[3] Basal ganglia peripheral output = %.4f (hand=%.4f foot=%.4f)\n",
           bg_total_output(&st), st.segment[SEG_HAND], st.segment[SEG_FOOT]);

    blood_marker_t m[16];
    int n = blood_panel(m, 16, (fused - 37.0), &seed);
    int abn = 0; for (int i=0;i<n;i++) if (blood_flag(&m[i])!='N') abn++;
    printf("[4] Blood panel: %d markers, %d out-of-range\n", n, abn);

    dna_stats_t ds = dna_analyze("ATGGCCATTGTAATGGGCCGCTGAAAGG");
    printf("[5] DNA len=%zu GC=%.1f%% | ", ds.length, 100.0*ds.gc_content);
    char rna[256], aa[128];
    rna_transcribe("ATGGCCATTGTAATGGGCCGCTGA", rna, sizeof(rna));
    rna_translate(rna, aa, sizeof(aa));
    printf("RNA peptide=%s\n", aa);
    printf("\nPipeline complete.\n");
    return 0;
}

static void usage(const char *prog)
{
    fputs(BANNER, stdout);
    printf("\nUsage: %s <command> [args]\n\n", prog);
    printf("  gamma  [lo hi steps]   Gamma-manifold thermal energy T'=INT Gamma' dx\n");
    printf("  basal  [E dopamine]    Basal-ganglia energy flow to extremities\n");
    printf("  sensor [trueC emiss]   IR sensor + thermometer fusion\n");
    printf("  mri    [tissue]        MRI spin-echo signal table\n");
    printf("  fmri                   fMRI BOLD (double-gamma HRF)\n");
    printf("  topo                   Brain topography scalp map\n");
    printf("  ct                     CT scan brain->extremity (Hounsfield)\n");
    printf("  blood  [thermalbias]   Blood panel with reference ranges\n");
    printf("  dna    [seq]           DNA sequence stats / k-mer\n");
    printf("  rna    [dnaSeq]        Transcription + translation\n");
    printf("  pipeline               Run full end-to-end pipeline\n");
    printf("  help                   This message\n\n");
    printf("NOTE: educational simulation only; not for clinical use.\n");
}

int main(int argc, char **argv)
{
    if (argc < 2) { usage(argv[0]); return 1; }
    const char *c = argv[1];
    int ac = argc - 2; char **av = argv + 2;

    if (!strcmp(c, "gamma"))    return cmd_gamma(ac, av);
    if (!strcmp(c, "basal"))    return cmd_basal(ac, av);
    if (!strcmp(c, "sensor"))   return cmd_sensor(ac, av);
    if (!strcmp(c, "mri"))      return cmd_mri(ac, av);
    if (!strcmp(c, "fmri"))     return cmd_fmri(ac, av);
    if (!strcmp(c, "topo"))     return cmd_topo(ac, av);
    if (!strcmp(c, "ct"))       return cmd_ct(ac, av);
    if (!strcmp(c, "blood"))    return cmd_blood(ac, av);
    if (!strcmp(c, "dna"))      return cmd_dna(ac, av);
    if (!strcmp(c, "rna"))      return cmd_rna(ac, av);
    if (!strcmp(c, "pipeline") || !strcmp(c, "all")) return cmd_pipeline(ac, av);
    if (!strcmp(c, "help") || !strcmp(c, "-h") || !strcmp(c, "--help")) {
        usage(argv[0]); return 0;
    }
    fprintf(stderr, "unknown command: %s\n", c);
    usage(argv[0]);
    return 1;
}
