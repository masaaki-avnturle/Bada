#!/usr/bin/env python3
import sys, subprocess
def main():
    if len(sys.argv) < 4:
        print('Usage: run_pipeline.py report.txt values.json question_entropy')
        return 2
    report = sys.argv[1]
    vals = sys.argv[2]
    h = sys.argv[3]
    subprocess.check_call([sys.executable, 'extract_equations.py', report, 'equations.jsonl'])
    subprocess.check_call([sys.executable, 'equation_entropy.py', 'equations.jsonl', 'equations_entropy.jsonl'])
    subprocess.check_call([sys.executable, 'value_substitute.py', 'equations_entropy.jsonl', vals, 'equations_subst.jsonl'])
    subprocess.check_call([sys.executable, 'causal_infer.py', 'equations_subst.jsonl', h, 'matches.json', 'analysis_report.txt'])
    print('Pipeline finished: matches.json and analysis_report.txt')
    return 0
if __name__ == '__main__':
    sys.exit(main())
