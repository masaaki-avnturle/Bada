/*
OmegaTrainer_Fixed_Controlled.c
UTF-8
瞬読トレーニング（修正版・キー操作対応: q/p/+/ - /n/m が即時有効）
- 画面に常に 10 行を一瞬表示し、前表示が残らないよう全画面クリアして上書きします。
- 単語内の文字をシャッフル（英字の大小保持、UTF-8対応）、日本語はグループ化して内部をシャッフル。
- キー操作（Enter不要）： q=終了, p=一時停止/再開, +=高速化, -=低速化, n=列減少, m=列増加
Build:
  gcc -O2 -o OmegaTrainer_Fixed_Controlled OmegaTrainer_Fixed_Controlled.c
*/
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <locale.h>
#include <unistd.h>
#include <ctype.h>
#include <termios.h>
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

/* Terminal raw mode helpers */
static struct termios orig_term;
static void enable_raw_mode(void){
  struct termios t;
  if(tcgetattr(STDIN_FILENO, &orig_term) == -1) return;
  t = orig_term;
  /* disable canonical mode, echo, signals */
  t.c_lflag &= ~(ECHO | ICANON | ISIG);
  /* minimum bytes for read = 0, timeout = 0 (nonblocking) */
  t.c_cc[VMIN] = 0;
  t.c_cc[VTIME] = 0;
  tcsetattr(STDIN_FILENO, TCSAFLUSH, &t);
}
static void disable_raw_mode(void){
  tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_term);
}

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
   and each UTF-8 codepoint as a token. */
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
    char *s = strdup(tok);
    if(!s) die("strdup");
    size_t n = strlen(s);
    if(n <= 1) return s;
    for(size_t i = n-1; i>0; --i){
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

/* Build corpus: group consecutive multibyte tokens into groups before scrambling to create Japanese "words". */
static Corpus build_corpus(char *text, size_t group_multibyte){
  Corpus c = {0};
  size_t tn = 0;
  char **tokens = split_tokens(text, &tn);
  size_t cap = tn + 16;
  c.chunks = malloc(sizeof(char*) * cap);
  size_t cn = 0;
  for(size_t i=0;i<tn;){
    unsigned char lead = (unsigned char)tokens[i][0];
    if(lead >= 128){
      size_t j = i;
      size_t taken = 0;
      size_t buflen = 1;
      while(j < tn && (unsigned char)tokens[j][0] >= 128 && taken < group_multibyte){
	buflen += strlen(tokens[j]);
	j++; taken++;
      }
      char *buf = malloc(buflen);
      buf[0]=0;
      for(size_t k=i;k<j;k++){ strcat(buf, tokens[k]); free(tokens[k]); }
      char *scr = scramble_token(buf);
      free(buf);
      c.chunks[cn++] = scr;
      i = j;
    } else {
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

/* display exactly rows x cols tokens, clearing screen entirely before printing */
static void display_block_clear(char **pool, size_t start, size_t rows, size_t cols, size_t pool_n){
  /* Clear whole screen and move cursor home */
  printf("\033[2J\033[H"); fflush(stdout);
  size_t idx = start;
  for(size_t r=0;r<rows;r++){
    for(size_t c=0;c<cols;c++){
      if(idx < pool_n) fputs(pool[idx], stdout);
      if(c+1 < cols) putchar(' ');
      idx++;
    }
    putchar('\n');
  }
  fflush(stdout);
}

/* interactive loop: prints blocks with full-screen clear each iteration so nothing remains from prior */
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
  FILE *logf = fopen("omega_fixed_controlled_session.log","a");
  if(!logf) logf = stderr;

  enable_raw_mode();
  printf("Omega Trainer (controlled): q=quit, p=pause/resume, +/- speed, n/m cols +/-\n");
  while(1){
    /* nonblocking input using read */
    char ch = 0;
    ssize_t r = read(STDIN_FILENO, &ch, 1);
    if(r > 0){
      if(ch == 'q' || ch == 'Q'){ if(logf) fprintf(logf,"QUIT\n"); break; }
      else if(ch == 'p' || ch == 'P'){ paused = !paused; fprintf(stderr, paused? "PAUSED\n":"RESUME\n"); }
      else if(ch == '+'){ interval_ms -= 100; if(interval_ms < MIN_INTERVAL_MS) interval_ms = MIN_INTERVAL_MS; }
      else if(ch == '-'){ interval_ms += 100; if(interval_ms > MAX_INTERVAL_MS) interval_ms = MAX_INTERVAL_MS; }
      else if(ch == 'n'){ if(cols > 1) cols--; tokens_per_screen = rows * cols; }
      else if(ch == 'm'){ cols++; tokens_per_screen = rows * cols; }
    }

    if(paused){ usleep(100000); continue; }

    if(cursor + tokens_per_screen > c->n){
      shuffle_chunks(pool, c->n);
      cursor = 0;
    }

    /* Clear screen fully and display exactly rows x cols tokens */
    display_block_clear(pool, cursor, rows, cols, c->n);

    if(logf){
      for(size_t i=0;i<tokens_per_screen && cursor+i < c->n;i++){
	if(i) fputc('\t', logf);
	fputs(pool[cursor+i], logf);
      }
      fputc('\n', logf);
      fflush(logf);
    }

    cursor += tokens_per_screen;
    usleep((useconds_t)interval_ms * 1000);
  }

  disable_raw_mode();
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

  size_t group_multibyte = 3; /* group size for Japanese chunking */

  Corpus corpus = build_corpus(text, group_multibyte);
  free(text);

  if(corpus.n == 0){ fprintf(stderr,"No tokens.\n"); free_corpus(&corpus); return 1; }

  shuffle_chunks(corpus.chunks, corpus.n);

  /* Display exactly 10 lines on screen; default 1 column => 10 tokens displayed as 10 lines */
  size_t rows = 10;
  size_t cols = 1;

  run_training(&corpus, rows, cols);

  free_corpus(&corpus);
  return 0;
}
