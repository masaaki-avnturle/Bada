# tiny_lang_entropy_qna.tl
# Analyze a submitted PDF using statistical entropy to infer sections (title, theorem, proof, concluded, conjecture)
# even when explicit headers are absent. Provide /setpdf, /entropy, /ask, /showpdf, /help, /quit.
#
# Builtins assumed: input(), print(), file_read(), file_write(), file_exists(), load_report(path)->string|null,
# split(), join(), trim(), lower(), find(), len(), tostring(), log(x) or log(x,base), openai_chat(prompt)->string|null
#
# Usage:
#  /setpdf <path>   - select PDF and extract text (uses load_report if available)
#  /entropy         - run entropy-based analysis and print inferred sections & stats
#  /ask <terms>     - search locally then OpenAI fallback
#  /showpdf, /help, /quit

kb_file         <- "~/omega_language/tmp/tiny_kb.txt"
selected_pdf_path <- "caostics.pdf"
selected_pdf_text <- "caostics.txt"

# --- Utilities ---
trim_s <- func(s) { if s == null { return "" } ; return s }
trim_newlines <- func(s) { if s == null { return "" } ; r := s ; while len(r) > 0 and (r[-1]=='\n' or r[-1]=='\r') { r := r[0:len(r)-1] } ; return r }

# tokenize: alnum+underscore sequences, lowercased
tokenize <- func(s) {
    out := []
    if s == null { return out }
    cur := ""
    i := 0
    while i < len(s) {
        c := s[i]
        isalnum := false
        if (c >= '0' and c <= '9') or (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z') or c == '_' { isalnum := true }
        if isalnum { cur := cur + lower(c) } else { if cur != "" { out := out + [cur]; cur := "" } }
        i := i + 1
    }
    if cur != "" { out := out + [cur] }
    return out
}

freq_map := func(tokens) {
    m := {}
    if tokens == null { return m }
    i := 0
    while i < len(tokens) {
        t := tokens[i]
        if m[t] == null { m[t] := 1 } else { m[t] := m[t] + 1 }
        i := i + 1
    }
    return m
}

# safe log2
log2 := func(x) {
    if x <= 0 { return 0.0 }
    try_val := null
    try { try_val := log(x, 2) } catch { try_val := log(x) / log(2) }
    return try_val
}

entropy_tokens := func(tokens) {
    if tokens == null { return 0.0 }
    n := len(tokens)
    if n == 0 { return 0.0 }
    m := freq_map(tokens)
    H := 0.0
    for k in m {
        p := m[k] / n
        if p > 0 { H := H - p * log2(p) }
    }
    return H
}

mean_token_length := func(tokens) {
    if tokens == null or len(tokens) == 0 { return 0.0 }
    s := 0
    i := 0
    while i < len(tokens) { s := s + len(tokens[i]); i := i + 1 }
    return s / len(tokens)
}

# --- Paragraph splitting & paragraph stats ---
split_paragraphs := func(text) {
    out := []
    if text == null { return out }
    # split on two or more newlines, but keep single-line breaks as part of paragraph
    parts := split(text, "\n\n")
    i := 0
    while i < len(parts) {
        p := trim_newlines(parts[i])
        if p != "" { out := out + [p] }
        i := i + 1
    }
    return out
}

paragraph_stats := func(p) {
    toks := tokenize(p)
    H := entropy_tokens(toks)
    vocab := 0
    if toks != null and len(toks) > 0 {
        fm := freq_map(toks)
        for k in fm { vocab := vocab + 1 }
    }
    meanlen := mean_token_length(toks)
    return { "text": p, "tokens": len(toks), "vocab": vocab, "entropy": H, "mean_tok_len": meanlen }
}

# --- Heuristic classifier: assign paragraph to one of target sections ---
classify_para := func(pstat) {
    txt := lower(pstat["text"])
    # strong keyword cues
    if find(txt, "theorem") >= 0 { return "theorem" }
    if find(txt, "proof") >= 0 { return "proof" }
    if find(txt, "conclud") >= 0 or find(txt, "conclusion") >= 0 { return "concluded" }
    if find(txt, "conject") >= 0 { return "conjecture" }
    # title heuristic: very short (tokens <= 10) and first paragraph likely title
    if pstat["tokens"] <= 12 and pstat["mean_tok_len"] > 3 and pstat["entropy"] < 4.0 { return "title" }
    # entropy-based heuristics:
    # - proofs often contain formulas/symbols => lower word entropy but longer tokens or many short tokens -> lower normalized entropy
    # - theorem statements short but technical -> moderate entropy
    # - concluded paragraphs narrative, higher entropy and larger vocab
    if pstat["entropy"] < 3.0 and pstat["tokens"] >= 10 { return "proof" }
    if pstat["entropy"] >= 4.5 and pstat["tokens"] >= 15 { return "concluded" }
    if pstat["entropy"] >= 4.0 and pstat["tokens"] >= 6 { return "theorem" }
    # otherwise default to 'full' (unassigned)
    return "full"
}

# --- Aggregate paragraphs into inferred sections ---
infer_sections := func(text) {
    pars := split_paragraphs(text)
    sections := { "title": [], "theorem": [], "proof": [], "concluded": [], "conjecture": [], "full": [] }
    i := 0
    while i < len(pars) {
        p := pars[i]
        pstat := paragraph_stats(p)
        cls := classify_para(pstat)
        # prefer first paragraph as title if unlabeled
        if i == 0 and cls == "full" and pstat["tokens"] <= 15 { cls := "title" }
        sections[cls] := sections[cls] + [ { "text": p, "stats": pstat } ]
        sections["full"] := sections["full"] + [ { "text": p, "stats": pstat } ]
        i := i + 1
    }
    return sections
}

# --- Compute per-section aggregated stats using entropy (Shannon) ---
aggregate_section_stats := func(sections) {
    agg := {}
    for name in [ "title", "theorem", "proof", "concluded", "conjecture", "full" ] {
        arr := sections[name]
        total_tokens := 0
        total_vocab_map := {}
        total_entropy_weighted := 0.0
        nparas := 0
        if arr != null {
            i := 0
            while i < len(arr) {
                ps := arr[i]["stats"]
                total_tokens := total_tokens + ps["tokens"]
                # collect vocab
                toks := tokenize(arr[i]["text"])
                fm := freq_map(toks)
                for k in fm { total_vocab_map[k] := 1 }
                total_entropy_weighted := total_entropy_weighted + ps["entropy"]
                nparas := nparas + 1
                i := i + 1
            }
        }
        vocab_count := 0
        for k in total_vocab_map { vocab_count := vocab_count + 1 }
        avg_entropy := 0.0
        if nparas > 0 { avg_entropy := total_entropy_weighted / nparas }
        agg[name] := { "paras": nparas, "tokens": total_tokens, "vocab": vocab_count, "avg_entropy": avg_entropy }
    }
    return agg
}

# --- Print analysis and interpretation ---
print_entropy_analysis := func(label, sections, agg) {
    print("Entropy analysis for: " + label)
    # print per-section aggregates
    for name in [ "title", "theorem", "proof", "concluded", "conjecture", "full" ] {
        info := agg[name]
        print("- " + name + ": paras=" + tostring(info["paras"]) + ", tokens=" + tostring(info["tokens"]) + ", vocab=" + tostring(info["vocab"]) + ", avg_entropy=" + tostring(info["avg_entropy"]))
    }
    # heuristic comparisons
    print("\nInterpretation hints:")
    # if proof avg_entropy significantly lower than theorem/concluded -> likely detailed formulas/technical derivations
    pproof := agg["proof"]["avg_entropy"]
    ptheo := agg["theorem"]["avg_entropy"]
    pconc := agg["concluded"]["avg_entropy"]
    if pproof < ptheo - 0.5 {
        print("  - 'proof' has lower entropy than 'theorem' -> proofs may be formula-heavy or repetitive (many symbols).")
    }
    if pconc > ptheo + 0.5 {
        print("  - 'concluded' higher entropy than 'theorem' -> conclusions are narrative/summary-like.")
    }
    if agg["title"]["paras"] > 0 {
        print("  - Title detected.")
    } else {
        print("  - No explicit short title paragraph detected.")
    }
    print("You can /ask <terms> to retrieve local extracts or ask OpenAI (if configured).")
}

# --- QnA / local search ---
find_lines_matching := func(text, keywords) {
    out := []
    if text == null or text == "" { return out }
    lines := split(text, "\n")
    lowkeys := []
    i := 0
    while i < len(keywords) { lowkeys := lowkeys + [ lower(trim_s(keywords[i])) ]; i := i + 1 }
    i := 0
    while i < len(lines) {
        line := trim_newlines(lines[i])
        ll := lower(line)
        j := 0
        matched := false
        while j < len(lowkeys) {
            if lowkeys[j] != "" and find(ll, lowkeys[j]) >= 0 { matched := true ; break }
            j := j + 1
        }
        if matched { out := out + [ line ] }
        i := i + 1
    }
    return out
}

answer_question_local := func(q) {
    if q == null or trim_s(q) == "" { print("Usage: /ask <keywords>"); return }
    if selected_pdf_text == null or trim_s(selected_pdf_text) == "" { print("No PDF text available. Use /setpdf <path> first.") ; return }
    hits := find_lines_matching(selected_pdf_text, split(trim_s(q), " "))
    if len(hits) > 0 {
        print("Local extracts:")
        i := 0
        while i < len(hits) and i < 10 { print("- " + hits[i]); i := i + 1 }
        return
    }
    if openai_chat != null {
        prompt := "Document:\n" + selected_pdf_text + "\nQUESTION:\n" + q + "\nAnswer concisely."
        resp := openai_chat(prompt)
        if resp != null and trim_s(resp) != "" {
            print("OpenAI answer:")
            print(trim_newlines(resp))
            return
        }
    }
    print("No local matches and OpenAI unavailable/returned nothing.")
}

# --- Commands ---
set_pdf := func(path) {
    if path == null or trim_s(path) == "" { print("Usage: /setpdf <path>"); return }
    selected_pdf_path := trim_s(path)
    selected_pdf_text := ""
    txt := null
    try { txt := load_report(selected_pdf_path) } catch { txt := null }
    if txt != null and trim_s(txt) != "" {
        selected_pdf_text := txt
        file_write(kb_file, "=== PDF: " + selected_pdf_path + " ===\n" + txt)
        print("PDF loaded and cached: " + selected_pdf_path)
    } else {
        selected_pdf_text := ""
        print("Could not extract text from: " + selected_pdf_path)
        print("If load_report is unavailable, extract text externally and write to " + kb_file)
    }
    # persist globals (some runtimes require)
    selected_pdf_path := selected_pdf_path
    selected_pdf_text := selected_pdf_text
}

show_pdf := func() {
    if selected_pdf_path == null or selected_pdf_path == "" { print("No PDF selected. Use /setpdf <path>") ; return }
    print("Selected PDF: " + selected_pdf_path)
    if selected_pdf_text != null and selected_pdf_text != "" { print("(text cached)") } else { print("(no cached text)") }
}

entropy_cmd := func() {
    if selected_pdf_text == null or trim_s(selected_pdf_text) == "" {
        print("No text available. Use /setpdf <path> first.")
        return
    }
    sections := infer_sections(selected_pdf_text)
    agg := aggregate_section_stats(sections)
    print_entropy_analysis(selected_pdf_path, sections, agg)
}

# --- Command dispatcher / REPL ---
exec_command := func(line) {
    if line == null { return false }
    cmd := trim_s(line)
    if cmd == "" { return false }
    if cmd == "/quit" { print("Quit"); return true }
    if cmd == "/help" {
        print("Commands: /setpdf <path>, /showpdf, /entropy, /ask <terms>, /help, /quit")
        return false
    }
    if substr(cmd,0,8) == "/setpdf " { set_pdf(substr(cmd,8,len(cmd))); return false }
    if cmd == "/showpdf" { show_pdf(); return false }
    if cmd == "/entropy" { entropy_cmd(); return false }
    if substr(cmd,0,5) == "/ask " { answer_question_local(substr(cmd,5,len(cmd))); return false }
    print("Unknown command: " + cmd)
    return false
}

repl := func() {
    print("Entropy QnA REPL. Type /help")
    while true {
        line := input("assistant> ")
        if line == null { print("input returned null; exiting."); return false }
        should_quit := exec_command(line)
        if should_quit { return true }
    }
}

main <- func() {
    print("Starting entropy-based PDF analyzer. Use /setpdf then /entropy.")
    ok := repl()
    if ok { print("Goodbye."); return }
    print("Exited (no interactive input).")
}

main()
