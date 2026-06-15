#ifndef NOEMA_VALUE_H
#define NOEMA_VALUE_H
/*
 * noema_value.h — minimal Value/VM surface shared by the standalone Noema
 * native-function modules (llm_qury.c, readline.c, set_env.c).
 *
 * The full runtime definitions live in noema_read.c / noema_photo5.c; this
 * header provides just enough of the public surface (the Value type, its tags
 * and the value constructors / environment hook) so that the individual
 * native-function sources can be compiled on their own.
 */
#include <stddef.h>

typedef enum {
    T_NULL,
    T_NUMBER,
    T_STRING,
    T_BOOL,
    T_LIST,
    T_HASH,
    T_OBJECT,
    T_FUNC
} ValueType;

typedef struct Value Value;
struct Value {
    ValueType type;
    union {
        double num;
        char  *str;
        int    boolean;
        void  *ptr;
    } v;
};

/* Value constructors / environment registration implemented by the host VM. */
Value *val_string(const char *s);
Value *val_number(double n);
Value *val_null(void);
Value *val_bool(int b);
Value *val_func(Value *(*fn)(int, Value **), int argc);
void   env_set(const char *name, Value *v);

#endif /* NOEMA_VALUE_H */
