#!/usr/bin/env python3
import sys
import argparse

def remove_leading_quote(line: str) -> str:
    return line[1:] if line.startswith('"') else line

def process_stream(inp, out):
    for line in inp:
        out.write(remove_leading_quote(line))

def main():
    p = argparse.ArgumentParser(description='各行先頭の " を取り除く')
    p.add_argument('infile', nargs='?', help='入力ファイル (省略時は stdin)')
    p.add_argument('outfile', nargs='?', help='出力ファイル (省略時は stdout)')
    args = p.parse_args()

    if args.infile:
        inp = open(args.infile, 'r', encoding='utf-8')
    else:
        inp = sys.stdin

    if args.outfile:
        out = open(args.outfile, 'w', encoding='utf-8')
    else:
        out = sys.stdout

    try:
        process_stream(inp, out)
    finally:
        if args.infile:
            inp.close()
        if args.outfile:
            out.close()

if __name__ == '__main__':
    main()
