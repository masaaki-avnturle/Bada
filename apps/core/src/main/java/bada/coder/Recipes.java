package bada.coder;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import bada.coder.Synth.Arr;
import bada.coder.Synth.ArrDecl;
import bada.coder.Synth.Assign;
import bada.coder.Synth.Bin;
import bada.coder.Synth.Call;
import bada.coder.Synth.Expr;
import bada.coder.Synth.ExprStmt;
import bada.coder.Synth.For;
import bada.coder.Synth.Func;
import bada.coder.Synth.Idx;
import bada.coder.Synth.IdxSet;
import bada.coder.Synth.If;
import bada.coder.Synth.Num;
import bada.coder.Synth.Print;
import bada.coder.Synth.Program;
import bada.coder.Synth.Ret;
import bada.coder.Synth.Stmt;
import bada.coder.Synth.Str;
import bada.coder.Synth.Var;
import bada.coder.Synth.While;

/**
 * Recipes (Java port of Bada::Coder::Recipes) — goal → complete program. Builds
 * classic algorithms as a Synth AST, emitted as original source per language.
 */
final class Recipes {

    // AST builders
    private static Expr num(long n) { return new Num(n, true); }
    private static Expr st(String s) { return new Str(s); }
    private static Expr var(String n) { return new Var(n); }
    private static Expr bn(String op, Expr l, Expr r) { return new Bin(op, l, r); }
    private static Expr cl(String name, Expr... a) { return new Call(name, list(a)); }
    private static Expr ix(String name, Expr e) { return new Idx(name, e); }
    private static Stmt asg(String n, Expr e) { return new Assign(n, e); }
    private static Stmt adecl(String n, List<Expr> es) { return new ArrDecl(n, es); }
    private static Stmt iset(String n, Expr i, Expr e) { return new IdxSet(n, i, e); }
    private static Stmt pr(Expr e) { return new Print(e); }
    private static Stmt ret(Expr e) { return new Ret(e); }
    private static Stmt forr(String v, Expr a, Expr b, Stmt... body) { return new For(v, a, b, list(body)); }
    private static Stmt whl(Expr c, Stmt... body) { return new While(c, list(body)); }
    private static Stmt iff(Expr c, List<Stmt> thn, List<Stmt> els) { return new If(c, thn, els); }
    private static Stmt func(String name, List<String> params, Stmt... body) { return new Func(name, params, list(body)); }

    @SafeVarargs private static <T> List<T> list(T... xs) { List<T> l = new ArrayList<>(); for (T x : xs) l.add(x); return l; }

    private static Program program(String name, Stmt... items) {
        Program p = new Program(name, list(items));
        p = Synth.resolve(p);
        p = Synth.asciify(p);
        return p;
    }

    /** Resolve a goal to a complete program, or null if no recipe matches. */
    static Program forGoal(String goal) {
        String g = goal == null ? "" : goal;
        String gl = g.toLowerCase();
        List<Long> nums = new ArrayList<>();
        Matcher m = Pattern.compile("\\d+").matcher(g);
        while (m.find()) nums.add(Long.parseLong(m.group()));

        if (gl.matches(".*fizz\\s*buzz.*") || g.matches(".*(フィズ\\s*バズ|フィズバズ).*")) return fizzbuzz(n(nums, 0, 20));
        if (gl.contains("fib") || g.contains("フィボ")) return fibonacci(n(nums, 0, 10));
        if (gl.contains("factorial") || g.contains("階乗") || g.contains("ファクトリアル")) return factorial(n(nums, 0, 5));
        if (gl.matches(".*\\bprime\\b.*") || gl.contains("is-prime") || g.contains("素数")) return prime(n(nums, 0, 29));
        if (gl.matches(".*\\bgcd\\b.*") || gl.contains("greatest common") || g.contains("最大公約数")) return gcd(n(nums, 0, 48), n(nums, 1, 36));
        if (gl.matches(".*\\bpower\\b.*") || gl.contains("exponent") || g.contains("べき乗") || g.contains("累乗")) return power(n(nums, 0, 2), n(nums, 1, 10));
        if (gl.contains("multiplication table") || gl.contains("times table") || g.contains("九九") || g.contains("掛け算表")) return multTable(n(nums, 0, 9));
        if (gl.matches(".*\\bsort\\b.*") || gl.contains("bubble") || g.contains("並べ替") || g.contains("並び替") || g.contains("ソート"))
            return bubbleSort(nums.size() >= 2 ? nums : List.of(5L, 2L, 9L, 1L, 7L, 3L));
        if (gl.matches(".*\\bsum\\b.*") || g.contains("合計") || g.contains("総和")) return sumToN(n(nums, 0, 100));
        return null;
    }

    private static long n(List<Long> nums, int i, long dflt) { return i < nums.size() ? nums.get(i) : dflt; }

    static Program factorial(long n) {
        return program("Factorial",
                func("factorial", list("n"),
                        asg("result", num(1)),
                        forr("i", num(1), var("n"), asg("result", bn("*", var("result"), var("i")))),
                        ret(var("result"))),
                pr(cl("factorial", num(n))));
    }

    static Program fibonacci(long n) {
        return program("Fibonacci",
                func("fib", list("n"),
                        asg("a", num(0)),
                        asg("b", num(1)),
                        forr("i", num(1), var("n"),
                                pr(var("a")),
                                asg("t", bn("+", var("a"), var("b"))),
                                asg("a", var("b")),
                                asg("b", var("t")))),
                new ExprStmt(cl("fib", num(n))));
    }

    static Program fizzbuzz(long n) {
        return program("FizzBuzz",
                forr("i", num(1), num(n),
                        iff(bn("==", bn("%", var("i"), num(15)), num(0)),
                                list(pr(st("FizzBuzz"))),
                                list(iff(bn("==", bn("%", var("i"), num(3)), num(0)),
                                        list(pr(st("Fizz"))),
                                        list(iff(bn("==", bn("%", var("i"), num(5)), num(0)),
                                                list(pr(st("Buzz"))),
                                                list(pr(var("i"))))))))));
    }

    static Program prime(long n) {
        return program("Prime",
                func("is_prime", list("n"),
                        iff(bn("<", var("n"), num(2)), list(ret(num(0))), list()),
                        asg("i", num(2)),
                        whl(bn("<=", bn("*", var("i"), var("i")), var("n")),
                                iff(bn("==", bn("%", var("n"), var("i")), num(0)), list(ret(num(0))), list()),
                                asg("i", bn("+", var("i"), num(1)))),
                        ret(num(1))),
                pr(cl("is_prime", num(n))));
    }

    static Program gcd(long a, long b) {
        return program("Gcd",
                func("gcd", list("a", "b"),
                        whl(bn("!=", var("b"), num(0)),
                                asg("t", var("b")),
                                asg("b", bn("%", var("a"), var("b"))),
                                asg("a", var("t"))),
                        ret(var("a"))),
                pr(cl("gcd", num(a), num(b))));
    }

    static Program power(long base, long exp) {
        return program("Power",
                func("power", list("base", "exp"),
                        asg("result", num(1)),
                        forr("i", num(1), var("exp"), asg("result", bn("*", var("result"), var("base")))),
                        ret(var("result"))),
                pr(cl("power", num(base), num(exp))));
    }

    static Program multTable(long n) {
        return program("MultiplicationTable",
                forr("i", num(1), num(n),
                        forr("j", num(1), num(n), pr(bn("*", var("i"), var("j"))))));
    }

    static Program sumToN(long n) {
        return program("Sum",
                func("sum_to", list("n"),
                        asg("total", num(0)),
                        forr("i", num(1), var("n"), asg("total", bn("+", var("total"), var("i")))),
                        ret(var("total"))),
                pr(cl("sum_to", num(n))));
    }

    static Program bubbleSort(List<Long> listIn) {
        List<Long> vals = listIn.size() > 64 ? listIn.subList(0, 64) : listIn;
        int len = vals.size();
        List<Expr> elems = new ArrayList<>();
        for (long v : vals) elems.add(num(v));
        return program("BubbleSort",
                adecl("a", elems),
                forr("i", num(0), num(len - 1),
                        forr("j", num(0), num(len - 2),
                                iff(bn(">", ix("a", var("j")), ix("a", bn("+", var("j"), num(1)))),
                                        list(asg("t", ix("a", var("j"))),
                                                iset("a", var("j"), ix("a", bn("+", var("j"), num(1)))),
                                                iset("a", bn("+", var("j"), num(1)), var("t"))),
                                        list()))),
                forr("k", num(0), num(len - 1), pr(ix("a", var("k")))));
    }

    private Recipes() {}
}
