/*
 * rt_audio.c — リアルタイム音声出力(ALSA直結)
 *
 * BFA_HAVE_ALSA が定義されていれば ALSA を使う。未定義ならスタブ
 * (rt_audio_start が常に失敗を返す) としてコンパイルされ、リンクに
 * libasound を必要としない。Makefile が ALSA の有無を自動判定する。
 */
#define _POSIX_C_SOURCE 200809L
#include "rt_audio.h"
#include "audio_core.h"

#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int rt_audio_available(void) {
#ifdef BFA_HAVE_ALSA
    return 1;
#else
    return 0;
#endif
}

#ifdef BFA_HAVE_ALSA

#include <pthread.h>
#include <alsa/asoundlib.h>

#define RT_PERIOD 1024   /* 1 周期あたりフレーム数 */

struct RtAudio {
    snd_pcm_t      *pcm;
    pthread_t       thread;
    pthread_mutex_t lock;
    int             running;
    int             started;

    /* 再生パラメータ(lock で保護) */
    double carrier;
    double beat;
    double gain;

    /* 位相(オーディオスレッド専用、連続性のため保持) */
    double phase_l;
    double phase_r;
};

static void *rt_thread(void *arg) {
    RtAudio *rt = (RtAudio *)arg;
    int16_t buf[RT_PERIOD * BFA_CHANNELS];
    const double sr = (double)BFA_SAMPLE_RATE;

    while (1) {
        pthread_mutex_lock(&rt->lock);
        if (!rt->running) { pthread_mutex_unlock(&rt->lock); break; }
        double carrier = rt->carrier;
        double beat    = rt->beat;
        double gain    = rt->gain;
        pthread_mutex_unlock(&rt->lock);

        double left_hz  = carrier;
        double right_hz = carrier + beat;
        double dphl = 2.0 * M_PI * left_hz  / sr;
        double dphr = 2.0 * M_PI * right_hz / sr;

        for (int i = 0; i < RT_PERIOD; i++) {
            double l = sin(rt->phase_l) * gain;
            double r = sin(rt->phase_r) * gain;
            rt->phase_l += dphl;
            rt->phase_r += dphr;
            if (rt->phase_l > 2.0 * M_PI) rt->phase_l -= 2.0 * M_PI;
            if (rt->phase_r > 2.0 * M_PI) rt->phase_r -= 2.0 * M_PI;
            buf[i * 2]     = (int16_t)(l * 32767.0);
            buf[i * 2 + 1] = (int16_t)(r * 32767.0);
        }

        snd_pcm_sframes_t n = snd_pcm_writei(rt->pcm, buf, RT_PERIOD);
        if (n < 0) {
            /* アンダーラン等から復帰を試みる */
            if (snd_pcm_recover(rt->pcm, (int)n, 1) < 0)
                break;
        }
    }
    return NULL;
}

RtAudio *rt_audio_create(void) {
    RtAudio *rt = calloc(1, sizeof(*rt));
    if (!rt) return NULL;
    rt->carrier = 200.0;
    rt->beat    = 8.0;
    rt->gain    = BFA_AMPLITUDE;
    pthread_mutex_init(&rt->lock, NULL);
    return rt;
}

int rt_audio_start(RtAudio *rt) {
    if (!rt || rt->started) return rt ? 0 : 1;

    if (snd_pcm_open(&rt->pcm, "default", SND_PCM_STREAM_PLAYBACK, 0) < 0)
        return 1;

    unsigned int rate = BFA_SAMPLE_RATE;
    if (snd_pcm_set_params(rt->pcm,
            SND_PCM_FORMAT_S16_LE,
            SND_PCM_ACCESS_RW_INTERLEAVED,
            BFA_CHANNELS,
            rate,
            1,            /* resample 許可 */
            50000) < 0) { /* 約50ms のレイテンシ */
        snd_pcm_close(rt->pcm);
        rt->pcm = NULL;
        return 1;
    }

    rt->running = 1;
    if (pthread_create(&rt->thread, NULL, rt_thread, rt) != 0) {
        rt->running = 0;
        snd_pcm_close(rt->pcm);
        rt->pcm = NULL;
        return 1;
    }
    rt->started = 1;
    return 0;
}

int rt_audio_is_running(const RtAudio *rt) {
    return rt && rt->running;
}

void rt_audio_set_freq(RtAudio *rt, double carrier, double beat) {
    if (!rt) return;
    pthread_mutex_lock(&rt->lock);
    if (carrier > 0) rt->carrier = carrier;
    rt->beat = beat;
    pthread_mutex_unlock(&rt->lock);
}

void rt_audio_set_gain(RtAudio *rt, double gain) {
    if (!rt) return;
    if (gain < 0) gain = 0;
    if (gain > 1) gain = 1;
    pthread_mutex_lock(&rt->lock);
    rt->gain = gain;
    pthread_mutex_unlock(&rt->lock);
}

void rt_audio_stop(RtAudio *rt) {
    if (!rt || !rt->started) return;
    pthread_mutex_lock(&rt->lock);
    rt->running = 0;
    pthread_mutex_unlock(&rt->lock);
    pthread_join(rt->thread, NULL);
    if (rt->pcm) {
        snd_pcm_drain(rt->pcm);
        snd_pcm_close(rt->pcm);
        rt->pcm = NULL;
    }
    rt->started = 0;
}

void rt_audio_destroy(RtAudio *rt) {
    if (!rt) return;
    rt_audio_stop(rt);
    pthread_mutex_destroy(&rt->lock);
    free(rt);
}

#else /* !BFA_HAVE_ALSA — スタブ実装 */

struct RtAudio { int dummy; };

RtAudio *rt_audio_create(void)                 { return NULL; }
int  rt_audio_start(RtAudio *rt)               { (void)rt; return 1; }
int  rt_audio_is_running(const RtAudio *rt)    { (void)rt; return 0; }
void rt_audio_set_freq(RtAudio *rt, double c, double b) { (void)rt; (void)c; (void)b; }
void rt_audio_set_gain(RtAudio *rt, double g)  { (void)rt; (void)g; }
void rt_audio_stop(RtAudio *rt)                { (void)rt; }
void rt_audio_destroy(RtAudio *rt)             { (void)rt; }

#endif /* BFA_HAVE_ALSA */
