"""検証結果を証明書にまとめ、Jones 多項式量子暗号 (jones_quantum_crypto) で封印する。"""

from __future__ import annotations

import hashlib
import json

SOUNDNESS = (
    "本アプリはリーマン予想・深リーマン予想を証明しない。両者は未解決問題である。"
    "「verified」は有限範囲の主張を倍精度浮動小数点で数値検証したという意味であり、"
    "区間演算による厳密証明でも、予想全体の証明でもない。"
)


def build_certificate(rh: dict, schoenfeld: dict, drh: list[dict],
                      quantum: list[dict] | None = None) -> dict:
    cert = {
        "engine": "riemann_prover (未知事前エンジン規約: proved / disproved / open)",
        "verdicts": {
            "riemann_hypothesis": "open",
            "deep_riemann_hypothesis": "open",
            "rh_up_to_height": rh["status"],
            "schoenfeld_inequality": schoenfeld["status"],
        },
        "rh_bounded": rh,
        "schoenfeld": schoenfeld,
        "drh_evidence": drh,
        "soundness": SOUNDNESS,
    }
    if quantum is not None:
        cert["quantum_search"] = quantum
    return cert


def _digest(cert: dict) -> bytes:
    body = {k: v for k, v in cert.items() if k != "seal"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).digest()


def seal(cert: dict, braid: list[int]) -> dict:
    """Seal the certificate under the key derived from the braid's Jones polynomial."""
    from jones_quantum_crypto import JonesQuantumCipher, jones_str
    cipher = JonesQuantumCipher.from_braid(braid)
    cert["seal"] = {
        "braid": braid,
        "jones_polynomial": jones_str(braid),
        "key_fingerprint": cipher.fingerprint(),
        "sealed_digest": cipher.encrypt(_digest(cert)).hex(),
    }
    return cert


def check_seal(cert: dict, braid: list[int] | None = None) -> bool:
    """True iff the certificate is unmodified and the braid opens the seal."""
    from jones_quantum_crypto import JonesQuantumCipher
    info = cert.get("seal")
    if not info:
        return False
    try:
        cipher = JonesQuantumCipher.from_braid(braid or info["braid"])
        return cipher.decrypt(bytes.fromhex(info["sealed_digest"])) == _digest(cert)
    except Exception:
        return False
