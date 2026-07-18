/*
 * gui_win32.c — Windows ネイティブGUI フロントエンド (Win32 API)
 *
 * Windows 10/11 用の .exe。追加ランタイム不要(Win32 + WinMM のみ)。
 *   - プリセット一覧(リストボックス)
 *   - 赤外線(IR)センサー・温度計・脳波計(EEG)・心電図(ECG) のライブ表示(シミュレーション)
 *   - 選択プリセットの音声波形(GDI 描画)
 *   - 音再生: WinMM waveOut でステレオ・バイノーラルビートを実再生
 *   - オラクル(お告げ)モード: 娯楽用メッセージを表示し音と連動
 *
 * ⚠️ 重要:
 *   - 本アプリは音響トーン発生器 + センサー可視化 + 娯楽オラクルです。
 *   - プリセット名は薬剤の薬効を再現しません。EEG/ECG は医療機器ではありません。
 *   - 「オラクル」は未来予知・アカシックレコード等ではなく、乱数で選んだ
 *     定型メッセージを出す娯楽機能です(oracle.c 参照)。
 *
 * ビルド(Linux上でクロスコンパイル):
 *   x86_64-w64-mingw32-gcc -std=c99 -O2 -municode -mwindows -o BadaBiofeedback.exe \
 *       gui_win32.c audio_core.c sensors.c biosignal.c oracle.c \
 *       -lgdi32 -luser32 -lwinmm -lm
 */
#include <windows.h>
#include <mmsystem.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "audio_core.h"
#include "sensors.h"
#include "biosignal.h"
#include "oracle.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ---- コントロール ID ---- */
#define IDC_LIST     101
#define IDC_PLAY     102
#define IDC_STOP     103
#define IDC_ORACLE   104
#define IDC_NEURO    105
#define IDC_QUIT     106
#define IDT_TICK     1

/* ---- 状態 ---- */
static SensorCtx     g_sc;
static SensorReading g_rd;
static BioCtx        g_bc;
static BioReading    g_br;
static int           g_sel = 0;
static int           g_neuro = 0;     /* EEG/ECG フィードバック */
static int           g_playing = 0;
static double        g_phase = 0.0;
static unsigned long g_oracle_seed = 0;
static wchar_t       g_oracle_line[256] = L"";
static wchar_t       g_status[256] = L"";

static HWND g_hList, g_hOracleLbl, g_hStatusLbl, g_hCanvas;
static HFONT g_font;

/* ---- WinMM 連続再生 ---- */
#define WAV_SR      44100
#define WAV_CH      2
#define NUM_BUFS    3
#define BUF_FRAMES  4410            /* 0.1s / buffer */
static HWAVEOUT g_wo = NULL;
static WAVEHDR  g_hdr[NUM_BUFS];
static short   *g_buf[NUM_BUFS];
static double   g_ph_l = 0, g_ph_r = 0;
static double   g_cur_carrier = 200, g_cur_beat = 8;
static CRITICAL_SECTION g_lock;

/* UTF-8 -> wide 変換(ヘルパ) */
static void u8_to_w(const char *s, wchar_t *out, int outcount) {
    MultiByteToWideChar(CP_UTF8, 0, s, -1, out, outcount);
}

/* 現在の carrier/beat を求める */
static void current_freq(double *carrier, double *beat) {
    const Preset *p = &BFA_PRESETS[g_sel];
    if (g_neuro) {
        *carrier = bfa_ecg_carrier(p->carrier, g_br.bpm);
        *beat    = bfa_eeg_beat(g_br.eeg_dominant);
    } else {
        *carrier = p->carrier;
        *beat    = p->beat;
    }
}

/* 1 バッファ分のサイン波を生成 */
static void fill_buffer(short *dst) {
    double carrier, beat;
    EnterCriticalSection(&g_lock);
    carrier = g_cur_carrier; beat = g_cur_beat;
    LeaveCriticalSection(&g_lock);

    double dphl = 2.0 * M_PI * carrier / WAV_SR;
    double dphr = 2.0 * M_PI * (carrier + beat) / WAV_SR;
    for (int i = 0; i < BUF_FRAMES; i++) {
        double l = sin(g_ph_l) * 0.45 * 32767.0;
        double r = sin(g_ph_r) * 0.45 * 32767.0;
        g_ph_l += dphl; g_ph_r += dphr;
        if (g_ph_l > 2*M_PI) g_ph_l -= 2*M_PI;
        if (g_ph_r > 2*M_PI) g_ph_r -= 2*M_PI;
        dst[i*2]   = (short)l;
        dst[i*2+1] = (short)r;
    }
}

static void CALLBACK wave_cb(HWAVEOUT hwo, UINT msg, DWORD_PTR inst,
                             DWORD_PTR p1, DWORD_PTR p2) {
    (void)hwo; (void)inst; (void)p2;
    if (msg == WOM_DONE && g_playing) {
        WAVEHDR *h = (WAVEHDR *)p1;
        fill_buffer((short *)h->lpData);
        waveOutWrite(g_wo, h, sizeof(WAVEHDR));
    }
}

static int audio_start(void) {
    if (g_wo) return 1;
    WAVEFORMATEX wf; ZeroMemory(&wf, sizeof(wf));
    wf.wFormatTag = WAVE_FORMAT_PCM;
    wf.nChannels = WAV_CH;
    wf.nSamplesPerSec = WAV_SR;
    wf.wBitsPerSample = 16;
    wf.nBlockAlign = WAV_CH * 2;
    wf.nAvgBytesPerSec = WAV_SR * wf.nBlockAlign;
    if (waveOutOpen(&g_wo, WAVE_MAPPER, &wf,
                    (DWORD_PTR)wave_cb, 0, CALLBACK_FUNCTION) != MMSYSERR_NOERROR) {
        g_wo = NULL; return 0;
    }
    g_playing = 1;
    for (int i = 0; i < NUM_BUFS; i++) {
        g_buf[i] = (short *)malloc(BUF_FRAMES * WAV_CH * sizeof(short));
        fill_buffer(g_buf[i]);
        ZeroMemory(&g_hdr[i], sizeof(WAVEHDR));
        g_hdr[i].lpData = (LPSTR)g_buf[i];
        g_hdr[i].dwBufferLength = BUF_FRAMES * WAV_CH * sizeof(short);
        waveOutPrepareHeader(g_wo, &g_hdr[i], sizeof(WAVEHDR));
        waveOutWrite(g_wo, &g_hdr[i], sizeof(WAVEHDR));
    }
    return 1;
}

static void audio_stop(void) {
    if (!g_wo) return;
    g_playing = 0;
    waveOutReset(g_wo);
    for (int i = 0; i < NUM_BUFS; i++) {
        waveOutUnprepareHeader(g_wo, &g_hdr[i], sizeof(WAVEHDR));
        free(g_buf[i]); g_buf[i] = NULL;
    }
    waveOutClose(g_wo);
    g_wo = NULL;
}

/* ---- 描画: 波形 + センサー ---- */
static void paint_canvas(HWND hwnd) {
    PAINTSTRUCT ps;
    HDC hdc = BeginPaint(hwnd, &ps);
    RECT rc; GetClientRect(hwnd, &rc);
    int W = rc.right, H = rc.bottom;

    /* 背景 */
    HBRUSH bg = CreateSolidBrush(RGB(24, 26, 32));
    FillRect(hdc, &rc, bg);
    DeleteObject(bg);

    HDC mem = CreateCompatibleDC(hdc);
    HBITMAP bmp = CreateCompatibleBitmap(hdc, W, H);
    HBITMAP old = (HBITMAP)SelectObject(mem, bmp);
    HBRUSH bg2 = CreateSolidBrush(RGB(24, 26, 32));
    RECT full = {0,0,W,H}; FillRect(mem, &full, bg2); DeleteObject(bg2);
    SetBkMode(mem, TRANSPARENT);
    SetTextColor(mem, RGB(220, 224, 230));
    SelectObject(mem, g_font);

    double carrier, beat; current_freq(&carrier, &beat);

    /* センサー数値 */
    wchar_t line[256];
    swprintf(line, 256, L"温度計: %.2f C    IR対象温: %.2f C    IR近接: %s",
             g_rd.ambient_c, g_rd.ir_object_c, g_rd.present ? L"●検知" : L"○なし");
    TextOutW(mem, 10, 8, line, (int)wcslen(line));

    wchar_t wb[8]; u8_to_w(bio_band_name(g_br.eeg_dominant), wb, 8);
    swprintf(line, 256, L"EEG支配: %s    ECG心拍: %.1f bpm %s    carrier=%.1fHz beat=%.1fHz",
             wb, g_br.bpm, g_br.beat ? L"♥" : L" ", carrier, beat);
    TextOutW(mem, 10, 30, line, (int)wcslen(line));

    /* 音声波形 */
    int wy = 60, wh = 70;
    HPEN axis = CreatePen(PS_SOLID, 1, RGB(60,66,80));
    HPEN wpen = CreatePen(PS_SOLID, 2, RGB(120, 200, 240));
    HGDIOBJ oldp = SelectObject(mem, axis);
    MoveToEx(mem, 0, wy + wh/2, NULL); LineTo(mem, W, wy + wh/2);
    SelectObject(mem, wpen);
    for (int x = 0; x < W; x++) {
        double t = g_phase + (double)x / W * (3.0 / carrier);
        double l, r; bfa_sample_at(t, carrier, beat, &l, &r);
        int y = wy + (int)((1.0 - l) * 0.5 * (wh - 4)) + 2;
        if (x == 0) MoveToEx(mem, x, y, NULL); else LineTo(mem, x, y);
    }

    /* EEG 帯域バー */
    int ex = 10, ey = 145, bw = 46, gap = 8, bh = 44;
    for (int b = 0; b < BIO_BAND_COUNT; b++) {
        int bx = ex + b * (bw + gap);
        RECT br0 = { bx, ey, bx + bw, ey + bh };
        HBRUSH bb = CreateSolidBrush(RGB(60,66,80));
        FillRect(mem, &br0, bb); DeleteObject(bb);
        int hh = (int)(g_br.eeg_band[b] * bh);
        RECT br1 = { bx, ey + (bh - hh), bx + bw, ey + bh };
        HBRUSH fb = CreateSolidBrush(b == g_br.eeg_dominant ? RGB(90,200,120) : RGB(240,200,80));
        FillRect(mem, &br1, fb); DeleteObject(fb);
        wchar_t nm[8]; u8_to_w(bio_band_name(b), nm, 8);
        TextOutW(mem, bx, ey + bh + 2, nm, (int)wcslen(nm));
    }

    /* ECG 波形 */
    int cx = 10 + BIO_BAND_COUNT*(bw+gap) + 16;
    int cw = W - cx - 10, ch = bh, cy = ey;
    RECT cr = { cx, cy, cx + cw, cy + ch };
    HBRUSH cbb = CreateSolidBrush(RGB(38,42,52)); FillRect(mem, &cr, cbb); DeleteObject(cbb);
    HPEN epen = CreatePen(PS_SOLID, 1, g_br.beat ? RGB(230,90,90) : RGB(120,200,240));
    SelectObject(mem, epen);
    if (g_br.ecg_count > 0 && cw > 1) {
        for (int x = 0; x < cw; x++) {
            int idx = (int)((double)x / cw * (ECG_WIN - 1));
            double v = g_br.ecg_wave[idx];
            int y = cy + (int)((1.0 - v) * 0.5 * (ch - 4)) + 2;
            if (x == 0) MoveToEx(mem, cx + x, y, NULL); else LineTo(mem, cx + x, y);
        }
    }

    SelectObject(mem, oldp);
    DeleteObject(axis); DeleteObject(wpen); DeleteObject(epen);

    BitBlt(hdc, 0, 0, W, H, mem, 0, 0, SRCCOPY);
    SelectObject(mem, old);
    DeleteObject(bmp);
    DeleteDC(mem);
    EndPaint(hwnd, &ps);
}

static void do_oracle(void) {
    /* seed をセンサー/生体値 + カウンタから合成(娯楽演出) */
    g_oracle_seed++;
    unsigned long seed = g_oracle_seed
        ^ (unsigned long)(g_rd.ir_object_c * 1000)
        ^ ((unsigned long)(g_br.bpm) << 8)
        ^ ((unsigned long)g_br.eeg_dominant << 16);
    const OracleCard *c = oracle_draw(seed, BFA_PRESET_COUNT);
    int pr = c->preset;
    if (pr < 0 || pr >= (int)BFA_PRESET_COUNT) pr = 0;
    g_sel = pr;
    SendMessageW(g_hList, LB_SETCURSEL, g_sel, 0);

    wchar_t msg[200], mood[16];
    u8_to_w(c->jp, msg, 200);
    u8_to_w(oracle_mood_jp(c->mood), mood, 16);
    swprintf(g_oracle_line, 256, L"🔮 [%s] %s", mood, msg);
    SetWindowTextW(g_hOracleLbl, g_oracle_line);
}

static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
    case WM_CREATE: {
        g_font = CreateFontW(18, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET,
            OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
            DEFAULT_PITCH | FF_DONTCARE, L"Meiryo");

        g_hList = CreateWindowW(L"LISTBOX", NULL,
            WS_CHILD|WS_VISIBLE|WS_BORDER|WS_VSCROLL|LBS_NOTIFY,
            10, 10, 250, 380, hwnd, (HMENU)IDC_LIST, NULL, NULL);
        SendMessageW(g_hList, WM_SETFONT, (WPARAM)g_font, TRUE);
        for (size_t i = 0; i < BFA_PRESET_COUNT; i++) {
            wchar_t item[128], jp[64];
            u8_to_w(BFA_PRESETS[i].jp, jp, 64);
            swprintf(item, 128, L"%s  %.0fHz/%.1fHz", jp,
                     BFA_PRESETS[i].carrier, BFA_PRESETS[i].beat);
            SendMessageW(g_hList, LB_ADDSTRING, 0, (LPARAM)item);
        }
        SendMessageW(g_hList, LB_SETCURSEL, 0, 0);

        g_hCanvas = CreateWindowW(L"BadaCanvas", NULL, WS_CHILD|WS_VISIBLE,
            270, 10, 500, 210, hwnd, (HMENU)0, NULL, NULL);

        g_hOracleLbl = CreateWindowW(L"STATIC",
            L"「オラクル」ボタンで娯楽メッセージを表示(未来予知ではありません)",
            WS_CHILD|WS_VISIBLE, 270, 230, 500, 60, hwnd, NULL, NULL, NULL);
        SendMessageW(g_hOracleLbl, WM_SETFONT, (WPARAM)g_font, TRUE);

        CreateWindowW(L"BUTTON", L"▶ 再生", WS_CHILD|WS_VISIBLE,
            270, 300, 90, 34, hwnd, (HMENU)IDC_PLAY, NULL, NULL);
        CreateWindowW(L"BUTTON", L"■ 停止", WS_CHILD|WS_VISIBLE,
            366, 300, 90, 34, hwnd, (HMENU)IDC_STOP, NULL, NULL);
        CreateWindowW(L"BUTTON", L"🔮 オラクル", WS_CHILD|WS_VISIBLE,
            462, 300, 120, 34, hwnd, (HMENU)IDC_ORACLE, NULL, NULL);
        CreateWindowW(L"BUTTON", L"脳波/心電FB", WS_CHILD|WS_VISIBLE,
            588, 300, 110, 34, hwnd, (HMENU)IDC_NEURO, NULL, NULL);
        CreateWindowW(L"BUTTON", L"終了", WS_CHILD|WS_VISIBLE,
            704, 300, 66, 34, hwnd, (HMENU)IDC_QUIT, NULL, NULL);

        g_hStatusLbl = CreateWindowW(L"STATIC",
            L"※音響トーン発生器+娯楽オラクル。薬剤/治療効果や予知を主張しません。",
            WS_CHILD|WS_VISIBLE, 10, 400, 760, 40, hwnd, NULL, NULL, NULL);
        SendMessageW(g_hStatusLbl, WM_SETFONT, (WPARAM)g_font, TRUE);

        /* センサー初期化 + タイマ */
        sensor_init(&g_sc);
        bio_init(&g_bc);
        SetTimer(hwnd, IDT_TICK, 120, NULL);
        return 0;
    }
    case WM_TIMER: {
        sensor_read(&g_sc, &g_rd);
        bio_read(&g_bc, &g_br);
        double carrier, beat; current_freq(&carrier, &beat);
        EnterCriticalSection(&g_lock);
        g_cur_carrier = carrier; g_cur_beat = beat;
        LeaveCriticalSection(&g_lock);
        g_phase += 0.03;
        InvalidateRect(g_hCanvas, NULL, FALSE);
        return 0;
    }
    case WM_COMMAND: {
        int id = LOWORD(wp);
        if (id == IDC_LIST && HIWORD(wp) == LBN_SELCHANGE) {
            int s = (int)SendMessageW(g_hList, LB_GETCURSEL, 0, 0);
            if (s >= 0) g_sel = s;
        } else if (id == IDC_PLAY) {
            if (!g_playing) {
                if (audio_start())
                    swprintf(g_status, 256, L"再生中(WinMM)");
                else
                    swprintf(g_status, 256, L"再生失敗(音声デバイス無し?)");
                SetWindowTextW(g_hStatusLbl, g_status);
            }
        } else if (id == IDC_STOP) {
            audio_stop();
            SetWindowTextW(g_hStatusLbl, L"停止しました。");
        } else if (id == IDC_ORACLE) {
            do_oracle();
        } else if (id == IDC_NEURO) {
            g_neuro = !g_neuro;
            SetWindowTextW(g_hStatusLbl,
                g_neuro ? L"脳波/心電FB ON(支配帯域→beat, 心拍→carrier)"
                        : L"脳波/心電FB OFF");
        } else if (id == IDC_QUIT) {
            DestroyWindow(hwnd);
        }
        return 0;
    }
    case WM_DESTROY:
        audio_stop();
        KillTimer(hwnd, IDT_TICK);
        if (g_font) DeleteObject(g_font);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

static LRESULT CALLBACK CanvasProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    if (msg == WM_PAINT) { paint_canvas(hwnd); return 0; }
    if (msg == WM_ERASEBKGND) return 1;
    return DefWindowProcW(hwnd, msg, wp, lp);
}

int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE hPrev, PWSTR cmd, int nShow) {
    (void)hPrev; (void)cmd;
    InitializeCriticalSection(&g_lock);

    WNDCLASSW wc; ZeroMemory(&wc, sizeof(wc));
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInst;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW+1);
    wc.lpszClassName = L"BadaBiofeedback";
    RegisterClassW(&wc);

    WNDCLASSW cc; ZeroMemory(&cc, sizeof(cc));
    cc.lpfnWndProc = CanvasProc;
    cc.hInstance = hInst;
    cc.hCursor = LoadCursor(NULL, IDC_ARROW);
    cc.lpszClassName = L"BadaCanvas";
    RegisterClassW(&cc);

    HWND hwnd = CreateWindowW(L"BadaBiofeedback",
        L"Bada Biofeedback — 音・センサー・オラクル (娯楽)",
        WS_OVERLAPPEDWINDOW & ~WS_THICKFRAME & ~WS_MAXIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 800, 490,
        NULL, NULL, hInst, NULL);
    ShowWindow(hwnd, nShow);
    UpdateWindow(hwnd);

    MSG m;
    while (GetMessageW(&m, NULL, 0, 0)) {
        TranslateMessage(&m);
        DispatchMessageW(&m);
    }
    DeleteCriticalSection(&g_lock);
    return 0;
}
