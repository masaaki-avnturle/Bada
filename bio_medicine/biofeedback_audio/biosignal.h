/*
 * biosignal.h — 脳波計(EEG) + 心電図(ECG) の抽象化レイヤー
 *
 * IR センサー/温度計(sensors.h)と同じ思想:
 *   1) 実機 (FILE): 環境変数で指定したファイルから「最新サンプル値」を読む
 *        BFA_EEG_PATH : EEG 1ch の生サンプル(任意スケール、内部で正規化)
 *        BFA_ECG_PATH : ECG 1ch の生サンプル(任意スケール、内部で正規化)
 *      外部の取得デーモン(OpenBCI/ADS1299/AD8232 等→ファイルに最新値を書く)を想定。
 *   2) シミュレーション: 上記が無ければ生理的にもっともらしい波形を生成。
 *
 * 解析:
 *   - EEG: 直近ウィンドウから Goertzel で帯域パワー
 *          (delta/theta/alpha/beta/gamma) を求め、支配帯域を判定。
 *   - ECG: R 波をしきい値+不応期で検出し、心拍数(BPM) を推定。
 *
 * 注意: 本コンテナに生体センサーは無いため通常はシミュレーションで動作する。
 *       医療機器ではなく、教育・可視化・バイオフィードバック用途。
 */
#ifndef BIOSIGNAL_H
#define BIOSIGNAL_H

#include <stddef.h>

#define EEG_FS        128            /* EEG サンプリング周波数(Hz) */
#define ECG_FS        256            /* ECG サンプリング周波数(Hz) */
#define EEG_WIN       256            /* EEG 解析/表示ウィンドウ(=2秒) */
#define ECG_WIN       512            /* ECG 解析/表示ウィンドウ(=2秒) */
#define EEG_STEP      16             /* 1 read あたり生成する EEG サンプル数 */
#define ECG_STEP      32             /* 1 read あたり生成する ECG サンプル数 */

#define BIO_BAND_COUNT 5             /* delta/theta/alpha/beta/gamma */

typedef enum {
    BIO_BACKEND_SIM  = 0,
    BIO_BACKEND_FILE = 1
} BioBackend;

typedef struct {
    /* --- EEG --- */
    double eeg_band[BIO_BAND_COUNT];  /* 帯域相対パワー(合計=1に正規化) */
    int    eeg_dominant;              /* 支配帯域 index (0..4) */
    float  eeg_wave[EEG_WIN];         /* 表示用 直近波形(-1..1) */
    int    eeg_count;                 /* eeg_wave に入っている有効サンプル数 */

    /* --- ECG --- */
    float  ecg_wave[ECG_WIN];         /* 表示用 直近波形(-1..1) */
    int    ecg_count;
    double bpm;                       /* 推定心拍数 */
    int    beat;                      /* この read で R 波を検出したか(1/0) */

    long   ts_ms;
} BioReading;

typedef struct {
    BioBackend backend;
    char eeg_path[512];
    char ecg_path[512];

    /* リングバッファ(解析用) */
    double eeg_buf[EEG_WIN];
    int    eeg_head;
    int    eeg_filled;

    double ecg_buf[ECG_WIN];
    int    ecg_head;
    int    ecg_filled;

    /* R 波検出状態 */
    long   ecg_sample_no;     /* 連番サンプルカウンタ */
    long   last_peak_no;      /* 直近 R 波のサンプル番号 */
    int    refractory;        /* 不応期カウンタ(サンプル) */
    double bpm_smooth;

    /* シミュレーション内部状態 */
    double eeg_t;
    double ecg_t;
    double sim_hr;            /* シミュレーション目標心拍数 */
    unsigned seed;
} BioCtx;

/* 環境変数を読んでバックエンドを決定し初期化する */
void bio_init(BioCtx *ctx);

/* 1 フレーム取得(複数サンプルを生成/取り込み、指標を再計算)。戻り値 0=成功 */
int  bio_read(BioCtx *ctx, BioReading *out);

/* バックエンド名 / 帯域名 */
const char *bio_backend_name(const BioCtx *ctx);
const char *bio_band_name(int band_index);   /* 0..4 -> "delta".. */

#endif /* BIOSIGNAL_H */
