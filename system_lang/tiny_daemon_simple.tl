# tiny_simple_text_daemon.tl
cmd_file   <- "/tmp/tiny_commands.txt"
state_file <- "/tmp/tiny_state.txt"

safe_read := func(p) { try { return file_read(p) } catch { return null } }
safe_write := func(p,t) { try { file_write(p,t) } catch { } }
exists := func(p) { try { return file_exists(p) } catch { return false } }

trim := func(s) { if s==null { return "" } ; return s }
trim_newlines := func(s) { if s==null { return "" } ; r:=s ; while len(r)>0 and (r[-1]=='\n' or r[-1]=='\r') { r := r[0:len(r)-1] } ; return r }
lower_trim := func(s) { return lower(trim(s)) }
starts_with := func(s,p) { if s==null or p==null { return false } ; if len(s) < len(p) { return false } ; return substr(s,0,len(p)) == p }

# state: first line = path, rest = text
read_state := func() {
    txt := safe_read(state_file)
    if txt == null { return { "path": "", "text": "" } }
    parts := split(txt, "\n")
    if len(parts) == 0 { return { "path": "", "text": "" } }
    p := trim_newlines(parts[0])
    rest := ""
    i := 1
    while i < len(parts) {
        rest := rest + parts[i]
        if i < len(parts)-1 { rest := rest + "\n" }
        i := i + 1
    }
    return { "path": p, "text": rest }
}
write_state := func(path, text) { safe_write(state_file, tostring(path) + "\n" + tostring(text)) }

# simple sentence splitter
split_sentences := func(text) {
    out := []
    if text==null or trim(text)=="" { return out }
    lines := split(text, "\n")
    i := 0
    while i < len(lines) {
        line := trim_newlines(lines[i])
        if line == "" { i := i + 1 ; continue }
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

# load text: read given path; if path ends with .pdf try same name .txt
load_text_file := func(path) {
    if path==null or trim(path)=="" { return null }
    t := safe_read(path)
    if t != null and trim(t) != "" { return t }
    # if .pdf, try .txt sibling
    if find(lower_trim(path), ".pdf") >= 0 {
        alt := substr(path,0,len(path)-4) + ".txt"
        t2 := safe_read(alt)
        if t2 != null and trim(t2) != "" { return t2 }
    }
    return null
}

# local answer search: keyword match on sentences
find_local_answer := func(question, doctext) {
    if doctext==null or trim(doctext)=="" { return null }
    q := lower_trim(question)
    parts := split(q, " ")
    kws := []
    i := 0
    while i < len(parts) {
        t := parts[i]
        if len(t) >= 3 { kws := kws + [t] }
        i := i + 1
    }
    if len(kws) == 0 { kws := parts }
    sents := split_sentences(doctext)
    hits := []
    i := 0
    while i < len(sents) {
        s := sents[i]
        sl := lower_trim(s)
        j := 0
        matched := false
        while j < len(kws) {
            if kws[j] != "" and find(sl, kws[j]) >= 0 { matched := true ; break }
            j := j + 1
        }
        if matched { hits := hits + [s] }
        i := i + 1
    }
    if len(hits) == 0 { return null }
    out := ""
    i := 0
    while i < len(hits) and i < 6 {
        out := out + hits[i] + " "
        i := i + 1
    }
    return trim_newlines(out)
}

# commands
cmd_reload := func(arg) {
    path := trim(arg)
    if path == "" { print("Usage: reload <path>") ; return false }
    print("[CMD] reload " + path)
    # store path immediately; try to load text from file
    write_state(path, "")
    txt := null
    try { txt := load_text_file(path) } catch { txt := null }
    if txt != null {
        write_state(path, txt)
        safe_write("/tmp/tiny_kb.txt", "=== " + path + " ===\n" + txt)
        print("[OK] text loaded and cached (chars=" + tostring(len(txt)) + ")")
    } else {
        print("[WARN] could not read text file now; path stored. Create a .txt at that path or retry.")
    }
    return false
}

cmd_ask := func(arg) {
    q := trim(arg)
    if q == "" { print("Usage: ask \"question\"") ; return false }
    if starts_with(q, "\"") and substr(q, len(q)-1, len(q)) == "\"" { q := substr(q,1,len(q)-1) }
    print("[CMD] ask: " + q)
    st := read_state()
    ans := null
    try { ans := find_local_answer(q, st["text"]) } catch { ans := null }
    if ans != null and trim(ans) != "" {
        print("[LOCAL ANSWER]")
        print(ans)
        return false
    }
    print("No answer found in cached text.")
    return false
}

cmd_show := func(_) {
    st := read_state()
    p := st["path"]
    if p == "" { print("No path set.") ; return false }
    cached := "no"
    if st["text"] != null and trim(st["text"]) != "" { cached := "yes" }
    print("path = " + p)
    print("cached_text = " + cached)
    return false
}

cmd_help := func(_) {
    print("Commands: reload <path>, ask \"question\", show, help, quit")
    return false
}

dispatch := func(line) {
    if line == null { return false }
    s := trim_newlines(line)
    if s == "" { return false }
    norm := s
    if starts_with(norm, "/") { norm := substr(norm,1,len(norm)) }
    if starts_with(norm, "reload ") { return cmd_reload(trim(substr(norm,8,len(norm)))) }
    if starts_with(norm, "ask ") { return cmd_ask(trim(substr(norm,4,len(norm)))) }
    if norm == "show" { return cmd_show("") }
    if norm == "help" { return cmd_help("") }
    if norm == "quit" { print("Quit requested."); return true }
    print("Unknown command: " + s)
    return false
}

main := func() {
    if not exists(cmd_file) { safe_write(cmd_file, "") }
    if not exists(state_file) { write_state("", "") }
    print("Simple daemon started. Monitoring " + cmd_file)
    processed := 0
    while true {
        content := safe_read(cmd_file)
        if content == null { content := "" }
        lines := split(content, "\n")
        i := processed
        quit_flag := false
        while i < len(lines) {
            l := trim_newlines(lines[i])
            if l != "" {
                print("[EXEC] " + l)
                ok := false
                try { ok := dispatch(l) } catch { ok := false ; print("[ERR] dispatch error for: " + l) }
                if ok { quit_flag := true ; break }
            }
            i := i + 1
        }
        processed := len(lines)
        if quit_flag { break }
        try { sleep(1) } catch { try { _ := safe_read(state_file) } catch { } }
    }
    print("Daemon exiting.")
}

main()
