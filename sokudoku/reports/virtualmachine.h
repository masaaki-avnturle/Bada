// virtualmachine.h
#ifndef VIRTUALMACHINE_H
#define VIRTUALMACHINE_H

#include "tuplespace.h"

typedef void (*OmegaFunction)(OmegaType** args, int num_args);

typedef struct VirtualMachine {
    TupleSpace* tuplespace;
    HashMap* functions;
} VirtualMachine;

VirtualMachine* VirtualMachine_create(TupleSpace* tuplespace);
void VirtualMachine_execute(VirtualMachine* vm, char* code);
void VirtualMachine_load_module(VirtualMachine* vm, char* module_name);
void VirtualMachine_call_function(VirtualMachine* vm, char* function_name, OmegaType** args, int num_args);
void VirtualMachine_register_function(VirtualMachine* vm, char* name, OmegaFunction func);

#endif // VIRTUALMACHINE_H

