/*
OmegaTrainer_Scramble_Multiline.c
UTF-8
瞬読トレーニング（単語内の文字をランダムに並べ替え・英字の大小保持・複数行同時表示）
- 入力: ファイルまたは標準入力（UTF-8 混在: 日本語＋英語）
- トークン（ASCII単語またはUTF-8コードポイント列）ごとに内部をシャッフル（英字の大文字/小文字は保持）
- 表示は複数行・複数カラムブロックで一度に表示（行数とカラム数で配置）
- 操作: q=終了, p=一時停止/再開, +/-=速さ調整, n/m=一行当たりのトークン数+/-
Build:
  gcc -O2 -o OmegaTrainer_Scramble_Multiline OmegaTrainer_Scramble_Multiline.c
*/
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <locale.h>
#include <unistd.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/select.h>

#define MAX_BUF 524288
#define DEFAULT_INTERVAL_MS 800
#define MIN_INTERVAL_MS 20
#define MAX_INTERVAL_MS 5000

typedef struct {
  char **chunks;
  size_t n;
} Corpus;

/* helpers */
static void die(const char *msg){ perror(msg); exit(1); }

static char *read_all(FILE *f){
  size_t cap = MAX_BUF, len = 0;
  char *buf = malloc(cap);
  if(!buf) die("malloc");
  while(!feof(f)){
    size_t r = fread(buf+len,1,cap-len,f);
    if(r==0) break;
    len += r;
    if(len + 4096 >= cap){
      cap *= 2;
      buf = realloc(buf, cap);
      if(!buf) die("realloc");
    }
  }
  buf[len]=0;
  return buf;
}

/* collapse whitespace to single space, preserve case */
static void normalize_whitespace(char *s){
  char *r=s, *w=s;
  while(*r){
    if((unsigned char)*r <= 32){
      *w++ = ' ';
      while(*r && (unsigned char)*r <= 32) r++;
    } else {
      *w++ = *r++;
    }
  }
  *w = 0;
}

/* UTF-8 codepoint length from lead byte */
static int utf8_len(unsigned char lead){
  if((lead & 0x80) == 0) return 1;
  if((lead & 0xE0) == 0xC0) return 2;
  if((lead & 0xF0) == 0xE0) return 3;
  if((lead & 0xF8) == 0xF0) return 4;
  return 1;
}

/* Split into tokens: ASCII alnum runs as single token, ASCII single punctuation as token,
   and each UTF-8 codepoint as a token (so Japanese sequences are many tokens unless adjacent codepoints are grouped later). */
static char **split_tokens(const char *s, size_t *out_n){
  size_t cap = 4096, n = 0;
  char **arr = malloc(sizeof(char*)*cap);
  if(!arr) die("malloc");
  const unsigned char *p = (const unsigned char*)s;
  while(*p){
    if(n+1 >= cap){ cap *= 2; arr = realloc(arr, sizeof(char*)*cap); if(!arr) die("realloc"); }
    if(*p < 128){
      const unsigned char *q = p;
      if(isalnum(*q)){
	while(*q && *q < 128 && isalnum(*q)) q++;
      } else {
	q = p + 1;
      }
      size_t L = q - p;
      arr[n] = malloc(L+1); memcpy(arr[n], p, L); arr[n][L]=0;
      n++; p = q;
    } else {
      int L = utf8_len(*p);
      arr[n] = malloc(L+1); memcpy(arr[n], p, L); arr[n][L]=0;
      n++; p += L;
    }
  }
  *out_n = n;
  return arr;
}

/* scramble ASCII token bytes (preserve case), or scramble order of UTF-8 codepoints */
static char *scramble_token(const char *tok){
  size_t L = strlen(tok);
  if(L <= 1) return strdup(tok);

  /* detect all-ASCII */
  int all_ascii = 1;
  for(size_t i=0;i<L;i++) if((unsigned char)tok[i] >= 128){ all_ascii = 0; break; }

  if(all_ascii){
    /* shuffle bytes but preserve original case since bytes unchanged except order */
    char *s = strdup(tok);
    if(!s) die("strdup");
    for(size_t i = strlen(s)-1; i>0; --i){
      size_t j = (size_t)rand() % (i+1);
      char t = s[i]; s[i]=s[j]; s[j]=t;
    }
    return s;
  } else {
    /* split into codepoints */
    const unsigned char *p = (const unsigned char*)tok;
    size_t count = 0;
    while(*p){ count++; p += utf8_len(*p); }
    if(count <= 1) return strdup(tok);
    char **pcs = malloc(sizeof(char*) * count);
    p = (const unsigned char*)tok;
    for(size_t i=0;i<count;i++){
      int le = utf8_len(*p);
      pcs[i] = malloc(le+1);
      memcpy(pcs[i], p, le); pcs[i][le]=0;
      p += le;
    }
    for(size_t i = count-1; i>0; --i){
      size_t j = (size_t)rand() % (i+1);
      char *t = pcs[i]; pcs[i]=pcs[j]; pcs[j]=t;
    }
    size_t tot = 1;
    for(size_t i=0;i<count;i++) tot += strlen(pcs[i]);
    char *out = malloc(tot); out[0]=0;
    for(size_t i=0;i<count;i++){ strcat(out, pcs[i]); free(pcs[i]); }
    free(pcs);
    return out;
  }
}

/* Build corpus: group contiguous UTF-8 tokens into small "words" to create larger Japanese chunks:
   to make Japanese show as shuffled characters within a word, group consecutive multibyte tokens into groups of G size. */
static Corpus build_corpus(char *text, size_t group_multibyte){
  Corpus c = {0};
  size_t tn = 0;
  char **tokens = split_tokens(text, &tn);
  /* approximate grouping: create chunks vector */
  size_t cap = tn + 16;
  c.chunks = malloc(sizeof(char*) * cap);
  size_t cn = 0;
  for(size_t i=0;i<tn;){
    /* if token is multibyte (lead >=128), group up to group_multibyte consecutive multibyte tokens */
    unsigned char lead = (unsigned char)tokens[i][0];
    if(lead >= 128){
      size_t j = i;
      size_t taken = 0;
      size_t buflen = 1;
      /* compute needed bytes and group */
      while(j < tn && (unsigned char)tokens[j][0] >= 128 && taken < group_multibyte){
	buflen += strlen(tokens[j]);
	j++; taken++;
      }
      char *buf = malloc(buflen);
      buf[0]=0;
      for(size_t k=i;k<j;k++){ strcat(buf, tokens[k]); free(tokens[k]); }
      /* scramble inside this grouped multibyte chunk */
      char *scr = scramble_token(buf);
      free(buf);
      c.chunks[cn++] = scr;
      i = j;
    } else {
      /* ASCII token: scramble if length>1 */
      if(strlen(tokens[i]) > 1){
	char *scr = scramble_token(tokens[i]);
	c.chunks[cn++] = scr;
	free(tokens[i]);
      } else {
	c.chunks[cn++] = strdup(tokens[i]);
	free(tokens[i]);
      }
      i++;
    }
    if(cn + 8 >= cap){ cap *= 2; c.chunks = realloc(c.chunks, sizeof(char*)*cap); if(!c.chunks) die("realloc"); }
  }
  free(tokens);
  c.n = cn;
  return c;
}

/* shuffle corpus */
static void shuffle_chunks(char **a, size_t n){
  if(n<=1) return;
  for(size_t i = n-1; i>0; --i){
    size_t j = (size_t)rand() % (i+1);
    char *t = a[i]; a[i]=a[j]; a[j]=t;
  }
}

/* display a block: rows x cols tokens per block; each token printed with single space separation */
static void display_block(char **pool, size_t start, size_t rows, size_t cols, size_t pool_n){
  size_t idx = start;
  for(size_t r=0;r<rows;r++){
    for(size_t c=0;c<cols;c++){
      if(idx >= pool_n){ putchar(' '); }
      else {
	fputs(pool[idx], stdout);
      }
      if(c+1 < cols) putchar(' ');
      idx++;
    }
    if(r+1 < rows) putchar('\n');
  }
}

/* interactive loop */
static void run_training(Corpus *c, size_t rows, size_t cols){
  if(!c || c->n==0) return;
  char **pool = malloc(sizeof(char*) * c->n);
  for(size_t i=0;i<c->n;i++) pool[i] = c->chunks[i];
  srand((unsigned int)time(NULL));
  shuffle_chunks(pool, c->n);

  int interval_ms = DEFAULT_INTERVAL_MS;
  size_t tokens_per_screen = rows * cols;
  size_t cursor = 0;
  int paused = 0;
  FILE *logf = fopen("omega_multiline_session.log","a");
  if(!logf) logf = stderr;

  printf("Omega Multiline Trainer: q=quit, p=pause/resume, +/- speed, n/m cols +/-\n");
  while(1){
    /* nonblocking input */
    fd_set set;
    struct timeval tv;
    FD_ZERO(&set);
    FD_SET(STDIN_FILENO, &set);
    tv.tv_sec = 0; tv.tv_usec = 0;
    int rv = select(STDIN_FILENO+1, &set, NULL, NULL, &tv);
    if(rv>0){
      int ch = getchar();
      if(ch==EOF) {}
      else if(ch=='q' || ch=='Q'){ if(logf) fprintf(logf,"QUIT\n"); break; }
      else if(ch=='p' || ch=='P'){ paused = !paused; fprintf(stderr, paused? "PAUSED\n":"RESUME\n"); }
      else if(ch=='+'){ interval_ms -= 100; if(interval_ms < MIN_INTERVAL_MS) interval_ms = MIN_INTERVAL_MS; }
      else if(ch=='-'){ interval_ms += 100; if(interval_ms > MAX_INTERVAL_MS) interval_ms = MAX_INTERVAL_MS; }
      else if(ch=='n'){ if(cols>1) cols--; tokens_per_screen = rows*cols; }
      else if(ch=='m'){ cols++; tokens_per_screen = rows*cols; }
    }
    if(paused){ usleep(100000); continue; }

    if(cursor + tokens_per_screen > c->n){
      shuffle_chunks(pool, c->n);
      cursor = 0;
    }
    /* clear screen line block and print block */
    printf("\r\33[2K"); /* clear current line */
    /* Move to top-left of a small area: print block with newlines */
    display_block(pool, cursor, rows, cols, c->n);
    fflush(stdout);
    if(logf){
      /* log flat line (tab-separated tokens) */
      for(size_t i=0;i<tokens_per_screen && cursor+i < c->n;i++){
	if(i) fputc('\t', logf);
	fputs(pool[cursor+i], logf);
      }
      fputc('\n', logf);
      fflush(logf);
    }
    cursor += tokens_per_screen;
    usleep((useconds_t)interval_ms * 1000);
    /* after printing block, move cursor up rows to overwrite next time (ANSI) */
    printf("\033[%zuA", rows); /* move cursor up 'rows' lines */
  }
  if(logf && logf!=stderr) fclose(logf);
  free(pool);
}

static void free_corpus(Corpus *c){
  if(!c) return;
  if(c->chunks){
    for(size_t i=0;i<c->n;i++) free(c->chunks[i]);
    free(c->chunks);
  }
}

int main(int argc, char **argv){
  setlocale(LC_ALL, "");
  FILE *f = stdin;
  if(argc>=2){
    f = fopen(argv[1],"rb");
    if(!f){ fprintf(stderr,"Cannot open %s\n", argv[1]); return 1; }
  }
  char *text = read_all(f);
  if(f!=stdin) fclose(f);
  if(!text || strlen(text) < 4){ fprintf(stderr,"Input too short.\n"); free(text); return 1; }
  normalize_whitespace(text);

  /* group_multibyte: how many adjacent multibyte codepoints to group into one "word" before scrambling.
     Larger value -> Japanese displays as longer grouped chunks. */
  size_t group_multibyte = 3; /* reasonable default */

  Corpus corpus = build_corpus(text, group_multibyte);
  free(text);

  if(corpus.n == 0){ fprintf(stderr,"No tokens.\n"); free_corpus(&corpus); return 1; }

  shuffle_chunks(corpus.chunks, corpus.n);

  /* display parameters: rows and cols (adjust as desired or make command-line options) */
  size_t rows = 4;
  size_t cols = 6;

  run_training(&corpus, rows, cols);

  free_corpus(&corpus);
  return 0;
}
