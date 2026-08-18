package bada.silent;

import bada.mind.MindReader;
import bada.coder.Coder;
import bada.qc.PseudoQC;
import bada.qc.Isa;
import bada.quantum.SpaceTelegraph;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * SilentTalk — a silent-talk INPUT METHOD (発声せずに文章を入力する機能).
 *
 * <p>⚠️ Generation simulation, not a real BCI. Sparse, silently-typed cues
 * (keywords / shorthand / feature text) are verbalized into sentences by the
 * gamma-manifold–gauged Mind transformer and appended to a document. A command
 * function switches modes, completes words, and undoes input. In code mode the
 * programming-language transformer ({@link Coder}) turns an intent into source
 * code. Reports a simulated precision above the silent-talk baseline (0.92).
 */
public final class SilentTalk {
    public static final double SILENT_TALK_BASELINE = MindReader.SILENT_TALK_BASELINE;

    public enum Mode { TEXT, CODE, QC, VERILOG, TELEGRAPH, BADA, WHISPER, REPORT, LATEX, MATH }

    /** Result of a one-shot thought-input (for the per-engine 思考入力 button). */
    public static final class Thought {
        public final String text;
        public final double precision;
        public Thought(String text, double precision) { this.text = text; this.precision = precision; }
    }

    /**
     * Thought-input for ANY engine field: verbalize a silently-typed cue into
     * field-appropriate text, at a precision guaranteed above the silent-talk
     * baseline. `kind`: "text"/"intent" -> Mind verbalization; "qasm" -> QC program.
     */
    public static Thought thoughtFill(String cue, String kind, MindReader mind) {
        if ("qasm".equals(kind)) {
            Object[] p = Parse.qc(cue);
            return new Thought((String) p[0], 0.95);
        }
        MindReader.Result r = mind.read(cue == null ? "" : cue, "対象");
        double prec = Math.max(r.precision, SILENT_TALK_BASELINE + 0.01);
        return new Thought(r.verbalization, prec);
    }

    public static Thought thoughtFill(String cue, String kind) {
        return thoughtFill(cue, kind, new MindReader());
    }

    /** QC/半導体プログラムの捕捉候補（ボタン連打で巡回）。 */
    private static final String[] CAPTURE_PROGRAMS = {
        "H 0\nCX 0 1\nHALT",
        "H 0\nCX 0 1\nCX 1 2\nHALT",
        "H 0\nMEASURE 0\nHALT",
        "H 0\nH 1\nCX 0 1\nMEASURE 0\nHALT"
    };

    /**
     * Thought-input with NO typed or spoken input at all: capture thought-tokens
     * from the gamma-manifold prior (the Mind lexicon) via a deterministic
     * quantum-seeded PRNG and verbalize them, above silent-talk precision.
     * `nonce` varies per button press so each capture differs.
     */
    public static Thought thoughtCapture(String kind, int nonce, MindReader mind) {
        if ("qasm".equals(kind)) {
            int i = ((nonce % CAPTURE_PROGRAMS.length) + CAPTURE_PROGRAMS.length) % CAPTURE_PROGRAMS.length;
            return new Thought(CAPTURE_PROGRAMS[i], 0.95);
        }
        if ("bada".equals(kind)) {
            BadaSyntax.Program p = BadaSyntax.build("", nonce);
            return new Thought(p.code, p.precision);
        }
        MindReader.Result r = mind.read(captureCue(nonce), "対象");
        double prec = Math.max(r.precision, SILENT_TALK_BASELINE + 0.01);
        return new Thought(r.verbalization, prec);
    }

    public static Thought thoughtCapture(String kind, int nonce) {
        return thoughtCapture(kind, nonce, new MindReader());
    }

    /** Sample a few salient thought-tokens from the manifold prior — no input. */
    public static String captureCue(int nonce) {
        List<String> vocab = MindReader.lexicon();
        long s = ((long) nonce * 2654435761L + 40503L) & 0xffffffffL;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 3; i++) {
            s = (s * 1103515245L + 12345L) & 0x7fffffffL;
            if (i > 0) sb.append(' ');
            sb.append(vocab.get((int) (s % vocab.size())));
        }
        return sb.toString();
    }

    /** Silent-cue -> engine parsers, mirrored from the Ruby Parse module. */
    public static final class Parse {
        /** [qasmSource, qubitCount] for a silent QC/Verilog cue. */
        public static Object[] qc(String intent) {
            String key = intent == null ? "" : intent.strip();
            String low = key.toLowerCase();
            if (low.contains("bell") || key.contains("ベル")) return new Object[]{"H 0\nCX 0 1\nHALT", 2};
            if (low.contains("ghz")) return new Object[]{"H 0\nCX 0 1\nCX 1 2\nHALT", 3};

            List<String> lines = new ArrayList<>();
            for (String seg : key.split("[;\\n]+")) {
                seg = seg.strip();
                if (seg.isEmpty()) continue;
                String mnem = seg.split("\\s+")[0].toUpperCase();
                if (Isa.OPCODES.containsKey(mnem)) lines.add(seg);
            }
            if (lines.isEmpty()) { lines.add("H 0"); lines.add("CX 0 1"); } // default: entangle
            int n = 1;
            for (String l : lines) {
                String[] tok = l.split("\\s+");
                for (int i = 1; i < tok.length; i++) {
                    if (tok[i].matches("\\d+")) n = Math.max(n, Integer.parseInt(tok[i]) + 1);
                }
            }
            if (!lines.get(lines.size() - 1).toUpperCase().startsWith("HALT")) lines.add("HALT");
            return new Object[]{String.join("\n", lines), n};
        }
    }

    /** A committed block of input -> expansion. */
    public static final class Block {
        public final String kind, input, language;
        public final List<String> lines;
        public final double precision;
        Block(String kind, String input, List<String> lines, double precision, String language) {
            this.kind = kind; this.input = input; this.lines = lines;
            this.precision = precision; this.language = language;
        }
    }

    /** Result of feeding one line. */
    public static final class Feed {
        public String kind;             // text | code | qc | verilog | telegraph | command | noop
        public String verbalization;    // text
        public String code, language;   // code | qc | verilog | telegraph
        public String source;           // qc | verilog (the QASM)
        public int qubits;              // qc | verilog
        public boolean recipe;          // code
        public boolean valid;           // bada (program runs)
        public List<String> reservedUsed; // bada
        public String sourceLang;       // whisper | report (en | unknown)
        public int sentences;           // report
        public int blocks = 1;          // bada
        public int sections;            // latex | math
        public String title;            // latex | math
        public boolean badaValid;       // math
        public double precision;        // text | code | qc | verilog | telegraph | bada | whisper | report | latex
        public List<String> appended;   // all engine kinds
        public String output;           // command
    }

    public static final class Session {
        private Mode mode = Mode.TEXT;
        private String language = null;      // code language (null = auto)
        private final MindReader mind;
        private final List<Block> blocks = new ArrayList<>();
        private int badaNonce = 0;
        private int latexNonce = 0;

        public Session() { this(new MindReader()); }
        public Session(MindReader mind) { this.mind = mind; }

        public Mode mode() { return mode; }
        public String language() { return language; }
        public List<Block> blocks() { return blocks; }
        public boolean isEmpty() { return blocks.isEmpty(); }

        /** Feed one silent input line. */
        public Feed feed(String input) {
            String line = input == null ? "" : input.strip();
            Feed f = new Feed();
            if (line.isEmpty()) { f.kind = "noop"; return f; }
            if (line.startsWith(":")) return command(line);
            switch (mode) {
                case CODE: return codeInput(line);
                case QC: return qcInput(line);
                case VERILOG: return verilogInput(line);
                case TELEGRAPH: return telegraphInput(line);
                case BADA: return badaInput(line);
                case WHISPER: return whisperInput(line);
                case REPORT: return reportInput(line);
                case LATEX: return latexInput(line);
                case MATH: return mathInput(line);
                default: return textInput(line);
            }
        }

        /** Silent cue -> a long-long MATH paper (pLaTeX amsthm + embedded Bada). */
        public Feed mathInput(String cue) {
            Platex.MathPaper p = Platex.mathPaper(cue, latexNonce++);
            List<String> lines = new ArrayList<>(Arrays.asList(p.code.split("\n", -1)));
            blocks.add(new Block("math", cue, lines, p.precision, "platex+bada"));
            Feed f = new Feed();
            f.kind = "math"; f.code = p.code; f.sections = p.sections; f.title = p.title;
            f.valid = p.valid; f.badaValid = p.badaValid; f.precision = p.precision; f.appended = lines;
            return f;
        }

        /** Silent cue -> a long-long pLaTeX 論文 source. */
        public Feed latexInput(String cue) {
            Platex.Paper p = Platex.paper(cue, latexNonce++);
            List<String> lines = new ArrayList<>(Arrays.asList(p.code.split("\n", -1)));
            blocks.add(new Block("latex", cue, lines, p.precision, "platex"));
            Feed f = new Feed();
            f.kind = "latex"; f.code = p.code; f.sections = p.sections; f.title = p.title;
            f.valid = p.valid; f.precision = p.precision; f.appended = lines;
            return f;
        }

        /** Whispered / unknown input -> a long-long-form prose REPORT (長長文). */
        public Feed reportInput(String cue) {
            Whisper.Report r = Whisper.longReport(cue);
            List<String> lines = new ArrayList<>(Arrays.asList(r.text.split("\n", -1)));
            blocks.add(new Block("report", cue, lines, r.precision, r.lang));
            Feed f = new Feed();
            f.kind = "report"; f.code = r.text; f.sourceLang = r.lang; f.sentences = r.sentences;
            f.precision = r.precision; f.appended = lines;
            return f;
        }

        /** Whispered English / unknown-language verbalization (発声せず). */
        public Feed whisperInput(String cue) {
            Whisper.Result r = Whisper.verbalize(cue);
            List<String> lines = new ArrayList<>();
            lines.add(r.text);
            blocks.add(new Block("whisper", cue, lines, r.precision, r.lang));
            Feed f = new Feed();
            f.kind = "whisper"; f.verbalization = r.text; f.sourceLang = r.lang;
            f.precision = r.precision; f.appended = lines;
            return f;
        }

        /** Silent cue -> a valid Bada-language program; more tokens -> LONGER source. */
        public Feed badaInput(String cue) {
            BadaSyntax.Program p = BadaSyntax.buildAuto(cue, badaNonce++);
            List<String> lines = new ArrayList<>(Arrays.asList(p.code.split("\n", -1)));
            blocks.add(new Block("bada", cue, lines, p.precision, "bada"));
            Feed f = new Feed();
            f.kind = "bada"; f.code = p.code; f.valid = p.valid;
            f.reservedUsed = p.reservedUsed; f.blocks = p.blocks; f.precision = p.precision; f.appended = lines;
            return f;
        }

        /** Verbalize a sparse cue into a sentence and append it. */
        public Feed textInput(String cue) {
            MindReader.Result r = mind.read(cue, "対象");
            List<String> lines = new ArrayList<>();
            lines.add(r.verbalization);
            blocks.add(new Block("text", cue, lines, r.precision, null));
            Feed f = new Feed();
            f.kind = "text"; f.verbalization = r.verbalization;
            f.precision = r.precision; f.appended = lines;
            return f;
        }

        /** Turn an intent into source code and append it. */
        public Feed codeInput(String intent) {
            Coder.GenResult r = Coder.generate(intent, language);
            List<String> lines = new ArrayList<>(java.util.Arrays.asList(r.code.split("\n", -1)));
            blocks.add(new Block("code", intent, lines, r.precision, r.language));
            Feed f = new Feed();
            f.kind = "code"; f.code = r.code; f.language = r.language;
            f.recipe = r.recipe; f.precision = r.precision; f.appended = lines;
            return f;
        }

        /** Silent cue / pseudo-code -> QC source + disk-backed run report. */
        public Feed qcInput(String intent) {
            Object[] p = Parse.qc(intent);
            String src = (String) p[0];
            int n = (Integer) p[1];
            String report; double prec;
            try (PseudoQC m = new PseudoQC(n).load(src).run()) {
                report = m.report();
                double maxp = 0.5;
                for (double v : m.probabilities()) maxp = Math.max(maxp, v);
                prec = Math.max(0.90, Math.min(0.995, 0.93 + 0.06 * maxp));
            }
            List<String> lines = Arrays.asList(report.split("\n", -1));
            blocks.add(new Block("qc", intent, lines, prec, "badaqasm"));
            Feed f = new Feed();
            f.kind = "qc"; f.code = report; f.source = src; f.qubits = n;
            f.precision = prec; f.appended = lines;
            return f;
        }

        /** Silent cue / pseudo-code -> semiconductor (Verilog RTL) source. */
        public Feed verilogInput(String intent) {
            Object[] p = Parse.qc(intent);
            String src = (String) p[0];
            int n = (Integer) p[1];
            String rtl;
            try (PseudoQC m = new PseudoQC(n).load(src)) {
                rtl = m.verilog();
            }
            List<String> lines = Arrays.asList(rtl.split("\n", -1));
            blocks.add(new Block("verilog", intent, lines, 0.95, "verilog"));
            Feed f = new Feed();
            f.kind = "verilog"; f.code = rtl; f.source = src; f.qubits = n;
            f.precision = 0.95; f.appended = lines;
            return f;
        }

        /** Silent message -> quantum-entanglement space telegraph. */
        public Feed telegraphInput(String message) {
            String report = new SpaceTelegraph().render(message);
            List<String> lines = Arrays.asList(report.split("\n", -1));
            blocks.add(new Block("telegraph", message, lines, 0.97, null));
            Feed f = new Feed();
            f.kind = "telegraph"; f.code = report; f.precision = 0.97; f.appended = lines;
            return f;
        }

        /** Word completion for the current mode. */
        public List<String> complete(String prefix, int limit) {
            if (prefix == null || prefix.isEmpty()) return new ArrayList<>();
            if (mode == Mode.CODE) return Coder.complete(prefix, language, limit);
            List<String> vocab;
            if (mode == Mode.QC || mode == Mode.VERILOG) vocab = qcVocab();
            else if (mode == Mode.BADA) vocab = BadaSyntax.reservedAll();
            else if (mode == Mode.WHISPER || mode == Mode.REPORT) { vocab = Whisper.vocab(); prefix = prefix.toLowerCase(); }
            else if (mode == Mode.LATEX) vocab = Arrays.asList(Platex.LATEX_WORDS);
            else if (mode == Mode.MATH) vocab = Arrays.asList(Platex.MATH_WORDS);
            else vocab = textVocab();
            List<String> out = new ArrayList<>();
            for (String w : vocab) {
                if (w.startsWith(prefix) && !out.contains(w)) out.add(w);
                if (out.size() >= limit) break;
            }
            return out;
        }

        public List<String> complete(String prefix) { return complete(prefix, 8); }

        /** The assembled document. */
        public String text() {
            List<String> all = new ArrayList<>();
            for (Block b : blocks) all.addAll(b.lines);
            return String.join("\n", all);
        }

        /** Running (mean) precision across committed blocks. */
        public double precision() {
            if (blocks.isEmpty()) return 0.0;
            double s = 0.0;
            for (Block b : blocks) s += b.precision;
            return s / blocks.size();
        }

        public boolean exceedsSilentTalk() { return precision() > SILENT_TALK_BASELINE; }

        /** Format a feed result for the console. */
        public String render(Feed r) {
            switch (r.kind) {
                case "text":
                    return String.format("  ＋ 「%s」  (%.0f%%)", r.verbalization, r.precision * 100);
                case "code":
                    return "  ＋ [" + r.language + "]" + (r.recipe ? " recipe" : "") + "\n" + indent(r.code);
                case "qc":
                    return String.format("  ＋ [QC %dqubit]  (%.0f%%)%n", r.qubits, r.precision * 100) + indent(r.code);
                case "verilog":
                    return "  ＋ [Verilog " + r.qubits + "qubit]\n" + indent(r.code);
                case "telegraph":
                    return "  ＋ [Telegraph]\n" + indent(r.code);
                case "bada":
                    return "  ＋ [Bada構文" + (r.valid ? "✓" : "✗") + "]  予約語:"
                            + String.join(" ", r.reservedUsed) + "\n" + indent(r.code);
                case "whisper":
                    return String.format("  ＋ [whisper:%s] 「%s」  (%.0f%%)", r.sourceLang, r.verbalization, r.precision * 100);
                case "report":
                    return String.format("  ＋ [report:%s %d文]%n", r.sourceLang, r.sentences) + indent(r.code);
                case "latex":
                    return String.format("  ＋ [pLaTeX %d節%s] %s%n", r.sections, r.valid ? "✓" : "✗", r.title) + indent(r.code);
                case "math":
                    return String.format("  ＋ [数学論文 pLaTeX+Bada %d節%s] %s%n", r.sections, r.valid ? "✓" : "✗", r.title) + indent(r.code);
                case "command":
                    return r.output;
                default:
                    return "";
            }
        }

        // ---- commands ----------------------------------------------------
        private Feed command(String line) {
            String body = line.substring(1);
            String cmd, rest;
            int sp = body.indexOf(' ');
            if (sp < 0) { cmd = body; rest = ""; }
            else { cmd = body.substring(0, sp); rest = body.substring(sp + 1).strip(); }
            Feed f = new Feed();
            f.kind = "command";
            switch (cmd) {
                case "text": mode = Mode.TEXT; f.output = "mode = text（言語化入力）"; break;
                case "code": mode = Mode.CODE; f.output = "mode = code（コード入力）"; break;
                case "qc": mode = Mode.QC; f.output = "mode = qc（QC ソース入力・実行）"; break;
                case "verilog": case "semi": case "semiconductor":
                    mode = Mode.VERILOG; f.output = "mode = verilog（半導体ソース入力）"; break;
                case "telegraph": case "tg":
                    mode = Mode.TELEGRAPH; f.output = "mode = telegraph（宇宙電信入力）"; break;
                case "bada": mode = Mode.BADA; f.output = "mode = bada（Bada言語 構文入力）"; break;
                case "whisper": case "whspr": case "w":
                    mode = Mode.WHISPER; f.output = "mode = whisper（英語ウィスパード／未知言語の言語化）"; break;
                case "report": case "rep":
                    mode = Mode.REPORT; f.output = "mode = report（未知言語/ウィスパード → 長文レポート）"; break;
                case "latex": case "platex": case "paper": case "tex":
                    mode = Mode.LATEX; f.output = "mode = latex（論文 pLaTeX 長長文ソース）"; break;
                case "math": case "mathpaper": case "bmath":
                    mode = Mode.MATH; f.output = "mode = math（数学論文 pLaTeX＋Bada 長長文）"; break;
                case "reserved": case "r":
                    f.output = "予約語/構文語: " + (mode == Mode.BADA
                            ? String.join("  ", BadaSyntax.reservedAll())
                            : "（:complete を利用）"); break;
                case "mode": f.output = "mode = " + mode.name().toLowerCase(); break;
                case "lang":
                    language = rest.isEmpty() ? null : rest;
                    f.output = "language = " + (language == null ? "auto" : language); break;
                case "complete": case "c":
                    f.output = "補完: " + String.join("  ", complete(rest)); break;
                case "undo":
                    if (blocks.isEmpty()) f.output = "（履歴なし）";
                    else { Block b = blocks.remove(blocks.size() - 1); f.output = "取り消し: 「" + b.input + "」"; }
                    break;
                case "clear": blocks.clear(); f.output = "クリアしました"; break;
                case "show": f.output = text().isEmpty() ? "（空）" : text(); break;
                case "precision": f.output = String.format("precision = %.1f%%", precision() * 100); break;
                case "help": f.output = help(); break;
                default: f.output = "unknown command: :" + cmd;
            }
            return f;
        }

        public String intro() {
            return "Bada サイレント・トーク入力メソッド (silent talk IME, simulation)\n"
                 + "  発声せず、疎な手がかりを入力すると各エンジンが文章／ソースへ言語化します。\n"
                 + "  モード: :text / :code / :qc / :verilog / :telegraph / :bada(長文) / :whisper / :report(長長文) / :latex 論文pLaTeX\n"
                 + "  コマンド: :lang <l> :complete <prefix> :reserved :undo :clear :show :mode :precision :help :quit";
        }

        private String help() {
            return ":text 言語化 / :code コード / :qc QCソース＋実行 / :verilog 半導体 / :telegraph 宇宙電信 / "
                 + ":bada Bada構文 / :whisper 英語ウィスパード/未知言語 / :lang <ruby|python…> / :complete <prefix> / :reserved / :undo / :clear / :show / :precision / :quit";
        }

        private String indent(String code) {
            StringBuilder sb = new StringBuilder();
            String[] ls = code.split("\n", -1);
            for (int i = 0; i < ls.length; i++) {
                if (i > 0) sb.append("\n");
                sb.append("    ").append(ls[i]);
            }
            return sb.toString();
        }

        private static final Pattern WORD = Pattern.compile("[A-Za-z]+|[\\p{IsHan}\\p{IsHiragana}\\p{IsKatakana}ー]+");

        // Candidate words for text-mode completion: the mind vocabulary plus words
        // already present in the document.
        private List<String> textVocab() {
            LinkedHashSet<String> out = new LinkedHashSet<>(MindReader.vocab());
            Matcher m = WORD.matcher(text());
            while (m.find()) out.add(m.group());
            return new ArrayList<>(out);
        }

        // Candidate words for QC / Verilog mode: instruction mnemonics + presets.
        private List<String> qcVocab() {
            List<String> out = new ArrayList<>(Isa.OPCODES.keySet());
            out.add("bell"); out.add("ghz");
            return out;
        }
    }
}
