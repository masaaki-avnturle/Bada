"""Omega Critical-Guard — 擬似量子VMによる臨界連鎖防止シミュレーション（教育用）."""
from .chain_model import ChainCore, CoreConfig, LCG
from .guard import CriticalGuard, GuardConfig, GuardTelemetry

__version__ = "0.1.0"
__all__ = ["ChainCore", "CoreConfig", "LCG", "CriticalGuard", "GuardConfig", "GuardTelemetry"]
