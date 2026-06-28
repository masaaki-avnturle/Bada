"""Bridge to the AL Bada libraries.

Each function loads the relevant Bada library (``apps/al/lib/*.bada``) and runs
it on the Bada VM, so the AL subsystems — Grover search, Lambda Driver cooling,
neural consciousness, the a-priori code engine, robot FPGA control — are all
computed by Bada code and reachable from Python (terminal command + tests).
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)                       # bada_webos/
_ROOT = os.path.dirname(_PKG)                       # repo root
for p in (_ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bada import load_program, run_source           # noqa: E402

_LIB = os.path.join(_PKG, "apps", "al", "lib")
APP = os.path.join(_PKG, "apps", "al", "al_laevatein.bada")
PILOT_APP = os.path.join(_PKG, "apps", "al", "al_pilot.bada")


def _run(libfile: str, extra: str) -> list[str]:
    src = load_program(os.path.join(_LIB, libfile)) + "\n" + extra
    buf = io.StringIO()
    with redirect_stdout(buf):
        vm = run_source(src)
    return vm.output


def _arr(literal: list) -> str:
    return "[" + ", ".join(str(x) for x in literal) + "]"


def _parse_list(s: str) -> list:
    inner = s.strip().lstrip("[").rstrip("]")
    out = []
    for tok in inner.split(","):
        tok = tok.strip()
        if not tok:
            continue
        out.append(float(tok) if "." in tok else int(tok))
    return out


# -- quantum algorithm -------------------------------------------------------
def grover(nq: int, marked: int) -> int:
    return int(_run("qsim.bada", f"print grover({nq}, {marked})")[-1])


# -- Lambda Driver cooling ---------------------------------------------------
def cooling_sim(steps: int, q_in: float, supercool: float) -> list:
    out = _run("cooling.bada",
               f"print cooling_sim({steps}, {q_in}, {supercool})")
    return _parse_list(out[-1])


# -- self-evolving neural consciousness --------------------------------------
def consciousness(k: int, gens: int, seed: int) -> int:
    return int(_run("neuro.bada",
                    f"print evolve_consciousness({k}, {gens}, {seed})")[-1])


# -- robot neural FPGA -------------------------------------------------------
def robot_fpga(sensors: list[int]) -> list:
    return _parse_list(
        _run("fpga.bada", f"print robot_fpga({_arr(sensors)})")[-1])


# -- unknown a-priori engine -------------------------------------------------
def apriori(seed: int, lines: int) -> str:
    out = _run("apriori.bada",
               f"say apriori_generate([{seed}], {lines})")
    return "\n".join(out)


# -- pilot brainwave -> Lambda Driver ---------------------------------------
def gamma_power(gamma_amp: float) -> float:
    out = _run("eeg.bada",
               f"st <- [1]\n"
               f"print gamma_power(gen_eeg({gamma_amp}, 48, 96, st), 96)")
    return float(out[-1])


def topo_peak(channel_gammas: list[float]) -> int:
    out = _run("fmri_topo.bada",
               f"st <- [1]\n"
               f"print peak_region(topo_map({_arr(channel_gammas)}, 96, st))")
    return int(out[-1])


def biofeedback(gamma0: float, target: float) -> list:
    """returns [resonance, haloperidol_level, effective_gamma]"""
    return _parse_list(
        _run("biofeedback.bada",
             f"print biofeedback({gamma0}, {target}, 40)")[-1])


def lambda_driver(eff_gamma: float, resonance: float,
                  supercool: float) -> list:
    """returns [at_field, anti_gravity]"""
    return _parse_list(
        _run("lambda_drive.bada",
             f"print lambda_driver({eff_gamma}, {resonance}, "
             f"{supercool})")[-1])
