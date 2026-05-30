"""Bytecode opcode definitions for the Bada virtual machine."""

# Each opcode is a small integer.  The compiler emits (opcode, arg) pairs;
# `arg` is either None or an integer (often an index into the constant pool).

(
    LOAD_CONST,        # push consts[arg]
    LOAD_NAME,         # push value of name consts[arg]
    DECLARE_NAME,      # define name consts[arg] in current scope from stack top
    STORE_NAME,        # assign to existing name consts[arg]
    LOAD_ATTR,         # obj.name  -> push attribute consts[arg]
    STORE_ATTR,        # obj, value -> set obj.name = value
    LOAD_INDEX,        # obj, idx -> push obj[idx]
    STORE_INDEX,       # obj, idx, value -> obj[idx] = value
    LOAD_SELF,         # push current 'self'
    LOAD_SUPER_METHOD, # push bound super method consts[arg]
    POP,               # discard top of stack
    DUP,               # duplicate top of stack
    BUILD_LIST,        # pop arg elements -> push list
    BUILD_MAP,         # pop 2*arg elements -> push map
    BINARY_OP,         # apply binary operator consts[arg]
    UNARY_OP,          # apply unary operator consts[arg]
    JUMP,              # ip = arg
    JUMP_IF_FALSE,     # pop; if falsey ip = arg
    JUMP_IF_TRUE,      # pop; if truthy ip = arg
    CALL,              # pop arg args + callee -> push result
    MAKE_FUNCTION,     # build closure from CodeObject consts[arg]
    BUILD_CLASS,       # build class from ClassDescriptor consts[arg]
    RETURN,            # return top of stack from current frame
    PRINT,             # pop arg values and print them
    GET_ITER,          # replace top with an iterator
    FOR_ITER,          # advance iterator; jump to arg when exhausted
    NOP,
) = range(27)


OPNAMES = {
    LOAD_CONST: "LOAD_CONST",
    LOAD_NAME: "LOAD_NAME",
    DECLARE_NAME: "DECLARE_NAME",
    STORE_NAME: "STORE_NAME",
    LOAD_ATTR: "LOAD_ATTR",
    STORE_ATTR: "STORE_ATTR",
    LOAD_INDEX: "LOAD_INDEX",
    STORE_INDEX: "STORE_INDEX",
    LOAD_SELF: "LOAD_SELF",
    LOAD_SUPER_METHOD: "LOAD_SUPER_METHOD",
    POP: "POP",
    DUP: "DUP",
    BUILD_LIST: "BUILD_LIST",
    BUILD_MAP: "BUILD_MAP",
    BINARY_OP: "BINARY_OP",
    UNARY_OP: "UNARY_OP",
    JUMP: "JUMP",
    JUMP_IF_FALSE: "JUMP_IF_FALSE",
    JUMP_IF_TRUE: "JUMP_IF_TRUE",
    CALL: "CALL",
    MAKE_FUNCTION: "MAKE_FUNCTION",
    BUILD_CLASS: "BUILD_CLASS",
    RETURN: "RETURN",
    PRINT: "PRINT",
    GET_ITER: "GET_ITER",
    FOR_ITER: "FOR_ITER",
    NOP: "NOP",
}
