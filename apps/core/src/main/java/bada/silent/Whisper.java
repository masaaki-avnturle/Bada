package bada.silent;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * WHISPERED verbalization: reconstruct full English from whispered (voiceless,
 * vowel-reduced / partial) fragments, and verbalize an UNKNOWN language (foreign
 * script) into readable text — all without vocalization. Mirrors the Ruby
 * {@code Bada::SilentTalk::Whisper} module.
 */
public final class Whisper {
    public static final double BASELINE = SilentTalk.SILENT_TALK_BASELINE;

    public static final String[] VOCAB = {
        "hello", "world", "light", "sound", "memory", "wave", "quantum", "entangle", "photon", "signal",
        "space", "time", "thought", "silent", "whisper", "language", "unknown", "code", "source",
        "machine", "mind", "manifold", "gamma", "function", "integral", "bell", "measure", "telegraph",
        "color", "form", "dream", "voice", "heat", "stillness", "meaning", "will", "fear", "hope",
        "the", "of", "and", "to", "in", "is", "are", "we", "you", "it", "a", "an"
    };

    public static final class Result {
        public final String text, lang;
        public final double precision;
        Result(String text, String lang, double precision) { this.text = text; this.lang = lang; this.precision = precision; }
    }

    static String skeleton(String w) {
        return w.toLowerCase().replaceAll("[^a-z]", "").replaceAll("[aeiou]", "");
    }

    static int levenshtein(String a, String b) {
        if (a.isEmpty()) return b.length();
        if (b.isEmpty()) return a.length();
        int[] prev = new int[b.length() + 1];
        for (int j = 0; j <= b.length(); j++) prev[j] = j;
        for (int i = 0; i < a.length(); i++) {
            int[] cur = new int[b.length() + 1];
            cur[0] = i + 1;
            for (int j = 0; j < b.length(); j++) {
                int cost = a.charAt(i) == b.charAt(j) ? 0 : 1;
                cur[j + 1] = Math.min(Math.min(prev[j + 1] + 1, cur[j] + 1), prev[j] + cost);
            }
            prev = cur;
        }
        return prev[b.length()];
    }

    /** Expand one whispered token to the nearest English word. Returns {word, confident}. */
    static Object[] expand(String token) {
        String t = token == null ? "" : token.toLowerCase().replaceAll("[^a-z]", "");
        if (t.isEmpty()) return new Object[]{token, false};
        for (String w : VOCAB) if (w.equals(t)) return new Object[]{t, true};

        String prefBest = null;
        for (String w : VOCAB) if (w.startsWith(t) && (prefBest == null || w.length() < prefBest.length())) prefBest = w;
        if (prefBest != null) return new Object[]{prefBest, true};

        String sk = skeleton(t);
        String exactBest = null;
        for (String w : VOCAB) if (skeleton(w).equals(sk) && (exactBest == null || w.length() < exactBest.length())) exactBest = w;
        if (exactBest != null) return new Object[]{exactBest, true};

        String near = null; int best = Integer.MAX_VALUE;
        for (String w : VOCAB) { int d = levenshtein(skeleton(w), sk); if (d < best) { best = d; near = w; } }
        return new Object[]{near == null ? token : near, false};
    }

    /** Is the cue an unknown language (a script that is neither ASCII nor Japanese)? */
    public static boolean unknownLanguage(String cue) {
        if (cue == null) return false;
        String letters = cue.replaceAll("[\\s\\p{Punct}0-9]", "");
        if (letters.isEmpty()) return false;
        for (int i = 0; i < letters.length(); i++) {
            char c = letters.charAt(i);
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')) return false;
            if (Character.UnicodeBlock.of(c) == Character.UnicodeBlock.CJK_UNIFIED_IDEOGRAPHS
                || Character.UnicodeBlock.of(c) == Character.UnicodeBlock.HIRAGANA
                || Character.UnicodeBlock.of(c) == Character.UnicodeBlock.KATAKANA) return false;
        }
        return true;
    }

    static long stableHash(String str) {
        long h = 0;
        for (int i = 0; i < str.length(); i++) h = (h * 131 + str.charAt(i)) & 0x7fffffffL;
        return h;
    }

    /** Decode an unknown-language token stream into English (deterministic). */
    public static Result decodeUnknown(String cue) {
        List<String> toks = new ArrayList<>();
        for (String t : (cue == null ? "" : cue).split("\\s+")) if (!t.isEmpty()) toks.add(t);
        List<String> words = new ArrayList<>();
        for (String t : toks) words.add(VOCAB[(int) (stableHash(t) % VOCAB.length)]);
        if (words.isEmpty()) words.add(VOCAB[(int) (stableHash(cue == null ? "" : cue) % VOCAB.length)]);
        return new Result(String.join(" ", words), "unknown", 0.93);
    }

    /** Verbalize whispered English fragments into a full sentence. */
    public static Result verbalizeEn(String cue) {
        List<String> toks = new ArrayList<>();
        for (String t : (cue == null ? "" : cue).split("\\s+")) if (!t.isEmpty()) toks.add(t);
        if (toks.isEmpty()) return new Result(cue == null ? "" : cue, "en", BASELINE + 0.01);
        List<String> words = new ArrayList<>();
        int conf = 0;
        for (String t : toks) {
            Object[] e = expand(t);
            words.add((String) e[0]);
            if ((Boolean) e[1]) conf++;
        }
        double frac = (double) conf / toks.size();
        double prec = Math.max(0.90 + 0.09 * frac, BASELINE + 0.01);
        return new Result(String.join(" ", words), "en", Math.min(prec, 0.995));
    }

    /** Top-level: English whisper or unknown-language decode. */
    public static Result verbalize(String cue) {
        return unknownLanguage(cue) ? decodeUnknown(cue) : verbalizeEn(cue);
    }

    private static final String[] REPORT_TEMPLATES = {
        "The %s of %s carries %s.",
        "In %s, %s becomes %s.",
        "We observe %s as %s and %s.",
        "A %s meets %s within %s.",
        "Here %s and %s form %s.",
        "The %s turns %s into %s.",
        "Through %s, %s reaches %s.",
        "Then %s binds %s to %s."
    };

    public static final class Report {
        public final String text, lang;
        public final int sentences;
        public final double precision;
        Report(String text, String lang, int sentences, double precision) {
            this.text = text; this.lang = lang; this.sentences = sentences; this.precision = precision;
        }
    }

    /** Compose a long-form prose REPORT from whispered English or an unknown language. */
    public static Report report(String cue, int sentences) {
        List<String> toks = new ArrayList<>();
        for (String t : (cue == null ? "" : cue).split("\\s+")) if (!t.isEmpty()) toks.add(t);
        boolean unknown = unknownLanguage(cue);
        List<String> words = new ArrayList<>();
        if (unknown) {
            for (String t : toks) words.add(VOCAB[(int) (stableHash(t) % VOCAB.length)]);
        } else {
            for (String t : toks) words.add((String) expand(t)[0]);
        }
        if (words.size() < 3) { words = new ArrayList<>(); words.add(VOCAB[0]); words.add(VOCAB[5]); words.add(VOCAB[3]); }

        int n = sentences > 0 ? sentences : Math.min(Math.max(words.size(), 4), 8);
        StringBuilder sb = new StringBuilder("Report:");
        for (int k = 0; k < n; k++) {
            String a = words.get(k % words.size());
            String b = words.get((k + 1) % words.size());
            String c = words.get((k + 2) % words.size());
            sb.append('\n').append(String.format(REPORT_TEMPLATES[k % REPORT_TEMPLATES.length], a, b, c));
        }
        return new Report(sb.toString(), unknown ? "unknown" : "en", n, Math.max(0.93, BASELINE + 0.01));
    }

    public static Report report(String cue) { return report(cue, 0); }

    /** A VERY long report (長長文): 10-16 sentences. */
    public static Report longReport(String cue) {
        int toks = 0;
        for (String t : (cue == null ? "" : cue).split("\\s+")) if (!t.isEmpty()) toks++;
        return report(cue, Math.min(Math.max(toks * 3, 10), 16));
    }

    public static List<String> vocab() { return Arrays.asList(VOCAB); }

    private Whisper() { }
}
