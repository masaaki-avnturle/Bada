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
    private static final Pattern ADD = Pattern.compile("\\b(add|sum|plus|total|accumulate|addition)\\b|足し算|合計|加算|足す|総和", Pattern.CASE_INSENSITIVE);
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
        public int statements;
        public boolean recipe;
        public boolean valid = true;
    }

    // Compile the described intent into an AST (Synth) and emit ORIGINAL code.
    public static GenResult generate(String intent, String language) {
        Detection det = detect(intent);
        if (language == null) language = det.confidence > 0.15 ? det.language : "ruby";

        // Compile the described steps. If trivial (a bare goal like "fibonacci"),
        // synthesise a whole program from a recipe instead.
        Synth.Program prog = Synth.compile(intent);
        boolean recipe = false;
        boolean meaningful = prog.items().size() >= 2
                || (prog.items().size() == 1 && !(prog.items().get(0) instanceof Synth.ExprStmt));
        if (!meaningful) {
            Synth.Program rp = Recipes.forGoal(intent);
            if (rp != null) { prog = rp; recipe = true; }
        }

        String code;
        if (prog.items().isEmpty()) {
            String msg = intent == null ? "" : intent.trim();
            if (msg.isEmpty()) msg = "hello";
            Synth.Program fb = new Synth.Program("Program",
                    List.of(new Synth.Print(new Synth.Str(msg.replace("\"", "'")))));
            code = Synth.emit(language, fb);
        } else {
            code = Synth.emit(language, prog);
        }

        GenResult r = new GenResult();
        r.language = language;
        r.code = code;
        r.reservedUsed = reservedWords(code, language);
        r.confidence = det.confidence;
        r.recipe = recipe;
        r.statements = prog.items().size();
        r.precision = Math.max(0.90, Math.min(0.995, 0.90 + 0.095 * (0.6 * det.confidence + 0.4)));
        return r;
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
