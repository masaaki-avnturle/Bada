#!/usr/bin/env python3
"""Generate the bundled hologram HTML assets for the Android APK.

The hologram apps are self-contained HTML/canvas (the Bada-computed frames are
embedded as JSON), so they run offline in a WebView.  This script renders the
whole hologram family into ``app/src/main/assets/holograms/`` plus an
``index.html`` launcher menu.  It is run both locally and in CI before the
Gradle build, so the bundled assets always match the Bada sources.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # repo root
PKG = os.path.join(ROOT, "bada_webos")
for p in (PKG, ROOT, os.path.join(ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from hologram import (HologramApp, HoloKeyboardApp, MirrorApp, VisionApp,  # noqa
                      GlassApp, FreeformApp, QCacheApp, QEvolveApp)

OUT = os.path.join(HERE, "app", "src", "main", "assets", "holograms")


def main():
    os.makedirs(OUT, exist_ok=True)
    items = []   # (filename, title, subtitle)

    def emit(name, title, subtitle, fn):
        fn(os.path.join(OUT, name))
        items.append((name, title, subtitle))
        print(f"  {name}")

    print("rendering hologram assets ...")
    h = HologramApp(n=14, frames=16)
    h.boot()

    fw = FreeformApp()
    fw.boot()
    emit("freeform.html", "Freeform マルチウィンドウ",
         "Samsung-Freeform 風のマルチウィンドウ + タスクバー（Start／終了ボタン）",
         fw.save_html)

    g = GlassApp()
    g.boot()
    emit("hologlass.html", "Transparent + Japanese HHKB",
         "see-through display & HHKB over the camera — romaji→kana input",
         g.save_html)

    qc = QCacheApp()
    qc.boot()
    emit("qcache.html", "Quantum Cache Disk",
         "hard disk → quantum cache: Reviser, Grover prediction, Γ/Jones (Bada)",
         qc.save_html)

    qe = QEvolveApp()
    qe.boot()
    emit("qevolve.html", "Self-Evolving Quantum Algorithm",
         "a GA evolves a quantum algorithm and emits it as Bada source (Bada)",
         qe.save_html)

    v = VisionApp(n=14, frames=16)
    v.boot()
    emit("holovision.html", "Spatial Hologram",
         "Vision-Pro-equivalent passthrough — apps float out of the tablet",
         v.save_html)

    emit("hologram_pyramid.html", "Hologram Display",
         "equation-group videos on the four-mirror reflection pyramid",
         lambda p: h.save_html(p, False))
    emit("hologram_free.html", "Hologram — Free View",
         "the reconstructed floating image (imaginary/reality shimmer)",
         lambda p: h.save_html(p, True))
    emit("hologram_floatup.html", "Float-up Hologram",
         "video floats up out of the conductive-plastic tablet (Jones relief)",
         lambda p: h.save_floatup(p))

    kb = HoloKeyboardApp()
    kb.boot()
    emit("holokbd.html", "Holographic HHKB",
         "the Happy Hacking Keyboard floating as a hologram",
         kb.save_html)

    m = MirrorApp(n=14, frames=16)
    m.boot()
    emit("holomirror.html", "Mirror App — Display",
         "smartphone mirror over the tablet — aerial display in the gap",
         lambda p: m.save_html(p, False))
    emit("holomirror_keyboard.html", "Mirror App — HHKB",
         "the aerial HHKB realized at the eyeglass-lens focus",
         lambda p: m.save_html(p, True))

    _write_index(items)
    print(f"wrote {len(items)} apps + index.html to {OUT}")


def _write_index(items):
    cards = "\n".join(
        f'  <a class="card" href="{name}">'
        f'<div class="t">{title}</div>'
        f'<div class="s">{sub}</div></a>'
        for name, title, sub in items)
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bada Hologram</title>
<style>
 body{{margin:0;background:#02040a;color:#cfe;font-family:monospace;
   -webkit-text-size-adjust:100%}}
 header{{padding:18px 16px;background:#04070f;border-bottom:2px solid #1a8}}
 header b{{color:#3fd;font-size:18px;letter-spacing:1px}}
 header div{{color:#69a;font-size:12px;margin-top:4px}}
 .grid{{padding:12px;display:flex;flex-direction:column;gap:10px}}
 .card{{display:block;background:linear-gradient(180deg,#0d1830,#0a1322);
   border:1px solid #2a4a7a;border-radius:12px;padding:14px 16px;
   text-decoration:none;color:#cfe;box-shadow:0 0 16px #0c6a5533}}
 .card:active{{border-color:#3fd}}
 .card .t{{color:#7fe;font-size:16px}} .card .s{{color:#9ab;font-size:12px;
   margin-top:5px;line-height:1.4}}
 footer{{text-align:center;color:#567;font-size:11px;padding:14px}}
</style></head><body>
<header><b>&#x1F52E; Bada Hologram</b>
 <div>holographic display · keyboard · mirror · spatial — computed in Bada</div></header>
<div class="grid">
{cards}
</div>
<footer>tap an app · everything runs offline in the WebView</footer>
</body></html>"""
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
