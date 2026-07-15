"""キー再割り当てエンジン / The remapping state machine.

入力イベント (物理キーの押下/解放) の列を受け取り、
設定に基づいて変換した出力イベントの列を生成する。

設計の中心は「論理修飾子の遅延アサート」:

  * 物理修飾キー (Control 等に割り当てられたキー) が押されると
    論理修飾子の集合 (active) が変化する。
  * 出力側では、``_out_mods`` が「OS に対して現在押下として送っている
    修飾キー」を表す。各イベント処理後、次の不変条件を保つ:

        _out_mods == active ∪ (保持中の出力キーが要求する修飾子)

  これにより、修飾キーのホールド・パススルー・和音のいずれも
  一貫した down/up ペアで表現できる。
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Config, FunctionAction, OutputAction
from .keys import KeyTable
from .keyseq import KeyStroke

# 論理修飾子 -> 出力で送出する正規の修飾キー
_MOD_OUTPUT_KEY = {
    "S": "LeftShift",
    "C": "LeftControl",
    "A": "LeftAlt",
    "W": "LeftWindows",
}


@dataclass(frozen=True)
class InputEvent:
    key: str
    pressed: bool


@dataclass(frozen=True)
class OutputEvent:
    key: str
    code: int
    pressed: bool

    def __str__(self) -> str:
        return f"{self.key}{'↓' if self.pressed else '↑'}"


@dataclass
class _Held:
    """保持中の出力キー 1 件。

    Attributes:
        stroke: 送出したストローク (None なら Ignore で無出力)。
        passthrough: 未マップの素通しなら True。
            素通しキーは物理修飾子をそのまま出力に載せるが、
            キーマップにマッチした再割り当ては修飾子を「消費」し、
            出力ストロークが持つ修飾子だけを載せる。
    """

    stroke: "KeyStroke | None"
    passthrough: bool = False


class Engine:
    def __init__(self, config: Config, keymap: str = "Global") -> None:
        self.config = config
        self.keys: KeyTable = config.keys
        self.active_keymap = keymap if keymap in config.keymaps else "Global"

        # 物理キーで現在押されている修飾キー -> それが表す論理修飾子
        self._key_to_mod = self._build_mod_lookup()
        self._held_mod_keys: set[str] = set()   # 押下中の物理修飾キー
        self._out_mods: set[str] = set()        # OS へ送出済みの論理修飾子
        # 保持中の再割り当てキー: 入力キー名 -> 保持レコード
        self._held_out: dict[str, _Held] = {}
        self.warnings: list[str] = []

    # -- 準備 ----------------------------------------------------------------
    def _build_mod_lookup(self) -> dict[str, str]:
        table: dict[str, str] = {}
        for mod, keyset in self.config.mod_assign.items():
            for k in keyset:
                try:
                    table[self.keys.canonical(k)] = mod
                except KeyError:
                    continue
        return table

    @property
    def _active(self) -> frozenset[str]:
        """現在アクティブな論理修飾子集合。"""
        return frozenset(self._key_to_mod[k] for k in self._held_mod_keys)

    # -- メイン処理 ----------------------------------------------------------
    def feed(self, ev: InputEvent) -> list[OutputEvent]:
        """入力イベントひとつを処理し、出力イベント列を返す。"""
        try:
            key = self.keys.canonical(ev.key)
        except KeyError:
            self.warnings.append(f"未知の入力キー: {ev.key}")
            return []

        if key in self._key_to_mod:
            return self._handle_modifier(key, ev.pressed)
        if ev.pressed:
            return self._handle_press(key)
        return self._handle_release(key)

    def feed_all(self, events: list[InputEvent]) -> list[OutputEvent]:
        out: list[OutputEvent] = []
        for ev in events:
            out.extend(self.feed(ev))
        return out

    # -- 修飾キー ------------------------------------------------------------
    def _handle_modifier(self, key: str, pressed: bool) -> list[OutputEvent]:
        if pressed:
            self._held_mod_keys.add(key)
        else:
            self._held_mod_keys.discard(key)
        return self._reconcile()

    # -- 通常キー押下 --------------------------------------------------------
    def _handle_press(self, key: str) -> list[OutputEvent]:
        active = self._active
        action = self._lookup(key, active, up=False)

        # 明示的な Ignore -> 何も出さず、解放時も無視するよう記録
        if isinstance(action, FunctionAction) and action.name.lower() in ("ignore", "undefined"):
            self._held_out[key] = _Held(stroke=None)
            return []

        # Default または未マップ -> パススルー (現在の修飾子付きで素通し)
        if action is None or (isinstance(action, FunctionAction) and action.name.lower() == "default"):
            return self._emit_hold(key, KeyStroke(key=key, mods=active), passthrough=True)

        if isinstance(action, FunctionAction):
            self.warnings.append(f"未対応の関数 &{action.name} は無視します")
            self._held_out[key] = _Held(stroke=None)
            return []

        assert isinstance(action, OutputAction)
        if len(action.strokes) == 1:
            return self._emit_hold(key, action.strokes[0], passthrough=False)
        # 複数ストローク -> シーケンスとしてタップ (押しっぱなし保持はしない)
        self._held_out[key] = _Held(stroke=None)
        return self._emit_sequence(action.strokes)

    # -- 通常キー解放 --------------------------------------------------------
    def _handle_release(self, key: str) -> list[OutputEvent]:
        out: list[OutputEvent] = []
        # ~ (up) パターンによる発火
        up_action = self._lookup(key, self._active, up=True)
        if isinstance(up_action, OutputAction):
            out.extend(self._emit_sequence(up_action.strokes))

        if key in self._held_out:
            held = self._held_out.pop(key)
            if held.stroke is not None:
                out.append(self._ev(held.stroke.key, pressed=False))
            out.extend(self._reconcile())
        return out

    # -- 出力補助 ------------------------------------------------------------
    def _emit_hold(self, input_key: str, stroke: KeyStroke, passthrough: bool) -> list[OutputEvent]:
        """単一ストロークを「押下」として送出し、保持を記録する。"""
        self._held_out[input_key] = _Held(stroke=stroke, passthrough=passthrough)
        out = self._reconcile()
        out.append(self._ev(stroke.key, pressed=True))
        return out

    def _emit_sequence(self, strokes: tuple[KeyStroke, ...]) -> list[OutputEvent]:
        """複数ストロークを down/up のタップ列として送出する。

        キーマップにマッチした出力なので物理修飾子は消費され、
        各ストロークが持つ修飾子のみを載せる。
        """
        out: list[OutputEvent] = []
        for st in strokes:
            out.extend(self._set_out_mods(set(st.mods)))
            out.append(self._ev(st.key, pressed=True))
            out.append(self._ev(st.key, pressed=False))
        out.extend(self._reconcile())
        return out

    def _reconcile(self) -> list[OutputEvent]:
        """不変条件を回復するよう修飾子の down/up を送出する。

        desired は保持中の各出力キーが要求する修飾子の和:
          * 素通しキー   -> 現在の物理修飾子 (active) を載せる
          * 再割り当てキー -> 出力ストロークの修飾子だけを載せる (物理側は消費)
        保持キーが無い (アイドル) ときは全解放。物理修飾子は
        素通しキーが実際に押されるまでアサートしない。
        """
        desired: set[str] = set()
        for held in self._held_out.values():
            if held.stroke is None:
                continue
            if held.passthrough:
                desired |= set(self._active)
            else:
                desired |= set(held.stroke.mods)
        return self._set_out_mods(desired)

    def _set_out_mods(self, desired: set[str] | frozenset[str]) -> list[OutputEvent]:
        desired = set(desired)
        out: list[OutputEvent] = []
        # 余分な修飾子を離す
        for m in list(self._out_mods - desired):
            out.append(self._ev(_MOD_OUTPUT_KEY[m], pressed=False))
            self._out_mods.discard(m)
        # 不足している修飾子を押す
        for m in sorted(desired - self._out_mods):
            out.append(self._ev(_MOD_OUTPUT_KEY[m], pressed=True))
            self._out_mods.add(m)
        return out

    def _ev(self, key: str, pressed: bool) -> OutputEvent:
        canon = self.keys.canonical(key)
        return OutputEvent(key=canon, code=self.keys.code(canon), pressed=pressed)

    # -- キーマップ探索 ------------------------------------------------------
    def _pat_matches(self, pattern: KeyStroke, key: str, active: frozenset[str]) -> bool:
        """パターンのキー名を正規化した上で入力と照合する。"""
        try:
            pk = self.keys.canonical(pattern.key)
        except KeyError:
            return False
        if pk != key:
            return False
        if pattern.dont_care:
            return pattern.mods <= active
        return pattern.mods == active

    def _lookup(self, key: str, active: frozenset[str], up: bool) -> object | None:
        for km in self.config.keymap_chain(self.active_keymap):
            for pattern, action in km.entries:
                if pattern.up != up:
                    continue
                if self._pat_matches(pattern, key, active):
                    return action
        # def subst をフォールバックとして参照
        for pattern, action in self.config.substitutions:
            if pattern.up != up:
                continue
            if self._pat_matches(pattern, key, active):
                return action
        return None

    # -- 状態 ----------------------------------------------------------------
    def flush(self) -> list[OutputEvent]:
        """全ての保持を解放する (終了時のクリーンアップ)。"""
        out: list[OutputEvent] = []
        for held in list(self._held_out.values()):
            if held.stroke is not None:
                out.append(self._ev(held.stroke.key, pressed=False))
        self._held_out.clear()
        out.extend(self._set_out_mods(set()))
        self._held_mod_keys.clear()
        return out
