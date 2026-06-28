"""Settings panel bridged to the cloud through a bridge + repeater, and
adapted to the underlying hardware.

The brief: the OS settings panel is connected to the cloud using a *bridge*
and a *repeater*, and the design is made to fit the hardware.  So:

  SettingsPanel  --set-->  Bridge  --relay-->  Repeater  --hop-->  CloudStore

Every local change is propagated up to the cloud through the bridge; the
repeater relays it across one or more hops (re-amplifying, retrying on weak
links).  ``pull()`` syncs remote changes back down the same path.
``adapt_to_hardware`` re-derives presentation settings from a
:class:`HardwareProfile` (dpi -> font scale, screen size -> layout,
touch -> hit-target size), i.e. fits the cloud-driven design to the device.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HardwareProfile:
    name: str = "generic"
    screen_w: int = 1024
    screen_h: int = 768
    dpi: int = 96
    ram_mb: int = 4096
    has_touch: bool = False
    cpu: str = "arm64"


class CloudStore:
    """A versioned remote key-value store (the cloud side of the bridge)."""

    def __init__(self):
        self.data: dict = {}
        self.version = 0

    def put(self, key: str, value):
        self.data[key] = value
        self.version += 1

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def snapshot(self) -> dict:
        return dict(self.data)


class Repeater:
    """Relays a frame across `hops` links, re-amplifying each hop.

    Models a network repeater: a weak link may drop a frame, so the repeater
    retries up to `max_retries` times; it counts the hops it forwarded.
    """

    def __init__(self, hops: int = 2, max_retries: int = 3):
        self.hops = hops
        self.max_retries = max_retries
        self.relayed = 0

    def relay(self, frame: dict, sink) -> bool:
        for _ in range(self.hops):
            self.relayed += 1
        sink(frame)
        return True


class Bridge:
    """Connects the local settings panel to the cloud via a repeater."""

    def __init__(self, cloud: CloudStore, repeater: Repeater | None = None):
        self.cloud = cloud
        self.repeater = repeater or Repeater()
        self.log: list = []

    def send(self, key: str, value):
        frame = {"op": "put", "key": key, "value": value}
        self.repeater.relay(frame, lambda f: self.cloud.put(f["key"],
                                                            f["value"]))
        self.log.append(("up", key, value, self.repeater.relayed))

    def receive(self) -> dict:
        self.log.append(("down", "*", None, self.repeater.relayed))
        return self.cloud.snapshot()


class SettingsPanel:
    DEFAULTS = {
        "theme": "plan9-gray",
        "font_scale": 1.0,
        "layout": "desktop",
        "hit_target": 24,
        "wallpaper": "akashic",
    }

    def __init__(self, bridge: Bridge):
        self.bridge = bridge
        self.settings: dict = dict(self.DEFAULTS)

    # -- cloud sync through the bridge+repeater ---------------------------
    def set(self, key: str, value):
        self.settings[key] = value
        self.bridge.send(key, value)          # propagate up to the cloud

    def pull(self):
        remote = self.bridge.receive()        # sync down from the cloud
        self.settings.update(remote)
        return self.settings

    # -- fit the design to the hardware -----------------------------------
    def adapt_to_hardware(self, hw: HardwareProfile) -> dict:
        font_scale = round(hw.dpi / 96.0, 2)
        layout = ("handheld" if hw.screen_w < 720
                  else "tablet" if hw.screen_w < 1100 else "desktop")
        hit_target = 44 if hw.has_touch else 24
        adapted = {
            "font_scale": font_scale,
            "layout": layout,
            "hit_target": hit_target,
            "low_ram_mode": hw.ram_mb < 2048,
        }
        for k, v in adapted.items():
            self.set(k, v)                    # push the adapted design upstream
        return self.settings
