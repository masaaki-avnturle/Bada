#!/usr/bin/env python3
"""Convert the source PDFs into plain-text / Markdown.

This is the reproducible extractor used to seed the `extracted/` Markdown
files. It uses pypdf, which reads the embedded text layer directly.

NOTE: Several of the source documents embed Japanese with custom (CID) font
encodings and *no* ToUnicode map. pypdf therefore returns garbled glyphs for
those passages. The committed `.md` files were hand-corrected for the
Japanese-heavy papers (Bada1, explorerfiles, dalia_meload, 20250330) from a
faithful rendering; the math/English papers come through cleanly here.

Usage:
    python3 convert_pdfs.py SRC_DIR OUT_DIR
"""
import sys
import os
import glob


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    try:
        import pypdf
    except ImportError:
        sys.exit("pypdf is required: pip install pypdf cffi")

    for pdf in sorted(glob.glob(os.path.join(src_dir, "*.pdf"))):
        stem = os.path.splitext(os.path.basename(pdf))[0]
        reader = pypdf.PdfReader(pdf)
        out_path = os.path.join(out_dir, stem + ".txt")
        with open(out_path, "w", encoding="utf-8") as fh:
            for i, page in enumerate(reader.pages, 1):
                fh.write("===== PAGE %d =====\n" % i)
                fh.write((page.extract_text() or "") + "\n")
        print("wrote %s (%d pages)" % (out_path, len(reader.pages)))


if __name__ == "__main__":
    main()
