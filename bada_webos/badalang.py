"""Locate and re-export the Bada language toolchain.

The Bada compiler + VM live in the sibling ``bada_silent_vim/bada`` package.
BadaWebOS uses Bada as its application programming language, so every webos
module imports the language through here::

    from bada_webos.badalang import run_source, compile_source
"""

from __future__ import annotations

import os
import sys

# repo root = parent of bada_webos/
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BADA_HOME = os.path.join(_ROOT, "bada_silent_vim")
if _BADA_HOME not in sys.path:
    sys.path.insert(0, _BADA_HOME)

from bada import compile_source, disassemble, run_source, to_text  # noqa: E402

__all__ = ["run_source", "compile_source", "disassemble", "to_text"]
