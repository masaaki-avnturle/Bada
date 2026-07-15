"""キー定義テーブル / Key definition table.

窓使いの憂鬱 (mayu) の内部では、各物理キーを「名前」で扱う。
ここでは名前 (mayu 互換のキー名) と Linux evdev の keycode を対応づける。
evdev コードを正典 (canonical) の数値表現として用いることで、
Linux バックエンドでは実キーフックが可能になり、他OSでも
シミュレータとして同じテーブルを共有できる。
"""

from __future__ import annotations

# --- 基本キー名 -> evdev keycode -------------------------------------------
# 参照: linux/input-event-codes.h の KEY_* 値
_BASE: dict[str, int] = {
    # 英字
    "A": 30, "B": 48, "C": 46, "D": 32, "E": 18, "F": 33, "G": 34,
    "H": 35, "I": 23, "J": 36, "K": 37, "L": 38, "M": 50, "N": 49,
    "O": 24, "P": 25, "Q": 16, "R": 19, "S": 31, "T": 20, "U": 22,
    "V": 47, "W": 17, "X": 45, "Y": 21, "Z": 44,
    # 数字段 (メイン)
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6,
    "6": 7, "7": 8, "8": 9, "9": 10, "0": 11,
    # 記号
    "Minus": 12, "Equal": 13, "BackSlash": 43, "BackSpace": 14,
    "Tab": 15, "LeftSquareBracket": 26, "RightSquareBracket": 27,
    "Enter": 28, "Semicolon": 39, "Quote": 40, "BackQuote": 41,
    "Comma": 51, "Period": 52, "Slash": 53, "Space": 57,
    # 制御・修飾
    "Escape": 1, "LeftControl": 29, "LeftShift": 42, "RightShift": 54,
    "LeftAlt": 56, "CapsLock": 58, "RightControl": 97, "RightAlt": 100,
    "LeftWindows": 125, "RightWindows": 126, "Applications": 127,
    # ファンクション
    "F1": 59, "F2": 60, "F3": 61, "F4": 62, "F5": 63, "F6": 64,
    "F7": 65, "F8": 66, "F9": 67, "F10": 68, "F11": 87, "F12": 88,
    # 編集・移動
    "NumLock": 69, "ScrollLock": 70, "Home": 102, "Up": 103,
    "PageUp": 104, "Left": 105, "Right": 106, "End": 107, "Down": 108,
    "PageDown": 109, "Insert": 110, "Delete": 111,
    # テンキー
    "NumMultiply": 55, "NumSubtract": 74, "NumAdd": 78, "NumEnter": 96,
    "NumDivide": 98, "NumDecimal": 83, "NumLock0": 82, "NumLock1": 79,
    "NumLock2": 80, "NumLock3": 81, "NumLock4": 75, "NumLock5": 76,
    "NumLock6": 77, "NumLock7": 71, "NumLock8": 72, "NumLock9": 73,
    # 日本語キーボード
    "Hankaku": 41, "Zenkaku": 85, "Hiragana": 93, "Katakana": 90,
    "Henkan": 92, "Muhenkan": 94, "Yen": 124, "KeypadJPComma": 95,
}

# --- 別名 (mayu では短縮名が慣習的に使われる) -------------------------------
_ALIASES: dict[str, str] = {
    "Esc": "Escape",
    "Ctrl": "LeftControl",
    "Control": "LeftControl",
    "LCtrl": "LeftControl",
    "RCtrl": "RightControl",
    "Shift": "LeftShift",
    "LShift": "LeftShift",
    "RShift": "RightShift",
    "Alt": "LeftAlt",
    "LAlt": "LeftAlt",
    "RAlt": "RightAlt",
    "Win": "LeftWindows",
    "LWin": "LeftWindows",
    "RWin": "RightWindows",
    "Windows": "LeftWindows",
    "Menu": "Applications",
    "App": "Applications",
    "Ret": "Enter",
    "Return": "Enter",
    "Del": "Delete",
    "Ins": "Insert",
    "PgUp": "PageUp",
    "PgDn": "PageDown",
    "Caps": "CapsLock",
    "Bs": "BackSpace",
    "Sp": "Space",
}


class KeyTable:
    """名前 <-> keycode の相互変換を提供する。

    ``def key`` ディレクティブで実行時に新しいキーを追加できるよう、
    インスタンスとして保持する。
    """

    def __init__(self) -> None:
        self._name_to_code: dict[str, int] = dict(_BASE)
        self._aliases: dict[str, str] = dict(_ALIASES)
        self._code_to_name: dict[int, str] = {}
        self._rebuild_reverse()

    def _rebuild_reverse(self) -> None:
        self._code_to_name = {}
        for name, code in self._name_to_code.items():
            # 最初に登録された正規名を優先する
            self._code_to_name.setdefault(code, name)

    # -- 検索系 --------------------------------------------------------------
    def canonical(self, name: str) -> str:
        """別名を正規名へ解決する (大小文字は区別しない)。"""
        key = self._match_ci(name)
        if key is None:
            raise KeyError(f"未知のキー名: {name!r}")
        return key

    def _match_ci(self, name: str) -> str | None:
        if name in self._name_to_code:
            return name
        if name in self._aliases:
            return self._aliases[name]
        low = name.lower()
        for n in self._name_to_code:
            if n.lower() == low:
                return n
        for a, target in self._aliases.items():
            if a.lower() == low:
                return target
        return None

    def code(self, name: str) -> int:
        return self._name_to_code[self.canonical(name)]

    def name(self, code: int) -> str:
        return self._code_to_name.get(code, f"0x{code:x}")

    def has(self, name: str) -> bool:
        return self._match_ci(name) is not None

    # -- 定義追加 (def key) --------------------------------------------------
    def define(self, name: str, code: int) -> None:
        self._name_to_code[name] = code
        self._code_to_name.setdefault(code, name)

    def define_alias(self, alias: str, target: str) -> None:
        target_canon = self.canonical(target)
        self._aliases[alias] = target_canon

    def all_names(self) -> list[str]:
        return sorted(self._name_to_code)
