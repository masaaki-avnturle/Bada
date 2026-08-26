"""Omega Critical-Guard — 擬似量子VMによる臨界連鎖防止と、臨界接近時の強度（教育用）."""
from .chain_model import ChainCore, CoreConfig, LCG
from .guard import CriticalGuard, GuardConfig, GuardTelemetry
from .subcritical import (
    multiplication, inverse_multiplication, steady_population, relaxation_time,
    approach_series, Measurement, ApproachConfig, ApproachToCritical,
    run_unsafe_approach, KineticsConfig, PointKinetics, reactivity_from_k,
    format_intensity_table, format_approach_report, format_kinetics_report,
)

__version__ = "0.2.0"
__all__ = [
    "ChainCore", "CoreConfig", "LCG",
    "CriticalGuard", "GuardConfig", "GuardTelemetry",
    "multiplication", "inverse_multiplication", "steady_population",
    "relaxation_time", "approach_series", "Measurement", "ApproachConfig",
    "ApproachToCritical", "run_unsafe_approach", "KineticsConfig",
    "PointKinetics", "reactivity_from_k",
    "format_intensity_table", "format_approach_report", "format_kinetics_report",
]
