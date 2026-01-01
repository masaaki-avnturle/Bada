#以下は tiny_lang 向けの常駐デーモン実装です。特徴：
#- /tmp/tiny_commands.txt を監視してコマンド実行（追加行を順に処理）。
#- サポートコマンド：/setpdf <path>, /reloadpdf, /showpdf, /entropy, /ask <terms>, /fetch <url>, /help, /quit
#- PDF抽出は組み込みの `load_report(path)` を試みます（無ければパスだけ保持して手動で kb にテキストを置く運用に対応）。
#- Web取得は `http_get(url)`、`fetch(url)`、`requests_get(url)` の順で試行（環境に応じて利用可能な関数にフォールバック）。
#- 例外処理と軽いポーリングを入れ、/quit が来ない限り終了しません。
#
#そのまま実行してください。環境で使える組み込み関数名が異なれば教えてください。
#
#```tiny_lang
# persistent_tiny_daemon.tl
cmd_file <- "/tmp/tiny_commands.txt"
kb_file  <- "/tmp/tiny_kb.txt"
web_file <- "/tmp/tiny_web.txt"

pdf_path <- ""
pdf_text <- ""

# --- utilities ---
trim_s := func(s) { if s == null { return "" } ; return s }
trim_newlines := func(s) { if s == null { return "" } ; r := s ; while len(r)>0 and (r[-1]=='\n' or r[-1]=='\r') { r := r[0:len(r)-1] } ; return r }
safe_read := func(p) { try { return file_read(p) } catch { return null } }
safe_write := func(p,t) { try { file_write(p,t) } catch { } }

# --- tokenizer & entropy ---
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

# --- paragraphs & section inference ---
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

# --- state setter ---
set_selected_text := func(path, text) {
    pdf_path := path
    pdf_text := text
    if text != null and trim_s(text) != "" { safe_write(kb_file, "=== PDF: " + path + " ===\n" + text) }
}

# --- fetch helpers (try multiple possible builtins) ---
http_get_try := func(url) {
    resp := null
    try { resp := http_get(url) } catch { resp := null }
    if resp != null and trim_s(resp) != "" { return resp }
    try { resp := fetch(url) } catch { resp := null }
    if resp != null and trim_s(resp) != "" { return resp }
    try { resp := requests_get(url) } catch { resp := null }
    return resp
}

# --- commands ---
cmd_setpdf := func(arg) {
    if arg == null or trim_s(arg) == "" { print("Usage: /setpdf <path>"); return }
    print("Selecting PDF: " + arg)
    txt := null
    try { txt := load_report(arg) } catch { txt := null }
    if txt != null and trim_s(txt) != "" {
        print("Text extracted and cached.")
        set_selected_text(arg, txt)
    } else {
        print("Could not extract text via load_report. Path stored; put text into " + kb_file + " or use /reloadpdf later.")
        set_selected_text(arg, "")
    }
}
cmd_reloadpdf := func() {
    if pdf_path == null or pdf_path == "" { print("No PDF selected. Use /setpdf first."); return }
    print("Reloading PDF: " + pdf_path)
    txt := null
    try { txt := load_report(pdf_path) } catch { txt := null }
    if txt != null and trim_s(txt) != "" {
        print("Reload successful.")
        set_selected_text(pdf_path, txt)
    } else {
        print("Reload failed or no text extracted.")
    }
}
cmd_showpdf := func() {
    if pdf_path == null or pdf_path == "" { print("No PDF selected."); return }
    print("Selected PDF: " + pdf_path)
    if pdf_text != null and pdf_text != "" { print("(text cached)") } else { print("(no cached text)") }
}
cmd_entropy := func() {
    if pdf_path == null or pdf_path == "" { print("No PDF selected. Use /setpdf"); return }
    text := pdf_text
    if text == null or trim_s(text) == "" {
        print("No cached text: attempting extraction now.")
        txt := null
        try { txt := load_report(pdf_path) } catch { txt := null }
        if txt != null and trim_s(txt) != "" { set_selected_text(pdf_path, txt); text := txt }
    }
    if text == null or trim_s(text) == "" { print("No text available for analysis."); return }
    sections := infer_sections(text)
    agg := aggregate_section_stats(sections)
    print_entropy_analysis(pdf_path, sections, agg)
}
cmd_ask := func(arg) {
    if arg == null or trim_s(arg) == "" { print("Usage: /ask <terms>"); return }
    if pdf_text == null or trim_s(pdf_text) == "" { print("No text available. Use /setpdf or /reloadpdf"); return }
    hits := []
    lines := split(pdf_text, "\n")
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
        while i < len(hits) and i < 20 { print("- " + hits[i]); i := i + 1 }
        return
    }
    print("No local matches.")
}
cmd_fetch := func(arg) {
    if arg == null or trim_s(arg) == "" { print("Usage: /fetch <url>"); return }
    url := trim_s(arg)
    print("Fetching: " + url)
    body := http_get_try(url)
    if body == null or trim_s(body) == "" { print("Fetch failed or empty."); return }
    safe_write(web_file, "=== URL: " + url + " ===\n" + body)
    # print first lines
    lines := split(body, "\n")
    i := 0
    print("Fetched (head):")
    while i < len(lines) and i < 20 { print("- " + trim_newlines(lines[i])); i := i + 1 }
}
cmd_help := func() { print("Commands: /setpdf <path>, /reloadpdf, /showpdf, /entropy, /ask <terms>, /fetch <url>, /help, /quit") }

# --- dispatcher ---
dispatch_line := func(line) {
    if line == null { return false }
    s := trim_newlines(line)
    if s == "" { return false }
    if substr(s,0,8) == "/setpdf " { cmd_setpdf(trim_s(substr(s,8,len(s))); return false }
    if s == "/reloadpdf" { cmd_reloadpdf(); return false }
    if s == "/showpdf" { cmd_showpdf(); return false }
    if s == "/entropy" { cmd_entropy(); return false }
    if substr(s,0,5) == "/ask " { cmd_ask(trim_s(substr(s,5,len(s)))); return false }
    if substr(s,0,7) == "/fetch " { cmd_fetch(trim_s(substr(s,7,len(s)))); return false }
    if s == "/help" { cmd_help(); return false }
    if s == "/quit" { print("Quit requested."); return true }
    print("Unknown command: " + s)
    return false
}

# --- main loop ---
main := func() {
    if not file_exists(cmd_file) { safe_write(cmd_file, "") }
    print("Daemon started. Monitoring " + cmd_file)
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
        if quit_now { print("Daemon exiting on /quit."); break }
        # light pause (try sleep if available)
        try { _ := safe_read(kb_file) } catch { }
        try { sleep(1) } catch { }
    }
}

main()
#```

#使い方（短く）：
#- デーモンを起動しておく。
#- 別端末でコマンドを追加：
#  echo "/setpdf /path/to/file.pdf" >> /tmp/tiny_commands.txt
#  echo "/fetch https://example.com" >> /tmp/tiny_commands.txt
#- 停止する場合のみ /quit を追記。
#
#もし起動直後に即終了する場合は、起動時の最初の print 出力（ログ）を教えてください。また、環境で利用可能な組み込み関数名（例: load_report/http_get/fetch/requests_get/sleep）が分かれば微調整します。
