"""窓使いの憂鬱 (mayu) — クロスプラットフォームのキー再割り当てエンジン。

本家 窓使いの憂鬱 の ``.mayu`` 設定構文を解析し、キーの再割り当てを行う。
Linux では evdev/uinput で実キーをフックし、他OSでは
シミュレータとして同一の変換ロジックを実行できる。
"""

from .config import Config, parse_file, parse_string
from .engine import Engine, InputEvent, OutputEvent
from .keys import KeyTable

__version__ = "0.1.0"
__all__ = [
    "Config",
    "Engine",
    "InputEvent",
    "OutputEvent",
    "KeyTable",
    "parse_file",
    "parse_string",
    "__version__",
]
