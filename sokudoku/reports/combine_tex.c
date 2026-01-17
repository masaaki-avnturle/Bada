#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_LINE_LENGTH 1024

void combine_tex_files(const char *output_file, char *input_files[], int num_files) {
  FILE *out_fp = fopen(output_file, "w");
  if (!out_fp) {
    perror("Error opening output file");
    return;
  }

  char line[MAX_LINE_LENGTH];
  int first_file = 1;

  // 最初のファイルのヘッダ部分を書き込む
  fputs("\\documentclass{jsarticle}\n", out_fp);
  fputs("\\usepackage[dvipdfmx,final]{graphicx}\n", out_fp);
  fputs("\\usepackage{amsmath}\n", out_fp);
  fputs("\\usepackage{amssymb}\n", out_fp);
  fputs("\\usepackage{chemfig}\n", out_fp);
  fputs("\\begin{document}\n", out_fp);

  for (int i = 0; i < num_files; i++) {
    FILE *in_fp = fopen(input_files[i], "r");
    if (!in_fp) {
      perror("Error opening input file");
      continue;
    }

    if (first_file) {
      // 最初のファイルの内容をそのまま書き込む
      while (fgets(line, sizeof(line), in_fp)) {
	fputs(line, out_fp);
	if (strstr(line, "\\maketitle") != NULL) {
	  first_file = 0; // 最初のファイルのタイトルまで書き込んだら次のファイルへ
	}
      }
    } else {
      // 2回目以降のファイルの処理
      while (fgets(line, sizeof(line), in_fp)) {
	// 各ファイルの内容を処理
	if (strstr(line, "\\documentclass{jsarticle}") != NULL ||
	    strstr(line, "\\usepackage[dvipdfmx,final]{graphicx}") != NULL ||
	    strstr(line, "\\usepackage{amsmath}") != NULL ||
	    strstr(line, "\\usepackage{amssymb}") != NULL ||
	    strstr(line, "\\usepackage{chemfig}") != NULL ||
	    strstr(line, "\\begin{document}") != NULL ||
	    strstr(line, "\\end{document}") != NULL) {
	  // これらの行はスキップ
	  continue;
	}
                
	// セクションとしてタイトルを設定
	if (strstr(line, "\\maketitle") != NULL) {
	  fputs("\\section{", out_fp);
	  char title[MAX_LINE_LENGTH];
	  // ファイル名をタイトルとして使用
	  snprintf(title, sizeof(title), "%s", input_files[i]);
	  title[strcspn(title, ".")] = 0; // 拡張子を削除
	  fputs(title, out_fp);
	  fputs("}\n", out_fp);
	}

	// 残りの行を出力
	fputs(line, out_fp);
      }
    }
    fclose(in_fp);
  }

  fputs("\\end{document}\n", out_fp); // 最後にend{document}を追加
  fclose(out_fp);
																																			      }

int main(int argc, char *argv[]) {
  if (argc < 3) {
    printf("Usage: %s output.tex input1.tex input2.tex ...\n", argv[0]);
    return 1;
  }

  combine_tex_files(argv[1], &argv[2], argc - 2);
  printf("TeX files combined successfully into %s\n", argv[1]);

  return 0;
}
