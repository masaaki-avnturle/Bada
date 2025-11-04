# Omega Entropy QA Package

Tools generated:
 - bin/extract_sections.py : extract sentences and math snippets
 - bin/entropy_model.py   : compute sentence-level Shannon entropy
 - bin/question_gen.py    : produce question templates (including entropy-targeted)
 - bin/qa_engine.py       : answer questions by matching entropy and heuristics

Quick workflow:
  python3 bin/extract_sections.py report.txt sentences.jsonl
  python3 bin/entropy_model.py sentences.jsonl sentences_entropy.jsonl
  python3 bin/question_gen.py questions.txt
  python3 bin/qa_engine.py report.txt sentences_entropy.jsonl questions.txt answers.txt

The QA engine is heuristic: it uses token overlap, keyword matching and entropy-distance to pick evidence sentences.
