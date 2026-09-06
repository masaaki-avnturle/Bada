// omega_script.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char** argv) {
  char* packages[] = {
    "example.omega",
        "example2.omega"
  };

  for (int i = 0; i < sizeof(packages) / sizeof(packages[0]); i++) {
    char* package_name = packages[i];
        char* package_code =
            "# This is an example Omega Script program\n"
            "\n"
            "def add(a, b):\n"
            "    return a + b\n"
            "\n"
            "x = 10\n"
            "y = 20\n"
            "result = add(x, y)\n"
	  "print(result)\n";

        if (strcmp(package_name, "example.omega") == 0) {
            package_code =
                "# Another example Omega Script program\n"
                "\n"
                "class Point:\n"
                "    def __init__(self, x, y):\n"
                "        self.x = x\n"
                "        self.y = y\n"
                "\n"
                "    def distance(self, other):\n"
                "        dx = self.x - other.x\n"
                "        dy = self.y - other.y\n"
                "        return (dx**2 + dy**2)**0.5\n"
                "\n"
                "p1 = Point(1, 2)\n"
                "p2 = Point(3, 4)\n"
                "dist = p1.distance(p2)\n"
	      "print(dist)\n";
        }

        FILE* fp = fopen(package_name, "w");
        if (fp) {
	  fputs(package_code, fp);
	  fclose(fp);
        } else {
	  fprintf(stderr, "Failed to create file: %s\n", package_name);
        }
  }

  return 0;
}
