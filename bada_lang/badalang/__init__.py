"""Bada — an object-oriented operator-algebra scripting language.

Public helpers:
    compile_source(src)  -> CodeObject
    run_source(src)      -> executes and returns the program result
"""

from .compiler import compile_source
from .vm import VM
from .errors import BadaError

__version__ = "1.0.0"


def run_source(source, filename="<bada>"):
    code = compile_source(source, filename)
    return VM().run_main(code)


__all__ = ["compile_source", "run_source", "VM", "BadaError", "__version__"]
