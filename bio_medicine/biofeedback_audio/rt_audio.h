/*
 * rt_audio.h — リアルタイム音声出力(ALSA直結) 抽象化
 *
 * 連続的にステレオサイン波を生成し、ALSA PCM デバイスへストリーム再生する。
 * carrier/beat はスレッド安全に動的更新でき、バイオフィードバックで
 * センサー値に追従させられる(位相連続なのでクリックノイズが出ない)。
 *
 * ビルド時に ALSA が無い/実行時にデバイスが無い場合でも安全:
 *   rt_audio_start() が失敗を返すだけで、呼び出し側は WAV 生成へフォールバックできる。
 */
#ifndef RT_AUDIO_H
#define RT_AUDIO_H

typedef struct RtAudio RtAudio;

/* 生成(まだ再生はしない)。失敗で NULL */
RtAudio *rt_audio_create(void);

/* 再生開始。0=成功, 非0=失敗(ALSA未対応/デバイス無し等) */
int  rt_audio_start(RtAudio *rt);

/* 再生中か(1/0) */
int  rt_audio_is_running(const RtAudio *rt);

/* 周波数を動的更新(スレッド安全, 位相連続) */
void rt_audio_set_freq(RtAudio *rt, double carrier, double beat);

/* 音量(0..1)を設定 */
void rt_audio_set_gain(RtAudio *rt, double gain);

/* 停止 */
void rt_audio_stop(RtAudio *rt);

/* 破棄(自動的に stop する) */
void rt_audio_destroy(RtAudio *rt);

/* この実行ファイルが ALSA 対応でビルドされたか(1/0) */
int  rt_audio_available(void);

#endif /* RT_AUDIO_H */
