#include "noema_value.h"
/* readline(prompt) native implementation for Noema */
/* Requires: val_string(), val_null(), Value type definitions, memory utilities */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* native readline: prints prompt (if given) and reads a line from stdin, returns Value* string */
static Value *native_readline(int argc, Value **argv){
  const char *prompt = NULL;
  if (argc >= 1 && argv[0]->type == T_STRING) prompt = argv[0]->v.str;

  /* print prompt (without newline) and flush */
  if (prompt && prompt[0] != '\0') {
    fputs(prompt, stdout);
    fflush(stdout);
  }

  char *line = NULL;
  size_t len = 0;
  ssize_t read = getline(&line, &len, stdin);
  if (read == -1) {
    if (line) free(line);
    return val_null(); /* EOF or error */
  }

  /* remove trailing CR/LF */
  while (read > 0 && (line[read-1] == '\n' || line[read-1] == '\r')) {
    line[--read] = '\0';
  }

  /* Create Value string and free buffer if val_string copies it; adapt if your val_string takes ownership */
  Value *ret = val_string(line);

  /* If val_string duplicates the content, free original; otherwise, if val_string takes ownership, do not free */
  /* Assume val_string clones the input, so free here: */
  free(line);

  return ret;
}

/* Registration: add to bootstrap_env() */
/* env_set("readline", val_func(native_readline, 1)); */

