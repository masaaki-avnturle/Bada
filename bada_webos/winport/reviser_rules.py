"""Reviser rule-sets for porting Windows.

A generic word-boundary rewriter (the same idea as the Bada reviser, but
rule-driven) used to rewrite Windows feature specs:

  * Win10 -> Win11  (renamed shell/APIs)
  * Windows -> quantum computer (CPU -> QPU, bit -> qubit, ...)

It is text-preserving: only whole-word tokens in the rule map are replaced.
"""

from __future__ import annotations

import re

WIN10_TO_WIN11 = {
    "Windows10": "Windows11",
    "ControlPanel": "Settings",
    "StartMenu": "StartMenuCentered",
    "Cortana": "Copilot",
    "TilesUI": "WidgetsUI",
    "DirectX11": "DirectX12",
    "Win32": "WinRT",
    "TPM1": "TPM2",
    "Edge18": "EdgeChromium",
}

WIN_TO_QUANTUM = {
    "CPU": "QPU",
    "thread": "qubit",
    "register": "qregister",
    "cache": "entangled_cache",
    "RAM": "QRAM",
    "bit": "qubit",
    "logic": "quantum_gate",
    "scheduler": "amplitude_scheduler",
    "process": "superposed_process",
}


def rewrite_words(text: str, rules: dict) -> str:
    if not rules:
        return text
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(k) for k in
                          sorted(rules, key=len, reverse=True)) + r")\b")
    return pattern.sub(lambda m: rules[m.group(0)], text)


def count_changes(text: str, rules: dict) -> int:
    n = 0
    for k in rules:
        n += len(re.findall(r"\b" + re.escape(k) + r"\b", text))
    return n


class WindowsReviser:
    """Reviser that ports Windows feature specs across versions and targets."""

    def to_win11(self, spec: str) -> str:
        return rewrite_words(spec, WIN10_TO_WIN11)

    def to_quantum(self, spec: str) -> str:
        return rewrite_words(spec, WIN_TO_QUANTUM)

    def changes_win11(self, spec: str) -> int:
        return count_changes(spec, WIN10_TO_WIN11)

    def changes_quantum(self, spec: str) -> int:
        return count_changes(spec, WIN_TO_QUANTUM)
