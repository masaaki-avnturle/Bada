"""BadaWebOS — a Web OS whose application language is Bada.

Boot sequence wires every subsystem together:

  1. QuantumKernel boots on the quantum substrate; the boot register is
     protected by the **Shor 9-qubit code** (inject + correct a cosmic-ray
     error).
  2. **w9wm** starts the desktop (8 virtual screens, title-barred windows).
  3. A **Rails** scaffold is transpiled into an OS app (design→design,
     function→object, view→window, hardware→software) and opened as windows.
  4. The **settings panel** adapts to the hardware and syncs to the cloud
     through a **bridge + repeater**.
  5. The **ultranetwork** boots as a Bada application (TupleSpace + arrow
     eval, neural XOR, gravity ports, bridge/repeater propagation).
  6. An **Android 12** app is installed and launched onto a second screen.
  7. The desktop is rendered to an HTML page.
"""

from __future__ import annotations

import os
import sys
from html import escape

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (_HERE, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from kernel.kernel import QuantumKernel                       # noqa: E402
from wm.w9wm import W9wm                                       # noqa: E402
from railsbridge.rails_to_os import (RailsField, RailsResource,  # noqa: E402
                                     RailsToOS)
from cloud.settings_bridge import (Bridge, CloudStore,         # noqa: E402
                                   HardwareProfile, Repeater,
                                   SettingsPanel)
from ultranet import UltraNetwork                              # noqa: E402
from android.installer import Android12Installer, AndroidManifest  # noqa
from terminal import Terminal                                  # noqa: E402
from qcrypto import QuantumCryptoApp                            # noqa: E402
from render.desktop import render_desktop                      # noqa: E402

_APP_DIR = os.path.join(_HERE, "apps")


class BadaWebOS:
    def __init__(self, hardware: HardwareProfile | None = None):
        self.hw = hardware or HardwareProfile(
            name="bada-tablet", screen_w=1024, screen_h=600, dpi=120,
            ram_mb=4096, has_touch=True, cpu="arm64")
        self.kernel = QuantumKernel()
        self.wm = W9wm(width=1024, height=600)
        self.installer = Android12Installer()
        self.window_content: dict[int, str] = {}
        self.report: dict = {}
        # subsystems kept for rendering / inspection
        self.cloud = CloudStore()
        self.bridge = Bridge(self.cloud, Repeater(hops=2))
        self.panel = SettingsPanel(self.bridge)
        self.ultranet = UltraNetwork()
        self.terminal = Terminal()
        self.qcrypto = QuantumCryptoApp()

    # ----------------------------------------------------------------
    def boot(self) -> dict:
        # 1. quantum kernel + Shor-9 QEC
        qec = self.kernel.boot(error_kind="Y", error_qubit=4)

        # 2/3. Rails -> OS app, opened as windows on w9wm (screen 1)
        res = RailsResource("article", [
            RailsField("title", "string"),
            RailsField("body", "text"),
            RailsField("published", "boolean")])
        osapp = RailsToOS().transpile(res)
        self.kernel.register_object("article", osapp.object_schema,
                                    osapp.methods)
        self.kernel.bind_driver("article")           # hardware -> software
        w_idx = self.wm.new_window("Articles — index", 24, 36, 372, 220)
        self.window_content[w_idx.wid] = osapp.windows["index"]
        w_new = self.wm.new_window("Articles — new", 410, 36, 320, 220)
        self.window_content[w_new.wid] = osapp.windows["new"]

        # 5. ultranetwork as a Bada app (run through the kernel too)
        un_report = self.ultranet.boot()
        self.kernel.run_app_file(
            "ultranetwork", os.path.join(_APP_DIR, "ultranetwork.bada"))
        w_un = self.wm.new_window("ultranetwork", 24, 280, 470, 250)
        self.window_content[w_un.wid] = self.ultranet.render_html()

        # 4. settings panel adapted to hardware + cloud bridge/repeater sync
        self.panel.adapt_to_hardware(self.hw)
        w_set = self.wm.new_window("Settings (cloud-bridged)", 512, 280,
                                   470, 250)
        self.window_content[w_set.wid] = self._settings_html()

        # 5b. Terminal bundling bash + vim + emacs (all over one VFS)
        self._terminal_demo()
        w_term = self.wm.new_window("Terminal — bash·vim·emacs", 250, 150,
                                    540, 320)
        self.window_content[w_term.wid] = self.terminal.render_html()

        # 5c. Quantum crypto: cryptanalyse a signature -> activate Jones crypto
        qc_report = self.qcrypto.boot()
        self.kernel.run_app_file(
            "quantum_crypto", os.path.join(_APP_DIR, "quantum_crypto.bada"))
        w_qc = self.wm.new_window("Quantum Crypto (Jones)", 70, 70, 470, 250)
        self.window_content[w_qc.wid] = self.qcrypto.render_html()

        # 6. Android 12 app installed + launched onto screen 2
        manifest = AndroidManifest(
            package="com.bada.notes", label="Bada Notes",
            target_sdk=31,
            permissions=["android.permission.INTERNET",
                         "android.permission.CAMERA",
                         "android.permission.BLUETOOTH_CONNECT"])
        self.installer.install(manifest)
        launched = self.installer.launch("com.bada.notes")
        self.wm.switch_screen(1)
        w_app = self.wm.new_window(f"Android: {launched}", 120, 70, 380, 280)
        self.window_content[w_app.wid] = self._android_html(manifest)
        self.wm.switch_screen(0)                      # return to main desktop

        self.report = {
            "qec": qec,
            "objects": list(self.kernel.objects),
            "drivers": list(self.kernel.drivers),
            "processes": [(p.name, p.state, p.output)
                          for p in self.kernel.processes],
            "rails_app": osapp.name,
            "ultranetwork": un_report,
            "quantum_crypto": {
                "activated": qc_report["activation"]["activated"],
                "jones": qc_report["activation"].get("jones"),
                "broken_key": qc_report["activation"].get("broken_key"),
            },
            "settings": dict(self.panel.settings),
            "cloud_version": self.cloud.version,
            "android": [a.package for a in self.installer.list_apps()],
            "terminal": {
                "apps": sorted(self.terminal.shell.BUILTINS),
                "editors": [f"{k}:{s.filename}" for k, s
                            in self.terminal.editors],
                "files": sorted(self.terminal.vfs.files),
            },
            "screens": self.wm.screens,
            "windows": [(w.name, w.screen) for w in self.wm.windows],
        }
        return self.report

    # ----------------------------------------------------------------
    def render(self) -> str:
        return render_desktop(self.wm, self.window_content,
                              self.kernel.qec_report, self.panel.settings,
                              self.hw.name)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.render())
        return path

    # -- terminal demo: bash + vim + emacs, one VFS -----------------------
    def _terminal_demo(self):
        t = self.terminal
        t.run_script([
            "pwd",
            'echo say \\"hello from the terminal\\" > hello.bada',
            "cat hello.bada",
        ])
        # edit the Bada file in vim (append a line), then run it
        t.open_vim("hello.bada", ["o", "print 6 * 7", "ESC", ":wq"])
        t.run_script(["bada hello.bada"])
        # jot a note in emacs
        t.open_emacs("notes.txt",
                     ["bash, vim and emacs share one VFS", "C-x C-s",
                      "C-x C-c"])
        t.run_script(["ls", "wc hello.bada"])

    # -- window body builders ---------------------------------------------
    def _settings_html(self) -> str:
        rows = "".join(
            f"<dt>{escape(k)}</dt><dd>{escape(str(v))}</dd>"
            for k, v in self.panel.settings.items())
        return (
            f'<dl class="os-detail">{rows}</dl>'
            f'<p>cloud v{self.cloud.version} via bridge+repeater '
            f'(relayed {self.bridge.repeater.relayed} hops)</p>')

    def _android_html(self, manifest: AndroidManifest) -> str:
        perms = "".join(f"<li>{escape(p)}</li>" for p in manifest.permissions)
        steps = "".join(f"<li>{escape(s)}</li>"
                        for s in self.installer.log[-6:])
        return (
            f'<h2>{escape(manifest.label)}</h2>'
            f'<p>pkg {escape(manifest.package)} · targetSdk '
            f'{manifest.target_sdk} (Android 12)</p>'
            f'<p>permissions:</p><ul>{perms}</ul>'
            f'<p>install log:</p><ul>{steps}</ul>')


def boot_and_render(html_path: str | None = None) -> tuple:
    os_ = BadaWebOS()
    report = os_.boot()
    if html_path:
        os_.save_html(html_path)
    return os_, report


if __name__ == "__main__":
    out = os.path.join(_HERE, "generated", "desktop.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    os_, report = boot_and_render(out)
    print("BadaWebOS booted.")
    print(f"  Shor-9 QEC: {report['qec']['injected']} -> "
          f"{report['qec']['recovery']} -> fidelity "
          f"{report['qec']['fidelity_corrected']} "
          f"({'OK' if report['qec']['ok'] else 'FAIL'})")
    print(f"  objects: {report['objects']}  drivers: {report['drivers']}")
    print(f"  windows: {[w for w, _ in report['windows']]}")
    print(f"  ultranetwork XOR acc: "
          f"{report['ultranetwork']['xor']['accuracy']}")
    print(f"  android installed: {report['android']}")
    print(f"  terminal apps: bash builtins + "
          f"{report['terminal']['editors']}")
    print(f"  quantum crypto: activated={report['quantum_crypto']['activated']}"
          f" Jones {report['quantum_crypto']['jones']}")
    print(f"  desktop written to {out}")
