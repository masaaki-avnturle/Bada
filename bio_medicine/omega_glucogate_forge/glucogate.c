/*
 * glucogate.c — Ω-GlucoGate Forge (ネイティブ C 版)
 * bio_medicine/omega_glucogate_forge — Masaaki Yamaguchi / Bada
 *
 * 形態形成場(Γ大域的部分積分多様体 e^{-x log x} で変調した Gray–Scott 反応拡散場)から
 * 「ドーパミン作動性 糖取り込み薬剤」を決定論的に鍛造し、経口PK → D2受容体占有 →
 * インスリン感受性/GLUT4 トランスロケーション → 細胞内への糖取り込み
 *     U_cell = Vmax * M * G/(Km + G)
 * を dt = 1 min で積分する。www/index.html および glucogate_sim.py と同一のモデル。
 *
 * ⚠ 概念シミュレーション・非医療。実在の医薬品を設計/製造/評価するものではなく、
 *    出力を医療判断に用いることはできません。
 *
 * build: gcc -std=c99 -O2 -o glucogate glucogate.c -lm
 * usage: ./glucogate [--preset t2d|t2d-severe|healthy] [--days N] [--dose MG]
 *                    [--doses-per-day N] [--first-dose H] [--auto-forge N]
 *                    [--feed F] [--kill K] [--kappa X] [--seed N]
 *                    [--grid N] [--rd-steps N] [--csv FILE]
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------ 共通 */
static double clampd(double v, double lo, double hi) { return v < lo ? lo : (v > hi ? hi : v); }

/* Γ大域的部分積分多様体の核 e^{-x log x} */
static double gamma_kernel(double x) { return x <= 1e-9 ? 1.0 : exp(-x * log(x)); }

/* ------------------------------------------------- ① 形態形成場 (製造装置) */
typedef struct { double occupancy, branching, symmetry, feature_length; } Desc;

static Desc morphogen_field(int n, double feed, double kill, double kappa,
                            unsigned seed, int iters)
{
    const double du = 0.16, dv = 0.08;
    int n2 = n * n, i, x, y, it;
    double *u = malloc(sizeof(double) * n2), *v = malloc(sizeof(double) * n2);
    double *nu = malloc(sizeof(double) * n2), *nv = malloc(sizeof(double) * n2);
    double *gu = malloc(sizeof(double) * n2), *gv = malloc(sizeof(double) * n2);
    double c = (n - 1) / 2.0;
    Desc d;
    unsigned st;

    for (i = 0; i < n2; i++) { u[i] = 1.0; v[i] = 0.0; }
    for (y = 0; y < n; y++) for (x = 0; x < n; x++) {
        double r = hypot(x - c, y - c) / (c + 1e-9);
        double g = 0.5 + 0.5 * gamma_kernel(kappa * r + 1e-6);
        gu[y * n + x] = du * g;
        gv[y * n + x] = dv * (1.0 - 0.35 * (g - 0.5));
    }
    /* 決定論的な種付け (線形合同法) */
    st = (unsigned)(seed * 1664525u + 1013904223u);
    {
        int rad = n / 16 + 1, s, seeds = n / 4 > 6 ? n / 4 : 6;
        if (rad < 2) rad = 2;
        for (s = 0; s < seeds; s++) {
            int sx, sy, dx, dy;
            st = st * 1664525u + 1013904223u; sx = (int)(n * 0.2 + (st / 4294967296.0) * n * 0.6);
            st = st * 1664525u + 1013904223u; sy = (int)(n * 0.2 + (st / 4294967296.0) * n * 0.6);
            for (dy = -rad; dy <= rad; dy++) for (dx = -rad; dx <= rad; dx++) {
                int ix, iy;
                if (dx * dx + dy * dy > rad * rad) continue;
                ix = ((sx + dx) % n + n) % n; iy = ((sy + dy) % n + n) % n;
                u[iy * n + ix] = 0.5; v[iy * n + ix] = 0.25;
            }
        }
    }
    for (it = 0; it < iters; it++) {
        for (y = 0; y < n; y++) {
            int yc = y * n, ym = ((y - 1 + n) % n) * n, yp = ((y + 1) % n) * n;
            for (x = 0; x < n; x++) {
                int ii = yc + x, xm = (x - 1 + n) % n, xp = (x + 1) % n;
                double lu = u[yc + xm] + u[yc + xp] + u[ym + x] + u[yp + x] - 4.0 * u[ii];
                double lv = v[yc + xm] + v[yc + xp] + v[ym + x] + v[yp + x] - 4.0 * v[ii];
                double uvv = u[ii] * v[ii] * v[ii];
                nu[ii] = clampd(u[ii] + gu[ii] * lu - uvv + feed * (1.0 - u[ii]), 0.0, 1.0);
                nv[ii] = clampd(v[ii] + gv[ii] * lv + uvv - (feed + kill) * v[ii], 0.0, 1.0);
            }
        }
        { double *t; t = u; u = nu; nu = t; t = v; v = nv; nv = t; }
    }
    /* 形態記述子 */
    {
        double occ = 0, g = 0, num = 0, den = 0, lam;
        long cross = 0;
        for (i = 0; i < n2; i++) if (v[i] > 0.20) occ += 1.0;
        for (y = 0; y < n; y++) {
            int yc = y * n, yp = ((y + 1) % n) * n, prev = v[yc] > 0.2;
            for (x = 0; x < n; x++) {
                int ii = yc + x;
                double a = v[ii], b = v[(n - 1 - y) * n + (n - 1 - x)];
                g += fabs(v[yc + (x + 1) % n] - v[ii]) + fabs(v[yp + x] - v[ii]);
                num += fabs(a - b); den += fabs(a) + fabs(b);
                if (x > 0) { int cur = v[ii] > 0.2; if (cur != prev) cross++; prev = cur; }
            }
        }
        lam = cross ? (2.0 * n * n) / (double)cross : (double)n;
        d.occupancy = occ / n2;
        d.branching = clampd(g / (2.0 * n2) * 12.0, 0.0, 1.0);
        d.symmetry = clampd(1.0 - num / (den + 1e-9), 0.0, 1.0);
        d.feature_length = clampd(lam / n, 0.0, 1.0);
    }
    free(u); free(v); free(nu); free(nv); free(gu); free(gv);
    return d;
}

/* ------------------------------------------------- ② 薬剤スペックの鍛造 */
typedef struct {
    char name[32];
    double pKi, Ki, MW, t_half_h, F_oral, ka, Vd_L, BBB, k_ins, k_glut4;
    Desc desc;
} Drug;

static Drug forge_drug(Desc d)
{
    Drug r;
    double occ = d.occupancy, br = d.branching, sym = d.symmetry, lam = d.feature_length;
    r.pKi = 6.40 + 2.80 * tanh(1.4 * br > 0 ? 1.4 * br : 0);
    r.BBB = clampd(0.10 + 0.85 * lam, 0.05, 0.95);
    r.F_oral = clampd(0.22 + 0.62 * sym, 0.10, 0.92);
    r.t_half_h = clampd(2.0 + 20.0 * occ, 1.0, 26.0);
    r.k_ins = clampd(0.20 + 1.60 * br * sym, 0.0, 2.0);
    r.k_glut4 = clampd(0.10 + 1.20 * occ * br, 0.0, 1.5);
    r.MW = 280.0 + 240.0 * occ;
    r.Vd_L = 45.0 + 190.0 * r.BBB;
    r.ka = 0.010 + 0.030 * sym;
    r.Ki = pow(10.0, -r.pKi) * r.MW * 1e6;
    r.desc = d;
    snprintf(r.name, sizeof(r.name), "O-GG-%04X-%04X",
             (unsigned)((long)(r.pKi * 1000 + r.t_half_h * 37 + r.BBB * 911) % 65536),
             (unsigned)((long)(r.k_ins * 3313 + r.k_glut4 * 7717 + r.F_oral * 1543) % 65536));
    return r;
}

static Drug no_drug(void)
{
    Drug r;
    memset(&r, 0, sizeof r);
    snprintf(r.name, sizeof(r.name), "(no drug)");
    r.pKi = 9; r.Ki = 1e9; r.MW = 300; r.t_half_h = 6; r.F_oral = 0;
    r.ka = 0.02; r.Vd_L = 100; r.BBB = 0; r.k_ins = 0; r.k_glut4 = 0;
    return r;
}

/* ------------------------------------------------- ③ 生理モデル (PK/PD) */
typedef struct { double Si, beta, kEGP, Gb, Ib; const char *key, *label; } Preset;
static const Preset PRESETS[] = {
    { 0.00085, 0.35, 0.35, 152.0, 15.0, "t2d",        "2型糖尿病(中等症)" },
    { 0.00050, 0.20, 0.22, 196.0, 13.0, "t2d-severe", "2型糖尿病(重症・高血糖)" },
    { 0.00220, 1.00, 0.75,  92.0,  8.0, "healthy",    "非糖尿病(対照)" }
};
#define NPRESET ((int)(sizeof(PRESETS)/sizeof(PRESETS[0])))

#define VG        112.0    /* 血糖分布容積 dL (体重 70 kg) */
#define KM         90.0    /* GLUT4 の見かけ Km (mg/dL) */
#define U_II       70.0    /* インスリン非依存の消費 mg/min */
#define EGP0      145.0    /* 基礎肝糖放出 mg/min */
#define P2          0.028
#define IZ          2.0
#define N_CLR       0.14
#define I_MIN       1.5
#define KD_X        0.035
#define TAU_M      12.0
#define M_MIN       0.05
#define M_MAX       1.0
#define SEC_GAIN    6.0
#define KEO         0.02
#define TAU_SENS 2880.0
#define ALPHA_HEP   0.22
#define IOTA_ISLET  0.45
#define TAU_MEAL   45.0
#define F_MEAL      0.90

typedef struct {
    double mean_glucose, peak_glucose, eA1c, TIR, TAR, TBR;
    double uptake_g_per_day, cell_clearance, mean_GLUT4;
    double peak_occ_central, mean_occ_peripheral, side_effect;
} Result;

static double m_target(double drive)
{
    double d = drive > 0 ? drive * drive : 0.0;
    return M_MIN + (M_MAX - M_MIN) * d / (d + KD_X * KD_X);
}

typedef struct {
    int preset, days, ndose, treated;
    double dose, first_h, meals[3][2];
    const char *csv;
} Opts;

static Result simulate(Drug dr, Opts o)
{
    const Preset p = PRESETS[o.preset];
    double Xb = p.Si * (p.Ib - IZ), Mb = m_target(Xb);
    double Vmax = (EGP0 - U_II) / (Mb * p.Gb / (KM + p.Gb));
    double sec_basal = N_CLR * (p.Ib - I_MIN);
    double ke = log(2.0) / (dr.t_half_h * 60.0), vd_ml = dr.Vd_L * 1000.0;
    double G = p.Gb, I = p.Ib, X = Xb, M = Mb;
    double Agut = 0, Ac = 0, Ce = 0, Psi = 0;
    long t, total = (long)o.days * 1440, day0 = total - 1440;
    long tir = 0, tar = 0, tbr = 0;
    double gsum = 0, up = 0, msum = 0, clr = 0, occCpeak = 0, occPsum = 0, gpeak = 0;
    Result r;
    FILE *fp = NULL;

    if (o.csv) {
        fp = fopen(o.csv, "w");
        if (fp) fprintf(fp, "t_h,glucose_mg_dL,insulin_uU_mL,GLUT4_membrane,"
                            "uptake_mg_min,plasma_drug_ng_mL,occ_central,occ_peripheral\n");
    }
    for (t = 0; t < total; t++) {
        int i;
        double abs_rate, Cp, occP, occC, Ra = 0, tod = (double)(t % 1440), egp, U, sec, lo, SiEff, Xd;
        if (o.treated && o.dose > 0)
            for (i = 0; i < o.ndose; i++)
                if (t % 1440 == (long)((o.first_h + i * (24.0 / o.ndose)) * 60.0 + 0.5))
                    Agut += o.dose;
        abs_rate = dr.ka * Agut;
        Agut -= abs_rate;
        Ac += dr.F_oral * abs_rate - ke * Ac;
        Cp = Ac / vd_ml * 1e6;                 /* mg/mL → ng/mL */
        occP = Cp / (Cp + dr.Ki);
        Ce += KEO * (dr.BBB * Cp - Ce);
        occC = Ce / (Ce + dr.Ki);
        Psi += (occC - Psi) / TAU_SENS;

        for (i = 0; i < 3; i++) {
            double dtm = tod - o.meals[i][0] * 60.0;
            if (dtm < 0) dtm += 1440.0;
            if (dtm < 600.0)
                Ra += o.meals[i][1] * 1000.0 * F_MEAL * (dtm / (TAU_MEAL * TAU_MEAL))
                      * exp(-dtm / TAU_MEAL);
        }
        egp = EGP0 * (1.0 - ALPHA_HEP * Psi) / (1.0 + p.kEGP * (I - p.Ib) / p.Ib);
        egp *= 1.0 + 2.5 * (85.0 - G > 0 ? 85.0 - G : 0.0) / 85.0;
        egp = clampd(egp, 0.15 * EGP0, 2.2 * EGP0);

        U = Vmax * M * G / (KM + G);            /* ← 血中の糖が細胞内へ */
        G += (Ra + egp - U_II - U) / VG;
        if (G < 15.0) G = 15.0;

        sec = sec_basal * (1.0 + p.beta * SEC_GAIN * (G > p.Gb ? G - p.Gb : 0.0) / 100.0);
        lo = clampd((G - 40.0) / 30.0, 0.0, 1.0);
        sec *= lo * (1.0 - IOTA_ISLET * occP);
        I += sec - N_CLR * (I - I_MIN);
        if (I < I_MIN) I = I_MIN;

        SiEff = p.Si * (1.0 + dr.k_ins * Psi);
        X += P2 * (SiEff * (I - IZ) - X);
        if (X < 0) X = 0;
        Xd = dr.k_glut4 * 0.020 * occP;
        M = clampd(M + (m_target(X + Xd) - M) / TAU_M, M_MIN, M_MAX);

        if (t >= day0) {
            gsum += G; up += U; msum += M; clr += U / G; occPsum += occP;
            if (G >= 70.0 && G <= 180.0) tir++; else if (G > 180.0) tar++; else tbr++;
            if (occC > occCpeak) occCpeak = occC;
            if (G > gpeak) gpeak = G;
            if (fp && (t - day0) % 5 == 0)
                fprintf(fp, "%.4f,%.3f,%.4f,%.5f,%.4f,%.5f,%.5f,%.5f\n",
                        (t - day0) / 60.0, G, I, M, U, Cp, occC, occP);
        }
    }
    if (fp) fclose(fp);
    r.mean_glucose = gsum / 1440.0;
    r.peak_glucose = gpeak;
    r.eA1c = (r.mean_glucose + 46.7) / 28.7;
    r.TIR = 100.0 * tir / 1440.0;
    r.TAR = 100.0 * tar / 1440.0;
    r.TBR = 100.0 * tbr / 1440.0;
    r.uptake_g_per_day = up / 1000.0;
    r.cell_clearance = clr / 1440.0;
    r.mean_GLUT4 = msum / 1440.0;
    r.peak_occ_central = occCpeak;
    r.mean_occ_peripheral = occPsum / 1440.0;
    r.side_effect = clampd(100.0 * (0.55 * pow(occCpeak, 1.2) + 0.30 * (occPsum / 1440.0))
                           + 1.5 * r.TBR, 0.0, 100.0);
    return r;
}

/* 製造装置の目的関数 (無投薬 base に対する改善度) */
static double forge_score(Result r, Result base)
{
    double dclr = 100.0 * (r.cell_clearance / (base.cell_clearance + 1e-9) - 1.0);
    return (base.mean_glucose - r.mean_glucose) + 0.50 * (r.TIR - base.TIR)
           + 0.30 * dclr - 2.0 * r.TBR - 0.30 * r.side_effect;
}

/* ------------------------------------------------------------------ CLI */
static void print_result(const char *tag, Result r)
{
    printf("  %-12s 平均血糖 %6.1f | 最高 %6.1f mg/dL | eA1c %4.1f%% | TIR %5.1f%% | 低血糖 %4.1f%%\n",
           tag, r.mean_glucose, r.peak_glucose, r.eA1c, r.TIR, r.TBR);
    printf("  %-12s 細胞内取込 %6.1f g/日 | 細胞内クリアランス %5.3f dL/min | GLUT4膜提示 %4.1f%%\n",
           "", r.uptake_g_per_day, r.cell_clearance, 100.0 * r.mean_GLUT4);
}

int main(int argc, char **argv)
{
    Opts o;
    int i, grid = 48, rd_steps = 500, auto_forge = 0, pi = 0;
    unsigned seed = 7;
    double feed = 0.037, kill = 0.060, kappa = 1.0;
    Drug drug;
    Result base, treat;

    o.preset = 0; o.days = 7; o.ndose = 1; o.dose = 4.8; o.first_h = 7.0; o.treated = 1;
    o.csv = NULL;
    o.meals[0][0] = 7;  o.meals[0][1] = 60;
    o.meals[1][0] = 12; o.meals[1][1] = 75;
    o.meals[2][0] = 19; o.meals[2][1] = 70;

    for (i = 1; i < argc; i++) {
        const char *a = argv[i];
        const char *nx = (i + 1 < argc) ? argv[i + 1] : NULL;
        if (!strcmp(a, "--preset") && nx) {
            int j; for (j = 0; j < NPRESET; j++) if (!strcmp(nx, PRESETS[j].key)) pi = j;
            o.preset = pi; i++;
        }
        else if (!strcmp(a, "--days") && nx) { o.days = atoi(nx); i++; }
        else if (!strcmp(a, "--dose") && nx) { o.dose = atof(nx); i++; }
        else if (!strcmp(a, "--doses-per-day") && nx) { o.ndose = atoi(nx); i++; }
        else if (!strcmp(a, "--first-dose") && nx) { o.first_h = atof(nx); i++; }
        else if (!strcmp(a, "--feed") && nx) { feed = atof(nx); i++; }
        else if (!strcmp(a, "--kill") && nx) { kill = atof(nx); i++; }
        else if (!strcmp(a, "--kappa") && nx) { kappa = atof(nx); i++; }
        else if (!strcmp(a, "--seed") && nx) { seed = (unsigned)atoi(nx); i++; }
        else if (!strcmp(a, "--grid") && nx) { grid = atoi(nx); i++; }
        else if (!strcmp(a, "--rd-steps") && nx) { rd_steps = atoi(nx); i++; }
        else if (!strcmp(a, "--auto-forge") && nx) { auto_forge = atoi(nx); i++; }
        else if (!strcmp(a, "--csv") && nx) { o.csv = nx; i++; }
        else if (!strcmp(a, "--help") || !strcmp(a, "-h")) {
            printf("usage: %s [--preset t2d|t2d-severe|healthy] [--days N] [--dose MG]\n"
                   "          [--doses-per-day N] [--first-dose H] [--auto-forge N]\n"
                   "          [--feed F] [--kill K] [--kappa X] [--seed N]\n"
                   "          [--grid N] [--rd-steps N] [--csv FILE]\n", argv[0]);
            return 0;
        }
        else { fprintf(stderr, "unknown option: %s (--help)\n", a); return 2; }
    }
    if (o.days < 1) o.days = 1;
    if (o.ndose < 1) o.ndose = 1;

    printf("Ω-GlucoGate Forge (C) — 形態形成場 薬剤製造装置 (概念シミュレーション・非医療)\n");
    printf("病態: %s / %d 日投与 / %.2f mg × %d 回/日\n",
           PRESETS[o.preset].label, o.days, o.dose, o.ndose);

    if (auto_forge > 0) {
        Opts so = o;
        Result ctrl;
        double best_s = -1e18;
        unsigned st = seed;
        Drug best;
        so.days = o.days < 4 ? o.days : 4;
        so.treated = 0;
        ctrl = simulate(no_drug(), so);
        so.treated = 1;
        best = forge_drug(morphogen_field(32, feed, kill, kappa, seed, 400));
        printf("\n[自動鍛造] %d 候補を探索中...\n", auto_forge);
        for (i = 0; i < auto_forge; i++) {
            double f, k, kp, s;
            Drug d;
            Result r;
            st = st * 1103515245u + 12345u; f = 0.026 + (st % 1000) / 1000.0 * 0.032;
            st = st * 1103515245u + 12345u; k = 0.055 + (st % 1000) / 1000.0 * 0.010;
            st = st * 1103515245u + 12345u; kp = 0.2 + (st % 1000) / 1000.0 * 2.4;
            d = forge_drug(morphogen_field(32, f, k, kp, seed + i, 400));
            r = simulate(d, so);
            s = forge_score(r, ctrl);
            printf("   候補%2d  F=%.3f k=%.3f κ=%.2f → pKi %.2f / t½ %.1fh / BBB %.2f / 得点 %.1f\n",
                   i + 1, f, k, kp, d.pKi, d.t_half_h, d.BBB, s);
            if (s > best_s) { best_s = s; best = d; }
        }
        drug = best;
    } else {
        drug = forge_drug(morphogen_field(grid, feed, kill, kappa, seed, rd_steps));
    }

    printf("\n[鍛造された薬剤] %s\n", drug.name);
    printf("  D2 親和性 pKi = %.2f (Ki %.2f ng/mL) / 分子量 %.0f\n", drug.pKi, drug.Ki, drug.MW);
    printf("  半減期 %.1f h / 経口F %.0f%% / Vd %.0f L / BBB透過指数 %.2f\n",
           drug.t_half_h, 100 * drug.F_oral, drug.Vd_L, drug.BBB);
    printf("  κ_インスリン感受性 %.2f / κ_GLUT4動員 %.2f\n", drug.k_ins, drug.k_glut4);
    printf("  形態記述子: occupancy=%.3f, branching=%.3f, symmetry=%.3f, feature_length=%.3f\n",
           drug.desc.occupancy, drug.desc.branching, drug.desc.symmetry, drug.desc.feature_length);

    {
        Opts co = o;
        co.treated = 0; co.csv = NULL;
        base = simulate(no_drug(), co);
    }
    treat = simulate(drug, o);
    printf("\n[最終24時間の指標]\n");
    print_result("対照(無投薬)", base);
    print_result("投薬", treat);
    printf("  Δ平均血糖 %+.1f mg/dL / ΔTIR %+.1f pt / Δ細胞内クリアランス %+.1f %% / 副作用指標 %.0f/100\n",
           treat.mean_glucose - base.mean_glucose, treat.TIR - base.TIR,
           100.0 * (treat.cell_clearance / base.cell_clearance - 1.0), treat.side_effect);
    printf("  中枢D2占有 ピーク %.0f%% / 末梢(膵島)D2占有 平均 %.0f%% / 製造装置スコア %.1f\n",
           100 * treat.peak_occ_central, 100 * treat.mean_occ_peripheral,
           forge_score(treat, base));
    if (o.csv) printf("\nCSV を書き出しました: %s\n", o.csv);
    printf("\n⚠ 本結果は概念モデルの出力であり、医療上の判断には使用できません。\n");
    return 0;
}
