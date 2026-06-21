"""Bridge to the hologram light-field library written in Bada
(apps/hologram/lib/hologram.bada).

Returns, to Python, the complex hologram light field (reality / imaginary
surfaces and magnitude) and the four-mirror reflection geometry from the
"Hologram Display" report.
"""

from __future__ import annotations

import ast
import io
import os
import sys
from contextlib import redirect_stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bada import load_program, run_source           # noqa: E402

_LIB = os.path.join(_PKG, "apps", "hologram", "lib", "hologram.bada")
_KBD = os.path.join(_PKG, "apps", "hologram", "lib", "keyboard.bada")
_MIR = os.path.join(_PKG, "apps", "hologram", "lib", "mirror.bada")
_SPA = os.path.join(_PKG, "apps", "hologram", "lib", "spatial.bada")
_SRC = None
_KSRC = None
_MSRC = None
_SSRC = None


def _run(extra: str):
    global _SRC
    if _SRC is None:
        _SRC = load_program(_LIB)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_SRC + "\n" + extra)
    return buf.getvalue().splitlines()


def _krun(extra: str):
    global _KSRC
    if _KSRC is None:
        _KSRC = load_program(_KBD)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_KSRC + "\n" + extra)
    return buf.getvalue().splitlines()


def _mrun(extra: str):
    global _MSRC
    if _MSRC is None:
        _MSRC = load_program(_MIR)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_MSRC + "\n" + extra)
    return buf.getvalue().splitlines()


def _srun(extra: str):
    global _SSRC
    if _SSRC is None:
        _SSRC = load_program(_SPA)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_SSRC + "\n" + extra)
    return buf.getvalue().splitlines()


def quad_names() -> list:
    # Bada prints string arrays unquoted: "[before, after, left, right]"
    s = _run("print quad_names()")[-1].strip().lstrip("[").rstrip("]")
    return [x.strip() for x in s.split(",") if x.strip()]


def quad_rot(name: str) -> int:
    return int(float(_run(f'print quad_rot("{name}")')[-1]))


def light_grid(kind: str, n: int, t: float) -> list:
    """One n x n grid of the light field ('re' | 'im' | 'mag') at time t."""
    flat = ast.literal_eval(_run(f'print light_flat("{kind}", {n}, {t})')[-1])
    return [flat[r * n:(r + 1) * n] for r in range(n)]


def light_frames(kind: str, n: int = 16, T: int = 16) -> list:
    """T animation frames of the light field, each an n x n grid (in Bada)."""
    return [light_grid(kind, n, k / T) for k in range(T)]


def metric_ds2(v: float, c: float) -> float:
    return float(_run(f"print metric_ds2({v}, {c})")[-1])


def hologram_mass(p: float, c: float, V: float, S: float) -> float:
    return float(_run(f"print hologram_mass({p}, {c}, {V}, {S})")[-1])


# --- Jones-polynomial relief (the light "mounds up") -----------------------
def jones_polynomial() -> list:
    """Trefoil Jones polynomial V(t) as [[exp, coeff], ...] (computed in Bada)."""
    return ast.literal_eval(_run("print jones_trefoil()")[-1])


def relief_grid(n: int, ph: float) -> list:
    flat = ast.literal_eval(_run(f"print relief_flat({n}, {ph})")[-1])
    return [flat[r * n:(r + 1) * n] for r in range(n)]


def relief_frames(n: int = 16, T: int = 16) -> list:
    """T frames of the Jones relief height field, each an n x n grid (in Bada)."""
    return [relief_grid(n, k / T) for k in range(T)]


# --- conductive-plastic tablet power model ---------------------------------
def tablet_power(bright: float, elev: float, npix: int) -> float:
    return float(_run(f"print tablet_power({bright}, {elev}, {npix})")[-1])


def power_scale(power: float, budget: float) -> float:
    return float(_run(f"print power_scale({power}, {budget})")[-1])


def battery_minutes(power: float, wh: float) -> float:
    return float(_run(f"print battery_minutes({power}, {wh})")[-1])


# --- HHKB keyboard layout --------------------------------------------------
def hhkb_keys() -> list:
    """The HHKB layout as [[x, y, w, code], ...] (computed in Bada)."""
    return ast.literal_eval(_krun("print hhkb_keys()")[-1])


def hhkb_width() -> int:
    return int(float(_krun("print hhkb_width()")[-1]))


def hhkb_rows() -> int:
    return int(float(_krun("print hhkb_rows()")[-1]))


# --- smartphone-mirror + eyeglass-lens aerial image ------------------------
def lens_image(do: float, f: float) -> float:
    return float(_mrun(f"print lens_image({do}, {f})")[-1])


def lorentz(v: float, c: float) -> float:
    return float(_mrun(f"print lorentz({v}, {c})")[-1])


def focal_jones(d: float, v: float, c: float, ph: float) -> float:
    return float(_mrun(f"print focal_jones({d}, {v}, {c}, {ph})")[-1])


def focus_z(d: float, v: float, c: float, ph: float) -> float:
    """Height (cm) of the aerial focus in the tablet↔mirror gap [0, d]."""
    return float(_mrun(f"print focus_z({d}, {v}, {c}, {ph})")[-1])


def focus_mag(d: float, v: float, c: float, ph: float) -> float:
    return float(_mrun(f"print focus_mag({d}, {v}, {c}, {ph})")[-1])


def focus_frames(d: float, v: float, c: float, T: int) -> list:
    return ast.literal_eval(_mrun(f"print focus_flat({d}, {v}, {c}, {T})")[-1])


# --- Vision-Pro-equivalent spatial layer -----------------------------------
def window_positions(n: int, radius: float, spread: float) -> list:
    """n app windows on a concave shell facing the viewer: [[x, y, z], ...]."""
    flat = ast.literal_eval(_srun(f"print window_flat({n}, {radius}, {spread})")[-1])
    return [flat[i:i + 3] for i in range(0, len(flat), 3)]


def parallax(z: float, head: float, refz: float) -> float:
    return float(_srun(f"print parallax({z}, {head}, {refz})")[-1])


def depth_scale(z: float, near: float, far: float) -> float:
    return float(_srun(f"print depth_scale({z}, {near}, {far})")[-1])


def passthrough_alpha(launch: float) -> float:
    """Tablet transparency as the display boots (1=opaque, 0.15=see-through)."""
    return float(_srun(f"print passthrough_alpha({launch})")[-1])
