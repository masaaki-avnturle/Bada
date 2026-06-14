#!/usr/bin/env python3
"""
omeganet.py — Omega UltraNet: consent-based, end-to-end encrypted collaboration.

A peer ("host") lets trusted people ("joiners") connect over the network by IP
and work together inside a shared, sandboxed workspace. Everything is encrypted
with a session key derived from a *shared knot diagram* (the earlier Jones /
Kauffman "quantum cryptography" scheme — see omega_qkd.py).

What this IS:
  * A consensual collaboration channel: encrypted group chat, a shared
    collaborative text buffer (the network counterpart of the HHKB shared
    typing surface), and sandboxed file exchange.

What this deliberately is NOT:
  * It does NOT execute remote commands and gives NO control over anyone's OS.
    "Entering" another machine here means joining its shared workspace, with
    that machine's owner approving you first. There is no back door.

Two independent consent gates protect every host:
  1. Cryptographic: you must already hold the same knot diagram the host gave
     you out-of-band, or mutual authentication fails and the socket is dropped.
  2. Human: the host sees your IP + key fingerprint and must approve you (or
     pre-list your IP in an allowlist). Every decision is written to an audit
     log in the workspace.

Usage
-----
  Host (the person sharing their workspace):
      python omeganet.py host --key keys/shared_trefoil.knot --name alice \
             --workspace workspace --port 8765 [--allow allowlist.txt]

  Join (the person connecting in, with permission):
      python omeganet.py join --key keys/shared_trefoil.knot --name bob \
             --workspace workspace_bob --host 203.0.113.7 --port 8765

  Self-test (no network, validates the crypto/handshake locally):
      python omeganet.py selftest

Interactive commands (host console and joiner REPL):
      <text>          send chat to everyone
      /note <text>    append a line to the shared collaborative buffer
      /send <path>    send a file into peers' workspace/received/ sandbox
      /who            list connected participants
      /help           show commands
      /quit           leave
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import threading
import time

from omega_qkd import derive_key_from_diagram, fingerprint
from secure_channel import handshake, SecureChannel, AuthError, ChannelError

MAX_FILE = 5 * 1024 * 1024  # 5 MiB cap on shared files
_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


# ---------------------------------------------------------------------------
#  JSON message helpers on top of the encrypted channel
# ---------------------------------------------------------------------------
def send_msg(ch: SecureChannel, obj: dict) -> None:
    ch.send(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def recv_msg(ch: SecureChannel) -> dict:
    return json.loads(ch.recv().decode("utf-8"))


# ---------------------------------------------------------------------------
#  Workspace (sandbox)
# ---------------------------------------------------------------------------
class Workspace:
    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.received = os.path.join(self.root, "received")
        self.buffer_path = os.path.join(self.root, "shared_buffer.txt")
        self.audit_path = os.path.join(self.root, "connection_log.txt")
        os.makedirs(self.received, exist_ok=True)
        if not os.path.exists(self.buffer_path):
            open(self.buffer_path, "a", encoding="utf-8").close()

    def append_note(self, who: str, text: str) -> None:
        with open(self.buffer_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {who}: {text}\n")

    def read_buffer(self) -> str:
        with open(self.buffer_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_file(self, name: str, data: bytes) -> str:
        safe = os.path.basename(name).replace("\\", "_").strip() or "file.bin"
        dest = os.path.join(self.received, safe)
        # never escape the sandbox
        if os.path.commonpath([self.received, os.path.abspath(dest)]) != self.received:
            raise ValueError("unsafe path")
        with open(dest, "wb") as f:
            f.write(data)
        return dest

    def audit(self, line: str) -> None:
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")


# ---------------------------------------------------------------------------
#  Application-level message handling (shared by host and joiner)
# ---------------------------------------------------------------------------
def apply_message(ws: Workspace, obj: dict) -> None:
    t = obj.get("t")
    who = obj.get("from", "?")
    if t == "chat":
        log(f"  💬 {who}: {obj.get('text', '')}")
    elif t == "note":
        text = obj.get("text", "")
        ws.append_note(who, text)
        log(f"  📝 ({who} → shared buffer) {text}")
    elif t == "file":
        try:
            data = base64.b64decode(obj.get("data", ""))
        except Exception:
            log(f"  ⚠ corrupt file from {who}")
            return
        if len(data) > MAX_FILE:
            log(f"  ⚠ file from {who} too large, dropped")
            return
        try:
            dest = ws.save_file(obj.get("name", "file.bin"), data)
            log(f"  📁 received '{os.path.basename(dest)}' from {who} → {dest}")
        except ValueError:
            log(f"  ⚠ rejected unsafe filename from {who}")
    elif t == "sys":
        log(f"  ★ {obj.get('text', '')}")


def build_outgoing(name: str, line: str):
    """Parse a console line into a message dict, or return None to ignore."""
    line = line.rstrip("\n")
    if not line:
        return None
    if line.startswith("/note "):
        return {"t": "note", "from": name, "text": line[6:]}
    if line.startswith("/send "):
        path = line[6:].strip()
        if not os.path.isfile(path):
            log(f"  ⚠ no such file: {path}")
            return None
        if os.path.getsize(path) > MAX_FILE:
            log("  ⚠ file exceeds 5 MiB limit")
            return None
        with open(path, "rb") as f:
            data = f.read()
        return {"t": "file", "from": name, "name": os.path.basename(path),
                "data": base64.b64encode(data).decode("ascii")}
    return {"t": "chat", "from": name, "text": line}


# ===========================================================================
#  HOST  (hub + consent gate)
# ===========================================================================
class Hub:
    def __init__(self, name: str, ws: Workspace):
        self.name = name
        self.ws = ws
        self.peers = {}          # ch -> peer name
        self.lock = threading.Lock()

    def broadcast(self, obj: dict, exclude: SecureChannel = None) -> None:
        dead = []
        with self.lock:
            targets = list(self.peers.items())
        for ch, _ in targets:
            if ch is exclude:
                continue
            try:
                send_msg(ch, obj)
            except (OSError, ChannelError):
                dead.append(ch)
        for ch in dead:
            self.drop(ch)

    def drop(self, ch: SecureChannel) -> None:
        with self.lock:
            who = self.peers.pop(ch, None)
        ch.close()
        if who:
            log(f"  ★ {who} left")
            self.broadcast({"t": "sys", "text": f"{who} left the session"})

    def who_list(self):
        with self.lock:
            return [self.name + " (host)"] + list(self.peers.values())


def approve(addr_ip: str, fp: str, allowlist: set, ws: Workspace, lock: threading.Lock) -> bool:
    """Human/allowlist consent gate for an incoming connection."""
    if addr_ip in allowlist:
        ws.audit(f"AUTO-ALLOW {addr_ip} fp={fp} (allowlist)")
        log(f"  ★ auto-approved {addr_ip} (allowlist)")
        return True
    with lock:  # serialize interactive prompts
        log("")
        log(f"  ┌─ Connection request ─────────────────────────")
        log(f"  │ IP          : {addr_ip}")
        log(f"  │ key matches : YES  (fingerprint {fp})")
        log(f"  │ Approve this person into your workspace?")
        log(f"  └──────────────────────────────────────────────")
        try:
            ans = input("  approve? [y/N] ").strip().lower()
        except EOFError:
            ans = "n"
    ok = ans in ("y", "yes")
    ws.audit(f"{'ALLOW' if ok else 'DENY'} {addr_ip} fp={fp} (manual)")
    return ok


def handle_peer(sock, addr, key, hub: Hub, ws: Workspace, allowlist, prompt_lock):
    ip = addr[0]
    try:
        sock.settimeout(20)
        ch = handshake(sock, key, is_host=True)
        sock.settimeout(None)
    except (AuthError, ChannelError, OSError) as e:
        ws.audit(f"REJECT {ip} ({e})")
        log(f"  ⚠ {ip} rejected during handshake: {e}")
        sock.close()
        return

    if not approve(ip, fingerprint(key), allowlist, ws, prompt_lock):
        try:
            send_msg(ch, {"t": "sys", "text": "Connection declined by host."})
        except OSError:
            pass
        ch.close()
        log(f"  ★ declined {ip}")
        return

    # Learn the joiner's display name (first message).
    try:
        hello = recv_msg(ch)
        peer_name = str(hello.get("name", ip))[:32]
    except (ChannelError, OSError, ValueError):
        ch.close()
        return

    with hub.lock:
        hub.peers[ch] = peer_name
    log(f"  ★ {peer_name} ({ip}) joined the session")
    ws.audit(f"JOINED {ip} as {peer_name}")
    send_msg(ch, {"t": "sys", "text": f"Welcome {peer_name}! You are in '{hub.name}' workspace."})
    # Sync current shared buffer to the newcomer.
    buf = ws.read_buffer()
    if buf.strip():
        send_msg(ch, {"t": "sys", "text": "----- shared buffer so far -----\n" + buf.rstrip()})
    hub.broadcast({"t": "sys", "text": f"{peer_name} joined"}, exclude=ch)

    # Relay loop.
    while True:
        try:
            obj = recv_msg(ch)
        except (ChannelError, OSError, ValueError):
            break
        if obj.get("t") == "who":
            send_msg(ch, {"t": "sys", "text": "participants: " + ", ".join(hub.who_list())})
            continue
        obj["from"] = peer_name  # authoritative name
        apply_message(ws, obj)
        hub.broadcast(obj, exclude=ch)
    hub.drop(ch)


def run_host(args):
    key = derive_key_from_diagram(args.key)
    ws = Workspace(args.workspace)
    hub = Hub(args.name, ws)
    allowlist = set()
    if args.allow and os.path.isfile(args.allow):
        with open(args.allow, encoding="utf-8") as f:
            allowlist = {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}
    prompt_lock = threading.Lock()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.bind, args.port))
    srv.listen(8)

    log("=" * 60)
    log(f"  Omega UltraNet host '{args.name}'")
    log(f"  listening on {args.bind}:{args.port}")
    log(f"  shared-key fingerprint: {fingerprint(key)}")
    log(f"  workspace: {ws.root}")
    log(f"  (share the SAME knot diagram + fingerprint out-of-band)")
    log("=" * 60)

    def acceptor():
        while True:
            try:
                sock, addr = srv.accept()
            except OSError:
                break
            threading.Thread(target=handle_peer,
                             args=(sock, addr, key, hub, ws, allowlist, prompt_lock),
                             daemon=True).start()

    threading.Thread(target=acceptor, daemon=True).start()

    # Host console.
    log("  type to chat · /note · /send · /who · /quit")
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip() == "/quit":
            break
        if line.strip() == "/who":
            log("  participants: " + ", ".join(hub.who_list()))
            continue
        if line.strip() == "/help":
            log("  <text> chat | /note <t> | /send <path> | /who | /quit")
            continue
        obj = build_outgoing(args.name, line)
        if obj:
            apply_message(ws, obj)
            hub.broadcast(obj)
    srv.close()
    log("  host shut down.")


# ===========================================================================
#  JOIN  (client)
# ===========================================================================
def run_join(args):
    key = derive_key_from_diagram(args.key)
    ws = Workspace(args.workspace)
    log(f"  connecting to {args.host}:{args.port} …")
    log(f"  shared-key fingerprint: {fingerprint(key)}")

    sock = socket.create_connection((args.host, args.port), timeout=20)
    try:
        ch = handshake(sock, key, is_host=False)
    except (AuthError, ChannelError, OSError) as e:
        log(f"  ✗ could not establish secure session: {e}")
        log("    (do both sides use the SAME knot diagram?)")
        return
    sock.settimeout(None)
    log("  ✓ encrypted session established · waiting for host approval …")

    send_msg(ch, {"name": args.name})

    stop = threading.Event()

    def reader():
        while not stop.is_set():
            try:
                obj = recv_msg(ch)
            except (ChannelError, OSError, ValueError):
                break
            apply_message(ws, obj)
        stop.set()
        log("  ★ disconnected from host.")

    threading.Thread(target=reader, daemon=True).start()

    log("  type to chat · /note · /send · /who · /quit")
    while not stop.is_set():
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            break
        s = line.strip()
        if s == "/quit":
            break
        if s == "/who":
            try:
                send_msg(ch, {"t": "who"})
            except OSError:
                break
            continue
        if s == "/help":
            log("  <text> chat | /note <t> | /send <path> | /who | /quit")
            continue
        obj = build_outgoing(args.name, line)
        if obj:
            if obj["t"] in ("note", "file"):
                apply_message(ws, obj)  # reflect locally too
            try:
                send_msg(ch, obj)
            except OSError:
                break
    stop.set()
    ch.close()


# ===========================================================================
#  SELFTEST  (no network — validates crypto, handshake, framing, replay)
# ===========================================================================
def run_selftest(_args):
    from omega_qkd import hkdf  # noqa: F401  (ensure import works)
    results = []

    # 1) Matching keys: handshake succeeds and messages round-trip.
    a, b = socket.socketpair()
    a.settimeout(5); b.settimeout(5)
    box = {}

    def side(target, sock, is_host, kkey, label):
        try:
            target[label] = handshake(sock, kkey, is_host)
        except Exception as e:  # noqa: BLE001
            target[label] = e

    k = b"\x11" * 32
    ta = threading.Thread(target=side, args=(box, a, True, k, "host"))
    tb = threading.Thread(target=side, args=(box, b, False, k, "join"))
    ta.start(); tb.start(); ta.join(); tb.join()
    ok = isinstance(box["host"], SecureChannel) and isinstance(box["join"], SecureChannel)
    results.append(("handshake with matching key", ok))

    if ok:
        host_ch, join_ch = box["host"], box["join"]
        join_ch.send(b"hello-from-join")
        r1 = host_ch.recv()
        host_ch.send(b"reply-from-host-\xf0\x9f\x94\x90")
        r2 = join_ch.recv()
        results.append(("encrypted round-trip", r1 == b"hello-from-join"
                        and r2 == b"reply-from-host-\xf0\x9f\x94\x90"))

        # Replay/tamper: feed a duplicated record back, expect rejection.
        join_ch.send(b"ping")
        host_ch.recv()
        replay_ok = False
        try:
            # craft a frame with a stale counter by reusing recv logic expectations
            host_ch._recv_ctr = 10 ** 9  # force any future record to look stale
            join_ch.send(b"again")
            host_ch.recv()
        except ChannelError:
            replay_ok = True
        results.append(("replay/out-of-order rejected", replay_ok))
    a.close(); b.close()

    # 2) Mismatched keys: authentication must fail.
    a2, b2 = socket.socketpair()
    a2.settimeout(5); b2.settimeout(5)
    box2 = {}
    ta = threading.Thread(target=side, args=(box2, a2, True, b"\x11" * 32, "host"))
    tb = threading.Thread(target=side, args=(box2, b2, False, b"\x22" * 32, "join"))
    ta.start(); tb.start(); ta.join(); tb.join()
    auth_blocked = isinstance(box2["host"], AuthError) or isinstance(box2["join"], (AuthError, ChannelError))
    results.append(("wrong key blocked by auth gate", auth_blocked))
    a2.close(); b2.close()

    print("\n  Omega UltraNet self-test")
    print("  " + "-" * 40)
    allgood = True
    for name, good in results:
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
        allgood &= good
    print("  " + "-" * 40)
    print(f"  {'ALL PASSED ✓' if allgood else 'FAILURES ✗'}\n")
    return 0 if allgood else 1


# ===========================================================================
#  CLI
# ===========================================================================
def main():
    p = argparse.ArgumentParser(description="Omega UltraNet — consensual encrypted collaboration")
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("host", help="share your workspace and approve joiners")
    h.add_argument("--key", required=True, help="shared knot diagram file")
    h.add_argument("--name", default=socket.gethostname())
    h.add_argument("--workspace", default="workspace")
    h.add_argument("--bind", default="0.0.0.0")
    h.add_argument("--port", type=int, default=8765)
    h.add_argument("--allow", help="optional IP allowlist file (auto-approve)")
    h.set_defaults(func=run_host)

    j = sub.add_parser("join", help="connect to a host (with permission)")
    j.add_argument("--key", required=True, help="shared knot diagram file")
    j.add_argument("--name", default=socket.gethostname())
    j.add_argument("--workspace", default="workspace_join")
    j.add_argument("--host", required=True, help="host IP address")
    j.add_argument("--port", type=int, default=8765)
    j.set_defaults(func=run_join)

    s = sub.add_parser("selftest", help="validate crypto locally (no network)")
    s.set_defaults(func=run_selftest)

    args = p.parse_args()
    rc = args.func(args)
    raise SystemExit(rc or 0)


if __name__ == "__main__":
    main()
