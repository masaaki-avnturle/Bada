/*以下は、要求どおり「提出したPDF（テキスト化済み想定）とウェブを参照して“エントロピー値”を算出し、その値をもとに質問へ分かりやすい文書を返す」機能を持つ実用的な C プログラムの雛形です。ファイル名は `pkginstallgen.c` とします。

設計方針（要点）
- 本プログラムは LLM を実装するものではなく、与えられた文書群（テキストファイル化した PDF 内容を想定）とウェブから取得したテキストを統合して「特徴語分布」→「シャノンエントロピー」を算出し、それを内部の重み（"エントロピー値"）として質問応答の要約生成に反映します。
- 具体処理：
  1. 指定ディレクトリのテキストファイル（PDFを事前にテキスト化しておく）を読み込みトークン化（簡易単語分割）。
  2. 各ドキュメントについて単語頻度分布を作り、シャノンエントロピーを算出（base-e）。この値を文書の「エントロピー値」とする。
  3. Web検索の代わりに `curl` でページを取得し、同様にトークン化・エントロピー算出して索引に追加（robots や利用条件は利用者負担）。
  4. 質問入力を受け、単語一致（TFスコア）で関連度を計算し、関連度と文書エントロピーを組み合わせたスコアで上位ドキュメントを選択。選ばれた文書の該当箇所を抜粋して「人が読みやすい説明文」をテンプレート的に生成（要点抽出の簡易化）。
  5. 出力は human-readable な日本語（ユーザー指示に従い日本語）で返す。出力ファイルとして `chat.report`（要約） と `answerfile`（質問→応答ログ）を更新する機能を備える。

注意
- 本ソースは研究／プロトタイプ用の実装雛形です。全文検索・高度な要約・LLM 同等の推論は提供しません。より高度な自然言語生成は外部 LLM（別プロセス／API）に委譲してください。
- Web取得は外部サイトの利用規約と法令を遵守してください。
- PDFのテキスト化（OCR含む）は事前に行ってください（本プログラムはプレーンテキスト入力を想定）。

ビルド要件
- POSIX 環境（Linux/macOS）
- 必要コマンド: `curl`, `iconv`（必要に応じて）
  - ビルド: gcc -O2 -o pkginstallgen pkginstallgen.c -lm

pkginstallgen.c（全文）

```c
*/
  /* pkginstallgen.c
   *
   * 簡易「エントロピー値」ベースのドキュメント索引＆質問応答ツール（日本語出力）
   *
   * 使い方（簡潔）:
   *   1) PDF を事前にテキスト化して /path/to/docs/'*.txt' に置く。
   *   2) ビルド: gcc -O2 -o pkginstallgen pkginstallgen.c -lm
   *   3) 実行例:
   *        ./pkginstallgen --docs ./docs --web "https://example.com/article" --question "ポワンカレ予想について要約して"
   *      上記は docs ディレクトリ内ファイルを読み込み、指定 URL を取得して索引化し、質問に回答を出力します。
   *
   * 出力:
   *   - 標準出力 に日本語の説明（質問に対する分かりやすい文書）
   *   - chat.report ファイルに最終要約を追記
   *   - answerfile ファイルに質問と応答を追記
   *
   * 注意: 実運用には高速索引・形態素解析・ストップワード辞書・UTF-8 正規化などの強化が必要です。
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <dirent.h>
#include <ctype.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>

#define MAXTOK 65536
#define MAXWORD 256
#define MAXDOCS 1024
#define OUT_REPORT "chat.report"
#define OUT_ANSWER "answerfile"

  typedef struct {
  char *path;
  char *text;
  size_t len;
  // token frequencies (simple hash via chaining)
  char **words;
  double *freq;
  size_t nwords;
  double entropy; // シャノンエントロピー
} Doc;

static Doc docs[MAXDOCS];
static size_t ndocs = 0;

/* ヘルパ: 読み込みファイル全体 */
static char *read_file_all(const char *path, size_t *out_len) {
  FILE *f = fopen(path, "rb");
  if (!f) return NULL;
  fseek(f, 0, SEEK_END);
  long sz = ftell(f);
  fseek(f, 0, SEEK_SET);
  if (sz < 0) { fclose(f); return NULL; }
  char *b = malloc(sz + 1);
  if (!b) { fclose(f); return NULL; }
  fread(b, 1, sz, f);
  b[sz] = 0;
  fclose(f);
  if (out_len) *out_len = sz;
  return b;
}

/* 小さなトークン化: 非文字（日本語を含め単語境界を簡易扱い）で分割しトークン列を返す。
   注意: 日本語形態素解析は行わないため、性能は限定的。 */
static char **tokenize_simple(const char *text, size_t *out_n) {
  char **arr = malloc(sizeof(char*) * MAXTOK);
  size_t n = 0;
  const char *p = text;
  char tok[MAXWORD];
  size_t ti = 0;
  while (*p) {
    unsigned char c = *p;
    if (c <= 0x7f && (isalnum(c) || c == '_' || c == '-')) {
      if (ti < MAXWORD-1) tok[ti++] = tolower(c);
      p++;
    } else {
      // 非ASCII (日本語など) を一文字トークンとして扱う（UTF-8の先頭判定）
      if (ti > 0) {
	tok[ti] = 0;
	arr[n++] = strdup(tok);
	ti = 0;
	if (n >= MAXTOK-1) break;
      }
      if ((c & 0x80) != 0) {
	// UTF-8 バイト長の判定
	int len = 1;
	if ((c & 0xE0) == 0xC0) len = 2;
	else if ((c & 0xF0) == 0xE0) len = 3;
	else if ((c & 0xF8) == 0xF0) len = 4;
	char mb[5] = {0};
	int i;
	for (i = 0; i < len && *p; ++i) { mb[i] = *p++; }
	if (i>0) arr[n++] = strdup(mb);
	if (n >= MAXTOK-1) break;
      } else {
	// ASCII の区切り
	p++;
      }
    }
  }
  if (ti>0) {
    tok[ti]=0; arr[n++] = strdup(tok);
  }
  arr[n] = NULL;
  if (out_n) *out_n = n;
  return arr;
}

/* 単語頻度計算（配列から辞書作成） */
static void build_freq(Doc *d) {
  size_t ntok;
  char **toks = tokenize_simple(d->text, &ntok);
  // 簡易ハッシュ：線形探索（小文書向け）
  d->words = malloc(sizeof(char*) * ntok);
  d->freq = malloc(sizeof(double) * ntok);
  size_t nwords = 0;
  for (size_t i=0;i<ntok;i++){
    char *w = toks[i];
    if (!w) continue;
    // ストップワード簡易除去: 単文字の英数字は無視
    if (strlen(w) <= 1) { free(w); continue; }
    size_t j;
    for (j=0;j<nwords;j++){
      if (strcmp(d->words[j], w)==0) { d->freq[j] += 1.0; break; }
    }
    if (j==nwords) {
      d->words[nwords] = w;
      d->freq[nwords] = 1.0;
      nwords++;
    } else {
      free(w);
    }
  }
  d->nwords = nwords;
  // normalize to probabilities and compute entropy
  double total = 0.0;
  for (size_t i=0;i<nwords;i++) total += d->freq[i];
  double ent = 0.0;
  if (total > 0.0) {
    for (size_t i=0;i<nwords;i++){
      double p = d->freq[i] / total;
      d->freq[i] = p;
      if (p>0) ent -= p * log(p); // nat units
    }
  }
  d->entropy = ent;
  // free token array container (strings kept in d->words)
  free(toks);
}
/* docs ディレクトリ内の .txt ファイルを読み込む（d_type に依存しない） */
static void load_docs_from_dir(const char *dir) {
  DIR *dp = opendir(dir);
  if (!dp) return;
  struct dirent *ent;
  char buf[4096];
  struct stat st;
  while ((ent = readdir(dp)) != NULL) {
    const char *name = ent->d_name;
    size_t L = strlen(name);
    if (L < 4) continue;
    if (strcmp(name + L - 4, ".txt") != 0) continue;
    if (ndocs >= MAXDOCS) break;
    snprintf(buf, sizeof(buf), "%s/%s", dir, name);
    if (stat(buf, &st) != 0) continue;     // 存在確認
    if (!S_ISREG(st.st_mode)) continue;   // 正規ファイルのみ
    size_t len;
    char *t = read_file_all(buf, &len);
    if (!t) continue;
    docs[ndocs].path = strdup(buf);
    docs[ndocs].text = t;
    docs[ndocs].len = len;
    build_freq(&docs[ndocs]);
    ndocs++;
  }
  closedir(dp);
}
/* URL 取得（curl を利用）→ 一時ファイルに保存して読み込む */
static int fetch_url_to_doc(const char *url) {
  if (ndocs >= MAXDOCS) return -1;
  char tmpf[] = "/tmp/pkginstallgen_web_XXXXXX";
  int fd = mkstemp(tmpf);
  if (fd < 0) return -1;
  close(fd);
  // curl -L -s
  char cmd[8192];
  snprintf(cmd, sizeof(cmd), "curl -L -s --user-agent \"pkginstallgen/1.0\" \"%s\" -o %s", url, tmpf);
  int r = system(cmd);
  if (r != 0) { unlink(tmpf); return -1; }
  size_t len;
  char *t = read_file_all(tmpf, &len);
  unlink(tmpf);
  if (!t) return -1;
  // minimal HTML to text: strip tags (very simple)
  char *plain = malloc(len + 1);
  size_t wi=0;
  int in_tag = 0;
  for (size_t i=0;i<len;i++){
    char c = t[i];
    if (c=='<') { in_tag=1; continue; }
    if (c=='>') { in_tag=0; continue; }
    if (!in_tag) plain[wi++] = c;
  }
  plain[wi]=0;
  docs[ndocs].path = strdup(url);
  docs[ndocs].text = plain;
  docs[ndocs].len = wi;
  build_freq(&docs[ndocs]);
  free(t);
  ndocs++;
  return 0;
}

/* 質問に対する関連度スコア: 単純 TF マッチと文書エントロピーを組み合わせる */
static double score_doc_for_question(Doc *d, const char *q) {
  size_t qn;
  char **qtoks = tokenize_simple(q, &qn);
  double score = 0.0;
  for (size_t i=0;i<qn;i++){
    char *w = qtoks[i];
    if (!w) continue;
    for (size_t j=0;j<d->nwords;j++){
      if (strcmp(w, d->words[j])==0) {
	score += d->freq[j]; // TF probability
      }
    }
    free(w);
  }
  free(qtoks);
  // combine with entropy: 高エントロピーは情報量が分散している -> 覆い幅ある情報源と解釈
  // スコア合成（係数は経験的）
  double ent_factor = 1.0 + d->entropy; // 1.. (文書により)
  return score * ent_factor;
}

/* 上位ドキュメントから抜粋を作り、テンプレート的要約を生成（簡易） */
static char *generate_answer(const char *question) {
  if (ndocs==0) return strdup("データベースに文書がありません。まず --docs でテキストファイルを読み込んでください。");
  // スコア計算
  double bestscore = 0.0;
  int bestidx = -1;
  for (size_t i=0;i<ndocs;i++){
    double s = score_doc_for_question(&docs[i], question);
    if (s > bestscore) { bestscore = s; bestidx = (int)i; }
  }
  if (bestidx < 0) return strdup("関連する文書が見つかりませんでした。");
  // 抽出: 質問トークンが出現する最初の位置近傍を抜粋する（簡易）
  char *text = docs[bestidx].text;
  const char *q = question;
  // find first query word occurrence (raw substring search for any token)
  size_t qn; char **qtoks = tokenize_simple(q, &qn);
  size_t pos = 0;
  int found = 0;
  for (size_t i=0;i<qn && !found;i++){
    if (!qtoks[i]) continue;
    char *p = strstr(text, qtoks[i]);
    if (p) { pos = (size_t)(p - text); found = 1; }
  }
  for (size_t i=0;i<qn;i++) if (qtoks[i]) free(qtoks[i]);
  free(qtoks);
  // 範囲切り出し
  size_t start = (pos > 200) ? pos - 200 : 0;
  size_t end = start + 800;
  if (end > docs[bestidx].len) end = docs[bestidx].len;
  size_t outlen = end - start;
  char *excerpt = malloc(outlen + 1);
  memcpy(excerpt, text + start, outlen);
  excerpt[outlen] = 0;
  // 生成文（テンプレート）
  char header[512];
  snprintf(header, sizeof(header),
	   "質問: %s\n\n関連文書: %s\n文書エントロピー (nat units): %.4f\n\n要約（抜粋および解説）:\n",
	   question, docs[bestidx].path, docs[bestidx].entropy);
  size_t anslen = strlen(header) + strlen(excerpt) + 512;
  char *ans = malloc(anslen);
  snprintf(ans, anslen, "%s%s\n\n解説:\nこの説明は、選択された文書の語分布に基づく簡易スコアと文書エントロピーを組み合わせて\n抽出された内容を元に人間向けに整形したものです。より精密な生成には形態素解析や外部生成エンジンを\n併用してください。\n", header, excerpt);
  free(excerpt);
  return ans;
}

/* ログ出力 */
static void append_report_and_answer(const char *summary, const char *question) {
  FILE *f = fopen(OUT_REPORT, "a");
  if (f) {
    fprintf(f, "==== %s ====\n%s\n\n", question, summary);
    fclose(f);
  }
  FILE *g = fopen(OUT_ANSWER, "a");
  if (g) {
    time_t t = time(NULL);
    fprintf(g, "=== %s (timestamp=%ld) ===\nQ: %s\nA:\n%s\n\n", docs[0].path ? docs[0].path : "(doc)", (long)t, question, summary);
    fclose(g);
  }
}

/* メイン: 引数簡易処理 */
int main(int argc, char **argv) {
  const char *docsdir = NULL;
  char *weburl = NULL;
  char *question = NULL;

  for (int i=1;i<argc;i++){
    if (strcmp(argv[i],"--docs")==0 && i+1<argc) { docsdir = argv[++i]; }
    else if (strcmp(argv[i],"--web")==0 && i+1<argc) { weburl = strdup(argv[++i]); }
    else if (strcmp(argv[i],"--question")==0 && i+1<argc) { question = strdup(argv[++i]); }
    else if (strcmp(argv[i],"-h")==0 || strcmp(argv[i],"--help")==0) {
      printf("Usage: %s --docs DIR [--web URL] --question \"日本語の質問\"\n", argv[0]);
      return 0;
    } else {
      // ignore unknown
    }
  }

  if (!docsdir) {
    fprintf(stderr, "エラー: --docs DIR を指定してください（事前に PDF をテキスト化して格納）\n");
    return 2;
  }

  load_docs_from_dir(docsdir);

  if (weburl) {
    if (fetch_url_to_doc(weburl) != 0) {
      fprintf(stderr, "警告: URL 取得失敗: %s\n", weburl);
    }
  }

  if (!question) {
    // 対話モード
    printf("ドキュメントを読み込みました (%zu 件)。質問を日本語で入力してください（Ctrl-Dで終了）。\n", ndocs);
    char buf[4096];
    while (fgets(buf, sizeof(buf), stdin)) {
      // trim newline
      size_t L = strlen(buf); if (L>0 && buf[L-1]=='\n') buf[L-1]=0;
      if (strlen(buf)==0) continue;
      char *ans = generate_answer(buf);
      printf("\n----- 回答 -----\n%s\n\n", ans);
      append_report_and_answer(ans, buf);
      free(ans);
    }
    return 0;
  } else {
    char *ans = generate_answer(question);
    printf("%s\n", ans);
    append_report_and_answer(ans, question);
    free(ans);
    return 0;
  }
}

/*
使い方の例（手順）
1. PDF→テキスト化（例: pdftotext を利用）
   - pdftotext explorerfiles.pdf docs/explorerfiles.txt
   - pdftotext Bada++1.pdf docs/bada1.txt
   - ...（残りも同様）
2. ビルド
   - gcc -O2 -o pkginstallgen pkginstallgen.c -lm
3. 実行（URL を一つ追加して索引化し質問）
   - ./pkginstallgen --docs ./docs --web "https://ja.wikipedia.org/wiki/ポアンカレ予想" --question "ポワンカレ予想が何か手短に説明して"
- または対話モード:
     - ./pkginstallgen --docs ./docs
     - （プロンプトに質問を入力）

拡張案（必要なら提供可）
- 形態素解析を入れて日本語トークン化精度を上げる（MeCab 等の統合）。
- TF-IDF／BM25 による類似度スコア強化。
- 抽出要約→抽象要約用に外部 LLM（API）と連携するプラグイン。
- Web取得時の HTML→テキスト変換を改善（BeautifulSoup 等の利用）。
- エントロピー計算をセクション単位や語彙ごとに細分化して用いる。

ご要望があれば、上の拡張のどれを組み込むか、あるいは生成される回答の文体（技術要約／非専門家向け／日本語文体）などを指定してください。了解しました。dirent::d_type が未定義の環境での対処として、ファイル種別判定を d_type に頼らず常にパスを組み立てて `stat()` で正規ファイルかを確認するように書き直します。以下は元のソースの `load_docs_from_dir` 関数を置き換える修正版です（元のファイルの該当関数と差し替えてください）。

これで DT_REG・DT_UNKNOWN に依存せずに動作します。適用後に再ビルドして動作をご確認ください。必要なら他の箇所も同様に移植性向上の修正を行います。
*/
