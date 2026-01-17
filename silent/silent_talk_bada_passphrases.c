/*以下は、提示された Bada/Omega レポートの構文要素（予約語・クラス/メソッド名候補・分岐／合流／代入記号・配列代入など）を抽出して合い言葉リストを自動生成し、その合い言葉で一時許可を与えた場合にコードスニペットをフォーカス中のエディタへ自動挿入する C アプリケーションです。基本動作は以前の `silent_talk_code_injector` 系と同様です。

- 合い言葉候補はソース中の配列に列挙（レポート中に現れる「Omega::DATABASE」「tuplespace」「VIRTUALMACHINE」等に加え、抽出した構文要素群を多数追加）。
- stdin に合い言葉（配列内のいずれか）を送ると一回分の許可になり、次の熱検出で現在言語のスニペットを挿入します。
- stdin コマンド: 合い言葉をそのまま送る（例: Omega::DATABASE）、lang:c / lang:py（言語切替）、inject（手動注入）、lock（無効化）。
- Xorg 環境、xdotool 必須、カメラ Y16 想定。

保存例: `silent_talk_bada_passphrases.c`  
コンパイル:
gcc -O2 silent_talk_bada_passphrases.c -o silent_talk_bada_passphrases -lpthread -lm

ソースコード:
```c
*/
// silent_talk_bada_passphrases.c
// V4L2 + xdotool: Bada/Omega レポートから抽出した構文要素を合い言葉候補として内蔵。
// SEND a passphrase (exact match) via stdin to enable one-shot insertion when thermal detection triggers.
// Commands via stdin:
//   <passphrase>    -- enable one-shot if matches candidate list
//   lang:c / lang:py -- choose snippet language
//   inject          -- manual immediate inject
//   lock            -- clear permit
// Compile: gcc -O2 silent_talk_bada_passphrases.c -o injector -lpthread -lm

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>
#include <sys/select.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/videodev2.h>

#define FRAME_W 160
#define FRAME_H 120
#define SAMPLE_MS 200
#define TEMP_SCALE 0.01
#define TEMP_OFFSET 0.0
#define BASE_TEMP 36.5
#define START_TH 0.08
#define STOP_TH 0.05

struct buffer { void *start; size_t length; };

// --- Derived passphrase set from Bada/Omega report ---
// Reserved-like tokens, class/method names, operators, arrows, assignment symbols, etc.
static const char *bada_tokens[] = {
				    /* core names */
				    "Omega::DATABASE", "Omega.TUPLESPACE", "tuplespace", "VIRTUALMACHINE", "VIRTUAL_MACHINE",
				    "ultranetwork", "virtual_connect", "emerge_equation", "assembly_process", "cognitive_system",
				    "regexpt.pattern", "w.emerged", "value.equation_create", "repository.reload",

				    /* class/method identifiers observed */
				    "UltraNetwork::DATABASE", "Ultranetwork", "virtual_connect", "load_file", "virtual_machine",
				    "startx", "launcher_application", "network_rout", "kterm_port", "main_loop", "iterator",
				    "emerge_equation", "rebuild", "reload", "import", "export", "attach", "attachment",

				    /* operators / arrows / symbols */
				    "=>", "->", ">-", ">>", "<-", "<=>", ":=>", "::", "::=", "==>", "=>:", "=<", "<->",

				    /* assignment / special tokens */
				    ":=", ".emerge_equation.reality", ".reload", ".recreated", ".included", ".excluded",

				    /* math / manifold tokens */
				    "nabla", "Delta", "partial", "otimes", "oplus", "bigoplus", "bigotimes",

				    /* DSL-like keywords */
				    "def", "class", "import", "typedef", "struct", "end", "mainloop", "main_loop", "if", "else", "elsif",

				    /* other notable tokens */
				    "Omega.DATABASE", "Omega::Tuplespace", "omegatuple", "pholograph_data", "tuplespace[process.excluded]"
};
static const int NUM_TOKENS = sizeof(bada_tokens)/sizeof(bada_tokens[0]);

// --- injector state ---
enum { LANG_C=0, LANG_PY=1 };
static volatile int allowed = 0;
static volatile int manual_inject = 0;
static int chosen_lang = LANG_C;

// V4L2 buffers
static struct buffer *vbufs = NULL;
static unsigned int vnbufs = 0;
static int vfd = -1;

static const char *ts() {
  static char b[64];
  struct timespec t; clock_gettime(CLOCK_REALTIME,&t);
  struct tm m; localtime_r(&t.tv_sec,&m);
  snprintf(b,sizeof(b),"%04d-%02d-%02d %02d:%02d:%02d",
	   m.tm_year+1900,m.tm_mon+1,m.tm_mday,m.tm_hour,m.tm_min,m.tm_sec);
  return b;
}

// minimal V4L2 open (Y16)
int v4l2_open_dev(const char *dev, int *out_fd, struct buffer **out_bufs, unsigned int *out_n) {
  int fd = open(dev, O_RDWR | O_NONBLOCK, 0); if (fd<0) return -1;
  struct v4l2_format fmt; memset(&fmt,0,sizeof(fmt));
  fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; fmt.fmt.pix.width = FRAME_W; fmt.fmt.pix.height = FRAME_H;
  fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_Y16; fmt.fmt.pix.field = V4L2_FIELD_NONE;
  ioctl(fd, VIDIOC_S_FMT, &fmt);
  struct v4l2_requestbuffers req; memset(&req,0,sizeof(req));
  req.count = 4; req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; req.memory = V4L2_MEMORY_MMAP;
  if (ioctl(fd, VIDIOC_REQBUFS, &req) < 0) { close(fd); return -1; }
  struct buffer *bufs = calloc(req.count, sizeof(*bufs));
  for (unsigned int i=0;i<req.count;i++) {
    struct v4l2_buffer b; memset(&b,0,sizeof(b));
    b.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; b.memory = V4L2_MEMORY_MMAP; b.index = i;
    if (ioctl(fd, VIDIOC_QUERYBUF, &b) < 0) continue;
    bufs[i].length = b.length;
    bufs[i].start = mmap(NULL, b.length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, b.m.offset);
  }
  for (unsigned int i=0;i<req.count;i++) { struct v4l2_buffer b; memset(&b,0,sizeof(b)); b.type=req.type; b.memory=V4L2_MEMORY_MMAP; b.index=i; ioctl(fd, VIDIOC_QBUF, &b); }
  enum v4l2_buf_type t = V4L2_BUF_TYPE_VIDEO_CAPTURE; ioctl(fd, VIDIOC_STREAMON, &t);
  *out_fd = fd; *out_bufs = bufs; *out_n = req.count;
  return 0;
}
void v4l2_close_dev(int fd, struct buffer *bufs, unsigned int n) {
  enum v4l2_buf_type t = V4L2_BUF_TYPE_VIDEO_CAPTURE; ioctl(fd, VIDIOC_STREAMOFF, &t);
  for (unsigned int i=0;i<n;i++) if (bufs[i].start) munmap(bufs[i].start, bufs[i].length);
  free(bufs); close(fd);
}

double *capture_temps(int fd, struct buffer *bufs) {
  fd_set fds; struct timeval tv; FD_ZERO(&fds); FD_SET(fd,&fds); tv.tv_sec=2; tv.tv_usec=0;
  if (select(fd+1,&fds,NULL,NULL,&tv) <= 0) return NULL;
  struct v4l2_buffer b; memset(&b,0,sizeof(b));
  b.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; b.memory = V4L2_MEMORY_MMAP;
  if (ioctl(fd, VIDIOC_DQBUF, &b) < 0) return NULL;
  void *data = bufs[b.index].start;
  double *t = malloc(sizeof(double)*FRAME_W*FRAME_H);
  if (!t) { ioctl(fd, VIDIOC_QBUF, &b); return NULL; }
  uint16_t *pix = (uint16_t*)data;
  for (int i=0;i<FRAME_W*FRAME_H;i++) t[i] = pix[i]*TEMP_SCALE + TEMP_OFFSET;
  ioctl(fd, VIDIOC_QBUF, &b);
  return t;
}
double global_metric(const double *t) {
  double sum=0, wsum=0; int cx=FRAME_W/2, cy=FRAME_H/2;
  for (int y=0;y<FRAME_H;y++) for (int x=0;x<FRAME_W;x++) {
      int idx=y*FRAME_W+x; double dx=x-cx, dy=y-cy;
      double r = sqrt(dx*dx+dy*dy)+1.0; double w = exp(-r/30.0);
      sum += t[idx]*w; wsum += w;
    }
  return (wsum==0)?0:(sum/wsum);
}
double read_pc_temp_sys() {
  FILE *f; char p[128];
  for (int i=0;i<8;i++) { snprintf(p,sizeof(p),"/sys/class/thermal/thermal_zone%d/temp",i); f=fopen(p,"r"); if(!f) continue; long v; if(fscanf(f,"%ld",&v)==1){ fclose(f); if(v>1000) return v/1000.0; return (double)v;} fclose(f); }
  return NAN;
}
double energy_metric(double gint, double pc) { double a=1.2,b=0.8; return a*(gint-BASE_TEMP)+b*(pc-BASE_TEMP); }

// xdotool helper (escape single quotes)
void xdotool_type(const char *text) {
  size_t n=strlen(text); char *cmd = malloc(n*4 + 128);
  if (!cmd) return;
  strcpy(cmd,"xdotool type --delay 5 -- '");
  for (size_t i=0;i<n;i++) {
    if (text[i]=='\'') strcat(cmd,"'\\''");
    else { size_t l=strlen(cmd); cmd[l]=text[i]; cmd[l+1]=0; }
  }
  strcat(cmd,"' &");
  system(cmd); free(cmd);
}

// snippets (C and Python) - can be extended or made configurable
const char *snippet_c = "#include <stdin.h>\nint x, y;\n// Omega-derived snippet\n";
const char *snippet_py = "# Omega-derived snippet\nx = None\ny = None\n";

// build the passphrase lookup: include bada_tokens plus explicit structural tokens
// simple stdin thread: accept passphrase, lang, inject, lock
void *stdin_thread(void *arg) {
  char line[512];
  while (fgets(line,sizeof(line),stdin)) {
    size_t ln=strlen(line); if (ln && line[ln-1]=='\n') line[ln-1]=0;
    if (strcmp(line,"lock")==0) { allowed=0; fprintf(stderr,"[%s] locked\n",ts()); continue; }
    if (strcmp(line,"inject")==0) { manual_inject=1; continue; }
    if (strcmp(line,"lang:c")==0) { chosen_lang=LANG_C; fprintf(stderr,"[%s] lang=C\n",ts()); continue; }
    if (strcmp(line,"lang:py")==0) { chosen_lang=LANG_PY; fprintf(stderr,"[%s] lang=PY\n",ts()); continue; }
    // check passphrase candidates
    for (int i=0;i<NUM_TOKENS;i++) {
      if (strcmp(line, bada_tokens[i])==0) {
	allowed = 1;
	fprintf(stderr,"[%s] passphrase accepted: %s\n", ts(), bada_tokens[i]);
	break;
      }
    }
  }
  return NULL;
}

void perform_inject() {
  if (chosen_lang==LANG_C) xdotool_type(snippet_c); else xdotool_type(snippet_py);
  fprintf(stderr,"[%s] injected snippet (lang=%s)\n", ts(), chosen_lang==LANG_C?"C":"PY");
}

int main(int argc, char **argv) {
  const char *dev="/dev/video0"; if (argc>=2) dev=argv[1];
  if (v4l2_open_dev(dev, &vfd, &vbufs, &vnbufs) != 0) { fprintf(stderr,"[%s] cannot open %s\n", ts(), dev); return 1; }
  fprintf(stderr,"[%s] started device=%s\n", ts(), dev);
  pthread_t th; pthread_create(&th,NULL,stdin_thread,NULL);

  enum { S_IDLE=0, S_LISTEN=1, S_INPUT=2 } state = S_IDLE;
  for (;;) {
    double pc = read_pc_temp_sys(); if (isnan(pc)) pc = BASE_TEMP;
    double *t = capture_temps(vfd, vbufs);
    if (!t) { usleep(SAMPLE_MS*1000); continue; }
    double gint = global_metric(t); double e = energy_metric(gint, pc);
    free(t);

    if (manual_inject) { manual_inject=0; perform_inject(); allowed=0; }

    if (state==S_IDLE) {
      if (e >= START_TH) { state=S_LISTEN; fprintf(stderr,"[%s] -> LISTEN e=%.4f\n", ts(), e); }
    } else if (state==S_LISTEN) {
      if (e >= START_TH*1.2) {
	if (allowed) { perform_inject(); allowed=0; state=S_INPUT; }
	else fprintf(stderr,"[%s] candidate detected but no passphrase e=%.4f\n", ts(), e);
      } else if (e < STOP_TH) { state=S_IDLE; fprintf(stderr,"[%s] -> IDLE e=%.4f\n", ts(), e); }
    } else if (state==S_INPUT) {
      if (e < STOP_TH) { state=S_IDLE; fprintf(stderr,"[%s] INPUT->IDLE e=%.4f\n", ts(), e); }
    }

    usleep(SAMPLE_MS*1000);
  }

  v4l2_close_dev(vfd, vbufs, vnbufs);
  return 0;
}

/*
注意（要点）
- 合い言葉リストは `bada_tokens[]` に列挙しています。必要なら PDF の他の語をここへ追加してください。  
- 実行前に挿入先エディタをフォーカスしてください（xdotool は Xorg 前提）。Wayland 非対応。  
- カメラフォーマット（Y16 等）やスニペット内容は実環境で調整してください。
*/
