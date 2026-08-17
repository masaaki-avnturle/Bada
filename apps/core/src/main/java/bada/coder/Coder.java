package bada.coder;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Bada::Coder (Java port) — thought-to-code (simulation). Bilingual (English +
 * 日本語) intent, automatic programming-language detection, reserved-word
 * recognition, word completion, and code generation. Not a brain interface.
 */
public final class Coder {
    public static final double SILENT_TALK_BASELINE = 0.92;

    static final class Spec {
        final String[] keywords, builtins;
        final Pattern[] hints;
        Spec(String[] k, String[] b, String[] h) {
            keywords = k; builtins = b;
            hints = new Pattern[h.length];
            for (int i = 0; i < h.length; i++) hints[i] = Pattern.compile(h[i]);
        }
    }

    static final Map<String, Spec> LANGUAGES = new LinkedHashMap<>();
    static {
        LANGUAGES.put("ruby", new Spec(
            "def end if elsif else unless while until for do class module return yield begin rescue ensure then case when next break and or not nil true false self super lambda in".split(" "),
            "puts print p require require_relative attr_accessor attr_reader new each map select reduce times loop raise proc".split(" "),
            new String[]{"\\bdef\\b[\\s\\S]*\\bend\\b", "\\bputs\\b", "\\.each\\b", "\\bunless\\b"}));
        LANGUAGES.put("python", new Spec(
            "def return if elif else while for in import from class lambda None True False try except finally with as pass yield global nonlocal assert del raise not and or is break continue".split(" "),
            "print range len int str list dict set input open enumerate zip map filter sum min max sorted type isinstance".split(" "),
            new String[]{"\\bdef\\b[^\\n]*:", "\\bprint\\(", "\\belif\\b", "\\brange\\("}));
        LANGUAGES.put("javascript", new Spec(
            "function var let const if else for while do return class new this typeof instanceof switch case break continue try catch finally throw import export default async await yield of in".split(" "),
            "console log document window Array Object Math JSON Promise map filter reduce forEach push length parseInt parseFloat".split(" "),
            new String[]{"\\bfunction\\b", "console\\.log", "=>", "\\bconst\\b", "\\blet\\b"}));
        LANGUAGES.put("c", new Spec(
            "int char float double void short long unsigned signed if else for while do switch case break continue return struct union enum typedef const static sizeof goto".split(" "),
            "printf scanf malloc free include stdio main puts fgets memcpy strlen".split(" "),
            new String[]{"#include", "\\bprintf\\(", "\\bint\\s+main\\b", "\\bvoid\\b"}));
        LANGUAGES.put("java", new Spec(
            "public private protected class interface static final void abstract if else for while do switch case break continue return new this super extends implements import package try catch finally throw throws".split(" "),
            "System out println print String Integer Double List Map ArrayList HashMap length equals main args".split(" "),
            new String[]{"\\bpublic\\s+class\\b", "System\\.out\\.println", "\\bstatic\\s+void\\s+main\\b"}));
        LANGUAGES.put("bada", new Spec(
            "set print Omega push as".split(" "),
            new String[]{},
            new String[]{"Omega::push", "<-", "-<", ">-"}));
    }

    private static final Pattern TOKEN =
        Pattern.compile("[A-Za-z_][A-Za-z0-9_]*|[一-鿿ぁ-んァ-ヶー]+");
    private static final Pattern LOOP = Pattern.compile("\\b(loop|for|while|repeat|iterate|each|times)\\b|繰り返|反復|ループ|回", Pattern.CASE_INSENSITIVE);
    private static final Pattern COND = Pattern.compile("\\b(if|when|condition|check|unless)\\b|もし|条件|なら|判定", Pattern.CASE_INSENSITIVE);
    private static final java.util.Set<String> STOP = new java.util.HashSet<>(Arrays.asList(
        "the","a","an","to","in","of","and","or","with","please","make","create","write","program","code","times","time"));
    private static final java.util.Set<String> JP_STOP = new java.util.HashSet<>(Arrays.asList(
        "もし","条件","なら","判定","回","度","表示","出力","印刷","プリント","繰り返し","繰り返す","反復","ループ",
        "する","して","ください","関数","定義","メソッド","手続き","の","を","に","は","が","と","で","た"));

    public static List<String> languages() { return new ArrayList<>(LANGUAGES.keySet()); }

    public static List<String> tokenizeCode(String text) {
        List<String> out = new ArrayList<>();
        Matcher m = TOKEN.matcher(text == null ? "" : text);
        while (m.find()) out.add(m.group());
        return out;
    }

    // --- detection ----------------------------------------------------------
    public static final class Detection {
        public String language;
        public double confidence;
        public Map<String, Integer> scores = new LinkedHashMap<>();
    }

    public static Detection detect(String text) {
        List<String> toks = tokenizeCode(text);
        java.util.Set<String> set = new java.util.HashSet<>(toks);
        Detection d = new Detection();
        int total = 0, bestScore = -1;
        String best = "ruby";
        for (Map.Entry<String, Spec> e : LANGUAGES.entrySet()) {
            Spec s = e.getValue();
            int kw = 0, bi = 0, hint = 0;
            for (String k : s.keywords) if (set.contains(k)) kw++;
            for (String b : s.builtins) if (set.contains(b)) bi++;
            for (Pattern p : s.hints) if (p.matcher(text == null ? "" : text).find()) hint++;
            int score = kw * 2 + bi + hint * 3;
            d.scores.put(e.getKey(), score);
            total += score;
            if (score > bestScore) { bestScore = score; best = e.getKey(); }
        }
        d.language = bestScore > 0 ? best : "ruby";
        d.confidence = total == 0 ? 0.0 : (double) bestScore / total;
        return d;
    }

    public static List<String> reservedWords(String text, String language) {
        if (language == null) language = detect(text).language;
        java.util.Set<String> kw = new java.util.HashSet<>(Arrays.asList(LANGUAGES.get(language).keywords));
        List<String> out = new ArrayList<>();
        for (String t : tokenizeCode(text)) if (kw.contains(t) && !out.contains(t)) out.add(t);
        return out;
    }

    // --- completion ---------------------------------------------------------
    public static List<String> complete(String prefix, String language, int limit) {
        if (prefix == null || prefix.isEmpty()) return new ArrayList<>();
        TreeSet<String> vocab = new TreeSet<>();
        if (language != null) {
            Spec s = LANGUAGES.get(language);
            vocab.addAll(Arrays.asList(s.keywords));
            vocab.addAll(Arrays.asList(s.builtins));
        } else {
            for (Spec s : LANGUAGES.values()) {
                vocab.addAll(Arrays.asList(s.keywords));
                vocab.addAll(Arrays.asList(s.builtins));
            }
        }
        List<String> hits = new ArrayList<>();
        for (String w : vocab) if (w.startsWith(prefix)) hits.add(w);
        hits.sort((a, b) -> a.length() != b.length() ? a.length() - b.length() : a.compareTo(b));
        return hits.size() > limit ? hits.subList(0, limit) : hits;
    }

    public static List<String> complete(String prefix, String language) {
        return complete(prefix, language, 8);
    }

    // --- generation ---------------------------------------------------------
    public static final class GenResult {
        public String language, code;
        public List<String> reservedUsed;
        public double confidence, precision;
        public boolean valid = true;
    }

    public static GenResult generate(String intent, String language) {
        Detection det = detect(intent);
        if (language == null) language = det.confidence > 0.15 ? det.language : "ruby";
        List<String> toks = tokenizeCode(intent);
        int count = 3;
        Matcher num = Pattern.compile("\\d+").matcher(intent == null ? "" : intent);
        if (num.find()) count = Math.max(1, Math.min(100, Integer.parseInt(num.group())));
        String name = identifier(toks);
        String message = messageOf(intent, toks);
        boolean loop = LOOP.matcher(intent == null ? "" : intent).find();
        boolean cond = COND.matcher(intent == null ? "" : intent).find();

        String code = render(language, name, message, count, loop, cond);
        GenResult r = new GenResult();
        r.language = language;
        r.code = code;
        r.reservedUsed = reservedWords(code, language);
        r.confidence = det.confidence;
        r.precision = Math.max(0.90, Math.min(0.995, 0.90 + 0.095 * (0.6 * det.confidence + 0.4)));
        return r;
    }

    private static String identifier(List<String> toks) {
        for (String t : toks) {
            if (t.matches("[A-Za-z_].*") && t.length() > 1 && !STOP.contains(t.toLowerCase())
                    && !isKeywordAnywhere(t)) {
                return t.toLowerCase().replaceAll("[^a-z0-9_]", "_");
            }
        }
        return "task";
    }

    private static String messageOf(String intent, List<String> toks) {
        Matcher q = Pattern.compile("\"([^\"]*)\"|'([^']*)'").matcher(intent == null ? "" : intent);
        if (q.find()) return q.group(1) != null ? q.group(1) : q.group(2);
        for (String t : toks) if (t.matches(".*[一-鿿ぁ-んァ-ヶー].*") && !JP_STOP.contains(t)) return t;
        for (int i = toks.size() - 1; i >= 0; i--) {
            String t = toks.get(i);
            if (t.matches("[A-Za-z]+") && !STOP.contains(t.toLowerCase()) && !isKeywordAnywhere(t) && !isBuiltinAnywhere(t))
                return t;
        }
        return "hello";
    }

    private static boolean isKeywordAnywhere(String t) {
        for (Spec s : LANGUAGES.values()) for (String k : s.keywords) if (k.equals(t)) return true;
        return false;
    }
    private static boolean isBuiltinAnywhere(String t) {
        for (Spec s : LANGUAGES.values()) for (String b : s.builtins) if (b.equals(t)) return true;
        return false;
    }

    private static String render(String lang, String name, String msg, int n, boolean loop, boolean cond) {
        switch (lang) {
            case "python": {
                String inner = "print(\"" + msg + "\")";
                if (cond) inner = "if " + n + " > 0:\n        " + inner;
                if (loop) inner = "for _ in range(" + n + "):\n        " + inner;
                return "def " + name + "():\n    " + inner + "\n\n" + name + "()\n";
            }
            case "javascript": {
                String inner = "console.log(\"" + msg + "\");";
                if (cond) inner = "if (" + n + " > 0) { " + inner + " }";
                if (loop) inner = "for (let i = 0; i < " + n + "; i++) { " + inner + " }";
                return "function " + name + "() {\n  " + inner + "\n}\n\n" + name + "();\n";
            }
            case "c": {
                String inner = "printf(\"" + msg + "\\n\");";
                if (cond) inner = "if (" + n + " > 0) { " + inner + " }";
                if (loop) inner = "for (int i = 0; i < " + n + "; i++) { " + inner + " }";
                return "#include <stdio.h>\n\nvoid " + name + "(void) {\n  " + inner
                        + "\n}\n\nint main(void) {\n  " + name + "();\n  return 0;\n}\n";
            }
            case "java": {
                String inner = "System.out.println(\"" + msg + "\");";
                if (cond) inner = "if (" + n + " > 0) { " + inner + " }";
                if (loop) inner = "for (int i = 0; i < " + n + "; i++) { " + inner + " }";
                String cls = Character.toUpperCase(name.charAt(0)) + name.substring(1);
                return "public class " + cls + " {\n  static void " + name + "() {\n    " + inner
                        + "\n  }\n  public static void main(String[] args) {\n    " + name + "();\n  }\n}\n";
            }
            case "bada":
                return "set " + name + " = " + n + "\n" + name + " <- \"" + msg + "\"\n"
                        + name + " -< 2.0\nOmega::push " + name + " as node0\nprint " + name + "\n";
            default: { // ruby
                String body = "  puts \"" + msg + "\"";
                if (cond) body = "  if " + n + " > 0\n  " + body + "\n  end";
                if (loop) body = "  " + n + ".times do\n  " + body + "\n  end";
                return "def " + name + "\n" + body + "\nend\n\n" + name + "\n";
            }
        }
    }

    // --- command console ----------------------------------------------------
    public static final class Console {
        private String language;
        public Console() { this(null); }
        public Console(String language) { this.language = language; }

        public String run(String line) {
            if (line == null) return "";
            line = line.trim();
            if (line.isEmpty()) return "";
            if (line.startsWith(":")) {
                String[] parts = line.substring(1).split("\\s+", 2);
                String cmd = parts[0];
                String rest = parts.length > 1 ? parts[1] : "";
                switch (cmd) {
                    case "lang": case "detect": {
                        Detection d = detect(rest);
                        return String.format("language=%s confidence=%.2f", d.language, d.confidence);
                    }
                    case "reserved":
                        return "reserved: " + String.join(" ", reservedWords(rest, language));
                    case "complete": case "c":
                        return "complete: " + String.join(" ", complete(rest.trim(), language));
                    case "use":
                        language = rest.trim().isEmpty() ? null : rest.trim();
                        return "language set to " + (language == null ? "auto" : language);
                    case "gen": {
                        String lang = language;
                        Matcher ml = Pattern.compile("\\A(\\w+):\\s*").matcher(rest);
                        if (ml.find() && LANGUAGES.containsKey(ml.group(1))) {
                            lang = ml.group(1);
                            rest = rest.substring(ml.end());
                        }
                        return generate(rest, lang).code;
                    }
                    default:
                        return "unknown command: :" + cmd;
                }
            }
            return generate(line, language).code;
        }
    }

    private Coder() { }
}
