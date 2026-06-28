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
_JPN = os.path.join(_PKG, "apps", "hologram", "lib", "romaji_kana.bada")
_FRF = os.path.join(_PKG, "apps", "hologram", "lib", "freeform.bada")
_QCA = os.path.join(_PKG, "apps", "hologram", "lib", "qcache.bada")
_QEV = os.path.join(_PKG, "apps", "hologram", "lib", "qevolve.bada")
_JCR = os.path.join(_PKG, "apps", "hologram", "lib", "jcrypto.bada")
_SRC = None
_KSRC = None
_MSRC = None
_SSRC = None
_JSRC = None
_FSRC = None
_QSRC = None
_QESRC = None
_JCSRC = None


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


# --- Japanese input for the HHKB (romaji -> kana) --------------------------
def _jrun(extra: str):
    global _JSRC
    if _JSRC is None:
        _JSRC = load_program(_JPN)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_JSRC + "\n" + extra)
    return buf.getvalue().splitlines()


def kana_table() -> dict:
    """The romaji -> hiragana table (authoritative, defined in Bada)."""
    out = {}
    for line in _jrun("kana_dump()"):
        if "\t" in line:
            k, v = line.split("\t", 1)
            out[k] = v
    return out


def romaji_to_kana(s: str) -> str:
    """Convert a romaji string to hiragana (computed in Bada)."""
    return _jrun(f'print romaji_to_kana("{s}")')[-1]


# --- Freeform multi-window manager -----------------------------------------
def _frun(extra: str):
    global _FSRC
    if _FSRC is None:
        _FSRC = load_program(_FRF)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_FSRC + "\n" + extra)
    return buf.getvalue().splitlines()


def wm_catalog() -> list:
    """The launchable apps as [{title, file, glyph}, ...] (from Bada)."""
    out = []
    for line in _frun("app_dump()"):
        parts = line.split("\t")
        if len(parts) == 3:
            out.append({"title": parts[0], "file": parts[1], "glyph": parts[2]})
    return out


def tb_height() -> int:
    return int(float(_frun("print tb_height()")[-1]))


def maximize_rect(sw: int, sh: int) -> list:
    return ast.literal_eval(_frun(f"print maximize_rect({sw}, {sh})")[-1])


def snap_rect(side: int, sw: int, sh: int) -> list:
    return ast.literal_eval(_frun(f"print snap_rect({side}, {sw}, {sh})")[-1])


def cascade(n: int, sw: int, sh: int) -> list:
    flat = ast.literal_eval(_frun(f"print cascade({n}, {sw}, {sh})")[-1])
    return [flat[i:i + 4] for i in range(0, len(flat), 4)]


def clamp_rect(x, y, w, h, sw, sh) -> list:
    return ast.literal_eval(
        _frun(f"print clamp_rect({x}, {y}, {w}, {h}, {sw}, {sh})")[-1])


def start_sections() -> list:
    """The Start-menu section titles (installed apps + Bada apps), from Bada."""
    return [s for s in _frun("section_dump()") if s.strip()]


def size_presets() -> list:
    """Launch-size presets as [{label, key}, ...] (携帯型 / 中 / 大), from Bada."""
    out = []
    for line in _frun("preset_dump()"):
        if "\t" in line:
            label, key = line.split("\t", 1)
            out.append({"label": label, "key": key})
    return out


def window_size(preset: str, sw: int, sh: int) -> list:
    return ast.literal_eval(_frun(f'print window_size("{preset}", {sw}, {sh})')[-1])


# --- Quantum Cache Disk ----------------------------------------------------
def _qrun(extra: str):
    global _QSRC
    if _QSRC is None:
        _QSRC = load_program(_QCA)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_QSRC + "\n" + extra)
    return buf.getvalue().splitlines()


def gamma_int(n: int) -> int:
    return int(float(_qrun(f"print gamma_int({n})")[-1]))


def gamma_ibp(z: int) -> int:
    """The integration-by-parts value z*Gamma(z) ( == Gamma(z+1) )."""
    return int(float(_qrun(f"print gamma_ibp({z})")[-1]))


def jones_thermal(beta: float) -> float:
    return float(_qrun(f"print jones_thermal({beta})")[-1])


def disk_state(patterns: list, nbits: int) -> list:
    """The disk's bit patterns as a normalized quantum state (amplitudes)."""
    arr = "[" + ", ".join(str(int(p)) for p in patterns) + "]"
    return ast.literal_eval(_qrun(f"print disk_state({arr}, {nbits})")[-1])


def revise_program(ops: list) -> list:
    """Rewrite von-Neumann cache ops to quantum gates: [(op, gate), ...]."""
    arr = "[" + ", ".join(f'"{o}"' for o in ops) + "]"
    out = []
    for line in _qrun(f"revise_dump({arr})"):
        if "\t" in line:
            a, b = line.split("\t", 1)
            out.append((a, b))
    return out


def predict_block(nq: int, l0: int, t: int) -> int:
    return int(float(_qrun(f"print predict_block({nq}, {l0}, {t})")[-1]))


def predict_curve(nq: int, l0: int, T: int) -> list:
    return ast.literal_eval(_qrun(f"print predict_curve({nq}, {l0}, {T})")[-1])


def predict_blocks(nq: int, l0: int, T: int) -> list:
    return [predict_block(nq, l0, t) for t in range(T)]


def _plain(x: float) -> str:
    # Bada's lexer has no exponent notation; render without 'e'
    s = f"{x:.60f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def uncertainty_bound(d_addr: float, hbar: float) -> float:
    return float(_qrun(
        f"print uncertainty_bound({_plain(d_addr)}, {_plain(hbar)})")[-1])


# --- Self-evolving quantum-algorithm source code (qevolve) ------------------
def _qe_src():
    global _QESRC
    if _QESRC is None:
        _QESRC = load_program(_QEV)
    return _QESRC


def _qerun(extra: str):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_qe_src() + "\n" + extra)
    return buf.getvalue()


GATE_NAMES = {0: "IDENTITY", 1: "ORACLE", 2: "DIFFUSE"}


def evolve_best(nq, marked, L, pop, gens, seed) -> list:
    return ast.literal_eval(_qerun(
        f"print evolve_best({nq}, {marked}, {L}, {pop}, {gens}, {seed})")
        .splitlines()[-1])


def evolve_curve(nq, marked, L, pop, gens, seed) -> list:
    return ast.literal_eval(_qerun(
        f"print evolve_curve({nq}, {marked}, {L}, {pop}, {gens}, {seed})")
        .splitlines()[-1])


def fitness(nq, marked, prog) -> float:
    arr = "[" + ", ".join(str(int(g)) for g in prog) + "]"
    return float(_qerun(f"print fitness({nq}, {marked}, {arr})").splitlines()[-1])


def emit_source(nq, marked, prog) -> str:
    """The evolved quantum algorithm written back out as Bada source code."""
    arr = "[" + ", ".join(str(int(g)) for g in prog) + "]"
    return _qerun(f"emit_source({nq}, {marked}, {arr})").rstrip("\n")


def verify_emitted(nq, marked, prog) -> float:
    """Run the *emitted* Bada source and return its evolved_fitness()."""
    src = emit_source(nq, marked, prog)
    out = _qerun(src + "\nprint evolved_fitness()")
    return float(out.splitlines()[-1])


# --- Quantum cryptography solved by the Jones polynomial (jcrypto) ----------
def _jc_src():
    global _JCSRC
    if _JCSRC is None:
        _JCSRC = load_program(_JCR)
    return _JCSRC


def _jcrun(extra: str):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_jc_src() + "\n" + extra)
    return buf.getvalue().splitlines()


def _braid(chi):
    return "[" + ", ".join(str(int(g)) for g in chi) + "]"


def _msg(m):
    return "[" + ", ".join(str(int(v)) for v in m) + "]"


def jones_pi(chi, n, x) -> float:
    return float(_jcrun(f"print jones_pi({_braid(chi)}, {n}, {x})")[-1])


def encrypt_msg(msg, chi, n, x) -> list:
    return ast.literal_eval(
        _jcrun(f"print encrypt_msg({_msg(msg)}, {_braid(chi)}, {n}, {x})")[-1])


def solve_msg(cph, chi, n, x) -> list:
    arr = "[" + ", ".join(repr(float(c)) for c in cph) + "]"
    return ast.literal_eval(
        _jcrun(f"print solve_msg({arr}, {_braid(chi)}, {n}, {x})")[-1])


def necessary_condition(chi_e, n_e, x_e, chi_d, n_d, x_d) -> bool:
    out = _jcrun(
        f"print necessary_condition({_braid(chi_e)}, {n_e}, {x_e}, "
        f"{_braid(chi_d)}, {n_d}, {x_d})")[-1]
    return int(float(out)) == 1


def pull_decrypt(msg, chi_e, n_e, x_e, chi_d, n_d, x_d) -> list:
    """Encrypt msg with key E, then PULL the plaintext from Omega::DATABASE
    using decrypt key D — non-empty only if the necessary condition holds."""
    prog = (_jc_src()
            + f"\nc <- encrypt_msg({_msg(msg)}, {_braid(chi_e)}, {n_e}, {x_e})\n"
            f"n <- pull_decrypt(c, {_braid(chi_e)}, {n_e}, {x_e}, "
            f"{_braid(chi_d)}, {n_d}, {x_d})\n")
    vm = run_source(prog)
    return list(vm.tuplespace.get("crypto", []))


# --- identity-bound decryption: the unlock is based on WHO pulls ------------
def person_id(name) -> int:
    """A stable integer identity for a person (name -> id)."""
    if isinstance(name, int):
        return name
    return sum(ord(c) for c in str(name))


def person_condition(chi, n, target, puller) -> bool:
    out = _jcrun(f"print person_condition({_braid(chi)}, {n}, "
                 f"{person_id(target)}, {person_id(puller)})")[-1]
    return int(float(out)) == 1


def pull_as(msg, chi, n, target, puller) -> list:
    """Encrypt to `target`, then PULL as `puller` — the plaintext comes out only
    when the puller IS the intended person (same identity-bound Jones key)."""
    prog = (_jc_src()
            + f"\nc <- encrypt_msg_to({_msg(msg)}, {_braid(chi)}, {n}, "
            f"{person_id(target)})\n"
            f"n <- pull_as(c, {_braid(chi)}, {n}, "
            f"{person_id(target)}, {person_id(puller)})\n")
    vm = run_source(prog)
    return list(vm.tuplespace.get("crypto", []))
