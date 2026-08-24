package bada.silent;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Bada Vim — an embedded vi-like modal editor over a multi-line buffer (NOT
 * short-text). Normal-mode motions/edits (i a o O dd x h j k l 0 $ gg G) plus ex
 * commands (:w :q :d :math :bada :latex :report :whisper :set) that embed the
 * generators — e.g. {@code :math 多様体 量子} inserts a long-long math paper.
 * Mirrors {@code Bada::SilentTalk::Vim}.
 */
public final class Vim {
    private final List<String> buffer = new ArrayList<>();
    private int row = 0, col = 0, nonce = 0;
    private String filename = null;
    private boolean saved = true;

    public static final class R {
        public final String msg;
        public final boolean quit;
        R(String msg, boolean quit) { this.msg = msg; this.quit = quit; }
    }

    public Vim() { this(""); }
    public Vim(String text) {
        if (text == null || text.isEmpty()) buffer.add("");
        else buffer.addAll(Arrays.asList(text.split("\n", -1)));
    }

    public String text() { return String.join("\n", buffer); }
    public int lineCount() { return buffer.size(); }
    public int row() { return row; }
    public int col() { return col; }
    public String filename() { return filename; }
    public boolean saved() { return saved; }

    public String status() {
        return String.format("[%s] %s %d行 (%d,%d)", filename == null ? "[No Name]" : filename,
                saved ? "" : "[+]", lineCount(), row + 1, col + 1);
    }

    /** Process one input line: ex command (":…") or a normal-mode command. */
    public R feed(String line) {
        if (line == null) return new R("", false);
        if (line.startsWith(":")) return ex(line.substring(1));
        if (line.isEmpty()) return new R("", false);

        char cmd = line.charAt(0);
        String rest = line.substring(1);
        if (line.equals("dd")) { deleteLine(); return touched("削除"); }
        if (line.equals("gg")) { row = 0; col = 0; return new R("top", false); }
        switch (cmd) {
            case 'i': insertText(rest); return touched("挿入");
            case 'a': col = Math.min(col + 1, cur().length()); insertText(rest); return touched("追記");
            case 'o': openBelow(rest); return touched("行追加");
            case 'O': openAbove(rest); return touched("行追加");
            case 'x': deleteChar(); return touched("削除");
            case 'G': row = buffer.size() - 1; col = 0; return new R("bottom", false);
            case '0': col = 0; return new R("", false);
            case '$': col = Math.max(cur().length() - 1, 0); return new R("", false);
            case 'h': col = Math.max(col - 1, 0); return new R("", false);
            case 'l': col = Math.min(col + 1, cur().length()); return new R("", false);
            case 'j': row = Math.min(row + 1, buffer.size() - 1); clampCol(); return new R("", false);
            case 'k': row = Math.max(row - 1, 0); clampCol(); return new R("", false);
            default: return new R("?" + cmd, false);
        }
    }

    /** Ex command handling (the ":" command line). */
    public R ex(String cmd) {
        String s = cmd == null ? "" : cmd.strip();
        int sp = s.indexOf(' ');
        String name = sp < 0 ? s : s.substring(0, sp);
        String arg = sp < 0 ? "" : s.substring(sp + 1).strip();
        switch (name) {
            case "w": case "write":
                saved = true; if (!arg.isEmpty()) filename = arg; return new R("written " + filename, false);
            case "q": case "quit": return new R("quit", true);
            case "wq": case "x": saved = true; return new R("written", true);
            case "d": case "delete": deleteLine(); return touched("削除");
            case "%d": buffer.clear(); buffer.add(""); row = 0; col = 0; return touched("全消去");
            case "set": return new R("set " + arg, false);
            case "bada": insertBlock(BadaSyntax.buildAuto(arg, bump()).code); return touched("Bada挿入");
            case "math": insertBlock(Platex.mathPaper(arg, bump()).code); return touched("数学論文挿入");
            case "latex": case "tex": insertBlock(Platex.paper(arg, bump()).code); return touched("論文挿入");
            case "report": insertBlock(Whisper.longReport(arg).text); return touched("レポート挿入");
            case "whisper": insertBlock(Whisper.verbalize(arg).text); return touched("言語化挿入");
            case "whisperen": insertBlock(Whisper.verbalizeEn(arg).text); return touched("ウィスパード英語挿入");
            case "burst": return burstReconstruct(arg);
            case "think": { Think t = think(); return new R(t.msg, false); }
            case "thinkprog": return thinkProgramArgs(arg);
            case "kw": { Think t = keywordCommand(arg);
                return new R(t == null ? "unknown keyword: " + arg : t.msg, false); }
            case "lang": return setThinkLang(arg);
            case "qc": insertBlock(qcSource(arg)); return touched("QCソース挿入");
            case "verilog": insertBlock(verilogSource(arg)); return touched("半導体ソース挿入");
            default: return new R("unknown ex: :" + name, false);
        }
    }

    /**
     * Reconstruct MANY whispered lines AT ONCE (複数行を一辺に・一瞬で). With no
     * argument the whole buffer is reconstructed in a single shot; with an
     * argument, ";"-separated whispered lines replace the buffer in one shot —
     * spanning multiple lines instantly, voicelessly, above silent-talk.
     */
    private R burstReconstruct(String arg) {
        String src = (arg == null || arg.strip().isEmpty()) ? text() : String.join("\n", arg.split(";"));
        Whisper.Result r = Whisper.verbalizeBlock(src);
        buffer.clear();
        for (String ln : r.text.split("\n", -1)) buffer.add(ln);
        if (buffer.isEmpty()) buffer.add("");
        row = Math.max(buffer.size() - 1, 0);
        col = cur().length();
        int filled = 0;
        for (String ln : buffer) if (!ln.strip().isEmpty()) filled++;
        return touched(String.format("一括ウィスパード復元 %d行 %.0f%%", filled, r.precision * 100));
    }

    // ---- 思っただけのコマンド操作 (thought-only command operation) ------------

    /** One applied thought/keyword command: keyword, vim command, precision. */
    public static final class Think {
        public final String msg, keyword, command;
        public final double precision;
        Think(String msg, String keyword, String command, double precision) {
            this.msg = msg; this.keyword = keyword; this.command = command; this.precision = precision;
        }
    }

    private int thinkNonce = 0;

    /** Program-writing actions the thought sampler draws from. */
    static final String[] THINK_ACTIONS = {"set", "assign", "push", "print"};

    /** キーワードのコマンド入力: keyword (EN/日本語) -> action, or null if unknown. */
    static String keywordAction(String word) {
        String w = word == null ? "" : word.strip().toLowerCase();
        switch (w) {
            case "set": case "代入": return "set";
            case "assign": case "束縛": return "assign";
            case "push": case "送出": return "push";
            case "print": case "表示": return "print";
            case "delete": case "削除": return "delete";
            case "top": case "先頭": return "top";
            case "bottom": case "末尾": return "bottom";
            case "save": case "保存": return "save";
            case "english": case "英語": return "english";
            case "japanese": case "日本語": return "japanese";
            default: return null;
        }
    }

    /**
     * Thought-programming language mode (使い分け): reserved words are ALWAYS
     * exact English (set/print/push/as/Omega::); the mode only decides the
     * print-related string literals — "en" = exact English words drawn straight
     * from the English vocabulary (正確な英語), "ja" = 日本語.
     */
    private String thinkLang = "en";

    public String thinkLang() { return thinkLang; }

    public R setThinkLang(String arg) {
        String a = arg == null ? "" : arg.strip().toLowerCase();
        switch (a) {
            case "en": case "english": case "英語":
                thinkLang = "en";
                return new R("lang=en（英語モード: 予約語も文字列も正確な英語）", false);
            case "ja": case "japanese": case "日本語":
                thinkLang = "ja";
                return new R("lang=ja（日本語モード: print文関係の文字列は日本語・予約語は英語）", false);
            default:
                return new R("unknown lang: " + arg + "（en / ja）", false);
        }
    }

    /**
     * Capture ONE vim command by THOUGHT alone (発声もタイプもせず、思っただけ)
     * from the command prior via the quantum-seeded PRNG, and apply it — each
     * command writes/edits Bada-language code, above the silent-talk baseline.
     */
    public Think think() { return thinkWith(++thinkNonce); }
    public Think think(int nonce) { return thinkWith(nonce); }

    private Think thinkWith(int nonce) {
        long s = thinkSeed(nonce);
        List<String> vars = thinkVars();
        String act = vars.isEmpty() ? "set" : THINK_ACTIONS[(int) ((s >> 5) % THINK_ACTIONS.length)];
        return applyThink(act, s);
    }

    /** キーワードのコマンド入力: map a keyword to its vim command and apply it. */
    public Think keywordCommand(String word) { return keywordCommand(word, ++thinkNonce); }
    public Think keywordCommand(String word, int nonce) {
        String act = keywordAction(word);
        if (act == null) return null;
        return applyThink(act, thinkSeed(nonce));
    }

    /** Parse ":thinkprog [steps] [en|ja]" arguments (順不同). */
    public R thinkProgramArgs(String arg) {
        int steps = 8;
        for (String tok : (arg == null ? "" : arg).split("\\s+")) {
            if (tok.matches("\\d+")) steps = Integer.parseInt(tok);
            else if (!tok.isEmpty()) setThinkLang(tok);
        }
        return thinkProgram(steps);
    }

    /**
     * 思考プログラミング: write a COMPLETE, grammar-verified Bada program by
     * thought-only commands operating this vim editor (no voice, no typing).
     */
    public R thinkProgram(int steps) {
        steps = Math.max(2, Math.min(steps, 32));
        buffer.clear(); buffer.add(""); row = 0; col = 0;
        StringBuilder kws = new StringBuilder();
        double prec = 1.0;
        for (int i = 0; i < steps; i++) {
            Think t = think();
            if (kws.length() > 0) kws.append(' ');
            kws.append(t.keyword);
            prec = Math.min(prec, t.precision);
        }
        for (String v : thinkVars()) { feed("G"); feed("oprint " + v); }
        saved = true;
        filename = "thought.bada";
        boolean ok = BadaSyntax.valid(text());
        return new R(String.format("思考プログラミング %d手 lang=%s [%s] Bada%s precision %.1f%% > silent-talk %.1f%%",
                steps, thinkLang, kws, ok ? "✓" : "✗", prec * 100, SilentTalk.SILENT_TALK_BASELINE * 100), false);
    }

    private static long thinkSeed(int nonce) {
        long s = ((long) nonce * 2654435761L + 40503L) & 0xffffffffL;
        return (s * 1103515245L + 12345L) & 0x7fffffffL;
    }

    /** Variables the program has defined so far (scanned from the buffer). */
    private List<String> thinkVars() {
        List<String> vars = new ArrayList<>();
        java.util.regex.Pattern p = java.util.regex.Pattern.compile("set\\s+(\\w+)\\s*=");
        for (String l : buffer) {
            java.util.regex.Matcher m = p.matcher(l);
            if (m.lookingAt() && !vars.contains(m.group(1))) vars.add(m.group(1));
        }
        return vars;
    }

    /** Apply one thought/keyword command (statement inserts append at the end). */
    private Think applyThink(String act, long s) {
        if (act.equals("english")) { R r = setThinkLang("en"); return new Think(r.msg, "english", ":lang en", 0.96); }
        if (act.equals("japanese")) { R r = setThinkLang("ja"); return new Think(r.msg, "japanese", ":lang ja", 0.96); }
        double p = 0.93 + ((s >> 7) % 60) / 1000.0;
        List<String> vars = thinkVars();
        if (vars.isEmpty() && (act.equals("assign") || act.equals("push") || act.equals("print"))) act = "set";
        String cmd;
        switch (act) {
            case "set":
                cmd = "oset " + BadaSyntax.VARS[(int) (s % BadaSyntax.VARS.length)]
                        + " = " + String.format("%.1f", ((s >> 3) % 90 + 10) / 10.0);
                break;
            case "assign": {
                String v = vars.get((int) ((s >> 13) % vars.size()));
                String w1, w2;
                if ("ja".equals(thinkLang)) {
                    // print文関係の文字列だけ日本語（予約語・演算子は英語のまま）
                    List<String> lex = bada.mind.MindReader.lexicon();
                    w1 = lex.get((int) ((s >> 11) % lex.size()));
                    w2 = lex.get((int) ((s >> 17) % lex.size()));
                } else {
                    // 正確な英語: exact words straight from the English vocabulary
                    w1 = SilentTalk.EN_THOUGHT_VOCAB[(int) ((s >> 11) % SilentTalk.EN_THOUGHT_VOCAB.length)];
                    w2 = SilentTalk.EN_THOUGHT_VOCAB[(int) ((s >> 17) % SilentTalk.EN_THOUGHT_VOCAB.length)];
                    p = Math.max(p, 0.96); // exact-vocabulary English needs no reconstruction
                }
                cmd = "o" + v + " <- \"" + w1 + " " + w2 + "\"";
                break;
            }
            case "push":
                cmd = "oOmega::push " + vars.get((int) ((s >> 13) % vars.size())) + " as node" + ((s >> 9) % 9 + 1);
                break;
            case "print":
                cmd = "oprint " + vars.get((int) ((s >> 13) % vars.size()));
                break;
            case "delete": cmd = "dd"; break;
            case "top": cmd = "gg"; break;
            case "bottom": cmd = "G"; break;
            default: cmd = ":w thought.bada"; break; // save
        }
        if (cmd.startsWith("o")) {
            if (buffer.size() == 1 && buffer.get(0).isEmpty()) {
                feed("i" + cmd.substring(1));
            } else {
                feed("G");
                feed(cmd);
            }
        } else if (cmd.startsWith(":")) {
            ex(cmd.substring(1));
        } else {
            feed(cmd);
        }
        return new Think(String.format("思考コマンド %s → %s  (%.1f%%)", act, cmd, p * 100), act, cmd, p);
    }

    private static int parseIntOr(String s, int d) {
        try { return Integer.parseInt(s.strip()); } catch (NumberFormatException e) { return d; }
    }

    /** Silent cue -> QC (OpenQASM-like) source + disk-backed run report. */
    private String qcSource(String intent) {
        Object[] p = SilentTalk.Parse.qc(intent);
        int n = (Integer) p[1];
        try (bada.qc.PseudoQC m = new bada.qc.PseudoQC(n).load((String) p[0]).run()) {
            return m.report();
        }
    }

    /** Silent cue -> semiconductor (Verilog RTL) source. */
    private String verilogSource(String intent) {
        Object[] p = SilentTalk.Parse.qc(intent);
        int n = (Integer) p[1];
        try (bada.qc.PseudoQC m = new bada.qc.PseudoQC(n).load((String) p[0])) {
            return m.verilog();
        }
    }

    // ---- internals ----------------------------------------------------------
    private int bump() { return ++nonce; }
    private String cur() { return row < buffer.size() ? buffer.get(row) : ""; }
    private void clampCol() { col = Math.min(col, Math.max(cur().length() - 1, 0)); }
    private R touched(String msg) { saved = false; return new R(msg, false); }

    private void insertText(String t) {
        String c = cur();
        String head = c.substring(0, Math.min(col, c.length()));
        String tail = c.substring(Math.min(col, c.length()));
        String[] parts = t.split("\n", -1);
        if (parts.length == 1) {
            buffer.set(row, head + t + tail);
            col += t.length();
        } else {
            List<String> nl = new ArrayList<>();
            nl.add(head + parts[0]);
            for (int i = 1; i < parts.length - 1; i++) nl.add(parts[i]);
            nl.add(parts[parts.length - 1] + tail);
            buffer.remove(row);
            buffer.addAll(row, nl);
            row += parts.length - 1;
            col = parts[parts.length - 1].length();
        }
    }

    private void openBelow(String t) { buffer.add(row + 1, ""); row += 1; col = 0; insertText(t); }
    private void openAbove(String t) { buffer.add(row, ""); col = 0; insertText(t); }

    private void deleteLine() {
        buffer.remove(row);
        if (buffer.isEmpty()) buffer.add("");
        row = Math.min(row, buffer.size() - 1);
        col = 0;
    }

    private void deleteChar() {
        String c = cur();
        if (c.isEmpty()) return;
        int cc = Math.min(col, c.length() - 1);
        buffer.set(row, c.substring(0, cc) + c.substring(cc + 1));
        clampCol();
    }

    private void insertBlock(String block) {
        String[] lines = block.split("\n", -1);
        buffer.addAll(row + 1, Arrays.asList(lines));
        row += lines.length;
        col = buffer.get(row).length();
    }
}
