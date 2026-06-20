"""QuantumKernel — the BadaWebOS kernel on a quantum substrate.

Built on the previously-designed quantum computer OS: the kernel's critical
state lives in a logical qubit protected by the **Shor 9-qubit code**, so a
stray single-qubit error (a "cosmic ray") on the boot register is detected and
corrected at boot.  On top of that the kernel provides the OS object model the
brief asked for:

    function  -> object    : ``register_object`` records methods as object verbs
    hardware  -> software  : ``bind_driver`` virtualises a device as a soft driver
    Bada      = app language: ``run_app`` executes a ``.bada`` program on the VM
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)                       # bada_webos/
_ROOT = os.path.dirname(_PKG)                       # repo root
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from quantum.shor9 import Shor9                     # noqa: E402
from bada import run_source, load_program           # noqa: E402


@dataclass
class KernelObject:
    name: str
    schema: dict = field(default_factory=dict)
    methods: list = field(default_factory=list)


@dataclass
class SoftDriver:
    device: str
    node: str          # virtual device node, e.g. /dev/soft/<device>
    bound: bool = True


@dataclass
class Process:
    pid: int
    name: str
    output: list = field(default_factory=list)
    state: str = "ready"


class QuantumKernel:
    def __init__(self):
        self.objects: dict[str, KernelObject] = {}
        self.drivers: dict[str, SoftDriver] = {}
        self.processes: list[Process] = []
        self._pid = 1
        self.boot_log: list[str] = []
        self.qec_report: dict = {}

    # -- boot with Shor-9 protected kernel register ------------------------
    def boot(self, error_kind: str = "Y", error_qubit: int = 4) -> dict:
        """Protect the boot register with Shor's code; inject and correct a
        single-qubit error, proving the quantum substrate is fault-tolerant."""
        code = Shor9()
        # boot state |b> = 0.6|0> + 0.8|1>  (an arbitrary kernel qubit)
        alpha, beta = 0.6, 0.8
        code.encode(alpha, beta)
        fid_before_err = code.fidelity(alpha, beta)
        code.inject_error(error_kind, error_qubit)       # cosmic-ray hit
        fid_corrupt = code.fidelity(alpha, beta)
        syndrome = code.syndrome()
        recovery = code.correct()
        fid_after = code.fidelity(alpha, beta)
        self.qec_report = {
            "code": "Shor-9",
            "injected": f"{error_kind}@{error_qubit}",
            "syndrome": syndrome,
            "recovery": recovery,
            "fidelity_before_error": round(fid_before_err, 4),
            "fidelity_corrupted": round(fid_corrupt, 4),
            "fidelity_corrected": round(fid_after, 4),
            "ok": fid_after > 0.999,
        }
        self.boot_log.append(
            f"Shor-9 QEC: error {error_kind}@{error_qubit} -> "
            f"syndrome {syndrome} -> recovery {recovery} -> "
            f"fidelity {fid_after:.4f}")
        return self.qec_report

    # -- function -> object ------------------------------------------------
    def register_object(self, name: str, schema: dict | None = None,
                        methods: list | None = None) -> KernelObject:
        obj = KernelObject(name, schema or {}, methods or [])
        self.objects[name] = obj
        self.boot_log.append(f"object registered: {name} "
                             f"({len(obj.methods)} methods)")
        return obj

    # -- hardware -> software ---------------------------------------------
    def bind_driver(self, device: str) -> SoftDriver:
        drv = SoftDriver(device=device, node=f"/dev/soft/{device}")
        self.drivers[device] = drv
        self.boot_log.append(f"soft-driver bound: {device} -> {drv.node}")
        return drv

    # -- Bada = application language --------------------------------------
    def run_app(self, name: str, source: str) -> Process:
        proc = Process(pid=self._pid, name=name)
        self._pid += 1
        proc.state = "running"
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                run_source(source)
            proc.output = buf.getvalue().splitlines()
            proc.state = "exited"
        except Exception as exc:
            proc.output = [f"{type(exc).__name__}: {exc}"]
            proc.state = "crashed"
        self.processes.append(proc)
        return proc

    def run_app_file(self, name: str, path: str) -> Process:
        with open(path) as f:
            return self.run_app(name, f.read())

    def run_program_file(self, name: str, path: str) -> Process:
        """Run a Bada program with ``#include`` directives resolved (libraries)."""
        return self.run_app(name, load_program(path))
