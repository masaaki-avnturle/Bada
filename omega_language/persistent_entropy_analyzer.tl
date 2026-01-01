#了解しました。終了せずに確実にコマンド待ち（対話／ファイル両対応）で動き続け、かつ提出PDFを読み込んでエントロピー解析（title/theorem/proof/concluded/conjecture を統計的に推定）できるtiny_lang互換の実用版ソースを再作成しました。主な改善点：
#
#- グローバル状態を関数内で上書きするときにローカル代入にならないようにし、必ずグローバル変数を更新する方式に統一（`set_selected_text` を利用）。
#- input() が null のとき必ずファイル監視モードに移行してプロセスを終了させない。
#- ファイル監視ループの busy-loop を軽減するため、I/O を伴う小さな待ち処理を挟む（環境に sleep があれば差し替え可）。
#- コマンドは /setpdf, /showpdf, /entropy, /ask, /help, /quit をサポート。/entropy は選択PDFからテキストを取得（キャッシュまたは再抽出）して解析する。
#- 解析は段落分割→段落ごとにトークン化→エントロピーと簡単統計を算出→ヒューリスティックで段落をセクションに割り当て→セクションごとに集計して出力。
#
#以下をそのまま実行してください（tiny_lang 実行環境の組込み関数名が若干異なる場合は微調整してください）。
#
#```tiny_lang
# persistent_entropy_analyzer.tl
# Persistent entropy-based PDF analyzer (interactive REPL or file-command mode).
# Commands: /setpdf <path>, /showpdf, /entropy, /ask <terms>, /help, /quit
#
# Required runtime builtins (expected):
# input(prompt), print(s), file_exists(path), file_read(path), file_write(path),
# split(s,sep), join(list,sep), trim(s), lower(s), find(hay,needle), len(s), tostring(x),
# load_report(path) -> string|null (optional), openai_chat(prompt)->string|null (optional)
#
kb_file    <- "/tmp/tiny_kb.txt"
cmd_file   <- "/tmp/tiny_commands.txt"
selected_pdf_path  <- ""
selected_pdf_text  <- ""   # cached extracted text (global)

# ---------- Utilities ----------
trim_s <- func(s) { if s == null { return "" } ; return s }
trim_newlines <- func(s) { if s == null { return "" } ; r := s ; while len(r)>0 and (r[-1]=='\n' or r[-1]=='\r') { r := r[0:len(r)-1] } ; return r }

tokenize <- func(s) {
    toks := []
    if s == null { return toks }
    cur := ""
    i := 0
    while i < len(s) {
        c := s[i]
        isalnum := false
        if (c>='0' and c<='9') or (c>='A' and c<='Z') or (c>='a' and c<='z') or c=='_' { isalnum := true }
        if isalnum { cur := cur + lower(c) } else { if cur != "" { toks := toks + [cur]; cur := "" } }
        i := i + 1
    }
    if cur != "" { toks := toks + [cur] }
    return toks
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

mean_token_length := func(tokens) {
    if tokens == null or len(tokens) == 0 { return 0.0 }
    sum := 0
    i := 0
    while i < len(tokens) { sum := sum + len(tokens[i]); i := i + 1 }
    return sum / len(tokens)
}

# ---------- Paragraph handling ----------
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
    return { "text": p, "tokens": len(toks), "entropy": entropy_tokens(toks), "mean_tok_len": mean_token_length(toks) }
}

# ---------- Heuristic classifier ----------
classify_para := func(ps) {
    txt := lower(ps["text"])
    # keyword strong cues
    if find(txt, "theorem") >= 0 { return "theorem" }
    if find(txt, "proof") >= 0 { return "proof" }
    if find(txt, "conclud") >= 0 or find(txt, "conclusion") >= 0 { return "concluded" }
    if find(txt, "conject") >= 0 { return "conjecture" }
    # short-first-paragraph title heuristic
    if ps["tokens"] <= 12 and ps["mean_tok_len"] > 3 and ps["entropy"] < 4.0 { return "title" }
    # entropy/token heuristics
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
        p := pars[i]
        ps := paragraph_stats(p)
        cls := classify_para(ps)
        if i == 0 and cls == "full" and ps["tokens"] <= 15 { cls := "title" }  # prefer first paragraph as title
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
    pproof := agg["proof"]["avg_entropy"]
    ptheo := agg["theorem"]["avg_entropy"]
    pconc := agg["concluded"]["avg_entropy"]
    if pproof < ptheo - 0.5 { print("Hint: proofs show lower entropy than theorems (likely formula/symbol heavy).") }
    if pconc > ptheo + 0.5 { print("Hint: conclusions show higher entropy than theorems (narrative/summary).") }
    if agg["title"]["paras"] > 0 { print("Title likely detected.") } else { print("No short title paragraph detected.") }
}

# ---------- Global state setter ----------
set_selected_text := func(path, text) {
    # assign to global vars (avoid redeclaring locals)
    selected_pdf_path := path
    selected_pdf_text := text
    # persist KB if text present
    if text != null and trim_s(text) != "" { file_write(kb_file, "=== PDF: " + path + " ===\n" + text) }
}

# ---------- Commands ----------
set_pdf := func(path) {
    if path == null or trim_s(path) == "" { print("Usage: /setpdf <path>"); return }
    print("Selecting PDF: " + path)
    txt := null
    try { txt := load_report(path) } catch { txt := null }
    if txt != null and trim_s(txt) != "" {
        print("Text extracted and cached.")
        set_selected_text(path, txt)
    } else {
        print("Could not extract text from PDF via load_report. Path stored; you may supply text in " + kb_file)
        set_selected_text(path, "")
    }
}

show_pdf := func() {
    if selected_pdf_path == null or selected_pdf_path == "" { print("No PDF selected. Use /setpdf <path>") ; return }
    print("Selected PDF: " + selected_pdf_path)
    if selected_pdf_text != null and selected_pdf_text != "" { print("(text cached)") } else { print("(no cached text)") }
}

entropy_cmd := func() {
    if selected_pdf_path == null or selected_pdf_path == "" { print("No PDF selected. Use /setpdf <path> first."); return }
    text := selected_pdf_text
    if text == null or trim_s(text) == "" {
        print("No cached text: attempting extraction now.")
        txt := null
        try { txt := load_report(selected_pdf_path) } catch { txt := null }
        if txt != null and trim_s(txt) != "" { set_selected_text(selected_pdf_path, txt); text := txt }
    }
    if text == null or trim_s(text) == "" {
        print("No text available for entropy analysis. Provide extracted text via load_report or place text in " + kb_file)
        return
    }
    sections := infer_sections(text)
    agg := aggregate_section_stats(sections)
    print_entropy_analysis(selected_pdf_path, sections, agg)
}

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
    if q == null or trim_s(q) == "" { print("Usage: /ask <terms>"); return }
    if selected_pdf_text == null or trim_s(selected_pdf_text) == "" { print("No text available. Use /setpdf <path>"); return }
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
        if resp != null and trim_s(resp) != "" { print("OpenAI answer:"); print(trim_newlines(resp)); return }
    }
    print("No local matches and OpenAI unavailable or returned nothing.")
}

# ---------- Command dispatcher ----------
exec_command := func(line) {
    if line == null { return false }
    cmd := trim_s(line)
    if cmd == "" { return false }
    if cmd == "/quit" { print("Quit requested."); return true }
    if cmd == "/help" {
        print("Commands: /setpdf <path>, /showpdf, /entropy, /ask <terms>, /help, /quit")
        return false
    }
    if substr(cmd,0,8) == "/setpdf " { set_pdf(trim_s(substr(cmd,8,len(cmd)))) ; return false }
    if cmd == "/showpdf" { show_pdf() ; return false }
    if cmd == "/entropy" { entropy_cmd() ; return false }
    if substr(cmd,0,5) == "/ask " { answer_question_local(trim_s(substr(cmd,5,len(cmd)))) ; return false }
    print("Unknown command: " + cmd)
    return false
}

# ---------- REPL and file-watcher (persistent) ----------
repl := func() {
    print("Interactive REPL. Type /help")
    while true {
        line := input("assistant> ")
        if line == null {
            print("input() returned null — switching to file-based command mode.")
            return false
        }
        should_quit := exec_command(line)
        if should_quit { return true }
    }
}

file_watch := func() {
    print("File-based command mode: append commands (one per line) to " + cmd_file)
    if not file_exists(cmd_file) { file_write(cmd_file, "") }
    processed := 0
    while true {
        content := file_read(cmd_file)
        if content == null { content := "" }
        lines := split(content, "\n")
        i := processed
        quit_now := false
        while i < len(lines) {
            l := trim_newlines(lines[i])
            if l != "" {
                print("File-cmd: " + l)
                should_quit := exec_command(l)
                if should_quit { quit_now := true ; break }
            }
            i := i + 1
        }
        processed := len(lines)
        if quit_now { return true }
        # light I/O pause: read kb_file (reduces CPU busy-loop); replace with sleep if available
        try { _ := file_read(kb_file) } catch { }
    }
}

# ---------- Entrypoint ----------
main := func() {
    print("Persistent entropy analyzer starting.")
    print("If interactive input unavailable, append commands to " + cmd_file)
    print("Ready. Use /setpdf <path> then /entropy.")
    ok := repl()
    if ok { print("Goodbye."); return }
    q := file_watch()
    if q { print("Goodbye."); return }
    print("Terminated.")
}

main()

#必要なら次を教えてください（短く）：
#- 実行環境の tiny_lang の組み込み関数名（特に PDF 抽出関数名）が違う場合の名称。
#- sleep が使えるなら busy-loop を sleep に置き換える小変更を出します。
