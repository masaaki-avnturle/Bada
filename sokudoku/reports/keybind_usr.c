```c
/*
 * pkginstallgen.c
 *
 * Generates omega_registry_pkg (fixed escaping issues).
 *
 * Build:
 *   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
 * Run:
 *   ./pkginstallgen
 *
 * This version fixes previous stray '\' and unterminated string problems
 * by properly escaping backslashes and quotes in embedded C strings.
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>

static int ensure_dir(const char *path) {
  if (!path) return -1;
  struct stat st;
  if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(path, 0755) == 0) return 0;
  if (errno == ENOENT) {
    char tmp[4096];
    strncpy(tmp, path, sizeof(tmp)-1);
    tmp[sizeof(tmp)-1] = 0;
    char *p = strrchr(tmp, '/');
    if (p && p != tmp) {
      *p = 0;
      if (ensure_dir(tmp) == 0) return mkdir(path, 0755) == 0 ? 0 : -1;
    }
  }
  return -1;
}

static int write_file(const char *path, const char *data, int mode) {
  char dir[4096];
  strncpy(dir, path, sizeof(dir)-1); dir[sizeof(dir)-1]=0;
  char *p = strrchr(dir, '/');
  if (p) { *p = 0; ensure_dir(dir); }
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
  if (data && fputs(data, f) == EOF) { fclose(f); return -1; }
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}

int main(void) {
  const char *root = "omega_registry_pkg";
  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }

  /* README */
    const char *readme =
"# omega_registry_pkg\n\n"
"Prototype package that simulates Windows registry operations (registry_sim) and\n"
"applies Emacs-like keybindings to applications (emacs_bindings). A minimal\n"
"Omega Script interpreter (omegascript) implemented in C is provided as a demo.\n\n"
      "Build the tools in usr/tools and run bin/run_pipeline to see examples.\n";
    write_file("omega_registry_pkg/README.md", readme, 0644);

    /* Makefile */
    const char *makefile =
      "CC ?= gcc\nCFLAGS ?= -O2 -std=c11 -Wall\n\nall: build\n\nbuild:\n\t@echo \"Build tools in usr/tools as needed (see README)\"\n\nclean:\n\trm -f usr/tools/registry_sim usr/tools/emacs_bindings usr/lang/omegascript\n";
    write_file("omega_registry_pkg/Makefile", makefile, 0644);

    /* bin/run_pipeline */
    const char *runner =
      "#!/usr/bin/env bash\nset -euo pipefail\nROOT=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\necho \"Sample pipeline: show registry, apply Emacs bindings, run Omega Script demo\"\nOUT=\"$ROOT/generated\"\nmkdir -p \"$OUT\"\nif [ -x \"$ROOT/usr/tools/registry_sim\" ]; then\n  \"$ROOT/usr/tools/registry_sim\" --show || true\nelse\n  echo \"registry_sim not built; see usr/tools/registry_sim.c\"\nfi\nif [ -x \"$ROOT/usr/tools/emacs_bindings\" ]; then\n  \"$ROOT/usr/tools/emacs_bindings\" --apply --config \"$ROOT/etc/emacs_bindings.conf\" || true\nelse\n  echo \"emacs_bindings not built; see usr/tools/emacs_bindings.c\"\nfi\nif [ -x \"$ROOT/usr/lang/omegascript\" ]; then\n  \"$ROOT/usr/lang/omegascript\" --run \"$ROOT/usr/lang/demo.os\" || true\nelse\n  echo \"omegascript not built; see usr/lang/omegascript.c\"\nfi\n";
    write_file("omega_registry_pkg/bin/run_pipeline", runner, 0755);

    /* include/omega.h */
    const char *omega_h =
      "/* omega helper header */\n#ifndef OMEGA_H\n#define OMEGA_H\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\nstatic inline void omega_log(const char *s) { fprintf(stderr, \"[omega] %s\\n\", s); }\n#endif\n";
    write_file("omega_registry_pkg/include/omega.h", omega_h, 0644);

    /* lib/omega_core.c */
    const char *omega_core =
      "/* omega_core.c - small helpers */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega.h\"\n\nvoid dump_sample(void) { omega_log(\"omega_core loaded\"); }\n";
    write_file("omega_registry_pkg/lib/omega_core.c", omega_core, 0644);

    /* etc config and emacs default bindings */
    const char *config_yaml =
      "registry_file: ./omega_registry.json\nemacs_bindings_conf: ./etc/emacs_bindings.conf\n";
    write_file("omega_registry_pkg/etc/config.yaml", config_yaml, 0644);

    const char *emacs_conf =
      "# emacs-like keybindings configuration (format: app_name:key => command)\n# Example: for a text editor that supports config keybindings\neditor:Ctrl-x Ctrl-s => save\neditor:Ctrl-x Ctrl-c => quit\nbrowser:Ctrl-x b => open-buffer\n";
    write_file("omega_registry_pkg/etc/emacs_bindings.conf", emacs_conf, 0644);

    /* usr/tools/registry_sim.c (fixed, no stray backslashes in C literal) */
    const char *registry_sim =
"/* registry_sim.c - simple registry simulator (file-backed key=value tree)\n"
" * Usage: registry_sim --get KEY | --set KEY VALUE | --del KEY | --show\n"
" * It uses omega_registry.json in package root by default.\n"
      " */\n\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <sys/stat.h>\n\nstatic const char *DB = \"omega_registry.json\";\n\n/* Very small key=value storage: each line 'key=value' */\n\nvoid ensure_db(void) {\n    FILE *f = fopen(DB, \"a\");\n    if (f) fclose(f);\n}\n\nvoid show_db(void) {\n    ensure_db();\n    FILE *f = fopen(DB, \"r\");\n    if (!f) { perror(\"open\"); return; }\n    char buf[4096];\n    puts(\"-- registry --\");\n    while (fgets(buf, sizeof(buf), f)) { fputs(buf, stdout); }\n    fclose(f);\n}\n\nvoid get_key(const char *k) {\n    ensure_db();\n    FILE *f = fopen(DB, \"r\");\n    if (!f) { perror(\"open\"); return; }\n    char buf[4096];\n    size_t L = strlen(k);\n    while (fgets(buf, sizeof(buf), f)) {\n        if (strncmp(buf, k, L) == 0 && buf[L] == '=') {\n            printf(\"%s\", buf + L + 1);\n            fclose(f);\n            return;\n        }\n    }\n    fclose(f);\n    printf(\"(null)\\n\");\n}\n\nvoid set_key(const char *k, const char *v) {\n    ensure_db();\n    FILE *f = fopen(DB, \"r\");\n    if (!f) {\n        FILE *w = fopen(DB, \"w\");\n        if (!w) { perror(\"open w\"); return; }\n        fprintf(w, \"%s=%s\\n\", k, v);\n        fclose(w);\n        printf(\"set %s\\n\", k);\n        return;\n    }\n    char tmpname[512];\n    snprintf(tmpname, sizeof(tmpname), \"%s.tmp\", DB);\n    FILE *t = fopen(tmpname, \"w\");\n    if (!t) { perror(\"open tmp\"); fclose(f); return; }\n    char buf[4096];\n    size_t L = strlen(k);\n    int found = 0;\n    while (fgets(buf, sizeof(buf), f)) {\n        if (strncmp(buf, k, L) == 0 && buf[L] == '=') {\n            fprintf(t, \"%s=%s\\n\", k, v);\n            found = 1;\n        } else fputs(buf, t);\n    }\n    if (!found) fprintf(t, \"%s=%s\\n\", k, v);\n    fclose(f);\n    fclose(t);\n    remove(DB);\n    rename(tmpname, DB);\n    printf(\"set %s\\n\", k);\n}\n\nvoid del_key(const char *k) {\n    ensure_db();\n    FILE *f = fopen(DB, \"r\");\n    if (!f) { perror(\"open r\"); return; }\n    char tmpname[512];\n    snprintf(tmpname, sizeof(tmpname), \"%s.tmp\", DB);\n    FILE *t = fopen(tmpname, \"w\");\n    if (!t) { perror(\"open tmp\"); fclose(f); return; }\n    char buf[4096];\n    size_t L = strlen(k);\n    while (fgets(buf, sizeof(buf), f)) {\n        if (strncmp(buf, k, L) == 0 && buf[L] == '=') continue;\n        fputs(buf, t);\n    }\n    fclose(f);\n    fclose(t);\n    remove(DB);\n    rename(tmpname, DB);\n    printf(\"del %s\\n\", k);\n}\n\nint main(int argc, char **argv) {\n    if (argc < 2) {\n        fprintf(stderr, \"usage: registry_sim --get KEY | --set KEY VALUE | --del KEY | --show\\n\");\n        return 1;\n    }\n    if (strcmp(argv[1], \"--show\") == 0) { show_db(); return 0; }\n    if (strcmp(argv[1], \"--get\") == 0 && argc >= 3) { get_key(argv[2]); return 0; }\n    if (strcmp(argv[1], \"--set\") == 0 && argc >= 4) { set_key(argv[2], argv[3]); return 0; }\n    if (strcmp(argv[1], \"--del\") == 0 && argc >= 3) { del_key(argv[2]); return 0; }\n    fprintf(stderr, \"invalid args\\n\");\n    return 2;\n}\n";
    write_file("omega_registry_pkg/usr/tools/registry_sim.c", registry_sim, 0644);

    /* usr/tools/emacs_bindings.c (fixed) */
    const char *emacs_bindings =
"/* emacs_bindings.c - apply Emacs-like keybindings (prototype)\n"
" * Usage: emacs_bindings --apply --config ./etc/emacs_bindings.conf\n"
      " */\n\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <sys/stat.h>\n\nstatic void ensure_dir(const char *path) {\n    struct stat st;\n    if (stat(path, &st) != 0) mkdir(path, 0755);\n}\n\n/* trim right newline and whitespace */\nstatic void rtrim(char *s) {\n    size_t L = strlen(s);\n    while (L > 0) {\n        char c = s[L-1];\n        if (c == '\\n' || c == '\\r' || c == ' ' || c == '\\t') { s[--L] = '\\0'; }\n        else break;\n    }\n}\n\nint main(int argc, char **argv) {\n    const char *conf = \"etc/emacs_bindings.conf\";\n    int apply = 0;\n    for (int i = 1; i < argc; ++i) {\n        if (strcmp(argv[i], \"--config\") == 0 && i+1 < argc) conf = argv[++i];\n        if (strcmp(argv[i], \"--apply\") == 0) apply = 1;\n    }\n\n    FILE *f = fopen(conf, \"r\");\n    if (!f) { fprintf(stderr, \"cannot open %s\\n\", conf); return 1; }\n\n    ensure_dir(\"generated\");\n    ensure_dir(\"generated/app_configs\");\n\n    char line[1024];\n    while (fgets(line, sizeof(line), f)) {\n        rtrim(line);\n        if (line[0] == '#' || strlen(line) < 3) continue;\n        /* format expected: app:keys => action */\n        char *colon = strchr(line, ':');\n        if (!colon) continue;\n        *colon = '\\0';\n        char *app = line;\n        char *rest = colon + 1;\n\n        char *arrow = strstr(rest, \"=>\");\n        if (!arrow) continue;\n        *arrow = '\\0';\n        char *keys = rest;\n        char *action = arrow + 2;\n\n        /* trim leading spaces */\n        while (*keys == ' ' || *keys == '\\t') ++keys;\n        while (*action == ' ' || *action == '\\t') ++action;\n        rtrim(keys);\n        rtrim(action);\n\n        char outpath[1024];\n        snprintf(outpath, sizeof(outpath), \"generated/app_configs/%s.conf\", app);\n        FILE *o = fopen(outpath, \"a\");\n        if (!o) continue;\n        fprintf(o, \"%s => %s\\n\", keys, action);\n        fclose(o);\n\n        if (apply) printf(\"applied %s: %s => %s\\n\", app, keys, action);\n    }\n\n    fclose(f);\n    printf(\"wrote generated/app_configs/\\n\");\n    return 0;\n}\n";
    write_file("omega_registry_pkg/usr/tools/emacs_bindings.c", emacs_bindings, 0644);

    /* usr/lang/omegascript.c (fixed) */
    const char *omegascript =
"/* omegascript.c - minimal Omega Script interpreter (prototype)\n"
" * supports commands: print \"...\" ; set VAR VALUE ; reg_set KEY VALUE ; reg_get KEY\n"
      " */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\n\nstatic void trim(char *s) { char *p = s + strlen(s) - 1; while (p >= s && (*p == '\\n' || *p == '\\r')) *p-- = '\\0'; }\n\nint main(int argc, char **argv) {\n    const char *script = \"usr/lang/demo.os\";\n    for (int i = 1; i < argc; i++) if (strcmp(argv[i], \"--run\") == 0 && i+1 < argc) script = argv[++i];\n    FILE *f = fopen(script, \"r\"); if (!f) { fprintf(stderr, \"no script %s\\n\", script); return 1; }\n    char line[1024];\n    while (fgets(line, sizeof(line), f)) {\n        trim(line);\n        if (strncmp(line, \"print \", 6) == 0) {\n            char *p = strchr(line, '\"'); if (p) { char *q = strrchr(line, '\"'); if (q && q > p) { *q = '\\0'; printf(\"%s\\n\", p+1); } }\n        } else if (strncmp(line, \"set \", 4) == 0) {\n            char var[128], val[512]; if (sscanf(line+4, \"%127s %511[^\"]\", var, val) >= 1) printf(\"set %s=%s\\n\", var, val);\n        } else if (strncmp(line, \"reg_set \", 8) == 0) {\n            char key[256], val[512]; if (sscanf(line+8, \"%255s %511[^\"]\", key, val) >= 1) {\n                char cmd[1024]; snprintf(cmd, sizeof(cmd), \"./usr/tools/registry_sim --set %s '%s'\", key, val);\n                system(cmd);\n            }\n        } else if (strncmp(line, \"reg_get \", 8) == 0) {\n            char key[256]; if (sscanf(line+8, \"%255s\", key) == 1) { char cmd[512]; snprintf(cmd, sizeof(cmd), \"./usr/tools/registry_sim --get %s\", key); system(cmd); }\n        }\n    }\n    fclose(f);\n    return 0;\n}\n";
    write_file("omega_registry_pkg/usr/lang/omegascript.c", omegascript, 0644);

    /* demo.os: using single backslashes in file content (escape in C literal as \\) */
    const char *demo_os =
"print \"Omega Script demo: registry set/get\"\n"
"reg_set HKEY_LOCAL_MACHINE\\Software\\MyApp\\Setting 42\n"
      "reg_get HKEY_LOCAL_MACHINE\\Software\\MyApp\\Setting\n";
    write_file("omega_registry_pkg/usr/lang/demo.os", demo_os, 0644);

    /* omega_registry.json initial contents (escaped in C literal as \\) */
    const char *registry_init =
"# omega_registry.json (simple key=value lines)\n"
      "HKEY_LOCAL_MACHINE\\Software\\MyApp\\Setting=1\n";
    write_file("omega_registry.json", registry_init, 0644);

    /* finish */
    printf("omega_registry_pkg created. Build the tools under usr/tools and usr/lang.\\n");
    return 0;
}
```
