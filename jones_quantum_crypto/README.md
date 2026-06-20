# jones_quantum_crypto

**Cryptanalysing a quantum digital signature activates Jones-polynomial quantum
cryptography.**

Built from the reports linking RSA / quantum signatures to the **Jones
polynomial**, D-branes and the non-commutative operator
`π(χ,x) = [iπ(χ,x), f(x)]` (`security_data2_guard.pdf`,
`quantum_computer4.pdf`, `whisperdtest.pdf`).

```
QuantumDigitalSignature.issue(msg, secret_braid, analysis_key)
        │  Ed25519 signature over msg, with the braid concealed inside
        ▼
cryptanalyze(signature, analysis_key)      ← decrypt / break the embedded key
        │  success → recovered braid
        ▼
JonesQuantumCipher.from_braid(braid)        ← key = Jones invariant of the braid
        │
        ▼   ✦ Jones-polynomial quantum cryptography ACTIVATED ✦
encrypt / decrypt payloads
```

Pure **Python 3, stdlib only**.  The Ed25519 signature is the same pure-Python
implementation used by the sibling `access_signature` package.

## The pieces

| module | what it does |
|:--|:--|
| `jones.py` | **Jones polynomial** of a braid closure via the **Kauffman bracket state sum** (resolve every crossing into A/B smoothings, count loops with union-find, normalise by writhe). Also evaluates at a root of unity — the **Aharonov–Jones–Landau** point that a quantum computer approximates (BQP-complete), i.e. the "quantum" in the scheme. |
| `qcipher.py` | **JonesQuantumCipher** — a 32-byte key derived from the braid's exact Jones/Kauffman invariant; HMAC-SHA256 counter-mode keystream with an authentication tag. |
| `qsign.py` | **QuantumDigitalSignature** — Ed25519 signature that also conceals a secret braid (encrypted under `analysis_key`); `verify`, `cryptanalyze`, and `cryptanalyze_bruteforce`. |
| `activation.py` | wires it together: successful cryptanalysis → activate the Jones cipher. `demo()` runs the whole thing. |

## Correctness (verified against the literature)
- unknot → `V = 1`
- right trefoil `σ₁³` → `V = -t⁴ + t³ + t`
- left trefoil `σ₁⁻³` → `V = -t⁻⁴ + t⁻³ + t⁻¹` (mirror)
- Hopf link `σ₁²` → `V = -t^{1/2} - t^{5/2}`
- a single kink reduces to the unknot (Reidemeister I invariance)

## Usage
```bash
# Jones polynomial + cipher key of a braid (σ₁³ = trefoil)
python3 -m jones_quantum_crypto.cli jones 1 1 1

# issue a quantum signature concealing the trefoil under a (weak) PIN
python3 -m jones_quantum_crypto.cli sign --msg "launch-authorization" \
        --braid 1 1 1 --key 0042 --out sig.json
python3 -m jones_quantum_crypto.cli verify sig.json

# CRYPTANALYSE: break the weak PIN -> activates Jones quantum cryptography
python3 -m jones_quantum_crypto.cli break sig.json --max 200
# ...or with the known key:
python3 -m jones_quantum_crypto.cli cryptanalyze sig.json --key 0042

# the activated Jones cipher
python3 -m jones_quantum_crypto.cli encrypt --braid 1 1 1 --text "secret"
python3 -m jones_quantum_crypto.cli decrypt --braid 1 1 1 --hex <hex>

python3 -m jones_quantum_crypto.cli demo        # full end-to-end
python3 -m unittest discover -s tests -v         # 19 tests
```

## Braid words
A list of non-zero ints: `+i` = generator σ_i, `-i` = σ_i⁻¹ (positions
1-indexed). Examples: trefoil `1 1 1`, figure-eight `1 -2 1 -2`, Hopf `1 1`.

## Security framing
This is a **research / own-data** construction: the "cryptanalysis" stage
decrypts a deliberately-escrowed (optionally weak) `analysis_key` *you control*,
as an authorised **decrypt-to-activate** trigger (like a dead-man's switch /
key-escrow ceremony). It is not a tool for attacking third-party keys. The
Ed25519 signature itself is standard and not weakened; only the embedded
trigger secret uses the escrow key.
