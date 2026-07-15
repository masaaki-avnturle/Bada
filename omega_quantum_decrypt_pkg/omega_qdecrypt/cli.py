"""Command-line application.

    python -m omega_qdecrypt.cli demo
    python -m omega_qdecrypt.cli jones   "3: 1 1 1"
    python -m omega_qdecrypt.cli invmat  "3: 1 2 1 2 1 2"
    python -m omega_qdecrypt.cli crack   --e 65537 --N 120204077 --cipher 3,141,59
    python -m omega_qdecrypt.cli solve   --braid "3: 1 1 1" --message "SECRET"
    python -m omega_qdecrypt.cli scan       ./some/folder
    python -m omega_qdecrypt.cli disinfect  ./some/folder
    python -m omega_qdecrypt.cli quarantine list
"""

from __future__ import annotations

import argparse
import sys

from . import antivirus, jones, rsa_toy, shor
from .matrix import PolyMatrix, inverse_exists
from .pipeline import run_pipeline


def _print_report(rep):
    for step in rep.steps:
        title = step.pop("title")
        print(f"\n=== {title} ===")
        for k, v in step.items():
            print(f"  {k}: {v}")
    print()
    if rep.success:
        print(f">>> SOLVED. plaintext = {rep.plaintext.decode('utf-8', 'replace')!r}")
    else:
        print(">>> not solved.")


def cmd_demo(args):
    """Full end-to-end demo: encrypt a themed secret, then break it."""
    secret = args.message or "MASAAKI-YAMAGUCHI/JONES-MANIFOLD/USB"
    pub, priv = rsa_toy.make_keypair()
    cipher = rsa_toy.encrypt(secret, pub)
    print(f"[+] Encrypted 'USB stick' target created.")
    print(f"    plaintext (hidden from solver): {secret!r}")
    print(f"    RSA public key (e, N) = {pub}")
    print(f"    ciphertext blocks: {cipher[:8]}{'...' if len(cipher) > 8 else ''}")

    braid = jones.parse_braid(args.braid)
    rep = run_pipeline(braid, {"cipher": cipher, "pub": pub}, true_braid=braid)
    _print_report(rep)
    return 0 if rep.success else 1


def cmd_jones(args):
    n, word = jones.parse_braid(args.braid)
    br = jones.kauffman_bracket(n, word)
    fn = jones.jones_bracket_normalized(n, word)
    print(f"strands   : {n}")
    print(f"braid word: {word}")
    print(f"writhe    : {jones.writhe(word)}")
    print(f"Kauffman bracket <D>(A) : {br}")
    print(f"normalized f_L(A)       : {fn}")
    print(f"Jones V_L(t) at t=1.3   : {jones.jones_value(n, word, 1.3):.6f}")
    print(f"32-byte key (hex)       : {jones.derive_key(n, word).hex()}")
    return 0


def cmd_invmat(args):
    n, word = jones.parse_braid(args.braid)
    B = jones.burau_of_braid(n, word)
    inv = inverse_exists(B)
    dinv = inverse_exists(B - PolyMatrix.identity(n))
    print(f"Burau matrix B(v) of the braid (fundamental-group representation):")
    print(B)
    print(f"\ndet(B)      = {inv['det']}")
    print(f"inverse matrix exists (det is a unit +/- v^k): {inv['invertible_ring']}")
    print(f"\ndifference operator  Delta = B - I")
    print(f"det(B - I)  = {dinv['det']}   (singular={dinv['singular']}: Delta fixes the all-ones vector)")
    return 0


def cmd_crack(args):
    cipher = [int(x) for x in args.cipher.split(",")] if args.cipher else None
    broken = shor.break_rsa(args.N, args.e)
    if broken is None:
        print("[-] Shor simulation failed to factor N.")
        return 1
    d, p, q = broken
    print(f"[+] Shor factored N = {args.N} = {p} * {q}")
    print(f"[+] recovered private exponent d = {d}")
    if cipher is not None:
        pt = rsa_toy.decrypt(cipher, (d, args.N))
        print(f"[+] decrypted plaintext = {pt.decode('utf-8', 'replace')!r}")
    return 0


def cmd_solve(args):
    secret = args.message or "SECRET"
    pub, _ = rsa_toy.make_keypair()
    cipher = rsa_toy.encrypt(secret, pub)
    braid = jones.parse_braid(args.braid)
    rep = run_pipeline(braid, {"cipher": cipher, "pub": pub}, true_braid=braid)
    _print_report(rep)
    return 0 if rep.success else 1


def _default_quarantine_dir():
    import os
    return os.environ.get("OMEGA_QUARANTINE_DIR",
                          os.path.join(os.path.expanduser("~"), ".omega_quarantine"))


def cmd_scan(args):
    detections, scanned = antivirus.scan_path(args.path, antivirus.SignatureDB.default())
    print(f"scanned {scanned} file(s) under {args.path}")
    if not detections:
        print("no threats found. (clean)")
        return 0
    for d in detections:
        print(d.line())
    print(f"\n{len(detections)} detection(s).")
    return 0


def cmd_disinfect(args):
    db = antivirus.SignatureDB.default()
    detections, scanned = antivirus.scan_path(args.path, db)
    targets = [d for d in detections
               if d.severity == "malicious" or (args.suspicious and d.severity == "suspicious")]
    print(f"scanned {scanned} file(s); {len(targets)} to quarantine.")
    if not targets:
        return 0
    q = antivirus.Quarantine(args.quarantine or _default_quarantine_dir())
    for d in targets:
        item = q.quarantine(d)
        print(f"  quarantined {d.threat}: {d.path} -> {item.qid} (locked/encrypted)")
    print(f"\nquarantine store: {q.dir}")
    return 0


def cmd_quarantine(args):
    q = antivirus.Quarantine(args.quarantine or _default_quarantine_dir())
    if args.action == "list":
        items = q.list_items()
        if not items:
            print("quarantine is empty.")
            return 0
        for it in items:
            print(f"  {it.qid}  {it.severity:9} {it.threat:20} {it.original_path}")
        return 0
    if args.action == "restore":
        print(f"restored (decrypted) -> {q.restore(args.qid)}")
        return 0
    if args.action == "remove":
        q.remove(args.qid)
        print(f"permanently removed {args.qid}")
        return 0
    print("usage: quarantine {list|restore <id>|remove <id>}")
    return 1


def build_parser():
    p = argparse.ArgumentParser(
        prog="omega_qdecrypt",
        description="Jones/Burau/Shor decryption toolkit + defensive virus scanner.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="end-to-end: build a target then break it")
    d.add_argument("braid", nargs="?", default="3: 1 1 1")
    d.add_argument("--message", default=None)
    d.set_defaults(func=cmd_demo)

    j = sub.add_parser("jones", help="Jones polynomial / bracket / key of a braid")
    j.add_argument("braid")
    j.set_defaults(func=cmd_jones)

    m = sub.add_parser("invmat", help="Burau matrix and inverse-existence test")
    m.add_argument("braid")
    m.set_defaults(func=cmd_invmat)

    c = sub.add_parser("crack", help="Shor-factor an RSA modulus and decrypt")
    c.add_argument("--e", type=int, required=True)
    c.add_argument("--N", type=int, required=True)
    c.add_argument("--cipher", default=None, help="comma-separated ciphertext blocks")
    c.set_defaults(func=cmd_crack)

    s = sub.add_parser("solve", help="run the whole pipeline on a fresh secret")
    s.add_argument("--braid", default="3: 1 1 1")
    s.add_argument("--message", default=None)
    s.set_defaults(func=cmd_solve)

    sc = sub.add_parser("scan", help="scan a file/folder for threats (read-only)")
    sc.add_argument("path")
    sc.set_defaults(func=cmd_scan)

    di = sub.add_parser("disinfect", help="scan then quarantine (encrypt away) threats")
    di.add_argument("path")
    di.add_argument("--suspicious", action="store_true", help="also quarantine heuristic hits")
    di.add_argument("--quarantine", default=None, help="quarantine store dir")
    di.set_defaults(func=cmd_disinfect)

    qz = sub.add_parser("quarantine", help="list/restore/remove quarantined files")
    qz.add_argument("action", choices=["list", "restore", "remove"])
    qz.add_argument("qid", nargs="?", default=None)
    qz.add_argument("--quarantine", default=None, help="quarantine store dir")
    qz.set_defaults(func=cmd_quarantine)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
