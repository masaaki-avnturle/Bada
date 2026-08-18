package bada.mind;

import bada.qc.PseudoQC;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Bada::Mind (Java port) — a SIMULATION of thought verbalization. It does NOT
 * read a real brain; from an input signal + a quantum-sampled seed it synthesises
 * a plausible verbalization, a mental image and the "app in the mind" (Bada
 * source), which a tiny embedded evaluator actually runs.
 */
public final class MindReader {
    public static final double SILENT_TALK_BASELINE = 0.92;
    private static final String[] LEXICON = {
        "光", "音", "記憶", "感情", "数", "意志", "空間", "時間", "恐れ", "望み",
        "コード", "画像", "波", "場", "夢", "声", "色", "形", "熱", "静寂",
        "流れ", "意味", "予感", "律動", "中心"
    };
    // Built-in Japanese "inner-experience" prior — a generative prior, not data
    // about any real person. Lets the verbalizer connect salient thought-tokens
    // into readable thought instead of a bare token list.
    private static final String[] MIND_CORPUS = {
        "光が記憶の奥で静かに揺れている",
        "音は波となって感情の底へ流れていく",
        "望みと恐れが心の中で交錯する",
        "意志は時間の流れに沿って形を変える",
        "夢の中で声が色を帯びて響く",
        "静寂の中に予感が生まれ律動が始まる",
        "空間の中心へ意味が静かに集まっていく",
        "記憶と感情が波のように寄せては返す",
        "コードが画像となって思考の場に浮かぶ",
        "熱をもった数が意志の律動を刻んでいく"
    };
    private static final java.util.Set<String> PARTICLES = new java.util.HashSet<>(java.util.Arrays.asList(
        "が", "の", "と", "に", "を", "は", "へ", "も", "で", "や", "ね", "よ", "か", "た", "て", "る"));
    private static final Pattern TOKEN =
        Pattern.compile("[A-Za-z0-9_]+|[\\p{IsHan}\\p{IsHiragana}\\p{IsKatakana}]");
    private static final Pattern CJK = Pattern.compile("[\\p{IsHan}\\p{IsHiragana}\\p{IsKatakana}]");

    private final int dModel, nHeads, nBlocks;
    private final boolean useCorpus;
    private Map<String, Map<String, Integer>> bigram = new HashMap<>();
    private Map<String, Integer> unigram = new HashMap<>();

    public MindReader() { this(24, 4, 2, true); }
    public MindReader(boolean useCorpus) { this(24, 4, 2, useCorpus); }
    public MindReader(int dModel, int nHeads, int nBlocks, boolean useCorpus) {
        this.dModel = dModel; this.nHeads = nHeads; this.nBlocks = nBlocks; this.useCorpus = useCorpus;
    }

    public static final class Result {
        public String subject, signal, verbalization, source;
        public long quantumSeed;
        public int[] quantumBits;
        public List<String> salient, sourceOutput;
        public double[][] mentalImage;
        public double precision;
        public boolean exceedsSilentTalk;
    }

    /** Vocabulary for text-mode completion: the lexicon plus words drawn from the prior. */
    public static List<String> vocab() {
        java.util.LinkedHashSet<String> out = new java.util.LinkedHashSet<>(java.util.Arrays.asList(LEXICON));
        Pattern word = Pattern.compile("[\\p{IsHan}\\p{IsHiragana}\\p{IsKatakana}ー]+");
        for (String s : MIND_CORPUS) {
            java.util.regex.Matcher m = word.matcher(s);
            while (m.find()) out.add(m.group());
        }
        return new ArrayList<>(out);
    }

    public Result read(String signal, String subject) {
        signal = signal == null ? "" : signal;
        if (signal.trim().isEmpty()) signal = "静寂 の 中 の 光";

        buildLanguageModel(signal);
        List<String> tokens = tokenize(signal);
        if (tokens.size() > 48) tokens = tokens.subList(0, 48);
        if (tokens.isEmpty()) { tokens = new ArrayList<>(); tokens.add("空"); tokens.add("白"); }

        List<String> vocab = new ArrayList<>();
        Map<String, Integer> index = new LinkedHashMap<>();
        for (String t : tokens) if (!index.containsKey(t)) { index.put(t, vocab.size()); vocab.add(t); }
        for (String t : LEXICON) if (!index.containsKey(t)) { index.put(t, vocab.size()); vocab.add(t); }

        int[] ids = new int[tokens.size()];
        for (int i = 0; i < tokens.size(); i++) ids[i] = index.get(tokens.get(i));

        long qseed = quantumSeed(signal);
        int[] qbits = lastQbits;

        Encoder enc = new Encoder(vocab.size(), dModel, nHeads, nBlocks, 48, qseed);
        double[][] hidden = enc.forward(ids);

        String verbal = verbalize(enc, hidden, vocab, tokens);
        List<String> salient = salientTokens(enc.lastAttention(), tokens, 4);
        double[][] image = new Vision(enc, 8, 2, qseed).process(baseImage(signal));
        String[] code = generateCode(salient, qseed);
        List<String> codeOut = runBada(code[0]);
        double prec = precision(enc, ids, hidden, tokens, verbal);

        Result r = new Result();
        r.subject = subject;
        r.signal = signal;
        r.quantumSeed = qseed;
        r.quantumBits = qbits;
        r.verbalization = verbal;
        r.salient = salient;
        r.mentalImage = image;
        r.source = code[0];
        r.sourceOutput = codeOut;
        r.precision = prec;
        r.exceedsSilentTalk = prec > SILENT_TALK_BASELINE;
        return r;
    }

    public String render(String signal, String subject) {
        Result r = read(signal, subject);
        String bar = "============================================================";
        StringBuilder sb = new StringBuilder();
        sb.append(bar).append("\n");
        sb.append(" Bada::Mind — 思考の言語化・心像・脳内アプリ (simulation)\n");
        sb.append(bar).append("\n\n");
        sb.append("  ※ これは生成シミュレーションです。実在の人物の脳から思考を取り出す\n");
        sb.append("     ものではなく、入力信号と量子シードから合成します。\n\n");
        sb.append("① 量子ブレイン状態サンプリング (Bada::QC で H+測定)\n");
        sb.append(String.format("    measured qubits = %s   -> seed = %d%n%n",
                java.util.Arrays.toString(r.quantumBits), r.quantumSeed));
        sb.append("② 思考の言語化 (manifold-gauge transformer)\n");
        sb.append(String.format("    subject : %s%n", r.subject));
        sb.append(String.format("    signal  : %s%n", r.signal));
        sb.append(String.format("    思考    : 「%s」%n", r.verbalization));
        sb.append(String.format("    salient : %s%n%n", String.join(" / ", r.salient)));
        sb.append("③ 脳内に浮かぶ心像 (image-processing transformer / ViT)\n");
        for (String line : Vision.ascii(r.mentalImage).split("\n")) sb.append("    ").append(line).append("\n");
        sb.append("\n④ 脳の思考回路に浮かぶアプリのソースコード (Bada language)\n");
        for (String line : r.source.split("\n")) sb.append("    ").append(line).append("\n");
        sb.append("    --- 実行結果 (Bada mini-interpreter) ---\n");
        for (String line : r.sourceOutput) sb.append("    ").append(line).append("\n");
        sb.append("\n⑤ 精度 (simulated)\n");
        sb.append(String.format("    precision = %.1f%%   silent-talk baseline = %.1f%%   -> %s%n",
                r.precision * 100, SILENT_TALK_BASELINE * 100,
                r.exceedsSilentTalk ? "EXCEEDS silent talk" : "below"));
        sb.append(bar);
        return sb.toString();
    }

    // ------------------------------------------------------------------ pieces

    private int[] lastQbits;

    private long quantumSeed(String signal) {
        int n = 4;
        StringBuilder prog = new StringBuilder();
        for (int q = 0; q < n; q++) prog.append("H ").append(q).append("\n");
        for (int q = 0; q < n; q++) prog.append("MEASURE ").append(q).append("\n");
        prog.append("HALT\n");
        long sigSeed = 0x9E3779B9L;
        for (byte b : signal.getBytes(java.nio.charset.StandardCharsets.UTF_8))
            sigSeed = ((sigSeed * 131) ^ (b & 0xFF)) & 0xFFFFFFFFL;
        int[] bits = new int[n];
        try (PseudoQC m = new PseudoQC(n, sigSeed).load(prog.toString()).run()) {
            Map<Integer, Integer> cls = m.classicalBits();
            for (int q = 0; q < n; q++) bits[q] = cls.getOrDefault(q, 0);
        }
        lastQbits = bits;
        long qint = 0;
        for (int i = 0; i < n; i++) qint |= ((long) bits[i]) << i;
        return ((qint << 32) ^ sigSeed) & 0x7FFFFFFFFFFFFFFFL;
    }

    private void buildLanguageModel(String signal) {
        bigram = new HashMap<>();
        unigram = new HashMap<>();
        if (!useCorpus) return;
        List<String> texts = new ArrayList<>(java.util.Arrays.asList(MIND_CORPUS));
        texts.add(signal);
        for (String text : texts) {
            List<String> toks = new ArrayList<>();
            for (String t : tokenize(text)) if (isCjk(t)) toks.add(t);
            for (int i = 0; i < toks.size(); i++) {
                unigram.merge(toks.get(i), 1, Integer::sum);
                if (i + 1 < toks.size())
                    bigram.computeIfAbsent(toks.get(i), x -> new HashMap<>())
                          .merge(toks.get(i + 1), 1, Integer::sum);
            }
        }
    }

    private String verbalize(Encoder enc, double[][] hidden, List<String> vocab, List<String> tokens) {
        if (!unigram.isEmpty()) return corpusVerbalize(enc, hidden, vocab, tokens);
        return baseVerbalize(enc, hidden, vocab);
    }

    /** Raw transformer decode (weight-tying argmax) — used without a corpus. */
    private String baseVerbalize(Encoder enc, double[][] hidden, List<String> vocab) {
        double[][] lg = enc.logits(hidden);
        Map<Integer, Integer> used = new HashMap<>();
        StringBuilder sb = new StringBuilder();
        for (double[] row : lg) {
            int best = 0;
            double bestScore = Double.NEGATIVE_INFINITY;
            for (int v = 0; v < row.length; v++) {
                double s = row[v] - used.getOrDefault(v, 0) * 2.5;
                if (s > bestScore) { bestScore = s; best = v; }
            }
            used.merge(best, 1, Integer::sum);
            sb.append(vocab.get(best));
        }
        return sb.toString();
    }

    /** Corpus-guided decode: transformer salience + character-bigram fluency. */
    private String corpusVerbalize(Encoder enc, double[][] hidden, List<String> vocab, List<String> tokens) {
        double[] hmean = meanRows(hidden);
        List<String> salient = salientTokens(enc.lastAttention(), tokens, tokens.size());
        String cur = null;
        for (String t : salient) if (isCjk(t) && !PARTICLES.contains(t)) { cur = t; break; }
        if (cur == null) for (String t : salient) if (isCjk(t)) { cur = t; break; }
        if (cur == null) cur = salient.isEmpty() ? tokens.get(0) : salient.get(0);

        StringBuilder out = new StringBuilder(cur);
        Map<String, Integer> used = new HashMap<>();
        used.put(cur, 1);
        int target = Math.min(Math.max(tokens.size(), 6), 18);
        for (int step = 0; step < target - 1; step++) {
            Map<String, Integer> cands = bigram.getOrDefault(cur, null);
            if (cands == null || cands.isEmpty()) cands = topUnigram(40);
            String best = null;
            double bestScore = Double.NEGATIVE_INFINITY;
            for (String tok : cands.keySet()) {
                if (tok == null) continue;
                int bc = bigram.getOrDefault(cur, java.util.Collections.emptyMap()).getOrDefault(tok, 0);
                double score = Math.log(bc + 1.0) + affinity(tok, hmean, vocab, enc)
                        + wordBonus(tok) - used.getOrDefault(tok, 0) * 1.5;
                if (score > bestScore) { bestScore = score; best = tok; }
            }
            if (best == null) break;
            out.append(best);
            used.merge(best, 1, Integer::sum);
            cur = best;
        }
        return out.toString();
    }

    private double affinity(String tok, double[] hmean, List<String> vocab, Encoder enc) {
        int idx = vocab.indexOf(tok);
        if (idx < 0) return 0.0;
        return Tensor.cosine(enc.embedding()[idx], hmean) * 1.2;
    }

    private double wordBonus(String tok) {
        if (tok.matches("[A-Za-z0-9_]+")) return -2.0;
        double b = isCjk(tok) ? 0.8 : 0.0;
        if (java.util.Arrays.asList(LEXICON).contains(tok)) b += 0.6;
        return b;
    }

    private Map<String, Integer> topUnigram(int n) {
        return unigram.entrySet().stream()
                .sorted((a, b) -> b.getValue() - a.getValue())
                .limit(n)
                .collect(java.util.LinkedHashMap::new, (m, e) -> m.put(e.getKey(), e.getValue()), Map::putAll);
    }

    private static boolean isCjk(String tok) {
        return CJK.matcher(tok).find();
    }

    private List<String> salientTokens(double[][] attn, List<String> tokens, int top) {
        List<String> picked = new ArrayList<>();
        int n = tokens.size();
        if (attn == null) {
            for (String t : tokens) if (!picked.contains(t)) { picked.add(t); if (picked.size() >= top) break; }
            return picked;
        }
        double[] sal = new double[n];
        for (int j = 0; j < n; j++) for (int i = 0; i < n; i++) sal[j] += attn[i][j];
        Integer[] order = new Integer[n];
        for (int j = 0; j < n; j++) order[j] = j;
        java.util.Arrays.sort(order, (x, y) -> Double.compare(sal[y], sal[x]));
        for (int j : order) {
            String t = tokens.get(j);
            if (!picked.contains(t)) picked.add(t);
            if (picked.size() >= top) break;
        }
        return picked;
    }

    private double[][] baseImage(String signal) {
        byte[] bytes = signal.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        int len = Math.max(bytes.length, 1);
        double[][] g = new double[8][8];
        for (int y = 0; y < 8; y++)
            for (int x = 0; x < 8; x++)
                g[y][x] = (bytes[(y * 8 + x) % len] & 0xFF) / 255.0;
        return g;
    }

    private String[] generateCode(List<String> salient, long qseed) {
        Tensor.PRNG rng = new Tensor.PRNG(qseed);
        StringBuilder sb = new StringBuilder();
        sb.append("# app floating in the mind — auto-generated Bada program\n");
        for (int i = 0; i < salient.size(); i++) {
            double val = Math.round((rng.nextFloat() * 5.0 + 0.5) * 1000.0) / 1000.0;
            sb.append("set mind").append(i).append(" = ").append(val).append("\n");
            sb.append("mind").append(i).append(" <- \"").append(salient.get(i)).append("\"\n");
            sb.append("mind").append(i).append(" -< 2.0\n");
            sb.append("mind").append(i).append(" >- mind").append(i).append("\n");
            sb.append("Omega::push mind").append(i).append(" as thought").append(i).append("\n");
            sb.append("print mind").append(i).append("\n");
        }
        return new String[]{sb.toString()};
    }

    /** A tiny embedded evaluator for the generated Bada program (set/<-/-</>-/push/print). */
    private List<String> runBada(String source) {
        Map<String, Double> env = new HashMap<>();
        List<String> out = new ArrayList<>();
        int pushCount = 0;
        for (String raw : source.split("\n")) {
            String line = raw.replaceAll("#.*$", "").trim();
            if (line.isEmpty()) continue;
            Matcher mSet = Pattern.compile("^set\\s+(\\w+)\\s*=\\s*([-+0-9.]+)$").matcher(line);
            Matcher mLeft = Pattern.compile("^(\\w+)\\s*<-\\s*\"(.*)\"$").matcher(line);
            Matcher mInt = Pattern.compile("^(\\w+)\\s*-<\\s*([-+0-9.]+)$").matcher(line);
            Matcher mRight = Pattern.compile("^(\\w+)\\s*>-\\s*(\\w+)$").matcher(line);
            Matcher mPush = Pattern.compile("^Omega::push\\s+(\\w+)(?:\\s+as\\s+(\\w+))?$").matcher(line);
            Matcher mPrint = Pattern.compile("^print\\s+(\\w+)$").matcher(line);
            if (mSet.matches()) {
                env.put(mSet.group(1), Double.parseDouble(mSet.group(2)));
            } else if (mLeft.matches()) {
                double xi = tokenXi(mLeft.group(2));
                double x = Math.abs(env.getOrDefault(mLeft.group(1), 0.0)) + 1.0;
                env.put(mLeft.group(1), Math.abs(Math.PI * xi * Math.log(x)));
            } else if (mInt.matches()) {
                double v = env.getOrDefault(mInt.group(1), 0.0);
                double x = Math.abs(v) + 2.0;
                env.put(mInt.group(1), xLogX(x) * element(x) + element(x));
            } else if (mRight.matches()) {
                double v = env.getOrDefault(mRight.group(1), 0.0);
                double x = Math.abs(v) + 1e-6;
                env.put(mRight.group(1), Math.exp(-xLogX(x)));
            } else if (mPush.matches()) {
                String key = mPush.group(2) != null ? mPush.group(2) : ("Ω::" + pushCount);
                double v = env.getOrDefault(mPush.group(1), 0.0);
                out.add(String.format("Ω::push %s (Xi=%.4f)", key, v));
                pushCount++;
            } else if (mPrint.matches()) {
                out.add(String.valueOf(env.getOrDefault(mPrint.group(1), 0.0)));
            }
        }
        return out;
    }

    private static double tokenXi(String tok) {
        double h = 0;
        for (int i = 0; i < tok.length(); i++) h = (h * 31 + tok.charAt(i)) % 1000;
        return 0.2 + (h / 1000.0) * 0.8;
    }

    private static double xLogX(double x) { return x <= 0 ? 0.0 : x * Math.log(x); }
    private static double element(double x) {
        if (x <= 1.0) return 1.0;
        double xl = xLogX(x);
        return Math.abs(xl) < 1e-9 ? 1.0 : 1.0 / (xl * xl);
    }

    private double precision(Encoder enc, int[] ids, double[][] hidden, List<String> tokens, String verbal) {
        double[] meanIn = meanRows(enc.embed(ids));
        double[] meanOut = meanRows(hidden);
        double align = (Tensor.cosine(meanIn, meanOut) + 1.0) / 2.0;
        double hIn = shannon(tokens);
        double hOut = shannon(tokenize(verbal));
        double match = 1.0 - (Math.abs(hIn - hOut) / (hIn + 1.0));
        double p = 0.90 + 0.095 * (0.5 * align + 0.5 * match);
        return Math.max(0.90, Math.min(0.995, p));
    }

    private static double[] meanRows(double[][] mat) {
        int d = mat[0].length;
        double[] acc = new double[d];
        for (double[] row : mat) for (int j = 0; j < d; j++) acc[j] += row[j];
        for (int j = 0; j < d; j++) acc[j] /= mat.length;
        return acc;
    }

    private static List<String> tokenize(String text) {
        List<String> out = new ArrayList<>();
        Matcher m = TOKEN.matcher(text);
        while (m.find()) out.add(m.group());
        return out;
    }

    private static double shannon(List<String> tokens) {
        if (tokens.isEmpty()) return 0.0;
        Map<String, Integer> f = new HashMap<>();
        for (String t : tokens) f.merge(t, 1, Integer::sum);
        double total = tokens.size();
        double h = 0.0;
        for (int c : f.values()) {
            double p = c / total;
            h -= p * (Math.log(p) / Math.log(2));
        }
        return h;
    }
}
