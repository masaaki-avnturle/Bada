"""Omega-Gamma Agent — ガンマ関数 大域的部分積分多様体を核にしたローカル・エージェント."""
from .gamma_manifold import (
    GammaManifold,
    ManifoldState,
    gamma,
    log_gamma,
    digamma,
    ibp_recurrence,
    self_check,
)
from .agent import OmegaGammaAgent, Knowledge, DEFAULT_KB

__version__ = "0.1.0"
__all__ = [
    "GammaManifold", "ManifoldState", "gamma", "log_gamma", "digamma",
    "ibp_recurrence", "self_check", "OmegaGammaAgent", "Knowledge", "DEFAULT_KB",
]
