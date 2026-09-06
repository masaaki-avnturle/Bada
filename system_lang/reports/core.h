// core.h
#ifndef CORE_H
#define CORE_H

#include "omega_types.h"
#include "omega_functions.h"
#include "manifold.h"
#include "tuplespace.h"
#include "virtualmachine.h"

typedef struct OmegaScript {
  // Internal state and functions for the Omega Script interpreter
} OmegaScript;

OmegaScript* OmegaScript_create(char** bnf_files, int num_files);
void OmegaScript_destroy(OmegaScript* script);
OmegaType* OmegaScript_generate_expression(OmegaScript* script, char* start_symbol, int max_depth);
OmegaType* OmegaScript_evaluate_expression(OmegaScript* script, char* expression);
void OmegaScript_execute(OmegaScript* script, char* code);

char* expression_to_string(OmegaType* expression);
char* type_to_string(OmegaType* type);

#endif // CORE_H
