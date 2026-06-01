#!/usr/bin/env python3
"""Build a distributable ZIP package of the Bada application suite.

Runs every GUI application to generate its self-contained .html, builds an
index.html launcher, and zips the apps together with the standalone
executables and the full source.

    python3 tools/build_zip.py     ->  dist/bada_suite.zip
"""

import os
import sys
import shutil
import subprocess
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # bada_lang/
DIST = os.path.join(ROOT, "dist")
BADA = os.path.join(ROOT, "bada.py")

# (app source, output .html, human title) - only HTML-producing GUI apps
APPS = [
    ("bada_os.bada", "bada_os.html", "Bada OS (w9wm / WindowMaker / Windows 11)"),
    ("mayu.bada", "mayu.html", "窓使いの憂鬱 mayu (registry key remapper)"),
    ("quantum_bada.bada", "quantum_bada.html", "Quantum_Bada (integrated medical)"),
    ("quantum_os.bada", "quantum_os.html", "Bada Quantum OS"),
    ("bada_forge.bada", "bada_forge.html", "Bada Forge (source auto-fix)"),
    ("project_forge.bada", "project_forge.html", "Project Forge (project completer)"),
    ("silent_talk.bada", "silent_talk.html", "Silent Talk (subvocal BCI)"),
    ("bada_brain.bada", "bada_brain.html", "Bada Brain (neuro suite)"),
    ("yamaguchi_health_app.bada", "yamaguchi_health.html", "YamaguchiHealth"),
    ("control_hub.bada", "control_hub.html", "Medical Control Hub"),
    ("diagnostic_console.bada", "diagnostic_console.html", "Diagnostic Console"),
    ("volume_viewer.bada", "volume_viewer.html", "3-D Volume Viewer"),
    ("psychotropic_gui.bada", "psychotropic_gui.html", "Psychotropic Sound"),
    ("medical_workstation.bada", "medical_workstation.html", "Medical Workstation"),
]


def run_app(stage, src, timeout=240):
    try:
        r = subprocess.run([sys.executable, BADA, "run", os.path.join(ROOT, "apps", src)],
                           cwd=stage, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def index_html(produced):
    cards = "".join(
        '<a class="tile" href="apps/{html}"><div class="t">{title}</div>'
        '<div class="b">{html}</div></a>'.format(html=h, title=t)
        for (h, t) in produced)
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Bada Application Suite</title><style>'
            "*{box-sizing:border-box;font-family:system-ui,sans-serif}"
            "body{margin:0;background:radial-gradient(120% 120% at 30% 20%,#2a6cf0,#10204a 60%,#0a0e1e);"
            "color:#e8eef7;padding:32px;min-height:100vh}"
            "h1{margin:0 0 4px}h2{color:#9fb6d6;font-weight:500;margin:0 0 24px;font-size:15px}"
            ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}"
            "a.tile{display:block;background:rgba(20,27,39,.85);border:1px solid #1f2a3a;border-radius:14px;"
            "padding:18px;text-decoration:none;color:#e8eef7;transition:.15s}"
            "a.tile:hover{border-color:#4a80d0;transform:translateY(-2px)}"
            "a.tile .t{font-weight:800;font-size:16px;margin-bottom:6px}a.tile .b{font-size:12px;color:#8aa0bd}"
            ".foot{margin-top:24px;color:#8aa0bd;font-size:13px}</style></head><body>"
            "<h1>&#129516; Bada Application Suite</h1>"
            "<h2>" + str(len(produced)) + " applications - written in the Bada language. Click to open.</h2>"
            '<div class="grid">' + cards + "</div>"
            '<div class="foot">bin/bada - run any app from one executable &middot; '
            'src/ - full source &middot; built by tools/build_zip.py</div>'
            "</body></html>")


def main():
    stage = tempfile.mkdtemp(prefix="bada_suite_")
    appdir = os.path.join(stage, "apps")
    os.makedirs(appdir)

    produced = []
    print("generating application HTML ...")
    for src, html, title in APPS:
        ok = run_app(stage, src)
        out = os.path.join(stage, html)
        if ok and os.path.isfile(out):
            shutil.move(out, os.path.join(appdir, html))
            produced.append((html, title))
            print("  [ok]   " + html)
        else:
            print("  [skip] " + src + " (no html / timed out)")

    # index launcher
    with open(os.path.join(stage, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html(produced))

    # remove loose media that some apps wrote into the stage root
    for nm in list(os.listdir(stage)):
        if nm.split(".")[-1] in ("pgm", "ppm", "gif", "wav", "reg", "badac"):
            os.remove(os.path.join(stage, nm))

    # executables
    bindir = os.path.join(stage, "bin")
    os.makedirs(bindir)
    for b in ("bada", "bada.pyz", "mayu", "mayu.pyz"):
        p = os.path.join(DIST, b)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(bindir, b))

    # source
    srcdir = os.path.join(stage, "src")
    os.makedirs(srcdir)
    for d in ("badalang", "lib", "apps", "tests"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(srcdir, d),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for fn in ("README.md", "GRAMMAR.md", "bada.py", "bada"):
        p = os.path.join(ROOT, fn)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(srcdir, fn))

    with open(os.path.join(stage, "README.txt"), "w", encoding="utf-8") as f:
        f.write("Bada Application Suite\n"
                "======================\n\n"
                "Open index.html in a browser to launch any application.\n\n"
                "bin/bada       run any app from one executable (needs Python 3):\n"
                "                 ./bin/bada list\n"
                "                 ./bin/bada run quantum_os\n"
                "                 ./bin/bada mayu\n"
                "bin/mayu       the mayu registry remapper, standalone.\n"
                "src/           full Bada source (VM, libraries, apps, tests).\n\n"
                "Built with the Bada language - a custom compiler + VM.\n")

    # zip it
    os.makedirs(DIST, exist_ok=True)
    out_zip = os.path.join(DIST, "bada_suite.zip")
    if os.path.exists(out_zip):
        os.remove(out_zip)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, _dirs, files in os.walk(stage):
            for nm in files:
                full = os.path.join(dirpath, nm)
                rel = os.path.join("bada_suite", os.path.relpath(full, stage))
                z.write(full, rel)

    shutil.rmtree(stage)
    print("\nbuilt: dist/bada_suite.zip  (%d apps, %d bytes)"
          % (len(produced), os.path.getsize(out_zip)))


if __name__ == "__main__":
    main()
