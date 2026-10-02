import json, numpy as np, logging, librosa
logging.disable(logging.WARNING)
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
out = {}
for name in ("r0923a", "r0923b"):
    y, sr = librosa.load(name + ".wav", sr=22050)
    hop = 256
    f0, vflag, vprob = librosa.pyin(y, fmin=60, fmax=1000, sr=sr, frame_length=2048, hop_length=hop)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    flat = librosa.feature.spectral_flatness(y=y, hop_length=hop)[0]
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    _, _, notes = predict(name + ".wav", ICASSP_2022_MODEL_PATH, onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=100)
    feats = []
    for s, e, p, a, *_ in notes:
        i0, i1 = int(s * sr / hop), max(int(s * sr / hop) + 2, int(e * sr / hop))
        seg = f0[i0:i1]
        seg = seg[~np.isnan(seg)]
        cents = 1200 * np.log2(seg / np.median(seg)) if len(seg) > 2 else np.array([0.0])
        glide = float(np.std(cents))                       # pitch wandering inside the note
        att = float(onset_env[max(0, i0 - 2):i0 + 3].max()) # attack sharpness
        # rise time: frames until rms reaches 90% of the note's peak
        r = rms[i0:i1]
        rise = float(np.argmax(r >= 0.9 * r.max()) * hop / sr) if len(r) else 0.0
        fl = float(np.mean(flat[i0:i1]))
        feats.append(dict(s=float(s), e=float(e), p=int(p), a=float(a), glide=glide, att=att, rise=rise, flat=fl,
                          voiced=float(np.mean(vprob[i0:i1]))))
    out[name] = feats
    G = np.array([f["glide"] for f in feats]); R = np.array([f["rise"] for f in feats]); A = np.array([f["att"] for f in feats])
    print(name, len(feats), "notes | glide cents median %.0f p75 %.0f p90 %.0f | rise s median %.2f p75 %.2f | attack median %.1f" % (
        np.median(G), np.percentile(G, 75), np.percentile(G, 90), np.median(R), np.percentile(R, 75), np.median(A)))
    # overall: share of time that is voiced with gliding pitch (voice-like) vs steady
    v = ~np.isnan(f0)
    d = np.abs(np.diff(1200 * np.log2(np.where(v, f0, 1.0) + 1e-9)))
    sliding = v[1:] & v[:-1] & (d > 30) & (d < 300)
    print("   voiced frames %.0f%%, sliding-pitch frames %.0f%%, noisy(breath-like) frames %.0f%%" % (
        100 * v.mean(), 100 * sliding.mean(), 100 * ((flat > 0.3) & (rms > np.percentile(rms, 40))).mean()))
json.dump(out, open("feat0923.json", "w"))
