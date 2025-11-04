import keyboard
import time

def send_sequence(seq, use_low_level=True):
    parts = [p.strip() for p in seq.split(",") if p.strip()]
    for part in parts:
        try:
            keyboard.send(part)
        except Exception:
            try:
                keyboard.press_and_release(part)
            except Exception:
                pass
        time.sleep(0.02)
