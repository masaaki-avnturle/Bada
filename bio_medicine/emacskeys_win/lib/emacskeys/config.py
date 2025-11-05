import os
import json
from .registry_store import load_mapping_by_hash, list_all_mappings

DEFAULT_CONFIG = {
    "enabled_processes": [],
    "mappings": {},
    "per_process_mappings": {},
    "use_low_level_send": True
}

def load_config(config_path=None, registry_hash=None):
    cfg = DEFAULT_CONFIG.copy()
    if registry_hash:
        reg = load_mapping_by_hash(registry_hash)
        if isinstance(reg, dict):
            cfg.update(reg)
            cfg["registry_hash"] = registry_hash
            return cfg
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                filecfg = json.load(f)
            cfg.update(filecfg)
            return cfg
        except Exception:
            pass
    regs = list_all_mappings()
    if regs:
        first = next(iter(regs.keys()))
        reg = regs[first]["data"]
        if isinstance(reg, dict):
            cfg.update(reg)
            cfg["registry_hash"] = first
            return cfg
    return cfg
