"""設定ファイルの構文解析 / Parser producing a :class:`Config`.

対応ディレクティブ:

    include "FILE"                 別ファイルを取り込む
    def key NAME = 0xNN            新しいキー名を定義
    def alias NAME = KEY           キーの別名を定義
    def subst PAT = OUT ...        全キーマップ共通の置換
    mod MODIFIER = KEY ...         修飾子に物理キーを割り当て (置換)
    mod MODIFIER += KEY ...        修飾子に物理キーを追加
    keymap NAME [ : PARENT ]       キーマップ定義の開始
    window NAME /regex/ : PARENT   ウィンドウ別キーマップ (タイトル正規表現)
      key PAT = OUT ...            打鍵の再割り当て (keymap 配下、字下げ)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from .keys import KeyTable
from .keyseq import KeyStroke, parse_keyseq, parse_keystroke
from .lexer import Line, is_string_token, string_value, tokenize

# 修飾子名 -> 論理修飾子記号
_MOD_NAMES = {
    "shift": "S",
    "control": "C",
    "ctrl": "C",
    "alt": "A",
    "meta": "A",
    "windows": "W",
    "win": "W",
}

# 標準の物理修飾キー (既定の割り当て)
_DEFAULT_MODS: dict[str, set[str]] = {
    "S": {"LeftShift", "RightShift"},
    "C": {"LeftControl", "RightControl"},
    "A": {"LeftAlt", "RightAlt"},
    "W": {"LeftWindows", "RightWindows"},
}


class ConfigError(Exception):
    """設定ファイルの構文・意味エラー。"""


# --- アクション表現 ---------------------------------------------------------
@dataclass(frozen=True)
class OutputAction:
    """出力キーシーケンスを送出するアクション。"""

    strokes: tuple[KeyStroke, ...]


@dataclass(frozen=True)
class FunctionAction:
    """``&Ignore`` / ``&Default`` などの組み込み関数。"""

    name: str
    args: tuple[str, ...] = ()


Action = "OutputAction | FunctionAction"


@dataclass
class Keymap:
    """ひとつのキーマップ。パターン -> アクションの並び。"""

    name: str
    parent: str | None = None
    window_regex: re.Pattern[str] | None = None
    entries: list[tuple[KeyStroke, object]] = field(default_factory=list)

    def add(self, pattern: KeyStroke, action: object) -> None:
        self.entries.append((pattern, action))


@dataclass
class Config:
    """解析済み設定一式。"""

    keys: KeyTable
    keymaps: dict[str, Keymap]
    mod_assign: dict[str, set[str]]
    substitutions: list[tuple[KeyStroke, object]]
    options: dict[str, str] = field(default_factory=dict)

    def keymap_chain(self, name: str) -> list[Keymap]:
        """指定キーマップから親をたどった探索順リストを返す。"""
        chain: list[Keymap] = []
        seen: set[str] = set()
        cur: str | None = name
        while cur and cur not in seen:
            km = self.keymaps.get(cur)
            if km is None:
                break
            chain.append(km)
            seen.add(cur)
            cur = km.parent
        return chain


# --- パーサ -----------------------------------------------------------------
class Parser:
    def __init__(self, search_paths: list[str] | None = None) -> None:
        self.keys = KeyTable()
        self.keymaps: dict[str, Keymap] = {}
        self.mod_assign: dict[str, set[str]] = {m: set(v) for m, v in _DEFAULT_MODS.items()}
        self.substitutions: list[tuple[KeyStroke, object]] = []
        self.options: dict[str, str] = {}
        self.search_paths = search_paths or []
        self._current: Keymap | None = None
        self._included: set[str] = set()

    # -- 公開 API ------------------------------------------------------------
    def parse_file(self, path: str) -> Config:
        self._include(path, base_dir=os.path.dirname(os.path.abspath(path)))
        return self._finish()

    def parse_string(self, source: str, base_dir: str = ".") -> Config:
        self._parse_lines(tokenize(source), base_dir)
        return self._finish()

    def _finish(self) -> Config:
        if "Global" not in self.keymaps:
            self.keymaps["Global"] = Keymap("Global")
        return Config(
            keys=self.keys,
            keymaps=self.keymaps,
            mod_assign=self.mod_assign,
            substitutions=self.substitutions,
            options=self.options,
        )

    # -- include -------------------------------------------------------------
    def _include(self, path: str, base_dir: str) -> None:
        resolved = self._resolve(path, base_dir)
        if resolved is None:
            raise ConfigError(f"include 先が見つかりません: {path!r}")
        real = os.path.abspath(resolved)
        if real in self._included:
            return  # 二重 include を防ぐ
        self._included.add(real)
        with open(real, encoding="utf-8") as f:
            source = f.read()
        self._parse_lines(tokenize(source), base_dir=os.path.dirname(real))

    def _resolve(self, path: str, base_dir: str) -> str | None:
        candidates = [os.path.join(base_dir, path), path]
        candidates += [os.path.join(p, path) for p in self.search_paths]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    # -- 行処理 --------------------------------------------------------------
    def _parse_lines(self, lines: list[Line], base_dir: str) -> None:
        for line in lines:
            try:
                self._parse_line(line, base_dir)
            except ConfigError as e:
                # 既に行番号が付いていれば (include 先など) そのまま送出
                if "行目" in str(e):
                    raise
                raise ConfigError(f"{line.number} 行目: {e}\n  > {line.raw.strip()}") from e
            except Exception as e:  # noqa: BLE001 - 位置情報を付けて再送出
                raise ConfigError(f"{line.number} 行目: {e}\n  > {line.raw.strip()}") from e

    def _parse_line(self, line: Line, base_dir: str) -> None:
        toks = line.tokens
        head = toks[0].lower()

        # keymap 配下の key 行 (字下げ) は現在のキーマップに属する
        if head == "key":
            self._parse_key(toks, into=self._current)
            return
        if head == "keymap" or head == "keymap2":
            self._parse_keymap(toks)
            return
        if head == "window":
            self._parse_window(toks)
            return
        if head == "mod":
            self._parse_mod(toks)
            return
        if head == "def":
            self._parse_def(toks, base_dir)
            return
        if head == "include":
            if len(toks) < 2 or not is_string_token(toks[1]):
                raise ConfigError('include には "ファイル名" が必要です')
            self._include(string_value(toks[1]), base_dir)
            return
        raise ConfigError(f"未知のディレクティブ: {toks[0]!r}")

    def _parse_keymap(self, toks: list[str]) -> None:
        if len(toks) < 2:
            raise ConfigError("keymap には名前が必要です")
        name = toks[1]
        parent = None
        if len(toks) >= 4 and toks[2] == ":":
            parent = toks[3]
        km = self.keymaps.get(name) or Keymap(name)
        if parent:
            km.parent = parent
        self.keymaps[name] = km
        self._current = km

    def _parse_window(self, toks: list[str]) -> None:
        # window NAME /regex/ [ : PARENT ]
        if len(toks) < 3:
            raise ConfigError("window には名前と正規表現が必要です")
        name = toks[1]
        rest = toks[2:]
        parent = None
        if len(rest) >= 2 and rest[-2] == ":":
            parent = rest[-1]
            rest = rest[:-2]
        pat = " ".join(rest)
        if pat.startswith("/") and pat.endswith("/") and len(pat) >= 2:
            pat = pat[1:-1]
        km = self.keymaps.get(name) or Keymap(name)
        km.parent = parent
        km.window_regex = re.compile(pat)
        self.keymaps[name] = km
        self._current = km

    def _parse_mod(self, toks: list[str]) -> None:
        # mod MODIFIER (= | +=) KEY ...
        if len(toks) < 3:
            raise ConfigError("mod の構文が不正です")
        mod_name = toks[1].lower()
        if mod_name not in _MOD_NAMES:
            raise ConfigError(f"未知の修飾子: {toks[1]!r}")
        mod = _MOD_NAMES[mod_name]
        op = toks[2]
        keys = [self.keys.canonical(t) for t in toks[3:]]
        target = self.mod_assign.setdefault(mod, set())
        if op == "=":
            target.clear()
            target.update(keys)
        elif op == "+=":
            target.update(keys)
        elif op == "-=":
            for k in keys:
                target.discard(k)
        else:
            raise ConfigError(f"mod には = / += / -= を使います (got {op!r})")

    def _parse_def(self, toks: list[str], base_dir: str) -> None:
        if len(toks) < 2:
            raise ConfigError("def の対象がありません")
        kind = toks[1].lower()
        if kind == "key":
            # def key NAME = 0xNN
            if len(toks) < 5 or toks[3] != "=":
                raise ConfigError("def key NAME = 0xNN の形が必要です")
            name = toks[2]
            code = int(toks[4], 0)
            self.keys.define(name, code)
        elif kind == "alias":
            if len(toks) < 5 or toks[3] != "=":
                raise ConfigError("def alias NAME = KEY の形が必要です")
            self.keys.define_alias(toks[2], toks[4])
        elif kind == "subst":
            # def subst PAT = OUT ...
            if "=" not in toks:
                raise ConfigError("def subst には = が必要です")
            eq = toks.index("=")
            pat = parse_keystroke(toks[2])
            action = self._parse_action(toks[eq + 1 :])
            self.substitutions.append((pat, action))
        elif kind == "option":
            # def option NAME = VALUE
            if len(toks) >= 5 and toks[3] == "=":
                self.options[toks[2]] = toks[4]
        else:
            raise ConfigError(f"未対応の def 種別: {toks[1]!r}")

    def _parse_key(self, toks: list[str], into: Keymap | None) -> None:
        if into is None:
            # keymap 宣言前の key はエラー (Global を暗黙生成)
            into = self.keymaps.setdefault("Global", Keymap("Global"))
            self._current = into
        if "=" not in toks:
            raise ConfigError("key には = が必要です")
        eq = toks.index("=")
        if eq != 2:
            raise ConfigError("key PATTERN = ... の形が必要です")
        pattern = parse_keystroke(toks[1])
        action = self._parse_action(toks[eq + 1 :])
        into.add(pattern, action)

    def _parse_action(self, toks: list[str]) -> object:
        if not toks:
            raise ConfigError("アクションが空です")
        if toks[0].startswith("&"):
            name = toks[0][1:]
            return FunctionAction(name=name, args=tuple(toks[1:]))
        return OutputAction(strokes=tuple(parse_keyseq(toks)))


def parse_file(path: str, search_paths: list[str] | None = None) -> Config:
    return Parser(search_paths=search_paths).parse_file(path)


def parse_string(source: str, search_paths: list[str] | None = None,
                 base_dir: str = ".") -> Config:
    return Parser(search_paths=search_paths).parse_string(source, base_dir=base_dir)
