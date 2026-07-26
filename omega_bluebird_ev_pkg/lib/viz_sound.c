/* lib/viz_sound.c — sound visualization ("音の映像化").
 *
 * Synthesizes a 16-bit PCM WAV whose partials (frequencies + amplitudes) are
 * derived from the Jones polynomial of the thermal-energy body: the Kauffman
 * bracket sets the fundamental, and the gamma-weighted thermal invariant sets
 * the timbre (overtone spread + tremolo). Also prints an ASCII spectrogram so
 * the sound is "visualized". Plain additive synthesis; the knot invariants
 * only choose the parameters.
 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "../include/omega_bluebird.h"

static void w16(FILE *f, int v){ unsigned char b[2]={v&0xff,(v>>8)&0xff}; fwrite(b,1,2,f); }
static void w32(FILE *f, unsigned v){ unsigned char b[4]={v&0xff,(v>>8)&0xff,(v>>16)&0xff,(v>>24)&0xff}; fwrite(b,1,4,f); }

int ob_visualize_sound(double bracket, double jones_thermal,
                       double seconds, const char *wav_path)
{
    const int sr = 44100;
    if (seconds <= 0) seconds = 2.0;
    int nsamp = (int)(sr * seconds);

    /* Map invariants to synthesis parameters (kept in audible range). */
    double f0     = 110.0 + fmod(fabs(bracket) * 37.0, 550.0);   /* fundamental */
    double spread = 1.0 + fabs(jones_thermal) * 0.5;             /* overtone gap */
    double trem   = 3.0 + fmod(fabs(jones_thermal) * 5.0, 9.0);  /* tremolo Hz   */
    int    npart  = 6;

    short *pcm = malloc(sizeof(short) * (nsamp > 0 ? nsamp : 1));
    if (!pcm) return -1;

    for (int i = 0; i < nsamp; i++) {
        double t = (double)i / sr;
        double env = exp(-1.5 * t / seconds);                    /* decay        */
        double lfo = 0.85 + 0.15 * sin(2 * OB_PI * trem * t);    /* tremolo      */
        double s = 0.0;
        for (int k = 1; k <= npart; k++) {
            double fk = f0 * (1.0 + (k - 1) * spread * 0.5);
            s += (1.0 / k) * sin(2 * OB_PI * fk * t);
        }
        double v = 0.28 * env * lfo * s;
        if (v > 1) v = 1;
        if (v < -1) v = -1;
        pcm[i] = (short)(v * 32767.0);
    }

    if (wav_path) {
        FILE *f = fopen(wav_path, "wb");
        if (!f) { free(pcm); return -2; }
        unsigned data_bytes = (unsigned)nsamp * 2;
        fwrite("RIFF",1,4,f); w32(f, 36 + data_bytes); fwrite("WAVE",1,4,f);
        fwrite("fmt ",1,4,f); w32(f,16); w16(f,1); w16(f,1);
        w32(f,sr); w32(f, sr*2); w16(f,2); w16(f,16);
        fwrite("data",1,4,f); w32(f, data_bytes);
        fwrite(pcm,2,nsamp,f); fclose(f);
    }

    /* ASCII spectrogram: coarse magnitude of the chosen partials over time. */
    printf("sound spectrogram (f0=%.1f Hz, partials=%d, tremolo=%.1f Hz):\n", f0, npart, trem);
    const char *ramp = " .:-=+*#%@";
    int cols = 48, rows = npart;
    for (int k = rows; k >= 1; k--) {
        double fk = f0 * (1.0 + (k - 1) * spread * 0.5);
        printf("%6.0fHz |", fk);
        for (int c = 0; c < cols; c++) {
            double t = (double)c / cols * seconds;
            double env = exp(-1.5 * t / seconds) * (1.0 / k);
            double lfo = 0.85 + 0.15 * sin(2 * OB_PI * trem * t);
            int lvl = (int)(env * lfo * 9.5);
            if (lvl > 9) lvl = 9;
            if (lvl < 0) lvl = 0;
            putchar(ramp[lvl]);
        }
        putchar('\n');
    }
    free(pcm);
    return 0;
}
