"""Tests for the GUI controller (no Kivy / no display needed)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app_controller as ctrl          # noqa: E402


def test_demo_solve_reports_success():
    out = ctrl.demo_solve("HELLO-APK", "3: 1 1 1")
    assert ">>> SOLVED: 'HELLO-APK'" in out
    assert "Shor" in out


def test_demo_solve_default_message():
    out = ctrl.demo_solve("", "3: 1 1 1")
    assert "SOLVED" in out


def test_jones_report():
    out = ctrl.jones_report("2: 1 1 1")
    assert "Jones V_L(t)" in out
    assert "inverse exists: True" in out


def test_crack_report_roundtrip():
    from omega_qdecrypt import rsa_toy
    pub, _ = rsa_toy.make_keypair(1009, 1013)
    e, N = pub
    cipher = ",".join(str(c) for c in rsa_toy.encrypt("HI", pub))
    out = ctrl.crack_report(N, e, cipher)
    assert "plaintext = 'HI'" in out


def test_bad_braid_raises_cleanly():
    try:
        ctrl.jones_report("not a braid")
    except Exception:
        return
    raise AssertionError("expected an exception for malformed braid")


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} app tests passed.")


if __name__ == "__main__":
    _run_all()
