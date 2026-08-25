"""Omega MorphoField — 形態形成場(反応拡散)＋外部場ドリフトと、腫瘍停滞の個体群動態."""
from .morphogen import MorphogenField, FieldConfig
from .tumor_dynamics import (
    TumorModel, TumorConfig, TumorFrame,
    policy_none, policy_continuous, make_adaptive_policy,
    compare_policies, format_comparison,
)

__version__ = "0.1.0"
__all__ = [
    "MorphogenField", "FieldConfig",
    "TumorModel", "TumorConfig", "TumorFrame",
    "policy_none", "policy_continuous", "make_adaptive_policy",
    "compare_policies", "format_comparison",
]
