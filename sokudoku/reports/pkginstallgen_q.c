  // pkginstallgen_q.c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>

  static int mkdir_p(const char *path) {
  char tmp[4096];
  char *p;
  size_t len;
  if (!path || !*path) return -1;
  snprintf(tmp, sizeof(tmp), "%s", path);
  len = strlen(tmp);
  if (tmp[len-1] == '/') tmp[len-1] = '\0';
  for (p = tmp + 1; *p; ++p) {
    if (*p == '/') {
      *p = '\0';
      if (mkdir(tmp, 0755) != 0 && errno != EEXIST) return -1;
      *p = '/';
    }
  }
  if (mkdir(tmp, 0755) != 0 && errno != EEXIST) return -1;
  return 0;
}

  static int write_file(const char *path, const char *content) {
    const char *last = strrchr(path, '/');
    if (last) {
      char dir[4096];
      size_t n = last - path;
      if (n >= sizeof(dir)) return -1;
      memcpy(dir, path, n); dir[n] = '\0';
      if (mkdir_p(dir) != 0) { fprintf(stderr, "mkdir_p failed for %s\n", dir); return -1; }
    }
    FILE *f = fopen(path, "w");
    if (!f) { perror(path); return -1; }
    fputs(content, f); fclose(f);
    return 0;
  }

int main(void) {
  mkdir_p("omega_q/src");

  // quantum_runtime.h
    const char *runtime_h =
"// omega_q/src/quantum_runtime.h\n"
"#ifndef QUANTUM_RUNTIME_H\n"
"#define QUANTUM_RUNTIME_H\n"
"#include <stddef.h>\n"
"\n"
"typedef struct QState { size_t nqubits; size_t dim; double *re; double *im; } QState;\n"
"typedef struct QGate { size_t dim; double *re; double *im; } QGate;\n"\n"
      // Fundamental quantum equations (from report):
"// Schrodinger equation (time-dependent): H |Psi> = i ħ ∂|Psi>/∂t\n"
"// We simulate time evolution by applying U = exp(-i H dt / ħ) (Trotter / matrix exponential approx.)\n"
"\n"
"QState* qstate_create(size_t nqubits);\n"
"void qstate_free(QState* s);\n"
"void qstate_normalize(QState* s);\n"
"QState* qstate_copy(const QState* s);\n"\n"
"QGate* qgate_create_from_matrix(size_t dim, const double *re, const double *im);\n"
"void qgate_free(QGate* g);\n"
"QState* qgate_apply(const QGate* g, const QState* s);\n"
"\n"
"// common gates\n"
"QGate* qgate_h(size_t nqubits, size_t target);\n"
"QGate* qgate_x(size_t nqubits, size_t target);\n" 
"QGate* qgate_cnot(size_t nqubits, size_t control, size_t target);\n"
"\n"
"// measurement: collapse single-shot measurement on one qubit, returns 0 or 1\n"
"int qstate_measure(QState* s, size_t qubit);\n"
"\n"
"// approximate time evolution via simple Trotter step: apply U = exp(-i H dt / ħ)\n"
"QGate* qgate_from_hamiltonian(size_t dim, const double *H_re, const double *H_im, double dt);\n"
"\n"
      "#endif // QUANTUM_RUNTIME_H\n";

    write_file("omega_q/src/quantum_runtime.h", runtime_h);

    // quantum_runtime.c
    const char *runtime_c =
"// omega_q/src/quantum_runtime.c\n"
"#include \"quantum_runtime.h\"\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"#include <math.h>\n"
"\n" 
"static inline size_t dim_from_q(size_t n) { return 1u << n; }\n"
"\n"
"QState* qstate_create(size_t nqubits) {\n"
"    QState* s = malloc(sizeof(QState));\n" 
"    s->nqubits = nqubits; s->dim = dim_from_q(nqubits);\n" 
"    s->re = calloc(s->dim, sizeof(double)); s->im = calloc(s->dim, sizeof(double));\n" 
"    // default |0...0>\n" 
"    if (s->dim > 0) s->re[0] = 1.0;\n" 
"    return s;\n}\n"
"\n"
"void qstate_free(QState* s) {\n"
"    if (!s) return; free(s->re); free(s->im); free(s);\n}\n"
"\n"
"void qstate_normalize(QState* s) {\n"
"    double norm2 = 0.0;\n" 
"    for (size_t i=0;i<s->dim;++i) norm2 += s->re[i]*s->re[i] + s->im[i]*s->im[i];\n" 
"    if (norm2<=0) return; double n = 1.0/sqrt(norm2);\n" 
"    for (size_t i=0;i<s->dim;++i){ s->re[i]*=n; s->im[i]*=n; }\n}\n"
"\n"
"QState* qstate_copy(const QState* s){ QState* c = malloc(sizeof(QState)); memcpy(c, s, sizeof(QState)); c->re = malloc(sizeof(double)*s->dim); c->im = malloc(sizeof(double)*s->dim); memcpy(c->re,s->re,sizeof(double)*s->dim); memcpy(c->im,s->im,sizeof(double)*s->dim); return c; }\n"
"\n"
"QGate* qgate_create_from_matrix(size_t dim, const double *re, const double *im){ QGate* g = malloc(sizeof(QGate)); g->dim = dim; g->re = malloc(sizeof(double)*dim*dim); g->im = malloc(sizeof(double)*dim*dim); memcpy(g->re,re,sizeof(double)*dim*dim); memcpy(g->im,im,sizeof(double)*dim*dim); return g; }\n"
"void qgate_free(QGate* g){ if(!g) return; free(g->re); free(g->im); free(g); }\n"
"\n"
"QState* qgate_apply(const QGate* g, const QState* s){ if(g->dim != s->dim) return NULL; QState* r = malloc(sizeof(QState)); r->nqubits = s->nqubits; r->dim = s->dim; r->re = calloc(r->dim,sizeof(double)); r->im = calloc(r->dim,sizeof(double)); for(size_t i=0;i<r->dim;++i){ double ar=0, ai=0; for(size_t j=0;j<r->dim;++j){ size_t idx = i*r->dim + j; double gr = g->re[idx], gi = g->im[idx]; double sr = s->re[j], si = s->im[j]; ar += gr*sr - gi*si; ai += gr*si + gi*sr; } r->re[i]=ar; r->im[i]=ai; } return r; }\n"
"\n"
"// helper: build single-qubit gate on nqubits by tensoring identity and small 2x2\nstatic QGate* build_single_qubit_gate(size_t nqubits, size_t target, const double m2_re[4], const double m2_im[4]){\n"
"    size_t dim = 1u<<nqubits; double *re = calloc(dim*dim,sizeof(double)); double *im = calloc(dim*dim,sizeof(double));\n" 
"    for(size_t i=0;i<dim;i++){\n" 
      "        for(size_t j=0;j<dim;j++){\n"            // compute whether i and j differ only on target bit\n"            size_t mask = ((size_t)1<<target);\n"            size_t i_low = (i & ~mask), j_low = (j & ~mask);\n"            if (i_low == j_low){ // same other bits\n"                size_t ibit = (i>>target)&1; size_t jbit = (j>>target)&1;\n"                size_t idx2 = ibit*2 + jbit;\n"                re[i*dim+j] = m2_re[idx2]; im[i*dim+j] = m2_im[idx2];\n"            }\n"        }\n"    }\n"    QGate* g = malloc(sizeof(QGate)); g->dim = dim; g->re = re; g->im = im; return g;\n"}\n"
"\n"
"QGate* qgate_h(size_t nqubits, size_t target){ double r[4] = {1/sqrt(2),1/sqrt(2),1/sqrt(2),-1/sqrt(2)}; double iz[4] = {0,0,0,0}; return build_single_qubit_gate(nqubits,target,r,iz); }\n"
"QGate* qgate_x(size_t nqubits, size_t target){ double r[4] = {0,1,1,0}; double iz[4] = {0,0,0,0}; return build_single_qubit_gate(nqubits,target,r,iz); }\n"
"\n"
"QGate* qgate_cnot(size_t nqubits, size_t control, size_t target){ size_t dim = 1u<<nqubits; double *re = calloc(dim*dim,sizeof(double)); double *im = calloc(dim*dim,sizeof(double)); for(size_t i=0;i<dim;i++){ size_t o=i; if(((i>>control)&1)) { // flip target bit\n" " size_t j = i ^ ((size_t)1<<target); re[j*dim + i] = 1.0; } else { re[i*dim + i] = 1.0; } } QGate* g = malloc(sizeof(QGate)); g->dim = dim; g->re = re; g->im = im; return g; }\n"
"\n"
"int qstate_measure(QState* s, size_t qubit){ // single-shot projective measurement\n" "    size_t dim = s->dim; double p0 = 0.0; size_t mask = ((size_t)1<<qubit);\n" "    for(size_t i=0;i<dim;i++) if(((i>>qubit)&1)==0) p0 += s->re[i]*s->re[i] + s->im[i]*s->im[i]; double r = ((double)rand())/RAND_MAX; int outcome = (r < p0) ? 0 : 1; for(size_t i=0;i<dim;i++){ if(((i>>qubit)&1) != outcome){ s->re[i]=0; s->im[i]=0; } } qstate_normalize(s); return outcome; }\n"
"\n"
      "// Very small matrix exponential via diagonalization not provided; use first-order Trotter U ≈ I - i H dt / ħ\nQGate* qgate_from_hamiltonian(size_t dim, const double *H_re, const double *H_im, double dt){ double hbar = 1.054571817e-34; double *re = malloc(sizeof(double)*dim*dim); double *im = malloc(sizeof(double)*dim*dim); for(size_t i=0;i<dim*dim;i++){ // U = I - i H dt / ħ => U = I + ( - i * H * dt / ħ )\n" " double a = - (dt / hbar) * H_im[i]; double b =   (dt / hbar) * H_re[i]; // -i*(a+ib) = b - i a\n" " re[i] = (i% (dim+1) == 0) ? 1.0 + a : a; // approximate: add identity on diagonals\n" " im[i] = b; }\n" " QGate* g = malloc(sizeof(QGate)); g->dim = dim; g->re = re; g->im = im; return g; }\n";
    write_file("omega_q/src/quantum_runtime.c", runtime_c);

    // quantum_interop.h
    const char *interop_h =
"// omega_q/src/quantum_interop.h\n"
"#ifndef QUANTUM_INTEROP_H\n"
"#define QUANTUM_INTEROP_H\n"
"#include \"quantum_runtime.h\"\n"
"// Minimal C API to expose quantum primitives to Omega interpreter\n"
"QState* omega_q_create_state(size_t n);\n"
"void omega_q_release_state(QState* s);\n"
"void omega_q_apply_gate(QState** ps, QGate* g);\n"
"QGate* omega_q_gate_h(size_t n, size_t target);\n"
"QGate* omega_q_gate_x(size_t n, size_t target);\n" 
"QGate* omega_q_gate_cnot(size_t n, size_t control, size_t target);\n"
"int omega_q_measure(QState* s, size_t qubit);\n"
"QGate* omega_q_gate_from_hamiltonian(size_t dim, const double *H_re, const double *H_im, double dt);\n"
      "#endif\n";
    write_file("omega_q/src/quantum_interop.h", interop_h);

    // quantum_interop.c
    const char *interop_c =
"// omega_q/src/quantum_interop.c\n"
"#include \"quantum_interop.h\"\n"
"#include <stdlib.h>\n"
"\n" 
"QState* omega_q_create_state(size_t n){ return qstate_create(n); }\n"
"void omega_q_release_state(QState* s){ qstate_free(s); }\n"
"void omega_q_apply_gate(QState** ps, QGate* g){ QState* new = qgate_apply(g, *ps); qstate_free(*ps); *ps = new; }\n"
"QGate* omega_q_gate_h(size_t n, size_t target){ return qgate_h(n,target); }\n"
"QGate* omega_q_gate_x(size_t n, size_t target){ return qgate_x(n,target); }\n"
"QGate* omega_q_gate_cnot(size_t n, size_t control, size_t target){ return qgate_cnot(n,control,target); }\n"
"int omega_q_measure(QState* s, size_t qubit){ return qstate_measure(s, qubit); }\n"
      "QGate* omega_q_gate_from_hamiltonian(size_t dim, const double *H_re, const double *H_im, double dt){ return qgate_from_hamiltonian(dim,H_re,H_im,dt); }\n";
    write_file("omega_q/src/quantum_interop.c", interop_c);

    // omega_interpreter extension stub (adds quantum primitives to existing interpreter)
    const char *interp_ext =
"// omega_q/src/omega_interpreter_qext.c\n"
"// This file provides example bindings: in a real setup integrate with the Omega interpreter's env/register system.\n"
"#include <stdio.h>\n"
"#include \"quantum_interop.h\"\n\n"
"// Example standalone demo when compiled\n"
"int main(void){\n"
"    // create 2-qubit state\n"
"    QState *s = omega_q_create_state(2);\n" 
"    printf(\"Initial state (|00>):\\n\");\n" 
"    for(size_t i=0;i<s->dim;i++) printf(\"amp[%zu] = %g + %gi\\n\", i, s->re[i], s->im[i]);\n"
"    // apply H on qubit 0\n"
"    QGate *H = omega_q_gate_h(2,0);\n" 
"    omega_q_apply_gate(&s, H);\n" 
"    qgate_free(H);\n" 
"    printf(\"After H on qubit0:\\n\");\n" 
"    for(size_t i=0;i<s->dim;i++) printf(\"amp[%zu] = %g + %gi\\n\", i, s->re[i], s->im[i]);\n"
"    // apply CNOT(0->1)\n"
"    QGate *C = omega_q_gate_cnot(2,0,1);\n" 
"    omega_q_apply_gate(&s, C);\n" 
"    qgate_free(C);\n" 
"    printf(\"After CNOT:\\n\");\n" 
"    for(size_t i=0;i<s->dim;i++) printf(\"amp[%zu] = %g + %gi\\n\", i, s->re[i], s->im[i]);\n"
"    // measure qubit 0\n"
"    int m = omega_q_measure(s, 0);\n" 
"    printf(\"Measured qubit0 = %d\\n\", m);\n" 
"    omega_q_release_state(s);\n" 
      "    return 0;\n}\n";
    write_file("omega_q/src/omega_interpreter_qext.c", interp_ext);

    // Makefile
    const char *makefile =
      "CC = gcc\nCFLAGS = -O2 -std=c11 -I.\nSOURCES = quantum_runtime.c quantum_interop.c omega_interpreter_qext.c\nTARGET = omega_q_demo\n\nall: $(TARGET)\n\n$(TARGET): $(SOURCES)\n\t$(CC) $(CFLAGS) -o $(TARGET) $(SOURCES) -lm\n\nclean:\n\trm -f $(TARGET)\n";
    write_file("omega_q/src/Makefile", makefile);

    // README summarizing included quantum equations and how they relate to implementation
    const char *readme =
"omega_q generated quantum extension\n\n"
"Files:\n"
"- quantum_runtime.h/.c : state vector & gate primitives, simple Trotter first-order evolution (U ≈ I - i H dt / ħ)\n"
"- quantum_interop.h/.c : C API to be bound into Omega interpreter (create state, apply gates, measure)\n"
"- omega_interpreter_qext.c : small demo applying H and CNOT and measuring\n"
"- Makefile : build demo\n\n"
"Key quantum equations referenced and reflected:\n"
"- Time-dependent Schroedinger equation: H |Psi> = i ħ ∂|Psi>/∂t\n  -> implemented as U ≈ exp(-i H dt / ħ); approximate via first-order expansion in qgate_from_hamiltonian\n"
      "- Unitary evolution: |Psi(t+dt)> = U |Psi(t)>\n"- Measurement: projective collapse, probabilistic sampling\n\n"
      "Notes:\n- This is a pedagogical, single-threaded state-vector simulator (full matrix gates). For n qubits complexity is O(2^n).\n- For production: replace matrix exponential with proper expm/Trotter-Suzuki, add sparse gates, optimize tensor operations, add decoherence/noise models, and integrate into the Omega interpreter environment (binding functions into environment, support script-level syntax).\n";
    write_file("omega_q/src/README.txt", readme);

    printf("omega_q/src generated. Build: cd omega_q/src && make\n");
    return 0;
}
