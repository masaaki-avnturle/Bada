/* bin/launcher.c — entry point for the BadaOS maglev kernel. */
#include <stdio.h>
#include <string.h>

int omega_interp(const char *);

int main(int argc, char **argv)
{
    if (argc < 2) {
        printf("BadaOS · Linear Shinkansen generative-AI kernel\n");
        printf("Usage: %s <command...>\n", argv[0]);
        printf("Example: %s boot\n", argv[0]);
        printf("         %s thermal examples/thermal_body.knot 1.2 320\n", argv[0]);
        return omega_interp("help");
    }
    char script[2048]; script[0] = 0;
    for (int i = 1; i < argc; i++) {
        if (i > 1) strncat(script, " ", sizeof(script) - strlen(script) - 1);
        strncat(script, argv[i], sizeof(script) - strlen(script) - 1);
    }
    return omega_interp(script);
}
