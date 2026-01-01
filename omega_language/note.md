# Research Notes â Personal Assistant Demo
Date: 2025-12-05

## Project
- Build tiny_lang assistant that:
  - provides a Vim-like editor (NORMAL / INSERT)
  - ingests PDFs and web pages
  - builds a searchable KB (tiny_kb.txt)
  - answers questions using local KB, fallback to OpenAI

## Tasks
- [x] Create starter notes
- [x] Add embedded sample PDF text and web snapshot
- [ ] Integrate real PDF(s) from literature
- [ ] Add source citations when answering
- [ ] Improve extraction quality (OCR if needed)

## Short glossary (for quick reference)
- KB: knowledge base file (tiny_kb.txt)
- REPORT: extracted PDF text
- URL: fetched webpage HTML/plaintext

## Quick manual commands
- /edit        â open notes in editor
- /use urls=.. reports=.. â set sources
- /build       â build tiny_kb.txt from sources
- /search foo  â search KB for keywords
- /ask <q>     â ask assistant (local then OpenAI)

## Notes to self
- When adding PDFs, put them under `reports/` and reference in /use.
- Keep each PDF extraction under 1MB in KB to keep searches fast.

