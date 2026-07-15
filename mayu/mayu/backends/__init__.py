"""入出力バックエンド / Input-output backends.

* :class:`~mayu.backends.simulate.SimulateBackend` — 全OS共通。
  入力イベント列を与えて変換結果を得る、検証・デモ用のドライラン。
* :class:`~mayu.backends.linux_evdev.EvdevBackend` — Linux 専用。
  evdev で実キーを掴み、uinput 仮想デバイスへ再送出する。
"""

from .base import Backend

__all__ = ["Backend"]
