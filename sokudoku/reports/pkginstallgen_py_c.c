/* pkginstallgen.c
   Compile: gcc -o pkginstallgen pkginstallgen.c
   Run: ./pkginstallgen

   This program generates two packages in the current directory:
   - omega-python/   (Python3 minimal Omega implementation)
   - omega-c/        (C minimal Omega implementation)

   Each embedded file's source appears below as C string literals.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>

/* Helper to create directory (recursive simple) */
static void mkd(const char *path) {
  if (mkdir(path, 0755) == -1) {
    if (errno == EEXIST) return;
    /* try mkdir -p via system as fallback for nested */
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "mkdir -p '%s'", path);
    if (system(cmd) != 0) {
      fprintf(stderr, "mkdir failed for %s\n", path);
      exit(1);
    }
  }
}

/* Helper to write file and optionally make executable */
static void writef(const char *path, const char *content, int make_exec) {
  FILE *f = fopen(path, "wb");
  if (!f) { perror(path); exit(1); }
  fwrite(content, 1, strlen(content), f);
  fclose(f);
  if (make_exec) {
    if (chmod(path, 0755) != 0) {
      perror("chmod");
      /* non-fatal */
    }
  }
}

/* ---------------------- Embedded files (Python package) ---------------------- */

static const char *py_bin_omega = 
"#!/usr/bin/env python3\n"
"import sys\n"
"from omega.runtime import Engine\n"
"\n"
"def main():\n"
"    if len(sys.argv) < 2:\n"
"        print(\"Usage: omega.py <source.omega> [--compile]\")\n"
"        sys.exit(1)\n"
"    src = open(sys.argv[1], \"r\", encoding=\"utf-8\").read()\n"
"    engine = Engine()\n"
"    if len(sys.argv) > 2 and sys.argv[2] == \"--compile\":\n"
"        print(engine.compile(src))\n"
"    else:\n"
"        engine.run(src)\n"
"\n"
"if __name__ == \"__main__\":\n"
  "    main()\n";

static const char *py_init = 
  "# package marker\n";

static const char *py_tuplespace = 
"import threading\n"
"\n"
"class Store:\n"
"    def __init__(self):\n"
"        self.space = []\n"
"        self.lock = threading.Lock()\n"
"\n"
"    def out(self, tpl):\n"
"        with self.lock:\n"
"            self.space.append(tuple(tpl))\n"
"        return True\n"
"\n"
"    def rd(self, pattern):\n"
"        with self.lock:\n"
"            for t in self.space:\n"
"                if self._match(pattern, t):\n"
"                    return t\n"
"        return None\n"
"\n"
"    def in_(self, pattern):\n"
"        with self.lock:\n"
"            for i, t in enumerate(self.space):\n"
"                if self._match(pattern, t):\n"
"                    return self.space.pop(i)\n"
"        return None\n"
"\n"
"    def _match(self, pattern, tpl):\n"
"        if not isinstance(pattern, (list, tuple)) or len(pattern) != len(tpl):\n"
"            return False\n"
  "        return all(p is None or p == v for p, v in zip(pattern, tpl))\n";

static const char *py_parser = 
"def parse(source: str):\n"
"    lines = []\n"
"    for raw in source.splitlines():\n"
"        ln = raw.strip()\n"
"        if not ln or ln.startswith(\"#\"):\n"
"            continue\n"
"        if ln.startswith(\"out \"):\n"
"            arg = ln[4:].strip()\n"
"            lines.append((\"out\", eval(arg)))\n"
"        elif ln.startswith(\"rd \"):\n"
"            arg = ln[3:].strip()\n"
"            lines.append((\"rd\", eval(arg)))\n"
"        elif ln.startswith(\"in \"):\n"
"            arg = ln[3:].strip()\n"
"            lines.append((\"in\", eval(arg)))\n"
"        elif ln.startswith(\"print \"):\n"
"            arg = ln[6:].strip()\n"
"            lines.append((\"print\", eval(arg)))\n"
"        else:\n"
"            lines.append((\"expr\", ln))\n"
  "    return (\"program\", lines)\n";

static const char *py_vm = 
"class Machine:\n"
"    def __init__(self, tuplespace):\n"
"        self.ts = tuplespace\n"
"\n"
"    def execute(self, ast):\n"
"        kind, body = ast\n"
"        if kind != \"program\":\n"
"            raise ValueError(\"invalid ast\")\n"
"        for node in body:\n"
"            op, arg = node\n"
"            if op == \"out\":\n"
"                self.ts.out(arg)\n"
"            elif op == \"rd\":\n" 
"                print(self.ts.rd(arg))\n"
"            elif op == \"in\":\n"
"                print(self.ts.in_(arg))\n"
"            elif op == \"print\":\n"
"                print(arg)\n"
"            elif op == \"expr\":\n"
"                try:\n"
"                    print(eval(arg))\n"
"                except Exception as e:\n"
"                    print(\"expr error:\", e)\n"
"            else:\n"
  "                print(\"unknown op\", op)\n";

static const char *py_compiler = 
"def emit_bytecode(ast):\n"
"    kind, body = ast\n"
"    if kind != \"program\":\n"
"        raise ValueError(\"invalid ast\")\n"
"    lines = []\n"
"    for op, arg in body:\n"
"        if op == \"out\": lines.append(f\"OUT {repr(arg)}\")\n"
"        elif op == \"rd\": lines.append(f\"RD  {repr(arg)}\")\n"
"        elif op == \"in\": lines.append(f\"IN  {repr(arg)}\")\n"
"        elif op == \"print\": lines.append(f\"PRINT {repr(arg)}\")\n"
"        elif op == \"expr\": lines.append(f\"EXPR {repr(arg)}\")\n"
"        else: lines.append(\"NOP\")\n"
  "    return \"\\n\".join(lines)\n";

static const char *py_runtime = 
"from .parser import parse\n"
"from .vm import Machine\n"
"from .tuplespace import Store\n"
"from .compiler import emit_bytecode\n"
"\n"
"class Engine:\n"
"    def __init__(self):\n"
"        self.ts = Store()\n"
"        self.vm = Machine(self.ts)\n"
"\n"
"    def run(self, source):\n"
"        ast = parse(source)\n"
"        self.vm.execute(ast)\n"
"\n"
"    def compile(self, source):\n"
"        ast = parse(source)\n"
  "        return emit_bytecode(ast)\n";

static const char *py_include_omega_h = 
  "#ifndef OMEGA_H\n#define OMEGA_H\n/* Omega spec (reference) */\n#endif\n";

static const char *py_etc_conf = 
  "tuplespace.max_entries = 10000\n";

static const char *py_example = 
"# example.omega\n"
"out [\"user\", 1, \"Alice\"]\n"
"out [\"user\", 2, \"Bob\"]\n"
"rd  [\"user\", None, None]\n"
"in  [\"user\", 1, None]\n"
"rd  [\"user\", None, None]\n"
  "print \"done\"\n";

static const char *py_setup_sh =
  "#!/usr/bin/env bash\nset -e\nPKG=omega-python\nmkdir -p $PKG/{bin,lib/omega,include,etc}\ncp -r bin/* $PKG/bin/\ncp -r lib/omega/* $PKG/lib/omega/\ncp include/omega.h $PKG/include/\ncp etc/omega.conf $PKG/etc/\nchmod +x $PKG/bin/omega.py\necho \"Assembled $PKG\"\n";

/* ---------------------- Embedded files (C package) ---------------------- */

static const char *c_parser_h =
  "#ifndef PARSER_H\n#define PARSER_H\ntypedef struct AST AST;\nAST* parse_source(const char *src);\nvoid free_ast(AST *ast);\n#endif\n";

static const char *c_parser_c =
  "#include \"parser.h\"\n#include <stdlib.h>\n#include <string.h>\n#include <stdio.h>\n\ntypedef struct Node {\n    char *op;\n    char *arg;\n    struct Node *next;\n} Node;\n\nstruct AST {\n    Node *head;\n};\n\nstatic char* str_strip(char *s) {\n    while(*s==' '||*s=='\\t') s++;\n    size_t len = strlen(s);\n    while(len>0 && (s[len-1]=='\\n' || s[len-1]=='\\r' || s[len-1]==' ' || s[len-1]=='\\t')) s[--len]=0;\n    return s;\n}\n\nAST* parse_source(const char *src) {\n    AST *ast = malloc(sizeof(AST));\n    ast->head = NULL;\n    Node **tail = &ast->head;\n\n    char *buf = strdup(src);\n    char *line = strtok(buf, \"\\n\");\n    while(line) {\n        char *ln = str_strip(line);\n        if (*ln == '#' || *ln == 0) { line = strtok(NULL, \"\\n\"); continue; }\n        Node *n = malloc(sizeof(Node));\n        n->next = NULL;\n        if (strncmp(ln, \"out \", 4) == 0) {\n            n->op = strdup(\"out\");\n            n->arg = strdup(ln+4);\n        } else if (strncmp(ln, \"rd \", 3) == 0) {\n            n->op = strdup(\"rd\");\n            n->arg = strdup(ln+3);\n        } else if (strncmp(ln, \"in \", 3) == 0) {\n            n->op = strdup(\"in\");\n            n->arg = strdup(ln+3);\n        } else if (strncmp(ln, \"print \", 6) == 0) {\n            n->op = strdup(\"print\");\n            n->arg = strdup(ln+6);\n        } else {\n            n->op = strdup(\"expr\");\n            n->arg = strdup(ln);\n        }\n        *tail = n;\n        tail = &n->next;\n        line = strtok(NULL, \"\\n\");\n    }\n    free(buf);\n    return ast;\n}\n\nvoid free_ast(AST *ast) {\n    if (!ast) return;\n    Node *n = ast->head;\n    while(n) {\n        Node *nx = n->next;\n        free(n->op); free(n->arg); free(n);\n        n = nx;\n    }\n    free(ast);\n}\n";

static const char *c_tuplespace_h =
  "#ifndef TUPLESPACE_H\n#define TUPLESPACE_H\ntypedef struct TupleSpace TupleSpace;\nTupleSpace* ts_new(void);\nvoid ts_free(TupleSpace*);\nvoid ts_out(TupleSpace*, const char *item);\nchar* ts_rd(TupleSpace*, const char *pattern);\nchar* ts_in(TupleSpace*, const char *pattern);\n#endif\n";

static const char *c_tuplespace_c =
  "#include \"tuplespace.h\"\n#include <stdlib.h>\n#include <string.h>\n#include <stdio.h>\n#include <pthread.h>\n\ntypedef struct Entry {\n    char *s;\n    struct Entry *next;\n} Entry;\n\nstruct TupleSpace {\n    Entry *head;\n    pthread_mutex_t lock;\n};\n\nTupleSpace* ts_new(void) {\n    TupleSpace *ts = malloc(sizeof(TupleSpace));\n    ts->head = NULL;\n    pthread_mutex_init(&ts->lock, NULL);\n    return ts;\n}\n\nvoid ts_free(TupleSpace *ts) {\n    if (!ts) return;\n    Entry *e = ts->head;\n    while(e) { Entry *n=e->next; free(e->s); free(e); e=n; }\n    pthread_mutex_destroy(&ts->lock);\n    free(ts);\n}\n\nvoid ts_out(TupleSpace *ts, const char *item) {\n    Entry *e = malloc(sizeof(Entry));\n    e->s = strdup(item);\n    pthread_mutex_lock(&ts->lock);\n    e->next = ts->head; ts->head = e;\n    pthread_mutex_unlock(&ts->lock);\n}\n\nstatic int match_pattern(const char *pattern, const char *item) {\n    if (!pattern) return 0;\n    if (strcmp(pattern, \"*\") == 0) return 1;\n    return strcmp(pattern, item) == 0;\n}\n\nchar* ts_rd(TupleSpace *ts, const char *pattern) {\n    pthread_mutex_lock(&ts->lock);\n    for(Entry *e = ts->head; e; e=e->next) {\n        if (match_pattern(pattern, e->s)) {\n            char *r = strdup(e->s);\n            pthread_mutex_unlock(&ts->lock);\n            return r;\n        }\n    }\n    pthread_mutex_unlock(&ts->lock);\n    return NULL;\n}\n\nchar* ts_in(TupleSpace *ts, const char *pattern) {\n    pthread_mutex_lock(&ts->lock);\n    Entry **pp = &ts->head;\n    while(*pp) {\n        if (match_pattern(pattern, (*pp)->s)) {\n            Entry *found = *pp;\n            *pp = found->next;\n            char *r = strdup(found->s);\n            free(found->s); free(found);\n            pthread_mutex_unlock(&ts->lock);\n            return r;\n        }\n        pp = &(*pp)->next;\n    }\n    pthread_mutex_unlock(&ts->lock);\n    return NULL;\n}\n";

static const char *c_vm_c =
  "#include \"parser.h\"\n#include \"tuplespace.h\"\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nextern struct AST* parse_source(const char*);\n\nvoid execute(AST *ast, TupleSpace *ts) {\n    struct NodeInternal { char *op; char *arg; struct NodeInternal *next; };\n    struct AST_internal { struct NodeInternal *head; };\n    struct AST_internal *a = (struct AST_internal*)ast;\n    for (struct NodeInternal *n = a->head; n; n = n->next) {\n        if (strcmp(n->op, \"out\")==0) {\n            ts_out(ts, n->arg);\n        } else if (strcmp(n->op, \"rd\")==0) {\n            char *r = ts_rd(ts, n->arg);\n            printf(\"%s\\n\", r ? r : \"nil\");\n            free(r);\n        } else if (strcmp(n->op, \"in\")==0) {\n            char *r = ts_in(ts, n->arg);\n            printf(\"%s\\n\", r ? r : \"nil\");\n            free(r);\n        } else if (strcmp(n->op, \"print\")==0) {\n            printf(\"%s\\n\", n->arg);\n        } else {\n            printf(\"expr: %s\\n\", n->arg);\n        }\n    }\n}\n";

static const char *c_main_c =
  "#include <stdio.h>\n#include <stdlib.h>\n#include \"parser.h\"\n#include \"tuplespace.h\"\n\nAST* parse_source(const char*); /* from parser.c */\nvoid free_ast(AST*); /* from parser.c */\n\nint main(int argc, char **argv) {\n    if (argc < 2) {\n        fprintf(stderr, \"Usage: omega <source.omega>\\n\");\n        return 1;\n    }\n    FILE *f = fopen(argv[1], \"r\");\n    if (!f) { perror(\"fopen\"); return 1; }\n    fseek(f, 0, SEEK_END);\n    long sz = ftell(f);\n    fseek(f, 0, SEEK_SET);\n    char *buf = malloc(sz+1);\n    fread(buf,1,sz,f);\n    buf[sz]=0;\n    fclose(f);\n\n    AST *ast = parse_source(buf);\n    TupleSpace *ts = ts_new();\n    extern void execute(AST*, TupleSpace*);\n    execute(ast, ts);\n    free_ast(ast);\n    ts_free(ts);\n    free(buf);\n    return 0;\n}\n";

static const char *c_makefile =
  "CC = gcc\nCFLAGS = -std=c11 -O2 -pthread -Iinclude\nSRCS = src/main.c src/parser.c src/tuplespace.c src/vm.c\nall: bin/omega\nbin/omega: $(SRCS)\n\t$(CC) $(CFLAGS) -o $@ $(SRCS)\nclean:\n\trm -f bin/omega *.o\n";

static const char *c_example =
  "# example.omega\nout user1\nout user2\nrd *\nin user1\nrd *\nprint done\n";

/* ---------------------- Generation main ---------------------- */

int main(void) {
  /* python package directories */
  mkd("omega-python");
  mkd("omega-python/bin");
  mkd("omega-python/lib");
  mkd("omega-python/lib/omega");
  mkd("omega-python/include");
  mkd("omega-python/etc");

  writef("omega-python/bin/omega.py", py_bin_omega, 1);
  writef("omega-python/lib/omega/__init__.py", py_init, 0);
  writef("omega-python/lib/omega/tuplespace.py", py_tuplespace, 0);
  writef("omega-python/lib/omega/parser.py", py_parser, 0);
  writef("omega-python/lib/omega/vm.py", py_vm, 0);
  writef("omega-python/lib/omega/compiler.py", py_compiler, 0);
  writef("omega-python/lib/omega/runtime.py", py_runtime, 0);
  writef("omega-python/include/omega.h", py_include_omega_h, 0);
  writef("omega-python/etc/omega.conf", py_etc_conf, 0);
  writef("omega-python/example.omega", py_example, 0);
  writef("omega-python/setup.sh", py_setup_sh, 1);

  /* C package directories */
  mkd("omega-c");
  mkd("omega-c/bin");
  mkd("omega-c/src");
  mkd("omega-c/include");

  writef("omega-c/src/parser.h", c_parser_h, 0);
  writef("omega-c/src/parser.c", c_parser_c, 0);
  writef("omega-c/src/tuplespace.h", c_tuplespace_h, 0);
  writef("omega-c/src/tuplespace.c", c_tuplespace_c, 0);
  writef("omega-c/src/vm.c", c_vm_c, 0);
  writef("omega-c/src/main.c", c_main_c, 0);
  writef("omega-c/Makefile", c_makefile, 0);
  writef("omega-c/example.omega", c_example, 0);

  /* small readme */
  writef("README_pkginstallgen.txt",
"This program generated two packages:\n"
"- omega-python\n"
"- omega-c\n\n"
"To build C package: cd omega-c && make\n"
	 "To run python package: ./omega-python/bin/omega.py omega-python/example.omega\n", 0);

  printf("Generated packages: omega-python/  omega-c/\n");
  return 0;
}
