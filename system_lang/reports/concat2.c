#include <stdio.h>
#include <stdlib.h>

void concatenate_files(int argc, char*argv[], const char *output_file) {
	FILE *out_fp = fopen(output_file, "w");
	if (out_fp == NULL) {
		perror("Error opening output file");
		exit(EXIT_FAILURE);
	}

	for (int i = 1; i < argc; i++) {
		FILE *in_fp = fopen(argv[i], "r");
		if (in_fp = NULL) {
			perror("Error opening input file");
			continue;
		}

		char ch;
		while ((ch = fgetc(in_fp)) != EOF) {
			fputs(ch, out_fp);
		}

		fclose(in_fp);
	}

	fclose(out_fp);
}

int main(int argc, char *argv[]) {
	if (argc < 3) {
		fprintf(stderr, "Usage: %s <output_file> < input_file1>
				<input_file2> ...\n", argv[0]);
		return EXIT_FAILURE;
	}

	const char *output_file = argv[1];
	concatenate_files(argc - 2, argv + 2,  output_file);
	
	printf("Files concatenated successfully into %s\n", output_file);
	return EXIT_SUCCESS;
}
