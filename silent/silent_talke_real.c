// silent_talk_real.c
// Ubuntu Linux 実装版（/sys/class/thermal と V4L2 対応赤外線カメラを使用）
// ※ 赤外線カメラが /dev/videoN に接続され、ピクセルフォーマットが 16-bit depth (Y16 等) を提供することを想定。
//   実機のドライバ/カメラによって生データのスケールが異なるため、TEMP_SCALE を環境に合わせて調整してください.
// コンパイル例: gcc -O2 silent_talk_real.c -o silent_talk_real -lm

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <errno.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>

#define FRAME_WIDTH 160
#define FRAME_HEIGHT 120
#define SAMPLE_INTERVAL_MS 200
#define BASELINE_TEMP 36.5
#define ZETA_TERMS 2000

// カメラデータを温度 (摂氏) に変換する係数(カメラに応じて変更)
#define TEMP_SCALE 0.01   // 例: カメラ生データ * 0.01 -> Celsius
#define TEMP_OFFSET 0.0   // 必要ならオフセット

// V4L2 バッファ構造
struct buffer {
  void   *start;
  size_t  length;
};

static const char *timestamp() {
  static char buf[64];
  struct timespec ts;
  clock_gettime(CLOCK_REALTIME, &ts);
  struct tm tm;
  localtime_r(&ts.tv_sec, &tm);
  snprintf(buf, sizeof(buf), "%04d-%02d-%02d %02d:%02d:%02d.%03ld",
	   tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday,
	   tm.tm_hour, tm.tm_min, tm.tm_sec,
	   ts.tv_nsec/1000000);
  return buf;
}

// ---------------- sys thermal (Linux) ----------------
double read_pc_temp_sys() {
  // thermal_zone* を順に探して first valid を返す
  FILE *f = NULL;
  char path[256];
  for (int i = 0; i < 8; ++i) {
    snprintf(path, sizeof(path), "/sys/class/thermal/thermal_zone%d/temp", i);
    f = fopen(path, "r");
    if (!f) continue;
    long val = 0;
    if (fscanf(f, "%ld", &val) == 1) {
      fclose(f);
      // 多くのシステムはミリ度 (milli°C)
      if (val > 1000) return val / 1000.0;
      return (double)val;
    }
    fclose(f);
  }
  return NAN;
}

// ---------------- V4L2 カメラ読取 (Y16想定) ----------------
int v4l2_open_device(const char *dev, int *fd, struct buffer **out_bufs, unsigned int *out_nbufs, int *w, int *h) {
  int r;
  struct v4l2_format fmt;
  struct v4l2_requestbuffers req;
  struct buffer *buffers = NULL;

  *fd = open(dev, O_RDWR | O_NONBLOCK, 0);
  if (*fd < 0) return -1;

  memset(&fmt, 0, sizeof(fmt));
  fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  // try to set format; many thermal cams supply Y16 or GREY16_BE
  fmt.fmt.pix.width = FRAME_WIDTH;
  fmt.fmt.pix.height = FRAME_HEIGHT;
  fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_Y16; // try Y16
  fmt.fmt.pix.field = V4L2_FIELD_NONE;
  r = ioctl(*fd, VIDIOC_S_FMT, &fmt);
  if (r < 0) {
    // fallback: query format
    if (ioctl(*fd, VIDIOC_G_FMT, &fmt) < 0) { close(*fd); return -1; }
  }
  *w = fmt.fmt.pix.width; *h = fmt.fmt.pix.height;

  memset(&req, 0, sizeof(req));
  req.count = 4;
  req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  req.memory = V4L2_MEMORY_MMAP;
  if (ioctl(*fd, VIDIOC_REQBUFS, &req) < 0) { close(*fd); return -1; }

  buffers = calloc(req.count, sizeof(*buffers));
  for (unsigned int i = 0; i < req.count; ++i) {
    struct v4l2_buffer buf;
    memset(&buf, 0, sizeof(buf));
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;
    buf.index = i;
    if (ioctl(*fd, VIDIOC_QUERYBUF, &buf) < 0) { free(buffers); close(*fd); return -1; }
    buffers[i].length = buf.length;
    buffers[i].start = mmap(NULL, buf.length, PROT_READ | PROT_WRITE, MAP_SHARED, *fd, buf.m.offset);
    if (buffers[i].start == MAP_FAILED) { for (unsigned int j=0;j<i;++j) munmap(buffers[j].start, buffers[j].length); free(buffers); close(*fd); return -1; }
  }
  // enqueue
  for (unsigned int i = 0; i < req.count; ++i) {
    struct v4l2_buffer buf;
    memset(&buf, 0, sizeof(buf));
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;
    buf.index = i;
    if (ioctl(*fd, VIDIOC_QBUF, &buf) < 0) { /* continue */ }
  }
  // start
  enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  if (ioctl(*fd, VIDIOC_STREAMON, &type) < 0) { /* continue */ }

  *out_bufs = buffers;
  *out_nbufs = req.count;
  return 0;
}

void v4l2_close_device(int fd, struct buffer *buffers, unsigned int nbufs) {
  enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  ioctl(fd, VIDIOC_STREAMOFF, &type);
  for (unsigned int i = 0; i < nbufs; ++i) if (buffers[i].start) munmap(buffers[i].start, buffers[i].length);
  free(buffers);
  close(fd);
}

// ブロッキングで次フレームを取得、Y16 -> 温度行列に変換（row-major double配列、caller が free する）
double *v4l2_capture_frame_to_temps(int fd, struct buffer *buffers) {
  struct v4l2_buffer buf;
  fd_set fds;
  struct timeval tv;
  int r;
  FD_ZERO(&fds);
  FD_SET(fd, &fds);
  tv.tv_sec = 2;
  tv.tv_usec = 0;
  r = select(fd+1, &fds, NULL, NULL, &tv);
  if (r <= 0) return NULL;
  memset(&buf, 0, sizeof(buf));
  buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  buf.memory = V4L2_MEMORY_MMAP;
  if (ioctl(fd, VIDIOC_DQBUF, &buf) < 0) return NULL;
  // buf.index 指定のバッファを参照
  void *data = buffers[buf.index].start;
  size_t bytes = buf.bytesused;
  // assume 16-bit per pixel, FRAME_WIDTH*FRAME_HEIGHT*2 <= bytes
  size_t expected = FRAME_WIDTH * FRAME_HEIGHT * 2;
  double *temps = malloc(sizeof(double) * FRAME_WIDTH * FRAME_HEIGHT);
  if (!temps) { ioctl(fd, VIDIOC_QBUF, &buf); return NULL; }
  // interpret as uint16_t little-endian (driver dependent)
  uint16_t *pix = (uint16_t*)data;
  for (int y=0;y<FRAME_HEIGHT;++y) {
    for (int x=0;x<FRAME_WIDTH;++x) {
      int idx = y*FRAME_WIDTH + x;
      uint16_t raw = pix[idx];
      double t = raw * TEMP_SCALE + TEMP_OFFSET;
      temps[idx] = t;
    }
  }
  ioctl(fd, VIDIOC_QBUF, &buf);
  return temps;
}

// ----------------- 数学・処理（前の実装を簡易移植） -----------------
double gamma_approx(double x) {
  if (x <= 0.0) return NAN;
  const double pi = 3.14159265358979323846;
  return sqrt(2.0*pi/x) * pow(x/M_E, x);
}
double zeta_approx(double s, int terms) {
  double sum = 0.0;
  for (int n = 1; n <= terms; ++n) sum += 1.0 / pow((double)n, s);
  return sum;
}
double global_partial_integral_from_temps(const double *temps) {
  double sum=0.0, wsum=0.0;
  int cx = FRAME_WIDTH/2, cy = FRAME_HEIGHT/2;
  for (int y=0;y<FRAME_HEIGHT;++y) for (int x=0;x<FRAME_WIDTH;++x) {
      int idx = y*FRAME_WIDTH + x;
      double dx = (double)(x-cx), dy=(double)(y-cy);
      double r = sqrt(dx*dx + dy*dy) + 1.0;
      double weight = exp(-r/30.0);
      sum += temps[idx]*weight;
      wsum += weight;
    }
  if (wsum==0.0) return 0.0;
  return sum/wsum;
}
double manifold_energy_metric(double global_integral, double pc_temp) {
  double a=1.2, b=0.8;
  return a*(global_integral - BASELINE_TEMP) + b*(pc_temp - BASELINE_TEMP);
}
char *generate_silent_message(double energy) {
  char *buf = malloc(64);
  if (!buf) return NULL;
  if (isnan(energy)) { strcpy(buf,"ERR"); return buf; }
  int level = (int)round(fabs(energy)*10.0);
  if (level>10) level=10;
  if (energy > 0.05) snprintf(buf,64,"MSG+%d", level);
  else if (energy < -0.05) snprintf(buf,64,"MSG-%d", level);
  else snprintf(buf,64,"MSG0");
  return buf;
}

// ---------------- main ----------------
int main(int argc, char **argv) {
  const char *video_dev = "/dev/video0";
  if (argc >= 2) video_dev = argv[1];

  int fd = -1;
  struct buffer *bufs = NULL;
  unsigned int nb = 0;
  int w=0,h=0;

  if (v4l2_open_device(video_dev, &fd, &bufs, &nb, &w, &h) != 0) {
    fprintf(stderr, "%s ERROR: cannot open video device %s (%s)\n", timestamp(), video_dev, strerror(errno));
    return 1;
  }

  FILE *outf = fopen("silent_talk_out.txt", "w");
  if (!outf) outf = stdout;

  printf("%s silent_talk_real starting; device=%s (%dx%d)\n", timestamp(), video_dev, w, h);

  for (;;) {
    // PC 温度
    double pc_temp = read_pc_temp_sys();
    if (isnan(pc_temp)) pc_temp = BASELINE_TEMP;

    // IR フレーム -> 温度行列
    double *temps = v4l2_capture_frame_to_temps(fd, bufs);
    if (!temps) {
      fprintf(stderr, "%s WARN: failed to capture frame\n", timestamp());
      usleep(SAMPLE_INTERVAL_MS * 1000);
      continue;
    }

    // 大域的部分積分的集約
    double gint = global_partial_integral_from_temps(temps);

    // 補助: gamma / zeta
    double gamma_v = gamma_approx(1.5);
    double zeta_v = zeta_approx(1.5, ZETA_TERMS);

    double energy = manifold_energy_metric(gint, pc_temp);
    char *msg = generate_silent_message(energy);

    // ログ
    char line[512];
    snprintf(line, sizeof(line), "pc_temp=%.3f gint=%.6f energy=%.6f msg=%s gamma~%.6f zeta~%.6f",
	     pc_temp, gint, energy, msg ? msg : "NULL", gamma_v, zeta_v);
    printf("[%s] %s\n", timestamp(), line);
    if (outf) { fprintf(outf, "%s\n", msg ? msg : "ERR"); fflush(outf); }

    free(msg);
    free(temps);

    usleep(SAMPLE_INTERVAL_MS * 1000);
  }

  v4l2_close_device(fd, bufs, nb);
  return 0;
}
