/* lib/viz_env.c — environment visualization ("周りの映像化").
 *
 * Renders a top-down driving scene to a binary PPM image and an ASCII preview.
 * The scene's texture (road shading, lane cadence, obstacle placement) is
 * modulated by the gamma-manifold entropy invariant, so a higher-entropy
 * surroundings produces a busier image. Ordinary rasterization; the invariant
 * only chooses parameters.
 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "../include/omega_bluebird.h"

int ob_visualize_env(const ManifoldEntropy *me, const BluebirdState *s,
                     int w, int h, const char *ppm_path)
{
    if (w < 16) w = 160;
    if (h < 16) h = 90;
    unsigned char *img = malloc((size_t)w * h * 3);
    if (!img) return -1;

    double xi   = me->invariant;
    double busy = me->entropy / 8.0;                 /* 0..1 texture density */
    double lane = w * (0.5 + 0.15 * s->lane_offset_m); /* ego lane center x  */
    int    obst_y = (int)(h * (1.0 - s->obstacle_dist_m / 60.0));

    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            unsigned char *px = img + ((size_t)y * w + x) * 3;
            double dx = fabs(x - lane) / (double)w;
            /* asphalt base darkened toward road center, sky-ish at edges */
            int road = dx < 0.28;
            double n = 0.5 + 0.5 * sin((x * 0.13 + y * 0.07) * (1.0 + 3.0 * xi));
            if (road) {
                unsigned char g = (unsigned char)(40 + 60 * busy * n);
                px[0] = g; px[1] = g; px[2] = (unsigned char)(g + 10);
                /* dashed lane markings cadence set by the manifold integral */
                int period = 6 + (int)(10 * me->manifold_integral);
                if (period < 3) period = 3;
                if (fabs(dx) < 0.01 && ((y / period) % 2 == 0)) { px[0]=px[1]=px[2]=230; }
            } else {
                px[0] = (unsigned char)(30 + 50 * n);
                px[1] = (unsigned char)(90 + 90 * n * busy);
                px[2] = (unsigned char)(40 + 40 * n);
            }
            /* obstacle marker */
            if (s->obstacle_ahead && abs(y - obst_y) < 3 && fabs(x - lane) < 6) {
                px[0] = 220; px[1] = 40; px[2] = 40;
            }
        }
    }

    if (ppm_path) {
        FILE *f = fopen(ppm_path, "wb");
        if (!f) { free(img); return -2; }
        fprintf(f, "P6\n%d %d\n255\n", w, h);
        fwrite(img, 1, (size_t)w * h * 3, f);
        fclose(f);
    }

    /* ASCII preview to stdout (downsampled) */
    const char *ramp = " .:-=+*#%@";
    int aw = 60, ah = 20;
    printf("environment map (Xi=%.4f, H=%.3f):\n", xi, me->entropy);
    for (int y = 0; y < ah; y++) {
        for (int x = 0; x < aw; x++) {
            int sx = x * w / aw, sy = y * h / ah;
            unsigned char *px = img + ((size_t)sy * w + sx) * 3;
            int lum = (px[0] + px[1] + px[2]) / 3;
            if (px[0] > 180 && px[1] < 90) putchar('X');      /* obstacle */
            else putchar(ramp[lum * 9 / 255]);
        }
        putchar('\n');
    }
    free(img);
    return 0;
}
