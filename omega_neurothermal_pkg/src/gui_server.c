/* gui_server.c — omega_neurothermal GUI (dependency-free web server)
 *
 * 既存の計算モジュール(gamma_thermal / basal_ganglia / sensors / imaging /
 * labanalysis)を再利用し、ブラウザ向けの GUI を提供する軽量 HTTP サーバ。
 *
 *  - 静的ファイル(web/ 配下の index.html / style.css / app.js)を配信
 *  - /api 配下の各エンドポイントで各装置機能を JSON 返却
 *  - すべての API レスポンスに「赤外線センサー + 温度計」の現在値を同梱し、
 *    GUI 上部のセンサーバーへ常時表示する（全アプリにセンサー付属の要件）
 *
 *  ビルド: make gui
 *  実行  : ./omega_neurothermal_gui [port] [webroot]
 *          既定 port=8080, webroot=./web  ->  ブラウザで http://localhost:8080
 *
 *  注意: 教育・可視化のためのローカル用シミュレーションサーバです。
 *        外部公開や臨床用途を意図していません。
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <ctype.h>
#include <stdint.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include "gamma_thermal.h"
#include "basal_ganglia.h"
#include "sensors.h"
#include "imaging.h"
#include "labanalysis.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ----------------------------------------------------------------- utils */

static const char *webroot = "./web";

/* very small URL query-string parameter getter (returns 1 if found) */
static int qparam(const char *query, const char *key, char *out, size_t outlen)
{
    if (!query) return 0;
    size_t klen = strlen(key);
    const char *p = query;
    while (p && *p) {
        if (strncmp(p, key, klen) == 0 && p[klen] == '=') {
            const char *v = p + klen + 1;
            size_t i = 0;
            while (*v && *v != '&' && i < outlen - 1) {
                if (*v == '%' && isxdigit((unsigned char)v[1]) && isxdigit((unsigned char)v[2])) {
                    char hex[3] = { v[1], v[2], 0 };
                    out[i++] = (char)strtol(hex, NULL, 16);
                    v += 3;
                } else if (*v == '+') {
                    out[i++] = ' '; v++;
                } else {
                    out[i++] = *v++;
                }
            }
            out[i] = 0;
            return 1;
        }
        p = strchr(p, '&');
        if (p) p++;
    }
    return 0;
}

static double qd(const char *query, const char *key, double dflt)
{
    char b[64];
    return qparam(query, key, b, sizeof(b)) ? atof(b) : dflt;
}

/* shared sensor snapshot derived from the gamma-thermal manifold */
typedef struct { double energy, core, ir, thermo, fused, fvar; } snapshot_t;

static snapshot_t make_snapshot(unsigned *seed)
{
    snapshot_t s;
    s.energy = om_thermal_energy(1.0, 5.0, 4000);     /* T' = INT Gamma' dx */
    s.core   = om_thermal_to_celsius(s.energy, 37.0, 1.5);
    s.ir     = ir_sensor_read(s.core, 0.97, 25.0, 0.1, seed);
    s.thermo = thermometer_read(s.core, s.core, 0.3, 0.05, seed);
    s.fused  = sensor_fuse(s.ir, 0.01, s.thermo, 0.0025, &s.fvar);
    return s;
}

/* append the common "sensors" JSON object */
static int json_sensors(char *b, int off, int cap, const snapshot_t *s)
{
    return off + snprintf(b + off, cap - off,
        "\"sensors\":{\"energy\":%.4f,\"core\":%.3f,\"ir\":%.3f,"
        "\"thermo\":%.3f,\"fused\":%.3f,\"sd\":%.3f}",
        s->energy, s->core, s->ir, s->thermo, s->fused, sqrt(s->fvar));
}

/* ----------------------------------------------------------- API handlers */
/* each writes a JSON body into b (capacity cap) and returns its length */

static int api_pipeline(char *b, int cap, const char *q, unsigned *seed)
{
    (void)q;
    snapshot_t s = make_snapshot(seed);
    bg_state_t st; memset(&st, 0, sizeof(st));
    bg_propagate(&st, fabs(s.energy), 0.6);
    blood_marker_t m[16];
    int n = blood_panel(m, 16, (s.fused - 37.0), seed);
    int abn = 0; for (int i = 0; i < n; i++) if (blood_flag(&m[i]) != 'N') abn++;
    dna_stats_t ds = dna_analyze("ATGGCCATTGTAATGGGCCGCTGAAAGG");
    char rna[256], aa[128];
    rna_transcribe("ATGGCCATTGTAATGGGCCGCTGA", rna, sizeof(rna));
    rna_translate(rna, aa, sizeof(aa));
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o,
        ",\"peripheral\":%.4f,\"hand\":%.4f,\"foot\":%.4f,"
        "\"markers\":%d,\"abnormal\":%d,"
        "\"dna_len\":%zu,\"gc\":%.3f,\"peptide\":\"%s\"}",
        bg_total_output(&st), st.segment[SEG_HAND], st.segment[SEG_FOOT],
        n, abn, ds.length, ds.gc_content, aa);
    return o;
}

static int api_gamma(char *b, int cap, const char *q, unsigned *seed)
{
    double lo = qd(q, "lo", 1.0), hi = qd(q, "hi", 5.0);
    int steps = (int)qd(q, "steps", 2000);
    snapshot_t s = make_snapshot(seed);
    double E = om_thermal_energy(lo, hi, steps);
    double Tc = om_thermal_to_celsius(E, 37.0, 1.5);
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o, ",\"lo\":%.4f,\"hi\":%.4f,\"steps\":%d,"
        "\"energy\":%.6f,\"temp\":%.3f,\"curve\":[", lo, hi, steps, E, Tc);
    int N = 60;
    for (int i = 0; i <= N; ++i) {
        double g = lo + (hi - lo) * i / N;
        o += snprintf(b + o, cap - o, "%s{\"g\":%.4f,\"gp\":%.5g}",
                      i ? "," : "", g, om_gamma_prime(g));
    }
    o += snprintf(b + o, cap - o, "]}");
    return o;
}

static int api_basal(char *b, int cap, const char *q, unsigned *seed)
{
    double E = qd(q, "E", om_thermal_energy(1.0, 5.0, 2000));
    double dop = qd(q, "dopamine", 0.6);
    snapshot_t s = make_snapshot(seed);
    bg_state_t st; memset(&st, 0, sizeof(st));
    bg_propagate(&st, fabs(E), dop);
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o, ",\"source\":%.4f,\"dopamine\":%.3f,"
        "\"total\":%.4f,\"nuclei\":[", E, dop, bg_total_output(&st));
    for (int i = 0; i < BG_NUCLEI_COUNT; ++i)
        o += snprintf(b + o, cap - o, "%s{\"name\":\"%s\",\"v\":%.4f}",
                      i ? "," : "", bg_nucleus_name(i), st.nucleus[i]);
    o += snprintf(b + o, cap - o, "],\"segments\":[");
    for (int i = 0; i < SEG_COUNT; ++i)
        o += snprintf(b + o, cap - o, "%s{\"name\":\"%s\",\"v\":%.4f}",
                      i ? "," : "", bg_segment_name(i), st.segment[i]);
    o += snprintf(b + o, cap - o, "]}");
    return o;
}

static int api_sensor(char *b, int cap, const char *q, unsigned *seed)
{
    double trueC = qd(q, "trueC", -999.0);
    double emiss = qd(q, "emiss", 0.97);
    snapshot_t base = make_snapshot(seed);
    if (trueC < -900.0) trueC = base.core;
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &base);
    o += snprintf(b + o, cap - o, ",\"trueC\":%.3f,\"emiss\":%.3f,\"series\":[", trueC, emiss);
    double prev = trueC;
    for (int k = 0; k < 16; ++k) {
        double ir = ir_sensor_read(trueC, emiss, 25.0, 0.15, seed);
        double th = thermometer_read(trueC, prev, 0.4, 0.08, seed);
        prev = th;
        double fv, f = sensor_fuse(ir, 0.0225, th, 0.0064, &fv);
        o += snprintf(b + o, cap - o, "%s{\"t\":%d,\"ir\":%.3f,\"th\":%.3f,\"f\":%.3f}",
                      k ? "," : "", k, ir, th, f);
    }
    o += snprintf(b + o, cap - o, "]}");
    return o;
}

static int api_mri(char *b, int cap, const char *q, unsigned *seed)
{
    char tissue[32]; if (!qparam(q, "tissue", tissue, sizeof(tissue))) strcpy(tissue, "gray");
    double t1, t2;
    snapshot_t s = make_snapshot(seed);
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    if (!mri_tissue_params(tissue, &t1, &t2)) {
        o += snprintf(b + o, cap - o, ",\"error\":\"unknown tissue\"}");
        return o;
    }
    o += snprintf(b + o, cap - o, ",\"tissue\":\"%s\",\"t1\":%.0f,\"t2\":%.0f,\"grid\":[",
                  tissue, t1, t2);
    double TR[] = {500, 1000, 2000, 3000, 4000};
    double TE[] = {15, 40, 80, 120};
    int first = 1;
    for (int a = 0; a < 5; ++a) for (int c = 0; c < 4; ++c) {
        o += snprintf(b + o, cap - o, "%s{\"tr\":%.0f,\"te\":%.0f,\"s\":%.4f}",
                      first ? "" : ",", TR[a], TE[c],
                      mri_spin_echo(1.0, t1, t2, TR[a], TE[c]));
        first = 0;
    }
    o += snprintf(b + o, cap - o, "]}");
    return o;
}

static int api_fmri(char *b, int cap, const char *q, unsigned *seed)
{
    (void)q;
    snapshot_t s = make_snapshot(seed);
    int n = 40; double dt = 1.0; double act[40] = {0}, bold[40];
    act[3]=act[4]=act[5]=1.0; act[18]=act[19]=act[20]=1.0;
    fmri_bold(act, bold, n, dt);
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o, ",\"series\":[");
    for (int i = 0; i < n; ++i)
        o += snprintf(b + o, cap - o, "%s{\"t\":%d,\"act\":%.0f,\"bold\":%.4f}",
                      i ? "," : "", i, act[i], bold[i]);
    o += snprintf(b + o, cap - o, "]}");
    return o;
}

static int api_topo(char *b, int cap, const char *q, unsigned *seed)
{
    (void)q;
    snapshot_t s = make_snapshot(seed);
    bg_state_t st; memset(&st, 0, sizeof(st));
    bg_propagate(&st, fabs(s.energy), 0.6);
    double src[4] = { st.nucleus[BG_CAUDATE], st.nucleus[BG_PUTAMEN],
                      st.nucleus[BG_GPI], st.nucleus[BG_STN] };
    double ang[4] = { 0.3, 1.9, 3.4, 5.0 };
    int E_N = 16; double pot[16];
    topography_project(src, ang, 4, pot, E_N);
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o, ",\"electrodes\":[");
    for (int i = 0; i < E_N; ++i)
        o += snprintf(b + o, cap - o, "%s{\"i\":%d,\"deg\":%.0f,\"v\":%.4f}",
                      i ? "," : "", i, 360.0 * i / E_N, pot[i]);
    o += snprintf(b + o, cap - o, "]}");
    return o;
}

static int api_ct(char *b, int cap, const char *q, unsigned *seed)
{
    (void)q;
    snapshot_t s = make_snapshot(seed);
    const char *layer[] = {"scalp/fat","skull/bone","gray matter",
                           "white matter","muscle","cortical bone(limb)"};
    double mu[]  = {0.020, 0.048, 0.021, 0.020, 0.023, 0.050};
    double thk[] = {0.6, 0.7, 2.0, 3.0, 4.0, 0.5};
    const double mu_water = 0.019; int L = 6;
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o, ",\"transmission\":%.6e,\"layers\":[",
                  ct_path_transmission(mu, thk, L));
    for (int i = 0; i < L; ++i)
        o += snprintf(b + o, cap - o,
            "%s{\"name\":\"%s\",\"mu\":%.4f,\"thk\":%.2f,\"hu\":%.1f}",
            i ? "," : "", layer[i], mu[i], thk[i], ct_hounsfield(mu[i], mu_water));
    o += snprintf(b + o, cap - o, "]}");
    return o;
}

static int api_blood(char *b, int cap, const char *q, unsigned *seed)
{
    snapshot_t s = make_snapshot(seed);
    double bias = qd(q, "bias", s.fused - 37.0);
    blood_marker_t m[16];
    int n = blood_panel(m, 16, bias, seed);
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o, ",\"bias\":%.3f,\"markers\":[", bias);
    for (int i = 0; i < n; ++i)
        o += snprintf(b + o, cap - o,
            "%s{\"name\":\"%s\",\"value\":%.2f,\"unit\":\"%s\","
            "\"lo\":%.2f,\"hi\":%.2f,\"flag\":\"%c\"}",
            i ? "," : "", m[i].name, m[i].value, m[i].unit,
            m[i].lo, m[i].hi, blood_flag(&m[i]));
    o += snprintf(b + o, cap - o, "]}");
    return o;
}

static int api_dna(char *b, int cap, const char *q, unsigned *seed)
{
    char seq[1024];
    if (!qparam(q, "seq", seq, sizeof(seq)))
        strcpy(seq, "ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG");
    snapshot_t s = make_snapshot(seed);
    dna_stats_t d = dna_analyze(seq);
    char km[8]; int kc; dna_top_kmer(seq, 3, km, sizeof(km), &kc);
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o,
        ",\"seq\":\"%s\",\"length\":%zu,\"valid\":%d,"
        "\"A\":%zu,\"C\":%zu,\"G\":%zu,\"T\":%zu,\"gc\":%.4f,"
        "\"kmer\":\"%s\",\"kmer_count\":%d}",
        seq, d.length, d.valid, d.count[0], d.count[1], d.count[2],
        d.count[3], d.gc_content, km, kc);
    return o;
}

static int api_rna(char *b, int cap, const char *q, unsigned *seed)
{
    char dna[1024];
    if (!qparam(q, "seq", dna, sizeof(dna)))
        strcpy(dna, "ATGGCCATTGTAATGGGCCGCTGA");
    snapshot_t s = make_snapshot(seed);
    char rna[2048], aa[1024];
    rna_transcribe(dna, rna, sizeof(rna));
    rna_translate(rna, aa, sizeof(aa));
    int o = 0;
    o += snprintf(b + o, cap - o, "{");
    o = json_sensors(b, o, cap, &s);
    o += snprintf(b + o, cap - o, ",\"dna\":\"%s\",\"rna\":\"%s\",\"peptide\":\"%s\"}",
                  dna, rna, aa);
    return o;
}

/* ----------------------------------------------------------- HTTP plumbing */

static int route_api(const char *path, const char *query, char *b, int cap, unsigned *seed)
{
    if (!strcmp(path, "/api/pipeline")) return api_pipeline(b, cap, query, seed);
    if (!strcmp(path, "/api/gamma"))    return api_gamma(b, cap, query, seed);
    if (!strcmp(path, "/api/basal"))    return api_basal(b, cap, query, seed);
    if (!strcmp(path, "/api/sensor"))   return api_sensor(b, cap, query, seed);
    if (!strcmp(path, "/api/mri"))      return api_mri(b, cap, query, seed);
    if (!strcmp(path, "/api/fmri"))     return api_fmri(b, cap, query, seed);
    if (!strcmp(path, "/api/topo"))     return api_topo(b, cap, query, seed);
    if (!strcmp(path, "/api/ct"))       return api_ct(b, cap, query, seed);
    if (!strcmp(path, "/api/blood"))    return api_blood(b, cap, query, seed);
    if (!strcmp(path, "/api/dna"))      return api_dna(b, cap, query, seed);
    if (!strcmp(path, "/api/rna"))      return api_rna(b, cap, query, seed);
    return -1;
}

static const char *mime_of(const char *path)
{
    const char *dot = strrchr(path, '.');
    if (!dot) return "application/octet-stream";
    if (!strcmp(dot, ".html")) return "text/html; charset=utf-8";
    if (!strcmp(dot, ".css"))  return "text/css; charset=utf-8";
    if (!strcmp(dot, ".js"))   return "application/javascript; charset=utf-8";
    if (!strcmp(dot, ".json")) return "application/json; charset=utf-8";
    if (!strcmp(dot, ".svg"))  return "image/svg+xml";
    return "text/plain; charset=utf-8";
}

static void send_all(int fd, const char *buf, size_t len)
{
    size_t sent = 0;
    while (sent < len) {
        ssize_t w = write(fd, buf + sent, len - sent);
        if (w <= 0) break;
        sent += (size_t)w;
    }
}

static void serve_static(int fd, const char *path)
{
    char fpath[4096];
    if (!strcmp(path, "/")) path = "/index.html";
    /* prevent path traversal */
    if (strstr(path, "..")) { dprintf(fd, "HTTP/1.1 400 Bad Request\r\n\r\n"); return; }
    snprintf(fpath, sizeof(fpath), "%s%s", webroot, path);
    FILE *f = fopen(fpath, "rb");
    if (!f) {
        const char *msg = "404 Not Found";
        dprintf(fd, "HTTP/1.1 404 Not Found\r\nContent-Length: %zu\r\n"
                    "Content-Type: text/plain\r\n\r\n%s", strlen(msg), msg);
        return;
    }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    char *data = malloc(sz > 0 ? (size_t)sz : 1);
    size_t rd = fread(data, 1, (size_t)sz, f);
    fclose(f);
    char hdr[256];
    int hl = snprintf(hdr, sizeof(hdr),
        "HTTP/1.1 200 OK\r\nContent-Type: %s\r\nContent-Length: %zu\r\n"
        "Cache-Control: no-store\r\n\r\n", mime_of(fpath), rd);
    send_all(fd, hdr, hl);
    send_all(fd, data, rd);
    free(data);
}

static void handle(int fd)
{
    char req[8192];
    ssize_t n = read(fd, req, sizeof(req) - 1);
    if (n <= 0) return;
    req[n] = 0;

    char method[8], target[2048];
    if (sscanf(req, "%7s %2047s", method, target) != 2) return;
    (void)method;

    char *query = strchr(target, '?');
    if (query) { *query = 0; query++; }

    if (strncmp(target, "/api/", 5) == 0) {
        static char body[1 << 16];
        unsigned seed = (unsigned)time(NULL) ^ (unsigned)fd ^ (unsigned)clock();
        int bl = route_api(target, query, body, (int)sizeof(body), &seed);
        if (bl < 0) {
            const char *msg = "{\"error\":\"unknown endpoint\"}";
            dprintf(fd, "HTTP/1.1 404 Not Found\r\nContent-Type: application/json\r\n"
                        "Content-Length: %zu\r\n\r\n%s", strlen(msg), msg);
            return;
        }
        char hdr[256];
        int hl = snprintf(hdr, sizeof(hdr),
            "HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n"
            "Content-Length: %d\r\nCache-Control: no-store\r\n\r\n", bl);
        send_all(fd, hdr, hl);
        send_all(fd, body, (size_t)bl);
    } else {
        serve_static(fd, target);
    }
}

int main(int argc, char **argv)
{
    int port = (argc > 1) ? atoi(argv[1]) : 8080;
    if (argc > 2) webroot = argv[2];

    int srv = socket(AF_INET, SOCK_STREAM, 0);
    if (srv < 0) { perror("socket"); return 1; }
    int one = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK); /* localhost only */
    addr.sin_port = htons((uint16_t)port);

    if (bind(srv, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); return 1;
    }
    if (listen(srv, 16) < 0) { perror("listen"); return 1; }

    printf("omega_neurothermal GUI server\n");
    printf("  webroot : %s\n", webroot);
    printf("  open    : http://localhost:%d\n", port);
    printf("  (Ctrl-C to stop; localhost only, educational simulation)\n");
    fflush(stdout);

    for (;;) {
        int cli = accept(srv, NULL, NULL);
        if (cli < 0) continue;
        handle(cli);
        close(cli);
    }
    return 0;
}
