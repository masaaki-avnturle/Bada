// omega_types.h
#ifndef OMEGA_TYPES_H
#define OMEGA_TYPES_H

typedef struct OmegaType OmegaType;

typedef struct Integer {
    OmegaType* base;
    int value;
} Integer;

typedef struct Float {
    OmegaType* base;
    double value;
} Float;

typedef struct String {
    OmegaType* base;
    char* value;
} String;

Integer* Integer_create(int value);
Float* Float_create(double value);
String* String_create(char* value);

OmegaType* Integer_add(OmegaType* a, OmegaType* b);
OmegaType* Integer_subtract(OmegaType* a, OmegaType* b);
OmegaType* Integer_multiply(OmegaType* a, OmegaType* b);
OmegaType* Integer_divide(OmegaType* a, OmegaType* b);

OmegaType* Float_add(OmegaType* a, OmegaType* b);
OmegaType* Float_subtract(OmegaType* a, OmegaType* b);
OmegaType* Float_multiply(OmegaType* a, OmegaType* b);
OmegaType* Float_divide(OmegaType* a, OmegaType* b);

OmegaType* String_add(OmegaType* a, OmegaType* b);

#endif // OMEGA_TYPES_H


