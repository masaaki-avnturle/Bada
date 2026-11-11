"""Error types for the Bada language toolchain."""


class BadaError(Exception):
    """Base class for all Bada errors."""

    def __init__(self, message, line=None, col=None):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(self.format())

    def format(self):
        where = ""
        if self.line is not None:
            where = f" (line {self.line}" + (f", col {self.col}" if self.col else "") + ")"
        return f"{self.kind}: {self.message}{where}"

    kind = "BadaError"


class BadaSyntaxError(BadaError):
    kind = "SyntaxError"


class BadaNameError(BadaError):
    kind = "NameError"


class BadaTypeError(BadaError):
    kind = "TypeError"


class BadaRuntimeError(BadaError):
    kind = "RuntimeError"


class BadaImmutableError(BadaError):
    """Raised when a write-once TupleSpace key is overwritten."""

    kind = "ImmutableError"


class BadaModuleError(BadaError):
    """Raised when an imported module cannot be found or loaded."""

    kind = "ModuleError"


class BadaThrow(Exception):
    """Carries a user-thrown Bada value through the Python call stack.

    This is distinct from BadaError: it represents an explicit `throw` of an
    arbitrary Bada value (number, string, map, instance, ...), not an internal
    interpreter error.
    """

    def __init__(self, value):
        self.value = value
        super().__init__("Bada exception")
