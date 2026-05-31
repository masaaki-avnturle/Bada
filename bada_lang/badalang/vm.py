"""The Bada virtual machine — a stack-based bytecode interpreter."""

import os
import sys
import math
import time
import threading

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
        # call frames are per-thread; the dict (thread id -> list) lets the
        # GC gather roots across every live Bada thread.
        self.thread_frames = {}
        self.exec_lock = threading.RLock()     # the Bada "GIL"
        from .gc import GarbageCollector
        self.gc = GarbageCollector(self)
        self._install_gc_builtins()
        self._install_runtime_builtins()
        # module / import machinery
        self.base_dir = os.getcwd()
        self.module_cache = {}
        self.importing = set()                 # cycle detection

    @property
    def frames(self):
        fr = self.thread_frames.get(threading.get_ident())
        if fr is None:
            fr = []
            self.thread_frames[threading.get_ident()] = fr
        return fr

    # --- public -----------------------------------------------------------

    def run_main(self, code, base_dir=None):
        if base_dir is not None:
            self.base_dir = base_dir
        self._install_reviser(getattr(code, "reviser_rules", None))
        with self.exec_lock:
            return self.run(code, self.global_env)

    # --- core loop --------------------------------------------------------

    def run(self, code, env, self_obj=None, defining_class=None):
        frame = Frame(code, env, self_obj, defining_class)
        frames = self.frames
        frames.append(frame)
        try:
            return self._run_frame(frame)
        finally:
            frames.pop()

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

    # --- threading & numerical-analysis builtins --------------------------

    def _install_runtime_builtins(self):
        from .objects import Mutex, Channel
        b = self.builtins_env.vars

        # threads
        b["spawn"] = NativeFunction(
            "spawn", lambda a: self._spawn(a[0], a[1:]))
        b["sleep"] = NativeFunction(
            "sleep", lambda a: self._park(lambda: time.sleep(a[0])), 1)
        b["yield_now"] = NativeFunction(
            "yield_now", lambda a: self._park(lambda: time.sleep(0)), 0)
        b["Mutex"] = self._mk_factory("Mutex", Mutex)
        b["Channel"] = self._mk_factory("Channel", Channel)
        b["thread_id"] = NativeFunction(
            "thread_id", lambda a: threading.get_ident(), 0)
        b["cpu_count"] = NativeFunction(
            "cpu_count", lambda a: os.cpu_count() or 1, 0)

        # numerical analysis (differential equations, integral manifolds, ...)
        b["derivative"] = NativeFunction("derivative", self._b_derivative)
        b["gradient"] = NativeFunction("gradient", self._b_gradient)
        b["integrate"] = NativeFunction("integrate", self._b_integrate)
        b["integrate2"] = NativeFunction("integrate2", self._b_integrate2)
        b["solve_ode"] = NativeFunction("solve_ode", self._b_solve_ode)
        b["newton"] = NativeFunction("newton", self._b_newton)

    def _mk_factory(self, name, cls):
        ns = Namespace(name)
        ns.members["new"] = NativeFunction(
            f"{name}.new", lambda a: self.gc.track(cls()))
        return ns

    # --- thread primitives ------------------------------------------------

    def _park(self, blocking_callable):
        """Release the Bada GIL while performing a blocking operation."""
        self.exec_lock.release()
        try:
            return blocking_callable()
        finally:
            self.exec_lock.acquire()

    def _spawn(self, fn, args):
        from .objects import BadaThread
        handle = BadaThread()
        self.gc.track(handle)
        args = list(args)

        def target():
            with self.exec_lock:
                try:
                    handle.result = self.call(fn, args)
                except BadaThrow as e:
                    handle.error = e.value
                except BadaError as e:
                    handle.error = {"type": e.kind, "message": e.message}
                finally:
                    handle.done = True
                    self.thread_frames.pop(threading.get_ident(), None)

        t = threading.Thread(target=target, daemon=True)
        handle.thread = t
        t.start()
        return handle

    def _thread_join(self, handle):
        if handle.thread is not None:
            self._park(handle.thread.join)
        if handle.error is not None:
            from .errors import BadaThrow
            raise BadaThrow(handle.error)
        return handle.result

    def _mutex_lock(self, mx):
        self._park(mx._lock.acquire)
        return None

    def _channel_send(self, ch, value):
        ch._q.put(value)
        return None

    def _channel_receive(self, ch):
        return self._park(ch._q.get)

    def _channel_close(self, ch):
        ch.closed = True
        return None

    # --- numerical analysis -----------------------------------------------

    def _num_call(self, fn, args):
        """Call a Bada function and require a numeric result."""
        r = self.call(fn, list(args))
        if isinstance(r, bool) or not isinstance(r, (int, float)):
            raise BadaTypeError("numerical routine expects the function to return a number")
        return float(r)

    def _b_derivative(self, a):
        fn, x = a[0], a[1]
        h = a[2] if len(a) > 2 else 1e-6
        return (self._num_call(fn, [x + h]) - self._num_call(fn, [x - h])) / (2 * h)

    def _b_gradient(self, a):
        fn, point = a[0], a[1]
        h = a[2] if len(a) > 2 else 1e-6
        grad = []
        for i in range(len(point)):
            fwd = list(point); fwd[i] = fwd[i] + h
            bwd = list(point); bwd[i] = bwd[i] - h
            grad.append((self._num_call(fn, [fwd]) - self._num_call(fn, [bwd])) / (2 * h))
        return grad

    def _b_integrate(self, a):
        """Definite integral via composite Simpson's rule."""
        fn, lo, hi = a[0], float(a[1]), float(a[2])
        n = int(a[3]) if len(a) > 3 else 1000
        if n % 2 == 1:
            n += 1
        h = (hi - lo) / n
        total = self._num_call(fn, [lo]) + self._num_call(fn, [hi])
        for i in range(1, n):
            x = lo + i * h
            total += (4 if i % 2 else 2) * self._num_call(fn, [x])
        return total * h / 3.0

    def _b_integrate2(self, a):
        """Double integral over a rectangle — an integral over a 2-manifold patch."""
        fn = a[0]
        x0, x1, y0, y1 = float(a[1]), float(a[2]), float(a[3]), float(a[4])
        nx = int(a[5]) if len(a) > 5 else 100
        ny = int(a[6]) if len(a) > 6 else 100
        hx = (x1 - x0) / nx
        hy = (y1 - y0) / ny
        total = 0.0
        for i in range(nx):
            xc = x0 + (i + 0.5) * hx
            for j in range(ny):
                yc = y0 + (j + 0.5) * hy
                total += self._num_call(fn, [xc, yc])
        return total * hx * hy

    def _b_solve_ode(self, a):
        """Solve dy/dt = f(t, y) with classic Runge-Kutta (RK4).

        Returns a list of [t, y] samples — a discretised integral curve on
        the solution manifold.
        """
        fn, y0, t0, t1 = a[0], float(a[1]), float(a[2]), float(a[3])
        steps = int(a[4]) if len(a) > 4 else 100
        h = (t1 - t0) / steps
        t, y = t0, y0
        out = [[t, y]]
        for _ in range(steps):
            k1 = self._num_call(fn, [t, y])
            k2 = self._num_call(fn, [t + h / 2, y + h / 2 * k1])
            k3 = self._num_call(fn, [t + h / 2, y + h / 2 * k2])
            k4 = self._num_call(fn, [t + h, y + h * k3])
            y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            t = t + h
            out.append([t, y])
        return out

    def _b_newton(self, a):
        """Find a root of f via the Newton-Raphson method."""
        fn, x = a[0], float(a[1])
        iters = int(a[2]) if len(a) > 2 else 50
        tol = a[3] if len(a) > 3 else 1e-10
        for _ in range(iters):
            fx = self._num_call(fn, [x])
            if abs(fx) < tol:
                break
            dfx = (self._num_call(fn, [x + 1e-7]) - self._num_call(fn, [x - 1e-7])) / 2e-7
            if dfx == 0:
                raise BadaRuntimeError("newton: zero derivative")
            x = x - fx / dfx
        return x

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

        from .objects import FileHandle, Regex, BadaThread, Mutex, Channel
        if isinstance(obj, FileHandle):
            return self._file_attr(obj, name)
        if isinstance(obj, Regex):
            return self._regex_attr(obj, name)
        if isinstance(obj, BadaThread):
            return self._thread_attr(obj, name)
        if isinstance(obj, Mutex):
            return self._mutex_attr(obj, name)
        if isinstance(obj, Channel):
            return self._channel_attr(obj, name)

        from .media import Image, GifWriter
        if isinstance(obj, Image):
            return self._image_attr(obj, name)
        if isinstance(obj, GifWriter):
            return self._gif_attr(obj, name)

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

    def _regex_attr(self, rx, name):
        table = {
            "test": lambda a: rx.test(a[0]),
            "match": lambda a: rx.match(a[0]),
            "find_all": lambda a: rx.find_all(a[0]),
            "replace": lambda a: rx.replace(a[0], a[1]),
            "split": lambda a: rx.split(a[0]),
            "source": lambda a: rx.source,
        }
        if name == "source":
            return rx.source
        if name in table:
            return NativeFunction(f"regex.{name}", table[name])
        raise BadaNameError(f"regex has no method {name!r}")

    def _thread_attr(self, th, name):
        if name == "join":
            return NativeFunction("thread.join", lambda a: self._thread_join(th))
        if name == "result":
            return th.result
        if name == "error":
            return th.error
        if name == "done":
            return th.done
        raise BadaNameError(f"thread has no method {name!r}")

    def _mutex_attr(self, mx, name):
        table = {
            "lock": lambda a: self._mutex_lock(mx),
            "unlock": lambda a: (mx._lock.release(), None)[1],
        }
        if name in table:
            return NativeFunction(f"mutex.{name}", table[name])
        raise BadaNameError(f"mutex has no method {name!r}")

    def _channel_attr(self, ch, name):
        table = {
            "send": lambda a: self._channel_send(ch, a[0]),
            "receive": lambda a: self._channel_receive(ch),
            "close": lambda a: self._channel_close(ch),
            "size": lambda a: ch._q.qsize(),
        }
        if name in table:
            return NativeFunction(f"channel.{name}", table[name])
        raise BadaNameError(f"channel has no method {name!r}")

    def _image_attr(self, img, name):
        table = {
            "set": lambda a: (img.set(a[0], a[1], a[2]), None)[1],
            "set_rgb": lambda a: (img.set_rgb(a[0], a[1], a[2], a[3], a[4]), None)[1],
            "get": lambda a: img.get(a[0], a[1]),
            "fill": lambda a: (img.fill(a[0]), None)[1],
            "save": lambda a: img.save(a[0]),
            "save_png": lambda a: img.save_png(a[0]),
            "data_uri": lambda a: img.data_uri(),
            "to_rgb": lambda a: self.gc.track(img.to_rgb()),
            "to_gray": lambda a: self.gc.track(img.to_gray()),
        }
        if name == "width":
            return img.width
        if name == "height":
            return img.height
        if name == "mode":
            return img.mode
        if name in table:
            return NativeFunction(f"image.{name}", table[name])
        raise BadaNameError(f"image has no method {name!r}")

    def _gif_attr(self, gif, name):
        table = {
            "add": lambda a: (gif.add(a[0]), gif)[1],
            "save": lambda a: gif.save(),
        }
        if name == "frame_count":
            return len(gif.frames)
        if name in table:
            return NativeFunction(f"gif.{name}", table[name])
        raise BadaNameError(f"gif has no method {name!r}")

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
