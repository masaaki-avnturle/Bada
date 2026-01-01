# tiny_daemon_reload_ask.tl
# Simple tiny_lang daemon:
# - /reload <path> : load PDF text via load_report(path) and cache
# - /ask "<question>" : try to answer from cached text (local search); if not found, call openai_chat(prompt) if available
# - /help, /quit supported
#
# Write commands to /tmp/tiny_commands.txt (append). Daemon monitors file and does not exit unless /quit.

cmd_file <- "/tmp/tiny_commands.txt"
kb_file  <- "/tmp/tiny_kb.txt"

pdf_path <- "~/file/"
pdf_text <- "~/file/"

# --- utils ---
trim := func(s) { if s == null { return "" } ; return s }
trim_newlines := func(s) { if s == null { return "" } ; r := s ; while len(r)>0 and (r[-1]=='\n' or r[-1]=='\r') { r := r[0:len(r)-1] } ; return r }
safe_read := func(p) { try { return file_read(p) } catch { return null } }
safe_write := func(p,t) { try { file_write(p,t) } catch { } }
split_lines := func(s) { if s==null { return [] } ; return split(s, "\n") }
lower_trim := func(s) { if s==null { return "" } ; return lower(trim(s)) }

# --- simple sentence splitter ---
split_sentences := func(text) {
    out := []
    if text == null { return out }
    # naive: split on period / question / exclamation followed by space or linebreak
    parts := split(text, "\n")
    i := 0
    while i < len(parts) {
        line := trim_newlines(parts[i])
        if line == "" { i := i + 1 ; continue }
        # break line into sentences by common punctuation
        buf := ""
        j := 0
        while j < len(line) {
            c := line[j]
            buf := buf + c
            if c == '.' or c == '?' or c == '!' {
                out := out + [trim_newlines(buf)]
                buf := ""
            }
            j := j + 1
        }
        if buf != "" { out := out + [trim_newlines(buf)] }
        i := i + 1
    }
    return out
}

# --- load PDF text ---
load_pdf := func(path) {
    if path == null or trim(path) == "" { print("Usage: /reload <path>"); return false }
    print("[CMD] reload " + path)
    txt := null
    try { txt := load_report(path) } catch { txt := null }
    if txt != null and trim(txt) != "" {
        pdf_path := path
        pdf_text := txt
        safe_write(kb_file, "=== PDF: " + path + " ===\n" + txt)
        print("[OK] PDF loaded: " + path + " (chars=" + tostring(len(txt)) + ")")
        return true
    } else {
        pdf_path := path
        pdf_text := ""
        print("[WARN] load_report failed or returned empty text. Path stored; you can place text into " + kb_file)
        return false
    }
}

# --- local answer: keyword search then context extraction ---
find_local_answer := func(question) {
    if pdf_text == null or trim(pdf_text) == "" { return null }
    qlow := lower_trim(question)
    # keywords: split question to words excluding common short words
    toks := split(qlow, " ")
    kws := []
    i := 0
    while i < len(toks) {
        t := toks[i]
        if len(t) >= 3 and t != "the" and t != "and" and t != "for" and t != "with" { kws := kws + [t] }
        i := i + 1
    }
    if len(kws) == 0 { kws := toks } # fallback
    sents := split_sentences(pdf_text)
    matches := []
    i := 0
    while i < len(sents) {
        s := sents[i]
        sl := lower_trim(s)
        j := 0
        found := true
        # require at least one keyword match (or all if few keywords)
        matched_any := false
        while j < len(kws) {
            if find(sl, kws[j]) >= 0 { matched_any := true }
            j := j + 1
        }
        if matched_any { matches := matches + [s] }
        i := i + 1
    }
    if len(matches) == 0 { return null }
    # return top few sentences concatenated
    out := ""
    i := 0
    while i < len(matches) and i < 4 {
        out := out + matches[i] + " "
        i := i + 1
    }
    return trim_newlines(out)
}

# --- remote fallback using openai_chat if available ---
ask_via_openai := func(question) {
    if openai_chat == null { return null }
    prompt := "You are given a document below. Answer the question concisely.\n\nDOCUMENT:\n" + (if pdf_text==null then "" else pdf_text) + "\n\nQUESTION:\n" + question + "\n\nAnswer:"
    resp := null
    try { resp := openai_chat(prompt) } catch { resp := null }
    if resp == null or trim(resp) == "" { return null }
    return trim_newlines(resp)
}

# --- command dispatcher ---
dispatch := func(line) {
    if line == null { return false }
    s := trim_newlines(line)
    if s == "" { return false }
    if starts_with(s, "/reload ") { path := trim(substr(s,8,len(s))) ; load_pdf(path) ; return false }
    if starts_with(s, "/ask ") {
        arg := trim(substr(s,5,len(s)))
        # allow quotes
        if starts_with(arg, "\"") and substr(arg, len(arg)-1, lenu(arg)) == "\"" { arg := substr(arg,1,len(arg)-1) }
        if arg == "" { print("Usage: /ask \"question\""); return false }
        print("[CMD] ask: " + arg)
        # try local
        local := null
        try { local := find_local_answer(arg) } catch { local := null }
        if local != null and trim(local) != "" {
            print("[LOCAL ANSWER]")
            print(local)
            return false
        }
        # fallback to openai_chat if available
        remote := null
        try { remote := ask_via_openai(arg) } catch { remote := null }
        if remote != null and trim(remote) != "" {
            print("[OPENAI ANSWER]")
            print(remote)
            return false
        }
        print("No answer found locally; no remote responder available or returned empty.")
        return false
    }
    if s == "/help" { print("Commands: /reload <path>, /ask \"question\", /help, /quit") ; return false }
    if s == "/quit" { print("Quit requested.") ; return true }
    print("Unknown command: " + s)
    return false
}

# helper starts_with (not standard in some tiny_lang)
starts_with := func(s,p) { if s==null or p==null { return false } ; if len(s) < len(p) { return false } ; return substr(s,0,len(p)) == p }

# --- main loop ---
main := func() {
    if not file_exists(cmd_file) { safe_write(cmd_file, "") }
    print("Daemon started. Monitor " + cmd_file)
    processed := 0
    while true {
        content := safe_read(cmd_file)
        if content == null { content := "" }
        lines := split(content, "\n")
        i := processed
        quit := false
        while i < len(lines) {
            l := trim_newlines(lines[i])
            if l != "" {
                print("Executing: " + l)
                ok := false
                try { ok := dispatch(l) } catch { ok := false ; print("Error dispatching: " + l) }
                if ok { quit := true ; break }
            }
            i := i + 1
        }
        processed := len(lines)
        if quit { break }
        try { sleep(1) } catch { try { _ := safe_read(kb_file) } catch { } }
    }
    print("Daemon exiting.")
}

main()

#使用例（別端末で実行）:
#- echo "/reload /full/path/to/sample.pdf" >> /tmp/tiny_commands.txt
#- echo "/ask \"What is the main result?\"" >> /tmp/tiny_commands.txt
#
#注:
#- 環境に `load_report(path)` が無ければ pdf_text を手動で `/tmp/tiny_kb.txt` に置いてください。
#- `openai_chat` があれば自動でフォールバックしてより自然な応答を返します。
