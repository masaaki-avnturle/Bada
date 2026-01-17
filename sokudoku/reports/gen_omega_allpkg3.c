続けます。パート3 — 残りのツール、データ、Makefile、README の書き込みと終了部（main の残り）を送ります。

```c
/* tools scripts */
snprintf(path, sizeof(path), "%s/tools/bnf_to_ply.py", root);
if (write_lines(path, bnf_to_ply_py, sizeof(bnf_to_ply_py)/sizeof(bnf_to_ply_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

snprintf(path, sizeof(path), "%s/tools/pdf_fallback_extract.py", root);
if (write_lines(path, pdf_fallback_extract_py, sizeof(pdf_fallback_extract_py)/sizeof(pdf_fallback_extract_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

snprintf(path, sizeof(path), "%s/tools/jones_poly.py", root);
if (write_lines(path, jones_poly_py, sizeof(jones_poly_py)/sizeof(jones_poly_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

snprintf(path, sizeof(path), "%s/tools/ml_predict.py", root);
if (write_lines(path, ml_predict_py, sizeof(ml_predict_py)/sizeof(ml_predict_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

snprintf(path, sizeof(path), "%s/tools/trace_aggregator.py", root);
if (write_lines(path, trace_aggregator_py, sizeof(trace_aggregator_py)/sizeof(trace_aggregator_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

/* editor snippets and tools README */
snprintf(path, sizeof(path), "%s/tools/vim_snippet.vim", root);
if (write_lines(path, vim_snippet, sizeof(vim_snippet)/sizeof(vim_snippet[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

snprintf(path, sizeof(path), "%s/tools/emacs_snippet.el", root);
if (write_lines(path, emacs_snippet, sizeof(emacs_snippet)/sizeof(emacs_snippet[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

snprintf(path, sizeof(path), "%s/tools/README.txt", root);
if (write_lines(path, tools_readme, sizeof(tools_readme)/sizeof(tools_readme[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

/* data files */
snprintf(path, sizeof(path), "%s/data/books.json", root);
if (write_file(path, books_json, 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

snprintf(path, sizeof(path), "%s/data/sample.csv", root);
if (write_lines(path, sample_csv, 3, 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

/* Makefile and README */
snprintf(path, sizeof(path), "%s/Makefile", root);
if (write_lines(path, makefile_txt, sizeof(makefile_txt)/sizeof(makefile_txt[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

snprintf(path, sizeof(path), "%s/README.txt", root);
if (write_lines(path, readme_txt, sizeof(readme_txt)/sizeof(readme_txt[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

printf("Generated package: %s\n", root);
printf("Run: cd %s && make prepare && make run\n", root);
return 0;
}
```

これでファイル全体を分割して送信しました。必要なら結合済みの完全ファイルを一括で再送しますか？
