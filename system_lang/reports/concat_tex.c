#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024

void processFile(FILE *inputFile, FILE *outputFile, int isFirstFile) {
	char buffer[BUFFER_SIZE];
	int insideDocument = 0;
	static int hasDocumentClass = 0;

	while (fgets(buffer, sizeof(buffer), inputFile) != NULL) {
		if(strstr(buffer, "\\documentclass{jsarticle}") != NULL) {
			if (isFirstFile && !hasDocumentClass) {
				fprintf(outputFile, "%s", buffer);

				hasDocumentClass = 1;
			}
			continue;
		}

		if(strstr(buffer, "\\usepackage{") != NULL) {
			if (isFirstFile) {
			  fprintf(outputFile, "%s", buffer);

			continue;
			}
		}

		if (strstr(buffer, "\\begin{document}") != NULL) {
			fprintf(outputFile, "%s", buffer);
			insideDocument = 1;
			continue;
		}

		if (strstr(buffer, "\\end{document}") != NULL) {
			if (!isFirstFile) {
			fprintf(outputFile, "%s", buffer);
			}
			break;
		}

		if (insideDocument) {
			fprintf(outputFile, "%s", buffer);
		}
	}
}
	

int main(int argc, char *argv[]) {
	if (argc < 3) {
		fprintf(stderr, "Usage: %s output_file input_file1 inpuy_file2
				[...]\n", argv[0]);
		return 1;
	}

	FILE *outputFile = fopen(argv[1], "w");
	if (outputFile == NULL) {
		perror("Error opening output file");
		return 1;
	}

	for (int i = 2; i < argc; i++) {
		FILE *inputFile = fopen(argv[i], "r");
		if (inputFile = NULL) {
			perror("Error opening input file");
			fclose(outputFile);
			return 1;
		}

		int isFirstFile = (i == 2);
		processFile(inputFile, outputFile, isFirstFile);
		fclose(inputFile);
	}

	fclose(outputFile);
	printf("TeX files ave been concatenated int %s\n", argv[1]);
	return 0;
}

					

