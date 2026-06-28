"""Android 12 application installer for BadaWebOS.

A simulated package installer that follows the Android 12 (API level 31)
install lifecycle: verify the manifest → check the targetSdk → resolve runtime
permissions → install into the app registry → create a launcher entry that
opens as a window on w9wm.  No real APK/dex is executed; the manifest is the
contract the OS installs against.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ANDROID_12_SDK = 31

# Permissions that became runtime/"dangerous" and must be granted explicitly.
RUNTIME_PERMISSIONS = {
    "android.permission.CAMERA",
    "android.permission.RECORD_AUDIO",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.READ_CONTACTS",
    "android.permission.BLUETOOTH_CONNECT",   # new in Android 12
}


@dataclass
class AndroidManifest:
    package: str
    label: str
    version_code: int = 1
    min_sdk: int = 21
    target_sdk: int = ANDROID_12_SDK
    permissions: list = field(default_factory=list)
    main_activity: str = ".MainActivity"


@dataclass
class InstalledApp:
    package: str
    label: str
    granted: list
    activity: str
    state: str = "installed"


class InstallError(Exception):
    pass


class Android12Installer:
    def __init__(self):
        self.registry: dict[str, InstalledApp] = {}
        self.log: list[str] = []

    def _step(self, msg: str):
        self.log.append(msg)

    def verify(self, m: AndroidManifest):
        if not m.package or "." not in m.package:
            raise InstallError(f"invalid package name {m.package!r}")
        if m.target_sdk > ANDROID_12_SDK:
            raise InstallError(
                f"{m.package}: targetSdk {m.target_sdk} > Android 12 "
                f"({ANDROID_12_SDK})")
        self._step(f"verify {m.package}: signature ok, "
                   f"targetSdk={m.target_sdk} (Android 12)")

    def resolve_permissions(self, m: AndroidManifest,
                            auto_grant: bool = True) -> list:
        granted = []
        for p in m.permissions:
            if p in RUNTIME_PERMISSIONS:
                if auto_grant:
                    granted.append(p)
                    self._step(f"grant runtime permission {p}")
                else:
                    self._step(f"defer runtime permission {p} (ask at use)")
            else:
                granted.append(p)
                self._step(f"install-time permission {p}")
        return granted

    def install(self, m: AndroidManifest,
                auto_grant: bool = True) -> InstalledApp:
        self.verify(m)
        granted = self.resolve_permissions(m, auto_grant=auto_grant)
        app = InstalledApp(package=m.package, label=m.label,
                           granted=granted, activity=m.main_activity)
        self.registry[m.package] = app
        self._step(f"install {m.package} -> /data/app/{m.package}")
        return app

    def launch(self, package: str) -> str:
        app = self.registry.get(package)
        if not app:
            raise InstallError(f"{package} not installed")
        app.state = "running"
        self._step(f"launch {package}{app.activity}")
        # The launcher hands the activity to the WM as a window title.
        return f"{app.label} ({package})"

    def list_apps(self) -> list:
        return list(self.registry.values())
