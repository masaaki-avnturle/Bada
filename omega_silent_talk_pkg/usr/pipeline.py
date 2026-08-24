#!/usr/bin/env python3
"""
pipeline.py — omega_silent_talk エンドツーエンド オーケストレーション

  1) gen_signal.py で脳信号 / 熱エネルギー列を生成
  2) bin/silent_talk --decode で思考記号列を復号
  3) bin/silent_talk --frame  で映像化フレーム (PGM) を出力
  4) 結果を generated/silent_report.json に保存

numpy 等の外部依存なし。標準ライブラリのみ。
"""
import os, subprocess, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN  = os.path.join(ROOT, "bin", "silent_talk")
GEN  = os.path.join(ROOT, "generated")
EX   = os.path.join(ROOT, "examples")


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True)


def ensure_build():
    if not os.path.exists(BIN):
        print("[pipeline] building...")
        r = sh("make", "-C", ROOT)
        if r.returncode != 0:
            print(r.stdout, r.stderr)
            sys.exit(1)


def gen_signals():
    os.makedirs(EX, exist_ok=True)
    gen = os.path.join(ROOT, "usr", "gen_signal.py")
    neuro_p   = os.path.join(EX, "neuro.txt")
    thermal_p = os.path.join(EX, "thermal.txt")
    with open(neuro_p, "w") as f:
        f.write(sh(sys.executable, gen, "neuro").stdout)
    with open(thermal_p, "w") as f:
        f.write(sh(sys.executable, gen, "thermal").stdout)
    return neuro_p, thermal_p


def parse_decode(text):
    out = {"symbols": [], "confidence": None, "gain": None,
           "intent": None, "entropy": None}
    for line in text.splitlines():
        if line.startswith("symbols:"):
            out["symbols"] = [int(x) for x in line.split(":", 1)[1].split()]
        elif line.startswith("confidence="):
            for tok in line.replace("=", " ").split():
                pass
            # "confidence=.. gain=..% intent=.. entropy=.."
            parts = line.split()
            for p in parts:
                if p.startswith("confidence="): out["confidence"] = float(p.split("=")[1])
                elif p.startswith("gain="):      out["gain"] = p.split("=")[1]
                elif p.startswith("intent="):    out["intent"] = float(p.split("=")[1])
                elif p.startswith("entropy="):   out["entropy"] = float(p.split("=")[1])
    return out


def main():
    ensure_build()
    os.makedirs(GEN, exist_ok=True)
    neuro_p, thermal_p = gen_signals()

    print("[pipeline] decoding thought signal...")
    dec = sh(BIN, "--decode", neuro_p, thermal_p, "8")
    print(dec.stdout.strip())
    result = parse_decode(dec.stdout)

    print("[pipeline] rendering visualization frame...")
    frame_p = os.path.join(GEN, "thought_frame.pgm")
    fr = sh(BIN, "--frame", neuro_p, frame_p)
    print(fr.stdout.strip())
    result["frame"] = frame_p if os.path.exists(frame_p) else None

    result["silent_talk_baseline"] = 0.62
    report_p = os.path.join(GEN, "silent_report.json")
    with open(report_p, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[pipeline] wrote {report_p}")

    if result["confidence"] is not None:
        verdict = ("EXCEEDS" if result["confidence"] > 0.62 else "below")
        print(f"[pipeline] confidence {result['confidence']:.4f} "
              f"{verdict} silent-talk baseline 0.62")


if __name__ == "__main__":
    main()
