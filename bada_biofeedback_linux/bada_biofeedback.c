/*
 * bada_biofeedback.c — Linux native port of the "Bada Biofeedback" app.
 *
 * A faithful C port of the app's reproducible core:
 *   - BadaMath   : Lanczos gamma, Euler-Mascheroni constant, Shannon thermal
 *                  entropy, gamma-manifold session envelope
 *   - Bada DSL   : the tiny .bada preset interpreter (preset "id" { k = v })
 *   - ToneSynth  : the relaxation soundscape (carrier + breathing AM + warmth
 *                  low-pass + session envelope), rendered to a 16-bit WAV file
 *   - Body region glow + procedural EEG/ECG, drawn as an ANSI/ASCII screen
 *
 * IMPORTANT / 重要:
 *   These are relaxation soundscapes and aesthetic simulations only. They do
 *   NOT reproduce, deliver, measure, or substitute for any medication or any
 *   physical quantity of the human body. Follow your prescription.
 *
 * Build:  gcc -std=c11 -O2 -o bada_biofeedback bada_biofeedback.c -lm
 * Usage:  ./bada_biofeedback                 # interactive menu
 *         ./bada_biofeedback --list          # list presets
 *         ./bada_biofeedback <id> [seconds]  # render a preset's soundscape
 *         ./bada_biofeedback --presets FILE --wav OUT.wav --seconds N <id>
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <unistd.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ----------------------------------------------------------------------- */
/* BadaMath — reproducible mathematical core (port of BadaMath.kt)          */
/* ----------------------------------------------------------------------- */

#define EULER_GAMMA 0.5772156649015329
static const double LANCZOS_G = 7.0;
static const double LANCZOS_C[9] = {
    0.99999999999980993,   676.5203681218851,   -1259.1392167224028,
    771.32342877765313,   -176.61502916214059,   12.507343278686905,
    -0.13857109526572012,  9.9843695780195716e-6, 1.5056327351493116e-7
};

/* Gamma function via the Lanczos approximation (with reflection for x<0.5). */
static double bada_gamma(double x) {
    if (x < 0.5)
        return M_PI / (sin(M_PI * x) * bada_gamma(1.0 - x));
    double z = x - 1.0;
    double a = LANCZOS_C[0];
    double t = z + LANCZOS_G + 0.5;
    for (int i = 1; i < 9; ++i) a += LANCZOS_C[i] / (z + i);
    return sqrt(2.0 * M_PI) * pow(t, z + 0.5) * exp(-t) * a;
}

/* Normalised Gamma(k, theta) density — the "partial-integration manifold". */
static double gamma_envelope(double t, double k, double theta) {
    if (t <= 0.0) return 0.0;
    double num = pow(t, k - 1.0) * exp(-t / theta);
    double den = bada_gamma(k) * pow(theta, k);
    return num / den;
}

/* Shannon-style thermal entropy of a two-state balance p, in bits (peak 1). */
static double thermal_entropy(double p) {
    double q = p; if (q < 1e-6) q = 1e-6; if (q > 1.0 - 1e-6) q = 1.0 - 1e-6;
    double s = -q * log(q) - (1.0 - q) * log(1.0 - q);
    return s / log(2.0);
}

static double clamp01(double v) { return v < 0.0 ? 0.0 : (v > 1.0 ? 1.0 : v); }

/* Session amplitude envelope at time t (gamma manifold + entropy breathing). */
static double session_envelope(double t_seconds, double duration_seconds) {
    double u = clamp01(t_seconds / duration_seconds);
    double g = gamma_envelope(u * 4.0 + 1e-3, 2.0, 0.6);
    double g_norm = clamp01(g / 0.42);
    double breath = thermal_entropy(0.5 + 0.45 * sin(2.0 * M_PI * t_seconds / 12.0));
    return clamp01(0.6 * g_norm + 0.4 * breath);
}

/* Oscillator (port of ToneSynth.oscillator): sine | triangle | soft. */
static double oscillator(double phase, const char *waveform) {
    if (strcmp(waveform, "triangle") == 0) {
        double p = phase / (2.0 * M_PI);
        return 2.0 * fabs(2.0 * (p - floor(p + 0.5))) - 1.0;
    }
    if (strcmp(waveform, "soft") == 0) {
        double s = sin(phase);
        return 0.85 * s + 0.15 * sin(2.0 * phase) * 0.5;
    }
    return sin(phase);
}

/* ----------------------------------------------------------------------- */
/* Bada preset DSL (port of BadaPreset.kt + BadaInterpreter.kt)             */
/* ----------------------------------------------------------------------- */

typedef struct {
    char   id[64];
    char   label[128];
    char   feeling[128];
    char   region[32];
    char   waveform[16];
    char   color[16];     /* #RRGGBB */
    char   narration[256];
    double base_hz;
    double beat_hz;
    double warmth;
} Preset;

/* Strip a // line comment in place. */
static void strip_comment(char *s) {
    char *c = strstr(s, "//");
    if (c) *c = '\0';
}

/* Trim leading/trailing whitespace in place; returns pointer into s. */
static char *trim(char *s) {
    while (*s == ' ' || *s == '\t' || *s == '\r' || *s == '\n') s++;
    char *e = s + strlen(s);
    while (e > s && (e[-1] == ' ' || e[-1] == '\t' || e[-1] == '\r' || e[-1] == '\n')) *--e = '\0';
    return s;
}

/* Remove surrounding double quotes if present. */
static void unquote(char *s) {
    size_t n = strlen(s);
    if (n >= 2 && s[0] == '"' && s[n - 1] == '"') { memmove(s, s + 1, n - 2); s[n - 2] = '\0'; }
}

static void preset_defaults(Preset *p, const char *id) {
    memset(p, 0, sizeof(*p));
    snprintf(p->id, sizeof p->id, "%s", id);
    snprintf(p->label, sizeof p->label, "%s", id);
    snprintf(p->region, sizeof p->region, "limbic");
    snprintf(p->waveform, sizeof p->waveform, "sine");
    snprintf(p->color, sizeof p->color, "#7ec8e3");
    p->base_hz = 100.0; p->beat_hz = 7.0; p->warmth = 0.6;
}

static void preset_set(Preset *p, const char *key, char *val) {
    if      (!strcmp(key, "label"))     snprintf(p->label, sizeof p->label, "%s", val);
    else if (!strcmp(key, "feeling"))   snprintf(p->feeling, sizeof p->feeling, "%s", val);
    else if (!strcmp(key, "region"))    snprintf(p->region, sizeof p->region, "%s", val);
    else if (!strcmp(key, "waveform"))  snprintf(p->waveform, sizeof p->waveform, "%s", val);
    else if (!strcmp(key, "color"))     snprintf(p->color, sizeof p->color, "%s", val);
    else if (!strcmp(key, "narration")) snprintf(p->narration, sizeof p->narration, "%s", val);
    else if (!strcmp(key, "base_hz"))   p->base_hz = atof(val);
    else if (!strcmp(key, "beat_hz"))   p->beat_hz = atof(val);
    else if (!strcmp(key, "warmth"))    p->warmth = clamp01(atof(val));
}

/* Parse a whole .bada source buffer; returns count, fills out[] (<= max). */
static int bada_parse(char *src, Preset *out, int max) {
    int count = 0;
    char *save_line;
    for (char *line = strtok_r(src, "\n", &save_line);
         line && count < max;
         line = strtok_r(NULL, "\n", &save_line)) {
        strip_comment(line);
        char *t = trim(line);
        /* preset "id" { */
        char *kw = strstr(t, "preset");
        char *q1 = t ? strchr(t, '"') : NULL;
        if (kw == t && q1) {
            char *q2 = strchr(q1 + 1, '"');
            if (!q2) continue;
            *q2 = '\0';
            preset_defaults(&out[count], q1 + 1);
            /* read body until a line that is just "}" */
            for (char *bl = strtok_r(NULL, "\n", &save_line); bl; bl = strtok_r(NULL, "\n", &save_line)) {
                strip_comment(bl);
                char *bt = trim(bl);
                if (!strcmp(bt, "}")) break;
                char *eq = strchr(bt, '=');
                if (!eq) continue;
                *eq = '\0';
                char *key = trim(bt);
                char *val = trim(eq + 1);
                /* lowercase key */
                for (char *k = key; *k; ++k) if (*k >= 'A' && *k <= 'Z') *k += 32;
                unquote(val);
                preset_set(&out[count], key, val);
            }
            count++;
        }
    }
    return count;
}

/* Load presets from a file path. Returns count or -1 on error. */
static int load_presets(const char *path, Preset *out, int max) {
    FILE *f = fopen(path, "rb");
    if (!f) return -1;
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    if (sz < 0) { fclose(f); return -1; }
    char *buf = malloc((size_t)sz + 1);
    if (!buf) { fclose(f); return -1; }
    size_t r = fread(buf, 1, (size_t)sz, f); buf[r] = '\0'; fclose(f);
    int n = bada_parse(buf, out, max);
    free(buf);
    return n;
}

/* ----------------------------------------------------------------------- */
/* Soundscape rendering to a 16-bit stereo WAV (port of ToneSynth.kt)        */
/* ----------------------------------------------------------------------- */

static void put_u32(FILE *f, uint32_t v) { fputc(v & 255, f); fputc((v >> 8) & 255, f); fputc((v >> 16) & 255, f); fputc((v >> 24) & 255, f); }
static void put_u16(FILE *f, uint16_t v) { fputc(v & 255, f); fputc((v >> 8) & 255, f); }

static int render_wav(const Preset *p, double seconds, const char *path) {
    const int sr = 44100;
    long frames = (long)(seconds * sr);
    FILE *f = fopen(path, "wb");
    if (!f) return -1;

    /* WAV header (PCM 16-bit stereo) */
    uint32_t data_bytes = (uint32_t)(frames * 2 * 2);
    fwrite("RIFF", 1, 4, f); put_u32(f, 36 + data_bytes); fwrite("WAVE", 1, 4, f);
    fwrite("fmt ", 1, 4, f); put_u32(f, 16); put_u16(f, 1); put_u16(f, 2);
    put_u32(f, sr); put_u32(f, sr * 2 * 2); put_u16(f, 4); put_u16(f, 16);
    fwrite("data", 1, 4, f); put_u32(f, data_bytes);

    double phase_c = 0, phase_bl = 0, phase_br = 0, lpL = 0, lpR = 0;
    const double two_pi = 2.0 * M_PI;
    double beatL = p->beat_hz, beatR = p->beat_hz * 1.02;
    double alpha = 1.0 - p->warmth * 0.85; if (alpha < 0.08) alpha = 0.08; if (alpha > 1.0) alpha = 1.0;

    for (long i = 0; i < frames; ++i) {
        double tSec = (double)i / sr;
        double env = session_envelope(tSec, seconds);
        double carrier = oscillator(phase_c, p->waveform);
        double ampL = 0.5 + 0.5 * sin(phase_bl);
        double ampR = 0.5 + 0.5 * sin(phase_br);
        double rawL = carrier * ampL * env * 0.28;
        double rawR = carrier * ampR * env * 0.28;
        lpL += alpha * (rawL - lpL);
        lpR += alpha * (rawR - lpR);
        int16_t sL = (int16_t)(clamp01((lpL + 1.0) * 0.5) * 65535.0 - 32768.0);
        int16_t sR = (int16_t)(clamp01((lpR + 1.0) * 0.5) * 65535.0 - 32768.0);
        put_u16(f, (uint16_t)sL); put_u16(f, (uint16_t)sR);

        phase_c += two_pi * p->base_hz / sr; if (phase_c > two_pi) phase_c -= two_pi;
        phase_bl += two_pi * beatL / sr; if (phase_bl > two_pi) phase_bl -= two_pi;
        phase_br += two_pi * beatR / sr; if (phase_br > two_pi) phase_br -= two_pi;
    }
    fclose(f);
    return 0;
}

/* ----------------------------------------------------------------------- */
/* Terminal UI — ANSI colour, body-region glow, procedural EEG/ECG          */
/* ----------------------------------------------------------------------- */

static int g_color = 1; /* ANSI colour enabled */

/* Parse "#RRGGBB" into r,g,b. */
static void hex_rgb(const char *hex, int *r, int *g, int *b) {
    unsigned v = 0; const char *h = hex; if (*h == '#') h++;
    sscanf(h, "%6x", &v);
    *r = (v >> 16) & 255; *g = (v >> 8) & 255; *b = v & 255;
}
static void set_fg(const char *hex) {
    if (!g_color) return;
    int r, g, b; hex_rgb(hex, &r, &g, &b);
    printf("\x1b[38;2;%d;%d;%dm", r, g, b);
}
static void reset_color(void) { if (g_color) printf("\x1b[0m"); }

static const char *region_label(const char *key) {
    if (!strcmp(key, "brain"))         return "脳 (brain)";
    if (!strcmp(key, "limbic"))        return "大脳辺縁系 (limbic)";
    if (!strcmp(key, "basal_ganglia")) return "大脳基底核 (basal ganglia)";
    if (!strcmp(key, "chest"))         return "胸 (chest)";
    if (!strcmp(key, "heart"))         return "心臓 (heart)";
    if (!strcmp(key, "whole_body"))    return "全身 (whole body)";
    return key;
}

/* A simple front-facing body silhouette with the target region glowing. */
static void draw_body_glow(const Preset *p, double intensity) {
    /* normalised target y for each region (mirrors BodyRegion.kt) */
    double ny = 0.5;
    if (!strcmp(p->region, "brain"))           ny = 0.10;
    else if (!strcmp(p->region, "limbic"))     ny = 0.14;
    else if (!strcmp(p->region, "basal_ganglia")) ny = 0.13;
    else if (!strcmp(p->region, "chest"))      ny = 0.42;
    else if (!strcmp(p->region, "heart"))      ny = 0.40;
    else                                       ny = 0.55; /* whole_body */

    const char *body[] = {
        "        .-\"\"-.        ",
        "       /      \\       ",
        "       \\      /       ",
        "        '-..-'        ",
        "       /|    |\\       ",
        "      / |    | \\      ",
        "        |    |        ",
        "        |    |        ",
        "       /      \\       ",
        "      /        \\      ",
    };
    int rows = (int)(sizeof body / sizeof body[0]);
    int target = (int)(ny * rows + 0.5); if (target >= rows) target = rows - 1;
    for (int r = 0; r < rows; ++r) {
        double d = fabs(r - target);
        double glow = intensity * exp(-d * d / 2.0);
        if (g_color && glow > 0.12) { set_fg(p->color); }
        printf("    %s", body[r]);
        if (glow > 0.55)      printf("  <<< %s", region_label(p->region));
        else if (glow > 0.25) printf("  <<");
        reset_color();
        printf("\n");
    }
}

/* Render a value series as a one-line ASCII sparkline. */
static void sparkline(const double *v, int n) {
    static const char *ramp = " .:-=+*#%@";
    for (int i = 0; i < n; ++i) {
        double x = clamp01(v[i]);
        int idx = (int)(x * 8.999);
        putchar(ramp[idx]);
    }
}

/* Procedural EEG: theta/alpha band around the preset beat rate. */
static void draw_eeg(const Preset *p, int width) {
    double buf[256]; if (width > 256) width = 256;
    for (int i = 0; i < width; ++i) {
        double t = (double)i / 8.0;
        double w = 0.5
                 + 0.30 * sin(2.0 * M_PI * p->beat_hz * t / 10.0)
                 + 0.12 * sin(2.0 * M_PI * (p->beat_hz * 1.7) * t / 10.0 + 1.3)
                 + 0.06 * sin(2.0 * M_PI * 13.0 * t / 10.0 + 0.7);
        buf[i] = clamp01(w);
    }
    set_fg(p->color); printf("  EEG  "); reset_color();
    sparkline(buf, width); putchar('\n');
}

/* Procedural ECG: a synthetic PQRST beat repeated (peak-held per column). */
static void draw_ecg(const Preset *p, int width) {
    double buf[256]; if (width > 256) width = 256;
    double bpm = 58.0 + 16.0 * p->warmth;      /* calmer presets ~ steadier */
    double beat = 60.0 / bpm;                  /* seconds per beat */
    for (int i = 0; i < width; ++i) {
        double peak = 0.0;
        /* sub-sample each column so the narrow QRS spike is never missed */
        for (int s = 0; s < 8; ++s) {
            double t = ((double)i + s / 8.0) * 0.05;
            double ph = fmod(t, beat) / beat;            /* 0..1 within a beat */
            double y = 0.42;
            y += 0.06 * exp(-pow((ph - 0.15) / 0.03, 2.0));  /* P */
            y -= 0.10 * exp(-pow((ph - 0.27) / 0.012, 2.0)); /* Q */
            y += 0.55 * exp(-pow((ph - 0.30) / 0.012, 2.0)); /* R */
            y -= 0.14 * exp(-pow((ph - 0.33) / 0.014, 2.0)); /* S */
            y += 0.10 * exp(-pow((ph - 0.55) / 0.05, 2.0));  /* T */
            if (y > peak) peak = y;
        }
        buf[i] = clamp01(peak);
    }
    set_fg("#ff6b8a"); printf("  ECG  "); reset_color();
    sparkline(buf, width); putchar('\n');
}

/* Session amplitude envelope as a sparkline (the gamma-manifold curve). */
static void draw_envelope(const Preset *p, double seconds, int width) {
    double buf[256]; if (width > 256) width = 256;
    for (int i = 0; i < width; ++i)
        buf[i] = session_envelope((double)i / width * seconds, seconds);
    set_fg(p->color); printf("  ENV  "); reset_color();
    sparkline(buf, width); putchar('\n');
}

static void hr(void) { printf("  ----------------------------------------------------------------\n"); }

static void show_preset(const Preset *p, double seconds, const char *wav) {
    double peak_entropy = thermal_entropy(0.5); /* = 1.0, the glow peak */
    printf("\n");
    set_fg(p->color);
    printf("  ● %s", p->label);
    reset_color();
    printf("   [%s]\n", p->id);
    hr();
    printf("  feeling   : %s\n", p->feeling);
    printf("  region    : %s\n", region_label(p->region));
    printf("  carrier   : %.1f Hz   breathing beat : %.2f Hz\n", p->base_hz, p->beat_hz);
    printf("  waveform  : %s        warmth : %.2f\n", p->waveform, p->warmth);
    printf("  colour    : %s ", p->color);
    if (g_color) { int r,g,b; hex_rgb(p->color,&r,&g,&b); printf("\x1b[48;2;%d;%d;%dm      \x1b[0m", r,g,b); }
    printf("\n");
    if (p->narration[0]) printf("  narration : %s\n", p->narration);
    hr();
    draw_body_glow(p, peak_entropy);
    hr();
    draw_envelope(p, seconds, 56);
    draw_eeg(p, 56);
    draw_ecg(p, 56);
    hr();
    if (wav) {
        if (render_wav(p, seconds, wav) == 0) {
            printf("  ♪ soundscape rendered: %s  (%.0fs, 44.1kHz stereo WAV)\n", wav, seconds);
            if (access("/usr/bin/aplay", X_OK) == 0)
                printf("    play with:  aplay %s\n", wav);
            else if (access("/usr/bin/paplay", X_OK) == 0)
                printf("    play with:  paplay %s\n", wav);
            else
                printf("    play it with any audio player.\n");
        } else {
            printf("  (could not write %s)\n", wav);
        }
    }
    printf("\n");
    printf("  γ (Euler-Mascheroni) = %.16f   Γ(1/2) = %.6f (=√π)\n", EULER_GAMMA, bada_gamma(0.5));
    printf("  ※ リラクゼーション用シミュレーションです。薬効の再現・代替ではありません。\n");
    printf("\n");
}

static void list_presets(const Preset *ps, int n) {
    printf("\n  Bada Biofeedback — presets (%d)\n", n);
    hr();
    for (int i = 0; i < n; ++i) {
        printf("  %2d) ", i + 1);
        set_fg(ps[i].color);
        printf("%-14s", ps[i].id);
        reset_color();
        printf(" %-16s  %s\n", ps[i].label, ps[i].feeling);
    }
    hr();
}

/* ----------------------------------------------------------------------- */
/* main                                                                     */
/* ----------------------------------------------------------------------- */

static int find_preset(const Preset *ps, int n, const char *id) {
    for (int i = 0; i < n; ++i) if (!strcmp(ps[i].id, id) || !strcmp(ps[i].label, id)) return i;
    /* numeric index? */
    char *end; long k = strtol(id, &end, 10);
    if (*end == '\0' && k >= 1 && k <= n) return (int)(k - 1);
    return -1;
}

static const char *default_presets_path(const char *argv0, char *buf, size_t n) {
    const char *cands[4]; int c = 0;
    cands[c++] = "medications.bada";
    cands[c++] = "presets/medications.bada";
    cands[c++] = "bada_biofeedback_linux/medications.bada";
    /* alongside the executable */
    static char near[1024];
    snprintf(near, sizeof near, "%s", argv0);
    char *slash = strrchr(near, '/');
    if (slash) { snprintf(slash + 1, sizeof near - (slash + 1 - near), "medications.bada"); cands[c++] = near; }
    for (int i = 0; i < c; ++i) { FILE *f = fopen(cands[i], "rb"); if (f) { fclose(f); snprintf(buf, n, "%s", cands[i]); return buf; } }
    snprintf(buf, n, "medications.bada");
    return buf;
}

int main(int argc, char **argv) {
    const char *presets_path = NULL;
    const char *wav = "bada_soundscape.wav";
    double seconds = 20.0;
    const char *want = NULL;
    int do_list = 0;

    if (!isatty(1)) g_color = 0;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--list") || !strcmp(argv[i], "list")) do_list = 1;
        else if (!strcmp(argv[i], "--no-color")) g_color = 0;
        else if (!strcmp(argv[i], "--presets") && i + 1 < argc) presets_path = argv[++i];
        else if (!strcmp(argv[i], "--wav") && i + 1 < argc) wav = argv[++i];
        else if (!strcmp(argv[i], "--seconds") && i + 1 < argc) seconds = atof(argv[++i]);
        else if (!strcmp(argv[i], "play") && i + 1 < argc) want = argv[++i];
        else if (!strcmp(argv[i], "-h") || !strcmp(argv[i], "--help")) {
            printf("usage: %s [--list] [<id|index> [seconds]] [--presets FILE] [--wav OUT] [--seconds N]\n", argv[0]);
            return 0;
        }
        else if (argv[i][0] != '-') {
            if (!want) want = argv[i];
            else seconds = atof(argv[i]);    /* second positional = seconds */
        }
    }

    char pathbuf[1024];
    if (!presets_path) presets_path = default_presets_path(argv[0], pathbuf, sizeof pathbuf);

    static Preset ps[128];
    int n = load_presets(presets_path, ps, 128);
    if (n < 0) { fprintf(stderr, "error: cannot read presets file '%s'\n", presets_path); return 1; }
    if (n == 0) { fprintf(stderr, "error: no presets found in '%s'\n", presets_path); return 1; }

    printf("\x1b[1m  Bada Biofeedback (Linux)\x1b[0m — relaxation soundscape simulator\n");
    printf("  presets: %s  (%d loaded)\n", presets_path, n);

    if (do_list) { list_presets(ps, n); return 0; }

    if (want) {
        int idx = find_preset(ps, n, want);
        if (idx < 0) { fprintf(stderr, "error: preset '%s' not found (try --list)\n", want); return 1; }
        show_preset(&ps[idx], seconds, wav);
        return 0;
    }

    /* interactive menu */
    if (!isatty(0)) { list_presets(ps, n); printf("  (run `%s <id>` to render a soundscape)\n", argv[0]); return 0; }
    for (;;) {
        list_presets(ps, n);
        printf("  select 1-%d (q to quit): ", n);
        fflush(stdout);
        char line[64];
        if (!fgets(line, sizeof line, stdin)) break;
        char *t = trim(line);
        if (t[0] == 'q' || t[0] == 'Q' || t[0] == '\0') break;
        int idx = find_preset(ps, n, t);
        if (idx < 0) { printf("  ? unknown selection\n"); continue; }
        show_preset(&ps[idx], seconds, wav);
        printf("  press Enter to continue...");
        fflush(stdout);
        if (!fgets(line, sizeof line, stdin)) break;
    }
    printf("  またね。\n");
    return 0;
}
