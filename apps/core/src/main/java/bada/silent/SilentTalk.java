package bada.silent;

import bada.mind.MindReader;
import bada.coder.Coder;

import java.util.ArrayList;
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

    public enum Mode { TEXT, CODE }

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
        public String kind;             // text | code | command | noop
        public String verbalization;    // text
        public String code, language;   // code
        public boolean recipe;          // code
        public double precision;        // text | code
        public List<String> appended;   // text | code
        public String output;           // command
    }

    public static final class Session {
        private Mode mode = Mode.TEXT;
        private String language = null;      // code language (null = auto)
        private final MindReader mind;
        private final List<Block> blocks = new ArrayList<>();

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
            return mode == Mode.CODE ? codeInput(line) : textInput(line);
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

        /** Word completion for the current mode. */
        public List<String> complete(String prefix, int limit) {
            if (prefix == null || prefix.isEmpty()) return new ArrayList<>();
            if (mode == Mode.CODE) return Coder.complete(prefix, language, limit);
            List<String> out = new ArrayList<>();
            for (String w : textVocab()) {
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
                 + "  発声せず、疎な手がかりを入力すると文章に言語化します。\n"
                 + "  コマンド: :text :code :lang <l> :complete <prefix> :undo :clear :show :precision :help :quit";
        }

        private String help() {
            return ":text 言語化入力 / :code コード入力 / :lang <ruby|python…> / "
                 + ":complete <prefix> 補完 / :undo 取消 / :clear / :show / :precision / :quit";
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
    }
}
