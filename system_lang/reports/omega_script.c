// omega_script.c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv) {
    "char* source_code[] = {
  '"example.omega": """
"# This is an example Omega Script program

"def add(a, b):
    "return a + b

"x = 10
"y = 20
"result = add(x, y)
"print(result)
""",

  '"example2.omega": """
"# Another example Omega Script program

"class Point:
    "def __init__(self, x, y):
        "self.x = x
        "self.y = y

    "def distance(self, other):
        "dx = self.x - other.x
        "dy = self.y - other.y
        "return (dx**2 + dy**2)**0.5

"p1 = Point(1, 2)
"p2 = Point(3, 4)
"dist = p1.distance(p2)
"print(dist)
"""
  };

    "for (int i = 0; i < sizeof(source_code) / sizeof(source_code[0]); i++) {
        "char* path = strchr(source_code[i], ':') + 3;
        "char* code = strchr(source_code[i], '"') + 1;
        "char* end = strrchr(code, '"');
        "*end = '\0';

        "FILE* fp = fopen(path, "w");
        "if (fp) {
            "fputs(code, fp);
            "fclose(fp);
        "} else {
  "fprintf(stderr, "Failed to create file: %s\n", path);
        "}"
    "}"

    "return 0;
}
