"""Garbage collector (ガベージコレクション) for the Bada virtual machine.

A tracing, mark-and-sweep collector over the Bada object graph.  Every heap
object the VM allocates (instances, lists, maps, tuplespaces, functions,
classes, bound methods) is registered in the collector's heap.  A collection:

  1. **mark**  — trace every object reachable from the GC roots
                 (globals + the environments and operand stacks of all live
                 call frames);
  2. **sweep** — drop every tracked object that was *not* reached, releasing
                 the VM's reference so the host can reclaim it; if a swept
                 instance's class defines ``__finalize__`` it is run first.

This realises the design-document idea that the running manifold of objects
is discarded once nothing in the program refers to it any longer.

Collections are triggered explicitly via the ``gc()`` builtin, or
automatically when the number of allocations since the last collection
crosses a threshold (checked only at safe points between instructions).
"""

from .objects import (
    BadaInstance, BadaClass, BadaFunction, BoundMethod, TupleSpace, Namespace,
)


# Python types that participate in Bada garbage collection.
HEAP_TYPES = (BadaInstance, BadaClass, BadaFunction, BoundMethod,
              TupleSpace, list, dict)


class GarbageCollector:
    def __init__(self, vm):
        self.vm = vm
        self.heap = {}            # id(obj) -> obj   (the tracked object set)
        self.enabled = True
        self.threshold = 10000    # allocations between automatic collections
        self.allocs = 0           # allocations since last collection
        self.collections = 0      # number of collections run
        self.collected_total = 0  # objects reclaimed across all collections
        self._collecting = False

    # --- tracking ---------------------------------------------------------

    def track(self, obj):
        """Register a freshly allocated heap object."""
        if isinstance(obj, HEAP_TYPES):
            oid = id(obj)
            if oid not in self.heap:
                self.heap[oid] = obj
                self.allocs += 1
        return obj

    def maybe_collect(self):
        """Run an automatic collection if warranted (called at safe points)."""
        if (self.enabled and not self._collecting
                and self.allocs >= self.threshold):
            self.collect()

    # --- collection -------------------------------------------------------

    def collect(self):
        """Run a full mark-and-sweep; return the number of objects reclaimed."""
        if self._collecting:
            return 0
        self._collecting = True
        try:
            reachable = self._mark()
            reclaimed = self._sweep(reachable)
            self.collections += 1
            self.collected_total += reclaimed
            self.allocs = 0
            return reclaimed
        finally:
            self._collecting = False

    def _roots(self):
        roots = [self.vm.global_env]
        for frame in self.vm.frames:
            roots.append(frame.env)
            roots.extend(frame.stack)
            if frame.self_obj is not None:
                roots.append(frame.self_obj)
            if frame.defining_class is not None:
                roots.append(frame.defining_class)
        return roots

    def _mark(self):
        from .vm import Environment
        reachable = set()
        seen = set()
        stack = list(self._roots())
        while stack:
            obj = stack.pop()
            oid = id(obj)
            if oid in seen:
                continue
            seen.add(oid)
            if id(obj) in self.heap:
                reachable.add(oid)

            if isinstance(obj, Environment):
                env = obj
                while env is not None:
                    stack.extend(env.vars.values())
                    env = env.parent
            elif isinstance(obj, list):
                stack.extend(obj)
            elif isinstance(obj, dict):
                stack.extend(obj.keys())
                stack.extend(obj.values())
            elif isinstance(obj, BadaInstance):
                stack.extend(obj.fields.values())
                stack.append(obj.klass)
            elif isinstance(obj, BadaClass):
                stack.extend(obj.methods.values())
                stack.extend(obj.statics.values())
                if obj.parent is not None:
                    stack.append(obj.parent)
            elif isinstance(obj, BadaFunction):
                if obj.closure is not None:
                    stack.append(obj.closure)
            elif isinstance(obj, BoundMethod):
                stack.append(obj.func)
                stack.append(obj.receiver)
                if obj.defining_class is not None:
                    stack.append(obj.defining_class)
            elif isinstance(obj, TupleSpace):
                stack.extend(obj.values())
            elif isinstance(obj, Namespace):
                stack.extend(obj.members.values())
        return reachable

    def _sweep(self, reachable):
        dead = [oid for oid in self.heap if oid not in reachable]
        for oid in dead:
            obj = self.heap.pop(oid, None)
            if obj is None:
                continue
            if isinstance(obj, BadaInstance):
                self._finalize(obj)
        return len(dead)

    def _finalize(self, instance):
        method, owner = instance.klass.find_method("__finalize__")
        if method is None:
            return
        try:
            self.vm.invoke(method, [], self_obj=instance, defining_class=owner)
        except Exception:
            # finalizers must never abort collection
            pass

    # --- introspection ----------------------------------------------------

    def stats(self):
        return {
            "heap": len(self.heap),
            "enabled": self.enabled,
            "threshold": self.threshold,
            "allocs": self.allocs,
            "collections": self.collections,
            "collected_total": self.collected_total,
        }
