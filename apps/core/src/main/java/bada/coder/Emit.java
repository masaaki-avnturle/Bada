package bada.coder;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import bada.coder.Synth.Arr;
import bada.coder.Synth.ArrDecl;
import bada.coder.Synth.Assign;
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
import bada.coder.Synth.Type;
import bada.coder.Synth.Var;
import bada.coder.Synth.While;

/** Per-language emitters for the Synth AST (Java port of Bada::Coder::Synth::Emit). */
final class Emit {

    private static String ind(int d) { return "  ".repeat(d); }
    private static String ex(Synth.Expr e) { return Synth.expr(e); }
    private static String elems(List<Synth.Expr> es) {
        List<String> x = new ArrayList<>();
        for (Synth.Expr e : es) x.add(ex(e));
        return String.join(", ", x);
    }

    // ---- Ruby ----
    static String ruby(Program p) {
        List<String> out = new ArrayList<>();
        for (Stmt s : p.items()) if (s instanceof Func f) out.addAll(rubyFunc(f));
        for (Stmt s : p.items()) if (!(s instanceof Func)) out.addAll(rubyStmt(s, 0));
        return String.join("\n", out) + "\n";
    }
    private static List<String> rubyFunc(Func f) {
        List<String> o = new ArrayList<>();
        o.add("def " + f.name() + "(" + String.join(", ", f.params()) + ")");
        for (Stmt s : f.body()) o.addAll(rubyStmt(s, 1));
        o.add("end"); o.add("");
        return o;
    }
    private static List<String> rubyStmt(Stmt s, int d) {
        String i = ind(d);
        List<String> o = new ArrayList<>();
        if (s instanceof Assign a) o.add(i + a.var() + " = " + ex(a.e()));
        else if (s instanceof ArrDecl ad) o.add(i + ad.name() + " = [" + elems(ad.elems()) + "]");
        else if (s instanceof IdxSet is) o.add(i + is.name() + "[" + ex(is.index()) + "] = " + ex(is.value()));
        else if (s instanceof Print pr) o.add(i + "puts " + ex(pr.e()));
        else if (s instanceof Ret r) o.add(i + "return " + ex(r.e()));
        else if (s instanceof ExprStmt es) o.add(i + ex(es.e()));
        else if (s instanceof For f) {
            o.add(i + "(" + ex(f.from()) + ".." + ex(f.to()) + ").each do |" + f.var() + "|");
            for (Stmt b : f.body()) o.addAll(rubyStmt(b, d + 1));
            o.add(i + "end");
        } else if (s instanceof While w) {
            o.add(i + "while " + ex(w.cond()));
            for (Stmt b : w.body()) o.addAll(rubyStmt(b, d + 1));
            o.add(i + "end");
        } else if (s instanceof If f) {
            o.add(i + "if " + ex(f.cond()));
            for (Stmt b : f.thenB()) o.addAll(rubyStmt(b, d + 1));
            if (!f.elseB().isEmpty()) { o.add(i + "else"); for (Stmt b : f.elseB()) o.addAll(rubyStmt(b, d + 1)); }
            o.add(i + "end");
        }
        return o;
    }

    // ---- Python ----
    static String python(Program p) {
        List<String> out = new ArrayList<>();
        for (Stmt s : p.items()) if (s instanceof Func f) out.addAll(pyFunc(f));
        for (Stmt s : p.items()) if (!(s instanceof Func)) out.addAll(pyStmt(s, 0));
        return String.join("\n", out) + "\n";
    }
    private static List<String> pyFunc(Func f) {
        List<String> o = new ArrayList<>();
        o.add("def " + f.name() + "(" + String.join(", ", f.params()) + "):");
        List<String> body = new ArrayList<>();
        for (Stmt s : f.body()) body.addAll(pyStmt(s, 1));
        o.addAll(body.isEmpty() ? List.of("    pass") : body);
        o.add("");
        return o;
    }
    private static List<String> pyStmt(Stmt s, int d) {
        String i = "    ".repeat(d);
        List<String> o = new ArrayList<>();
        if (s instanceof Assign a) o.add(i + a.var() + " = " + ex(a.e()));
        else if (s instanceof ArrDecl ad) o.add(i + ad.name() + " = [" + elems(ad.elems()) + "]");
        else if (s instanceof IdxSet is) o.add(i + is.name() + "[" + ex(is.index()) + "] = " + ex(is.value()));
        else if (s instanceof Print pr) o.add(i + "print(" + ex(pr.e()) + ")");
        else if (s instanceof Ret r) o.add(i + "return " + ex(r.e()));
        else if (s instanceof ExprStmt es) o.add(i + ex(es.e()));
        else if (s instanceof For f) {
            o.add(i + "for " + f.var() + " in range(" + ex(f.from()) + ", (" + ex(f.to()) + ") + 1):");
            o.addAll(pyBody(f.body(), d + 1));
        } else if (s instanceof While w) {
            o.add(i + "while " + ex(w.cond()) + ":");
            o.addAll(pyBody(w.body(), d + 1));
        } else if (s instanceof If f) {
            o.add(i + "if " + ex(f.cond()) + ":");
            o.addAll(pyBody(f.thenB(), d + 1));
            if (!f.elseB().isEmpty()) { o.add(i + "else:"); o.addAll(pyBody(f.elseB(), d + 1)); }
        }
        return o;
    }
    private static List<String> pyBody(List<Stmt> body, int d) {
        List<String> o = new ArrayList<>();
        for (Stmt s : body) o.addAll(pyStmt(s, d));
        return o.isEmpty() ? List.of("    ".repeat(d) + "pass") : o;
    }

    // ---- JavaScript ----
    static String javascript(Program p) {
        List<String> out = new ArrayList<>();
        Set<String> declared = new HashSet<>();
        for (Stmt s : p.items()) if (s instanceof Func f) out.addAll(jsFunc(f));
        for (Stmt s : p.items()) if (!(s instanceof Func)) out.addAll(jsStmt(s, 0, declared));
        return String.join("\n", out) + "\n";
    }
    private static List<String> jsFunc(Func f) {
        List<String> o = new ArrayList<>();
        o.add("function " + f.name() + "(" + String.join(", ", f.params()) + ") {");
        Set<String> local = new HashSet<>(f.params());
        for (Stmt s : f.body()) o.addAll(jsStmt(s, 1, local));
        o.add("}"); o.add("");
        return o;
    }
    private static List<String> jsStmt(Stmt s, int d, Set<String> declared) {
        String i = ind(d);
        List<String> o = new ArrayList<>();
        if (s instanceof Assign a) {
            if (declared.contains(a.var())) o.add(i + a.var() + " = " + ex(a.e()) + ";");
            else { declared.add(a.var()); o.add(i + "let " + a.var() + " = " + ex(a.e()) + ";"); }
        } else if (s instanceof ArrDecl ad) {
            declared.add(ad.name());
            o.add(i + "let " + ad.name() + " = [" + elems(ad.elems()) + "];");
        } else if (s instanceof IdxSet is) o.add(i + is.name() + "[" + ex(is.index()) + "] = " + ex(is.value()) + ";");
        else if (s instanceof Print pr) o.add(i + "console.log(" + ex(pr.e()) + ");");
        else if (s instanceof Ret r) o.add(i + "return " + ex(r.e()) + ";");
        else if (s instanceof ExprStmt es) o.add(i + ex(es.e()) + ";");
        else if (s instanceof For f) {
            declared.add(f.var());
            o.add(i + "for (let " + f.var() + " = " + ex(f.from()) + "; " + f.var() + " <= " + ex(f.to()) + "; " + f.var() + "++) {");
            for (Stmt b : f.body()) o.addAll(jsStmt(b, d + 1, declared));
            o.add(i + "}");
        } else if (s instanceof While w) {
            o.add(i + "while (" + ex(w.cond()) + ") {");
            for (Stmt b : w.body()) o.addAll(jsStmt(b, d + 1, declared));
            o.add(i + "}");
        } else if (s instanceof If f) {
            o.add(i + "if (" + ex(f.cond()) + ") {");
            for (Stmt b : f.thenB()) o.addAll(jsStmt(b, d + 1, declared));
            if (f.elseB().isEmpty()) o.add(i + "}");
            else {
                o.add(i + "} else {");
                for (Stmt b : f.elseB()) o.addAll(jsStmt(b, d + 1, declared));
                o.add(i + "}");
            }
        }
        return o;
    }

    // ---- C ----
    private static String tc(Type t) {
        return t == Type.DOUBLE ? "double" : t == Type.STRING ? "const char*" : t == Type.VOID ? "void" : "int";
    }

    static String c(Program p, Map<String, Type> types) {
        List<String> out = new ArrayList<>();
        out.add("#include <stdio.h>"); out.add("");
        for (Stmt s : p.items()) if (s instanceof Func f) { out.addAll(cFunc(f, types)); out.add(""); }
        out.add("int main(void) {");
        types.forEach((v, t) -> { if (t != Type.ARRAY) out.add("  " + tc(t) + " " + v + " = " + (t == Type.STRING ? "\"\"" : "0") + ";"); });
        for (Stmt s : p.items()) if (!(s instanceof Func)) out.addAll(cStmt(s, 1, types));
        out.add("  return 0;"); out.add("}");
        return String.join("\n", out) + "\n";
    }
    private static List<String> cFunc(Func f, Map<String, Type> types) {
        List<String> o = new ArrayList<>();
        List<String> ps = new ArrayList<>();
        for (String p : f.params()) ps.add("int " + p);
        Map<String, Type> local = Synth.localTypes(f.params(), f.body());
        Map<String, Type> merged = new java.util.LinkedHashMap<>(types); merged.putAll(local);
        o.add(tc(funcRet(f, types)) + " " + f.name() + "(" + (ps.isEmpty() ? "void" : String.join(", ", ps)) + ") {");
        local.forEach((v, t) -> { if (t != Type.ARRAY) o.add("  " + tc(t) + " " + v + " = " + (t == Type.STRING ? "\"\"" : "0") + ";"); });
        for (Stmt s : f.body()) o.addAll(cStmt(s, 1, merged));
        o.add("}");
        return o;
    }
    private static List<String> cStmt(Stmt s, int d, Map<String, Type> types) {
        String i = ind(d);
        List<String> o = new ArrayList<>();
        if (s instanceof Assign a) o.add(i + a.var() + " = " + ex(a.e()) + ";");
        else if (s instanceof ArrDecl ad) o.add(i + "int " + ad.name() + "[] = {" + elems(ad.elems()) + "};");
        else if (s instanceof IdxSet is) o.add(i + is.name() + "[" + ex(is.index()) + "] = " + ex(is.value()) + ";");
        else if (s instanceof Print pr) {
            Type t = Synth.inferExpr(pr.e(), types);
            String fmt = t == Type.STRING ? "%s" : t == Type.DOUBLE ? "%f" : "%d";
            o.add(i + "printf(\"" + fmt + "\\n\", " + ex(pr.e()) + ");");
        } else if (s instanceof Ret r) o.add(i + "return " + ex(r.e()) + ";");
        else if (s instanceof ExprStmt es) o.add(i + ex(es.e()) + ";");
        else if (s instanceof For f) {
            o.add(i + "for (int " + f.var() + " = " + ex(f.from()) + "; " + f.var() + " <= " + ex(f.to()) + "; " + f.var() + "++) {");
            for (Stmt b : f.body()) o.addAll(cStmt(b, d + 1, types));
            o.add(i + "}");
        } else if (s instanceof While w) {
            o.add(i + "while (" + ex(w.cond()) + ") {");
            for (Stmt b : w.body()) o.addAll(cStmt(b, d + 1, types));
            o.add(i + "}");
        } else if (s instanceof If f) {
            o.add(i + "if (" + ex(f.cond()) + ") {");
            for (Stmt b : f.thenB()) o.addAll(cStmt(b, d + 1, types));
            if (f.elseB().isEmpty()) o.add(i + "}");
            else { o.add(i + "} else {"); for (Stmt b : f.elseB()) o.addAll(cStmt(b, d + 1, types)); o.add(i + "}"); }
        }
        return o;
    }

    // ---- Java ----
    private static String tj(Type t) {
        return t == Type.DOUBLE ? "double" : t == Type.STRING ? "String" : t == Type.VOID ? "void" : "int";
    }

    static String java(Program p, Map<String, Type> types) {
        List<String> out = new ArrayList<>();
        String cls = p.name() == null ? "Program" : p.name();
        out.add("public class " + cls + " {");
        for (Stmt s : p.items()) if (s instanceof Func f) {
            for (String l : javaFunc(f, types)) out.add("  " + l);
            out.add("");
        }
        out.add("  public static void main(String[] args) {");
        types.forEach((v, t) -> { if (t != Type.ARRAY) out.add("    " + tj(t) + " " + v + " = " + (t == Type.STRING ? "\"\"" : "0") + ";"); });
        for (Stmt s : p.items()) if (!(s instanceof Func)) out.addAll(javaStmt(s, 2, types));
        out.add("  }"); out.add("}");
        return String.join("\n", out) + "\n";
    }
    private static List<String> javaFunc(Func f, Map<String, Type> types) {
        List<String> o = new ArrayList<>();
        List<String> ps = new ArrayList<>();
        for (String p : f.params()) ps.add("int " + p);
        Map<String, Type> local = Synth.localTypes(f.params(), f.body());
        Map<String, Type> merged = new java.util.LinkedHashMap<>(types); merged.putAll(local);
        o.add("static " + tj(funcRet(f, types)) + " " + f.name() + "(" + String.join(", ", ps) + ") {");
        local.forEach((v, t) -> { if (t != Type.ARRAY) o.add("  " + tj(t) + " " + v + " = " + (t == Type.STRING ? "\"\"" : "0") + ";"); });
        for (Stmt s : f.body()) o.addAll(javaStmt(s, 1, merged));
        o.add("}");
        return o;
    }
    private static List<String> javaStmt(Stmt s, int d, Map<String, Type> types) {
        String i = ind(d);
        List<String> o = new ArrayList<>();
        if (s instanceof Assign a) o.add(i + a.var() + " = " + ex(a.e()) + ";");
        else if (s instanceof ArrDecl ad) o.add(i + "int[] " + ad.name() + " = {" + elems(ad.elems()) + "};");
        else if (s instanceof IdxSet is) o.add(i + is.name() + "[" + ex(is.index()) + "] = " + ex(is.value()) + ";");
        else if (s instanceof Print pr) o.add(i + "System.out.println(" + ex(pr.e()) + ");");
        else if (s instanceof Ret r) o.add(i + "return " + ex(r.e()) + ";");
        else if (s instanceof ExprStmt es) o.add(i + ex(es.e()) + ";");
        else if (s instanceof For f) {
            o.add(i + "for (int " + f.var() + " = " + ex(f.from()) + "; " + f.var() + " <= " + ex(f.to()) + "; " + f.var() + "++) {");
            for (Stmt b : f.body()) o.addAll(javaStmt(b, d + 1, types));
            o.add(i + "}");
        } else if (s instanceof While w) {
            o.add(i + "while (" + ex(w.cond()) + ") {");
            for (Stmt b : w.body()) o.addAll(javaStmt(b, d + 1, types));
            o.add(i + "}");
        } else if (s instanceof If f) {
            o.add(i + "if (" + ex(f.cond()) + ") {");
            for (Stmt b : f.thenB()) o.addAll(javaStmt(b, d + 1, types));
            if (f.elseB().isEmpty()) o.add(i + "}");
            else { o.add(i + "} else {"); for (Stmt b : f.elseB()) o.addAll(javaStmt(b, d + 1, types)); o.add(i + "}"); }
        }
        return o;
    }

    private static Type funcRet(Func f, Map<String, Type> types) {
        for (Stmt s : f.body()) if (s instanceof Ret r) return Synth.inferExpr(r.e(), types);
        return Type.VOID;
    }

    // ---- Bada (best effort) ----
    static String bada(Program p) {
        List<String> o = new ArrayList<>();
        o.add("# generated Bada program");
        int n = 0;
        for (Stmt s : p.items()) {
            if (s instanceof Assign a) {
                String val = a.e() instanceof Num num ? Synth.num(num) : "0";
                o.add("set " + a.var() + " = " + val);
            } else if (s instanceof Print pr) {
                if (pr.e() instanceof Var v) {
                    o.add("print " + v.name());
                    o.add("Omega::push " + v.name() + " as node" + n++);
                } else {
                    o.add("print " + ex(pr.e()));
                }
            }
        }
        return String.join("\n", o) + "\n";
    }

    private Emit() {}
}
