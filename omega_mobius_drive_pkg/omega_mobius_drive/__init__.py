"""Omega Möbius-Drive — 擬似量子VM × メビウス回路HDD × 反ダランベルシアン場の内部統制シミュレーション."""
from .mobius_disk import MobiusDisk, Sector
from .dalembert import DAlembertField, FieldConfig
from .pseudo_quantum import PseudoQuantumVM, QReg
from .controller import MobiusDriveSystem, Telemetry

__version__ = "0.1.0"
__all__ = [
    "MobiusDisk", "Sector", "DAlembertField", "FieldConfig",
    "PseudoQuantumVM", "QReg", "MobiusDriveSystem", "Telemetry",
]
