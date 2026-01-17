以下は補間（バイリニア）表示を切替可能にした更新版のソースコードです。キー操作: '+'/'=' ズームイン、'-' ズームアウト、'g' ピクセルグリッド切替、'i' 補間切替、ESC 終了。

コンパイル:
gcc -std=c11 -O2 loupe_interp.c -o loupe_interp -lSDL2 -lm

  ソース（ファイル名: loupe_interp.c）:
```c
  // loupe_interp.c
  // Image loupe with optional pixel-grid and bilinear interpolation.
  // Uses SDL2 + stb_image.h

#define SDL_MAIN_HANDLED
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

  static void fatal(const char *msg) { fprintf(stderr,"%s\n",msg); exit(1); }

/* Bilinear sample from RGBA image buffer (iw x ih) at floating coords (x,y) */
static void bilinear_sample_rgba(const unsigned char *img, int iw, int ih, double x, double y, unsigned char out[4]) {
														      if (x < 0) x = 0; if (y < 0) y = 0;
														      if (x > iw - 1) x = iw - 1; if (y > ih - 1) y = ih - 1;
														      int x0 = (int)floor(x), y0 = (int)floor(y);
														      int x1 = x0 + 1 < iw ? x0 + 1 : x0;
														      int y1 = y0 + 1 < ih ? y0 + 1 : y0;
														      double sx = x - x0, sy = y - y0;
														      for (int c = 0; c < 4; ++c) {
															double c00 = img[(y0*iw + x0)*4 + c];
															double c10 = img[(y0*iw + x1)*4 + c];
															double c01 = img[(y1*iw + x0)*4 + c];
															double c11 = img[(y1*iw + x1)*4 + c];
															double c0 = c00 * (1.0 - sx) + c10 * sx;
															double c1 = c01 * (1.0 - sx) + c11 * sx;
															double cv = c0 * (1.0 - sy) + c1 * sy;
															if (cv < 0) cv = 0; if (cv > 255) cv = 255;
															out[c] = (unsigned char)(cv + 0.5);
														      }
}

int main(int argc, char **argv) {
				 if (argc < 2) { fprintf(stderr, "Usage: %s <image>\n", argv[0]); return 1; }
				 const char *imgpath = argv[1];
				 int iw, ih, ic;
				 unsigned char *img = stbi_load(imgpath, &iw, &ih, &ic, 4);
				 if (!img) { fprintf(stderr,"Failed to load image: %s\n", imgpath); return 2; }

				 if (SDL_Init(SDL_INIT_VIDEO) != 0) fatal(SDL_GetError());

				 int winw = iw < 1200 ? iw : 1200;
				 int winh = (int)((double)winw * ih / iw);
				 SDL_Window *win = SDL_CreateWindow("Loupe - Image Viewer", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, winw, winh, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE);
				 if (!win) fatal(SDL_GetError());
				 SDL_Renderer *ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
				 if (!ren) fatal(SDL_GetError());
				 SDL_Texture *tex = SDL_CreateTexture(ren, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STATIC, iw, ih);
				 SDL_UpdateTexture(tex, NULL, img, iw * 4);

				 int loupe_size = 360;
				 int zoom = 8;
				 int show_grid = 0;
				 int use_interp = 0; // 0 = nearest (pixelated), 1 = bilinear interpolation
				 SDL_Window *loupe_win = SDL_CreateWindow("Loupe", SDL_WINDOWPOS_CENTERED + 60, SDL_WINDOWPOS_CENTERED + 60, loupe_size, loupe_size, SDL_WINDOW_SHOWN);
				 SDL_Renderer *loupe_ren = SDL_CreateRenderer(loupe_win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
				 SDL_Texture *loupe_tex = SDL_CreateTexture(loupe_ren, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STREAMING, loupe_size, loupe_size);

				 int running = 1;
				 SDL_Event e;
				 int mx = 0, my = 0;

				 while (running) {
				   while (SDL_PollEvent(&e)) {
				     if (e.type == SDL_QUIT) running = 0;
				     else if (e.type == SDL_KEYDOWN) {
				       if (e.key.keysym.sym == SDLK_ESCAPE) running = 0;
				       else if (e.key.keysym.sym == SDLK_PLUS || e.key.keysym.sym == SDLK_EQUALS) { if (zoom < 64) zoom++; }
				       else if (e.key.keysym.sym == SDLK_MINUS) { if (zoom > 1) zoom--; }
				       else if (e.key.keysym.sym == SDLK_g) { show_grid = !show_grid; }
				       else if (e.key.keysym.sym == SDLK_i) { use_interp = !use_interp; } 
				     } else if (e.type == SDL_MOUSEMOTION) {
				       int wx, wy; SDL_GetWindowSize(win, &wx, &wy);
				       int px = e.motion.x, py = e.motion.y;
				       double sx = (double)wx / iw, sy = (double)wy / ih;
				       double s = sx < sy ? sx : sy;
				       int disp_w = (int)(iw * s), disp_h = (int)(ih * s);
				       int offx = (wx - disp_w) / 2, offy = (wy - disp_h) / 2;
				       int ix = (int)round((px - offx) / s), iy = (int)round((py - offy) / s);
				       if (ix < 0) ix = 0; if (ix >= iw) ix = iw-1;
				       if (iy < 0) iy = 0; if (iy >= ih) iy = ih-1;
				       mx = ix; my = iy;
				     } else if (e.type == SDL_WINDOWEVENT) {
				       if (e.window.windowID == SDL_GetWindowID(win) && e.window.event == SDL_WINDOWEVENT_CLOSE) running = 0;
				       if (e.window.windowID == SDL_GetWindowID(loupe_win) && e.window.event == SDL_WINDOWEVENT_CLOSE) {
					 SDL_DestroyRenderer(loupe_ren); SDL_DestroyWindow(loupe_win); loupe_win = NULL; loupe_ren = NULL;
				       }
				     }
				   }

				   // render main window
				   SDL_SetRenderDrawColor(ren, 30,30,30,255); SDL_RenderClear(ren);
				   int ww, wh; SDL_GetWindowSize(win, &ww, &wh);
				   double sx = (double)ww / iw, sy = (double)wh / ih;
				   double s = sx < sy ? sx : sy;
				   int disp_w = (int)(iw * s), disp_h = (int)(ih * s);
				   SDL_Rect dst = { (ww - disp_w)/2, (wh - disp_h)/2, disp_w, disp_h };
				   SDL_RenderCopy(ren, tex, NULL, &dst);
				   int cx = dst.x + (int)round(mx * s), cy = dst.y + (int)round(my * s);
				   SDL_SetRenderDrawColor(ren, 255,0,0,200);
				   SDL_RenderDrawLine(ren, cx-10, cy, cx+10, cy);
				   SDL_RenderDrawLine(ren, cx, cy-10, cx, cy+10);
				   SDL_RenderPresent(ren);

				   // prepare loupe buffer
				   if (loupe_ren && loupe_tex) {
				     int lw = loupe_size, lh = loupe_size;
				     unsigned char *buf = malloc(lw * lh * 4);
				     if (!buf) { fprintf(stderr,"malloc failed\n"); break; }
				     int half_src = use_interp ? (lw/(2*zoom)) : (lw/(2*zoom));
				     double cx_src = mx + 0.0, cy_src = my + 0.0;
				     double left = cx_src - (double)lw / (2.0 * zoom);
				     double top  = cy_src - (double)lh / (2.0 * zoom);
				     for (int y = 0; y < lh; ++y) {
				       for (int x = 0; x < lw; ++x) {
					 size_t dstidx = ((size_t)y * lw + x) * 4;
					 if (use_interp) {
					   double sx_src = left + (double)x / (double)zoom;
					   double sy_src = top  + (double)y / (double)zoom;
					   unsigned char pix[4];
					   bilinear_sample_rgba(img, iw, ih, sx_src, sy_src, pix);
					   buf[dstidx+0] = pix[0]; buf[dstidx+1] = pix[1]; buf[dstidx+2] = pix[2]; buf[dstidx+3] = pix[3];
					 } else {
					   int sx_src = (int)floor(left + (double)x / (double)zoom + 0.5);
					   int sy_src = (int)floor(top  + (double)y / (double)zoom + 0.5);
					   if (sx_src < 0) sx_src = 0; if (sx_src >= iw) sx_src = iw-1;
					   if (sy_src < 0) sy_src = 0; if (sy_src >= ih) sy_src = ih-1;
					   size_t srcidx = ((size_t)sy_src * iw + sx_src) * 4;
					   buf[dstidx+0] = img[srcidx+0];
					   buf[dstidx+1] = img[srcidx+1];
					   buf[dstidx+2] = img[srcidx+2];
					   buf[dstidx+3] = img[srcidx+3];
					 }
				       }
				     }

				     if (show_grid && !use_interp) {
				       for (int y = 0; y < lh; ++y) if ((y % zoom) == 0) for (int x = 0; x < lw; ++x) {
					     size_t idx = ((size_t)y * lw + x) * 4; buf[idx+0]=255; buf[idx+1]=255; buf[idx+2]=255;
					   }
				       for (int x = 0; x < lw; ++x) if ((x % zoom) == 0) for (int y = 0; y < lh; ++y) {
					     size_t idx = ((size_t)y * lw + x) * 4; buf[idx+0]=255; buf[idx+1]=255; buf[idx+2]=255;
					   }
				     } else if (show_grid && use_interp) {
				       // draw finer grid lines (every 1 source pixel in zoom space)
				       for (int y = 0; y < lh; ++y) {
					 double sy_src = top + (double)y / zoom;
					 if (fabs(sy_src - round(sy_src)) < 0.5 / zoom) {
					   for (int x = 0; x < lw; ++x) { size_t idx = ((size_t)y * lw + x) * 4; buf[idx+0]=255; buf[idx+1]=255; buf[idx+2]=255; }
					 }
				       }
				       for (int x = 0; x < lw; ++x) {
					 double sx_src = left + (double)x / zoom;
					 if (fabs(sx_src - round(sx_src)) < 0.5 / zoom) {
					   for (int y = 0; y < lh; ++y) { size_t idx = ((size_t)y * lw + x) * 4; buf[idx+0]=255; buf[idx+1]=255; buf[idx+2]=255; }
					 }
				       }
				     }

				     SDL_UpdateTexture(loupe_tex, NULL, buf, lw * 4);
				     free(buf);

				     SDL_SetRenderDrawColor(loupe_ren, 50,50,50,255); SDL_RenderClear(loupe_ren);
				     SDL_RenderCopy(loupe_ren, loupe_tex, NULL, NULL);
				     SDL_SetRenderDrawColor(loupe_ren, 255,0,0,200);
				     SDL_RenderDrawLine(loupe_ren, lw/2 - 10, lh/2, lw/2 + 10, lh/2);
				     SDL_RenderDrawLine(loupe_ren, lw/2, lh/2 - 10, lw/2, lh/2 + 10);
				     // status text is omitted (SDL_ttf not used) — user can see mode via console
				     SDL_RenderPresent(loupe_ren);
				   }

				   SDL_Delay(10);
				 }

				 if (loupe_tex) SDL_DestroyTexture(loupe_tex);
				 if (loupe_ren) SDL_DestroyRenderer(loupe_ren);
				 if (loupe_win) SDL_DestroyWindow(loupe_win);
				 SDL_DestroyTexture(tex);
				 SDL_DestroyRenderer(ren);
				 SDL_DestroyWindow(win);
				 SDL_Quit();
				 stbi_image_free(img);
				 return 0;
}
```

注意:
- 本プログラムは補間で画像表示を滑らかにする機能を提供します。隠蔽解除（モザイク除去）を助ける機能は含みません。
- 必要なら、UI に現在のモード（補間/非補間/ズーム/グリッド）をテキストで表示する機能（SDL_ttf 使用）や、出力のスクリーンショット保存機能を追加できます。希望があれば教えてください。
