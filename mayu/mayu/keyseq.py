"""キーストローク / キーシーケンスの表現と解析。

窓使いの憂鬱 の記法:

    C-b        Control + b
    S-A-x      Shift + Alt + x
    *C-A       Control + a、ただし他の修飾は問わない (``*`` = don't care)
    ~S-Space   Shift + Space が「離された」瞬間 (``~`` = key up)

修飾子の頭文字:
    S=Shift  C=Control  A=Alt  M=Meta(=Alt)  W=Windows
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 論理修飾子 (順序は表示用に固定)
MODIFIERS = ("C", "A", "S", "W")

_PREFIX_MAP = {
    "S": "S",  # Shift
    "C": "C",  # Control
    "A": "A",  # Alt
    "M": "A",  # Meta -> Alt 扱い
    "W": "W",  # Windows
}


@dataclass(frozen=True)
class KeyStroke:
    """1 打鍵ぶんのパターン / 出力。

    Attributes:
        key: 正規化前のキー名 (解決は KeyTable が行う)。
        mods: 必須の押下修飾子集合。
        dont_care: ``*`` 指定。True なら mods 以外の修飾子は照合で無視。
        up: ``~`` 指定。True なら「キーが離された」イベントで発火/送出。
    """

    key: str
    mods: frozenset[str] = field(default_factory=frozenset)
    dont_care: bool = False
    up: bool = False

    def __str__(self) -> str:
        pre = ""
        if self.dont_care:
            pre += "*"
        if self.up:
            pre += "~"
        for m in MODIFIERS:
            if m in self.mods:
                pre += m + "-"
        return pre + self.key

    def matches(self, key: str, active: frozenset[str]) -> bool:
        """入力イベント (key, 現在の押下修飾子集合) に一致するか。"""
        if key != self.key:
            return False
        if self.dont_care:
            return self.mods <= active
        return self.mods == active


def parse_keystroke(token: str) -> KeyStroke:
    """``C-b`` 等のトークンひとつを KeyStroke に変換する。"""
    dont_care = False
    up = False
    s = token
    # 先頭の * ~ を任意個・任意順で受け付ける
    while s and s[0] in "*~":
        if s[0] == "*":
            dont_care = True
        else:
            up = True
        s = s[1:]

    mods: set[str] = set()
    # `X-` の形が続く限り修飾子として剥がす
    while len(s) >= 2 and s[1] == "-" and s[0] in _PREFIX_MAP:
        mods.add(_PREFIX_MAP[s[0]])
        s = s[2:]

    if not s:
        raise ValueError(f"キー本体が空です: {token!r}")
    return KeyStroke(key=s, mods=frozenset(mods), dont_care=dont_care, up=up)


def parse_keyseq(tokens: list[str]) -> list[KeyStroke]:
    """トークン列を KeyStroke の並び (シーケンス) に変換する。"""
    return [parse_keystroke(t) for t in tokens]
