/* bin/generate_analyze.c */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>

static int run_pdftotext(const char *inpdf, const char *outtxt) {
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "./scripts/pdftotext-wrapper.sh '%s' '%s'", inpdf, outtxt);
    int rc = system(cmd);
    return rc;
}

static int analyze_text(const char *txtpath) {
    FILE *f = fopen(txtpath, "r");
    if (!f) { perror("fopen"); return 1; }
    char buf[4096]; size_t words = 0, lines = 0;
    while (fgets(buf, sizeof(buf), f)) {
        lines++;
        char *p = buf;
        while (*p) {
            while (*p && isspace((unsigned char)*p)) p++;
            if (*p) { words++; while (*p && !isspace((unsigned char)*p)) p++; }
        }
    }
    fclose(f);
    printf("Text analysis: lines=%zu words=%zu\n", lines, words);
    return 0;
}

static int call_python_generator(const char *language) {
    char cmd[1024]; snprintf(cmd, sizeof(cmd), "python3 ./lib/math_expression_generator.py --language %s", language);
    FILE *p = popen(cmd, "r"); if (!p) { perror("popen"); return 1; }
    char line[1024];
    if (fgets(line, sizeof(line), p)) {
        printf("Generated expression (%s): %s", language, line);
    } else {
        printf("No output from python generator\n");
    }
    pclose(p);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s <input.pdf> [language]\n", argv[0]); return 2; }
    const char *inpdf = argv[1]; const char *lang = (argc >= 3) ? argv[2] : "python";
    char outtxt[1024]; snprintf(outtxt, sizeof(outtxt), "data/converted.txt");
    if (run_pdftotext(inpdf, outtxt) != 0) { fprintf(stderr, "pdftotext failed\n"); return 1; }
    if (analyze_text(outtxt) != 0) { fprintf(stderr, "analysis failed\n"); return 1; }
    if (call_python_generator(lang) != 0) { fprintf(stderr, "python generator failed\n"); return 1; }
    return 0;
}
