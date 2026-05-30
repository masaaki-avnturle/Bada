"""Built-in functions, math, and the Omega namespace for Bada.

Includes the "manifold / operator-algebra" flavoured functions that give
the Bada language its identity: zeta, gamma, beta and the non-commutative
pi-operator pi_op.
"""

import math

from .objects import (
    NativeFunction, Namespace, TupleSpace, bada_str, bada_repr,
)
from .errors import BadaTypeError, BadaRuntimeError


def _native(name, arity=None):
    def wrap(fn):
        return NativeFunction(name, fn, arity)
    return wrap


# --- core builtins ---------------------------------------------------------

def b_print_str(args):
    return bada_str(args[0])


def make_builtins():
    funcs = {}

    def reg(name, fn, arity=None):
        funcs[name] = NativeFunction(name, fn, arity)

    # type / conversion
    reg("len", lambda a: _len(a[0]), 1)
    reg("str", lambda a: bada_str(a[0]), 1)
    reg("repr", lambda a: bada_repr(a[0]), 1)
    reg("num", lambda a: _num(a[0]), 1)
    reg("int", lambda a: int(_num(a[0])), 1)
    reg("type", lambda a: _typename(a[0]), 1)
    reg("bool", lambda a: not (a[0] is None or a[0] is False), 1)

    # list / map operations
    reg("list", lambda a: list(a))
    reg("push", lambda a: _push(a[0], a[1]), 2)
    reg("pop", lambda a: _pop(a[0]), 1)
    reg("first", lambda a: a[0][0] if a[0] else None, 1)
    reg("last", lambda a: a[0][-1] if a[0] else None, 1)
    reg("index", lambda a: a[0][int(a[1])], 2)
    reg("range", lambda a: _range(a))
    reg("keys", lambda a: _keys(a[0]), 1)
    reg("values", lambda a: _values(a[0]), 1)
    reg("has", lambda a: _has(a[0], a[1]), 2)
    reg("map_set", lambda a: _map_set(a[0], a[1], a[2]), 3)

    # string operations
    reg("split", lambda a: a[0].split(a[1]) if len(a) > 1 else a[0].split(), None)
    reg("join", lambda a: a[1].join(bada_str(x) for x in a[0]), 2)
    reg("upper", lambda a: a[0].upper(), 1)
    reg("lower", lambda a: a[0].lower(), 1)
    reg("trim", lambda a: a[0].strip(), 1)
    reg("replace", lambda a: a[0].replace(a[1], a[2]), 3)
    reg("contains", lambda a: a[1] in a[0], 2)

    # math
    reg("abs", lambda a: abs(a[0]), 1)
    reg("floor", lambda a: math.floor(a[0]), 1)
    reg("ceil", lambda a: math.ceil(a[0]), 1)
    reg("round", lambda a: round(a[0], int(a[1]) if len(a) > 1 else 0))
    reg("sqrt", lambda a: math.sqrt(a[0]), 1)
    reg("pow", lambda a: math.pow(a[0], a[1]), 2)
    reg("sin", lambda a: math.sin(a[0]), 1)
    reg("cos", lambda a: math.cos(a[0]), 1)
    reg("tan", lambda a: math.tan(a[0]), 1)
    reg("exp", lambda a: math.exp(a[0]), 1)
    reg("log", lambda a: math.log(a[0]) if len(a) == 1 else math.log(a[0], a[1]))
    reg("max", lambda a: max(a[0]) if len(a) == 1 else max(a), None)
    reg("min", lambda a: min(a[0]) if len(a) == 1 else min(a), None)

    # operator-algebra / manifold functions
    reg("gamma", lambda a: math.gamma(a[0]), 1)
    reg("beta", lambda a: _beta(a[0], a[1]), 2)
    reg("zeta", lambda a: _zeta(a[0], int(a[1]) if len(a) > 1 else 2000))
    reg("pi_op", lambda a: _pi_op(a[0], a[1]), 2)

    # io / system
    reg("input", lambda a: input(bada_str(a[0]) if a else ""))
    reg("assert", lambda a: _assert(a))
    reg("error", lambda a: _error(a[0]))
    reg("clock", lambda a: __import__("time").time())

    # constants
    funcs["PI"] = math.pi
    funcs["E"] = math.e
    funcs["INF"] = math.inf

    funcs["TupleSpace"] = _tuplespace_class()
    funcs["Omega"] = _omega_namespace(funcs)

    return funcs


# --- implementations -------------------------------------------------------

def _len(x):
    if isinstance(x, (str, list, dict)):
        return len(x)
    if isinstance(x, TupleSpace):
        return len(x)
    raise BadaTypeError(f"len() not supported for {_typename(x)}")


def _num(x):
    if isinstance(x, bool):
        return 1 if x else 0
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        try:
            return int(x) if x.strip().lstrip("-+").isdigit() else float(x)
        except ValueError:
            raise BadaTypeError(f"cannot convert {x!r} to number")
    raise BadaTypeError(f"cannot convert {_typename(x)} to number")


def _typename(x):
    if x is None:
        return "nil"
    if isinstance(x, bool):
        return "bool"
    if isinstance(x, int):
        return "int"
    if isinstance(x, float):
        return "float"
    if isinstance(x, str):
        return "string"
    if isinstance(x, list):
        return "list"
    if isinstance(x, dict):
        return "map"
    if isinstance(x, TupleSpace):
        return "tuplespace"
    from .objects import BadaInstance, BadaClass, BadaFunction, BoundMethod, NativeFunction as NF
    if isinstance(x, BadaInstance):
        return x.klass.name
    if isinstance(x, BadaClass):
        return "class"
    if isinstance(x, (BadaFunction, BoundMethod, NF)):
        return "function"
    return type(x).__name__


def _push(lst, value):
    if not isinstance(lst, list):
        raise BadaTypeError("push() expects a list")
    lst.append(value)
    return lst


def _pop(lst):
    if not isinstance(lst, list):
        raise BadaTypeError("pop() expects a list")
    if not lst:
        raise BadaRuntimeError("pop() from empty list")
    return lst.pop()


def _range(a):
    if len(a) == 1:
        return list(range(int(a[0])))
    if len(a) == 2:
        return list(range(int(a[0]), int(a[1])))
    return list(range(int(a[0]), int(a[1]), int(a[2])))


def _keys(x):
    if isinstance(x, dict):
        return list(x.keys())
    if isinstance(x, TupleSpace):
        return x.keys()
    raise BadaTypeError("keys() expects a map or tuplespace")


def _values(x):
    if isinstance(x, dict):
        return list(x.values())
    if isinstance(x, TupleSpace):
        return x.values()
    raise BadaTypeError("values() expects a map or tuplespace")


def _has(x, key):
    if isinstance(x, dict):
        return key in x
    if isinstance(x, TupleSpace):
        return x.has(key)
    if isinstance(x, (list, str)):
        return key in x
    raise BadaTypeError("has() expects a collection")


def _map_set(m, k, v):
    if not isinstance(m, dict):
        raise BadaTypeError("map_set() expects a map")
    m[k] = v
    return m


def _assert(a):
    cond = a[0]
    if cond is None or cond is False:
        msg = bada_str(a[1]) if len(a) > 1 else "assertion failed"
        raise BadaRuntimeError(msg)
    return True


def _error(msg):
    raise BadaRuntimeError(bada_str(msg))


# --- operator-algebra functions --------------------------------------------

def _beta(p, q):
    """Euler beta:  B(p,q) = Gamma(p) Gamma(q) / Gamma(p+q)."""
    return math.gamma(p) * math.gamma(q) / math.gamma(p + q)


def _zeta(s, terms=2000):
    """Riemann zeta by truncated Dirichlet series (real s > 1).

    Illustrative numeric implementation for the operator-algebra demos.
    """
    if s <= 1:
        raise BadaRuntimeError("zeta(s) implemented for real s > 1")
    total = 0.0
    for n in range(1, terms + 1):
        total += 1.0 / (n ** s)
    return total


def _pi_op(chi, x):
    """Non-commutative pi-operator (real surrogate):  pi(chi, x) = pi * chi * log x.

    Models the framework relation pi(chi,x) = [i*pi(chi,x), f(x)] using the
    imaginary magnitude pi*chi*log(x).
    """
    if x <= 0:
        raise BadaRuntimeError("pi_op(chi, x) requires x > 0")
    return math.pi * chi * math.log(x)


# --- TupleSpace as a constructible class object -----------------------------

def _tuplespace_class():
    """A pseudo-class exposing TupleSpace.new(name?) to scripts."""
    ns = Namespace("TupleSpace")
    ns.members["new"] = NativeFunction(
        "TupleSpace.new",
        lambda a: TupleSpace(a[0] if a else "tuplespace"),
        None,
    )
    return ns


def _omega_namespace(funcs):
    """Omega:: namespace — the operator-algebra database universe."""
    members = {
        "DATABASE": _tuplespace_class(),       # Omega::DATABASE.new(...)
        "zeta": funcs["zeta"],
        "gamma": funcs["gamma"],
        "beta": funcs["beta"],
        "pi_op": funcs["pi_op"],
        "PI": math.pi,
    }
    return Namespace("Omega", members)
