# -*- coding: utf-8 -*-
"""segment.py — 録音 (mono 22.05 kHz WAV) から安定した音高の断片を切り出し JSON に保存する。"""
import numpy as np, wave, glob, os, json
import sys
WAVDIR=sys.argv[1]; OUT=sys.argv[2]
def load(p):
    w=wave.open(p); sr=w.getframerate(); n=w.getnframes()
    return np.frombuffer(w.readframes(n),dtype=np.int16).astype(np.float32)/32768, sr
def f0_acf(frame,sr,fmin=70,fmax=900):
    frame=frame-frame.mean()
    r=np.sqrt((frame**2).mean())
    if r<0.01: return 0,0,r
    ac=np.correlate(frame,frame,'full')[len(frame)-1:]; ac/=ac[0]+1e-9
    lo=int(sr/fmax); hi=int(sr/fmin); seg=ac[lo:hi]; i=int(np.argmax(seg))
    # octave-error guard: check half period
    f=sr/(lo+i)
    return f, seg[i], r
segs=[]
for p in sorted(glob.glob(WAVDIR+'/*.wav')):
    x,sr=load(p); N=2048; hop=512; name=os.path.basename(p)[:-4]
    fr=[]
    for i in range(0,len(x)-N,hop):
        f,c,r=f0_acf(x[i:i+N],sr); fr.append((i/sr,f,c,r))
    fr=np.array(fr)
    midi=np.where(fr[:,1]>0,69+12*np.log2(np.maximum(fr[:,1],1)/440),-99)
    voiced=(fr[:,2]>0.6)&(fr[:,1]>0)
    i=0;n=len(fr)
    while i<n:
        if not voiced[i]: i+=1; continue
        j=i+1; ref=midi[i]
        while j<n and voiced[j] and abs(midi[j]-np.median(midi[i:j]))<0.6: j+=1
        dur=(j-i)*hop/sr
        if dur>=0.18:
            m=float(np.median(midi[i:j])); 
            segs.append(dict(src=name,start=float(fr[i,0]),dur=float(dur),midi=m,rms=float(fr[i:j,3].mean()),clar=float(fr[i:j,2].mean())))
        i=j
json.dump(segs,open(OUT,'w'))
import collections
print(len(segs),'segments')
d=np.array([s['dur'] for s in segs]); m=np.array([round(s['midi']) for s in segs])
print('dur pct 50/90/max',np.percentile(d,[50,90,100]))
print('midi range',m.min(),m.max()); 
h=collections.Counter(m.tolist()); print(sorted(h.items()))
bysrc=collections.Counter(s['src'] for s in segs); print(bysrc)
