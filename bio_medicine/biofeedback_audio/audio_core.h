/*
 * audio_core.h — プリセット定義と WAV サイン波合成の共有コア
 *
 * CLI / ncurses GUI / X11 GUI から共通利用される。
 * 本モジュールは音響トーンの生成のみを行う。プリセット名はラベルであり、
 * 薬剤や治療効果を再現・代替するものではない（医学的主張はしない）。
 */
#ifndef AUDIO_CORE_H
#define AUDIO_CORE_H

#include <stddef.h>

#define BFA_SAMPLE_RATE   44100
#define BFA_CHANNELS      2
#define BFA_BITS_PER_SAMP 16
#define BFA_AMPLITUDE     0.45   /* ピーク振幅 (0..1) */
#define BFA_FADE_SECONDS  0.05   /* フェードイン/アウト(秒) */

typedef struct {
    const char *key;     /* コマンド/識別用キー(英字) */
    const char *jp;      /* 日本語ラベル */
    double      carrier; /* キャリア周波数(Hz) */
    double      beat;    /* バイノーラルビート周波数(Hz) */
} Preset;

extern const Preset BFA_PRESETS[];
extern const size_t BFA_PRESET_COUNT;

/* beat 周波数から EEG 帯域名を返す */
const char *bfa_band_name(double beat);

/* キーからプリセットを検索(大文字小文字無視)。見つからなければ NULL */
const Preset *bfa_find_preset(const char *key);

/*
 * ステレオ WAV を書き出す。
 *   左 = sin(2*pi*carrier*t), 右 = sin(2*pi*(carrier+beat)*t)
 * 戻り値: 0=成功, 非0=失敗
 */
int bfa_write_wav(const char *path, double carrier, double beat, double seconds);

/*
 * 時刻 t(秒) における左右サンプル値(-1..1, エンベロープ未適用)を返す。
 * GUI の波形表示などに使用。
 */
void bfa_sample_at(double t, double carrier, double beat,
                   double *left, double *right);

/*
 * WAV を生成し、利用可能なプレイヤー(aplay/paplay/ffplay/afplay)で再生を試みる。
 * 再生はベストエフォート(プレイヤーが無ければ生成のみ)。
 * 戻り値: 0=WAV生成成功, 非0=失敗
 */
int bfa_play_wav(const char *path, double carrier, double beat, double seconds);

/* ---- センサー → 周波数 マッピング(バイオフィードバック共通) ---- */

/*
 * 温度計の周囲温度から beat 周波数(Hz)を変調する。
 * 基準 24C で base_beat、±1C ごとに ±0.5Hz。範囲 [0.5, 30]Hz にクランプ。
 */
double bfa_feedback_beat(double base_beat, double ambient_c);

/*
 * IR が捉えた対象物体温度から carrier 周波数(Hz)を変調する。
 * 基準 30C で base_carrier、+1C ごとに +10Hz。範囲 [80, 1200]Hz にクランプ。
 * (対象が近く/温かいほど高い音になる)
 */
double bfa_feedback_carrier(double base_carrier, double ir_object_c);

/* ---- 生体信号(EEG/ECG) → 周波数 マッピング ---- */

/*
 * 脳波の支配帯域(0=delta..4=gamma)から、その帯域の代表周波数(Hz)を返す。
 * バイオフィードバックで「今の脳波に音のうなり(beat)を合わせる」用途。
 *   delta=2.5, theta=6, alpha=10, beta=20, gamma=35
 */
double bfa_eeg_beat(int dominant_band);

/*
 * 心拍数(BPM)から carrier 周波数(Hz)へのオフセットを与える。
 * 基準 60BPM で base_carrier、+1BPM ごとに +1Hz。範囲 [80, 1200]Hz。
 */
double bfa_ecg_carrier(double base_carrier, double bpm);

#endif /* AUDIO_CORE_H */
