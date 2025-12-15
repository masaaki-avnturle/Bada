# tiny_lang_entropy_demo_running.tl
# Practical runnable tiny_lang script that works even in non-interactive runtimes.
# Behavior:
#  - If interactive input is available, runs a REPL (commands documented below).
#  - If input returns null immediately (non-interactive), runs a self-demo:
#      * builds KB from embedded sample
#      * computes entropy for embedded PDF
#      * runs a sample /ask question and prints results
#
# Builtins assumed (defensive use):
#   print(s), input(prompt) -> string|null, file_write(path,content), file_read(path),
#   file_exists(path), split(s,sep), join(list,sep), trim(s), lower(s), find(hay,needle),
#   load_report(path) -> string|null (optional), http_get(url) -> string|null (optional),
#   openai_chat(prompt) -> string|null (optional), len(s), tostring(x)
#
# Save and run with tiny_lang_full or compatible interpreter.

# ---- Config / Embedded samples ----
kb_file      <- "tmp/tiny_kb.txt"
use_embedded <- true

#embedded_pdf_path <- "embedded_sample.pdf"   # logical name used in output
#embedded_pdf_text <- "Title: Convergence Theorem\n\nTitle\nA Simple Theorem on Sequences\n\nTheorem 1.\nFor every n, sequence a_n converges.\n\nProof.\nBy induction; base case trivial. Assume true for k, show for k+1.\nApply inequality and bound; limit follows.\n\nConcluded\nWe demonstrated convergence under mild conditions.\n\nConjecture\nExtension to multi-dimensional sequences likely holds under similar norms.\n"

#embedded_web_text <- "<html><body><h1>Demo Page</h1><p>This page describes an assistant that builds a KB and computes entropy of document sections.</p></body></html>"

# ---- Utilities ----
trim_newlines <- func(s) {
    if s == null { return "" }
    r <- s
    while len(r) > 0 and (r[-1] == '\n' or r[-1] == '\r') { r <- r[0:len(r)-1] }
    return r
}

# simple tokenize: alphanumeric sequences lowercased
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

# safe log2 using fallback via natural log if needed
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

# extract simple sections by headers (case-insensitive)
extract_sections <- func(text) {
    sections <- {}
    if text == null { return sections }
    low <- lower(text)
    # find positions of known headers
    headers <- [ "title", "theorem", "proof", "concluded", "conjecture" ]
    occs <- []
    i <- 0
    while i < len(headers) {
        h <- headers[i]
        # search for variants: "\n<h>" or "<h>:" or at start
        keys <- [ "\n" + h, h + ":", h + "\n", "\n" + h + "." ]
        j <- 0
        while j < len(keys) {
            idx <- find(low, keys[j])
            if idx >= 0 { occs <- occs + [ { "name": h, "pos": idx } ] ; break }
            j <- j + 1
        }
        i <- i + 1
    }
    # always include full
    sections["full"] <- text
    if len(occs) == 0 { return sections }
    # sort occs by pos
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
    # extract blocks
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
    # overall vocab size
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

# ---- KB build using embedded samples (or provided PDFs/URLs) ----
build_kb_embed <- func() {
    parts <- []
    parts <- parts + [ "=== EMBEDDED PDF: " + embedded_pdf_path + " ===\n" + embedded_pdf_text ]
    parts <- parts + [ "\n=== EMBEDDED WEB ===\n" + embedded_web_text ]
    full <- join(parts, "\n")
    file_write(kb_file, full)
    print("KB built at " + kb_file + " (embedded samples).")
}

# ---- Simple local search and answer ----
find_lines_matching <- func(text, keywords) {
    out <- []
    if text == null or text == "" { return out }
    lines <- split(text, "\n")
    lowkeys <- []
    i <- 0
    while i < len(keywords) {
        lowkeys <- lowkeys + [ lower(trim(keywords[i])) ]
        i <- i + 1
    }
    i <- 0
    while i < len(lines) {
        line <- lines[i]
        ll <- lower(line)
        j <- 0
        matched <- false
        while j < len(lowkeys) {
            if lowkeys[j] != "" and find(ll, lowkeys[j]) >= 0 { matched <- true; break }
            j <- j + 1
        }
        if matched { out <- out + [ trim_newlines(line) ] }
        i <- i + 1
    }
    return out
}

answer_question_local <- func(q) {
    if not file_exists(kb_file) { build_kb_embed() }
    kb <- file_read(kb_file)
    kws <- split(trim(q), " ")
    hits <- find_lines_matching(kb, kws)
    if len(hits) > 0 {
        print("Local extracts:")
        i <- 0
        while i < len(hits) and i < 8 {
            print("- " + hits[i])
            i <- i + 1
        }
        return
    }
    if openai_chat != null {
        prompt <- "CONTEXT:\n" + kb + "\nQUESTION:\n" + q + "\nANSWER:"
        resp <- openai_chat(prompt)
        if resp != null and trim(resp) != "" {
            print("OpenAI answer:")
            print(trim_newlines(resp))
            return
        }
    }
    print("No local information found and OpenAI unavailable or returned nothing.")
}

# ---- REPL: interactive commands ----
print_help <- func() {
    print("Commands:")
    print("  /build                   - build KB from embedded samples")
    print("  /entropy-embedded        - compute entropy for embedded PDF sample")
    print("  /ask <question>          - ask using local KB then OpenAI fallback")
    print("  /help /quit              - help/exit")
}

run_repl <- func() {
    print("Interactive mode. Type /help")
    while true {
        line <- input("assistant> ")
        if line == null { print("input returned null; exiting REPL."); break }
        cmd <- trim(line)
        if cmd == "" { continue }
        if cmd == "/quit" { break }
        if cmd == "/help" { print_help(); continue }
        if cmd == "/build" { build_kb_embed(); continue }
        if cmd == "/entropy-embedded" {
            res <- process_text_entropy(embedded_pdf_path, embedded_pdf_text)
            print_entropy_results(embedded_pdf_path, res)
            continue
        }
        if substr(cmd, 0, 5) == "/ask " {
            q <- trim(substr(cmd, 5, len(cmd)))
            if q == "" { print("Provide question after /ask"); continue }
            answer_question_local(q)
            continue
        }
        print("Unknown command. Type /help")
    }
    print("Goodbye.")
}

# ---- Non-interactive demo sequence ----
run_demo_once <- func() {
    print("Non-interactive environment detected. Running self-demo...")
    build_kb_embed()
    # compute entropy for embedded PDF
    res <- process_text_entropy(embedded_pdf_path, embedded_pdf_text)
    print_entropy_results(embedded_pdf_path, res)
    # perform a sample question
    print("\nSample question: 'What does the paper conclude about convergence?'")
    answer_question_local("conclude convergence")
    print("Demo finished. Goodbye.")
}

# ---- Entrypoint: detect interactivity by performing a single input() check ----
main <- func() {
    # try a non-blocking input probe; some runtimes return null immediately
    probe <- input("")   # empty prompt; may block in interactive shells
    if probe == null {
        # non-interactive or EOF: run demo
        run_demo_once()
        return
    }
    # if probe returned a string, treat it as the first command (unless empty)
    first_cmd <- trim(probe)
    if first_cmd == "" {
        # continue into REPL
        run_repl()
        return
    }
    # handle first command then REPL
    # push the first command by executing it
    if first_cmd == "/quit" { print("Goodbye."); return }
    if first_cmd == "/help" { print_help(); run_repl(); return }
    if first_cmd == "/build" { build_kb_embed(); run_repl(); return }
    if first_cmd == "/entropy-embedded" {
        res <- process_text_entropy(embedded_pdf_path, embedded_pdf_text)
        print_entropy_results(embedded_pdf_path, res)
        run_repl()
        return
    }
    if substr(first_cmd, 0, 5) == "/ask " {
        q <- trim(substr(first_cmd, 5, len(first_cmd)))
        answer_question_local(q)
        run_repl()
        return
    }
    # unknown first command -> start REPL
    print("First input unknown; entering REPL. Type /help")
    run_repl()
}

# run
main()
