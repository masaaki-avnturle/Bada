package bada.coder;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Synth (Java port of Bada::Coder::Synth) — a natural-language → program
 * compiler. It parses a described intent (English or 日本語) into an AST of
 * statements and expressions, then emits ORIGINAL source code in the target
 * language. Rule-based intent compiler, not an LLM.
 *
 * Statements are separated by ";", newline, "。" or "そして"; "then" delimits an
 * if…then…else. Operands are ASCII/Japanese names, numbers, or "quoted strings".
 */
public final class Synth {

    // ===== AST =====
    sealed interface Expr permits Num, Str, Var, Bin, Neg, Call, Idx, Arr {}
    record Num(double v, boolean isInt) implements Expr {}
    record Str(String v) implements Expr {}
    record Var(String name) implements Expr {}
    record Bin(String op, Expr l, Expr r) implements Expr {}
    record Neg(Expr e) implements Expr {}
    record Call(String name, List<Expr> args) implements Expr {}
    record Idx(String name, Expr index) implements Expr {}
    record Arr(List<Expr> elems) implements Expr {}

    sealed interface Stmt permits Assign, Print, Ret, ExprStmt, For, While, If, Func, ArrDecl, IdxSet {}
    record Assign(String var, Expr e) implements Stmt {}
    record Print(Expr e) implements Stmt {}
    record Ret(Expr e) implements Stmt {}
    record ExprStmt(Expr e) implements Stmt {}
    record For(String var, Expr from, Expr to, List<Stmt> body) implements Stmt {}
    record While(Expr cond, List<Stmt> body) implements Stmt {}
    record If(Expr cond, List<Stmt> thenB, List<Stmt> elseB) implements Stmt {}
    record Func(String name, List<String> params, List<Stmt> body) implements Stmt {}
    record ArrDecl(String name, List<Expr> elems) implements Stmt {}
    record IdxSet(String name, Expr index, Expr value) implements Stmt {}

    public record Program(String name, List<Stmt> items) {}

    enum Type { INT, DOUBLE, STRING, ARRAY, VOID }

    private static final String IDENT = "[A-Za-z_]\\w*|[一-鿿ァ-ヶー]+";
    private static final String BODY_VERB =
        "(?:print|puts|show|output|display|echo|log|say|set|let|assign|return|add|increment|increase|call|if|while|for|repeat)\\b";

    // ===== compile =====
    public static Program compile(String intent) {
        String text = intent == null ? "" : intent;
        List<Stmt> items = new ArrayList<>();
        for (String seg : splitSegments(text)) {
            Stmt s = parseStatement(seg.trim());
            if (s != null) items.add(s);
        }
        Program prog = new Program(programName(text), items);
        prog = resolve(prog);
        prog = asciify(prog);
        return prog;
    }

    static String programName(String text) {
        Matcher m = Pattern.compile("\\b(?:function|func|def|program|class)\\s+([A-Za-z_]\\w*)").matcher(text);
        String n = m.find() ? m.group(1) : "program";
        return n.substring(0, 1).toUpperCase() + n.substring(1);
    }

    // ===== segmentation =====
    static List<String> splitSegments(String text) {
        text = text.replaceAll("\\r\\n?", "\n");
        text = text.replaceAll("(?i)\\band then\\b", ";").replace("そして", ";").replace("。", ";").replace("\n", ";");
        List<String> out = new ArrayList<>();
        int depth = 0;
        StringBuilder buf = new StringBuilder();
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (ch == '(') { depth++; buf.append(ch); }
            else if (ch == ')') { depth--; buf.append(ch); }
            else if (ch == ';') {
                if (depth <= 0) { out.add(buf.toString()); buf = new StringBuilder(); }
                else buf.append(ch);
            } else buf.append(ch);
        }
        out.add(buf.toString());
        List<String> res = new ArrayList<>();
        for (String s : out) if (!s.trim().isEmpty()) res.add(s);
        return res;
    }

    // ===== statement parsing =====
    private static Matcher mm(String re, String s) {
        Matcher m = Pattern.compile(re, Pattern.CASE_INSENSITIVE).matcher(s);
        return m.matches() ? m : null;
    }
    private static Matcher mmU(String re, String s) { // unicode/no-ignorecase
        Matcher m = Pattern.compile(re).matcher(s);
        return m.matches() ? m : null;
    }

    static Stmt parseStatement(String seg) {
        if (seg.isEmpty()) return null;
        Matcher m;

        // FUNCTION: function NAME (with|taking|of)? PARAMS returns EXPR
        if ((m = mm("(?:define\\s+|create\\s+)?(?:a\\s+)?(?:function|func|method)\\s+([A-Za-z_]\\w*)\\s*(?:\\((.*?)\\)|(?:with|taking|of)\\s+(.+?))?\\s+(?:that\\s+)?(?:returns?|returning)\\s+(.+)", seg)) != null) {
            String params = coalesce(m.group(2), m.group(3), "");
            List<Stmt> body = list(new Ret(parseExpr(m.group(4))));
            return new Func(m.group(1), parseParams(params), body);
        }
        // JP function: NAME 関数 (引数 PARAMS)? EXPR を返す
        if ((m = mmU("(" + IDENT + ")\\s*(?:という)?関数\\s*(?:\\((.*?)\\)|(?:引数)?\\s*(.+?))?\\s*[はがを]?\\s*(.+?)\\s*を返す", seg)) != null) {
            String params = coalesce(m.group(2), m.group(3), "");
            return new Func(m.group(1), parseParams(params), list(new Ret(parseExpr(m.group(4)))));
        }

        // FOR: for VAR from A to B [:|do|space] STMT
        if ((m = mm("for\\s+([A-Za-z_]\\w*)\\s+from\\s+(.+?)\\s+to\\s+(.+?)(?:\\s*[:,]|\\s+do\\b|\\s+)(.+)", seg)) != null) {
            return new For(m.group(1), parseExpr(m.group(2)), parseExpr(m.group(3)), stmtList(m.group(4)));
        }
        if ((m = mm("repeat\\s+(.+?)\\s+times?\\s+(.+)", seg)) != null) {
            return new For("_i", new Num(1, true), parseExpr(m.group(1)), stmtList(m.group(2)));
        }
        // JP for: A から B まで VAR STMT (繰り返す)? | STMT を N 回 繰り返す
        if ((m = mmU("(.+?)\\s*から\\s*(.+?)\\s*まで\\s*(" + IDENT + ")\\s*を?\\s*(.+?)(?:を?\\s*繰り返す)?", seg)) != null) {
            return new For(m.group(3), parseExpr(m.group(1)), parseExpr(m.group(2)), stmtList(m.group(4)));
        }
        if ((m = mmU("(.+?)\\s*を\\s*(.+?)\\s*回\\s*繰り返す", seg)) != null) {
            return new For("_i", new Num(1, true), parseExpr(m.group(2)), stmtList(m.group(1)));
        }

        // WHILE
        if ((m = mm("while\\s+(.+?)(?:\\s*[:,]|\\s+do\\b)\\s*(.+)", seg)) != null) {
            return new While(parseExpr(m.group(1)), stmtList(m.group(2)));
        }
        if ((m = mm("while\\s+(.+?)\\s+(" + BODY_VERB + ".+)", seg)) != null) {
            return new While(parseExpr(m.group(1)), stmtList(m.group(2)));
        }

        // IF: if COND then STMT [else STMT]
        if ((m = mm("if\\s+(.+?)\\s+then\\s+(.+?)(?:\\s+else\\s+(.+))?", seg)) != null) {
            List<Stmt> els = m.group(3) != null ? stmtList(m.group(3)) : new ArrayList<>();
            return new If(parseExpr(m.group(1)), stmtList(m.group(2)), els);
        }
        // JP if: もし COND なら STMT (でなければ STMT)
        if ((m = mmU("もし\\s*(.+?)\\s*なら\\s*(.+?)(?:\\s*でなければ\\s*(.+))?", seg)) != null) {
            List<Stmt> els = m.group(3) != null ? stmtList(m.group(3)) : new ArrayList<>();
            return new If(parseExpr(m.group(1)), stmtList(m.group(2)), els);
        }

        // RETURN
        if ((m = mm("return\\s+(.+)", seg)) != null) return new Ret(parseExpr(m.group(1)));
        if ((m = mmU("(.+?)\\s*を返す", seg)) != null) return new Ret(parseExpr(m.group(1)));

        // PRINT
        if ((m = mm("(?:print|puts|show|output|display|echo|log|say)\\s+(.+)", seg)) != null) {
            return new Print(parseExpr(m.group(1)));
        }
        if ((m = mmU("(.+?)\\s*を\\s*(?:表示|出力|印刷|プリント)(?:する)?", seg)) != null) {
            return new Print(parseExpr(m.group(1)));
        }

        // COMPOUND ADD
        if ((m = mm("add\\s+(.+?)\\s+to\\s+([A-Za-z_]\\w*)", seg)) != null) {
            return new Assign(m.group(2), new Bin("+", new Var(m.group(2)), parseExpr(m.group(1))));
        }
        if ((m = mmU("(" + IDENT + ")\\s*に\\s*(.+?)\\s*を\\s*(?:足す|加える|加算(?:する)?)", seg)) != null) {
            return new Assign(m.group(1), new Bin("+", new Var(m.group(1)), parseExpr(m.group(2))));
        }
        if ((m = mm("(?:increment|increase)\\s+([A-Za-z_]\\w*)(?:\\s+by\\s+(.+))?", seg)) != null) {
            Expr by = m.group(2) != null ? parseExpr(m.group(2)) : new Num(1, true);
            return new Assign(m.group(1), new Bin("+", new Var(m.group(1)), by));
        }

        // ASSIGN
        if ((m = mm("(?:set|let)\\s+([A-Za-z_]\\w*)\\s+(?:to|be|=)\\s+(.+)", seg)) != null) {
            return new Assign(m.group(1), parseExpr(m.group(2)));
        }
        if ((m = mm("assign\\s+(.+?)\\s+to\\s+([A-Za-z_]\\w*)", seg)) != null) {
            return new Assign(m.group(2), parseExpr(m.group(1)));
        }
        if ((m = mm("([A-Za-z_]\\w*)\\s*=\\s*(.+)", seg)) != null) {
            return new Assign(m.group(1), parseExpr(m.group(2)));
        }
        if ((m = mmU("(" + IDENT + ")\\s*を\\s*(.+?)\\s*に(?:する|セット)", seg)) != null) {
            return new Assign(m.group(1), parseExpr(m.group(2)));
        }
        if ((m = mmU("(" + IDENT + ")\\s*に\\s*(.+?)\\s*を\\s*代入(?:する)?", seg)) != null) {
            return new Assign(m.group(1), parseExpr(m.group(2)));
        }
        if ((m = mmU("(" + IDENT + ")\\s*は\\s*(.+)", seg)) != null) {
            return new Assign(m.group(1), parseExpr(m.group(2)));
        }

        // CALL / bare expression
        if ((m = mm("call\\s+(.+)", seg)) != null) return new ExprStmt(parseExpr(m.group(1)));
        Expr e = parseExpr(seg);
        return e != null ? new ExprStmt(e) : null;
    }

    static List<Stmt> stmtList(String seg) {
        List<Stmt> l = new ArrayList<>();
        Stmt s = parseStatement(seg.trim());
        if (s != null) l.add(s);
        return l;
    }

    static List<String> parseParams(String str) {
        List<String> out = new ArrayList<>();
        if (str == null) return out;
        for (String p : str.replaceAll("(?i)\\band\\b", ",").split("[,\\s]+")) {
            p = p.trim();
            if (!p.isEmpty() && p.matches("[A-Za-z_]\\w*")) out.add(p);
        }
        return out;
    }

    // ===== expression parsing =====
    static Expr parseExpr(String str) {
        try {
            List<String[]> toks = lex(normalizeOps(str));
            return new Parser(toks).parse();
        } catch (RuntimeException ex) {
            return null;
        }
    }

    static String normalizeOps(String s) {
        s = " " + s + " ";
        String[][] subs = {
            {"(?i)\\bis\\s+greater\\s+than\\s+or\\s+equal\\s+to\\b", " >= "}, {"(?i)\\bat\\s+least\\b", " >= "}, {"以上", " >= "},
            {"(?i)\\bis\\s+less\\s+than\\s+or\\s+equal\\s+to\\b", " <= "}, {"(?i)\\bat\\s+most\\b", " <= "}, {"以下", " <= "},
            {"(?i)\\bis\\s+greater\\s+than\\b", " > "}, {"(?i)\\bgreater\\s+than\\b", " > "}, {"より大きい|を超える|超える", " > "},
            {"(?i)\\bis\\s+less\\s+than\\b", " < "}, {"(?i)\\bless\\s+than\\b", " < "}, {"より小さい|未満", " < "},
            {"(?i)\\bis\\s+not\\s+equal\\s+to\\b", " != "}, {"(?i)\\bnot\\s+equal\\s+to\\b", " != "},
            {"(?i)\\bis\\s+equal\\s+to\\b", " == "}, {"(?i)\\bequal\\s+to\\b", " == "}, {"(?i)\\bequals\\b", " == "}, {"等しい", " == "},
            {"(?i)\\bplus\\b", " + "}, {"(?i)\\bminus\\b", " - "},
            {"(?i)\\btimes\\b", " * "}, {"(?i)\\bmultiplied\\s+by\\b", " * "},
            {"(?i)\\bdivided\\s+by\\b", " / "}, {"(?i)\\bmodulo\\b", " % "}, {"(?i)\\bmod\\b", " % "},
            {"足す|プラス|加える", " + "}, {"引く|マイナス", " - "}, {"掛ける|かける", " * "}, {"割る|わる", " / "}
        };
        for (String[] sub : subs) s = s.replaceAll(sub[0], sub[1]);
        return s;
    }

    // lexer -> list of [kind, text]
    static List<String[]> lex(String s) {
        List<String[]> toks = new ArrayList<>();
        int i = 0, n = s.length();
        while (i < n) {
            char ch = s.charAt(i);
            if (Character.isWhitespace(ch)) { i++; continue; }
            Matcher m;
            if ((m = Pattern.compile("^\\d+(?:\\.\\d+)?").matcher(s.substring(i))).find()) {
                toks.add(new String[]{"num", m.group()}); i += m.group().length();
            } else if (ch == '"' || ch == '\'') {
                int j = s.indexOf(ch, i + 1); if (j < 0) j = n - 1;
                toks.add(new String[]{"str", s.substring(i + 1, j)}); i = j + 1;
            } else if ((m = Pattern.compile("^[A-Za-z_]\\w*").matcher(s.substring(i))).find()) {
                toks.add(new String[]{"ident", m.group()}); i += m.group().length();
            } else if ((m = Pattern.compile("^[一-鿿ァ-ヶー]+").matcher(s.substring(i))).find()) {
                toks.add(new String[]{"ident", m.group()}); i += m.group().length();
            } else if ((m = Pattern.compile("^(>=|<=|==|!=|&&|\\|\\||[-+*/%()<>,])").matcher(s.substring(i))).find()) {
                toks.add(new String[]{"op", m.group()}); i += m.group().length();
            } else { i++; }
        }
        return toks;
    }

    static final class Parser {
        private final List<String[]> t;
        private int i = 0;
        Parser(List<String[]> t) { this.t = t; }
        Expr parse() { return comparison(); }
        private String[] peek() { return i < t.size() ? t.get(i) : null; }
        private String acceptOp(String... ops) {
            String[] p = peek();
            if (p != null && p[0].equals("op")) for (String o : ops) if (o.equals(p[1])) { i++; return o; }
            return null;
        }
        private Expr comparison() {
            Expr left = additive();
            String op = acceptOp(">", "<", ">=", "<=", "==", "!=", "&&", "||");
            if (op != null) return new Bin(op, left, additive());
            return left;
        }
        private Expr additive() {
            Expr node = term();
            String op;
            while ((op = acceptOp("+", "-")) != null) node = new Bin(op, node, term());
            return node;
        }
        private Expr term() {
            Expr node = unary();
            String op;
            while ((op = acceptOp("*", "/", "%")) != null) node = new Bin(op, node, unary());
            return node;
        }
        private Expr unary() {
            if (acceptOp("-") != null) return new Neg(unary());
            return primary();
        }
        private Expr primary() {
            String[] p = peek();
            if (p == null) return new Num(0, true);
            if (p[0].equals("num")) { i++; boolean isInt = !p[1].contains("."); return new Num(Double.parseDouble(p[1]), isInt); }
            if (p[0].equals("str")) { i++; return new Str(p[1]); }
            if (p[0].equals("ident")) {
                i++;
                String name = p[1];
                String[] q = peek();
                if (q != null && q[0].equals("op") && q[1].equals("(")) {
                    i++;
                    List<Expr> args = new ArrayList<>();
                    String[] r = peek();
                    if (!(r != null && r[0].equals("op") && r[1].equals(")"))) {
                        args.add(comparison());
                        while (peek() != null && peek()[0].equals("op") && peek()[1].equals(",")) { i++; args.add(comparison()); }
                    }
                    acceptOp(")");
                    return new Call(name, args);
                }
                return new Var(name);
            }
            if (p[0].equals("op") && p[1].equals("(")) { i++; Expr e = comparison(); acceptOp(")"); return e; }
            i++;
            return new Num(0, true);
        }
    }

    // ===== resolve unknown identifiers -> string literals =====
    static Program resolve(Program prog) {
        Set<String> funcs = new HashSet<>();
        for (Stmt s : prog.items()) if (s instanceof Func f) funcs.add(f.name());
        Set<String> declared = new HashSet<>();
        List<Stmt> items = new ArrayList<>();
        for (Stmt s : prog.items()) items.add(resolveStmt(s, declared, funcs));
        return new Program(prog.name(), items);
    }

    static Stmt resolveStmt(Stmt s, Set<String> declared, Set<String> funcs) {
        if (s instanceof Func f) {
            Set<String> local = new HashSet<>(declared); local.addAll(f.params());
            return new Func(f.name(), f.params(), resolveBody(f.body(), local, funcs));
        } else if (s instanceof Assign a) {
            Expr e = resolveExpr(a.e(), declared, funcs);
            declared.add(a.var());
            return new Assign(a.var(), e);
        } else if (s instanceof ArrDecl ad) {
            List<Expr> es = new ArrayList<>();
            for (Expr x : ad.elems()) es.add(resolveExpr(x, declared, funcs));
            declared.add(ad.name());
            return new ArrDecl(ad.name(), es);
        } else if (s instanceof IdxSet is) {
            return new IdxSet(is.name(), resolveExpr(is.index(), declared, funcs), resolveExpr(is.value(), declared, funcs));
        } else if (s instanceof Print p) {
            return new Print(resolveExpr(p.e(), declared, funcs));
        } else if (s instanceof Ret r) {
            return new Ret(resolveExpr(r.e(), declared, funcs));
        } else if (s instanceof ExprStmt es) {
            return new ExprStmt(resolveExpr(es.e(), declared, funcs));
        } else if (s instanceof For fo) {
            Expr from = resolveExpr(fo.from(), declared, funcs);
            Expr to = resolveExpr(fo.to(), declared, funcs);
            Set<String> local = new HashSet<>(declared); local.add(fo.var());
            return new For(fo.var(), from, to, resolveBody(fo.body(), local, funcs));
        } else if (s instanceof While w) {
            return new While(resolveExpr(w.cond(), declared, funcs), resolveBody(w.body(), declared, funcs));
        } else if (s instanceof If f) {
            return new If(resolveExpr(f.cond(), declared, funcs),
                    resolveBody(f.thenB(), declared, funcs), resolveBody(f.elseB(), declared, funcs));
        }
        return s;
    }

    static List<Stmt> resolveBody(List<Stmt> body, Set<String> declared, Set<String> funcs) {
        List<Stmt> out = new ArrayList<>();
        for (Stmt s : body) out.add(resolveStmt(s, declared, funcs));
        return out;
    }

    static Expr resolveExpr(Expr e, Set<String> declared, Set<String> funcs) {
        if (e == null) return null;
        if (e instanceof Var v) return declared.contains(v.name()) ? e : new Str(v.name());
        if (e instanceof Bin b) return new Bin(b.op(), resolveExpr(b.l(), declared, funcs), resolveExpr(b.r(), declared, funcs));
        if (e instanceof Neg ng) return new Neg(resolveExpr(ng.e(), declared, funcs));
        if (e instanceof Call c) {
            List<Expr> args = new ArrayList<>();
            for (Expr a : c.args()) args.add(resolveExpr(a, declared, funcs));
            return new Call(c.name(), args);
        }
        if (e instanceof Idx ix) return new Idx(ix.name(), resolveExpr(ix.index(), declared, funcs));
        if (e instanceof Arr ar) {
            List<Expr> es = new ArrayList<>();
            for (Expr x : ar.elems()) es.add(resolveExpr(x, declared, funcs));
            return new Arr(es);
        }
        return e;
    }

    // ===== transliterate Japanese identifiers to ASCII =====
    static Program asciify(Program prog) {
        Map<String, String> map = new LinkedHashMap<>();
        int[] counter = {0};
        List<Stmt> items = new ArrayList<>();
        for (Stmt s : prog.items()) items.add(asciifyStmt(s, map, counter));
        return new Program(asciiName(prog.name(), map, counter), items);
    }

    static String asciiName(String name, Map<String, String> map, int[] counter) {
        if (name == null || name.matches("[A-Za-z_]\\w*")) return name;
        return map.computeIfAbsent(name, k -> "v" + (++counter[0]));
    }

    static Stmt asciifyStmt(Stmt s, Map<String, String> map, int[] counter) {
        if (s instanceof Func f) {
            List<String> ps = new ArrayList<>();
            for (String p : f.params()) ps.add(asciiName(p, map, counter));
            return new Func(asciiName(f.name(), map, counter), ps, asciifyBody(f.body(), map, counter));
        } else if (s instanceof Assign a) {
            return new Assign(asciiName(a.var(), map, counter), asciifyExpr(a.e(), map, counter));
        } else if (s instanceof ArrDecl ad) {
            List<Expr> es = new ArrayList<>();
            for (Expr x : ad.elems()) es.add(asciifyExpr(x, map, counter));
            return new ArrDecl(asciiName(ad.name(), map, counter), es);
        } else if (s instanceof IdxSet is) {
            return new IdxSet(asciiName(is.name(), map, counter), asciifyExpr(is.index(), map, counter), asciifyExpr(is.value(), map, counter));
        } else if (s instanceof Print p) {
            return new Print(asciifyExpr(p.e(), map, counter));
        } else if (s instanceof Ret r) {
            return new Ret(asciifyExpr(r.e(), map, counter));
        } else if (s instanceof ExprStmt es) {
            return new ExprStmt(asciifyExpr(es.e(), map, counter));
        } else if (s instanceof For fo) {
            return new For(asciiName(fo.var(), map, counter), asciifyExpr(fo.from(), map, counter),
                    asciifyExpr(fo.to(), map, counter), asciifyBody(fo.body(), map, counter));
        } else if (s instanceof While w) {
            return new While(asciifyExpr(w.cond(), map, counter), asciifyBody(w.body(), map, counter));
        } else if (s instanceof If f) {
            return new If(asciifyExpr(f.cond(), map, counter), asciifyBody(f.thenB(), map, counter), asciifyBody(f.elseB(), map, counter));
        }
        return s;
    }

    static List<Stmt> asciifyBody(List<Stmt> body, Map<String, String> map, int[] counter) {
        List<Stmt> out = new ArrayList<>();
        for (Stmt s : body) out.add(asciifyStmt(s, map, counter));
        return out;
    }

    static Expr asciifyExpr(Expr e, Map<String, String> map, int[] counter) {
        if (e == null) return null;
        if (e instanceof Var v) return new Var(asciiName(v.name(), map, counter));
        if (e instanceof Call c) {
            List<Expr> args = new ArrayList<>();
            for (Expr a : c.args()) args.add(asciifyExpr(a, map, counter));
            return new Call(asciiName(c.name(), map, counter), args);
        }
        if (e instanceof Bin b) return new Bin(b.op(), asciifyExpr(b.l(), map, counter), asciifyExpr(b.r(), map, counter));
        if (e instanceof Neg ng) return new Neg(asciifyExpr(ng.e(), map, counter));
        if (e instanceof Idx ix) return new Idx(asciiName(ix.name(), map, counter), asciifyExpr(ix.index(), map, counter));
        if (e instanceof Arr ar) {
            List<Expr> es = new ArrayList<>();
            for (Expr x : ar.elems()) es.add(asciifyExpr(x, map, counter));
            return new Arr(es);
        }
        return e;
    }

    // ===== type inference (C / Java) =====
    static Map<String, Type> inferTypes(Program prog) {
        Map<String, Type> types = new LinkedHashMap<>();
        for (Stmt s : prog.items()) inferStmt(s, types);
        return types;
    }
    static void inferStmt(Stmt s, Map<String, Type> types) {
        if (s instanceof Assign a) { types.putIfAbsent(a.var(), inferExpr(a.e(), types)); }
        else if (s instanceof ArrDecl ad) { types.put(ad.name(), Type.ARRAY); }
        // the loop variable is declared by the for-statement itself, so it is NOT typed here
        else if (s instanceof For fo) { for (Stmt b : fo.body()) inferStmt(b, types); }
        else if (s instanceof While w) { for (Stmt b : w.body()) inferStmt(b, types); }
        else if (s instanceof If f) { for (Stmt b : f.thenB()) inferStmt(b, types); for (Stmt b : f.elseB()) inferStmt(b, types); }
    }
    static Type inferExpr(Expr e, Map<String, Type> types) {
        if (e instanceof Num n) return n.isInt() ? Type.INT : Type.DOUBLE;
        if (e instanceof Str) return Type.STRING;
        if (e instanceof Var v) return types.getOrDefault(v.name(), Type.INT);
        if (e instanceof Idx) return Type.INT;
        if (e instanceof Arr) return Type.ARRAY;
        if (e instanceof Neg ng) return inferExpr(ng.e(), types);
        if (e instanceof Bin b) {
            if (List.of(">", "<", ">=", "<=", "==", "!=", "&&", "||").contains(b.op())) return Type.INT;
            Type lt = inferExpr(b.l(), types), rt = inferExpr(b.r(), types);
            if (b.op().equals("+") && (lt == Type.STRING || rt == Type.STRING)) return Type.STRING;
            if (b.op().equals("/") || lt == Type.DOUBLE || rt == Type.DOUBLE) return Type.DOUBLE;
            return Type.INT;
        }
        return Type.INT;
    }

    // ===== emit =====
    public static String emit(String language, Program prog) {
        return switch (language) {
            case "python" -> Emit.python(prog);
            case "javascript" -> Emit.javascript(prog);
            case "c" -> Emit.c(prog, inferTypes(prog));
            case "java" -> Emit.java(prog, inferTypes(prog));
            case "bada" -> Emit.bada(prog);
            default -> Emit.ruby(prog);
        };
    }

    static String num(Num n) {
        if (n.isInt()) return Long.toString((long) n.v());
        return Double.toString(n.v());
    }

    // shared expression rendering (arithmetic/comparison syntax is common)
    static String expr(Expr e) {
        if (e == null) return "0";
        if (e instanceof Num n) return num(n);
        if (e instanceof Str s) return "\"" + s.v() + "\"";
        if (e instanceof Var v) return v.name();
        if (e instanceof Neg ng) return "-" + expr(ng.e());
        if (e instanceof Call c) {
            List<String> a = new ArrayList<>();
            for (Expr x : c.args()) a.add(expr(x));
            return c.name() + "(" + String.join(", ", a) + ")";
        }
        if (e instanceof Idx ix) return ix.name() + "[" + expr(ix.index()) + "]";
        if (e instanceof Arr ar) {
            List<String> xs = new ArrayList<>();
            for (Expr x : ar.elems()) xs.add(expr(x));
            return "[" + String.join(", ", xs) + "]";
        }
        if (e instanceof Bin b) return "(" + expr(b.l()) + " " + b.op() + " " + expr(b.r()) + ")";
        return "0";
    }

    // Types of a function's local variables (assigns/arrdecls), minus params and
    // loop variables — needed for C/Java declarations inside a function body.
    static Map<String, Type> localTypes(List<String> params, List<Stmt> body) {
        Map<String, Type> t = new LinkedHashMap<>();
        for (Stmt s : body) inferStmt(s, t);
        for (String p : params) t.remove(p);
        return t;
    }

    // helpers
    @SafeVarargs
    static <T> List<T> list(T... xs) { List<T> l = new ArrayList<>(); for (T x : xs) l.add(x); return l; }
    static String coalesce(String... xs) { for (String x : xs) if (x != null) return x; return null; }

    private Synth() {}
}
