"""Runtime object model for the Bada language.

Plain Python types are reused where natural (int/float numbers, str
strings, bool, None for nil, list for arrays, dict for maps).  The classes
below model the parts that have no direct Python equivalent: code objects,
functions, classes/instances, the immutable TupleSpace and namespaces.
"""

from .errors import BadaImmutableError, BadaTypeError, BadaRuntimeError
from .opcodes import OPNAMES


class CodeObject:
    """A compiled unit of executable bytecode."""

    def __init__(self, name, params=None):
        self.name = name
        self.params = params or []
        self.code = []        # list of [opcode, arg]
        self.consts = []      # constant pool

    def emit(self, op, arg=None):
        self.code.append([op, arg])
        return len(self.code) - 1

    def add_const(self, value):
        # de-duplicate simple, hashable constants
        try:
            for i, c in enumerate(self.consts):
                if type(c) is type(value) and c == value:
                    return i
        except Exception:
            pass
        self.consts.append(value)
        return len(self.consts) - 1

    def disassemble(self, indent=0):
        pad = "  " * indent
        lines = [f"{pad}<code {self.name}({', '.join(self.params)})>"]
        nested = []
        for i, (op, arg) in enumerate(self.code):
            name = OPNAMES.get(op, str(op))
            if arg is None:
                lines.append(f"{pad}{i:4} {name}")
            else:
                extra = ""
                if op_uses_const(op) and 0 <= arg < len(self.consts):
                    c = self.consts[arg]
                    if isinstance(c, CodeObject):
                        extra = f"   ; <code {c.name}>"
                        nested.append(c)
                    elif isinstance(c, ClassDescriptor):
                        extra = f"   ; class {c.name}"
                        nested.extend(m[1] for m in c.methods)
                    else:
                        extra = f"   ; {c!r}"
                lines.append(f"{pad}{i:4} {name:18}{arg}{extra}")
        for c in nested:
            lines.append(c.disassemble(indent + 1))
        return "\n".join(lines)


def op_uses_const(op):
    from . import opcodes as O
    return op in (
        O.LOAD_CONST, O.LOAD_NAME, O.DECLARE_NAME, O.STORE_NAME,
        O.LOAD_ATTR, O.STORE_ATTR, O.LOAD_SUPER_METHOD,
        O.BINARY_OP, O.UNARY_OP, O.MAKE_FUNCTION, O.BUILD_CLASS,
    )


class ClassDescriptor:
    """Static description of a class, stored in a constant pool."""

    def __init__(self, name, parent_name, fields, methods):
        self.name = name
        self.parent_name = parent_name      # str or None
        self.fields = fields                # list of (name, default CodeObject or None)
        self.methods = methods              # list of (name, CodeObject, is_static)


class BadaFunction:
    """A function or method closure: code + the environment it captured."""

    def __init__(self, code, closure, name=None):
        self.code = code
        self.closure = closure
        self.name = name or code.name

    def __repr__(self):
        return f"<fun {self.name}>"


class BoundMethod:
    def __init__(self, func, receiver, defining_class=None):
        self.func = func
        self.receiver = receiver
        self.defining_class = defining_class

    def __repr__(self):
        return f"<bound method {self.func.name}>"


class NativeFunction:
    def __init__(self, name, fn, arity=None):
        self.name = name
        self.fn = fn
        self.arity = arity  # None = variadic

    def __repr__(self):
        return f"<native {self.name}>"


class BadaClass:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.methods = {}       # name -> BadaFunction
        self.statics = {}       # name -> BadaFunction
        self.field_defs = []    # list of (name, default CodeObject or None)

    def find_method(self, name):
        klass = self
        while klass is not None:
            if name in klass.methods:
                return klass.methods[name], klass
            klass = klass.parent
        return None, None

    def all_field_defs(self):
        chain = []
        klass = self
        stack = []
        while klass is not None:
            stack.append(klass)
            klass = klass.parent
        for klass in reversed(stack):  # base fields first
            chain.extend(klass.field_defs)
        return chain

    def __repr__(self):
        return f"<class {self.name}>"


class BadaInstance:
    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    def __repr__(self):
        return f"<{self.klass.name} instance>"


class TupleSpace:
    """Write-once associative store — the core Bada / Omega::DATABASE idea.

    Once a key has been written it can never be overwritten or deleted,
    modelling the immutable "Akashic record" tuplespace from the design.
    """

    def __init__(self, name="tuplespace"):
        self.name = name
        self._store = {}

    def push(self, key, value):
        if key in self._store:
            raise BadaImmutableError(
                f"tuplespace key {key!r} is write-once and already bound")
        self._store[key] = value
        return value

    def get(self, key):
        if key not in self._store:
            raise BadaRuntimeError(f"tuplespace has no key {key!r}")
        return self._store[key]

    def has(self, key):
        return key in self._store

    def keys(self):
        return list(self._store.keys())

    def values(self):
        return list(self._store.values())

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return f"<TupleSpace {self.name} ({len(self._store)} entries)>"


class Namespace:
    """A simple bag of named members, used for Omega:: and modules."""

    def __init__(self, name, members=None):
        self.name = name
        self.members = members or {}

    def get(self, name):
        if name not in self.members:
            raise BadaRuntimeError(f"namespace {self.name} has no member {name!r}")
        return self.members[name]

    def __repr__(self):
        return f"<namespace {self.name}>"


# --- value -> display string ----------------------------------------------

def bada_repr(value):
    """Source-ish representation (strings quoted)."""
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, float):
        if value == int(value) and abs(value) < 1e16:
            return str(int(value)) + ".0"
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(bada_repr(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{bada_repr(k)}: {bada_repr(v)}" for k, v in value.items()) + "}"
    return str(value)


def bada_str(value):
    """Human display string (strings unquoted)."""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        return bada_repr(value)
    return bada_repr(value)


def is_truthy(value):
    if value is None or value is False:
        return False
    return True
