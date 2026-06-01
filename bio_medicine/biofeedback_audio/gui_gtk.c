/*
 * gui_gtk.c — GTK+3 グラフィカルGUI フロントエンド
 *
 * モダンなデスクトップGUI。
 *   - プリセット一覧(GtkTreeView, クリックで選択)
 *   - 赤外線(IR)センサー + 温度計 のライブ表示(GtkProgressBar)
 *   - 選択プリセットの波形(GtkDrawingArea + cairo)
 *   - ボタン: Play(WAV) / Save / Realtime(ALSA連続再生) / BioFB / Quit
 *       BioFB ON: 温度計 -> beat、IR対象温度 -> carrier を変調
 *       Realtime ON: ALSA でセンサー値に追従した連続再生
 *
 * 重要: 音響トーン発生器です。プリセット名はラベルであり、薬剤や治療効果を
 *       再現・代替しません(医学的主張なし)。
 *
 * ビルド: Makefile 参照(要 gtk+-3.0、ALSAがあれば実時間再生有効)
 * 実行:
 *   DISPLAY=:0 ./bfa_gtk     (Xディスプレイのあるデスクトップで)
 *   ./bfa_gtk --selftest     (GUIを開かず検証して終了)
 */
#define _POSIX_C_SOURCE 200809L
#include "audio_core.h"
#include "sensors.h"
#include "rt_audio.h"
#include "biosignal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <gtk/gtk.h>

/* アプリ状態 */
typedef struct {
    SensorCtx     sc;
    SensorReading rd;
    BioCtx        bc;
    BioReading    br;
    RtAudio      *rt;
    int           sel;
    int           feedback;   /* 温度/IR -> beat/carrier */
    int           neuro;      /* EEG/ECG -> beat/carrier */
    int           realtime;
    double        phase;

    GtkWidget *win;
    GtkWidget *tree;
    GtkWidget *pb_temp;
    GtkWidget *pb_ir;
    GtkWidget *pb_raw;
    GtkWidget *lbl_present;
    GtkWidget *lbl_info;
    GtkWidget *lbl_status;
    GtkWidget *lbl_eeg;
    GtkWidget *pb_band[BIO_BAND_COUNT];
    GtkWidget *lbl_ecg;
    GtkWidget *ecg_draw;
    GtkWidget *draw;
    GtkWidget *btn_rt;
    GtkWidget *btn_fb;
    GtkWidget *btn_neuro;
} App;

static double eff_carrier(App *a) {
    const Preset *p = &BFA_PRESETS[a->sel];
    if (a->neuro)    return bfa_ecg_carrier(p->carrier, a->br.bpm);
    if (a->feedback) return bfa_feedback_carrier(p->carrier, a->rd.ir_object_c);
    return p->carrier;
}
static double eff_beat(App *a) {
    const Preset *p = &BFA_PRESETS[a->sel];
    if (a->neuro)    return bfa_eeg_beat(a->br.eeg_dominant);
    if (a->feedback) return bfa_feedback_beat(p->beat, a->rd.ambient_c);
    return p->beat;
}

static void set_status(App *a, const char *msg) {
    gtk_label_set_text(GTK_LABEL(a->lbl_status), msg);
}

/* ---- 波形描画 ---- */
static gboolean on_draw(GtkWidget *w, cairo_t *cr, gpointer data) {
    App *a = data;
    GtkAllocation al; gtk_widget_get_allocation(w, &al);
    int W = al.width, H = al.height;

    cairo_set_source_rgb(cr, 0.15, 0.16, 0.20);
    cairo_paint(cr);

    double ec = eff_carrier(a), eb = eff_beat(a);
    cairo_set_source_rgb(cr, 0.47, 0.78, 0.94);
    cairo_set_line_width(cr, 1.5);
    for (int x = 0; x < W; x++) {
        double t = a->phase + (double)x / W * (3.0 / ec);
        double l, r; bfa_sample_at(t, ec, eb, &l, &r);
        double y = (1.0 - l) * 0.5 * (H - 4) + 2;
        if (x == 0) cairo_move_to(cr, x, y);
        else        cairo_line_to(cr, x, y);
    }
    cairo_stroke(cr);
    return FALSE;
}

/* ---- ECG 波形描画 ---- */
static gboolean on_draw_ecg(GtkWidget *w, cairo_t *cr, gpointer data) {
    App *a = data;
    GtkAllocation al; gtk_widget_get_allocation(w, &al);
    int W = al.width, H = al.height;

    cairo_set_source_rgb(cr, 0.15, 0.16, 0.20);
    cairo_paint(cr);
    if (a->br.ecg_count <= 0) return FALSE;

    if (a->br.beat) cairo_set_source_rgb(cr, 0.90, 0.35, 0.35);
    else            cairo_set_source_rgb(cr, 0.47, 0.78, 0.94);
    cairo_set_line_width(cr, 1.5);
    for (int x = 0; x < W; x++) {
        int idx = (int)((double)x / W * (ECG_WIN - 1));
        double v = a->br.ecg_wave[idx];
        double y = (1.0 - v) * 0.5 * (H - 4) + 2;
        if (x == 0) cairo_move_to(cr, x, y);
        else        cairo_line_to(cr, x, y);
    }
    cairo_stroke(cr);
    return FALSE;
}

/* ---- 周期更新(センサー + 生体信号 + 表示 + 実時間音声) ---- */
static gboolean tick(gpointer data) {
    App *a = data;
    sensor_read(&a->sc, &a->rd);
    bio_read(&a->bc, &a->br);

    double ec = eff_carrier(a), eb = eff_beat(a);
    if (a->realtime && a->rt && rt_audio_is_running(a->rt))
        rt_audio_set_freq(a->rt, ec, eb);

    double f_temp = (a->rd.ambient_c - 10.0) / 30.0; if (f_temp<0)f_temp=0; if(f_temp>1)f_temp=1;
    double f_iro  = (a->rd.ir_object_c - 20.0) / 20.0; if(f_iro<0)f_iro=0; if(f_iro>1)f_iro=1;
    char tx[64];
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(a->pb_temp), f_temp);
    snprintf(tx, sizeof(tx), "温度計 %.2f C", a->rd.ambient_c);
    gtk_progress_bar_set_text(GTK_PROGRESS_BAR(a->pb_temp), tx);
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(a->pb_ir), f_iro);
    snprintf(tx, sizeof(tx), "IR対象温 %.2f C", a->rd.ir_object_c);
    gtk_progress_bar_set_text(GTK_PROGRESS_BAR(a->pb_ir), tx);
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(a->pb_raw), a->rd.ir_raw);
    snprintf(tx, sizeof(tx), "IR生値 %.2f", a->rd.ir_raw);
    gtk_progress_bar_set_text(GTK_PROGRESS_BAR(a->pb_raw), tx);
    gtk_label_set_text(GTK_LABEL(a->lbl_present),
                       a->rd.present ? "IR近接: ●検知" : "IR近接: ○なし");

    /* EEG 帯域パワー */
    for (int b = 0; b < BIO_BAND_COUNT; b++) {
        char bt[48];
        gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(a->pb_band[b]), a->br.eeg_band[b]);
        snprintf(bt, sizeof(bt), "%s %.0f%%%s", bio_band_name(b),
                 a->br.eeg_band[b] * 100.0, (b == a->br.eeg_dominant) ? " ◀" : "");
        gtk_progress_bar_set_text(GTK_PROGRESS_BAR(a->pb_band[b]), bt);
    }
    char el[128];
    snprintf(el, sizeof(el), "EEG(脳波計) 支配帯域: %s → beat %.1fHz",
             bio_band_name(a->br.eeg_dominant), bfa_eeg_beat(a->br.eeg_dominant));
    gtk_label_set_text(GTK_LABEL(a->lbl_eeg), el);
    char cl[96];
    snprintf(cl, sizeof(cl), "ECG(心電図) 心拍: %.1f bpm %s → carrier",
             a->br.bpm, a->br.beat ? "♥" : "");
    gtk_label_set_text(GTK_LABEL(a->lbl_ecg), cl);

    const Preset *p = &BFA_PRESETS[a->sel];
    const char *mode = a->neuro ? "[脳波/心電FB]" : (a->feedback ? "[温度FB]" : "[FB:OFF]");
    char info[400];
    snprintf(info, sizeof(info),
             "選択: %s   carrier %.1f→%.1fHz   beat %.1f→%.2fHz(%s)   %s",
             p->jp, p->carrier, ec, p->beat, eb, bfa_band_name(eb), mode);
    gtk_label_set_text(GTK_LABEL(a->lbl_info), info);

    a->phase += 0.02;
    gtk_widget_queue_draw(a->draw);
    gtk_widget_queue_draw(a->ecg_draw);
    return TRUE; /* 継続 */
}

/* ---- ツリー選択 ---- */
static void on_tree_sel(GtkTreeSelection *selp, gpointer data) {
    App *a = data;
    GtkTreeModel *model; GtkTreeIter it;
    if (gtk_tree_selection_get_selected(selp, &model, &it)) {
        gint idx;
        gtk_tree_model_get(model, &it, 0, &idx, -1);
        if (idx >= 0 && idx < (int)BFA_PRESET_COUNT) a->sel = idx;
    }
}

/* ---- ボタン ---- */
static void on_play(GtkButton *b, gpointer data) {
    (void)b; App *a = data;
    const Preset *p = &BFA_PRESETS[a->sel];
    char path[256]; snprintf(path, sizeof(path), "/tmp/bfa_%s.wav", p->key);
    bfa_play_wav(path, eff_carrier(a), eff_beat(a), 15.0);
    char m[128]; snprintf(m, sizeof(m), "再生(試行): %s", p->jp);
    set_status(a, m);
}
static void on_save(GtkButton *b, gpointer data) {
    (void)b; App *a = data;
    const Preset *p = &BFA_PRESETS[a->sel];
    char path[256]; snprintf(path, sizeof(path), "%s.wav", p->key);
    char m[320];
    if (bfa_write_wav(path, eff_carrier(a), eff_beat(a), 30.0) == 0)
        snprintf(m, sizeof(m), "保存: %s (30s)", path);
    else snprintf(m, sizeof(m), "保存失敗");
    set_status(a, m);
}
static void on_realtime(GtkButton *b, gpointer data) {
    (void)b; App *a = data;
    if (!rt_audio_available()) { set_status(a, "実時間再生は無効(ALSA無し)"); return; }
    if (a->realtime && rt_audio_is_running(a->rt)) {
        rt_audio_stop(a->rt); a->realtime = 0;
        gtk_button_set_label(GTK_BUTTON(a->btn_rt), "Realtime");
        set_status(a, "実時間再生 停止");
    } else {
        rt_audio_set_freq(a->rt, eff_carrier(a), eff_beat(a));
        if (rt_audio_start(a->rt) == 0) {
            a->realtime = 1;
            gtk_button_set_label(GTK_BUTTON(a->btn_rt), "Realtime■");
            set_status(a, "実時間再生 開始(ALSA)");
        } else set_status(a, "実時間再生 失敗(出力デバイス無し?)");
    }
}
static void on_fb(GtkButton *b, gpointer data) {
    (void)b; App *a = data;
    a->feedback = !a->feedback;
    if (a->feedback) { a->neuro = 0; gtk_button_set_label(GTK_BUTTON(a->btn_neuro), "Neuro"); }
    gtk_button_set_label(GTK_BUTTON(a->btn_fb), a->feedback ? "TempFB■" : "TempFB");
    set_status(a, a->feedback ? "温度FB ON (温度→beat, IR→carrier)" : "温度FB OFF");
}
static void on_neuro(GtkButton *b, gpointer data) {
    (void)b; App *a = data;
    a->neuro = !a->neuro;
    if (a->neuro) { a->feedback = 0; gtk_button_set_label(GTK_BUTTON(a->btn_fb), "TempFB"); }
    gtk_button_set_label(GTK_BUTTON(a->btn_neuro), a->neuro ? "Neuro■" : "Neuro");
    set_status(a, a->neuro ? "脳波/心電FB ON (脳波支配帯域→beat, 心拍→carrier)" : "脳波/心電FB OFF");
}
static void on_quit(GtkButton *b, gpointer data) {
    (void)b; App *a = data;
    if (a->rt) rt_audio_stop(a->rt);
    gtk_main_quit();
}

/* ---- 自己診断(GUIを開かない) ---- */
static int selftest(void) {
    SensorCtx sc; sensor_init(&sc);
    printf("[selftest] sensor backend = %s\n", sensor_backend_name(&sc));
    printf("[selftest] realtime audio (ALSA) = %s\n",
           rt_audio_available() ? "compiled-in" : "not available");
    printf("[selftest] GTK %d.%d.%d\n",
           gtk_get_major_version(), gtk_get_minor_version(), gtk_get_micro_version());
    SensorReading r;
    for (int i = 0; i < 3; i++) {
        sensor_read(&sc, &r);
        printf("[selftest] amb=%.2fC ir_obj=%.2fC ir_raw=%.2f present=%d\n",
               r.ambient_c, r.ir_object_c, r.ir_raw, r.present);
    }
    const Preset *p = &BFA_PRESETS[0];
    printf("[selftest] preset[0]=%s carrier=%.1f beat=%.1f -> fb_carrier=%.2f fb_beat=%.2f\n",
           p->jp, p->carrier, p->beat,
           bfa_feedback_carrier(p->carrier, r.ir_object_c),
           bfa_feedback_beat(p->beat, r.ambient_c));
    BioCtx bc; bio_init(&bc);
    BioReading br;
    for (int i = 0; i < 40; i++) bio_read(&bc, &br);
    printf("[selftest] biosignal backend = %s\n", bio_backend_name(&bc));
    printf("[selftest] EEG dominant=%s -> beat=%.1fHz   ECG bpm=%.1f -> carrier=%.1fHz\n",
           bio_band_name(br.eeg_dominant), bfa_eeg_beat(br.eeg_dominant),
           br.bpm, bfa_ecg_carrier(p->carrier, br.bpm));
    if (bfa_write_wav("/tmp/bfa_gtk_selftest.wav", p->carrier, p->beat, 0.5) != 0) {
        printf("[selftest] WAV write FAILED\n"); return 1;
    }
    printf("[selftest] WAV write OK\n[selftest] OK\n");
    return 0;
}

static GtkWidget *make_gauge(const char *initial) {
    GtkWidget *pb = gtk_progress_bar_new();
    gtk_progress_bar_set_show_text(GTK_PROGRESS_BAR(pb), TRUE);
    gtk_progress_bar_set_text(GTK_PROGRESS_BAR(pb), initial);
    return pb;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "--selftest") == 0) {
        /* GTK のバージョン取得のため最小初期化(ディスプレイ不要) */
        return selftest();
    }

    if (!gtk_init_check(&argc, &argv)) {
        fprintf(stderr,
            "GTK を初期化できません(DISPLAY未設定/未接続)。\n"
            "Xディスプレイのある環境で実行してください。検証だけなら: %s --selftest\n",
            argv[0]);
        return 1;
    }

    App a; memset(&a, 0, sizeof(a));
    sensor_init(&a.sc);
    bio_init(&a.bc);
    a.rt = rt_audio_create();
    a.sel = 0;

    a.win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(a.win),
        "バイオフィードバック 音アプリ (GTK) — IR/温度/脳波計/心電図");
    gtk_window_set_default_size(GTK_WINDOW(a.win), 880, 760);
    g_signal_connect(a.win, "destroy", G_CALLBACK(gtk_main_quit), NULL);

    GtkWidget *root = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
    gtk_container_set_border_width(GTK_CONTAINER(root), 8);
    gtk_container_add(GTK_CONTAINER(a.win), root);

    /* ヘッダ + 注意書き */
    GtkWidget *hdr = gtk_label_new(NULL);
    gtk_label_set_xalign(GTK_LABEL(hdr), 0.0);
    gtk_label_set_markup(GTK_LABEL(hdr),
        "<b>バイオフィードバック 音アプリ (GTK)</b>  IRセンサー + 温度計\n"
        "<small>※音響トーン発生器です。薬剤や治療効果を再現・代替しません。</small>");
    gtk_box_pack_start(GTK_BOX(root), hdr, FALSE, FALSE, 0);

    /* 中段: 左=一覧、右=センサー */
    GtkWidget *mid = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    gtk_box_pack_start(GTK_BOX(root), mid, TRUE, TRUE, 0);

    /* プリセット一覧(TreeView) */
    GtkListStore *store = gtk_list_store_new(5, G_TYPE_INT, G_TYPE_STRING,
                                             G_TYPE_STRING, G_TYPE_STRING, G_TYPE_STRING);
    for (int i = 0; i < (int)BFA_PRESET_COUNT; i++) {
        char c[16], b[16];
        snprintf(c, sizeof(c), "%.1f", BFA_PRESETS[i].carrier);
        snprintf(b, sizeof(b), "%.1f", BFA_PRESETS[i].beat);
        GtkTreeIter it;
        gtk_list_store_append(store, &it);
        gtk_list_store_set(store, &it, 0, i, 1, BFA_PRESETS[i].jp,
                           2, c, 3, b, 4, bfa_band_name(BFA_PRESETS[i].beat), -1);
    }
    a.tree = gtk_tree_view_new_with_model(GTK_TREE_MODEL(store));
    g_object_unref(store);
    const char *titles[] = { "ラベル", "carrier", "beat", "帯域" };
    for (int col = 0; col < 4; col++) {
        GtkCellRenderer *rend = gtk_cell_renderer_text_new();
        GtkTreeViewColumn *c = gtk_tree_view_column_new_with_attributes(
            titles[col], rend, "text", col + 1, NULL);
        gtk_tree_view_append_column(GTK_TREE_VIEW(a.tree), c);
    }
    GtkTreeSelection *selp = gtk_tree_view_get_selection(GTK_TREE_VIEW(a.tree));
    gtk_tree_selection_set_mode(selp, GTK_SELECTION_BROWSE);
    g_signal_connect(selp, "changed", G_CALLBACK(on_tree_sel), &a);

    GtkWidget *scroll = gtk_scrolled_window_new(NULL, NULL);
    gtk_widget_set_size_request(scroll, 360, -1);
    gtk_container_add(GTK_CONTAINER(scroll), a.tree);
    gtk_box_pack_start(GTK_BOX(mid), scroll, FALSE, FALSE, 0);

    /* センサーパネル */
    GtkWidget *sensors = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
    gtk_box_pack_start(GTK_BOX(mid), sensors, TRUE, TRUE, 0);
    GtkWidget *sl = gtk_label_new(NULL);
    gtk_label_set_xalign(GTK_LABEL(sl), 0.0);
    gtk_label_set_markup(GTK_LABEL(sl), "<b>センサー(ライブ)</b>");
    gtk_box_pack_start(GTK_BOX(sensors), sl, FALSE, FALSE, 0);
    a.pb_temp = make_gauge("温度計");
    a.pb_ir   = make_gauge("IR対象温");
    a.pb_raw  = make_gauge("IR生値");
    gtk_box_pack_start(GTK_BOX(sensors), a.pb_temp, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(sensors), a.pb_ir,   FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(sensors), a.pb_raw,  FALSE, FALSE, 0);
    a.lbl_present = gtk_label_new("IR近接: -");
    gtk_label_set_xalign(GTK_LABEL(a.lbl_present), 0.0);
    gtk_box_pack_start(GTK_BOX(sensors), a.lbl_present, FALSE, FALSE, 0);
    a.lbl_info = gtk_label_new("選択: -");
    gtk_label_set_xalign(GTK_LABEL(a.lbl_info), 0.0);
    gtk_label_set_line_wrap(GTK_LABEL(a.lbl_info), TRUE);
    gtk_box_pack_start(GTK_BOX(sensors), a.lbl_info, FALSE, FALSE, 4);

    char backend[128];
    snprintf(backend, sizeof(backend), "センサー: %s   実時間音声(ALSA): %s",
             sensor_backend_name(&a.sc),
             rt_audio_available() ? "利用可" : "無効");
    GtkWidget *be = gtk_label_new(backend);
    gtk_label_set_xalign(GTK_LABEL(be), 0.0);
    gtk_box_pack_start(GTK_BOX(sensors), be, FALSE, FALSE, 0);

    /* --- 脳波計(EEG) パネル --- */
    a.lbl_eeg = gtk_label_new(NULL);
    gtk_label_set_xalign(GTK_LABEL(a.lbl_eeg), 0.0);
    gtk_label_set_markup(GTK_LABEL(a.lbl_eeg), "<b>EEG(脳波計)</b>");
    gtk_box_pack_start(GTK_BOX(sensors), a.lbl_eeg, FALSE, FALSE, 4);
    for (int b = 0; b < BIO_BAND_COUNT; b++) {
        a.pb_band[b] = make_gauge(bio_band_name(b));
        gtk_box_pack_start(GTK_BOX(sensors), a.pb_band[b], FALSE, FALSE, 0);
    }

    /* --- 心電図(ECG) パネル --- */
    a.lbl_ecg = gtk_label_new(NULL);
    gtk_label_set_xalign(GTK_LABEL(a.lbl_ecg), 0.0);
    gtk_label_set_markup(GTK_LABEL(a.lbl_ecg), "<b>ECG(心電図)</b>");
    gtk_box_pack_start(GTK_BOX(sensors), a.lbl_ecg, FALSE, FALSE, 4);
    a.ecg_draw = gtk_drawing_area_new();
    gtk_widget_set_size_request(a.ecg_draw, -1, 70);
    g_signal_connect(a.ecg_draw, "draw", G_CALLBACK(on_draw_ecg), &a);
    gtk_box_pack_start(GTK_BOX(sensors), a.ecg_draw, FALSE, FALSE, 0);

    /* 波形 */
    GtkWidget *wl = gtk_label_new(NULL);
    gtk_label_set_xalign(GTK_LABEL(wl), 0.0);
    gtk_label_set_markup(GTK_LABEL(wl), "<b>音声波形 (L=carrier)</b>");
    gtk_box_pack_start(GTK_BOX(root), wl, FALSE, FALSE, 0);
    a.draw = gtk_drawing_area_new();
    gtk_widget_set_size_request(a.draw, -1, 110);
    g_signal_connect(a.draw, "draw", G_CALLBACK(on_draw), &a);
    gtk_box_pack_start(GTK_BOX(root), a.draw, FALSE, FALSE, 0);

    /* ボタン列 */
    GtkWidget *bbox = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
    gtk_box_pack_start(GTK_BOX(root), bbox, FALSE, FALSE, 0);
    GtkWidget *bp = gtk_button_new_with_label("Play");
    GtkWidget *bs = gtk_button_new_with_label("Save");
    a.btn_rt = gtk_button_new_with_label("Realtime");
    a.btn_fb = gtk_button_new_with_label("TempFB");
    a.btn_neuro = gtk_button_new_with_label("Neuro");
    GtkWidget *bq = gtk_button_new_with_label("Quit");
    g_signal_connect(bp, "clicked", G_CALLBACK(on_play), &a);
    g_signal_connect(bs, "clicked", G_CALLBACK(on_save), &a);
    g_signal_connect(a.btn_rt, "clicked", G_CALLBACK(on_realtime), &a);
    g_signal_connect(a.btn_fb, "clicked", G_CALLBACK(on_fb), &a);
    g_signal_connect(a.btn_neuro, "clicked", G_CALLBACK(on_neuro), &a);
    g_signal_connect(bq, "clicked", G_CALLBACK(on_quit), &a);
    gtk_box_pack_start(GTK_BOX(bbox), bp, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(bbox), bs, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(bbox), a.btn_rt, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(bbox), a.btn_fb, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(bbox), a.btn_neuro, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(bbox), bq, TRUE, TRUE, 0);

    /* ステータスバー */
    a.lbl_status = gtk_label_new("↑↓/クリック:選択  各ボタンで操作");
    gtk_label_set_xalign(GTK_LABEL(a.lbl_status), 0.0);
    gtk_box_pack_start(GTK_BOX(root), a.lbl_status, FALSE, FALSE, 0);

    /* 初期選択 */
    GtkTreePath *path0 = gtk_tree_path_new_from_indices(0, -1);
    gtk_tree_selection_select_path(selp, path0);
    gtk_tree_path_free(path0);

    /* 150ms タイマでライブ更新 */
    g_timeout_add(150, tick, &a);

    gtk_widget_show_all(a.win);
    gtk_main();

    if (a.rt) rt_audio_destroy(a.rt);
    printf("終了しました。\n");
    return 0;
}
