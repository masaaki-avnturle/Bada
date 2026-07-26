/* bin/launcher.c — entry point for the Bluebird EV autonomous-driving OS. */
#include <stdio.h>
#include <string.h>

int omega_interp(const char *);

int main(int argc, char **argv)
{
    if (argc < 2) {
        printf("BadaOS · Bluebird EV autonomous-driving kernel\n");
        printf("Usage: %s <command...>\n", argv[0]);
        printf("Try:   %s codegen examples/road_scene.txt out/policy.bada\n", argv[0]);
        return omega_interp("help");
    }
    char script[2048]; script[0] = 0;
    for (int i = 1; i < argc; i++) {
        if (i > 1) strncat(script, " ", sizeof(script) - strlen(script) - 1);
        strncat(script, argv[i], sizeof(script) - strlen(script) - 1);
    }
    return omega_interp(script);
}
