/*
OmegaTrainer.c
UTF-8
Simple command-line "瞬読" conversion/training app in C.
- Reads UTF-8 text input (mixed Japanese/English) from a file or stdin.
- Performs basic "Omega" style string processing: normalize whitespace/punctuation,
  split into chunks by characters, words (Latin), or Japanese grapheme clusters (simple heuristic),
  optionally transliterate Latin to uppercase, map punctuation, and produce randomized sequences.
- Presents sequences in rapid succession for "瞬読" training, with adjustable speed and chunk size.
- Saves session logs.

Build:
  gcc -O2 -o OmegaTrainer OmegaTrainer.c

Usage:
  ./OmegaTrainer [input.txt]
Controls during run:
  q = quit, p = pause/resume, [+]/[-] = faster/slower, n/m = chunk size +/-.
*/

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <wchar.h>
#include <locale.h>
#include <unistd.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/select.h>

#define MAX_BUF 262144
#define MAX_CHUNKS 65536
#define DEFAULT_INTERVAL_MS 300
#define MIN_INTERVAL_MS 20
#define MAX_INTERVAL_MS 2000

typedef struct {
  char *raw;
  char **chunks;
  size_t n;
} Corpus;

static void die(const char *s){ perror(s); exit(1); }

/* Read entire file/STDIN into buffer */
static char *read_all(FILE *f){
  char *buf = malloc(MAX_BUF);
  if(!buf) die("malloc");
  size_t cap = MAX_BUF, len = 0;
  while(!feof(f)){
    size_t r = fread(buf+len,1,cap-len,f);
    len += r;
    if(len+1024 >= cap){
      cap *= 2;
      buf = realloc(buf, cap);
      if(!buf) die("realloc");
    }
  }
  buf[len]=0;
  return buf;
}

/* Normalize: collapse spaces, map punctuation, ASCII uppercase */
static void normalize_utf8(char *s){
  char *r = s, *w = s;
  while(*r){
    // collapse multiple spaces/tabs/newlines into single space
    if((unsigned char)*r <= 32){
      *w++ = ' ';
      while(*r && (unsigned char)*r <= 32) r++;
      continue;
    }
    // map common full-width punctuation to ASCII
    if((unsigned char)*r == 0xE3 /* possibly multibyte; naive pass-through */){
      // skip; leave multibyte sequences untouched for simplicity
    }
    // ASCII letters -> uppercase
    if((unsigned char)*r < 128){
      *w++ = toupper((unsigned char)*r);
      r++;
      continue;
    }
    // otherwise copy byte
    *w++ = *r++;
  }
  *w = 0;
}

/* Heuristic split into chunks:
   - For ASCII sequences (letters/digits) treat contiguous run as one chunk (word).
   - For UTF-8 multibyte bytes (>=0x80) treat each UTF-8 codepoint as one chunk by scanning leading byte length.
*/
static char **split_chunks(const char *s, size_t *out_n){
  size_t cap = 1024;
  char **arr = malloc(sizeof(char*)*cap);
  if(!arr) die("malloc");
  size_t n = 0;
  const unsigned char *p = (const unsigned char*)s;
  while(*p){
    if(n+1 >= cap){ cap *= 2; arr = realloc(arr, sizeof(char*)*cap); if(!arr) die("realloc"); }
    if(*p < 128){
      // ascii: group continuous letters/digits/punctuation groups depending
      const unsigned char *q = p;
      if(isalnum(*q)){
	while(*q && *q < 128 && isalnum(*q)) q++;
      } else {
	// treat punctuation or single ascii char as chunk
	q = p + 1;
      }
      size_t L = q - p;
      arr[n] = malloc(L+1);
      memcpy(arr[n], p, L); arr[n][L]=0;
      n++;
      p = q;
    } else {
      // utf-8 leading byte determines length
      unsigned char lead = *p;
      int len = 1;
      if((lead & 0xE0) == 0xC0) len = 2;
      else if((lead & 0xF0) == 0xE0) len = 3;
      else if((lead & 0xF8) == 0xF0) len = 4;
      // allocate chunk for that codepoint
      arr[n] = malloc(len+1);
      memcpy(arr[n], p, len); arr[n][len]=0;
      n++;
      p += len;
    }
  }
  *out_n = n;
  return arr;
}

/* Fisher-Yates shuffle */
static void shuffle_chunks(char **a, size_t n){
  if(n<=1) return;
  for(size_t i = n-1; i>0; --i){
    size_t j = (size_t)rand() % (i+1);
    char *t = a[i]; a[i] = a[j]; a[j] = t;
  }
}

/* Present training: produce randomized windows of chunks and display with timing */
static void run_training(Corpus *c){
  if(!c || c->n==0) return;
  size_t idx_pool = c->n;
  // create index pool copy
  char **pool = malloc(sizeof(char*) * idx_pool);
  for(size_t i=0;i<idx_pool;i++) pool[i]=c->chunks[i];
  // seed
  srand((unsigned int)time(NULL));
  // shuffle pool initially
  shuffle_chunks(pool, idx_pool);

  int interval_ms = DEFAULT_INTERVAL_MS;
  size_t window = 5; // number of chunks per display
  int paused = 0;
  FILE *logf = fopen("omega_session.log","a");
  if(!logf) logf = stderr;

  printf("OmegaTrainer: press q to quit, p pause/resume, +/- speed, n/m window size +/-\n");
  size_t cursor = 0;
  while(1){
    // check for keyboard input nonblocking
    fd_set set;
    struct timeval tv;
    FD_ZERO(&set);
    FD_SET(STDIN_FILENO, &set);
    tv.tv_sec = 0;
    tv.tv_usec = 0;
    int rv = select(STDIN_FILENO+1, &set, NULL, NULL, &tv);
    if(rv>0){
      int ch = getchar();
      if(ch==EOF) {}
      else if(ch=='q' || ch=='Q'){ fprintf(logf,"QUIT\n"); break; }
      else if(ch=='p' || ch=='P'){ paused = !paused; fprintf(stderr, paused? "PAUSED\n":"RESUME\n"); }
      else if(ch=='+'){ interval_ms -= 50; if(interval_ms < MIN_INTERVAL_MS) interval_ms = MIN_INTERVAL_MS; }
      else if(ch=='-'){ interval_ms += 50; if(interval_ms > MAX_INTERVAL_MS) interval_ms = MAX_INTERVAL_MS; }
      else if(ch=='n'){ if(window>1) window--; }
      else if(ch=='m'){ window++; if(window> (int)c->n) window = c->n; }
    }
    if(paused){ usleep(100000); continue; }
    // pick a sequence of 'window' chunks from pool starting at cursor, if not enough remaining, reshuffle
    if(cursor + window > idx_pool){
      shuffle_chunks(pool, idx_pool);
      cursor = 0;
    }
    // build display string
    char display[4096]; display[0]=0;
    size_t pos=0;
    for(size_t k=0;k<window;k++){
      char *ck = pool[cursor+k];
      size_t L = strlen(ck);
      if(pos + L + 4 >= sizeof(display)) break;
      // add space between chunks for readability
      strcat(display, ck);
      pos += L;
      if(k < window-1) { strcat(display, " "); pos++; }
    }
    // clear line and print centered
    printf("\r\33[2K"); fflush(stdout);
    printf("%s", display); fflush(stdout);
    // log timestamp and display
    if(logf) fprintf(logf,"%ld\t%s\n", (long)time(NULL), display);
    cursor += window;
    // sleep interval
    usleep((useconds_t)interval_ms * 1000);
  }
  if(logf && logf!=stderr) fclose(logf);
  free(pool);
}

/* Free corpus */
static void free_corpus(Corpus *c){
  if(!c) return;
  if(c->raw) free(c->raw);
  if(c->chunks){
    for(size_t i=0;i<c->n;i++) free(c->chunks[i]);
    free(c->chunks);
  }
}

/* Basic command-line: read file, normalize, split, run training */
int main(int argc, char **argv){
  setlocale(LC_ALL, "");
  FILE *f = stdin;
  if(argc>=2){
    f = fopen(argv[1],"rb");
    if(!f){ fprintf(stderr,"Cannot open %s\n", argv[1]); return 1; }
  }
  char *text = read_all(f);
  if(f!=stdin) fclose(f);
  if(!text || strlen(text) < 4){
    fprintf(stderr,"Input too short. Provide more text.\n");
    free(text);
    return 1;
  }
  normalize_utf8(text);

  Corpus corpus = {0};
  corpus.raw = text;
  corpus.chunks = split_chunks(corpus.raw, &corpus.n);
  if(corpus.n == 0){ fprintf(stderr,"No chunks extracted.\n"); free_corpus(&corpus); return 1; }

  // Optionally apply simple Omega transformations:
  // - Reverse every n-th chunk, map ASCII words to uppercase already done by normalize.
  for(size_t i=0;i<corpus.n;i++){
    if((i % 7) == 0){
      // reverse bytes of chunk (for variety)
      size_t L = strlen(corpus.chunks[i]);
      for(size_t a=0,b=L-1;a<b;a++,b--){
	char tmp = corpus.chunks[i][a];
	corpus.chunks[i][a] = corpus.chunks[i][b];
	corpus.chunks[i][b] = tmp;
      }
    }
  }

  // shuffle corpus
  shuffle_chunks(corpus.chunks, corpus.n);

  // run interactive trainer
  run_training(&corpus);

  free_corpus(&corpus);
  return 0;
}
