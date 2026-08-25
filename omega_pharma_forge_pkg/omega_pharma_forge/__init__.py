"""Omega Pharma-Forge — 擬似量子VMで触媒投与を制御する自己触媒連鎖の反応速度論シミュレーション（教育用）."""
from .reaction_network import ReactionNetwork, RateConstants, State
from .synthesizer import QuantumSynthesizer, DosingConfig, Frame, run_uncontrolled

__version__ = "0.1.0"
__all__ = [
    "ReactionNetwork", "RateConstants", "State",
    "QuantumSynthesizer", "DosingConfig", "Frame", "run_uncontrolled",
]
