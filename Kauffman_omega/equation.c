  int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "Usage: %s question.txt [source1.pdf|source2.txt|https://... ...]\n", argv[0]);
    return 1;
  }

  // Read question
  char *question = NULL;
  if (strcmp(argv[1], "-") == 0) {
    // stdin
    size_t cap=0,len=0; char buf[BUF_CHUNK];
    while (fgets(buf,sizeof(buf),stdin)) {
      size_t t=strlen(buf);
      if (len + t + 1 > cap) { size_t nc = (cap==0)?(t+BUF_CHUNK):(cap*2 + t); char *n=realloc(question,nc); if(!n){free(question);fprintf(stderr,"mem error\n");return 1;} question=n; cap=nc; }
      memcpy(question+len, buf, t); len+=t; question[len]='\0';
    }
  } else {
    question = read_file(argv[1]);
    if (!question) { fprintf(stderr,"質問ファイル読み込み失敗: %s\n", argv[1]); return 1; }
  }

  // Compute question indicators
  double Hq = shannon_entropy((unsigned char*)question, strlen(question));
  double Sq = pseudo_spectral((unsigned char*)question, strlen(question));

  // Collect templates from sources (argv[2..])
  char *templates[MAX_PARAS]; double Ht[MAX_PARAS]; double St[MAX_PARAS];
  int tcount = 0;

  for (int i=2; i<argc; ++i) {
    char *src = argv[i];
    char *text = NULL;
    if (strncmp(src, "http://", 7) == 0 || strncmp(src, "https://", 8) == 0) {
      text = fetch_url(src);
      if (!text) { fprintf(stderr,"URL取得失敗: %s\n", src); continue; }
    } else if (file_exists(src)) {
      size_t L = strlen(src);
      if (L >= 4 && strcasecmp(src + L - 4, ".pdf") == 0) {
	text = pdf_to_text(src);
	if (!text) { fprintf(stderr,"PDF解析失敗: %s\n", src); continue; }
      } else {
	text = read_file(src);
	if (!text) { fprintf(stderr,"ファイル読み込み失敗: %s\n", src); continue; }
      }
    } else {
      fprintf(stderr,"ソース無効: %s\n", src); continue;
    }
        
    // Paragraphize and pick candidate paragraphs
    char *paras[1024]; int pc = extract_paragraphs(text, paras, 1024);
    for (int p=0; p<pc && tcount < MAX_PARAS; ++p) {
      if (!is_candidate_para(paras[p])) { free(paras[p]); continue; }
      templates[tcount] = paras[p]; // keep ownership
      Ht[tcount] = shannon_entropy((unsigned char*)templates[tcount], strlen(templates[tcount]));
      St[tcount] = pseudo_spectral((unsigned char*)templates[tcount], strlen(templates[tcount]));
      tcount++;
    }
    free(text);
  }

  // If no external sources provided, also try to extract templates from question itself
  if (tcount == 0) {
    char *paras[32]; int pc = extract_paragraphs(question, paras, 32);
    for (int p=0; p<pc && tcount < MAX_PARAS; ++p) {
      if (!is_candidate_para(paras[p])) { free(paras[p]); continue; }
      templates[tcount] = paras[p];
      Ht[tcount] = shannon_entropy((unsigned char*)templates[tcount], strlen(templates[tcount]));
      St[tcount] = pseudo_spectral((unsigned char*)templates[tcount], strlen(templates[tcount]));
      tcount++;
    }
  }

  // If still none, report and exit
  if (tcount == 0) {
    printf("テンプレート候補が見つかりませんでした。PDF/Webに数式・定理風の記述が必要です。\n");
    free(question); return 0;
  }

  // Compute similarity scores and pick top-K
  typedef struct { int idx; double score; } Pair;
  Pair *pairs = malloc(sizeof(Pair) * tcount);
  for (int i=0;i<tcount;i++) { pairs[i].idx = i; pairs[i].score = sim_score(Hq, Ht[i], Sq, St[i]); }
  // Sort desc
  for (int i=0;i<tcount;i++) for (int j=i+1;j<tcount;j++) if (pairs[j].score > pairs[i].score) { Pair tmp = pairs[i]; pairs[i]=pairs[j]; pairs[j]=tmp; }

  // Detect concepts in question
  char concepts[16][128]; int ccount = detect_concepts(question, concepts, 16);

  // Output human-readable document (non-numeric main) and show selected templates/equations
  printf("=== omega report.ask (自動生成) ===\n\n");
  printf("タイトル（要旨）: 質問の情報構造に合致する外部文書から抽出した説明と方程式\n\n");
  printf("質問（要約）:\n");
  if (strlen(question) > 800) { fwrite(question,1,800,stdout); printf("...（省略）\n\n"); }
  else printf("%s\n\n", question);

  printf("検出概念: ");
  for (int i=0;i<ccount;i++) { printf("%s", concepts[i]); if (i<ccount-1) printf("、"); }
  printf("\n\n");

  printf("（主出力は分かりやすい文書です。下は選出テンプレートの原文抜粋と方程式断片です。）\n\n");

  int K = TOPK; if (K > tcount) K = tcount;
  for (int k=0;k<K;k++) {
    int idx = pairs[k].idx;
    printf("----- 選出テンプレート %d (score=%.5f) -----\n", k+1, pairs[k].score);
    // print brief meta
    printf("出典抜粋:\n");
    if (strlen(templates[idx]) > 1600) { fwrite(templates[idx],1,1600,stdout); printf("...（省略）\n"); }
    else printf("%s\n", templates[idx]);

    // extract equation-like lines
    printf("\n抽出方程式断片:\n");
    const char *p = templates[idx];
    char line[4096];
    while (*p) {
      int li=0;
      while (*p && *p!='\n' && li < (int)sizeof(line)-2) line[li++] = *p++;
      if (*p=='\n') p++;
      line[li] = '\0';
      if (strchr(line,'=') || strstr(line,"ζ") || strstr(line,"∇") || strstr(line,"Δ") || strstr(line,"Gamma(") || strchr(line,'$')) {
	printf("%s\n", line);
      }
    }
    printf("\n\n");
  }

  // Compose a concise, human-friendly explanation (non-numeric) based on best template
  int best = pairs[0].idx;
  printf("=== 合成解答（分かりやすい文書） ===\n\n");

  // Simple natural-language synthesis: describe relation between question and template concepts
  printf("この回答は、質問文の情報的特徴（例: 記述の多様性や記号的構造）と、外部文書から抽出した説明/方程式断片の\n");
  printf("情報的特徴（シャノンエントロピーやスペクトル様指標）が類似している点を基準に自動選出したテンプレートに基づきます。\n\n");

  // Show plain-language description referencing template
  printf("- 選出されたテンプレートは、次のような主題に関係しています: ");
  for (int i=0;i<ccount;i++) { printf("%s", concepts[i]); if (i<ccount-1) printf("、"); }
  printf("。\n\n");

  // Provide intuitive summary of equations observed
  printf("- 観察された方程式断片の直感的な説明（例）:\n");
  printf("  ・ゼータ関数・スペクトル解析に触れる断片は、スペクトルの分布とその零点や極から幾何学的／解析的情報を抽出する方針を示します。\n");
  printf("  ・ヤン＝ミルズや質量ギャップに関する断片は、ゲージ場の非線形方程式とそのスペクトル下限に関する議論を含みます。\n");
  printf("  ・ナビエ–ストークスに関連する断片は、速度場の発散・渦度・スペクトル分布の評価に基づく記述です。\n\n");

  // Suggest generated equation (constructed from template fragments): present as explanation rather than raw math
  printf("- 方程式生成（説明的）:\n");
  printf("  選出テンプレートの方程式断片を組み合わせると、以下のような説明的方程式群が得られます（数式は原文の断片を参照してください）:\n\n");
  // Print extracted equation fragments from best template as representative
  printf("  代表断片:\n");
  {
    const char *p = templates[best];
    char line[4096];
    int any=0;
    while (*p) {
      int li=0;
      while (*p && *p!='\n' && li < (int)sizeof(line)-2) line[li++] = *p++;
      if (*p=='\n') p++;
      line[li]='\0';
      if (strchr(line,'=') || strstr(line,"ζ") || strstr(line,"∇") || strstr(line,"Δ") || strstr(line,"Gamma(") || strchr(line,'$')) {
	printf("    %s\n", line);
	any=1;
      }
    }
    if (!any) printf("    （代表的方程式断片は見つかりませんでした、テンプレート本文を参照してください）\n");
  }
  printf("\n");

  // Internal references: numeric indicators
  printf("=== 内部参照（解析数値） ===\n");
  printf("質問エントロピー H(q): %.6f bits/byte\n", Hq);
  printf("質問擬似スペクトル Sq: %.6f\n\n", Sq);
  printf("上位テンプレート指標（index, H, S, score）:\n");
  for (int k=0;k<K;k++) {
    int idx = pairs[k].idx;
    printf(" %d: H=%.6f S=%.6f score=%.6f\n", k+1, Ht[idx], St[idx], pairs[k].score);
  }
  printf("\n");

  // Cleanup
  for (int i=0;i<tcount;i++) free(templates[i]);
  free(pairs);
  free(question);
  return 0;
}


