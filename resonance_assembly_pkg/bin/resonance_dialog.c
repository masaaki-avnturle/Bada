/* resonance_dialog.c — the dialog-box application.
 *
 * A terminal "dialog box" UI over the Bada resonance engine. It lets you:
 *   1. enter / edit the target structure data (field by field — the data can
 *      be corrected back and forth, 交互に修正, as many rounds as you like);
 *   2. run the resonance + fracture-mechanics durability diagnosis;
 *   3. read the AGM (相加相乗平均) assembly-precision adjustment;
 *   4. apply the special-relativity error correction of the complex rotating
 *      body and feed the corrected frequency back into the diagnosis;
 *   5. inspect the Galois / global-differential-manifold (Bada operator) view.
 *
 * Run interactively, or with `--demo` for a non-interactive walkthrough.
 *
 * Build:  make         (produces bin/resonance_dialog)
 * Run:    ./bin/resonance_dialog
 *         ./bin/resonance_dialog --demo
 */
#include "bada_resonance.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ---- terminal dialog-box drawing (UTF-8 box characters) --------------- */

#define BOX_W 70

static void box_top(void)    { printf("┌"); for (int i=0;i<BOX_W-2;i++) printf("─"); printf("┐\n"); }
static void box_bot(void)    { printf("└"); for (int i=0;i<BOX_W-2;i++) printf("─"); printf("┘\n"); }
static void box_sep(void)    { printf("├"); for (int i=0;i<BOX_W-2;i++) printf("─"); printf("┤\n"); }

/* print one boxed line, padded to width (assumes ASCII content width) */
static void box_line(const char *s)
{
    int n = (int)strlen(s);
    printf("│ %s", s);
    for (int i = n; i < BOX_W - 4; i++) putchar(' ');
    printf(" │\n");
}

static void box_titled(const char *title)
{
    box_top();
    char buf[BOX_W * 4];
    snprintf(buf, sizeof buf, "%s", title);
    box_line(buf);
    box_sep();
}

/* ---- input helpers (EOF-safe; keep current value on blank / EOF) ------ */

static int read_line(char *buf, size_t n)
{
    if (!fgets(buf, (int)n, stdin)) return 0;     /* EOF */
    size_t l = strlen(buf);
    if (l && buf[l-1] == '\n') buf[l-1] = '\0';
    return 1;
}

static void prompt_double(const char *label, double *value)
{
    char buf[128];
    printf("  %-46s [%g]: ", label, *value);
    fflush(stdout);
    if (!read_line(buf, sizeof buf)) { printf("\n"); return; }
    if (buf[0] == '\0') return;                   /* blank -> keep value */
    char *end; double v = strtod(buf, &end);
    if (end != buf) *value = v;
}

static void prompt_int(const char *label, int *value)
{
    char buf[128];
    printf("  %-46s [%d]: ", label, *value);
    fflush(stdout);
    if (!read_line(buf, sizeof buf)) { printf("\n"); return; }
    if (buf[0] == '\0') return;
    char *end; long v = strtol(buf, &end, 10);
    if (end != buf) *value = (int)v;
}

static void prompt_string(const char *label, char *value, size_t n)
{
    char buf[256];
    printf("  %-46s [%s]: ", label, value);
    fflush(stdout);
    if (!read_line(buf, sizeof buf)) { printf("\n"); return; }
    if (buf[0] == '\0') return;
    snprintf(value, n, "%.*s", (int)(n - 1), buf);
}

/* ---- views ------------------------------------------------------------ */

static void view_data(const BadaTarget *t)
{
    char b[128];
    box_titled("対象データ — Target structure data");
    snprintf(b, sizeof b, "name        : %s", t->name);              box_line(b);
    snprintf(b, sizeof b, "storeys  N  : %d", t->storeys);           box_line(b);
    snprintf(b, sizeof b, "mass     m  : %.3g kg/storey", t->mass);  box_line(b);
    snprintf(b, sizeof b, "stiffness k : %.3g N/m", t->stiffness);   box_line(b);
    snprintf(b, sizeof b, "damping  z  : %.4g", t->damping);         box_line(b);
    snprintf(b, sizeof b, "excitation  : %.4g Hz", t->exc_freq);     box_line(b);
    snprintf(b, sizeof b, "crack    a  : %.4g m", t->crack_a);       box_line(b);
    snprintf(b, sizeof b, "geom     Y  : %.3g", t->Y_factor);        box_line(b);
    snprintf(b, sizeof b, "sigma_stat  : %.4g MPa", t->sigma_static);box_line(b);
    snprintf(b, sizeof b, "K_IC        : %.4g MPa*sqrt(m)", t->Kic); box_line(b);
    snprintf(b, sizeof b, "rot radius R: %.3g m", t->rot_radius);    box_line(b);
    snprintf(b, sizeof b, "rot Omega   : %.5g rad/s", t->rot_omega); box_line(b);
    snprintf(b, sizeof b, "member dim h: %.4g mm", t->member_dim);   box_line(b);
    snprintf(b, sizeof b, "target r*   : %.3g", t->target_ratio);    box_line(b);
    box_bot();
}

static void edit_data(BadaTarget *t)
{
    printf("\n  [編集] Enter = keep current value, ^D = stop editing.\n\n");
    prompt_string("Name",                         t->name, sizeof t->name);
    prompt_int   ("Storeys N",                    &t->storeys);
    prompt_double("Modal storey mass m (kg)",     &t->mass);
    prompt_double("Storey stiffness k (N/m)",     &t->stiffness);
    prompt_double("Damping ratio zeta",           &t->damping);
    prompt_double("Excitation frequency (Hz)",    &t->exc_freq);
    prompt_double("Crack/flaw size a (m)",        &t->crack_a);
    prompt_double("Geometry factor Y",            &t->Y_factor);
    prompt_double("Static stress sigma (MPa)",    &t->sigma_static);
    prompt_double("Fracture toughness K_IC",      &t->Kic);
    prompt_double("Rotation radius R (m)",        &t->rot_radius);
    prompt_double("Rotation Omega (rad/s)",       &t->rot_omega);
    prompt_double("Governing member dim h (mm)",  &t->member_dim);
    prompt_double("Safe detuning ratio r*",       &t->target_ratio);
    printf("\n  データを更新しました — data updated.\n");
}

static void view_diagnosis(const BadaTarget *t, const BadaDiagnosis *d)
{
    char b[128];

    box_titled("1. 共鳴診断 — Resonance diagnosis");
    snprintf(b, sizeof b, "fundamental f1     : %.4f Hz", d->spectrum.f[0]);  box_line(b);
    snprintf(b, sizeof b, "dangerous mode     : #%d @ %.4f Hz",
             d->mode_index + 1, d->f_mode);                                   box_line(b);
    snprintf(b, sizeof b, "corrected exc f    : %.6f Hz (proper)", d->rel.f_proper); box_line(b);
    snprintf(b, sizeof b, "frequency ratio r  : %.4f  (r* target %.2f)",
             d->ratio, t->target_ratio);                                      box_line(b);
    snprintf(b, sizeof b, "amplification DAF  : %.3f x", d->daf);             box_line(b);
    snprintf(b, sizeof b, "dynamic stress     : %.2f MPa", d->sigma_dyn);     box_line(b);
    box_bot();

    box_titled("2. 破壊力学・耐久診断 — Fracture / durability");
    snprintf(b, sizeof b, "stress intensity K : %.3f MPa*sqrt(m)", d->Ki);    box_line(b);
    snprintf(b, sizeof b, "critical crack ac  : %.5f m", d->a_crit);          box_line(b);
    snprintf(b, sizeof b, "safety factor      : %.3f", d->safety_factor);     box_line(b);
    snprintf(b, sizeof b, "verdict            : %s",
             d->safe ? "SAFE — 安全" : "RESONANCE RISK — 要調整");            box_line(b);
    box_bot();

    box_titled("3. 組立精度調整 (相加相乗平均/AGM) — Assembly tuning");
    snprintf(b, sizeof b, "k current          : %.4g N/m", t->stiffness);     box_line(b);
    snprintf(b, sizeof b, "k target (r*)      : %.4g N/m", d->k_target);      box_line(b);
    snprintf(b, sizeof b, "k arith mean       : %.4g N/m", d->k_arith);       box_line(b);
    snprintf(b, sizeof b, "k geom  mean       : %.4g N/m", d->k_geom);        box_line(b);
    snprintf(b, sizeof b, "k AGM  (blend)     : %.4g N/m", d->k_agm);         box_line(b);
    snprintf(b, sizeof b, "stiffness change   : %+.2f %%", d->dk_rel * 100.0);box_line(b);
    snprintf(b, sizeof b, "member precision dh: %+.4f mm (on h=%.0f mm)",
             d->dh_mm, t->member_dim);                                        box_line(b);
    box_bot();

    box_titled("4. 複素回転体・特殊相対性誤差修正 — Rel. correction");
    snprintf(b, sizeof b, "tangential v       : %.4g m/s", d->rel.v);         box_line(b);
    snprintf(b, sizeof b, "beta = v/c         : %.3e", d->rel.beta);          box_line(b);
    snprintf(b, sizeof b, "Lorentz gamma      : %.12f", d->rel.gamma);        box_line(b);
    snprintf(b, sizeof b, "freq correction df : %+.3e Hz", d->rel.df);        box_line(b);
    snprintf(b, sizeof b, "rotation phasor    : %.3f + %.3fi",
             creal(d->rel.phasor), cimag(d->rel.phasor));                     box_line(b);
    box_bot();

    box_titled("5. ガロワ群・大域微分多様体 — Galois / manifold gauge");
    snprintf(b, sizeof b, "sum  omega^2 (trace): %.4g  [Galois-invariant]", d->spectrum.sum_eig); box_line(b);
    snprintf(b, sizeof b, "prod omega^2 (det)  : %.4g  [Galois-invariant]", d->spectrum.prod_eig);box_line(b);
    snprintf(b, sizeof b, "manifold inv  Xi    : %.6f", d->xi_invariant);     box_line(b);
    {
        double complex L = bada_op_left(1.0, d->f_mode > 0 ? d->f_mode : 1.0);
        snprintf(b, sizeof b, "Bada <- (pi op)     : %.4f + %.4fi", creal(L), cimag(L)); box_line(b);
    }
    snprintf(b, sizeof b, "Bada -< (manifold)  : %.6f", bada_op_mid(d->mode_index + 2.0)); box_line(b);
    snprintf(b, sizeof b, "Bada >- (quantum)   : %.6f", bada_op_right(d->ratio > 0 ? d->ratio : 1.0)); box_line(b);
    box_bot();
}

/* ---- menu ------------------------------------------------------------- */

static void show_menu(void)
{
    printf("\n");
    box_titled("Bada Resonance — 共鳴振動・組立精度・破壊力学ダイアログ");
    box_line("1) データ表示        Show target data");
    box_line("2) データ編集        Edit data (alternately correctable)");
    box_line("3) 診断実行          Run full diagnosis");
    box_line("4) デフォルト読込    Load default target");
    box_line("0) 終了              Quit");
    box_bot();
    printf("  選択 / select> ");
    fflush(stdout);
}

static void run_demo(void)
{
    BadaTarget t = bada_default_target();
    printf("=== Bada Resonance — DEMO (non-interactive) ===\n\n");
    view_data(&t);
    printf("\n");
    BadaDiagnosis d = bada_diagnose(&t);
    view_diagnosis(&t, &d);

    /* Show the "alternately corrected data" idea: soften the structure so the
     * AGM adjustment drives it to the safe ratio, then re-diagnose. */
    printf("\n--- alternate correction: apply the AGM target stiffness ---\n\n");
    t.stiffness = d.k_agm;
    BadaDiagnosis d2 = bada_diagnose(&t);
    view_diagnosis(&t, &d2);
}

int main(int argc, char **argv)
{
    if (argc > 1 && strcmp(argv[1], "--demo") == 0) {
        run_demo();
        return 0;
    }

    BadaTarget t = bada_default_target();
    char buf[64];

    printf("Bada Resonance Dialog — type the menu number, Enter to confirm.\n");
    printf("(姉の許可済み / authorized durability-diagnosis tool)\n");

    for (;;) {
        show_menu();
        if (!read_line(buf, sizeof buf)) { printf("\n(EOF) bye.\n"); break; }
        if (buf[0] == '\0') continue;
        switch (buf[0]) {
            case '1': printf("\n"); view_data(&t); break;
            case '2': edit_data(&t); break;
            case '3': {
                printf("\n");
                BadaDiagnosis d = bada_diagnose(&t);
                view_diagnosis(&t, &d);
                /* offer the alternate-correction round */
                printf("\n  AGM目標剛性を適用して再診断? apply AGM stiffness & re-run? [y/N]: ");
                fflush(stdout);
                if (read_line(buf, sizeof buf) && (buf[0]=='y'||buf[0]=='Y')) {
                    t.stiffness = d.k_agm;
                    printf("\n");
                    BadaDiagnosis d2 = bada_diagnose(&t);
                    view_diagnosis(&t, &d2);
                }
                break;
            }
            case '4': t = bada_default_target(); printf("\n  デフォルト読込済み — defaults loaded.\n"); break;
            case '0': case 'q': printf("\nbye.\n"); return 0;
            default:  printf("\n  ?? unknown selection.\n");
        }
    }
    return 0;
}
