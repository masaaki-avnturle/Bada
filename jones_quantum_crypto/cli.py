#!/usr/bin/env python3
"""jones-quantum-crypto — CLI.

  jones BRAID...                  Jones polynomial + key fingerprint of a braid
  sign  --msg M --braid B... --key K [--out F]   issue a quantum signature
  verify FILE                     verify the Ed25519 signature
  cryptanalyze FILE --key K       decrypt the embedded secret; activate Jones
  break FILE [--max N]            brute-force a weak PIN; activate on success
  encrypt --braid B... --text T   Jones-cipher encrypt (key from braid)
  decrypt --braid B... --hex H    Jones-cipher decrypt
  demo                            full end-to-end activation demo
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jones_quantum_crypto import (JonesActivation, JonesQuantumCipher,  # noqa
                                  QuantumDigitalSignature, demo,
                                  describe_braid, evaluate_at_root_of_unity)


def _braid(args_list):
    return [int(x) for x in args_list]


def cmd_jones(args):
    braid = _braid(args.braid)
    d = describe_braid(braid)
    print(f"braid           : {d['braid']}")
    print(f"Jones V(t)      : {d['jones']}")
    print(f"AJL eval (r=5)  : {evaluate_at_root_of_unity(braid, 5):.4f}")
    print(f"key fingerprint : {d['key_fingerprint']}")


def cmd_sign(args):
    qds = QuantumDigitalSignature()
    sig = qds.issue(args.msg.encode(), _braid(args.braid), args.key)
    text = json.dumps(sig, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"signature written to {args.out}")
        print(f"(private seed for this run: {qds.seed.hex()})")
    else:
        print(text)


def cmd_verify(args):
    with open(args.file) as f:
        sig = json.load(f)
    print("VALID" if QuantumDigitalSignature.verify(sig) else "INVALID")


def cmd_cryptanalyze(args):
    with open(args.file) as f:
        sig = json.load(f)
    act = JonesActivation()
    rep = act.activate_from_cryptanalysis(sig, args.key)
    _print_activation(rep)


def cmd_break(args):
    with open(args.file) as f:
        sig = json.load(f)
    act = JonesActivation()
    rep = act.activate_by_breaking(sig, (f"{i:04d}" for i in range(args.max)))
    _print_activation(rep)


def _print_activation(rep):
    if not rep["activated"]:
        print(f"cryptanalysis FAILED — {rep.get('reason')}")
        sys.exit(1)
    print("=== CRYPTANALYSIS SUCCEEDED → Jones quantum cryptography ACTIVATED ===")
    if "broken_key" in rep:
        print(f"broken key      : {rep['broken_key']}  (after {rep['tried']} tries)")
    print(f"recovered braid : {rep['recovered_braid']}")
    print(f"Jones V(t)      : {rep['jones']}")
    print(f"key fingerprint : {rep['key_fingerprint']}")


def cmd_encrypt(args):
    cipher = JonesQuantumCipher.from_braid(_braid(args.braid))
    print(cipher.encrypt(args.text.encode()).hex())


def cmd_decrypt(args):
    cipher = JonesQuantumCipher.from_braid(_braid(args.braid))
    print(cipher.decrypt(bytes.fromhex(args.hex)).decode())


def cmd_demo(args):
    print(json.dumps(demo(), indent=2))


def build_parser():
    p = argparse.ArgumentParser(
        prog="jones-quantum-crypto", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("jones"); sp.add_argument("braid", nargs="+")
    sp.set_defaults(func=cmd_jones)

    sp = sub.add_parser("sign")
    sp.add_argument("--msg", required=True)
    sp.add_argument("--braid", nargs="+", required=True)
    sp.add_argument("--key", required=True)
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_sign)

    sp = sub.add_parser("verify"); sp.add_argument("file")
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("cryptanalyze")
    sp.add_argument("file"); sp.add_argument("--key", required=True)
    sp.set_defaults(func=cmd_cryptanalyze)

    sp = sub.add_parser("break")
    sp.add_argument("file"); sp.add_argument("--max", type=int, default=10000)
    sp.set_defaults(func=cmd_break)

    sp = sub.add_parser("encrypt")
    sp.add_argument("--braid", nargs="+", required=True)
    sp.add_argument("--text", required=True)
    sp.set_defaults(func=cmd_encrypt)

    sp = sub.add_parser("decrypt")
    sp.add_argument("--braid", nargs="+", required=True)
    sp.add_argument("--hex", required=True)
    sp.set_defaults(func=cmd_decrypt)

    sub.add_parser("demo").set_defaults(func=cmd_demo)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
