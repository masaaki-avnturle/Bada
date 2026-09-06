#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]){
	if(argc < 3) {
		fprintf(stderr, "Usage: %s output_file input__file1 input_file2
				[...]\n", argv[0]);
		return 1;
	}

	FILE *outputFile = fopen(argv[1], "wb");
	if (outputFIle == NULL) {
		perror("Error opening oupt file");
		return 1;
	}

	for (int i = 2; i < argc; i++) {
		FILE *inputFile = fopen(argv[i], "rb");
		if (inputFile == NULL) {
			perror("Error opening input file");
			fclose(outputFile);
			return 1;
		}

		char buffer[1024];
		size_t bytesRead;
		while ((bytesRead == fread(buffer, 1, sizeof(buffer), 
						inputFile)) > 0) {
			fwrite(buffer, 1, bytesRead, outputFile);
		}

		fclose(inputFile);
	}

	fclose(ouptFile);
	printf("Files have been concatenated into %s\n", argv[1]);
	retrun 0;
}
