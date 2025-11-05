#!/usr/bin/env python3
import sys,os,subprocess,json,re,argparse
def run(cmd): return subprocess.call(cmd)
def load_report(path):
    if not os.path.exists(path): print('Report not found:',path); return False
    run([sys.executable,'extract_equations.py',path,'equations.jsonl'])
    run([sys.executable,'equation_entropy.py','equations.jsonl','equations_entropy.jsonl'])
    run([sys.executable,'equation_decomposer.py','equations.jsonl','equations_decomposed.jsonl'])
    print('Loaded and processed report')
    return True
def question_to_entropy(q):
    m=re.search(r'([0-9]+(?:\.[0-9]+)?)',q)
    if m: return float(m.group(1))
    q=q.lower()
    if 'shannon' in q or 'entropy' in q: return 1.5
    if 'gamma' in q: return 2.0
    if 'zeta' in q: return 2.2
    if 'manifold' in q: return 1.9
    if 'noncomm' in q: return 2.1
    return 1.6
def ask_question(q,values=None):
    H=question_to_entropy(q); print('Interpreted target entropy=',H)
    vals = values if values and os.path.exists(values) else 'examples/sample_values.json'
    run([sys.executable,'value_substitute.py','equations_entropy.jsonl',vals,'equations_subst.jsonl'])
    run([sys.executable,'causal_infer.py','equations_subst.jsonl',str(H),'matches.json','analysis_report.txt'])
    if os.path.exists('matches.json'):
        j=json.load(open('matches.json','r',encoding='utf-8'))
        if j:
            print('\n--- Top candidate ---')
            print(j[0].get('answer_text','(no answer)'))
    if os.path.exists('analysis_report.txt'):
        print('\n--- Analysis ---')
        print(open('analysis_report.txt','r',encoding='utf-8').read())
def interactive():
    print('Commands: load <report>, ask <question>, exit')
    while True:
        try: line=input('> ').strip()
        except EOFError: break
        if not line: continue
        if line.lower().startswith('load '): load_report(line[5:].strip())
        elif line.lower().startswith('ask '): ask_question(line[4:].strip())
        elif line.lower() in ('exit','quit'): break
        else: print('Unknown command')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--load'); p.add_argument('--ask'); p.add_argument('--values'); p.add_argument('--interactive', action='store_true')
    args=p.parse_args()
    if args.load: load_report(args.load)
    if args.ask: ask_question(args.ask,args.values)
    if args.interactive: interactive()
if __name__=='__main__': sys.exit(main())
