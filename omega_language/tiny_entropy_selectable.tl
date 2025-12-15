# tiny_lang_entropy_selectable.tl
# Allows selecting any PDF file to analyze entropy via /setpdf <path> and /entropy-embedded.
# If the selected PDF can't be read, falls back to an embedded sample.
#
# Required runtime builtins (defensive use):
#   input(prompt), print(s), file_exists(path), load_report(path) -> string|null,
#   file_write(path,content), file_read(path), split(s,sep), join(list,sep), trim(s),
#   lower(s), find(hay,needle), len(s), tostring(x)
#
# Commands:
#  /setpdf <path>        - select a PDF file to analyze
#  /showpdf              - show current selected PDF path
#  /entropy-embedded     - compute entropy report for selected PDF (or embedded fallback)
#  /buildkb              - write KB file combining PDF and embedded web sample
#  /help /quit           - help/exit

# ---- State ----
kb_file              <- "tmp/tiny_kb.txt"
selected_pdf_path    <- ""            # user-set path via /setpdf
selected_pdf_text    <- ""            # cached extracted text (or empty)
use_embedded_sample  <- true

# ---- Embedded fallback sample ----
#embedded_pdf_path <- "embedded_sample_paper.pdf"
embedded_pdf_path <- "caostics.pdf"
embedded_pdf_text <- "Title: Convergence Theorem\n\nTitle\nA Simple Theorem on Sequences\n\nTheorem 1.\nFor every n, sequence a_n converges under mild assumptions.\n\nProof.\nBy induction; base case trivial. Assume true for k, show for k+1. Use inequality bounds to conclude.\n\nConcluded\nWe demonstrated convergence under mild conditions.\n\nConjecture\nExtension to multi-dimensional sequences likely holds under similar norm conditions.\n"

embedded_web_text <- "<html><body><h1>Demo Page</h1><p>Assistant builds KB and computes entropy of document sections.</p></body></html>"

# ---- Utilities ----
trim_newlines <- func(s) {
    if s == null { return "" }
    r <- s
    while len(r) > 0 and (r[-1] == '\n' or r[-1] == '\r') { r <- r[0:len(r)-1] }
    return r
}

tokenize <- func(s) {
    toks <- []
    if s == null { return toks }
    cur <- ""
    i <- 0
    while i < len(s) {
        c <- s[i]
        isalnum <- false
        if (c >= '0' and c <= '9') or (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z') or c == '_' {
            isalnum <- true
        }
        if isalnum {
            cur <- cur + lower(c)
        } else {
            if cur != "" { toks <- toks + [cur]; cur <- "" }
        }
        i <- i + 1
    }
    if cur != "" { toks <- toks + [cur] }
    return toks
}

freq_map <- func(tokens) {
    m <- {}
    if tokens == null { return m }
    i <- 0
    while i < len(tokens) {
        t <- tokens[i]
        if m[t] == null { m[t] <- 1 } else { m[t] <- m[t] + 1 }
        i <- i + 1
    }
    return m
}

log2 <- func(x) {
    if x <= 0 { return 0.0 }
    try_val <- null
    try {
        try_val <- log(x, 2)
    } catch {
        try_val <- log(x) / log(2)
    }
    return try_val
}

entropy_tokens <- func(tokens) {
    if tokens == null { return 0.0 }
    n <- len(tokens)
    if n == 0 { return 0.0 }
    m <- freq_map(tokens)
    H <- 0.0
    for k in m {
        cnt <- m[k]
        p <- cnt / n
        if p > 0 { H <- H - p * log2(p) }
    }
    return H
}

# ---- Section extraction ----
extract_sections <- func(text) {
    sections <- {}
    if text == null { return sections }
    low <- lower(text)
    headers <- [ "title", "theorem", "proof", "concluded", "conjecture" ]
    occs <- []
    i <- 0
    while i < len(headers) {
        h <- headers[i]
        keys <- [ "\n" + h, h + ":", h + "\n", "\n" + h + "." ]
        j <- 0
        while j < len(keys) {
            idx <- find(low, keys[j])
            if idx >= 0 { occs <- occs + [ { "name": h, "pos": idx } ]; break }
            j <- j + 1
        }
        i <- i + 1
    }
    sections["full"] <- text
    if len(occs) == 0 { return sections }
    # sort occs
    k <- 0
    while k < len(occs) {
        l <- k + 1
        while l < len(occs) {
            if occs[l]["pos"] < occs[k]["pos"] {
                tmp <- occs[k]; occs[k] <- occs[l]; occs[l] <- tmp
            }
            l <- l + 1
        }
        k <- k + 1
    }
    i <- 0
    while i < len(occs) {
        name <- occs[i]["name"]
        start <- occs[i]["pos"]
        end <- len(text)
        if i + 1 < len(occs) { end <- occs[i+1]["pos"] }
        blk <- trim_newlines(text[start:end])
        sections[name] <- blk
        i <- i + 1
    }
    return sections
}

process_text_entropy <- func(label, text) {
    secs <- extract_sections(text)
    results <- {}
    total_vocab <- {}
    for k in secs {
        s <- secs[k]
        toks <- tokenize(s)
        H <- entropy_tokens(toks)
        vocab_size <- 0
        if toks != null and len(toks) > 0 {
            fm <- freq_map(toks)
            for key in fm { vocab_size <- vocab_size + 1; total_vocab[key] <- 1 }
        }
        results[k] <- { "entropy": H, "tokens": len(toks), "vocab": vocab_size }
    }
    totv <- 0
    for key in total_vocab { totv <- totv + 1 }
    results["summary"] <- { "label": label, "total_vocab": totv }
    return results
}

print_entropy_results <- func(path_label, res) {
    print("Entropy report for: " + path_label)
    order <- [ "title", "theorem", "proof", "concluded", "conjecture", "full" ]
    i <- 0
    while i < len(order) {
        n <- order[i]
        if res[n] != null {
            info <- res[n]
            ent <- info["entropy"]
            toks <- info["tokens"]
            vocab <- info["vocab"]
            norm <- 0.0
            if vocab > 1 { norm <- ent / log2(vocab) }
            print("- " + n + ": entropy=" + tostring(ent) + ", tokens=" + tostring(toks) + ", vocab=" + tostring(vocab) + ", normalized=" + tostring(norm))
        } else {
            print("- " + n + ": (not present)")
        }
        i <- i + 1
    }
    print("-- summary: total_vocab=" + tostring(res["summary"]["total_vocab"]))
}

# ---- Operations: select PDF, load text, build KB, analyze ----
set_pdf <- func(path) {
    if path == null or trim(path) == "" { print("Provide a PDF path."); return }
    selected_pdf_path <- trim(path)
    # try extracting text
    txt <- null
    try {
        txt <- load_report(selected_pdf_path)
    } catch {
        txt <- null
    }
    if txt == null or trim(txt) == "" {
        selected_pdf_text <- ""   # clear cache; will fallback to embedded
        print("Could not extract text from: " + selected_pdf_path + " (keep path but will use embedded fallback).")
    } else {
        selected_pdf_text <- txt
        print("PDF text extracted and cached for: " + selected_pdf_path)
    }
}

show_pdf <- func() {
    if selected_pdf_path == "" { print("No PDF selected. Use /setpdf <path>") }
    else {
        print("Selected PDF: " + selected_pdf_path)
        if selected_pdf_text != "" { print("(text cached)"); } else { print("(no cached text; will attempt extraction when analyzing)") }
    }
}

get_pdf_text_for_analysis <- func() {
    if selected_pdf_path != "" {
        # prefer cached text
        if selected_pdf_text != "" { return { "path": selected_pdf_path, "text": selected_pdf_text } }
        # try extracting now
        txt <- null
        try {
            txt <- load_report(selected_pdf_path)
        } catch {
            txt <- null
        }
        if txt != null and trim(txt) != "" { selected_pdf_text <- txt; return { "path": selected_pdf_path, "text": txt } }
        # extraction failed
        if use_embedded_sample {
            return { "path": embedded_pdf_path + " (embedded fallback)", "text": embedded_pdf_text }
        }
        return { "path": selected_pdf_path, "text": "" }
    }
    # no selected PDF -> embedded if allowed
    if use_embedded_sample { return { "path": embedded_pdf_path + " (embedded)", "text": embedded_pdf_text } }
    return { "path": "(none)", "text": "" }
}

build_kb <- func() {
    p <- get_pdf_text_for_analysis()
    parts <- []
    parts <- parts + [ "=== PDF: " + p["path"] + " ===\n" + p["text"] ]
    parts <- parts + [ "\n=== WEB FALLBACK ===\n" + embedded_web_text ]
    full <- join(parts, "\n")
    file_write(kb_file, full)
    print("KB built at " + kb_file)
}

entropy_for_selected <- func() {
    p <- get_pdf_text_for_analysis()
    if p["text"] == null or trim(p["text"]) == "" {
        print("No PDF text available to analyze.")
        return
    }
    res <- process_text_entropy(p["path"], p["text"])
    print_entropy_results(p["path"], res)
}

# ---- REPL ----
print_help <- func() {
    print("Commands:")
    print("  /setpdf <path>     - set PDF path (tries to extract and cache text)")
    print("  /showpdf           - show currently selected PDF")
    print("  /buildkb           - build KB combining PDF and web fallback")
    print("  /entropy-embedded  - compute entropy report for selected PDF (or embedded fallback)")
    print("  /help /quit        - help/exit")
}

run_repl <- func() {
    print("Entropy assistant. Type /help")
    while true {
        line <- input("assistant> ")
        if line == null { print("input returned null; exiting."); break }
        cmd <- trim(line)
        if cmd == "" { continue }
        if cmd == "/quit" { break }
        if cmd == "/help" { print_help(); continue }
        if substr(cmd, 0, 8) == "/setpdf " {
            set_pdf(substr(cmd, 8, len(cmd)))
            continue
        }
        if cmd == "/showpdf" { show_pdf(); continue }
        if cmd == "/buildkb" { build_kb(); continue }
        if cmd == "/entropy-embedded" { entropy_for_selected(); continue }
        print("Unknown command. Type /help")
    }
    print("Goodbye.")
}

# ---- Entry ----
main <- func() {
    # start REPL (probe input once)
    probe <- input("")
    if probe == null {
        # non-interactive: run a demo using embedded fallback
        print("Non-interactive: running demo using embedded fallback.")
        build_kb()
        entropy_for_selected()
        print("Demo finished. Goodbye.")
        return
    }
    # if probe contains a command, execute it then enter REPL
    first_cmd <- trim(probe)
    if first_cmd != "" {
        if first_cmd == "/quit" { print("Goodbye."); return }
        if substr(first_cmd, 0, 8) == "/setpdf " { set_pdf(substr(first_cmd, 8, len(first_cmd))) }
        else if first_cmd == "/showpdf" { show_pdf() }
        else if first_cmd == "/buildkb" { build_kb() }
        else if first_cmd == "/entropy-embedded" { entropy_for_selected() }
        else { print("First command not recognized; entering REPL.") }
    }
    run_repl()
}

# Run
main()
