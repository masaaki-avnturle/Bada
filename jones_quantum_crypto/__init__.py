"""jones_quantum_crypto — cryptanalysing a quantum digital signature activates
Jones-polynomial quantum cryptography.

Pipeline: a quantum (Ed25519) digital signature conceals a secret braid;
decrypting/breaking it recovers the braid, whose Jones polynomial seeds a
quantum cipher.
"""

from .jones import (jones_polynomial, jones_str, kauffman_bracket,
                    normalized_bracket, evaluate_at_root_of_unity, Laurent)
from .qcipher import JonesQuantumCipher, braid_key, describe_braid
from .qsign import QuantumDigitalSignature
from .activation import JonesActivation, demo

__all__ = [
    "jones_polynomial", "jones_str", "kauffman_bracket", "normalized_bracket",
    "evaluate_at_root_of_unity", "Laurent",
    "JonesQuantumCipher", "braid_key", "describe_braid",
    "QuantumDigitalSignature", "JonesActivation", "demo",
]
