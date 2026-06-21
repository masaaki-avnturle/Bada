"""C backend: Bada reserved words / method commands as C executables."""

from .gen import generate, build, command_manifest

__all__ = ["generate", "build", "command_manifest"]
