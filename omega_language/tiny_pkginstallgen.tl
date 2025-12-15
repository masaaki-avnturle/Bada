以下は、提示された C プログラムの機能をできるだけ忠実に tiny_lang スタイルに置き換えたスクリプトです。実行環境の tiny_lang 実装によっては組み込み関数名（`file_read` / `file_write` / `file_exists` / `run` / `sleep` 等）が異なるかもしれません。必要に応じて関数名を置換してください。

機能概略
- refs/ に curl でダウンロード（`fetch dicts <url> ...`）。実行はバックグラウンド化（シェルの & を利用）。
- `reload report "file"`: レポート読み込み、行分割、数値抽出、式っぽい行抽出（簡易ヒューリスティック）。
- トークン化して語頻度蓄積、エントロピー計算。
- `ask "question"`: レポート中のキーワード一致による抜粋、簡易データ駆動モデル（最小二乗の簡易実装）を構成し、説明文を生成。
- `export "file"`: last_analysis と last_tree を書き出す。

保存名例: tiny_pkginstallgen.tl

```tiny_lang
# tiny_pkginstallgen.tl
# 注意: tiny_lang 実装に応じて file_read/file_write/run/sleep/file_exists を適宜置換してください.

cmd_file <- "/tmp/tiny_commands.txt"
refs_dir <- "refs"
kb_file <- "/tmp/tiny_kb.txt"
state_export <- "/tmp/pkginstall_export.txt"

# Globals
corpus := {}                 # map token -> count (simulate with two arrays)
tokens_list := []
tokens_count := []
total_tokens := 0

last_report_lines := []
last_report_numbers := []
last_report_eqs := []

last_analysis := ""
last_tree := ""

# helpers
safe_read := func(p) { try { return file_read(p) } catch { return null } }
safe_write := func(p,t) { try { file_write(p,t) } catch { } }
exists := func(p) { try { return file_exists(p) } catch { return false } }
mkdir_p := func(d) { try { run("mkdir -p " + d) } catch { } }

trim := func(s) { if s==null { return "" } ; return s }
lower := func(s) { try { return lower(s) } catch { return s } }

# tokenize text into alphanumeric lowercased tokens and update corpus
tokenize_and_add := func(text) {
    if text == null { return }
    i := 0
    while i < len(text) {
        # skip non-alnum
        while i < len(text) and not ( (text[i]>="0" and text[i]<="9") or (text[i]>="A" and text[i]<="Z") or (text[i]>="a" and text[i]<="z") ) { i := i + 1 }
        if i >= len(text) { break }
        j := i
        buf := ""
        while j < len(text) and ( (text[j]>="0" and text[j]<="9") or (text[j]>="A" and text[j]<="Z") or (text[j]>="a" and text[j]<="z") ) {
            c := text[j]
            # to lower
            try { c := lower(c) } catch { }
            buf := buf + c
            j := j + 1
        }
        # add token
        if buf != "" {
            found := false
            k := 0
            while k < len(tokens_list) {
                if tokens_list[k] == buf { tokens_count[k] := tokens_count[k] + 1 ; total_tokens := total_tokens + 1 ; found := true ; break }
                k := k + 1
            }
            if not found {
                tokens_list := tokens_list + [buf]
                tokens_count := tokens_count + [1]
                total_tokens := total_tokens + 1
            }
        }
        i := j
    }
}

# sort corpus by count desc (simple bubble-ish for small sizes)
sort_corpus := func() {
    n := len(tokens_list)
    i := 0
    while i < n {
        j := i + 1
        while j < n {
            if tokens_count[j] > tokens_count[i] or (tokens_count[j] == tokens_count[i] and tokens_list[j] < tokens_list[i]) {
                # swap
                t := tokens_list[i]; tokens_list[i] := tokens_list[j]; tokens_list[j] := t
                c := tokens_count[i]; tokens_count[i] := tokens_count[j]; tokens_count[j] := c
            }
            j := j + 1
        }
        i := i + 1
    }
}

# compute Shannon entropy (bits)
compute_entropy := func() {
    if total_tokens == 0 { return 0.0 }
    H := 0.0
    i := 0
    while i < len(tokens_list) {
        p := tokens_count[i] / total_tokens
        if p > 0.0 { H := H - p * (log(p) / log(2.0)) }
        i := i + 1
    }
    return H
}

# extract numbers and equation-like lines from text
is_equation_like := func(line) {
    if line == null { return false }
    if find(line, "=") >= 0 or find(line, "->") >= 0 or find(line, "log(") >= 0 or find(line, "exp(") >= 0 or find(line, "^") >= 0 { return true }
    has_alpha := false; has_op := false
    i := 0
    while i < len(line) {
        c := line[i]
        if (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") { has_alpha := true }
        if c == "+" or c == "-" or c == "*" or c == "/" { has_op := true }
        i := i + 1
    }
    return has_alpha and has_op
}

extract_report_facts := func(text) {
    # clear previous
    last_report_lines := []
    last_report_numbers := []
    last_report_eqs := []
    if text == null { return }
    # split lines
    lines := split(text, "\n")
    i := 0
    while i < len(lines) {
        line := trim(lines[i])
        last_report_lines := last_report_lines + [line]
        # find numbers via scanning
        j := 0
        while j < len(line) {
            ch := line[j]
            if (ch >= "0" and ch <= "9") or ch == "+" or ch == "-" or ch == "." {
                # extract continuous numeric-ish substring
                k := j
                numbuf := ""
                while k < len(line) and ((line[k] >= "0" and line[k] <= "9") or line[k] == "." or line[k] == "e" or line[k] == "E" or line[k] == "+" or line[k] == "-") {
                    numbuf := numbuf + line[k]
                    k := k + 1
                }
                # attempt parse
                try {
                    v := tonumber(numbuf)
                    last_report_numbers := last_report_numbers + [v]
                } catch { }
                j := k
            } else { j := j + 1 }
        }
        if is_equation_like(line) { last_report_eqs := last_report_eqs + [line] }
        i := i + 1
    }
}

# very small linear least squares for basis [1, x, x^2, log(1+x), exp(-x)]
lsq_fit := func(X, Y) {
    n := len(X)
    if n == 0 { return null }
    # determine m basis
    m := 2
    if n >= 5 { m := 4 }
    if n >= 12 { m := 5 }
    # build Gram and rhs
    G := []
    rhs := []
    i := 0
    while i < m*m { G := G + [0.0] ; i := i + 1 }
    i := 0
    while i < m { rhs := rhs + [0.0] ; i := i + 1 }
    s := 0
    while s < n {
        x := X[s]
        phi := []
        phi := phi + [1.0]
        phi := phi + [x]
        if m >= 3 { phi := phi + [x*x] }
        if m >= 4 { phi := phi + [log(1.0 + abs(x))] }
        if m >= 5 { phi := phi + [exp(-x)] }
        i := 0
        while i < m {
            j := 0
            while j < m {
                G[i*m + j] := G[i*m + j] + phi[i] * phi[j]
                j := j + 1
            }
            rhs[i] := rhs[i] + phi[i] * Y[s]
            i := i + 1
        }
        s := s + 1
    }
    # Solve by naive Gaussian elimination (m small)
    A := []
    i := 0
    while i < m*m { A := A + [G[i]] ; i := i + 1 }
    b := []
    i := 0
    while i < m { b := b + [rhs[i]] ; i := i + 1 }
    i := 0
    while i < m {
        # pivot
        piv := i
        maxv := abs(A[i*m + i])
        r := i + 1
        while r < m {
            v := abs(A[r*m + i])
            if v > maxv { maxv := v ; piv := r }
            r := r + 1
        }
        if maxv < 1e-12 { return null }
        if piv != i {
            c := 0
            while c < m { t := A[i*m + c] ; A[i*m + c] := A[piv*m + c] ; A[piv*m + c] := t ; c := c + 1 }
            t := b[i]; b[i] := b[piv]; b[piv] := t
        }
        diag := A[i*m + i]
        c := i
        while c < m { A[i*m + c] := A[i*m + c] / diag ; c := c + 1 }
        b[i] := b[i] / diag
        r := 0
        while r < m {
            if r != i {
                f := A[r*m + i]
                c := i
                while c < m { A[r*m + c] := A[r*m + c] - f * A[i*m + c] ; c := c + 1 }
                b[r] := b[r] - f * b[i]
            }
            r := r + 1
        }
        i := i + 1
    }
    coef := []
    i := 0
    while i < m { coef := coef + [b[i]] ; i := i + 1 }
    return coef
}

# build data-driven model and explanation
build_model := func() {
    H := compute_entropy()
    vocab := len(tokens_list)
    mean_token := 0.0
    if vocab > 0 { mean_token := total_tokens / vocab }
    # prepare samples
    X := []
    Y := []
    if len(last_report_numbers) >= 2 {
        pairs := len(last_report_numbers) / 2
        i := 0
        while i < pairs {
            X := X + [ last_report_numbers[2*i] ]
            Y := Y + [ last_report_numbers[2*i + 1] ]
            i := i + 1
        }
    } else if len(last_report_numbers) == 1 {
        base := last_report_numbers[0]
        i := 0
        while i < 5 { X := X + [ i + 1.0 ] ; Y := Y + [ base * (i + 1.0) ] ; i := i + 1 }
    } else {
        v := (vocab < 5) ? 3 : 6
        i := 0
        while i < v { X := X + [ i + 1.0 ] ; Y := Y + [ (i + 1.0) * (1.0 + H*0.1) ] ; i := i + 1 }
    }
    coef := lsq_fit(X, Y)
    # build expression string
    expr := ""
    if coef == null {
        expr := expr + "No fit possible; insufficient numeric evidence. "
    } else {
        # m determined by coef length
        m := len(coef)
        expr := expr + "Y(X) = "
        if m >= 1 { expr := expr + tostring(coef[0]) }
        if m >= 2 { expr := expr + " + " + tostring(coef[1]) + " * X" }
        if m >= 3 { expr := expr + " + " + tostring(coef[2]) + " * X^2" }
        if m >= 4 { expr := expr + " + " + tostring(coef[3]) + " * log(1+X)" }
        if m >= 5 { expr := expr + " + " + tostring(coef[4]) + " * exp(-X)" }
    }
    # compose analysis text
    analysis := "Model generated.\nCorpus: vocab=" + tostring(vocab) + " total_tokens=" + tostring(total_tokens) + " entropy=" + tostring(H) + "\n"
    analysis := analysis + "Samples used: " + tostring(len(X)) + "\n"
    analysis := analysis + "Expression: " + expr + "\n"
    if len(last_report_eqs) > 0 {
        analysis := analysis + "Equation-like lines from report (evidence):\n"
        i := 0
        while i < len(last_report_eqs) and i < 6 { analysis := analysis + " - " + last_report_eqs[i] + "\n" ; i := i + 1 }
    }
    return analysis
}

# CLI commands

cmd_fetch_dicts := func(args) {
    if len(args) < 2 { print("usage: fetch dicts <url> [url...]"); return }
    mkdir_p(refs_dir)
    i := 1
    while i < len(args) {
        url := args[i]
        safe := ""
        j := 0
        while j < len(url) {
            ch := url[j]
            okch := ( (ch >= "0" and ch <= "9") or (ch >= "A" and ch <= "Z") or (ch >= "a" and ch <= "z") )
            if okch { safe := safe + ch } else { safe := safe + "_" }
            j := j + 1
        }
        out := refs_dir + "/" + safe + ".txt"
        # use curl in background to avoid blocking; rely on shell &
        cmd := "curl -sS -f -L --connect-timeout 10 --max-time 20 -o " + out + " '" + url + "' 2>/dev/null &"
        try { run(cmd) } catch { print("failed to launch curl for " + url) }
        # attempt to ingest if file exists now
        if exists(out) {
            txt := safe_read(out)
            if txt != null { tokenize_and_add(txt) ; safe_write(kb_file, "ingested " + out + "\n") }
        }
        i := i + 1
    }
    sort_corpus()
    print("fetch launched; corpus vocab=" + tostring(len(tokens_list)) + " total=" + tostring(total_tokens))
}

cmd_reload_report := func(path) {
    if path == null or path == "" { print("usage: reload report \"file\""); return }
    txt := safe_read(path)
    if txt == null { print("failed to read " + path); return }
    # clear previous corpus and report
    tokens_list := [] ; tokens_count := [] ; total_tokens := 0
    last_report_lines := [] ; last_report_numbers := [] ; last_report_eqs := []
    extract_report_facts(txt)
    # ingest report tokens
    i := 0
    while i < len(last_report_lines) { tokenize_and_add(last_report_lines[i]) ; i := i + 1 }
    # ingest any refs files present
    try {
        run("mkdir -p " + refs_dir)
        # naive read of directory entries via run + temp file list (some tiny_lang may not support dir read)
        try {
            # if file system dir read exists, skip shell trick
            dlist := run("ls -1 " + refs_dir + " 2>/dev/null")
            if dlist != null {
                lines := split(dlist, "\n")
                j := 0
                while j < len(lines) {
                    name := trim(lines[j])
                    if name != "" {
                        fpath := refs_dir + "/" + name
                        if exists(fpath) {
                            r := safe_read(fpath)
                            if r != null { tokenize_and_add(r) }
                        }
                    }
                    j := j + 1
                }
            }
        } catch { }
    } catch { }
    sort_corpus()
    print("report reloaded: vocab=" + tostring(len(tokens_list)) + " total=" + tostring(total_tokens) + " numbers=" + tostring(len(last_report_numbers)) + " eqs=" + tostring(len(last_report_eqs)))
}

cmd_ask := func(q) {
    if q == null or q == "" { print("usage: ask \"question\""); return }
    # ensure refs ingested (best-effort)
    # search report lines for question tokens
    found := false
    evidence := ""
    words := split(q, " ")
    i := 0
    while i < len(words) {
        w := lower(trim(words[i]))
        j := 0
        while j < len(last_report_lines) {
            if find(lower(last_report_lines[j]), w) >= 0 {
                if not found { evidence := evidence + "Relevant report excerpts:\n"; found := true }
                evidence := evidence + " - " + last_report_lines[j] + "\n"
            }
            j := j + 1
        }
        i := i + 1
    }
    modeltxt := build_model()
    analysis := "Question: " + q + "\nCorpus vocab=" + tostring(len(tokens_list)) + " total=" + tostring(total_tokens) + " entropy=" + tostring(compute_entropy()) + "\n\n"
    if found { analysis := analysis + evidence + "\n" } else { analysis := analysis + "No direct phrase matches found; proceeding with data-driven synthesis.\n\n" }
    analysis := analysis + "Model & justification:\n" + modeltxt + "\n"
    last_analysis := analysis
    # simple tree
    t := "generated_tree:\nquestion=" + q + "\nmodel_summary:\n" + modeltxt + "\n"
    last_tree := t
    print("ask: generated artifacts (use export to write files)")
}

cmd_export := func(path) {
    if path == null or path == "" { print("usage: export \"file\""); return }
    if last_analysis == "" { print("nothing to export; run ask first"); return }
    out := "### pkginstallgen export\n\nanalysis:\n" + last_analysis + "\n\ntree:\n" + last_tree + "\n"
    safe_write(path, out)
    print("exported to " + path)
}

# dispatcher
dispatch := func(tokens) {
    if len(tokens) == 0 { return false }
    if tokens[0] == "fetch" and len(tokens) >= 2 and tokens[1] == "dicts" { cmd_fetch_dicts(tokens) ; return false }
    if tokens[0] == "reload" and len(tokens) >= 3 and tokens[1] == "report" { cmd_reload_report(tokens[2]) ; return false }
    if tokens[0] == "ask" and len(tokens) >= 2 { cmd_ask(join(slice(tokens,1,len(tokens)), " ")) ; return false }
    if tokens[0] == "export" and len(tokens) >= 2 { cmd_export(tokens[1]) ; return false }
    if tokens[0] == "help" { print("commands: fetch dicts <url...>, reload report \"file\", ask \"question\", export \"file\", quit") ; return false }
    if tokens[0] == "quit" or tokens[0] == "exit" { print("quit"); return true }
    print("unknown command: " + tokens[0])
    return false
}

# simple arg splitting (respect quoted strings)
split_args := func(line) {
    out := []
    i := 0
    while i < len(line) {
        while i < len(line) and (line[i] == " " or line[i] == "\t") { i := i + 1 }
        if i >= len(line) { break }
        if line[i] == '"' or line[i] == '\'' {
            q := line[i]; i := i + 1
            s := ""
            while i < len(line) and line[i] != q {
                if line[i] == "\\" and i+1 < len(line) { i := i + 1 ; s := s + line[i] ; i := i + 1 ; continue }
                s := s + line[i]
                i := i + 1
            }
            if i < len(line) and line[i] == q { i := i + 1 }
            out := out + [s]
        } else {
            s := ""
            while i < len(line) and not (line[i] == " " or line[i] == "\t") { s := s + line[i] ; i := i + 1 }
            out := out + [s]
        }
    }
    return out
}

# main loop
print("tiny_pkginstallgen ready. type 'help'.")
while true {
    try { print("> ") } catch { }
    l := ""
    try { l := input() } catch { l := null }
    if l == null { break }
    toks := split_args(l)
    ok := false
    try { ok := dispatch(toks) } catch { print("command error") ; ok := false }
    if ok { break }
    try { sleep(0.2) } catch { }
}
print("exiting.")
```

使い方（例）
- 起動: tiny_lang 実行環境で上スクリプトを実行。
- デフォルトで refs の自動取得を行わないため、明示的に:
  - fetch dicts "https://en.wikipedia.org/api/rest_v1/page/summary/Riemann_hypothesis"
  - reload report "/full/path/to/report.txt"
  - ask "リーマンゼータに関するエントロピーは?"
  - export "/tmp/out.txt"

注意（重要）
- tiny_lang の機能差により `run("curl ... &")` や `input()`、`sleep()`、`file_read` などの存在／挙動が異なります。実行環境の組み込み API 名に合わせて小さく置換してください（例: `file_read` → `read_file` 等）。必要なら実行環境名を教えてください、対応版を出します。
- 本スクリプトは「高度なNLP/数学的推論エンジン」ではなく、提示機能の“代理実装”です。実データでの精度向上や数式解析を望む場合は Python + numpy/scipy/regex 等へ移植することを推奨します。

必要であれば、あなたの tiny_lang 実行環境で使える正確な組み込み関数名を教えてください。それに合わせて動作確認済みの最小版に調整します。
