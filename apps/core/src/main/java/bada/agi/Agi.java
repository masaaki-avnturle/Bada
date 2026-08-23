package bada.agi;

import bada.quantum.Jones;
import bada.mind.MindReader;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * ChatΩ — an evolved conversational engine (chatGPT の進化版, a SIMULATION).
 * Java port of {@code Bada::AGI}.
 *
 * <p>Every turn runs an AGI SELF-EVOLUTION loop: candidate replies are sampled
 * from the gamma-function GLOBAL INTEGRATION-BY-PARTS MANIFOLD prior (the Mind
 * lexicon), each candidate is encoded as a closed (2, m) BRAID scored by the
 * JONES POLYNOMIAL (topological coherence with the prompt), and the population
 * is evolved (elitist selection + crossover + quantum-seeded mutation) across
 * generations. Elitism makes the best fitness monotonically non-decreasing — a
 * visible self-evolution curve — and the fittest reply is verbalized by the
 * Mind engine, floored above the silent-talk baseline. Generative SIMULATION,
 * NOT a real AGI.
 */
public final class Agi {
    public static final double BASELINE = 0.92;
    public static final int MAX_CROSS = 6;
    public static final int CAND_LEN = 10;

    /** English manifold prior — used when the prompt is English. */
    static final String[] EN_LEX = {
        "light", "sound", "memory", "emotion", "number", "will", "space", "time",
        "fear", "hope", "code", "image", "wave", "field", "dream", "voice",
        "color", "form", "heat", "stillness", "flow", "meaning", "premonition",
        "rhythm", "center", "quantum", "entangle", "photon", "signal", "thought",
        "silent", "manifold", "gamma"
    };

    public static final class Gen {
        public final int generation, writhe, crossings;
        public final double bestFitness, jones;
        Gen(int g, double f, double j, int w, int c) {
            generation = g; bestFitness = f; jones = j; writhe = w; crossings = c;
        }
    }

    public static final class Result {
        public String prompt, reply, braid;
        public double precision, jonesValue, jonesCorrelation;
        public int generations, population, jonesWrithe, jonesCrossings;
        public boolean exceedsSilentTalk;
        public List<String> genes;
        public List<Gen> trace;
    }

    private Agi() { }

    public static Result chat(String prompt, int generations, int population, int nonce) {
        return chat(prompt, generations, population, nonce, new MindReader());
    }

    public static Result chat(String prompt, int generations, int population, int nonce, MindReader mind) {
        String p = prompt == null ? "" : prompt;
        long s = seed(p, nonce);
        List<String> vocab = buildVocab(p);

        List<List<String>> pop = new ArrayList<>();
        for (int i = 0; i < population; i++) { s = step(s); pop.add(randomCandidate(vocab, s + i)); }

        List<Gen> trace = new ArrayList<>();
        List<String> best = null;
        double bestFit = 0.0;

        for (int g = 0; g < generations; g++) {
            final String pp = p;
            final List<String> vv = vocab;
            pop.sort((a, b) -> Double.compare(fitness(b, pp, vv), fitness(a, pp, vv)));
            best = pop.get(0);
            bestFit = fitness(best, p, vocab);
            int[][] cr = crossingsOf(best);
            trace.add(new Gen(g + 1, round4(bestFit), round4(Jones.jonesValue(cr, Math.E)),
                    Jones.writhe(cr), cr.length));

            int keepN = Math.max((int) Math.ceil(population / 2.0), 1);
            List<List<String>> keep = new ArrayList<>(pop.subList(0, keepN));
            List<List<String>> children = new ArrayList<>();
            while (keep.size() + children.size() < population) {
                s = step(s);
                List<String> a = keep.get((int) ((s >> 3) % keep.size()));
                s = step(s);
                List<String> b = keep.get((int) ((s >> 5) % keep.size()));
                s = step(s);
                children.add(mutate(crossover(a, b, s), vocab, s));
            }
            pop = new ArrayList<>(keep);
            pop.addAll(children);
        }

        int[][] cr = crossingsOf(best);
        Result r = new Result();
        r.prompt = p;
        r.reply = composeReply(p, best, mind);
        r.precision = coherence(bestFit);
        r.exceedsSilentTalk = r.precision > BASELINE;
        r.generations = generations;
        r.population = population;
        r.braid = braidWord(best);
        r.jonesValue = Jones.jonesValue(cr, Math.E);
        r.jonesWrithe = Jones.writhe(cr);
        r.jonesCorrelation = Jones.correlation(cr);
        r.jonesCrossings = cr.length;
        r.genes = best;
        r.trace = trace;
        return r;
    }

    /** Full human-readable transcript of the evolved turn. */
    public static String render(String prompt, int generations, int population, int nonce) {
        Result r = chat(prompt, generations, population, nonce);
        StringBuilder sb = new StringBuilder();
        sb.append("ChatΩ — AGI 自己進化チャット (chatGPT 進化版・simulation)\n");
        sb.append("prompt> ").append(r.prompt).append("\n\n");
        sb.append("── 自己進化の過程 (Jones 多項式フィットネス) ──\n");
        sb.append("  gen |  fitness |   Jones(t=e) | writhe | crossings\n");
        for (Gen t : r.trace) {
            sb.append(String.format("  %3d | %7.4f | %12.4f | %+6d | %d%n",
                    t.generation, t.bestFitness, t.jones, t.writhe, t.crossings));
        }
        sb.append("\nbraid (勝者の組みひも): ").append(r.braid).append("\n");
        sb.append(String.format("coherence precision = %.1f%%  (silent-talk %.1f%%)  -> %s%n",
                r.precision * 100, BASELINE * 100, r.exceedsSilentTalk ? "EXCEEDS" : "below"));
        sb.append("\nChatΩ> ").append(r.reply);
        return sb.toString();
    }

    // ---- gamma-manifold sampling --------------------------------------------

    static long seed(String prompt, int nonce) {
        long h = stableHash(prompt);
        return (h * 2654435761L + 40503L + (long) nonce * 2246822519L) & 0xffffffffL;
    }

    static long step(long s) { return (s * 1103515245L + 12345L) & 0x7fffffffL; }

    static long stableHash(String str) {
        long h = 0;
        String s = str == null ? "" : str;
        for (int i = 0; i < s.length(); i++) h = (h * 131 + s.charAt(i)) & 0x7fffffffL;
        return h;
    }

    static String[] prior(String prompt) {
        return english(prompt) ? EN_LEX : MindReader.lexicon().toArray(new String[0]);
    }

    static List<String> buildVocab(String prompt) {
        List<String> out = new ArrayList<>();
        for (String t : prompt.split("[\\s、。,.!?！？]+")) if (!t.isEmpty()) out.add(t);
        for (String t : prior(prompt)) if (!out.contains(t)) out.add(t);
        if (out.isEmpty()) out.addAll(Arrays.asList(prior(prompt)));
        return out;
    }

    static List<String> randomCandidate(List<String> vocab, long s) {
        List<String> out = new ArrayList<>();
        for (int i = 0; i < CAND_LEN; i++) { s = step(s); out.add(vocab.get((int) (s % vocab.size()))); }
        return out;
    }

    // ---- Jones-polynomial fitness -------------------------------------------

    static int[][] crossingsOf(List<String> cand) {
        long h = 0;
        for (String t : cand) h += stableHash(t);
        int m = 2 + (int) (h % (MAX_CROSS - 1));
        int[][] cr = new int[m][5];
        for (int i = 0; i < m; i++) {
            int prev = (i - 1 + m) % m;
            int sign = (stableHash(cand.get(i % cand.size())) % 2 != 0) ? +1 : -1;
            cr[i] = new int[]{2 * prev, 2 * prev + 1, 2 * i + 1, 2 * i, sign};
        }
        return cr;
    }

    static double fitness(List<String> cand, String prompt, List<String> vocab) {
        if (cand.isEmpty()) return 0.0;
        double jc = Jones.correlation(crossingsOf(cand));
        List<String> ptok = new ArrayList<>();
        for (String t : prompt.split("[\\s、。,.!?！？]+")) if (!t.isEmpty()) ptok.add(t);
        List<String> pri = Arrays.asList(prior(prompt));
        int hits = 0;
        for (String t : cand) if (ptok.contains(t) || pri.contains(t)) hits++;
        double rel = (double) hits / cand.size();
        long distinct = cand.stream().distinct().count();
        double div = (double) distinct / cand.size();
        return 0.5 * jc + 0.4 * rel + 0.1 * div;
    }

    static double coherence(double fit) {
        double lo = BASELINE + 0.01;
        return Math.max(Math.min(lo + (0.995 - lo) * fit, 0.995), lo);
    }

    // ---- evolution operators ------------------------------------------------

    static List<String> crossover(List<String> a, List<String> b, long s) {
        int cut = 1 + (int) (s % (CAND_LEN - 1));
        List<String> out = new ArrayList<>(a.subList(0, Math.min(cut, a.size())));
        out.addAll(b.subList(Math.min(cut, b.size()), b.size()));
        while (out.size() < CAND_LEN) out.add(b.get(out.size() % b.size()));
        return out.subList(0, CAND_LEN);
    }

    static List<String> mutate(List<String> cand, List<String> vocab, long s) {
        List<String> out = new ArrayList<>(cand);
        for (int k = 0; k < 2; k++) {
            s = step(s);
            int pos = (int) (s % out.size());
            s = step(s);
            out.set(pos, vocab.get((int) (s % vocab.size())));
        }
        return out;
    }

    // ---- reply synthesis ----------------------------------------------------

    static String braidWord(List<String> cand) {
        int[][] cr = crossingsOf(cand);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < cr.length; i++) {
            if (i > 0) sb.append(' ');
            sb.append(cr[i][4] > 0 ? "σ+" : "σ-");
        }
        return sb.toString();
    }

    static String composeReply(String prompt, List<String> cand, MindReader mind) {
        MindReader.Result r = mind.read(String.join(" ", cand), "対象");
        String thought = r.verbalization == null ? "" : r.verbalization.trim();
        if (thought.isEmpty()) thought = String.join(" ", cand);
        if (english(prompt)) {
            return "After self-evolution over the gamma-manifold, ChatΩ's most coherent "
                    + "response to your prompt is: " + thought + ".";
        }
        return "ガンマ多様体上での自己進化を経て、ChatΩ が最も整合した応答: " + thought + "。";
    }

    static boolean english(String str) {
        if (str == null || str.isEmpty()) return false;
        int latin = 0;
        for (int i = 0; i < str.length(); i++) {
            char c = str.charAt(i);
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')) latin++;
        }
        return (double) latin / Math.max(str.length(), 1) > 0.4;
    }

    static double round4(double v) { return Math.round(v * 10000.0) / 10000.0; }
}
