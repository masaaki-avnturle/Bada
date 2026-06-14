#!/usr/bin/env python3
"""bada-webos — command line for the Bada Web OS.

Subcommands
  boot [--html PATH]   boot the whole OS, print the report, write the desktop
  qec [--kind --qubit] run Shor-9 error correction (single case, or --all)
  rails NAME f:type..  transpile a Rails scaffold into an OS app
  ultranet             boot the ultranetwork (TupleSpace/XOR/gravity/repeater)
  android              install + launch the Android 12 demo app
  wm                   demo the w9wm window manager (ASCII)
  run FILE.bada        run a Bada application through the kernel
"""

from __future__ import annotations

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (_HERE, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from webos import BadaWebOS                                   # noqa: E402
from quantum.shor9 import demo_correct                       # noqa: E402
from railsbridge.rails_to_os import (RailsField, RailsResource,  # noqa
                                     RailsToOS)
from ultranet import UltraNetwork                            # noqa: E402
from android.installer import Android12Installer, AndroidManifest  # noqa
from wm.w9wm import W9wm                                     # noqa: E402
from kernel.kernel import QuantumKernel                      # noqa: E402


def cmd_boot(args):
    os_ = BadaWebOS()
    r = os_.boot()
    print("== BadaWebOS boot report ==")
    print(f"Shor-9 QEC : {r['qec']['injected']} -> {r['qec']['recovery']} "
          f"-> fidelity {r['qec']['fidelity_corrected']} "
          f"({'OK' if r['qec']['ok'] else 'FAIL'})")
    print(f"objects    : {r['objects']}")
    print(f"drivers    : {r['drivers']}")
    print(f"windows    : {[w for w, _ in r['windows']]}")
    print(f"ultranet   : XOR acc {r['ultranetwork']['xor']['accuracy']}, "
          f"propagation {r['ultranetwork']['propagation']['strengths']}")
    print(f"settings   : layout={r['settings']['layout']} "
          f"font_scale={r['settings']['font_scale']} "
          f"(cloud v{r['cloud_version']})")
    print(f"android    : {r['android']}")
    if args.html:
        os_.save_html(args.html)
        print(f"desktop    : {args.html}")


def cmd_qec(args):
    if args.all:
        ok = 0
        for kind in ("X", "Y", "Z"):
            for q in range(9):
                d = demo_correct(kind, q)
                ok += d["fidelity_after"] > 0.999
                print(f"{kind}@{q}: syndrome {d['syndrome']} -> "
                      f"{d['recovery']} fidelity {d['fidelity_after']:.4f}")
        print(f"\n{ok}/27 single-qubit errors corrected")
    else:
        d = demo_correct(args.kind, args.qubit)
        for k, v in d.items():
            print(f"{k:18}: {v}")


def cmd_rails(args):
    fields = []
    for spec in args.fields:
        name, _, typ = spec.partition(":")
        fields.append(RailsField(name, typ or "string"))
    app = RailsToOS().transpile(RailsResource(args.name, fields))
    print(f"OS app   : {app.name}")
    print(f"object   : {app.object_schema}")
    print(f"methods  : {app.methods}")
    print(f"routes   : {app.routes}")
    print(f"driver   : {app.driver}")
    print(f"\n--- index window template ---\n{app.windows['index']}")


def cmd_ultranet(args):
    r = UltraNetwork().boot()
    print("TupleSpace output:", r["tuplespace"]["output"])
    print("Akashic store    :", r["tuplespace"]["tuplespace"])
    print("XOR truth table  :", r["xor"]["truth_table"],
          "acc", r["xor"]["accuracy"])
    print("propagation      :", r["propagation"]["strengths"])
    print("gravity-gated    :", r["propagation"]["gravity_gated"])


def cmd_android(args):
    inst = Android12Installer()
    m = AndroidManifest("com.bada.notes", "Bada Notes", target_sdk=31,
                        permissions=["android.permission.INTERNET",
                                     "android.permission.CAMERA",
                                     "android.permission.BLUETOOTH_CONNECT"])
    inst.install(m)
    print(inst.launch("com.bada.notes"))
    print("\n".join(inst.log))


def cmd_wm(args):
    wm = W9wm()
    wm.new_window("rio", 10, 10, 300, 180)
    wm.new_window("acme", 120, 80, 400, 240)
    wm.switch_screen(2)
    wm.new_window("stats", 60, 40, 280, 160)
    wm.switch_screen(0)
    print(wm.render_ascii())
    print("\nroot menu:", wm.root_menu())


def cmd_run(args):
    k = QuantumKernel()
    proc = k.run_app_file(os.path.basename(args.file), args.file)
    print(f"[{proc.state}] pid {proc.pid} {proc.name}")
    print("\n".join(proc.output))


def build_parser():
    p = argparse.ArgumentParser(
        prog="bada-webos", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("boot"); sp.add_argument("--html")
    sp.set_defaults(func=cmd_boot)

    sp = sub.add_parser("qec")
    sp.add_argument("--kind", default="Y", choices=["X", "Y", "Z"])
    sp.add_argument("--qubit", type=int, default=4)
    sp.add_argument("--all", action="store_true")
    sp.set_defaults(func=cmd_qec)

    sp = sub.add_parser("rails")
    sp.add_argument("name")
    sp.add_argument("fields", nargs="*", help="name:type ...")
    sp.set_defaults(func=cmd_rails)

    sub.add_parser("ultranet").set_defaults(func=cmd_ultranet)
    sub.add_parser("android").set_defaults(func=cmd_android)
    sub.add_parser("wm").set_defaults(func=cmd_wm)

    sp = sub.add_parser("run"); sp.add_argument("file")
    sp.set_defaults(func=cmd_run)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
