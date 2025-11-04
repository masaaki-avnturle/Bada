#!/usr/bin/env python3
import os,sys,webbrowser
d='generated' if len(sys.argv)<=1 else sys.argv[1]
out=os.path.join(d,'report.html'); os.makedirs(d,exist_ok=True)
with open(out,'w',encoding='utf-8') as f:
    f.write('<html><body><h1>ASR Report</h1>');
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.txt') or fn.endswith('.json'):
            f.write('<h2>'+fn+'</h2><pre>'+open(os.path.join(d,fn),'r',encoding='utf-8',errors='ignore').read()[:10000]+'</pre>')
    f.write('</body></html>')
print('wrote',out)
