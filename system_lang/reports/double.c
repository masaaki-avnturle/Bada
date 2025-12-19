#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_COMMANDS 1000
#define MAX_LENGTH 256

typedef struct {
  char command[MAX_LENGTH];
} Command;

void processFile(FILE *inputFile, FILE *outputFile, Command commands[], int *commandCount, int isFirstFile) {
  char line[MAX_LENGTH];
  int inDocument = 0;

  while (fgets(line, sizeof(line), inputFile)) {
    // Handle the first file's document class and packages
    if (isFirstFile) {
      if (strstr(line, "\\documentclass{jsarticle}") != NULL ||
	  strstr(line, "\\usepackage[dvipdfmx]{graphicx}") != NULL ||
	  strstr(line, "\\usepackage[final]{graphicx}") != NULL ||
	  strstr(line, "\\usepackage{amsmath}") != NULL ||
	  strstr(line, "\\usepackage{amssymb}") != NULL ||
	  strstr(line, "\\begin{document}") != NULL ||
	  strstr(line, "\\title{") != NULL ||
	  strstr(line, "\\author{") != NULL ||
	  strstr(line, "\\date{") != NULL ||
	  strstr(line, "\\maketitle") != NULL) {
	fprintf(outputFile, "%s", line);
	if (strstr(line, "\\begin{document}") != NULL) {
	  inDocument = 1;
	}
	continue;
      }
    } else {
      // For subsequent files, skip document class and package declarations
      if (strstr(line, "\\documentclass{jsarticle}") != NULL ||
	  strstr(line, "\\usepackage") != NULL) {
	continue;
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

    // If in document, print the line
    if (inDocument) {
      fprintf(outputFile, "%s", line);
    }
  }
}

int main(int argc, char *argv[]) {
  if (argc < 3) {
    fprintf(stderr, "Usage: %s output.tex input1.tex [input2.tex ...]\n", argv[0]);
    return EXIT_FAILURE;
  }

  FILE *outputFile = fopen(argv[1], "w");
  if (outputFile == NULL) {
    perror("Failed to open output file");
    return EXIT_FAILURE;
  }

  Command commands[MAX_COMMANDS];
  int commandCount = 0;

  // Process each input file
  for (int i = 2; i < argc; i++) {
    FILE *inputFile = fopen(argv[i], "r");
    if (inputFile == NULL) {
      perror("Failed to open input file");
      fclose(outputFile);
      return EXIT_FAILURE;
    }

    processFile(inputFile, outputFile, commands, &commandCount, (i == 2));
    fclose(inputFile);
  }

  fclose(outputFile);
  return EXIT_SUCCESS;
}
