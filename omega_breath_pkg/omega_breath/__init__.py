"""Omega Breath — 呼吸ガイドと心拍変動(RSA/圧受容器反射共鳴)の教育用シミュレータ."""
from .patterns import BreathPattern, PATTERNS, get
from .hrv import RSASimulator, HRVConfig, resonance_sweep
from .guide import run_guide, run_guide_safe, render_bar

__version__ = "0.1.0"
__all__ = ["BreathPattern", "PATTERNS", "get", "RSASimulator", "HRVConfig",
           "resonance_sweep", "run_guide", "run_guide_safe", "render_bar"]
