package bada.silent;

import bada.mind.MindReader;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * pLaTeX PAPER writer: generate a long-long-form 論文 (Japanese LaTeX / jsarticle)
 * source — title, abstract, many sections, equations — without any vocalization.
 * Mirrors {@code Bada::SilentTalk::Platex} (same PRNG / templates).
 */
public final class Platex {
    public static final String[] SECTION_TITLES = {
        "序論", "背景と定義", "多様体ゲージの構成", "主定理", "証明", "数値実験",
        "半導体実装", "考察", "関連研究", "結論", "今後の課題", "補遺"
    };

    public static final String[] EQUATIONS = {
        "\\iint \\frac{1}{(x \\log x)^2}\\,dx_m",
        "\\beta(p,q) = \\frac{\\Gamma(p)\\Gamma(q)}{\\Gamma(p+q)}",
        "S = 2\\sqrt{2} > 2",
        "E(a,b) = -\\cos(a-b)",
        "\\Xi = \\frac{\\beta(H+1,\\,M+1)}{\\log(N+1)}",
        "\\psi = e^{-x \\log x}"
    };

    private static final String[] BODY = {
        "本節では%sと%sの関係を%sの観点から論じる。",
        "%sは%sの大域的部分積分多様体上で%sとして特徴づけられる。",
        "数値実験により%sが%sへ収束し%sが保存されることを確認した。",
        "%sのゲージ変換の下で%sは不変であり%sを誘導する。",
        "以上より%sと%sの間に%sを介した対応が成り立つ。"
    };

    public static final String[] LATEX_WORDS = {
        "\\documentclass", "\\usepackage", "\\title", "\\author", "\\date", "\\maketitle",
        "\\begin", "\\end", "\\section", "\\subsection", "\\equation", "\\abstract", "\\today",
        "\\Gamma", "\\beta", "\\iint", "\\frac", "\\sqrt", "\\cos", "\\log", "\\psi"
    };

    private static final Pattern WORD = Pattern.compile("[A-Za-z]+|[\\p{IsHan}\\p{IsHiragana}\\p{IsKatakana}ー]+");
    private static final Pattern BEGIN = Pattern.compile("\\\\begin\\{");
    private static final Pattern END = Pattern.compile("\\\\end\\{");

    public static final class Paper {
        public final String code, title;
        public final int sections;
        public final boolean valid;
        public final double precision;
        Paper(String code, String title, int sections, boolean valid, double precision) {
            this.code = code; this.title = title; this.sections = sections; this.valid = valid; this.precision = precision;
        }
    }

    public static Paper paper(String cue, int sections, int nonce) {
        final long[] s = { ((long) nonce * 2654435761L + 40503L) & 0xffffffffL };
        java.util.function.LongSupplier nxt = () -> (s[0] = (s[0] * 1103515245L + 12345L) & 0x7fffffffL);

        List<String> words = new ArrayList<>();
        Matcher m = WORD.matcher(cue == null ? "" : cue);
        while (m.find()) words.add(m.group());
        if (words.size() < 3) {
            List<String> lex = MindReader.lexicon();
            words = new ArrayList<>();
            for (int i = 0; i < 3; i++) words.add(lex.get((int) (nxt.getAsLong() % lex.size())));
        }
        final List<String> ws = words;
        java.util.function.Supplier<String> pick = () -> ws.get((int) (nxt.getAsLong() % ws.size()));

        StringBuilder t = new StringBuilder();
        for (int i = 0; i < Math.min(3, ws.size()); i++) { if (i > 0) t.append('と'); t.append(ws.get(i)); }
        String title = t + "の大域的部分積分多様体による解析";
        int n = sections > 0 ? sections : Math.min(Math.max(ws.size() * 2, 6), 12);

        List<String> lines = new ArrayList<>();
        lines.add("\\documentclass[a4paper,11pt]{jsarticle}");
        lines.add("\\usepackage{amsmath,amssymb}");
        lines.add("\\title{" + title + "}");
        lines.add("\\author{Bada 研究会\\\\Global Differential Manifold Research}");
        lines.add("\\date{\\today}");
        lines.add("\\begin{document}");
        lines.add("\\maketitle");
        lines.add("\\begin{abstract}");
        lines.add(String.format("本論文では、ガンマ関数の大域的部分積分多様体を用いて%sと%sの構造を解析し、%sとの関係を示す。",
                pick.get(), pick.get(), pick.get()));
        lines.add("\\end{abstract}");
        for (int i = 0; i < n; i++) {
            lines.add("\\section{" + SECTION_TITLES[i % SECTION_TITLES.length] + "}");
            for (int j = 0; j < 2; j++) {
                lines.add(String.format(BODY[(int) (nxt.getAsLong() % BODY.length)], pick.get(), pick.get(), pick.get()));
            }
            if (i % 2 == 0) {
                lines.add("\\begin{equation}");
                lines.add("  " + EQUATIONS[(int) (nxt.getAsLong() % EQUATIONS.length)]);
                lines.add("\\end{equation}");
            }
        }
        lines.add("\\end{document}");
        String code = String.join("\n", lines);
        return new Paper(code, title, n, valid(code), Math.max(0.95, SilentTalk.SILENT_TALK_BASELINE + 0.01));
    }

    public static Paper paper(String cue, int nonce) { return paper(cue, 0, nonce); }

    private static final String[] DEFINITIONS = {
        "%sを、%sの大域的部分積分多様体上の%sとして定義する。",
        "%sとは、%sのゲージ変換で%sを保つ対象のことである。"
    };
    private static final String[] THEOREMS = {
        "%sにおいて%sは%sに一意に収束する。",
        "任意の%sに対し、%sは%sの不変量を与える。"
    };
    private static final String[] PROOFS = {
        "%sの定義と多様体積分の性質より、%sが%sを満たすことがわかる。よって主張が従う。",
        "%sを%sで評価すると、%sの収束が帰納的に示される。$\\qed$"
    };
    public static final String[] MATH_WORDS;
    static {
        String[] extra = {
            "\\newtheorem", "\\theoremstyle", "\\begin{theorem}", "\\begin{lemma}", "\\begin{definition}",
            "\\begin{proof}", "\\qed", "\\qedhere", "\\label", "\\ref", "\\eqref", "\\amsthm"
        };
        MATH_WORDS = new String[LATEX_WORDS.length + extra.length];
        System.arraycopy(LATEX_WORDS, 0, MATH_WORDS, 0, LATEX_WORDS.length);
        System.arraycopy(extra, 0, MATH_WORDS, LATEX_WORDS.length, extra.length);
    }

    public static final class MathPaper {
        public final String code, title;
        public final int sections;
        public final boolean valid, badaValid;
        public final double precision;
        MathPaper(String code, String title, int sections, boolean valid, boolean badaValid, double precision) {
            this.code = code; this.title = title; this.sections = sections;
            this.valid = valid; this.badaValid = badaValid; this.precision = precision;
        }
    }

    /** A long-long MATHEMATICS paper (数学論文): pLaTeX amsthm + embedded Bada. */
    public static MathPaper mathPaper(String cue, int sections, int nonce) {
        final long[] s = { ((long) nonce * 2654435761L + 40503L) & 0xffffffffL };
        java.util.function.LongSupplier nxt = () -> (s[0] = (s[0] * 1103515245L + 12345L) & 0x7fffffffL);

        List<String> words = new ArrayList<>();
        Matcher m = WORD.matcher(cue == null ? "" : cue);
        while (m.find()) words.add(m.group());
        if (words.size() < 3) {
            List<String> lex = MindReader.lexicon();
            words = new ArrayList<>();
            for (int i = 0; i < 3; i++) words.add(lex.get((int) (nxt.getAsLong() % lex.size())));
        }
        final List<String> ws = words;
        java.util.function.Supplier<String> pick = () -> ws.get((int) (nxt.getAsLong() % ws.size()));

        StringBuilder t = new StringBuilder();
        for (int i = 0; i < Math.min(3, ws.size()); i++) { if (i > 0) t.append('と'); t.append(ws.get(i)); }
        String title = t + "に関する大域的部分積分多様体の数学的研究";
        int n = sections > 0 ? sections : Math.min(Math.max(ws.size() * 2, 6), 12);

        List<String> lines = new ArrayList<>();
        lines.add("\\documentclass[a4paper,11pt]{jsarticle}");
        lines.add("\\usepackage{amsmath,amssymb,amsthm}");
        lines.add("\\theoremstyle{plain}");
        lines.add("\\newtheorem{theorem}{定理}[section]");
        lines.add("\\newtheorem{lemma}[theorem]{補題}");
        lines.add("\\theoremstyle{definition}");
        lines.add("\\newtheorem{definition}[theorem]{定義}");
        lines.add("\\title{" + title + "}");
        lines.add("\\author{Bada 数学研究会}");
        lines.add("\\date{\\today}");
        lines.add("\\begin{document}");
        lines.add("\\maketitle");
        lines.add("\\begin{abstract}");
        lines.add(String.format("本論文では、ガンマ関数の大域的部分積分多様体上で%sと%sを定式化し、%sに関する定理を証明する。",
                pick.get(), pick.get(), pick.get()));
        lines.add("\\end{abstract}");
        for (int i = 0; i < n; i++) {
            lines.add("\\section{" + SECTION_TITLES[i % SECTION_TITLES.length] + "}");
            lines.add("\\begin{definition}");
            lines.add(String.format(DEFINITIONS[(int) (nxt.getAsLong() % DEFINITIONS.length)], pick.get(), pick.get(), pick.get()));
            lines.add("\\end{definition}");
            lines.add("\\begin{theorem}");
            lines.add(String.format(THEOREMS[(int) (nxt.getAsLong() % THEOREMS.length)], pick.get(), pick.get(), pick.get()));
            lines.add("\\end{theorem}");
            lines.add("\\begin{equation}");
            lines.add("  " + EQUATIONS[(int) (nxt.getAsLong() % EQUATIONS.length)]);
            lines.add("\\end{equation}");
            lines.add("\\begin{proof}");
            lines.add(String.format(PROOFS[(int) (nxt.getAsLong() % PROOFS.length)], pick.get(), pick.get(), pick.get()));
            lines.add("\\end{proof}");
        }
        BadaSyntax.Program bada = BadaSyntax.buildLong(cue, 4, nonce);
        lines.add("\\section{Bada 言語による構成的計算}");
        lines.add("上記の不変量は、次の Bada 言語プログラムで構成的に計算される。");
        lines.add("\\begin{verbatim}");
        for (String bl : bada.code.split("\n", -1)) lines.add(bl);
        lines.add("\\end{verbatim}");
        lines.add("\\end{document}");

        String code = String.join("\n", lines);
        return new MathPaper(code, title, n, valid(code), bada.valid, Math.max(0.96, SilentTalk.SILENT_TALK_BASELINE + 0.01));
    }

    public static MathPaper mathPaper(String cue, int nonce) { return mathPaper(cue, 0, nonce); }

    /** Light validity: documentclass + document environment + balanced begin/end. */
    public static boolean valid(String code) {
        if (!code.contains("\\documentclass") || !code.contains("\\begin{document}") || !code.contains("\\end{document}")) return false;
        int b = 0, e = 0;
        Matcher mb = BEGIN.matcher(code); while (mb.find()) b++;
        Matcher me = END.matcher(code); while (me.find()) e++;
        return b == e;
    }

    private Platex() { }
}
