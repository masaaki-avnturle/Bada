package bada.mind;

/**
 * Minimal pure-Java tensor helpers (matrices as double[][]) and a seeded
 * xorshift64 PRNG. Java port of Bada::Transformer::Tensor.
 */
public final class Tensor {

    public static double[][] matmul(double[][] a, double[][] b) {
        int m = a.length, k = b.length, n = b[0].length;
        double[][] out = new double[m][n];
        for (int i = 0; i < m; i++) {
            for (int t = 0; t < k; t++) {
                double av = a[i][t];
                if (av == 0.0) continue;
                double[] bt = b[t];
                double[] oi = out[i];
                for (int j = 0; j < n; j++) oi[j] += av * bt[j];
            }
        }
        return out;
    }

    public static double[][] transpose(double[][] a) {
        int r = a.length, c = a[0].length;
        double[][] t = new double[c][r];
        for (int i = 0; i < r; i++) for (int j = 0; j < c; j++) t[j][i] = a[i][j];
        return t;
    }

    public static double[][] add(double[][] a, double[][] b) {
        double[][] o = new double[a.length][a[0].length];
        for (int i = 0; i < a.length; i++)
            for (int j = 0; j < a[0].length; j++) o[i][j] = a[i][j] + b[i][j];
        return o;
    }

    public static double[][] addBias(double[][] a, double[] bias) {
        double[][] o = new double[a.length][a[0].length];
        for (int i = 0; i < a.length; i++)
            for (int j = 0; j < a[0].length; j++) o[i][j] = a[i][j] + bias[j];
        return o;
    }

    public static double[] softmax(double[] v) {
        double mx = Double.NEGATIVE_INFINITY;
        for (double x : v) mx = Math.max(mx, x);
        double sum = 0.0;
        double[] e = new double[v.length];
        for (int i = 0; i < v.length; i++) { e[i] = Math.exp(v[i] - mx); sum += e[i]; }
        if (sum == 0.0) sum = 1e-12;
        for (int i = 0; i < e.length; i++) e[i] /= sum;
        return e;
    }

    public static double[] layernorm(double[] v) {
        double mean = 0.0;
        for (double x : v) mean += x;
        mean /= v.length;
        double var = 0.0;
        for (double x : v) var += (x - mean) * (x - mean);
        var /= v.length;
        double inv = 1.0 / Math.sqrt(var + 1e-5);
        double[] o = new double[v.length];
        for (int i = 0; i < v.length; i++) o[i] = (v[i] - mean) * inv;
        return o;
    }

    public static double gelu(double x) {
        return 0.5 * x * (1.0 + Math.tanh(Math.sqrt(2.0 / Math.PI) * (x + 0.044715 * x * x * x)));
    }

    public static double[][] geluMat(double[][] a) {
        double[][] o = new double[a.length][a[0].length];
        for (int i = 0; i < a.length; i++)
            for (int j = 0; j < a[0].length; j++) o[i][j] = gelu(a[i][j]);
        return o;
    }

    public static double cosine(double[] u, double[] v) {
        double dot = 0, nu = 0, nv = 0;
        for (int i = 0; i < u.length; i++) { dot += u[i] * v[i]; nu += u[i] * u[i]; nv += v[i] * v[i]; }
        double d = Math.sqrt(nu) * Math.sqrt(nv);
        return d == 0 ? 0.0 : dot / d;
    }

    public static double[][] randmat(int rows, int cols, PRNG rng, double scale) {
        double[][] m = new double[rows][cols];
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) m[i][j] = (rng.nextFloat() * 2.0 - 1.0) * scale;
        return m;
    }

    /** Deterministic xorshift64 PRNG. */
    public static final class PRNG {
        private long s;
        public PRNG(long seed) {
            s = seed;
            if (s == 0) s = 0x9E3779B97F4A7C15L;
        }
        public long nextU64() {
            long x = s;
            x ^= (x << 13);
            x ^= (x >>> 7);
            x ^= (x << 17);
            s = x;
            return x;
        }
        public double nextFloat() {
            return (nextU64() >>> 11) / (double) (1L << 53);
        }
    }

    private Tensor() { }
}
