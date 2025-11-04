#include <stdio.h>
int parse_and_run(const char *path);
int main(int argc, char **argv){ const char *p = (argc >= 2) ? argv[1] : "examples/sample5.omega"; printf("[omega-bin] running %s\n", p); return parse_and_run(p); }
