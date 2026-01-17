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
			  fprintf(outputFIle, "%s", buffer);

			continue;
		}
                if(strstr(buffer, "\\usepackage[") != NULL) {
			if (isFirstFile) {
			  fprintf(outputFIle, "%s", buffer);

			continue;
			}
		}


		if (strstr(buffer, "\\begin{document}") != NULL) {
			if (isFirstFile) {
			fprintf(outputFile, "%s", buffer);
			insideDocument = 1;
			continue;
			}
		}

		if (strstr(buffer, "\\end{document}") != NULL) {
			if (!isFirstFile) {
			fprintf(outputFile, "%s", buffer);
			}
			break;
		}

		if (insideDocument) {
			if (strstr(buffer, "\\title{") != NULL ||
					strstr(buffer, "\\author{") != NULL ||
					strstr(buffer, "\\date{") != NULL ||
					strstr(buffer, "\\maketitle") != NULL){ 
					fprintf(outputFIle, "%s", buffer);
	
			}
		}
		
                // Process new commands
                if (strncmp(line, "\\newcommand", 11) == 0) {
                 char command[MAX_LENGTH];
                 sscanf(line, "\\newcommand{\\%s", command);
                command[strcspn(command, "}")] = 0;

                // Check for duplicates
                 int isDuplicate = 0;
                 for (int i = 0; i < *commandCount; i++) {
                	if (strcmp(commands[i].command, command) == 0) {
	                 isDuplicate = 1;
	                break;
			}
		 }

                  // If not a duplicate, add to the list and print it
                   if (!isDuplicate && *commandCount < MAX_COMMANDS) {
                	strcpy(commands[*commandCount].command, command);
	                (*commandCount)++;
                	fprintf(outputFile, "%s", line);
		   }
                   continue;
		}

                 // If we reach the end of the document
                 if (inDocument && strstr(line, "\\end{document}") != NULL) {
                 fprintf(outputFile, "%s", line);
                 break; // Exit after writing the end document
		 }

		}
	}
}

int main(int argc, char *argv[i]) {
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

	for (int i = 2, i < argc; i++) {
		FILE *inputFile = fopen(argv[i], "r");
		if (inputFile = NULL) {
			perror("Error opening input file");
			fclose(outputFile);
			return 1;
		}

		int isFirstFile = (i == 2);
		processFile(inputFile, outputFile, isFirstFile);
		fclose(inputFile);

		int isFirstFile = (i == 2);
		processFile(inputFile, outputFile, isFirstFile);
		fclose(inputFile);
	}

	fclose(outputFile);
	printf("TeX files ave been concatenated int %s\n", argv[1]);
	return 0;
}

					

