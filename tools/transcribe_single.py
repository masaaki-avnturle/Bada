import json, numpy as np, logging
logging.disable(logging.WARNING)
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
_, _, notes = predict("rec0924.wav", ICASSP_2022_MODEL_PATH, onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=100)
ev = sorted([(float(s), float(e), int(p), float(a)) for s, e, p, a, *_ in notes])
ps = np.array([p for _, _, p, _ in ev])
q = np.quantile(ps, [0.25, 0.5, 0.75])
# split the single recording into four voices by register (quartiles): bass, tenor, alto, soprano
bands = [[x for x in ev if x[2] <= q[0]], [x for x in ev if q[0] < x[2] <= q[1]], [x for x in ev if q[1] < x[2] <= q[2]], [x for x in ev if x[2] > q[2]]]
# key order = recording index used by the fugue script: 0 -> alto, 1 -> soprano, 2 -> bass, 3 -> tenor
out = {"0": bands[2], "1": bands[3], "2": bands[0], "3": bands[1]}
json.dump(out, open("notes_0924.json", "w"))
print(len(ev), "notes, pitch", ps.min(), "-", ps.max(), "quartiles", q, [len(b) for b in bands])
