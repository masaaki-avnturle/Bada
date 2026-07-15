"""Linux 実キーフックバックエンド (evdev / uinput)。

物理キーボードデバイスを ``grab`` して OS への直接入力を止め、
変換結果を uinput 仮想キーボードから送出する。

必要: ``python-evdev`` パッケージと /dev/uinput への書込権限
(通常は root もしくは input グループ + udev ルール)。

本家 窓使いの憂鬱 が Windows のキーボードフィルタドライバで行うことを、
Linux では evdev のデバイス grab で実現している。
"""

from __future__ import annotations

import sys

from ..engine import Engine, InputEvent
from .base import Backend


class EvdevBackend(Backend):
    def __init__(self, engine: Engine, device_path: str | None = None,
                 grab: bool = True) -> None:
        super().__init__(engine)
        self.device_path = device_path
        self.grab = grab
        self._evdev = None
        self._ui = None
        self._dev = None

    # -- 準備 ----------------------------------------------------------------
    def _import_evdev(self):
        try:
            import evdev  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "python-evdev が必要です。`pip install evdev` を実行してください。\n"
                "(この機能は Linux 専用です)"
            ) from e
        return evdev

    def _pick_device(self, evdev):
        if self.device_path:
            return evdev.InputDevice(self.device_path)
        # キーボードらしきデバイスを自動選択 (EV_KEY を持ち、英字キーを備える)
        from evdev import ecodes  # type: ignore
        for path in evdev.list_devices():
            dev = evdev.InputDevice(path)
            caps = dev.capabilities()
            keys = caps.get(ecodes.EV_KEY, [])
            if ecodes.KEY_A in keys and ecodes.KEY_Z in keys:
                return dev
            dev.close()
        raise RuntimeError("キーボードデバイスが見つかりません。--device で指定してください。")

    @staticmethod
    def list_devices() -> list[tuple[str, str]]:
        """(パス, 名前) の一覧を返す (CLI の list-devices 用)。"""
        try:
            import evdev  # type: ignore
        except ImportError as e:
            raise RuntimeError("python-evdev が必要です。`pip install evdev`") from e
        out = []
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                out.append((path, dev.name))
                dev.close()
            except Exception:  # noqa: BLE001
                continue
        return out

    # -- 実行 ----------------------------------------------------------------
    def run(self) -> None:  # pragma: no cover - 実デバイス依存
        evdev = self._import_evdev()
        from evdev import UInput, categorize, ecodes  # type: ignore

        self._dev = self._pick_device(evdev)
        self._ui = UInput.from_device(self._dev, name="mayu-virtual-keyboard")

        if self.grab:
            self._dev.grab()
        sys.stderr.write(f"[mayu] フック開始: {self._dev.name} ({self._dev.path})\n")
        sys.stderr.write("[mayu] 停止するには Ctrl-C。\n")
        try:
            for event in self._dev.read_loop():
                if event.type != ecodes.EV_KEY:
                    continue
                # value: 0=up, 1=down, 2=repeat
                name = self.engine.keys.name(event.code)
                if event.value == 2:
                    # リピートはそのまま通す (保持中キーのコードを再送)
                    self._ui.write(ecodes.EV_KEY, event.code, 2)
                    self._ui.syn()
                    continue
                pressed = event.value == 1
                outs = self.engine.feed(InputEvent(name, pressed=pressed))
                for o in outs:
                    self._ui.write(ecodes.EV_KEY, o.code, 1 if o.pressed else 0)
                self._ui.syn()
        except KeyboardInterrupt:
            pass
        finally:
            for o in self.engine.flush():
                self._ui.write(ecodes.EV_KEY, o.code, 1 if o.pressed else 0)
            self._ui.syn()
            if self.grab:
                try:
                    self._dev.ungrab()
                except Exception:  # noqa: BLE001
                    pass
            self._ui.close()
            self._dev.close()
            sys.stderr.write("\n[mayu] フック終了。\n")
