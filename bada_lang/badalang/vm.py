"""The Bada virtual machine — a stack-based bytecode interpreter."""

import os
import sys
import math

from . import opcodes as O
from .objects import (
    CodeObject, ClassDescriptor, BadaFunction, BoundMethod, NativeFunction,
    BadaClass, BadaInstance, TupleSpace, Namespace, bada_str, bada_repr,
    is_truthy,
)
from .builtins import make_builtins
from .errors import (
    BadaNameError, BadaTypeError, BadaRuntimeError, BadaError,
    BadaThrow, BadaModuleError,
)


sys.setrecursionlimit(10000)


class Environment:
    __slots__ = ("vars", "parent")

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise BadaNameError(f"undefined name {name!r}")

    def declare(self, name, value):
        self.vars[name] = value

    def assign(self, name, value):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        # implicit declaration in the current scope
        self.vars[name] = value


class Frame:
    __slots__ = ("code", "env", "self_obj", "defining_class", "stack", "ip",
                 "handlers", "pending")

    def __init__(self, code, env, self_obj=None, defining_class=None):
        self.code = code
        self.env = env
        self.self_obj = self_obj
        self.defining_class = defining_class
        self.stack = []
        self.ip = 0
        self.handlers = []   # stack of (catch_ip, finally_ip, stack_depth)
        self.pending = None  # exception awaiting re-raise after a finally block


class VM:
    def __init__(self):
        self.builtins_env = Environment()
        self.builtins_env.vars = make_builtins()
        self.global_env = Environment(self.builtins_env)
        self.frames = []                       # live call frames (GC roots)
        from .gc import GarbageCollector
        self.gc = GarbageCollector(self)
        self._install_gc_builtins()
        # module / import machinery
        self.base_dir = os.getcwd()
        self.module_cache = {}
        self.importing = set()                 # cycle detection

    # --- public -----------------------------------------------------------

    def run_main(self, code, base_dir=None):
        if base_dir is not None:
            self.base_dir = base_dir
        self._install_reviser(getattr(code, "reviser_rules", None))
        return self.run(code, self.global_env)

    # --- core loop --------------------------------------------------------

    def run(self, code, env, self_obj=None, defining_class=None):
        frame = Frame(code, env, self_obj, defining_class)
        self.frames.append(frame)
        try:
            return self._run_frame(frame)
        finally:
            self.frames.pop()

    def _run_frame(self, frame):
        stack = frame.stack
        code = frame.code
        env = frame.env
        consts = code.consts
        instructions = code.code
        push = stack.append
        pop = stack.pop
        gc = self.gc

        while frame.ip < len(instructions):
            # safe point: only collect between instructions, when all live
            # temporaries are on a frame stack or in an environment (i.e. roots)
            if gc.allocs >= gc.threshold:
                gc.maybe_collect()

            op, arg = instructions[frame.ip]
            frame.ip += 1

            try:
                if op == O.LOAD_CONST:
                    push(consts[arg])
                elif op == O.LOAD_NAME:
                    push(env.get(consts[arg]))
                elif op == O.DECLARE_NAME:
                    env.declare(consts[arg], pop())
                elif op == O.STORE_NAME:
                    env.assign(consts[arg], stack[-1])  # leave value as result
                elif op == O.LOAD_SELF:
                    if frame.self_obj is None:
                        raise BadaRuntimeError("'self' used outside a method")
                    push(frame.self_obj)
                elif op == O.POP:
                    pop()
                elif op == O.DUP:
                    push(stack[-1])
                elif op == O.BUILD_LIST:
                    items = [pop() for _ in range(arg)][::-1]
                    push(gc.track(items))
                elif op == O.BUILD_MAP:
                    pairs = {}
                    tmp = [pop() for _ in range(2 * arg)][::-1]
                    for i in range(0, len(tmp), 2):
                        pairs[tmp[i]] = tmp[i + 1]
                    push(gc.track(pairs))
                elif op == O.LOAD_ATTR:
                    obj = pop()
                    push(self.get_attr(obj, consts[arg]))
                elif op == O.STORE_ATTR:
                    value = pop()
                    obj = pop()
                    self.set_attr(obj, consts[arg], value)
                    push(value)
                elif op == O.LOAD_INDEX:
                    index = pop()
                    obj = pop()
                    push(self.get_index(obj, index))
                elif op == O.STORE_INDEX:
                    value = pop()
                    index = pop()
                    obj = pop()
                    self.set_index(obj, index, value)
                    push(value)
                elif op == O.BINARY_OP:
                    right = pop()
                    left = pop()
                    push(self.binary_op(consts[arg], left, right))
                elif op == O.UNARY_OP:
                    push(self.unary_op(consts[arg], pop()))
                elif op == O.JUMP:
                    frame.ip = arg
                elif op == O.JUMP_IF_FALSE:
                    if not is_truthy(pop()):
                        frame.ip = arg
                elif op == O.JUMP_IF_TRUE:
                    if is_truthy(pop()):
                        frame.ip = arg
                elif op == O.CALL:
                    args = [pop() for _ in range(arg)][::-1]
                    callee = pop()
                    push(self.call(callee, args))
                elif op == O.MAKE_FUNCTION:
                    push(gc.track(BadaFunction(consts[arg], env)))
                elif op == O.BUILD_CLASS:
                    push(gc.track(self.build_class(consts[arg], env)))
                elif op == O.LOAD_SUPER_METHOD:
                    push(self.load_super_method(frame, consts[arg]))
                elif op == O.PRINT:
                    vals = [pop() for _ in range(arg)][::-1]
                    print(" ".join(bada_str(v) for v in vals))
                elif op == O.GET_ITER:
                    push(self.get_iter(pop()))
                elif op == O.FOR_ITER:
                    it = stack[-1]
                    try:
                        push(next(it))
                    except StopIteration:
                        frame.ip = arg
                elif op == O.SETUP_TRY:
                    catch_ip, finally_ip = consts[arg]
                    frame.handlers.append((catch_ip, finally_ip, len(stack)))
                elif op == O.POP_BLOCK:
                    frame.handlers.pop()
                elif op == O.THROW:
                    raise BadaThrow(pop())
                elif op == O.RERAISE:
                    exc = frame.pending
                    frame.pending = None
                    if exc is not None:
                        raise exc
                elif op == O.IMPORT_MODULE:
                    push(self.import_module(consts[arg]))
                elif op == O.RETURN:
                    return pop()
                elif op == O.NOP:
                    pass
                else:
                    raise BadaRuntimeError(f"unknown opcode {op}")

            except (BadaError, BadaThrow) as exc:
                if not frame.handlers:
                    raise
                catch_ip, finally_ip, depth = frame.handlers.pop()
                del stack[depth:]                 # unwind operand stack
                if catch_ip is not None:
                    # enter catch: push the exception value, and install a
                    # finally-only handler so a throw in catch still runs finally
                    push(self._exc_value(exc))
                    frame.handlers.append((None, finally_ip, depth))
                    frame.pending = None
                    frame.ip = catch_ip
                else:
                    # no catch (or finally-only handler): run finally, then reraise
                    frame.pending = exc
                    frame.ip = finally_ip

        return None

    @staticmethod
    def _exc_value(exc):
        """Convert a caught exception into the value bound in `catch (e)`."""
        if isinstance(exc, BadaThrow):
            return exc.value
        return {"type": exc.kind, "message": exc.message}

    # --- garbage collector & reviser wiring -------------------------------

    def _install_gc_builtins(self):
        gc = self.gc

        def gc_collect(args):
            return gc.collect()

        def gc_stats(args):
            return gc.stats()

        def gc_enable(args):
            gc.enabled = True
            return True

        def gc_disable(args):
            gc.enabled = False
            return False

        def gc_threshold(args):
            gc.threshold = int(args[0])
            return gc.threshold

        def gc_heap(args):
            return len(gc.heap)

        b = self.builtins_env.vars
        b["gc"] = NativeFunction("gc", gc_collect, 0)
        b["gc_collect"] = NativeFunction("gc_collect", gc_collect, 0)
        b["gc_stats"] = NativeFunction("gc_stats", gc_stats, 0)
        b["gc_enable"] = NativeFunction("gc_enable", gc_enable, 0)
        b["gc_disable"] = NativeFunction("gc_disable", gc_disable, 0)
        b["gc_threshold"] = NativeFunction("gc_threshold", gc_threshold, 1)
        b["gc_heap"] = NativeFunction("gc_heap", gc_heap, 0)

    def _install_reviser(self, rules):
        """Expose the applied reviser rules as an immutable Reviser tuplespace."""
        space = TupleSpace("reviser")
        if rules:
            for i, rule in enumerate(rules):
                space.push(f"{i}:{rule.kind}:{rule.pattern}", rule.replacement)
        self.global_env.declare("Reviser", space)

    # --- import / library loading -----------------------------------------

    def import_module(self, parts):
        parts = list(parts)

        # 1. built-in namespace (e.g. Omega, Omega::DATABASE)
        first = parts[0]
        if first in self.builtins_env.vars and isinstance(
                self.builtins_env.vars[first], Namespace):
            value = self.builtins_env.vars[first]
            for name in parts[1:]:
                value = self.get_attr(value, name)
            return value

        # 2. file-based module / library
        path = self._resolve_module(parts)
        if path is None:
            spec = "::".join(parts)
            raise BadaModuleError(
                f"cannot find module {spec!r} (searched {self._search_dirs()})")
        if path in self.module_cache:
            return self.module_cache[path]
        if path in self.importing:
            raise BadaModuleError(f"circular import of {path!r}")

        self.importing.add(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
            from .compiler import compile_source
            code = compile_source(source, path)
            module_env = Environment(self.builtins_env)
            saved_base = self.base_dir
            self.base_dir = os.path.dirname(path)
            try:
                self.run(code, module_env)
            finally:
                self.base_dir = saved_base
            name = parts[-1]
            ns = Namespace(name, dict(module_env.vars))
            self.gc.track(ns)
            self.module_cache[path] = ns
            return ns
        finally:
            self.importing.discard(path)

    def _search_dirs(self):
        dirs = [self.base_dir, os.path.join(self.base_dir, "lib")]
        env_path = os.environ.get("BADA_PATH", "")
        dirs.extend(p for p in env_path.split(os.pathsep) if p)
        # bundled standard library: <bada_lang>/lib
        stdlib = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lib")
        dirs.append(stdlib)
        return dirs

    def _resolve_module(self, parts):
        # explicit file path form: import "dir/file.bada"
        if len(parts) == 1 and (parts[0].endswith(".bada") or "/" in parts[0]):
            cand = parts[0]
            if not cand.endswith(".bada"):
                cand += ".bada"
            for d in self._search_dirs():
                p = os.path.join(d, cand)
                if os.path.isfile(p):
                    return os.path.abspath(p)
            if os.path.isfile(cand):
                return os.path.abspath(cand)
            return None
        # dotted/namespaced form: import a::b::c  ->  a/b/c.bada
        rel = os.path.join(*parts) + ".bada"
        for d in self._search_dirs():
            p = os.path.join(d, rel)
            if os.path.isfile(p):
                return os.path.abspath(p)
        # also try just the last component as a flat module name
        flat = parts[-1] + ".bada"
        for d in self._search_dirs():
            p = os.path.join(d, flat)
            if os.path.isfile(p):
                return os.path.abspath(p)
        return None

    # --- calling ----------------------------------------------------------

    def call(self, callee, args):
        if isinstance(callee, NativeFunction):
            if callee.arity is not None and len(args) != callee.arity:
                raise BadaTypeError(
                    f"{callee.name}() expects {callee.arity} arg(s), got {len(args)}")
            return self.gc.track(callee.fn(args))

        if isinstance(callee, BadaFunction):
            return self.invoke(callee, args, self_obj=None, defining_class=None)

        if isinstance(callee, BoundMethod):
            return self.invoke(callee.func, args,
                               self_obj=callee.receiver,
                               defining_class=callee.defining_class)

        if isinstance(callee, BadaClass):
            return self.construct(callee, args)

        raise BadaTypeError(f"value of type {type(callee).__name__} is not callable")

    def invoke(self, func, args, self_obj, defining_class):
        params = func.code.params
        if len(args) != len(params):
            raise BadaTypeError(
                f"{func.name}() expects {len(params)} arg(s), got {len(args)}")
        env = Environment(func.closure)
        for name, value in zip(params, args):
            env.declare(name, value)
        return self.run(func.code, env, self_obj, defining_class)

    def construct(self, klass, args):
        instance = BadaInstance(klass)
        self.gc.track(instance)
        # initialise fields (base classes first) by running default code
        for name, default_code in klass.all_field_defs():
            if default_code is None:
                instance.fields[name] = None
            else:
                env = Environment(self.global_env)
                instance.fields[name] = self.run(default_code, env, instance, klass)
        init, owner = klass.find_method("init")
        if init is not None:
            self.invoke(init, args, self_obj=instance, defining_class=owner)
        elif args:
            raise BadaTypeError(
                f"{klass.name} has no 'init' but was given {len(args)} argument(s)")
        return instance

    # --- class construction ----------------------------------------------

    def build_class(self, descriptor, env):
        parent = None
        if descriptor.parent_name is not None:
            parent = env.get(descriptor.parent_name)
            if not isinstance(parent, BadaClass):
                raise BadaTypeError(
                    f"parent {descriptor.parent_name!r} is not a class")
        klass = BadaClass(descriptor.name, parent)
        klass.field_defs = list(descriptor.fields)
        for name, code, is_static in descriptor.methods:
            func = BadaFunction(code, env, name=f"{descriptor.name}.{name}")
            if is_static:
                klass.statics[name] = func
            else:
                klass.methods[name] = func
        return klass

    def load_super_method(self, frame, name):
        if frame.self_obj is None or frame.defining_class is None:
            raise BadaRuntimeError("'super' used outside a method")
        parent = frame.defining_class.parent
        if parent is None:
            raise BadaRuntimeError(
                f"class {frame.defining_class.name} has no parent for 'super'")
        method, owner = parent.find_method(name)
        if method is None:
            raise BadaNameError(f"super has no method {name!r}")
        return BoundMethod(method, frame.self_obj, owner)

    # --- attribute / index access ----------------------------------------

    def get_attr(self, obj, name):
        if isinstance(obj, BadaInstance):
            if name in obj.fields:
                return obj.fields[name]
            method, owner = obj.klass.find_method(name)
            if method is not None:
                return BoundMethod(method, obj, owner)
            raise BadaNameError(f"{obj.klass.name} has no attribute {name!r}")

        if isinstance(obj, BadaClass):
            if name == "new":
                return NativeFunction(
                    f"{obj.name}.new", lambda a, k=obj: self.construct(k, a))
            if name == "name":
                return obj.name
            if name in obj.statics:
                return BoundMethod(obj.statics[name], obj, obj)
            raise BadaNameError(f"class {obj.name} has no static member {name!r}")

        if isinstance(obj, Namespace):
            return obj.get(name)

        if isinstance(obj, TupleSpace):
            return self._tuplespace_attr(obj, name)

        if isinstance(obj, dict):
            return self._map_attr(obj, name)

        if isinstance(obj, list):
            return self._list_attr(obj, name)

        if isinstance(obj, str):
            return self._str_attr(obj, name)

        from .objects import FileHandle
        if isinstance(obj, FileHandle):
            return self._file_attr(obj, name)

        raise BadaTypeError(f"cannot read attribute {name!r} on {type(obj).__name__}")

    def set_attr(self, obj, name, value):
        if isinstance(obj, BadaInstance):
            obj.fields[name] = value
            return
        raise BadaTypeError(
            f"cannot set attribute {name!r} on {type(obj).__name__}")

    def get_index(self, obj, index):
        if isinstance(obj, list):
            i = int(index)
            if i < 0:
                i += len(obj)
            if not (0 <= i < len(obj)):
                raise BadaRuntimeError(f"list index {index} out of range")
            return obj[i]
        if isinstance(obj, dict):
            if index not in obj:
                raise BadaRuntimeError(f"map has no key {index!r}")
            return obj[index]
        if isinstance(obj, TupleSpace):
            return obj.get(index)
        if isinstance(obj, str):
            i = int(index)
            if i < 0:
                i += len(obj)
            return obj[i]
        raise BadaTypeError(f"cannot index {type(obj).__name__}")

    def set_index(self, obj, index, value):
        if isinstance(obj, list):
            i = int(index)
            if i < 0:
                i += len(obj)
            if not (0 <= i < len(obj)):
                raise BadaRuntimeError(f"list index {index} out of range")
            obj[i] = value
            return
        if isinstance(obj, dict):
            obj[index] = value
            return
        if isinstance(obj, TupleSpace):
            obj.push(index, value)  # write-once
            return
        raise BadaTypeError(f"cannot index-assign {type(obj).__name__}")

    # --- builtin-type method tables ---------------------------------------

    def _tuplespace_attr(self, ts, name):
        table = {
            "push": lambda a: ts.push(a[0], a[1]),
            "get": lambda a: ts.get(a[0]),
            "has": lambda a: ts.has(a[0]),
            "keys": lambda a: ts.keys(),
            "values": lambda a: ts.values(),
            "len": lambda a: len(ts),
            "name": lambda a: ts.name,
        }
        if name == "name":
            return ts.name
        if name in table:
            return NativeFunction(f"tuplespace.{name}", table[name])
        raise BadaNameError(f"tuplespace has no method {name!r}")

    def _map_attr(self, m, name):
        table = {
            "get": lambda a: m.get(a[0], a[1] if len(a) > 1 else None),
            "set": lambda a: (m.__setitem__(a[0], a[1]), a[1])[1],
            "has": lambda a: a[0] in m,
            "keys": lambda a: list(m.keys()),
            "values": lambda a: list(m.values()),
            "len": lambda a: len(m),
            "remove": lambda a: m.pop(a[0], None),
        }
        if name in table:
            return NativeFunction(f"map.{name}", table[name])
        raise BadaNameError(f"map has no method {name!r}")

    def _list_attr(self, lst, name):
        table = {
            "push": lambda a: (lst.append(a[0]), lst)[1],
            "pop": lambda a: lst.pop(),
            "len": lambda a: len(lst),
            "first": lambda a: lst[0] if lst else None,
            "last": lambda a: lst[-1] if lst else None,
            "contains": lambda a: a[0] in lst,
            "reverse": lambda a: (lst.reverse(), lst)[1],
            "sort": lambda a: (lst.sort(), lst)[1],
        }
        if name in table:
            return NativeFunction(f"list.{name}", table[name])
        raise BadaNameError(f"list has no method {name!r}")

    def _file_attr(self, fh, name):
        table = {
            "read": lambda a: fh.read(),
            "readline": lambda a: fh.readline(),
            "lines": lambda a: fh.lines(),
            "write": lambda a: fh.write(bada_str(a[0])),
            "close": lambda a: fh.close(),
            "path": lambda a: fh.path,
            "mode": lambda a: fh.mode,
        }
        if name in ("path", "mode"):
            return table[name](None)
        if name in table:
            return NativeFunction(f"file.{name}", table[name])
        raise BadaNameError(f"file has no method {name!r}")

    def _str_attr(self, s, name):
        table = {
            "len": lambda a: len(s),
            "upper": lambda a: s.upper(),
            "lower": lambda a: s.lower(),
            "trim": lambda a: s.strip(),
            "split": lambda a: s.split(a[0]) if a else s.split(),
            "contains": lambda a: a[0] in s,
            "replace": lambda a: s.replace(a[0], a[1]),
            "starts": lambda a: s.startswith(a[0]),
            "ends": lambda a: s.endswith(a[0]),
        }
        if name in table:
            return NativeFunction(f"string.{name}", table[name])
        raise BadaNameError(f"string has no method {name!r}")

    # --- operators --------------------------------------------------------

    DUNDER = {
        "+": "__add__", "-": "__sub__", "*": "__mul__", "/": "__div__",
        "%": "__mod__", "==": "__eq__", "!=": "__ne__",
        "<": "__lt__", ">": "__gt__", "<=": "__le__", ">=": "__ge__",
        "<~": "__lact__", "~>": "__ract__", "-<": "__branch__",
    }

    def binary_op(self, op, left, right):
        # operator overloading on Bada instances
        if isinstance(left, BadaInstance):
            method, owner = left.klass.find_method(self.DUNDER.get(op, ""))
            if method is not None:
                return self.invoke(method, [right], left, owner)

        if op == "+":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            self._numeric2(op, left, right)
            return left + right
        if op == "-":
            self._numeric2(op, left, right)
            return left - right
        if op == "*":
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            if isinstance(left, list) and isinstance(right, int):
                return left * right
            self._numeric2(op, left, right)
            return left * right
        if op == "/":
            self._numeric2(op, left, right)
            if right == 0:
                raise BadaRuntimeError("division by zero")
            return left / right
        if op == "%":
            self._numeric2(op, left, right)
            if right == 0:
                raise BadaRuntimeError("modulo by zero")
            return left % right
        if op == "==":
            return self._equals(left, right)
        if op == "!=":
            return not self._equals(left, right)
        if op in ("<", ">", "<=", ">="):
            return self._compare(op, left, right)
        if op in ("<~", "~>", "-<"):
            return self._manifold(op, left, right)
        raise BadaRuntimeError(f"unknown binary operator {op!r}")

    def _numeric2(self, op, left, right):
        if not isinstance(left, (int, float)) or isinstance(left, bool) \
                or not isinstance(right, (int, float)) or isinstance(right, bool):
            raise BadaTypeError(
                f"operator {op!r} needs numbers, got "
                f"{type(left).__name__} and {type(right).__name__}")

    def _equals(self, left, right):
        if isinstance(left, BadaInstance) or isinstance(right, BadaInstance):
            return left is right
        if isinstance(left, bool) or isinstance(right, bool):
            return left is right
        return left == right

    def _compare(self, op, left, right):
        ok = (isinstance(left, (int, float)) and isinstance(right, (int, float))) \
            or (isinstance(left, str) and isinstance(right, str))
        if not ok:
            raise BadaTypeError(
                f"cannot compare {type(left).__name__} and {type(right).__name__}")
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        return left >= right

    def _manifold(self, op, left, right):
        """Default numeric semantics for the manifold operators."""
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise BadaTypeError(f"manifold operator {op!r} needs numbers")
        if op == "<~":   # left action  pi(left, right) = pi*left*log(right)
            if right <= 0:
                raise BadaRuntimeError("'<~' requires right operand > 0")
            return math.pi * left * math.log(right)
        if op == "~>":   # right action  left * exp(-right*log(right))
            if right <= 0:
                raise BadaRuntimeError("'~>' requires right operand > 0")
            return left * math.exp(-right * math.log(right))
        if op == "-<":   # branch / manifold integral  beta(left, right)
            return math.gamma(left) * math.gamma(right) / math.gamma(left + right)
        raise BadaRuntimeError(f"unknown manifold operator {op!r}")

    def unary_op(self, op, value):
        if op == "-":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise BadaTypeError("unary '-' needs a number")
            return -value
        if op == "not":
            return not is_truthy(value)
        raise BadaRuntimeError(f"unknown unary operator {op!r}")

    # --- iteration --------------------------------------------------------

    def get_iter(self, obj):
        if isinstance(obj, list):
            return iter(obj)
        if isinstance(obj, str):
            return iter(obj)
        if isinstance(obj, dict):
            return iter(list(obj.keys()))
        if isinstance(obj, TupleSpace):
            return iter(obj.keys())
        raise BadaTypeError(f"{type(obj).__name__} is not iterable")
