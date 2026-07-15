"""シミュレータバックエンド (全OS共通)。

実キーボードを掴まずに、与えられた入力イベント列を変換して返す。
テスト・CI・他OSでのデモに用いる。

入力の書式 (文字列):
    "C-b C-f a"          修飾子付き打鍵をタップ (down,up) として展開
    "S-{Left Left} x"    { } でくくると押しっぱなし (down ... up)
    "@Emacs"             （将来拡張用）キーマップ切替の目印

タップ記法をそのまま InputEvent 列へ展開するユーティリティも提供する。
"""

from __future__ import annotations

from ..engine import Engine, InputEvent, OutputEvent
from ..keyseq import parse_keystroke
from .base import Backend


def expand_taps(spec: str) -> list[InputEvent]:
    """"C-b a" のような打鍵指定を InputEvent 列へ展開する。

    各トークンは修飾子付きストローク。修飾子は down/up でくくって送る。
    例: ``C-b`` -> LeftControl↓, b↓, b↑, LeftControl↑
    """
    events: list[InputEvent] = []
    for tok in spec.split():
        st = parse_keystroke(tok)
        mod_keys = _mods_to_keys(st.mods)
        for mk in mod_keys:
            events.append(InputEvent(mk, pressed=True))
        events.append(InputEvent(st.key, pressed=True))
        events.append(InputEvent(st.key, pressed=False))
        for mk in reversed(mod_keys):
            events.append(InputEvent(mk, pressed=False))
    return events


_MOD_TO_KEY = {"S": "LeftShift", "C": "LeftControl", "A": "LeftAlt", "W": "LeftWindows"}


def _mods_to_keys(mods: frozenset[str]) -> list[str]:
    return [_MOD_TO_KEY[m] for m in ("C", "A", "S", "W") if m in mods]


class SimulateBackend(Backend):
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)

    def translate(self, events: list[InputEvent]) -> list[OutputEvent]:
        out = self.engine.feed_all(events)
        out.extend(self.engine.flush())
        return out

    def translate_spec(self, spec: str) -> list[OutputEvent]:
        return self.translate(expand_taps(spec))

    def run(self) -> None:  # pragma: no cover - 対話ループは CLI 側で扱う
        raise RuntimeError("SimulateBackend.run は対話実行では使いません。"
                           "CLI の simulate サブコマンドを使ってください。")


def format_events(events: list[OutputEvent]) -> str:
    """出力イベント列を人間可読な 1 行文字列に整形する。"""
    return " ".join(str(e) for e in events)


def format_taps(events: list[OutputEvent]) -> str:
    """down/up ペアを ``C-b`` のような和音表記へ畳んで整形する。

    修飾キーの down/up に挟まれた通常キーのタップを見つけて和音化する。
    """
    parts: list[str] = []
    mods_down: list[str] = []
    inv = {v: k for k, v in _MOD_TO_KEY.items()}
    i = 0
    pending: str | None = None
    for e in events:
        if e.key in inv:
            if e.pressed:
                mods_down.append(inv[e.key])
            else:
                if inv[e.key] in mods_down:
                    mods_down.remove(inv[e.key])
            continue
        if e.pressed:
            pending = e.key
        else:
            prefix = "".join(m + "-" for m in ("C", "A", "S", "W") if m in mods_down)
            parts.append(prefix + (pending or e.key))
            pending = None
        i += 1
    if pending is not None:
        prefix = "".join(m + "-" for m in ("C", "A", "S", "W") if m in mods_down)
        parts.append(prefix + pending + "↓")
    return " ".join(parts)
