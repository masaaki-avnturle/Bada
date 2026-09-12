/* ============================================================================
 * agos_jni.c -- JNI terminal for the Anti-Gravity OS on Android.
 *
 * The stage-0 Bada interpreter (src/bada.c) is compiled verbatim into this
 * shared library; the only additions are (a) renaming its CLI main out of
 * the way, (b) capturing stdout through a pipe so the flight-session log can
 * be handed back to the Java console view, and (c) resetting the append-only
 * ledgers between re-boots so every boot re-derives G1-G4 from scratch.
 * ==========================================================================*/
#include <jni.h>
#include <unistd.h>
#include <string.h>

#define main bada_cli_main
#include "bada.c"
#undef main

/* reset the global append-only state so a re-boot starts from honest zero */
static void agos_reset(void){
    LEDGER.n = 0;
    GRAMMAR.n = 0;
    G_LAST_MAXDIFF = 0.0;
    if (G_LAST_A) G_LAST_A->n = 0;
}

JNIEXPORT jstring JNICALL
Java_com_bada_antigravityos_MainActivity_runBada(JNIEnv *env, jobject thiz, jstring jpath){
    (void)thiz;
    const char *path = (*env)->GetStringUTFChars(env, jpath, NULL);

    agos_reset();

    /* capture stdout: the interpreter prints the whole session via printf */
    fflush(stdout);
    int fds[2];
    if (pipe(fds) != 0){
        (*env)->ReleaseStringUTFChars(env, jpath, path);
        return (*env)->NewStringUTF(env, "boot failed: pipe()");
    }
    int saved = dup(STDOUT_FILENO);
    dup2(fds[1], STDOUT_FILENO);
    close(fds[1]);

    char *src = read_file(path);
    Node *prog = parse_source(src, NULL);
    run_program(prog);

    fflush(stdout);
    dup2(saved, STDOUT_FILENO);   /* closes the last write end -> EOF below */
    close(saved);

    size_t cap = 65536, len = 0;
    char *buf = xmalloc(cap);
    ssize_t n;
    while ((n = read(fds[0], buf + len, cap - len - 1)) > 0){
        len += (size_t)n;
        if (cap - len < 4096){ cap *= 2; buf = xrealloc(buf, cap); }
    }
    close(fds[0]);
    buf[len] = 0;

    (*env)->ReleaseStringUTFChars(env, jpath, path);
    jstring out = (*env)->NewStringUTF(env, buf);
    free(buf);
    free(src);
    return out;
}
