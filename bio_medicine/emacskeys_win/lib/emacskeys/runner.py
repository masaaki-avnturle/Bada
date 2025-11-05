import argparse
import sys
import time
from .listener import KeyMapper
from .registry_store import store_text_under_hash, list_all_mappings, compute_hash_of_text

def main():
    parser = argparse.ArgumentParser(description="Emacs-like per-app keybindings (ctypes, no pywin32)")
    parser.add_argument("--config-file", "-f", help="Import JSON mapping file to registry and exit", default=None)
    parser.add_argument("--registry-hash", "-r", help="Load mapping from registry by hash", default=None)
    parser.add_argument("--list-registry", action="store_true", help="List registry mappings")
    args = parser.parse_args()

    if args.config_file:
        try:
            with open(args.config_file, "r", encoding="utf-8") as f:
                txt = f.read()
            hs = store_text_under_hash(txt, source_path=args.config_file)
            print("Stored mapping with hash:", hs)
        except Exception as e:
            print("Failed to store mapping:", e)
        return

    if args.list_registry:
        regs = list_all_mappings()
        if not regs:
            print("No registry mappings found.")
            return
        for hs, info in regs.items():
            sp = info.get("source_path") or ""
            print(hs, sp)
        return

    mapper = KeyMapper(config_path=None, registry_hash=args.registry_hash)
    try:
        print("Starting Emacs key mapper. Press Ctrl+C to exit.")
        mapper.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        mapper.stop()
        sys.exit(0)
