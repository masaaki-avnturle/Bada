"""Omega MedSafe — 服薬リスクの重複を指摘する教育用チェッカー（用量・配合は扱わない）."""
from .drug_classes import CLASSES, RISK_LABELS, DRUG_TO_CLASS, lookup, normalize
from .checker import check, format_report, Report, Finding

__version__ = "0.1.0"
__all__ = ["CLASSES", "RISK_LABELS", "DRUG_TO_CLASS", "lookup", "normalize",
           "check", "format_report", "Report", "Finding"]
