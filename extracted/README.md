# Extracted PDFs → Markdown

Text extracted and converted from a set of source PDFs (papers and design notes
by **Masaaki Yamaguchi**) into Markdown, with equations rendered in LaTeX-style
math and prose preserved. One Markdown file per source PDF, named after the
original file stem.

## Index

| Markdown | Title | Pages | Lang |
|:---------|:------|:-----:|:----:|
| [`20250205.md`](20250205.md) | Beta function reveal with global differential manifold | 5 | EN |
| [`20250330.md`](20250330.md) | DNA of Universe and human being entrance with zeta function | 2 | JA/EN |
| [`astagin.md`](astagin.md) | (untitled draft — identical body to `caostics.md`) | 5 | EN |
| [`Bada1.md`](Bada1.md) | Artificial Intelligence and TupleSpace of ultranetwork | 22 | JA + Omega DSL |
| [`cafe.md`](cafe.md) | Library of akashic recode | 6 | EN |
| [`caostics.md`](caostics.md) | Euler product estrade from Heisenberg Non-commutative with deprivate equation | 5 | EN |
| [`dalia.md`](dalia.md) | Magic operate with dalia function system | 5 | EN |
| [`dalia_meload.md`](dalia_meload.md) | M dimension from catastrophe theory built with M manifold stream from space ideality theory | 1 | EN |
| [`explorerfiles.md`](explorerfiles.md) | 無と時間、空間、そしてものごとの相対性 (Nothingness, Time, Space and the Relativity of Things) | 49 | JA/EN |
| [`quantum_computer4.md`](quantum_computer4.md) | Quantum Computer in a certain theorem | 7 | EN |

## Notes on the sources

- **`astagin` / `caostics` / `dalia`** share the same "circle element / neipa
  number / Euler product" core. `caostics.md` holds the full transcription;
  `astagin.md` points to it (identical body); `dalia.md` is a distinct variant
  with a different ("dalia function" / T-tensor / timebow) ending.
- **`explorerfiles.pdf`** is the long 49-page Japanese essay (the chemistry
  sections are figures, summarized in prose). The Heisenberg–Gamma and
  cohomology/D-brane equation blocks recur verbatim several times in the source;
  those repetitions are noted rather than re-typed.

## Reproducing the extraction

[`convert_pdfs.py`](convert_pdfs.py) regenerates plain-text dumps from the
PDFs via `pypdf`:

```sh
pip install pypdf cffi
python3 convert_pdfs.py <SRC_DIR_WITH_PDFS> <OUT_DIR>
```

The math/English papers come through `pypdf` cleanly. Documents with
custom-encoded (CID) Japanese fonts and no ToUnicode map garble under `pypdf`;
the Markdown for those (`Bada1`, `explorerfiles`, `dalia_meload`, `20250330`)
was hand-corrected from a faithful rendering.
