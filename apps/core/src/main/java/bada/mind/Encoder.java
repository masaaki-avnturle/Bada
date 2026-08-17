package bada.mind;

import java.util.ArrayList;
import java.util.List;

/**
 * From-scratch Transformer encoder gauged by the gamma-function global partial
 * integral manifold (∬ 1/(x log x)^2 as an attention distance kernel). Java port
 * of Bada::Transformer::Encoder.
 */
public final class Encoder {
    private final int vocab, dModel, nHeads, dHead, nBlocks, dFf;
    private final double hbarEff;
    private final double[][] embed;
    private final List<Block> blocks = new ArrayList<>();
    private double[][] lastAttention;

    private static final class Block {
        double[][] wq, wk, wv, wo, w1, w2;
        double[] b1, b2;
    }

    public Encoder(int vocab, int dModel, int nHeads, int nBlocks, int dFf, long seed) {
        this.vocab = vocab;
        this.dModel = dModel;
        this.nHeads = nHeads;
        this.dHead = dModel / nHeads;
        this.nBlocks = nBlocks;
        this.dFf = dFf;
        Tensor.PRNG rng = new Tensor.PRNG(seed);
        this.embed = Tensor.randmat(vocab, dModel, rng, 0.6);
        for (int i = 0; i < nBlocks; i++) {
            Block b = new Block();
            b.wq = Tensor.randmat(dModel, dModel, rng, 0.5);
            b.wk = Tensor.randmat(dModel, dModel, rng, 0.5);
            b.wv = Tensor.randmat(dModel, dModel, rng, 0.5);
            b.wo = Tensor.randmat(dModel, dModel, rng, 0.5);
            b.w1 = Tensor.randmat(dModel, dFf, rng, 0.5);
            b.b1 = new double[dFf];
            b.w2 = Tensor.randmat(dFf, dModel, rng, 0.5);
            b.b2 = new double[dModel];
            blocks.add(b);
        }
        this.hbarEff = 1.0 / Math.sqrt(dHead);
    }

    public Encoder(int vocab, long seed) { this(vocab, 24, 4, 2, 48, seed); }

    public int dModel() { return dModel; }
    public double[][] embedding() { return embed; }
    public double[][] lastAttention() { return lastAttention; }

    public double[][] embed(int[] ids) {
        double[][] x = new double[ids.length][];
        for (int i = 0; i < ids.length; i++) x[i] = embed[Math.floorMod(ids[i], vocab)].clone();
        return x;
    }

    private double[][] positional(int n) {
        double[][] pe = new double[n][dModel];
        for (int pos = 0; pos < n; pos++) {
            for (int i = 0; i < dModel; i++) {
                double angle = pos / Math.pow(10_000.0, (2.0 * (i / 2)) / dModel);
                pe[pos][i] = (i % 2 == 0) ? Math.sin(angle) : Math.cos(angle);
            }
        }
        return pe;
    }

    private static double manifoldElement(double x) {
        if (x <= 1.0) return 1.0;
        double xl = x * Math.log(x);
        if (Math.abs(xl) < 1e-9) return 1.0;
        return 1.0 / (xl * xl);
    }

    private double[][] gaugeBias(int n) {
        double[][] g = new double[n][n];
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                g[i][j] = Math.log(manifoldElement(Math.abs(i - j) + 2) + 1e-12);
        return g;
    }

    public double[][] forward(int[] ids) {
        return run(Tensor.add(embed(ids), positional(ids.length)));
    }

    public double[][] run(double[][] x) {
        double[][] bias = gaugeBias(x.length);
        lastAttention = null;
        for (Block blk : blocks) {
            double[][] attn = attention(x, blk, bias);
            double[][] x1 = new double[x.length][];
            for (int i = 0; i < x.length; i++) {
                double[] sum = new double[dModel];
                for (int k = 0; k < dModel; k++) sum[k] = x[i][k] + attn[i][k];
                x1[i] = Tensor.layernorm(sum);
            }
            double[][] ff = ffn(x1, blk);
            double[][] x2 = new double[x1.length][];
            for (int i = 0; i < x1.length; i++) {
                double[] sum = new double[dModel];
                for (int k = 0; k < dModel; k++) sum[k] = x1[i][k] + ff[i][k];
                x2[i] = Tensor.layernorm(sum);
            }
            x = x2;
        }
        return x;
    }

    public double[][] logits(double[][] hidden) {
        return Tensor.matmul(hidden, Tensor.transpose(embed));
    }

    private double[][] attention(double[][] x, Block blk, double[][] bias) {
        int n = x.length;
        double[][] q = Tensor.matmul(x, blk.wq);
        double[][] k = Tensor.matmul(x, blk.wk);
        double[][] v = Tensor.matmul(x, blk.wv);
        double[][] context = new double[n][dModel];
        double[][] avg = new double[n][n];
        for (int h = 0; h < nHeads; h++) {
            int off = h * dHead;
            for (int i = 0; i < n; i++) {
                double[] scores = new double[n];
                for (int j = 0; j < n; j++) {
                    double dot = 0;
                    for (int d = 0; d < dHead; d++) dot += q[i][off + d] * k[j][off + d];
                    scores[j] = dot * hbarEff + bias[i][j];
                }
                double[] w = Tensor.softmax(scores);
                for (int j = 0; j < n; j++) {
                    avg[i][j] += w[j] / nHeads;
                    for (int d = 0; d < dHead; d++) context[i][off + d] += w[j] * v[j][off + d];
                }
            }
        }
        lastAttention = avg;
        return Tensor.matmul(context, blk.wo);
    }

    private double[][] ffn(double[][] x, Block blk) {
        double[][] h = Tensor.geluMat(Tensor.addBias(Tensor.matmul(x, blk.w1), blk.b1));
        return Tensor.addBias(Tensor.matmul(h, blk.w2), blk.b2);
    }
}
