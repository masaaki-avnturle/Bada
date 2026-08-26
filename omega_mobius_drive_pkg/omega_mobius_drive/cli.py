"""cli.py — `python -m omega_mobius_drive.cli [cycles]`"""
from __future__ import annotations
import sys
from .controller import MobiusDriveSystem


def main() -> int:
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    system = MobiusDriveSystem(sectors=64, seed=seed)
    system.run(cycles=cycles)
    print(system.report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
