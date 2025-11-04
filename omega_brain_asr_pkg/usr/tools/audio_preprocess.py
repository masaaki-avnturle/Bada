#!/usr/bin/env python3
import sys, json
# Writes a small fake feature file if run
if __name__=='__main__': out='generated/feat.json'; import os; os.makedirs('generated', exist_ok=True); json.dump({'energy':[1,2,3,2,1]}, open(out,'w')); print('wrote',out)
