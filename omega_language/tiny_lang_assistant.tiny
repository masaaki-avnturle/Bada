# tiny_lang_entropy_assistant.tl
# Purpose: practical tiny_lang assistant that:
#  - loads PDF text (via `load_report`) and web pages (`http_get`)
#  - extracts document sections: title, theorem, proof, concluded, conjecture
#  - computes Shannon entropy for each section and overall
#  - answers questions using local KB (PDFs + webpages) and OpenAI fallback
#
# Assumptions (runtime builtins):
#   input(prompt), print(s), file_read(path), file_write(path,content), file_exists(path)
#   split(s, sep), join(list, sep), trim(s), lower(s), find(hay, needle)
#   load_report(path) -> string | null    # extracts text from a PDF
#   http_get(url) -> string | null
#   openai_chat(prompt) -> string | null
#   length(s) -> int
#   log(x, base) -> float   # if not present, we compute log2 via ln / ln2 fallback
#
# Notes:
#   - Shannon entropy H = -sum_i p_i * log2(p_i), where p_i is token probability.
#   - Tokens computed by simple whitespace + punctuation split (sufficient for demo).
#   - Defensive checks included (nulls, empty sections).
#
# Save and run with tiny_lang_full or compatible interpreter.

# ---- Config/state ----
kb_file        <- "tmp/tiny_kb.txt"
session_pdfs   <- []          # list of PDF paths
session_urls   <- []          # list of URLs
use_embedded   <- true        # provide embedded sample if no sources

# ---- Embedded sample PDF text (fallback) ----
sample_pdf <- "Title: Sample Theorem Paper\n\nTitle\nA Simple Theorem on Sequences\n\nTheorem 1.\nFor every n, sequence a_n converges.\n\nProof.\nBy induction; base case trivial. Assume true for k, show for k+1.\nApply inequality and bound; limit follows.\n\nConcluded\nWe demonstrated convergence under mild conditions.\n\nConjecture\nExtension to multi-dimensional sequences likely holds under similar norms.\n"

# ---- Utilities ----
trim_newlines <- func(s) {
    if s == null { return "" }
    r <- s
    while len(r) > 0 and (r[-1] == '\n' or r[-1] == '\r') { r <- r[0:len(r)-1] }
    return r
}

safe_lower <- func(s) { if s == null { return "" } else { return lower(s) } }

# split into tokens: simple split on non-alphanumeric characters
tokenize <- func(s) {
    out <- []
    if s == null { return out }
    cur <- ""
    i <- 0
    while i < len(s) {
        c <- s[i]
        isalnum <- false
        # check alnum (letters or digits, underscore treated as letter)
        if (c >= '0' and c <= '9') or (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z') or c == '_' {
            isalnum <- true
        }
        if isalnum {
            cur <- cur + lower(c)
        } else {
            if cur != "" { out <- out + [cur]; cur <- "" }
        }
        i <- i + 1
    }
    if cur != "" { out <- out + [cur] }
    return out
}

# compute frequency map from token list
freq_map <- func(tokens) {
    m <- {}    # assume runtime supports dict-like literal; if not, emulate with two lists
    if tokens == null { return m }
    i <- 0
    while i < len(tokens) {
        t <- tokens[i]
        if m[t] == null { m[t] <- 1 } else { m[t] <- m[t] + 1 }
        i <- i + 1
    }
    return m
}

# compute log2, using ln fallback if log base param not present
log2 <- func(x) {
    if x <= 0 { return 0.0 }
    # prefer built-in log with base param; else use natural log / ln2
    # try call: log(x, 2) defensively
    try_val <- null
    try {
        try_val <- log(x, 2)
    } catch {
        # compute using ln: ln(x) / ln(2)
        try_val <- log(x) / log(2)
    }
    return try_val
}

# Shannon entropy calculation for token list
entropy_tokens <- func(tokens) {
    if tokens == null { return 0.0 }
    n <- len(tokens)
    if n == 0 { return 0.0 }
    m <- freq_map(tokens)
    H <- 0.0
    # iterate keys
    for key in m {
        cnt <- m[key]
        p <- cnt / n
        if p > 0 {
            H <- H - p * log2(p)
        }
    }
    return H
}

# normalized entropy: H / log2(V) where V = vocabulary size (max entropy)
normalized_entropy <- func(H, vocab_size) {
    if vocab_size <= 1 { return 0.0 }
    return H / log2(vocab_size)
}

# ---- Section extraction from text ----
# Looks for section headers (case-insensitive) and extracts block until next header or end.
extract_sections <- func(text) {
    sections <- {}        # map: name -> string
    if text == null { return sections }
    low <- lower(text)
    # header positions
    headers <- [ ["title", ["\ntitle", "title:"] ],
                 ["theorem", ["\ntheorem", "theorem."] ],
                 ["proof", ["\nproof", "proof."] ],
                 ["concluded", ["\nconcluded", "conclusion", "\nconclusion", "concluded."] ],
                 ["conjecture", ["\nconjecture", "conjecture."] ] ]
    # default entire text as 'full'
    sections["full"] <- text

    i <- 0
    # find indices of header occurrences
    occs <- []
    while i < len(headers) {
        name <- headers[i][0]
        keys <- headers[i][1]
        j <- 0
        while j < len(keys) {
            key <- keys[j]
            idx <- find(low, key)
            if idx >= 0 {
                occs <- occs + [ { "name": name, "pos": idx + 1 } ]  # +1 to skip leading newline
            }
            j <- j + 1
        }
        i <- i + 1
    }
    # sort occs by position
    # Assume runtime provides sort; if not, simple bubble sort
    k <- 0
    while k < len(occs) {
        l <- k + 1
        while l < len(occs) {
            if occs[l]["pos"] < occs[k]["pos"] {
                tmp <- occs[k]
                occs[k] <- occs[l]
                occs[l] <- tmp
            }
            l <- l + 1
        }
        k <- k + 1
    }
    # Extract blocks between positions
    if len(occs) == 0 { return sections }
    i <- 0
    while i < len(occs) {
        name <- occs[i]["name"]
        start <- occs[i]["pos"]
        end <- len(text)
        if i + 1 < len(occs) { end <- occs[i+1]["pos"] - 1 }
        blk <- trim_newlines(substr(text, start, end))
        sections[name] <- blk
        i <- i + 1
    }
    return sections
}

# safe substring using runtime substr
substr <- func(s, a, b) {
    if s == null { return "" }
    if a < 0 { a <- 0 }
    if b < a { return "" }
    if a >= len(s) { return "" }
    if b > len(s) { b <- len(s) }
    return s[a:b]
}

# ---- Process a PDF: extract text, parse sections, compute entropies ----
process_pdf_entropy <- func(path) {
    out <- {}   # map to return
    txt <- load_report(path)
    if txt == null or trim(txt) == "" {
        # fallback to embedded sample if allowed
        if use_embedded {
            txt <- sample_pdf
            print("Using embedded sample PDF text as fallback.")
        } else {
            print("Failed to extract text from: " + path)
            return null
        }
    }
    # parse
    sections <- extract_sections(txt)
    # ensure some sections exist; if not, treat whole doc as 'full'
    if sections == null or len(sections) == 0 {
        sections <- { "full": txt }
    } else {
        # ensure full present
        if sections["full"] == null { sections["full"] <- txt }
    }
    # compute entropy per section
    results <- {}
    total_vocab <- {}   # collect vocabulary across sections
    for k in sections {
        stext <- sections[k]
        toks <- tokenize(stext)
        H <- entropy_tokens(toks)
        vocab_size <- 0
        if toks != null and len(toks) > 0 {
            vm <- freq_map(toks)
            # count keys
            vocab_size <- 0
            for key in vm { vocab_size <- vocab_size + 1 }
            # collect into total_vocab
            for key in vm { total_vocab[key] <- 1 }
        } else {
            vocab_size <- 0
        }
        nlen <- len(toks)
        results[k] <- { "entropy": H, "tokens": nlen, "vocab": vocab_size }
    }
    # overall entropy computed on full doc tokens
    full_toks <- tokenize(sections["full"])
    overall_H <- entropy_tokens(full_toks)
    # overall vocab size:
    total_vocab_size <- 0
    for key in total_vocab { total_vocab_size <- total_vocab_size + 1 }
    results["overall"] <- { "entropy": overall_H, "tokens": len(full_toks), "vocab": total_vocab_size }
    out["path"] <- path
    out["sections"] <- results
    out["raw_sections"] <- sections
    return out
}

# ---- Answer logic: compute entropy and reply in human-friendly form ----
reply_entropy_report <- func(path) {
    res <- process_pdf_entropy(path)
    if res == null { print("Could not process PDF."); return }
    print("Entropy report for: " + res["path"])
    secs <- res["sections"]
    # print each requested section: title, theorem, proof, concluded, conjecture, overall
    order <- ["title", "theorem", "proof", "concluded", "conjecture", "overall"]
    for name in order {
        if secs[name] != null {
            info <- secs[name]
            ent <- info["entropy"]
            toks <- info["tokens"]
            vocab <- info["vocab"]
            # normalized entropy (divide by log2(vocab) if vocab>1)
            norm <- 0.0
            if vocab > 1 { norm <- ent / log2(vocab) }
            print("- " + name + ": entropy=" + tostring(ent) + ", tokens=" + tostring(toks) + ", vocab=" + tostring(vocab) + ", normalized=" + tostring(norm))
        } else {
            print("- " + name + ": (not present)")
        }
    }
    # Optionally show short raw extracts for sections found
    print("\nShort extracts (first 200 chars) for present sections:")
    for key in res["raw_sections"] {
        s <- res["raw_sections"][key]
        preview <- s[0:200]
        print("[" + key + "] " + trim_newlines(preview) + ( (len(s) > 200) ? "..." : "" ))
    }
}

# ---- KB build (PDFs + web pages merged) ----
build_kb <- func() {
    parts <- []
    # add all PDFs
    i <- 0
    while i < len(session_pdfs) {
        p <- session_pdfs[i]
        txt <- load_report(p)
        if txt == null or trim(txt) == "" {
            if use_embedded {
                txt <- sample_pdf
            } else {
                txt <- "(empty PDF: " + p + ")"
            }
        }
        parts <- parts + [ "\n=== PDF: " + p + " ===\n" + txt ]
        i <- i + 1
    }
    if len(session_pdfs) == 0 and use_embedded {
        parts <- parts + [ "\n=== EMBEDDED SAMPLE PDF ===\n" + sample_pdf ]
    }
    # add webpages
    i <- 0
    while i < len(session_urls) {
        u <- session_urls[i]
        pg <- http_get(u)
        if pg == null or trim(pg) == "" {
            pg <- "(failed to fetch: " + u + ")"
        }
        parts <- parts + [ "\n=== URL: " + u + " ===\n" + pg ]
        i <- i + 1
    }
    full <- join(parts, "\n")
    ok <- file_write(kb_file, full)
    if ok { print("KB built at " + kb_file) } else { print("Failed writing KB.") }
}

# ---- Simple search and answer via local KB then OpenAI fallback ----
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

answer_question <- func(question) {
    if question == null or trim(question) == "" { print("Empty question."); return }
    # if KB missing, build
    if not file_exists(kb_file) { build_kb() }
    kb <- file_read(kb_file)
    if kb == null { kb <- "" }
    kws <- split(trim(question), " ")
    hits <- find_lines_matching(kb, kws)
    if len(hits) > 0 {
        print("Local extracts:")
        i <- 0
        while i < len(hits) and i < 10 {
            print("- " + hits[i])
            i <- i + 1
        }
        print("You can also request /entropy <pdfpath> to get entropy metrics for a PDF.")
        return
    }
    # fallback to OpenAI
    if openai_chat != null {
        prompt <- "Use the CONTEXT below (KB) to answer concisely.\n\nCONTEXT:\n" + kb + "\n\nQUESTION:\n" + question + "\n\nANSWER:"
        resp <- openai_chat(prompt)
        if resp == null or trim(resp) == "" { print("OpenAI returned no answer.") } else { print(trim_newlines(resp)) }
    } else {
        print("No local matches and OpenAI not available.")
    }
}

# ---- Command parsing and REPL ----
print_help <- func() {
    print("Commands:")
    print("  /use reports=path1,path2 urls=url1,url2   - set session sources")
    print("  /build                                   - build KB from sources")
    print("  /entropy <pdfpath>                       - compute entropy report for PDF")
    print("  /ask <question>                          - ask using KB then OpenAI fallback")
    print("  /help /quit                              - help/exit")
}

set_session_from_arg <- func(argstr) {
    if argstr == null { return }
    s <- trim(argstr)
    if s == "" { return }
    uidx <- find(s, "urls=")
    ridx <- find(s, "reports=")
    if uidx >= 0 {
        start <- uidx + 5
        end <- len(s)
        if ridx >= 0 and ridx > uidx { end <- ridx }
        sub <- trim(substr(s, start, end))
        session_urls <- split(sub, ",")
    }
    if ridx >= 0 {
        start <- ridx + 8
        end <- len(s)
        if uidx >= 0 and uidx > ridx { end <- uidx }
        sub <- trim(substr(s, start, end))
        session_pdfs <- split(sub, ",")
    }
    print("Session PDFs: " + join(session_pdfs, ","))
    print("Session URLs: " + join(session_urls, ","))
}

main <- func() {
    print("Entropy-aware tiny_lang assistant. Type /help")
    while true {
        line <- input("assistant> ")
        if line == null { break }
        cmd <- trim(line)
        if cmd == "" { continue }
        if cmd == "/quit" { break }
        if cmd == "/help" { print_help(); continue }
        if substr(cmd, 0, 5) == "/use " {
            set_session_from_arg(substr(cmd, 5, len(cmd)))
            continue
        }
        if cmd == "/build" { build_kb(); continue }
        if substr(cmd, 0, 9) == "/entropy " {
            path <- trim(substr(cmd, 9, len(cmd)))
            if path == "" { print("Specify PDF path. Example: /entropy mypaper.pdf"); continue }
            reply_entropy_report(path)
            continue
        }
        if substr(cmd, 0, 5) == "/ask " {
            q <- trim(substr(cmd, 5, len(cmd)))
            answer_question(q)
            continue
        }
        print("Unknown command. Type /help")
    }
    print("Goodbye.")
}

# run
main()
