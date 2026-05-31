/*
 * sensors.h — 赤外線(IR)センサー + 温度計 の抽象化レイヤー
 *
 * バックエンド:
 *   1) 実機 (FILE/sysfs): 環境変数で指定したファイルから数値を読む
 *        BFA_TEMP_PATH : 温度ソース (sysfs thermal_zone の millidegC、または摂氏の数値)
 *        BFA_IR_PATH   : IR センサーソース (物体温度[摂氏] もしくは生値)
 *      例) MLX90614(IR放射温度計) を iio/sysfs やシリアル読み取りデーモン経由で
 *          ファイルに出力しておけば、そのまま読み込める。
 *   2) シミュレーション: 上記が未設定/読み取り不可ならダミー値を生成。
 *
 * 注意: 本コンテナにはセンサーが無いため通常はシミュレーションで動作する。
 *       実機 Raspberry Pi 等では BFA_TEMP_PATH / BFA_IR_PATH を設定して使う。
 */
#ifndef SENSORS_H
#define SENSORS_H

typedef enum {
    SENSOR_BACKEND_SIM  = 0,  /* シミュレーション */
    SENSOR_BACKEND_FILE = 1   /* 実機(ファイル/sysfs) */
} SensorBackend;

typedef struct {
    double ambient_c;   /* 周囲温度(摂氏) … 温度計 */
    double ir_object_c; /* IR が捉えた対象物体温度(摂氏) … 赤外線センサー */
    double ir_raw;      /* IR 生値(0..1 正規化) */
    int    present;     /* 対象を検知したか(IR近接) 1/0 */
    long   ts_ms;       /* 取得時刻(ms) */
} SensorReading;

typedef struct {
    SensorBackend backend;
    char temp_path[512];
    char ir_path[512];
    /* シミュレーション用の内部状態 */
    double sim_t;
    unsigned sim_seed;
} SensorCtx;

/* 環境変数を読んでバックエンドを決定し初期化する */
void sensor_init(SensorCtx *ctx);

/* 1 サンプル取得。戻り値 0=成功 */
int  sensor_read(SensorCtx *ctx, SensorReading *out);

/* バックエンド名(表示用) */
const char *sensor_backend_name(const SensorCtx *ctx);

#endif /* SENSORS_H */
