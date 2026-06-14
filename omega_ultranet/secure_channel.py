"""
secure_channel.py — authenticated, encrypted message channel over a TCP socket.

Construction (pure Python standard library, no external dependencies):

  * Master key K  : 32 bytes derived from the shared knot diagram (omega_qkd).
  * Handshake     : exchange two random 16-byte nonces; session keys are
                    HKDF-SHA256(K, salt = client_nonce || server_nonce).
                    Four directional keys are derived (enc/mac x c2s/s2c).
  * Mutual auth   : each side proves possession of K with an HMAC over the
                    transcript. A wrong knot diagram => auth failure => abort.
                    This is the cryptographic consent gate.
  * Records       : encrypt-then-MAC. Keystream is HMAC-SHA256 in counter mode
                    (a keyed PRF); integrity is HMAC-SHA256 over counter||ct.
                    A strictly increasing per-direction counter prevents replay.

This is conceptually the network sibling of the file-based AES-256-GCM tool in
omega_jones_crypto_pkg: same knot-derived key, authenticated encryption, fresh
per-session keys.
"""
from __future__ import annotations

import hmac
import hashlib
import secrets
import socket
import struct

from omega_qkd import hkdf

INFO = b"omega-ultranet-v1"
NONCE_LEN = 16
MAC_LEN = 32
MAX_FRAME = 16 * 1024 * 1024  # 16 MiB hard cap per record


class AuthError(Exception):
    """Raised when the peer fails to prove possession of the shared key."""


class ChannelError(Exception):
    """Raised on framing / integrity / replay violations."""


def _recvall(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ChannelError("connection closed by peer")
        buf += chunk
    return bytes(buf)


def _keystream(key: bytes, counter: int, n: int) -> bytes:
    out = bytearray()
    block = 0
    while len(out) < n:
        out += hmac.new(key, struct.pack(">QQ", counter, block), hashlib.sha256).digest()
        block += 1
    return bytes(out[:n])


class SecureChannel:
    """A framed, authenticated, encrypted full-duplex channel over one socket."""

    def __init__(self, sock, send_enc, send_mac, recv_enc, recv_mac):
        self.sock = sock
        self._send_enc = send_enc
        self._send_mac = send_mac
        self._recv_enc = recv_enc
        self._recv_mac = recv_mac
        self._send_ctr = 0
        self._recv_ctr = 0

    # -- record layer ----------------------------------------------------
    def send(self, plaintext: bytes) -> None:
        self._send_ctr += 1
        ctr = self._send_ctr
        ks = _keystream(self._send_enc, ctr, len(plaintext))
        ct = bytes(a ^ b for a, b in zip(plaintext, ks))
        hdr = struct.pack(">Q", ctr)
        mac = hmac.new(self._send_mac, hdr + ct, hashlib.sha256).digest()
        payload = hdr + mac + ct
        self.sock.sendall(struct.pack(">I", len(payload)) + payload)

    def recv(self) -> bytes:
        (plen,) = struct.unpack(">I", _recvall(self.sock, 4))
        if plen > MAX_FRAME or plen < 8 + MAC_LEN:
            raise ChannelError("bad frame length")
        payload = _recvall(self.sock, plen)
        hdr, mac, ct = payload[:8], payload[8:8 + MAC_LEN], payload[8 + MAC_LEN:]
        expect = hmac.new(self._recv_mac, hdr + ct, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expect):
            raise ChannelError("integrity check failed")
        (ctr,) = struct.unpack(">Q", hdr)
        if ctr <= self._recv_ctr:
            raise ChannelError("replay / out-of-order record")
        self._recv_ctr = ctr
        ks = _keystream(self._recv_enc, ctr, len(ct))
        return bytes(a ^ b for a, b in zip(ct, ks))

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


def handshake(sock: socket.socket, master_key: bytes, is_host: bool) -> SecureChannel:
    """Run the nonce exchange + mutual authentication; return a SecureChannel."""
    my_nonce = secrets.token_bytes(NONCE_LEN)
    sock.sendall(my_nonce)
    peer_nonce = _recvall(sock, NONCE_LEN)

    client_nonce, server_nonce = (peer_nonce, my_nonce) if is_host else (my_nonce, peer_nonce)
    salt = client_nonce + server_nonce
    okm = hkdf(master_key, salt, INFO, 128)
    c2s_enc, c2s_mac, s2c_enc, s2c_mac = okm[0:32], okm[32:64], okm[64:96], okm[96:128]

    if is_host:
        send_enc, send_mac, recv_enc, recv_mac = s2c_enc, s2c_mac, c2s_enc, c2s_mac
    else:
        send_enc, send_mac, recv_enc, recv_mac = c2s_enc, c2s_mac, s2c_enc, s2c_mac

    # Mutual authentication over the transcript.
    client_tag = hmac.new(c2s_mac, b"auth-client" + salt, hashlib.sha256).digest()
    server_tag = hmac.new(s2c_mac, b"auth-server" + salt, hashlib.sha256).digest()

    if is_host:
        peer_tag = _recvall(sock, MAC_LEN)
        if not hmac.compare_digest(peer_tag, client_tag):
            raise AuthError("peer failed authentication (wrong shared knot key)")
        sock.sendall(server_tag)
    else:
        sock.sendall(client_tag)
        peer_tag = _recvall(sock, MAC_LEN)
        if not hmac.compare_digest(peer_tag, server_tag):
            raise AuthError("host failed authentication (wrong shared knot key)")

    return SecureChannel(sock, send_enc, send_mac, recv_enc, recv_mac)
