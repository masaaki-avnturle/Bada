// silent_talk_auto.c
// Ubuntu (Linux) 実装:
// - V4L2 赤外線カメラ（Y16想定）で大域的部分積分風の熱指標を算出
// - 指標が閾値を越えると「聞き取り開始」→定型テキストをエディタへ自動入力（xdotool を使用）
// - 指標が下がると「聞き取り停止」して自動入力を停止
// 注意:
// - 実機のカメラのフォーマット/スケールに合わせて TEMP_SCALE/TEMP_OFFSET を調整してください。
// - xdotool を事前にインストールしてください: sudo apt install xdotool
// コンパイル: gcc -O2 silent_talk_auto.c -o silent_talk_auto -lm
// 実行例: ./silent_talk_auto /dev/video0

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/select.h>
#include <linux/videodev2.h>

#define FRAME_WIDTH 160
#define FRAME_HEIGHT 120
#define SAMPLE_INTERVAL_MS 200
#define BASELINE_TEMP 36.5

// カメラ生データ->摂氏変換係数（要調整）
#define TEMP_SCALE 0.01
#define TEMP_OFFSET 0.0

// 閾値（要実環境で調整）
// energy は manifold_energy_metric の出力（小さな正負値）
#define LISTEN_START_THRESHOLD 0.08
#define LISTEN_STOP_THRESHOLD 0.05

// 自動入力する文字列（用途に応じて編集）
static const char *AUTO_TEXT =
    "Listening started. Detected increased thermal activity.\n"
  "Transcribing predefined message...\n";

// V4L2 バッファ
struct buffer { void *start; size_t length; };

// タイムスタンプ
static const char *timestamp() {
  static char buf[64];
  struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts);
  struct tm tm; localtime_r(&ts.tv_sec, &tm);
  snprintf(buf, sizeof(buf), "%04d-%02d-%02d %02d:%02d:%02d.%03ld",
	   tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday,
	   tm.tm_hour, tm.tm_min, tm.tm_sec, ts.tv_nsec/1000000);
  return buf;
}

// sysfs CPU/SoC 温度読み取り（フォールバック）
double read_pc_temp_sys() {
  FILE *f=NULL; char path[256];
  for (int i=0;i<8;++i) {
    snprintf(path,sizeof(path),"/sys/class/thermal/thermal_zone%d/temp",i);
    f = fopen(path,"r"); if (!f) continue;
    long v=0; if (fscanf(f,"%ld",&v)==1) { fclose(f); if (v>1000) return v/1000.0; return (double)v; }
    fclose(f);
  }
  return NAN;
}

// V4L2 open/stream on
int v4l2_open_device(const char *dev, int *out_fd, struct buffer **out_bufs, unsigned int *out_nbufs) {
  int fd = open(dev, O_RDWR | O_NONBLOCK, 0); if (fd < 0) return -1;
  struct v4l2_format fmt; memset(&fmt,0,sizeof(fmt));
  fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  fmt.fmt.pix.width = FRAME_WIDTH; fmt.fmt.pix.height = FRAME_HEIGHT;
  fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_Y16; fmt.fmt.pix.field = V4L2_FIELD_NONE;
  ioctl(fd, VIDIOC_S_FMT, &fmt); // ignore error, try to proceed
  struct v4l2_requestbuffers req; memset(&req,0,sizeof(req));
  req.count = 4; req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; req.memory = V4L2_MEMORY_MMAP;
  if (ioctl(fd, VIDIOC_REQBUFS, &req) < 0) { close(fd); return -1; }
  struct buffer *bufs = calloc(req.count, sizeof(*bufs));
  for (unsigned int i=0;i<req.count;++i) {
    struct v4l2_buffer buf; memset(&buf,0,sizeof(buf));
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; buf.memory = V4L2_MEMORY_MMAP; buf.index = i;
    if (ioctl(fd, VIDIOC_QUERYBUF, &buf) < 0) { /*cleanup*/ }
    bufs[i].length = buf.length;
    bufs[i].start = mmap(NULL, buf.length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, buf.m.offset);
  }
  for (unsigned int i=0;i<req.count;++i) { struct v4l2_buffer buf; memset(&buf,0,sizeof(buf)); buf.type=V4L2_BUF_TYPE_VIDEO_CAPTURE; buf.memory=V4L2_MEMORY_MMAP; buf.index=i; ioctl(fd, VIDIOC_QBUF, &buf); }
  enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE; ioctl(fd, VIDIOC_STREAMON, &type);
  *out_fd = fd; *out_bufs = bufs; *out_nbufs = req.count;
  return 0;
}

void v4l2_close_device(int fd, struct buffer *bufs, unsigned int nbufs) {
  enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE; ioctl(fd, VIDIOC_STREAMOFF, &type);
  for (unsigned int i=0;i<nbufs;++i) if (bufs[i].start) munmap(bufs[i].start, bufs[i].length);
  free(bufs); close(fd);
}

// フレーム取得 -> 温度行列 (malloc, caller free)
double *v4l2_capture_frame_to_temps(int fd, struct buffer *bufs) {
  fd_set fds; struct timeval tv; FD_ZERO(&fds); FD_SET(fd,&fds); tv.tv_sec=2; tv.tv_usec=0;
  int r = select(fd+1, &fds, NULL, NULL, &tv); if (r<=0) return NULL;
  struct v4l2_buffer buf; memset(&buf,0,sizeof(buf)); buf.type=V4L2_BUF_TYPE_VIDEO_CAPTURE; buf.memory=V4L2_MEMORY_MMAP;
  if (ioctl(fd, VIDIOC_DQBUF, &buf) < 0) return NULL;
  void *data = bufs[buf.index].start;
  double *temps = malloc(sizeof(double) * FRAME_WIDTH * FRAME_HEIGHT);
  uint16_t *pix = (uint16_t*)data;
  for (int y=0;y<FRAME_HEIGHT;++y) for (int x=0;x<FRAME_WIDTH;++x) {
      int idx = y*FRAME_WIDTH + x; uint16_t raw = pix[idx];
      temps[idx] = raw * TEMP_SCALE + TEMP_OFFSET;
    }
  ioctl(fd, VIDIOC_QBUF, &buf);
  return temps;
}

// 大域的部分積分風集約
double global_partial_integral_from_temps(const double *t) {
  double sum=0.0, wsum=0.0; int cx=FRAME_WIDTH/2, cy=FRAME_HEIGHT/2;
  for (int y=0;y<FRAME_HEIGHT;++y) for (int x=0;x<FRAME_WIDTH;++x) {
      int idx=y*FRAME_WIDTH+x; double dx=(double)(x-cx), dy=(double)(y-cy);
      double r=sqrt(dx*dx+dy*dy)+1.0; double weight=exp(-r/30.0);
      sum += t[idx]*weight; wsum += weight;
    }
  return (wsum==0.0)?0.0:(sum/wsum);
}

// 多様体エネルギー指標（簡易）
double manifold_energy_metric(double global_integral, double pc_temp) {
  double a=1.2, b=0.8; return a*(global_integral - BASELINE_TEMP) + b*(pc_temp - BASELINE_TEMP);
}

// xdotool でテキスト入力（非同期に大きなテキストを一気に送る際は遅延をいれる）
void send_text_via_xdotool(const char *text) {
  // xdotool type を使う。長文の場合は適宜分割して送る。
  // snprintf により生成したコマンドは /bin/sh 経由で実行されるので注意。
  char *esc = NULL;
  // 最小限のエスケープ: シングルクオートで囲むため内部のシングルクォートを '\'' に置換
  size_t in_len = strlen(text);
  esc = malloc(in_len*4 + 32);
  char *p = esc; *p = 0;
  strcat(p, "xdotool type --delay 10 -- '");
  p += strlen(p);
  for (size_t i=0;i<in_len;++i) {
    char c = text[i];
    if (c == '\'') { strcat(p, "'\\''"); p += 4; }
    else { *p++ = c; *p = 0; }
  }
  strcat(p, "' &");
  // 実行
  system(esc);
  free(esc);
}

// 小さなメッセージ（行）を送る（即時）
void send_short_line(const char *line) {
  char cmd[256];
  snprintf(cmd,sizeof(cmd),"xdotool type --delay 5 -- '%s' &", line);
  system(cmd);
}

int main(int argc, char **argv) {
  const char *dev = "/dev/video0";
  if (argc >= 2) dev = argv[1];
  int fd; struct buffer *bufs = NULL; unsigned int nbufs = 0;
  if (v4l2_open_device(dev, &fd, &bufs, &nbufs) != 0) {
    fprintf(stderr,"%s ERROR: open v4l2 device %s failed: %s\n", timestamp(), dev, strerror(errno));
    return 1;
  }
  printf("%s started. device=%s\n", timestamp(), dev);

  enum { STATE_IDLE=0, STATE_LISTENING=1, STATE_INPUTTING=2 } state = STATE_IDLE;
  double last_energy = 0.0;

  for (;;) {
    double pc_temp = read_pc_temp_sys(); if (isnan(pc_temp)) pc_temp = BASELINE_TEMP;
    double *temps = v4l2_capture_frame_to_temps(fd, bufs);
    if (!temps) { usleep(SAMPLE_INTERVAL_MS*1000); continue; }
    double gint = global_partial_integral_from_temps(temps);
    double energy = manifold_energy_metric(gint, pc_temp);
    free(temps);

    // 状態遷移: 閾値に基づくヒューリスティック
    if (state == STATE_IDLE) {
      if (energy >= LISTEN_START_THRESHOLD) {
	state = STATE_LISTENING;
	printf("[%s] -> LISTENING (energy=%.4f)\n", timestamp(), energy);
	send_short_line("[silent_talk] Listening started...\n");
      }
    } else if (state == STATE_LISTENING) {
      if (energy >= LISTEN_START_THRESHOLD * 1.2) {
	// 明確な入力開始を検出したら自動入力（非同期）
	state = STATE_INPUTTING;
	printf("[%s] -> INPUTTING (energy=%.4f)\n", timestamp(), energy);
	// 自動入力（長文）をxdotoolで非同期に送る
	send_text_via_xdotool(AUTO_TEXT);
      } else if (energy < LISTEN_STOP_THRESHOLD) {
	state = STATE_IDLE;
	printf("[%s] -> IDLE (energy=%.4f)\n", timestamp(), energy);
	send_short_line("[silent_talk] Listening stopped.\n");
      }
    } else if (state == STATE_INPUTTING) {
      // 入力中もエネルギー低下で停止
      if (energy < LISTEN_STOP_THRESHOLD) {
	state = STATE_IDLE;
	printf("[%s] INPUTTING -> IDLE (energy=%.4f)\n", timestamp(), energy);
	send_short_line("[silent_talk] Input stopped.\n");
      } else {
	// まだ高い: 継続（何もしない）
      }
    }

    last_energy = energy;
    usleep(SAMPLE_INTERVAL_MS * 1000);
  }

  v4l2_close_device(fd, bufs, nbufs);
  return 0;
}
