import numpy as np, sys, json
from scipy.io import wavfile
from scipy.signal import medfilt
def extract(path, N=2048, H=256):
    sr, x = wavfile.read(path); x = x.astype(np.float32)/32768
    x = x - np.convolve(x, np.ones(64)/64, 'same')  # crude highpass
    f0=[]; en=[]
    win=np.hanning(N)
    for i in range(0,len(x)-N,H):
        fr=x[i:i+N]*win
        rms=np.sqrt(np.mean(fr**2)); en.append(rms)
        if rms<0.01: f0.append(0); continue
        sp=np.fft.rfft(fr, 2*N); ac=np.fft.irfft(np.abs(sp)**2)[:N]; ac/= (ac[0]+1e-9)
        lo,hi=int(sr/1000),int(sr/80)
        seg=ac[lo:hi]; k=lo+np.argmax(seg)
        # octave-error check: prefer lower octave (2k) if nearly as strong
        if 2*k<hi and ac[2*k]>0.9*ac[k]: k=2*k
        f0.append(sr/k if ac[k]>0.4 else 0)
    f0=np.array(f0); en=np.array(en)
    midi=np.where(f0>0, 69+12*np.log2(np.maximum(f0,1)/440), np.nan)
    m=np.copy(midi); m[np.isnan(m)]=0
    m=medfilt(m,9); m[m==0]=np.nan
    t=np.arange(len(m))*H/sr
    # segment into notes
    notes=[]; cur=None
    for i,v in enumerate(m):
        if np.isnan(v):
            if cur: notes.append(cur); cur=None
            continue
        r=int(round(v))
        if cur and abs(r-cur['p'])<=0 : cur['end']=t[i]; cur['vals'].append(v); cur['e'].append(en[i])
        else:
            if cur: notes.append(cur)
            cur={'p':r,'start':t[i],'end':t[i],'vals':[v],'e':[en[i]]}
    if cur: notes.append(cur)
    out=[]
    for n in notes:
        d=n['end']-n['start']+H/sr
        if d<0.09: continue
        out.append({'p':int(round(np.median(n['vals']))),'t':round(float(n['start']),3),'d':round(float(d),3),'v':round(float(np.max(n['e'])),3)})
    # merge same-pitch neighbors with tiny gaps
    merged=[]
    for n in out:
        if merged and merged[-1]['p']==n['p'] and n['t']-(merged[-1]['t']+merged[-1]['d'])<0.12:
            merged[-1]['d']=round(n['t']+n['d']-merged[-1]['t'],3); merged[-1]['v']=max(merged[-1]['v'],n['v'])
        else: merged.append(n)
    return merged
names="C C# D D# E F F# G G# A A# B".split()
for path in sys.argv[1:]:
    notes=extract(path)
    json.dump(notes, open(path.replace('.wav','_notes.json'),'w'))
    print("==",path,len(notes),"notes")
    print(" ".join("%s%d@%.1f(%.2f)"%(names[n['p']%12],n['p']//12-1,n['t'],n['d']) for n in notes))
