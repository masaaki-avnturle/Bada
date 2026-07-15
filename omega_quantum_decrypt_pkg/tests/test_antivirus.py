"""Tests for the defensive antivirus subsystem.

The malicious sample used here is the industry-standard EICAR test file -- a
harmless 68-byte string every antivirus is designed to detect.  We build it at
runtime from fragments (so this source file does not contain the contiguous
test string), scan it, then clean up.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app_controller as ctrl                                   # noqa: E402
from omega_qdecrypt import antivirus                            # noqa: E402
from omega_qdecrypt.antivirus import fingerprint, signatures    # noqa: E402


def _eicar_bytes() -> bytes:
    # Assembled from fragments; equals the standard EICAR test string.
    parts = [
        r"X5O!P%@AP[4\PZX54(P^)7CC)7}",
        "$EICAR-STANDARD-",
        "ANTIVIRUS-TEST-FILE!",
        "$H+H*",
    ]
    return "".join(parts).encode("ascii")


def _write(tmp, name, data: bytes) -> str:
    p = os.path.join(tmp, name)
    with open(p, "wb") as f:
        f.write(data)
    return p


def test_eicar_hash_matches_known_signature():
    assert fingerprint.sha256_of_bytes(_eicar_bytes()) == signatures.EICAR_SHA256


def test_scan_detects_eicar():
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "clean.txt", b"hello world, nothing to see here\n")
        _write(tmp, "sample.com", _eicar_bytes())
        dets, scanned = antivirus.scan_path(tmp, antivirus.SignatureDB.default())
        assert scanned == 2
        assert len(dets) == 1
        assert dets[0].severity == "malicious"
        assert "EICAR" in dets[0].threat


def test_heuristic_flags_suspicious_script():
    data = b"powershell -w hidden -enc SQBFAFgA...=="
    flags = fingerprint.heuristic_flags(data)
    assert any("suspicious-token" in f for f in flags)


def test_hash_signature_custom():
    db = antivirus.SignatureDB.default()
    payload = b"my-bad-file-body"
    db.add_hash(fingerprint.sha256_of_bytes(payload), "Custom.Test")
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "x.bin", payload)
        d = antivirus.scan_file(p, db)
        assert d and d.threat == "Custom.Test"


def test_jones_fingerprint_deterministic():
    data = bytes(range(256)) * 4
    a = fingerprint.jones_fingerprint(data)
    b = fingerprint.jones_fingerprint(data)
    assert a == b and len(a) == 12


def test_quarantine_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        store = os.path.join(tmp, "_q")
        target = _write(tmp, "sample.com", _eicar_bytes())
        db = antivirus.SignatureDB.default()
        d = antivirus.scan_file(target, db)
        assert d is not None
        q = antivirus.Quarantine(store)
        item = q.quarantine(d)
        # original neutralised/removed, blob stored
        assert not os.path.exists(target)
        assert os.path.exists(os.path.join(store, item.qid + ".bin"))
        assert len(q.list_items()) == 1
        # restore == decrypt back to identical bytes
        q.restore(item.qid)
        assert os.path.exists(target)
        with open(target, "rb") as f:
            assert f.read() == _eicar_bytes()
        assert q.list_items() == []


def test_quarantine_remove():
    with tempfile.TemporaryDirectory() as tmp:
        store = os.path.join(tmp, "_q")
        target = _write(tmp, "sample.com", _eicar_bytes())
        d = antivirus.scan_file(target, antivirus.SignatureDB.default())
        q = antivirus.Quarantine(store)
        item = q.quarantine(d)
        q.remove(item.qid)
        assert q.list_items() == []
        assert not os.path.exists(os.path.join(store, item.qid + ".bin"))


def test_controller_scan_and_disinfect():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["OMEGA_QUARANTINE_DIR"] = os.path.join(tmp, "_q")
        _write(tmp, "sample.com", _eicar_bytes())
        rep = ctrl.scan_report(tmp)
        assert "malicious" in rep and "EICAR" in rep
        out = ctrl.disinfect_report(tmp)
        assert "quarantined" in out
        lst = ctrl.quarantine_report()
        assert "EICAR" in lst
        os.environ.pop("OMEGA_QUARANTINE_DIR", None)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} antivirus tests passed.")


if __name__ == "__main__":
    _run_all()
