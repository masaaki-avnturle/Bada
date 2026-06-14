"""Render the BadaWebOS desktop as a single HTML page.

This is the "HTML template features → operating-system frame" deliverable: the
w9wm window manager (8 virtual screens, title-barred windows) drawn as a
Plan 9 / rio-styled desktop, with each window's body filled by its app
template (Rails-generated views, the settings panel, the ultranetwork report,
the installed Android app).  A status strip shows the Shor-9 QEC kernel state.
"""

from __future__ import annotations

from html import escape

CSS = """
* { box-sizing: border-box; }
body { margin:0; font-family: 'Lucida Console','DejaVu Sans Mono',monospace;
       background:#2b2b2b; color:#e8e8e8; }
.topbar { background:#1d1f21; color:#c8a44a; padding:6px 12px;
          border-bottom:2px solid #c8a44a; display:flex; gap:18px;
          font-size:13px; align-items:center; }
.topbar b { color:#fff; }
.qec.ok { color:#7ec699; } .qec.bad { color:#e06c75; }
.w9wm-root { position:relative; height:560px; margin:0;
             background:#5a6b7b
             repeating-linear-gradient(45deg,#536473 0 12px,#5a6b7b 12px 24px); }
.w9wm-screens { position:absolute; right:8px; top:8px; z-index:50;
                display:flex; gap:3px; }
.w9wm-screens .scr { background:#1d1f21; color:#9aa; padding:2px 7px;
                     border:1px solid #000; font-size:12px; }
.w9wm-screens .scr.cur { background:#c8a44a; color:#000; font-weight:bold; }
.win { position:absolute; background:#d9d9d9; color:#111;
       border:4px solid #1d1f21; box-shadow:3px 3px 0 #0007; overflow:hidden; }
.win.focused { border-color:#c8a44a; }
.titlebar { background:#1d1f21; color:#eee; font-size:12px;
            padding:2px 8px; line-height:14px; }
.win.focused .titlebar { background:#c8a44a; color:#000; }
.client { padding:8px; font-size:12px; height:100%; overflow:auto; }
.os-table { border-collapse:collapse; width:100%; }
.os-table th,.os-table td { border:1px solid #888; padding:2px 6px;
                            font-size:11px; }
.os-btn { display:inline-block; margin-top:6px; background:#1d1f21;
          color:#c8a44a; padding:3px 8px; text-decoration:none; }
.os-form label { display:block; margin:4px 0; font-size:11px; }
h2 { font-size:14px; margin:0 0 6px; }
.taskbar { background:#1d1f21; border-top:2px solid #c8a44a; padding:4px 12px;
           font-size:12px; color:#9aa; }
"""


def _window_box(win, content: str, focused: bool) -> str:
    cls = "win focused" if focused else "win"
    style = (f"left:{win.x}px;top:{win.y}px;"
             f"width:{win.w}px;height:{win.h}px")
    return (f'<div class="{cls}" style="{style}">'
            f'<div class="titlebar">{escape(win.name)}</div>'
            f'<div class="client">{content}</div></div>')


def render_desktop(wm, window_content: dict, qec: dict,
                   settings: dict, hardware: str = "generic") -> str:
    qcls = "qec ok" if qec.get("ok") else "qec bad"
    qtxt = (f'Shor-9 QEC: {qec.get("injected")} → recovery '
            f'{qec.get("recovery")} → fidelity '
            f'{qec.get("fidelity_corrected")}')
    top = (
        '<div class="topbar">'
        '<b>BadaWebOS</b>'
        '<span>wm: w9wm</span>'
        f'<span class="{qcls}">{escape(qtxt)}</span>'
        f'<span>hw: {escape(hardware)}</span>'
        f'<span>theme: {escape(str(settings.get("theme")))} '
        f'· layout: {escape(str(settings.get("layout")))}</span>'
        '</div>')

    wins = wm.windows_on(wm.current)
    body = ['<div class="w9wm-root">']
    body.append('<div class="w9wm-screens">')
    for i in range(wm.screens):
        c = "scr cur" if i == wm.current else "scr"
        body.append(f'<span class="{c}">{i + 1}</span>')
    body.append('</div>')
    for win in wins:
        content = window_content.get(win.wid, f"{escape(win.name)} client")
        body.append(_window_box(win, content, win.wid == wm.focused))
    body.append('</div>')

    tasks = "  ·  ".join(escape(w.name) for w in wins) or "no windows"
    taskbar = f'<div class="taskbar">screen {wm.current + 1}/{wm.screens} ' \
              f'│ {tasks}</div>'

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>BadaWebOS desktop</title>"
        f"<style>{CSS}</style></head><body>"
        f"{top}{''.join(body)}{taskbar}"
        "</body></html>")
