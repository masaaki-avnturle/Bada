# persistent_file_daemon.tl
# Always-running file-command daemon for tiny_lang.
# Writes output via print(); read commands from /tmp/tiny_commands.txt (one per line).
# Commands: /setpdf <path>, /showpdf, /entropy, /ask <terms>, /help, /quit

cmd_file <- "/tmp/tiny_commands.txt"
kb_file  <- "/tmp/tiny_kb.txt"

selected_pdf_path <- "~/file/"
selected_pdf_text <- ""

# Utilities
trim_s := func(s) { if s == null { return "" } ; return s }
trim_newlines := func(s) { if s == null { return "" } ; r := s ; while len(r)>0 and (r[-1]=='\n' or r[-1]=='\r') { r := r[0:len(r)-1] } ; return r }

safe_read := func(path) {
    try { return file_read(path) } catch { return null }
}
safe_write := func(path, t) {
    try { file_write(path, t) } catch { }
}

# Tokenization & entropy
tokenize := func(s) {
    out := []
    if s == null { return out }
    cur := ""
    i := 0
    while i < len(s) {
        c := s[i]
        isalnum := false
        if (c>='0' and c<='9') or (c>='A' and c<='Z') or (c>='a' and c<='z') or c=='_' { isalnum := true }
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
log2 := func(x) { if x <= 0 { return 0.0 } ; try { return log(x,2) } catch { return log(x) / log(2) } }
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

# Paragraph handling & heuristics
split_paragraphs := func(text) {
    out := []
    if text == null { return out }
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
    return { "text": p, "tokens": len(toks), "entropy": entropy_tokens(toks) }
}
classify_para := func(ps) {
    txt := lower(ps["text"])
    if find(txt, "proof") >= 0 { return "proof" }
    if find(txt, "theorem") >= 0 { return "theorem" }
    if find(txt, "conclud") >= 0 or find(txt, "conclusion") >= 0 { return "concluded" }
    if find(txt, "conject") >= 0 { return "conjecture" }
    if ps["tokens"] <= 12 and ps["entropy"] < 4.0 { return "title" }
    if ps["entropy"] < 3.0 and ps["tokens"] >= 8 { return "proof" }
    if ps["entropy"] >= 4.5 and ps["tokens"] >= 15 { return "concluded" }
    if ps["entropy"] >= 4.0 and ps["tokens"] >= 6 { return "theorem" }
    return "full"
}
infer_sections := func(text) {
    pars := split_paragraphs(text)
    sections := { "title": [], "theorem": [], "proof": [], "concluded": [], "conjecture": [], "full": [] }
    i := 0
    while i < len(pars) {
        ps := paragraph_stats(pars[i])
        cls := classify_para(ps)
        if i == 0 and cls == "full" and ps["tokens"] <= 15 { cls := "title" }
        sections[cls] := sections[cls] + [ps]
        sections["full"] := sections["full"] + [ps]
        i := i + 1
    }
    return sections
}
aggregate_section_stats := func(sections) {
    agg := {}
    names := [ "title", "theorem", "proof", "concluded", "conjecture", "full" ]
    for n in names {
        arr := sections[n]
        total_tokens := 0
        total_entropy := 0.0
        vocab_map := {}
        count := 0
        if arr != null {
            i := 0
            while i < len(arr) {
                ps := arr[i]
                total_tokens := total_tokens + ps["tokens"]
                toks := tokenize(ps["text"])
                fm := freq_map(toks)
                for k in fm { vocab_map[k] := 1 }
                total_entropy := total_entropy + ps["entropy"]
                count := count + 1
                i := i + 1
            }
        }
        vocab := 0
        for k in vocab_map { vocab := vocab + 1 }
        avg_entropy := 0.0
        if count > 0 { avg_entropy := total_entropy / count }
        agg[n] := { "paras": count, "tokens": total_tokens, "vocab": vocab, "avg_entropy": avg_entropy }
    }
    return agg
}
print_entropy_analysis := func(label, sections, agg) {
    print("Entropy analysis: " + label)
    order := [ "title", "theorem", "proof", "concluded", "conjecture", "full" ]
    i := 0
    while i < len(order) {
        n := order[i]
        info := agg[n]
        print("- " + n + ": paras=" + tostring(info["paras"]) + ", tokens=" + tostring(info["tokens"]) + ", vocab=" + tostring(info["vocab"]) + ", avg_entropy=" + tostring(info["avg_entropy"]))
        i := i + 1
    }
}

# State setter (assign globals)
set_selected_text := func(path, text) {
    selected_pdf_path := path
    selected_pdf_text := text
    if text != null and trim_s(text) != "" { safe_write(kb_file, "=== PDF: " + path + " ===\n" + text) }
}

# Commands
cmd_setpdf := func(arg) {
    if arg == null or trim_s(arg) == "" { print("Usage: /setpdf <path>"); return }
    print("Selecting PDF: " + arg)
    txt := null
    try { txt := load_report(arg) } catch { txt := null }
    if txt != null and trim_s(txt) != "" {
        print("Extracted text and cached.")
        set_selected_text(arg, txt)
    } else {
        print("Could not extract text via load_report. Path stored; provide text in " + kb_file)
        set_selected_text(arg, "")
    }
}
cmd_showpdf := func() {
    if selected_pdf_path == null or selected_pdf_path == "" { print("No PDF selected.") ; return }
    print("Selected PDF: " + selected_pdf_path)
    if selected_pdf_text != null and selected_pdf_text != "" { print("(text cached)") } else { print("(no cached text)") }
}
cmd_entropy := func() {
    if selected_pdf_path == null or selected_pdf_path == "" { print("No PDF selected. Use /setpdf"); return }
    text := selected_pdf_text
    if text == null or trim_s(text) == "" {
        print("No cached text: attempting extraction now.")
        txt := null
        try { txt := load_report(selected_pdf_path) } catch { txt := null }
        if txt != null and trim_s(txt) != "" { set_selected_text(selected_pdf_path, txt); text := txt }
    }
    if text == null or trim_s(text) == "" { print("No text available for analysis."); return }
    sections := infer_sections(text)
    agg := aggregate_section_stats(sections)
    print_entropy_analysis(selected_pdf_path, sections, agg)
}
cmd_ask := func(arg) {
    if arg == null or trim_s(arg) == "" { print("Usage: /ask <terms>"); return }
    if selected_pdf_text == null or trim_s(selected_pdf_text) == "" { print("No text available. Use /setpdf"); return }
    hits := []
    lines := split(selected_pdf_text, "\n")
    kws := split(trim_s(arg), " ")
    i := 0
    while i < len(lines) {
        line := trim_newlines(lines[i])
        ll := lower(line)
        j := 0
        matched := false
        while j < len(kws) {
            if kws[j] != "" and find(ll, lower(kws[j])) >= 0 { matched := true ; break }
            j := j + 1
        }
        if matched { hits := hits + [line] }
        i := i + 1
    }
    if len(hits) > 0 {
        print("Local matches:")
        i := 0
        while i < len(hits) and i < 10 { print("- " + hits[i]); i := i + 1 }
        return
    }
    if openai_chat != null {
        prompt := "Document:\n" + selected_pdf_text + "\nQUESTION:\n" + arg + "\nAnswer concisely."
        resp := openai_chat(prompt)
        if resp != null and trim_s(resp) != "" { print("OpenAI answer:"); print(trim_newlines(resp)); return }
    }
    print("No matches found.")
}

# Dispatcher
dispatch_line := func(line) {
    if line == null { return false }
    s := trim_newlines(line)
    if s == "" { return false }
    if substr(s,0,8) == "/setpdf " { cmd_setpdf(trim_s(substr(s,8,len(s))); return false }
    if s == "/showpdf" { cmd_showpdf(); return false }
    if s == "/entropy" { cmd_entropy(); return false }
    if substr(s,0,5) == "/ask " { cmd_ask(trim_s(substr(s,5,len(s)))); return false }
    if s == "/help" { print("Commands: /setpdf <path>, /showpdf, /entropy, /ask <terms>, /help, /quit"); return false }
    if s == "/quit" { print("Quit requested."); return true }
    print("Unknown command: " + s)
    return false
}

# Main loop (never exits unless /quit)
main := func() {
    # ensure command file exists
    if not file_exists(cmd_file) { safe_write(cmd_file, "") }
    print("Daemon started; monitoring " + cmd_file)
    processed := 0
    while true {
        content := safe_read(cmd_file)
        if content == null { content := "" }
        lines := split(content, "\n")
        i := processed
        quit_now := false
        while i < len(lines) {
            l := trim_newlines(lines[i])
            if l != "" {
                print("Executing: " + l)
                should_quit := dispatch_line(l)
                if should_quit { quit_now := true ; break }
            }
            i := i + 1
        }
        processed := len(lines)
        if quit_now { print("Exiting on /quit."); break }
        # light pause to avoid busy-loop:
        try { _ := safe_read(kb_file) } catch { }
        # If runtime supports sleep, uncomment below:
        # try { sleep(1) } catch { }
    }
}

main()
