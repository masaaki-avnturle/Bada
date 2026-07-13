package bada.quantum;

import java.util.HashMap;
import java.util.Map;

/**
 * Jones-polynomial correlation of an entangled pair via the Kauffman bracket
 * state sum (a Java port of omega_jones_crypto_pkg/lib/jones_key.c). An
 * entangled pair maps to the Hopf link (non-trivial Jones); a separable pair
 * maps to the unlink (trivial). The polynomial thus certifies the correlation
 * (Jones多項式に基づく相関関係).
 */
public final class Jones {
    // crossing = {e0, e1, e2, e3, sign}
    public static final int[][] HOPF = {
        {0, 1, 2, 3, +1},
        {2, 3, 0, 1, +1}
    };
    public static final int[][] TREFOIL = {
        {0, 1, 5, 4, +1},
        {1, 2, 3, 5, +1},
        {3, 4, 0, 2, +1}
    };

    /** A tiny Laurent polynomial in A: exponent -> coefficient. */
    public static final class Laurent {
        final Map<Integer, Double> terms = new HashMap<>();

        static Laurent mono(double c, int e) {
            Laurent l = new Laurent();
            l.terms.put(e, c);
            return l;
        }

        Laurent add(Laurent o) {
            Laurent r = new Laurent();
            r.terms.putAll(terms);
            for (Map.Entry<Integer, Double> en : o.terms.entrySet())
                r.terms.merge(en.getKey(), en.getValue(), Double::sum);
            r.prune();
            return r;
        }

        Laurent mul(Laurent o) {
            Laurent r = new Laurent();
            for (Map.Entry<Integer, Double> a : terms.entrySet())
                for (Map.Entry<Integer, Double> b : o.terms.entrySet())
                    r.terms.merge(a.getKey() + b.getKey(), a.getValue() * b.getValue(), Double::sum);
            r.prune();
            return r;
        }

        void prune() { terms.entrySet().removeIf(e -> Math.abs(e.getValue()) < 1e-9); }

        public double eval(double a) {
            double s = 0;
            for (Map.Entry<Integer, Double> e : terms.entrySet())
                s += e.getValue() * Math.pow(a, e.getKey());
            return s;
        }

        @Override public String toString() {
            if (terms.isEmpty()) return "0";
            StringBuilder sb = new StringBuilder();
            terms.entrySet().stream()
                 .sorted((x, y) -> y.getKey() - x.getKey())
                 .forEach(e -> sb.append(String.format("%+.3g*A^%d ", e.getValue(), e.getKey())));
            return sb.toString().trim();
        }
    }

    // union-find (port of the C code)
    static int ufFind(int[] parent, int a) {
        while (parent[a] >= 0) a = parent[a];
        return a;
    }

    static void ufUnion(int[] parent, int a, int b) {
        a = ufFind(parent, a);
        b = ufFind(parent, b);
        if (a == b) return;
        if (parent[a] < parent[b]) { parent[a] += parent[b]; parent[b] = a; }
        else { parent[b] += parent[a]; parent[a] = b; }
    }

    /** Kauffman bracket <L> as a Laurent polynomial in A. */
    public static Laurent bracket(int[][] crossings) {
        int n = crossings.length;
        if (n == 0) return Laurent.mono(1.0, 0);
        int maxLbl = 0;
        for (int[] cr : crossings)
            for (int k = 0; k < 4; k++) maxLbl = Math.max(maxLbl, cr[k]);
        int u = maxLbl + 1;
        Laurent d = new Laurent();
        d.terms.put(2, -1.0);
        d.terms.put(-2, -1.0);
        Laurent total = new Laurent();
        for (long s = 0; s < (1L << n); s++) {
            int[] parent = new int[u];
            java.util.Arrays.fill(parent, -1);
            int aCnt = 0, bCnt = 0;
            for (int i = 0; i < n; i++) {
                int[] cr = crossings[i];
                if (((s >> i) & 1) == 0) {
                    ufUnion(parent, cr[0], cr[1]); ufUnion(parent, cr[2], cr[3]); aCnt++;
                } else {
                    ufUnion(parent, cr[1], cr[2]); ufUnion(parent, cr[3], cr[0]); bCnt++;
                }
            }
            java.util.Set<Integer> roots = new java.util.HashSet<>();
            for (int l = 0; l < u; l++) roots.add(ufFind(parent, l));
            int loops = roots.size();
            Laurent weight = Laurent.mono(1.0, aCnt - bCnt);
            Laurent dpow = Laurent.mono(1.0, 0);
            for (int t = 0; t < loops - 1; t++) dpow = dpow.mul(d);
            total = total.add(weight.mul(dpow));
        }
        return total;
    }

    public static int writhe(int[][] crossings) {
        int w = 0;
        for (int[] cr : crossings) w += cr[4];
        return w;
    }

    /** Jones f_L = (-A^3)^(-writhe) * <L>, as a Laurent polynomial in A. */
    public static Laurent polynomial(int[][] crossings) {
        int w = writhe(crossings);
        Laurent norm = Laurent.mono(Math.pow(-1.0, w), -3 * w);
        return norm.mul(bracket(crossings));
    }

    /** Numeric Jones value at variable t (A = t^{-1/4}). */
    public static double jonesValue(int[][] crossings, double t) {
        double a = Math.pow(t, -0.25);
        return polynomial(crossings).eval(a);
    }

    /** Correlation strength in [0,1]; entangled/Hopf large, unlink ~0. */
    public static double correlation(int[][] crossings, double t) {
        double v = jonesValue(crossings, t);
        double d = Math.abs(v - 1.0);
        return d / (1.0 + d);
    }

    public static double correlation(int[][] crossings) { return correlation(crossings, Math.E); }
}
