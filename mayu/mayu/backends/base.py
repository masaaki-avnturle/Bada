"""バックエンド共通インターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..engine import Engine


class Backend(ABC):
    """入力を受け取りエンジンに流し、出力を実行する土台。"""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @abstractmethod
    def run(self) -> None:
        """イベントループを開始する (バックエンド依存)。"""
        raise NotImplementedError
