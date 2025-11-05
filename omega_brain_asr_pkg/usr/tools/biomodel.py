#!/usr/bin/env python3
import json
json.dump({'templates':[{'id':'t01','node':'striatum','dop':0.9}]}, open('generated/templates.json','w'))
print('wrote generated/templates.json')
