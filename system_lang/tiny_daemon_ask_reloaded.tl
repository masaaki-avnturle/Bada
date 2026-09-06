ä�������������������������������������������������������������������������������� `tiny_lang` 用デーモンを以下に示します。期待動作：

- コマンドファイル `/tmp/tiny_commands.txt` を監視（追記された行を順に処理）。
- /reload <path>：指定 PDF を `load_report(path)` で読み取り、テキストをキャッシュ。
- /ask "質問"：まずローカルキャッシュ内を検索して回答を返す（一致箇所の文脈を返す）。見つからなければ `openai_chat(prompt)` があればそれを使って回答。
- /show、/help、/quit をサポート。例外は捕捉してデーモンは継続。

そのままファイルに保存して tiny_lang 実行環境で実行してください。環境に `load_report` / `openai_chat` / `sleep` の有無があれば後で調整します。

```tiny_lang
# tiny_daemon_reload_ask_clean.tl
# Monitor /tmp/tiny_commands.txt; commands: /reload <path>, /ask "question", /show, /help, /quit

cmd_file <- "/tmp/tiny_commands.txt"
kb_file  <- "/tmp/tiny_kb.txt"

pdf_path <- ""
pdf_text <- ""

# --- utilities ---
safe_read := func(p) { try { return file_read(p) } catch { return null } }
safe_write := func(p,t) { try { file_write(p,t) } catch { } }
trim := func(s) { if s == null { return "" } ; return s }
trim_newlines := func(s) { if s == null { return "" } ; r := s ; while len(r)>0 and (r[-1]=='\n' or r[-1]=='\r') { r := r[0:len(r)-1] } ; return r }
lower_trim := func(s) { return lower(trim(s)) }
starts_with := func(s,p) { if s == null or p == null { return false } ; if len(s) < len(p) { return false } ; return substr(s,0,len(p)) == p }

# --- simple sentence splitter (naive) ---
split_sentences := func(text) {
    out := []
    if text == null or trim(text) == "" { return out }
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

# --- load PDF text via load_report (non-fatal) ---
load_pdf_text := func(path) {
    if path == null or trim(path) == "" { return null }
    txt := null
    try { txt := load_report(path) } catch { txt := null }
    if txt == null or trim(txt) == "" { return null }
    return txt
}

# --- save cached kb file ---
cache_pdf_text := func(path, text) {
    try { safe_write(kb_file, "=== PDF: " + path + " ===\n" + text) } catch { }
}

# --- local answer search: collect sentences matching keywords (naive) ---
find_local_answer := func(question) {
    if pdf_text == null or trim(pdf_text) == "" { return null }
    q := lower_trim(question)
    # build keywords (simple split, ignore short tokens)
    parts := split(q, " ")
    kws := []
    i := 0
    while i < len(parts) {
        t := parts[i]
        if len(t) >= 3 { kws := kws + [t] }
        i := i + 1
    }
    if len(kws) == 0 { kws := parts }
    sents := split_sentences(pdf_text)
    hits := []
    i := 0
    while i < len(sents) {
        s := sents[i]
        sl := lower_trim(s)
        j := 0
        matched := false
        while j < len(kws) {
            if find(sl, kws[j]) >= 0 { matched := true ; break }
            j := j + 1
        }
        if matched { hits := hits + [s] }
        i := i + 1
    }
    if len(hits) == 0 { return null }
    # return up to first 4 matching sentences as context
    out := ""
    i := 0
    while i < len(hits) and i < 4 {
        out := out + hits[i] + " "
        i := i + 1
    }
    return trim_newlines(out)
}

# --- fallback to openai_chat if available ---
ask_via_openai := func(question) {
    if openai_chat == null { return null }
    prompt := "Document:\n" + (if pdf_text==null then "" else pdf_text) + "\n\nQuestion:\n" + question + "\n\nAnswer concisely:"
    resp := null
    try { resp := openai_chat(prompt) } catch { resp := null }
    if resp == null or trim(resp) == "" { return null }
    return trim_newlines(resp)
}

# --- commands ---
cmd_reload := func(arg) {
    path := trim(arg)
    if path == "" { print("Usage: /reload <path>") ; return false }
    print("[CMD] reload " + path)
    txt := null
    try { txt := load_pdf_text(path) } catch { txt := null }
    if txt != null {
        pdf_path := path
        pdf_text := txt
        cache_pdf_text(path, txt)
        print("[OK] PDF loaded. chars=" + tostring(len(txt)))
    } else {
        pdf_path := path
        pdf_text := ""
        print("[WARN] Could not extract text with load_report. Path stored; you can put text into " + kb_file + " or try again.")
    }
    return false
}
cmd_ask := func(arg) {
    q := trim(arg)
    if q == "" { print("Usage: /ask \"question\"") ; return false }
    # remove surrounding quotes if present
    if starts_with(q, "\"") and substr(q, len(q)-1, len(q)) == "\"" { q := substr(q,1,len(q)-1) }
    print("[CMD] ask: " + q)
    # try local
    local := null
    try { local := find_local_answer(q) } catch { local := null }
    if local != null and trim(local) != "" {
        print("[LOCAL ANSWER]")
        print(local)
        return false
    }
    # fallback remote
    remote := null
    try { remote := ask_via_openai(q) } catch { remote := null }
    if remote != null and trim(remote) != "" {
        print("[OPENAI ANSWER]")
        print(remote)
        return false
    }
    print("No answer found locally; no remote responder available or returned empty.")
    return false
}
cmd_show := func(_) {
    if pdf_path == null or pdf_path == "" { print("No PDF loaded.") ; return false }
    cached := "no"
    if pdf_text != null and trim(pdf_text) != "" { cached := "yes" }
    print("PDF: " + pdf_path + " (cached_text=" + cached + ")")
    return false
}
cmd_help := func(_) {
    print("Commands: /reload <path>, /ask \"question\", /show, /help, /quit")
    return false
}

# dispatcher
dispatch := func(line) {
    if line == null { return false }
    s := trim_newlines(line)
    if s == "" { return false }
    if starts_with(s, "/reload ") { return cmd_reload(trim(substr(s,8,len(s)))) }
    if starts_with(s, "/ask ") { return cmd_ask(trim(substr(s,5,len(s)))) }
    if s == "/show" { return cmd_show("") }
    if s == "/help" { return cmd_help("") }
    if s == "/quit" { print("Quit requested.") ; return true }
    print("Unknown command: " + s)
    return false
}

# main loop: monitor whole file and process appended lines
main := func() {
    if not file_exists(cmd_file) { safe_write(cmd_file, "") }
    print("Daemon started. Monitoring " + cmd_file)
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
        # sleep if available, otherwise do harmless read
        try { sleep(1) } catch { try { _ := safe_read(kb_file) } catch { } }
    }
    print("Daemon exiting.")
}

main()
```

使い方（例）
- デーモン起動（tiny_lang 環境で上スクリプトを実行）。
- 別端末でコマンドを送る：
  - echo "/reload /full/path/to/sample.pdf" >> /tmp/tiny_commands.txt
  - echo "/ask \"What is the main theorem?\"" >> /tmp/tiny_commands.txt
  - echo "/show" >> /tmp/tiny_commands.txt
  - echo "/quit" >> /tmp/tiny_commands.txt

注意
- 環境に `load_report(path)` が無い場合は、/tmp/tiny_kb.txt に手動でテキストを置いてください（デーモンは /reload でパスだけを保持します）。
- `openai_chat` があるとフォールバックでより良い応答が得られます。ない場合はローカル検索のみで応答します。

必要なら、環境での最初の起動ログ（最初に print される行）や、組み込み関数名の違いを教えてください。環境に合わせて微調整します。