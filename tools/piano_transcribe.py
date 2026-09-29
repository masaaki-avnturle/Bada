import json, sys, numpy as np, logging
logging.disable(logging.WARNING)
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
out = {}
for i in range(4):
    _, _, notes = predict(f"rec{i}.wav", ICASSP_2022_MODEL_PATH, onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=100)
    ev = sorted([(float(s), float(e), int(p), float(a)) for s, e, p, a, *_ in notes])
    out[i] = ev
    ps = [p for _, _, p, _ in ev]
    print(i, len(ev), "notes, pitch", min(ps), "-", max(ps), "median", np.median(ps), "dur med", np.median([e-s for s,e,_,_ in ev]))
json.dump(out, open("notes.json", "w"))
