#include <stdio.h>
int parse_and_run(const char *path);
int main(int argc,char **argv){ const char *p = (argc>=2)?argv[1]:"examples/objects.omega"; return parse_and_run(p); }
