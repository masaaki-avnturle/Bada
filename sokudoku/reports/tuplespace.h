// tuplespace.h
#ifndef TUPLESPACE_H
#define TUPLESPACE_H

#include "omega_types.h"

typedef struct TupleSpace {
    OmegaArray* tuples;
    HashMap* subscribers;
} TupleSpace;

typedef void (*TupleCallback)(OmegaType* tuple);

TupleSpace* TupleSpace_create();
void TupleSpace_add_tuple(TupleSpace* tuplespace, OmegaType* tuple);
void TupleSpace_remove_tuple(TupleSpace* tuplespace, OmegaType* tuple);
OmegaArray* TupleSpace_query(TupleSpace* tuplespace, OmegaType* pattern);
bool TupleSpace_match_pattern(TupleSpace* tuplespace, OmegaType* tuple, OmegaType* pattern);
void TupleSpace_subscribe(TupleSpace* tuplespace, OmegaType* pattern, TupleCallback callback);
void TupleSpace_notify(TupleSpace* tuplespace, OmegaType* tuple);

#endif // TUPLESPACE_H


