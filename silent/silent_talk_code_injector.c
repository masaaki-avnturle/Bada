// silent_talk_code_injector.c
// Ubuntu/Xorg 用: V4L2 赤外線カメラで熱指標を監視し、合い言葉受理後に言語特化のコード構成要素を
// フォーカス中のエディタへ自動入力するツール。
// - xdotool 必須 (sudo apt install xdotool)
// - Xorg 環境で動作（Wayland 非対応）
// - カメラは V4L2/Y16 (16bit) を想定。TEMP_SCALE 等は実機に合わせて調整。
// - stdin 経由で「合い言葉」「言語選択」「挿入内容設定」を行い、熱検出で挿入を実行。
//   例: 入力行の形式
//     passphrase                      <- 合い言葉（デフォルト "open-sesame"）を送ると一回許可
//     lock                             <- 許可を解除
//     lang:c / lang:py                 <- 挿入言語選択
//     set:include:stdin.h              <- (C) include 指示: 組み立てた '#include <stdin.h>' を挿入
//     set:vars:x,y,z                   <- (C) 変数定義 -> 'int x, y, z;' を挿入
//     set:struct:MyS:a,b               <- (C) struct 定義: fields a,b を int として定義
//     set:def:func_name:param1,param2  <- (py) def 作成: 'def func_name(param1, param2): ...'
//     set:class:ClassName:method1,method2 <- (py) class 作成
//     inject                            <- 手動で即時挿入（合い言葉不要）
// コンパイル: gcc -O2 silent_talk_code_injector.c -o silent_talk_code_injector -lpthread -lm
// 実行例: ./silent_talk_code_injector /dev/video0

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <pthread.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/select.h>
#include <linux/videodev2.h>

#define FRAME_WIDTH 160
#define FRAME_HEIGHT 120
#define SAMPLE_INTERVAL_MS 200
#define BASELINE_TEMP 36.5
#define TEMP_SCALE 0.01
#define TEMP_OFFSET 0.0

#define LISTEN_START_THRESHOLD 0.08
#define LISTEN_STOP_THRESHOLD 0.05

static const char *DEFAULT_PASSPHRASE = "open-sesame";

// V4L2 buffer
struct buffer { void *start; size_t length; };

// 挿入設定構造体（シンプル）
typedef struct {
  int lang; // 0=C, 1=PY
  enum { KIND_INCLUDE, KIND_VARS, KIND_STRUCT, KIND_CFUNC, KIND_PYDEF, KIND_PYCLASS, KIND_RAW } kind;
  char arg1[256]; // name / header / struct name / func name
  char arg2[512]; // fields / params / methods / raw text
} inject_spec_t;

static inject_spec_t current_spec; // 保持される挿入仕様
static volatile int allowed = 0; // 合い言葉一回分許可
static volatile int manual_inject = 0; // 手動即時注入要求

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

// --- V4L2 simple helpers ---
int v4l2_open_device(const char *dev, int *out_fd, struct buffer **out_bufs, unsigned int *out_nbufs) {
  int fd = open(dev, O_RDWR | O_NONBLOCK, 0); if (fd < 0) return -1;
  struct v4l2_format fmt; memset(&fmt,0,sizeof(fmt));
  fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  fmt.fmt.pix.width = FRAME_WIDTH; fmt.fmt.pix.height = FRAME_HEIGHT;
  fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_Y16; fmt.fmt.pix.field = V4L2_FIELD_NONE;
  ioctl(fd, VIDIOC_S_FMT, &fmt);
  struct v4l2_requestbuffers req; memset(&req,0,sizeof(req));
  req.count = 4; req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; req.memory = V4L2_MEMORY_MMAP;
  if (ioctl(fd, VIDIOC_REQBUFS, &req) < 0) { close(fd); return -1; }
  struct buffer *bufs = calloc(req.count, sizeof(*bufs));
  for (unsigned int i=0;i<req.count;++i) {
    struct v4l2_buffer buf; memset(&buf,0,sizeof(buf));
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; buf.memory = V4L2_MEMORY_MMAP; buf.index = i;
    if (ioctl(fd, VIDIOC_QUERYBUF, &buf) < 0) continue;
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
double *v4l2_capture_frame_to_temps(int fd, struct buffer *bufs) {
  fd_set fds; struct timeval tv; FD_ZERO(&fds); FD_SET(fd,&fds); tv.tv_sec=2; tv.tv_usec=0;
  if (select(fd+1, &fds, NULL, NULL, &tv) <= 0) return NULL;
  struct v4l2_buffer buf; memset(&buf,0,sizeof(buf)); buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; buf.memory = V4L2_MEMORY_MMAP;
  if (ioctl(fd, VIDIOC_DQBUF, &buf) < 0) return NULL;
  void *data = bufs[buf.index].start;
  double *temps = malloc(sizeof(double) * FRAME_WIDTH * FRAME_HEIGHT);
  if (!temps) { ioctl(fd, VIDIOC_QBUF, &buf); return NULL; }
  uint16_t *pix = (uint16_t*)data;
  for (int y=0;y<FRAME_HEIGHT;++y) for (int x=0;x<FRAME_WIDTH;++x) {
      int idx = y*FRAME_WIDTH + x; uint16_t raw = pix[idx];
      temps[idx] = raw * TEMP_SCALE + TEMP_OFFSET;
    }
  ioctl(fd, VIDIOC_QBUF, &buf);
  return temps;
}

// --- processing ---
double global_partial_integral_from_temps(const double *t) {
  double sum=0.0, wsum=0.0; int cx=FRAME_WIDTH/2, cy=FRAME_HEIGHT/2;
  for (int y=0;y<FRAME_HEIGHT;++y) for (int x=0;x<FRAME_WIDTH;++x) {
      int idx=y*FRAME_WIDTH+x; double dx=(double)(x-cx), dy=(double)(y-cy);
      double r=sqrt(dx*dx+dy*dy)+1.0; double weight=exp(-r/30.0);
      sum += t[idx]*weight; wsum += weight;
    }
  return (wsum==0.0)?0.0:(sum/wsum);
}
double manifold_energy_metric(double global_integral, double pc_temp) {
  double a=1.2,b=0.8; return a*(global_integral-BASELINE_TEMP)+b*(pc_temp-BASELINE_TEMP);
}
double read_pc_temp_sys() {
  FILE *f=NULL; char path[256];
  for (int i=0;i<8;++i) {
    snprintf(path,sizeof(path),"/sys/class/thermal/thermal_zone%d/temp",i);
    f=fopen(path,"r"); if(!f) continue;
    long v=0; if(fscanf(f,"%ld",&v)==1){ fclose(f); if(v>1000) return v/1000.0; return (double)v; } fclose(f);
  }
  return NAN;
}

// --- xdotool helper ---
void send_via_xdotool_escaped(const char *text) {
  size_t in_len = strlen(text);
  char *esc = malloc(in_len*4 + 128);
  if (!esc) return;
  char *p = esc;
  strcpy(p, "xdotool type --delay 5 -- '"); p += strlen(p);
  for (size_t i=0;i<in_len;++i) {
    char c = text[i];
    if (c == '\'') { strcpy(p, "'\\''"); p += 4; }
    else { *p++ = c; *p = 0; }
  }
  strcpy(p, "' &");
  system(esc);
  free(esc);
}

// --- code generation helpers ---
static void trim_spaces(char *s) {
  char *p=s; while(*p && isspace((unsigned char)*p)) p++;
  if (p!=s) memmove(s,p,strlen(p)+1);
  // rtrim
  int l=strlen(s); while(l>0 && isspace((unsigned char)s[l-1])) s[--l]=0;
}
static void replace_commas_with_comma_space(char *s) {
  char *p = s; while(*p) { if (*p==',') { *p++ = ','; if (*p!=' ') { memmove(p+1,p,strlen(p)+1); *p=' '; p++; } } else p++; }
}

// Build C include: e.g., arg1="stdin.h" -> "#include <stdin.h>\n"
static void build_c_include(const inject_spec_t *sp, char *out, size_t outlen) {
  snprintf(out,outlen,"#include <%s>\n", sp->arg1);
}
// Build C variable decl: arg2 = "x,y" -> "int x, y;\n"
static void build_c_vars(const inject_spec_t *sp, char *out, size_t outlen) {
  char buf[512]; strncpy(buf, sp->arg2, sizeof(buf)-1); buf[sizeof(buf)-1]=0; trim_spaces(buf); replace_commas_with_comma_space(buf);
  snprintf(out,outlen,"int %s;\n", buf);
}
// Build C struct: arg1=Name arg2="a,b" -> "typedef struct { int a; int b; } Name;\n"
static void build_c_struct(const inject_spec_t *sp, char *out, size_t outlen) {
  char buf[512]; strncpy(buf, sp->arg2, sizeof(buf)-1); buf[sizeof(buf)-1]=0; trim_spaces(buf); replace_commas_with_comma_space(buf);
  char fields[1024]="";
  char *tok = strtok(buf, ",");
  while (tok) {
    trim_spaces(tok);
    if (strlen(fields)) strncat(fields, "    ", sizeof(fields)-strlen(fields)-1);
    strncat(fields, "int ", sizeof(fields)-strlen(fields)-1);
    strncat(fields, tok, sizeof(fields)-strlen(fields)-1);
    strncat(fields, ";\n", sizeof(fields)-strlen(fields)-1);
    tok = strtok(NULL,",");
  }
  snprintf(out,outlen,"typedef struct %s {\n%s} %s;\n", sp->arg1, fields, sp->arg1);
}
// Build C function prototype: arg1=name arg2="a,b" -> "void name(int a, int b) {\n    // TODO\n}\n"
static void build_c_func(const inject_spec_t *sp, char *out, size_t outlen) {
  char buf[512]; strncpy(buf, sp->arg2, sizeof(buf)-1); buf[sizeof(buf)-1]=0; trim_spaces(buf); replace_commas_with_comma_space(buf);
  snprintf(out,outlen,"void %s(%s) {\n    // TODO\n}\n", sp->arg1, buf);
}
// Build Python def: arg1=name arg2="p1,p2" -> "def name(p1, p2):\n    pass\n"
static void build_py_def(const inject_spec_t *sp, char *out, size_t outlen) {
  char buf[512]; strncpy(buf, sp->arg2, sizeof(buf)-1); buf[sizeof(buf)-1]=0; trim_spaces(buf); replace_commas_with_comma_space(buf);
  snprintf(out,outlen,"def %s(%s):\n    \"\"\"TODO\"\"\"\n    pass\n\n", sp->arg1, buf);
}
// Build Python class: arg1=ClassName arg2="m1,m2" -> class with methods skeletons
static void build_py_class(const inject_spec_t *sp, char *out, size_t outlen) {
  char buf[512]; strncpy(buf, sp->arg2, sizeof(buf)-1); buf[sizeof(buf)-1]=0; trim_spaces(buf); replace_commas_with_comma_space(buf);
  char methods[2048]="";
  char *tok = strtok(buf, ",");
  while (tok) {
    trim_spaces(tok);
    strncat(methods, "    def ", sizeof(methods)-strlen(methods)-1);
    strncat(methods, tok, sizeof(methods)-strlen(methods)-1);
    strncat(methods, "(self):\n        pass\n\n", sizeof(methods)-strlen(methods)-1);
    tok = strtok(NULL, ",");
  }
  snprintf(out,outlen,"class %s:\n    \"\"\"TODO: class %s\"\"\"\n\n%s", sp->arg1, sp->arg1, methods);
}
// Raw insertion (user provided)
static void build_raw(const inject_spec_t *sp, char *out, size_t outlen) {
  strncpy(out, sp->arg2, outlen-1); out[outlen-1]=0;
}

// Top-level build dispatcher
static void build_insertion_text(const inject_spec_t *sp, char *out, size_t outlen) {
  out[0]=0;
  switch (sp->kind) {
  case KIND_INCLUDE: build_c_include(sp,out,outlen); break;
  case KIND_VARS: build_c_vars(sp,out,outlen); break;
  case KIND_STRUCT: build_c_struct(sp,out,outlen); break;
  case KIND_CFUNC: build_c_func(sp,out,outlen); break;
  case KIND_PYDEF: build_py_def(sp,out,outlen); break;
  case KIND_PYCLASS: build_py_class(sp,out,outlen); break;
  case KIND_RAW: build_raw(sp,out,outlen); break;
  default: snprintf(out,outlen,"/* unknown spec */\n"); break;
  }
}

// --- stdin thread: commands to set spec, language, passphrase, manual inject ---
static char passphrase_buf[128];
void *stdin_thread(void *arg) {
  char line[1024];
  while (fgets(line, sizeof(line), stdin) != NULL) {
    // trim
    size_t ln = strlen(line); if (ln && line[ln-1]=='\n') line[ln-1]=0;
    if (strlen(line)==0) continue;
    if (strcmp(line, "lock")==0) { allowed=0; fprintf(stderr,"[%s] locked\n", timestamp()); continue; }
    if (strcmp(line, "inject")==0) { manual_inject=1; continue; }
    if (strncmp(line, "lang:",5)==0) {
      char *v = line+5; if (strcmp(v,"c")==0) current_spec.lang=0; else if (strcmp(v,"py")==0) current_spec.lang=1;
      fprintf(stderr,"[%s] lang set to %s\n", timestamp(), current_spec.lang==0?"C":"py"); continue;
    }
    if (strncmp(line, "set:",4)==0) {
      // set:TYPE:ARGS...
      char *p = line+4;
      char *type = strtok(p, ":");
      char *a1 = strtok(NULL, ":");
      char *a2 = strtok(NULL, "");
      if (!type) continue;
      if (strcmp(type,"include")==0 && a1) {
	current_spec.kind = KIND_INCLUDE; strncpy(current_spec.arg1, a1, sizeof(current_spec.arg1)-1); current_spec.arg1[sizeof(current_spec.arg1)-1]=0;
	fprintf(stderr,"[%s] spec set: include <%s>\n", timestamp(), current_spec.arg1); continue;
      }
      if (strcmp(type,"vars")==0 && a1) {
	current_spec.kind = KIND_VARS; current_spec.lang = 0; strncpy(current_spec.arg2, a1, sizeof(current_spec.arg2)-1); current_spec.arg2[sizeof(current_spec.arg2)-1]=0;
	fprintf(stderr,"[%s] spec set: vars %s\n", timestamp(), current_spec.arg2); continue;
      }
      if (strcmp(type,"struct")==0 && a1 && a2) {
	current_spec.kind = KIND_STRUCT; current_spec.lang = 0; strncpy(current_spec.arg1, a1, sizeof(current_spec.arg1)-1); strncpy(current_spec.arg2, a2, sizeof(current_spec.arg2)-1);
	fprintf(stderr,"[%s] spec set: struct %s (%s)\n", timestamp(), current_spec.arg1, current_spec.arg2); continue;
      }
      if (strcmp(type,"cfunc")==0 && a1 && a2) {
	current_spec.kind = KIND_CFUNC; current_spec.lang = 0; strncpy(current_spec.arg1,a1,sizeof(current_spec.arg1)-1); strncpy(current_spec.arg2,a2,sizeof(current_spec.arg2)-1);
	fprintf(stderr,"[%s] spec set: cfunc %s(%s)\n", timestamp(), current_spec.arg1, current_spec.arg2); continue;
      }
      if (strcmp(type,"def")==0 && a1) {
	current_spec.kind = KIND_PYDEF; current_spec.lang = 1; strncpy(current_spec.arg1,a1,sizeof(current_spec.arg1)-1); if (a2) strncpy(current_spec.arg2,a2,sizeof(current_spec.arg2)-1); else current_spec.arg2[0]=0;
	fprintf(stderr,"[%s] spec set: py def %s(%s)\n", timestamp(), current_spec.arg1, current_spec.arg2); continue;
      }
      if (strcmp(type,"class")==0 && a1) {
	current_spec.kind = KIND_PYCLASS; current_spec.lang = 1; strncpy(current_spec.arg1,a1,sizeof(current_spec.arg1)-1); if (a2) strncpy(current_spec.arg2,a2,sizeof(current_spec.arg2)-1); else current_spec.arg2[0]=0;
	fprintf(stderr,"[%s] spec set: py class %s (%s)\n", timestamp(), current_spec.arg1, current_spec.arg2); continue;
      }
      if (strcmp(type,"raw")==0 && a1) {
	current_spec.kind = KIND_RAW; current_spec.lang = 0; strncpy(current_spec.arg2, a1, sizeof(current_spec.arg2)-1);
	fprintf(stderr,"[%s] spec set: raw\n", timestamp()); continue;
      }
      continue;
    }
    // passphrase check
    if (strcmp(line, passphrase_buf)==0) {
      allowed = 1;
      fprintf(stderr,"[%s] passphrase accepted (one injection allowed)\n", timestamp());
      continue;
    }
    // unknown
    fprintf(stderr,"[%s] unknown stdin command\n", timestamp());
  }
  return NULL;
}

// --- main ---
int main(int argc, char **argv) {
  const char *dev = "/dev/video0";
  if (argc >= 2) dev = argv[1];
  strncpy(passphrase_buf, DEFAULT_PASSPHRASE, sizeof(passphrase_buf)-1); passphrase_buf[sizeof(passphrase_buf)-1]=0;

  // default spec: C include <stdin.h> to match user's request example
  current_spec.lang = 0;
  current_spec.kind = KIND_INCLUDE;
  strncpy(current_spec.arg1, "stdin.h", sizeof(current_spec.arg1)-1);
  current_spec.arg1[sizeof(current_spec.arg1)-1]=0;

  int fd; struct buffer *bufs = NULL; unsigned int nbufs = 0;
  if (v4l2_open_device(dev, &fd, &bufs, &nbufs) != 0) {
    fprintf(stderr,"[%s] ERROR: cannot open %s: %s\n", timestamp(), dev, strerror(errno));
    return 1;
  }
  fprintf(stderr,"[%s] started device=%s\n", timestamp(), dev);

  pthread_t th; pthread_create(&th, NULL, stdin_thread, NULL);

  enum { STATE_IDLE=0, STATE_LISTENING=1, STATE_INPUTTING=2 } state = STATE_IDLE;

  for (;;) {
    double pc_temp = read_pc_temp_sys(); if (isnan(pc_temp)) pc_temp = BASELINE_TEMP;
    double *temps = v4l2_capture_frame_to_temps(fd, bufs);
    if (!temps) { usleep(SAMPLE_INTERVAL_MS*1000); continue; }
    double gint = global_partial_integral_from_temps(temps);
    double energy = manifold_energy_metric(gint, pc_temp);
    free(temps);

    // manual immediate inject
    if (manual_inject) {
      manual_inject = 0;
      char built[4096]; build_insertion_text(&current_spec, built, sizeof(built));
      send_via_xdotool_escaped(built);
      fprintf(stderr,"[%s] manual inject executed\n", timestamp());
      allowed = 0; // optionally consume
    }

    if (state == STATE_IDLE) {
      if (energy >= LISTEN_START_THRESHOLD) {
	state = STATE_LISTENING;
	fprintf(stderr,"[%s] -> LISTENING (e=%.4f)\n", timestamp(), energy);
      }
    } else if (state == STATE_LISTENING) {
      if (energy >= LISTEN_START_THRESHOLD * 1.2) {
	// candidate to inject
	if (allowed) {
	  char built[4096]; build_insertion_text(&current_spec, built, sizeof(built));
	  send_via_xdotool_escaped(built);
	  fprintf(stderr,"[%s] injected (kind=%d lang=%d)\n", timestamp(), current_spec.kind, current_spec.lang);
	  allowed = 0; // consume passphrase
	  state = STATE_INPUTTING;
	} else {
	  fprintf(stderr,"[%s] detection but no passphrase allowed\n", timestamp());
	}
      } else if (energy < LISTEN_STOP_THRESHOLD) {
	state = STATE_IDLE;
	fprintf(stderr,"[%s] -> IDLE (e=%.4f)\n", timestamp(), energy);
      }
    } else if (state == STATE_INPUTTING) {
      if (energy < LISTEN_STOP_THRESHOLD) {
	state = STATE_IDLE;
	fprintf(stderr,"[%s] inputting->IDLE (e=%.4f)\n", timestamp(), energy);
      }
    }

    usleep(SAMPLE_INTERVAL_MS*1000);
  }

  v4l2_close_device(fd, bufs, nbufs);
  return 0;
}
