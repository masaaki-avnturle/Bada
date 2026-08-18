package bada.silent;

import bada.mind.MindReader;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Bada-language SILENT SYNTAX INPUT: reserved words, syntax-rule operators and
 * statement templates of the Bada language, generated without any vocalization.
 * Mirrors {@code Bada::SilentTalk::BadaSyntax} (same PRNG, same templates), and
 * validates each program against the Bada grammar the interpreter accepts.
 */
public final class BadaSyntax {
    public static final String[] RESERVED   = {"set", "print", "as", "push"};      // 予約語
    public static final String[] NAMESPACES = {"Omega::", "Ω::"};                  // TupleSpace 名前空間
    public static final String[] OPERATORS  = {"<-", "-<", ">-"};                  // 構文規則の演算子
    public static final String ASSIGN = "=";
    private static final String[] VARS = {"g", "h", "m", "psi", "phi", "node", "xi"};

    // The Bada statement forms (what the interpreter accepts).
    private static final Pattern[] FORMS = {
        Pattern.compile("^set\\s+\\w+\\s*=\\s*.+$"),
        Pattern.compile("^\\w+\\s*(<-|-<|>-)\\s*.+$"),
        Pattern.compile("^(Omega|Ω)::push\\s+\\w+(\\s+as\\s+\\w+)?$"),
        Pattern.compile("^print\\s+.+$")
    };
    private static final Pattern WORD = Pattern.compile("[A-Za-z]+|[\\p{IsHan}\\p{IsHiragana}\\p{IsKatakana}ー]+");

    /** All reserved / syntax-rule words (for completion & recognition). */
    public static List<String> reservedAll() {
        List<String> out = new ArrayList<>(Arrays.asList(RESERVED));
        out.addAll(Arrays.asList(NAMESPACES));
        out.addAll(Arrays.asList(OPERATORS));
        out.add(ASSIGN);
        return out;
    }

    /** Which reserved / syntax words appear in a line (予約語の自動認識). */
    public static List<String> reservedWords(String line) {
        List<String> all = reservedAll();
        List<String> out = new ArrayList<>();
        for (String t : line.trim().split("\\s+")) if (all.contains(t)) out.add(t);
        return out;
    }

    public static final class Program {
        public final String code;
        public final boolean valid;
        public final List<String> reservedUsed;
        public final double precision;
        public int blocks = 1;
        Program(String code, boolean valid, List<String> reservedUsed, double precision) {
            this.code = code; this.valid = valid; this.reservedUsed = reservedUsed; this.precision = precision;
        }
    }

    /** Build a syntactically valid Bada program without voice (mirrors the Ruby PRNG). */
    public static Program build(String cue, int nonce) {
        final long[] s = { ((long) nonce * 2654435761L + 40503L) & 0xffffffffL };
        java.util.function.LongSupplier nxt = () -> (s[0] = (s[0] * 1103515245L + 12345L) & 0x7fffffffL);

        List<String> words = new ArrayList<>();
        Matcher m = WORD.matcher(cue == null ? "" : cue);
        while (m.find()) words.add(m.group());
        if (words.isEmpty()) {
            List<String> lex = MindReader.lexicon();
            for (int i = 0; i < 2; i++) words.add(lex.get((int) (nxt.getAsLong() % lex.size())));
        }

        String v = VARS[(int) (nxt.getAsLong() % VARS.length)];
        double num1 = (nxt.getAsLong() % 90 + 10) / 10.0;
        double num2 = (nxt.getAsLong() % 40 + 10) / 10.0;
        String op = OPERATORS[(int) (nxt.getAsLong() % OPERATORS.length)];
        String key = "node" + (nxt.getAsLong() % 9 + 1);
        StringBuilder lit = new StringBuilder();
        for (int i = 0; i < Math.min(3, words.size()); i++) { if (i > 0) lit.append(' '); lit.append(words.get(i)); }

        List<String> lines = new ArrayList<>();
        lines.add("set " + v + " = " + num(num1));
        lines.add(v + " <- \"" + lit + "\"");
        lines.add(op.equals(">-") ? (v + " >- " + v) : (v + " " + op + " " + num(num2)));
        lines.add("Omega::push " + v + " as " + key);
        lines.add("print " + v);
        String code = String.join("\n", lines);

        boolean ok = valid(code);
        List<String> used = new ArrayList<>();
        for (String w : reservedAll()) if (!w.equals(ASSIGN) && code.contains(w)) used.add(w);
        return new Program(code, ok, used, ok ? 0.96 : 0.90);
    }

    /** Write a LONG Bada program (長文ソースコード): `blocks` variable lifecycles. */
    public static Program buildLong(String cue, int blocks, int nonce) {
        blocks = Math.max(1, Math.min(16, blocks));
        final long[] s = { ((long) nonce * 2654435761L + 40503L) & 0xffffffffL };
        java.util.function.LongSupplier nxt = () -> (s[0] = (s[0] * 1103515245L + 12345L) & 0x7fffffffL);

        List<String> cueWords = new ArrayList<>();
        Matcher m = WORD.matcher(cue == null ? "" : cue);
        while (m.find()) cueWords.add(m.group());

        List<String> lines = new ArrayList<>();
        List<String> vars = new ArrayList<>();
        List<String> lex = MindReader.lexicon();
        for (int bi = 0; bi < blocks; bi++) {
            List<String> words;
            if (bi == 0 && !cueWords.isEmpty()) {
                words = cueWords;
            } else {
                words = new ArrayList<>();
                for (int i = 0; i < 2; i++) words.add(lex.get((int) (nxt.getAsLong() % lex.size())));
            }
            String v = VARS[(int) (nxt.getAsLong() % VARS.length)] + bi;
            vars.add(v);
            double num1 = (nxt.getAsLong() % 90 + 10) / 10.0;
            double num2 = (nxt.getAsLong() % 40 + 10) / 10.0;
            String op = OPERATORS[(int) (nxt.getAsLong() % OPERATORS.length)];
            StringBuilder lit = new StringBuilder();
            for (int i = 0; i < Math.min(3, words.size()); i++) { if (i > 0) lit.append(' '); lit.append(words.get(i)); }
            lines.add("set " + v + " = " + num(num1));
            lines.add(v + " <- \"" + lit + "\"");
            lines.add(op.equals(">-") ? (v + " >- " + v) : (v + " " + op + " " + num(num2)));
            lines.add("Omega::push " + v + " as node" + (bi + 1));
        }
        for (String v : vars) lines.add("print " + v);
        String code = String.join("\n", lines);

        boolean ok = valid(code);
        List<String> used = new ArrayList<>();
        for (String w : reservedAll()) if (!w.equals(ASSIGN) && code.contains(w)) used.add(w);
        Program p = new Program(code, ok, used, ok ? 0.96 : 0.90);
        p.blocks = blocks;
        return p;
    }

    /** Choose long or short by how many thought-tokens the cue carries. */
    public static Program buildAuto(String cue, int nonce) {
        int n = tokenCount(cue);
        if (n >= 2) return buildLong(cue, Math.max(2, Math.min(10, n)), nonce);
        return build(cue, nonce);
    }

    /** A VERY long Bada program (長長文ソース): 8-12 variable lifecycles. */
    public static Program buildVeryLong(String cue, int nonce) {
        int n = tokenCount(cue);
        return buildLong(cue, Math.max(8, Math.min(12, n * 2)), nonce);
    }

    private static int tokenCount(String cue) {
        int n = 0;
        Matcher m = WORD.matcher(cue == null ? "" : cue);
        while (m.find()) n++;
        return n;
    }

    // Match Ruby's Float#to_s for one-decimal values (7.9, 8.0).
    private static String num(double d) {
        if (d == Math.floor(d)) return (long) d + ".0";
        return String.valueOf(Math.round(d * 10.0) / 10.0);
    }

    /** A program is accepted only if every statement matches a Bada grammar form. */
    public static boolean valid(String code) {
        for (String raw : code.split("\n", -1)) {
            String line = raw.replaceAll("#.*$", "").trim();
            if (line.isEmpty()) continue;
            boolean any = false;
            for (Pattern f : FORMS) if (f.matcher(line).matches()) { any = true; break; }
            if (!any) return false;
        }
        return true;
    }

    private BadaSyntax() { }
}
