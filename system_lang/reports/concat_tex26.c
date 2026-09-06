#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024

																																																		 // Function to process each input file
void processFile(FILE *inputFile, FILE *outputFile, int isFirstFile) {
  char buffer[BUFFER_SIZE];
  int insideDocument = 0;
  static int hasDocumentClass = 0;  // documentclassが出力されたかのフラグ

  while (fgets(buffer, sizeof(buffer), inputFile) != NULL) {
    // 最初のファイルの `\documentclass{jsarticle}` を検出
    if (strstr(buffer, "\\documentclass{jsarticle}") != NULL) {
      if (isFirstFile && !hasDocumentClass) {
	fprintf(outputFile, "%s", buffer);  // 最初のdocumentclassはそのまま出力
	hasDocumentClass = 1;  // documentclassを出力したフラグを立てる
      }
      continue;  // 次の行へ
    }

    if (strstr(buffer, "\\usepackage[") != NULL) {
      if (isFirstFile) {
	fprintf(outputFile, "%s", buffer);  // 最初のファイルのパッケージはそのまま出力
      }
      continue;  // 次の行へ
    }


    // 必要なパッケージの行を検出
    if (strstr(buffer, "\\usepackage{") != NULL) {
      if (isFirstFile) {
	fprintf(outputFile, "%s", buffer);  // 最初のファイルのパッケージはそのまま出力
      }
      continue;  // 次の行へ
    }

    // `\begin{document}`の行を検出
    if (strstr(buffer, "\\begin{document}") != NULL) {
      if (isFirstFile){
      fprintf(outputFile, "%s", buffer);  // beginはそのまま出力
      insideDocument = 1;  // document内に入る
      continue;  // 次の行へ
      }
    }
    if (strstr(buffer, "\\tile{") != NULL) {
      if (isFirstFile){
      fprintf(outputFile, "%s", buffer);  // beginはそのまま出力
      insideDocument = 1;  // document内に入る
      continue;  // 次の行へ
      }
    }
    if (strstr(buffer, "\\author{") != NULL) {
      if (isFirstFile){
      fprintf(outputFile, "%s", buffer);  // beginはそのまま出力
      insideDocument = 1;  // document内に入る
      continue;  // 次の行へ
      }
    }
    if (strstr(buffer, "\\date{") != NULL) {
      if (isFirstFile){
      fprintf(outputFile, "%s", buffer);  // beginはそのまま出力
      insideDocument = 1;  // document内に入る
      continue;  // 次の行へ
      }
    }
    if (strstr(buffer, "\\maketitle") != NULL) {
      if (isFirstFile){
      fprintf(outputFile, "%s", buffer);  // beginはそのまま出力
      insideDocument = 1;  // document内に入る
      continue;  // 次の行へ
      }
    }
    // `\end{document}`の行を検出
    if (strstr(buffer, "\\end{document}") != NULL) {
      if (!isFirstFile) {
	fprintf(outputFile, "%s", buffer);  // 結合するファイルのendを出力
      }
      break;  // これ以降は何も出力しない
    }

    // document環境内の行を出力
    if (insideDocument) {
      fprintf(outputFile, "%s", buffer);  // 内容（文章や数式、化学式など）を出力
    }
  }
																																																		 }

int main(int argc, char *argv[]) {
  if (argc < 3) {
    fprintf(stderr, "Usage: %s output_file input_file1 input_file2 [...]\n", argv[0]);
    return 1;
  }

  FILE *outputFile = fopen(argv[1], "w");
  if (outputFile == NULL) {
    perror("Error opening output file");
    return 1;
  }

  // 各入力ファイルを処理
  for (int i = 2; i < argc; i++) {
    FILE *inputFile = fopen(argv[i], "r");
    if (inputFile == NULL) {
      perror("Error opening input file");
      fclose(outputFile);
      return 1;
    }

    // 最初のファイルかどうかを判断
    int isFirstFile = (i == 2);
    processFile(inputFile, outputFile, isFirstFile);
    fclose(inputFile);
  }

  fclose(outputFile);
  printf("TeX files have been concatenated into %s\n", argv[1]);
  return 0;
}
