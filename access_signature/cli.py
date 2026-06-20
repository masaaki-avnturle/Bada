#!/usr/bin/env python3
"""access-signature — CLI for the digital-signature access gatekeeper.

  init   --email E              create the owner key pair + set approver email
  on-access --actor A --repo R --op {clone,push,pull} [--email E]
                                record an access attempt; email the owner
  list   [--status S]           list access requests
  approve REQUEST_ID [--ttl N]  approve: issue + email a signed password
  deny   REQUEST_ID             deny a request
  verify --actor A --repo R --password P [--consume]
                                verify a digital-signature password
  whoami                        show owner + protected repos
  outbox                        list spooled emails (when SMTP is unset)
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from access_signature.gatekeeper import Gatekeeper      # noqa: E402


def _gk(args) -> Gatekeeper:
    return Gatekeeper(state_dir=args.state)


def cmd_init(args):
    gk = _gk(args).init_owner(args.email)
    print(f"owner set to {args.email}")
    print(f"private key : {gk.key_path}  (keep secret, do not commit)")
    print("public key  : stored in registry; protected repos = "
          f"{gk.registry.data['repos']}")


def cmd_on_access(args):
    res = _gk(args).on_access(args.actor, args.repo, args.op, args.email)
    print(res["status"])
    if res["status"] == "pending":
        print(f"request id: {res['request']['id']} — owner emailed for "
              f"approval")
    elif res["status"] == "ignored":
        print(res["reason"])


def cmd_list(args):
    for r in _gk(args).registry.requests(args.status):
        print(f"{r['id']}  {r['status']:8}  {r['operation']:5}  "
              f"{r['repo']:12}  {r['actor']} <{r['actor_email']}>")


def cmd_approve(args):
    res = _gk(args).approve(args.request_id, ttl_days=args.ttl)
    print(f"approved {res['actor']} for {res['repo']}")
    print(f"password (emailed, shown once): {res['password']}")
    print(f"signature: {res['signature'][:32]}…")


def cmd_deny(args):
    _gk(args).deny(args.request_id)
    print(f"denied {args.request_id}")


def cmd_verify(args):
    res = _gk(args).verify(args.actor, args.repo, args.password,
                           consume=args.consume)
    if res["ok"]:
        print(f"VALID — signature verified (credential {res['credential']})")
    else:
        print("INVALID — no matching valid signed password")
        sys.exit(1)


def cmd_verify_token(args):
    ok = _gk(args).verify_token(args.actor, args.repo, args.password,
                                args.signature, args.expires, args.pubkey)
    print("VALID" if ok else "INVALID")
    if not ok:
        sys.exit(1)


def cmd_pubkey(args):
    pub = _gk(args).owner_public_pem()
    if not pub:
        print("(no owner key — run 'init' first)")
        sys.exit(1)
    print(pub)


def cmd_whoami(args):
    gk = _gk(args)
    print(f"github account : {gk.registry.data['owner']['github_account']}")
    print(f"approver email : {gk.registry.owner_email}")
    print(f"protected repos: {gk.registry.data['repos']}")
    print(f"has key        : {os.path.exists(gk.key_path)}")


def cmd_outbox(args):
    outbox = os.path.join(_gk(args).state_dir, "outbox")
    if not os.path.isdir(outbox):
        print("(no spooled mail — SMTP may be configured, or nothing sent)")
        return
    for name in sorted(os.listdir(outbox)):
        print(name)


def build_parser():
    p = argparse.ArgumentParser(
        prog="access-signature", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--state", default=None,
                   help="state directory (default: package state/)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init"); sp.add_argument("--email", required=True)
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("on-access")
    sp.add_argument("--actor", required=True)
    sp.add_argument("--repo", required=True)
    sp.add_argument("--op", required=True,
                    choices=["clone", "push", "pull", "fetch"])
    sp.add_argument("--email")
    sp.set_defaults(func=cmd_on_access)

    sp = sub.add_parser("list"); sp.add_argument("--status")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("approve")
    sp.add_argument("request_id")
    sp.add_argument("--ttl", type=int, default=7, help="days valid")
    sp.set_defaults(func=cmd_approve)

    sp = sub.add_parser("deny"); sp.add_argument("request_id")
    sp.set_defaults(func=cmd_deny)

    sp = sub.add_parser("verify")
    sp.add_argument("--actor", required=True)
    sp.add_argument("--repo", required=True)
    sp.add_argument("--password", required=True)
    sp.add_argument("--consume", action="store_true")
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("verify-token", help="stateless signature check")
    sp.add_argument("--actor", required=True)
    sp.add_argument("--repo", required=True)
    sp.add_argument("--password", required=True)
    sp.add_argument("--signature", required=True)
    sp.add_argument("--expires", type=int, required=True)
    sp.add_argument("--pubkey", help="owner public key hex (default: registry)")
    sp.set_defaults(func=cmd_verify_token)

    sub.add_parser("pubkey").set_defaults(func=cmd_pubkey)
    sub.add_parser("whoami").set_defaults(func=cmd_whoami)
    sub.add_parser("outbox").set_defaults(func=cmd_outbox)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
