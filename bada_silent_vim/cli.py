#!/usr/bin/env python3
"""bada-silent-vim command-line interface.

Subcommands
-----------
  run FILE          compile FILE and execute it on the BadaVM (interpreter)
  compile FILE      show the BadaVM bytecode disassembly (compiler)
  synth WORDS --out reconstruct silent-talk lip frames (PGM images) for words
  decode DIR        decode a directory of lip frames into silent-talk tokens
  edit [FILE]       launch the interactive BadaVim editor (keyboard)
  silent-edit DIR   drive BadaVim with silent-talk frames from DIR (headless)
  demo              full end-to-end silent-talk -> Bada program -> run demo
"""

from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from bada import compile_source, disassemble, run_source       # noqa: E402
from silenttalk import SilentTalkDecoder, synth_stream, write_frames  # noqa
from editor import BadaVim, run_interactive                    # noqa: E402
from app import SilentVimSession                               # noqa: E402


def cmd_run(args):
    with open(args.file) as f:
        run_source(f.read())


def cmd_compile(args):
    with open(args.file) as f:
        print(disassemble(compile_source(f.read())))


def cmd_synth(args):
    paths = write_frames(synth_stream(args.words, hold=args.hold), args.out)
    print(f"wrote {len(paths)} frames for {len(args.words)} "
          f"utterance(s) to {args.out}")


def cmd_decode(args):
    for tok in SilentTalkDecoder().decode_dir(args.dir):
        print(tok)


def cmd_edit(args):
    ed = BadaVim.open(args.file) if args.file else BadaVim()
    run_interactive(ed)


def cmd_silent_edit(args):
    ed = BadaVim.open(args.file) if args.file else BadaVim()
    sess = SilentVimSession(ed=ed)
    sess.feed_frames_dir(args.dir)
    print("=== silent-talk transcript ===")
    print("\n".join(sess.transcript))
    print("\n=== buffer ===")
    print(sess.buffer_text())
    if args.run:
        print("\n=== run output ===")
        for line in sess.run():
            print(line)


def cmd_demo(args):
    # A small Bada program dictated entirely by silent talk.
    # In NORMAL mode: enter insert.  In INSERT: dictate tokens.  ESCAPE, RUN.
    words = [
        "AI",         # INSERT
        "EI",         # "print "
        "IA", "OU", "IE",   # "[" "42" "]"
        "AO",         # NEWLINE (open new line, stay in insert)
        "EA",         # "say "
        "UE", "OE", "UE",   # '"' hello '"'
        "UO",         # ESCAPE
        "OA",         # RUN
    ]
    sess = SilentVimSession()
    sess.feed_words(words, hold=args.hold)
    print("=== silent-talk transcript ===")
    print("\n".join(sess.transcript))
    print("\n=== resulting Bada buffer ===")
    print(sess.buffer_text())
    print("\n=== program output (BadaVM) ===")
    for line in sess.ed.output:
        print(line)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bada-silent-vim",
                                description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("run", help="run a .bada file")
    sp.add_argument("file")
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("compile", help="disassemble a .bada file")
    sp.add_argument("file")
    sp.set_defaults(func=cmd_compile)

    sp = sub.add_parser("synth", help="synthesize silent-talk frames")
    sp.add_argument("words", nargs="+", help="viseme-words, e.g. AI EA OE")
    sp.add_argument("--out", default="generated/frames")
    sp.add_argument("--hold", type=int, default=3)
    sp.set_defaults(func=cmd_synth)

    sp = sub.add_parser("decode", help="decode a frames directory")
    sp.add_argument("dir")
    sp.set_defaults(func=cmd_decode)

    sp = sub.add_parser("edit", help="interactive editor")
    sp.add_argument("file", nargs="?")
    sp.set_defaults(func=cmd_edit)

    sp = sub.add_parser("silent-edit", help="drive editor with frames")
    sp.add_argument("dir")
    sp.add_argument("file", nargs="?")
    sp.add_argument("--run", action="store_true")
    sp.set_defaults(func=cmd_silent_edit)

    sp = sub.add_parser("demo", help="end-to-end silent-talk demo")
    sp.add_argument("--hold", type=int, default=3)
    sp.set_defaults(func=cmd_demo)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
