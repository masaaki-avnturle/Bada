package bada.mind;

/**
 * Image-processing Transformer (ViT-style) on the manifold-gauge Encoder. Cuts a
 * grid into patches, mixes them, and reconstructs the "mental image". Java port
 * of Bada::Transformer::Vision.
 */
public final class Vision {
    private final Encoder encoder;
    private final int grid, patch, perSide, patchDim;
    private final double[][] projIn;
    private final double[][] projOut;

    public Vision(Encoder encoder, int grid, int patch, long seed) {
        this.encoder = encoder;
        this.grid = grid;
        this.patch = patch;
        this.perSide = grid / patch;
        this.patchDim = patch * patch;
        Tensor.PRNG rng = new Tensor.PRNG(seed);
        this.projIn = Tensor.randmat(patchDim, encoder.dModel(), rng, 0.5);
        this.projOut = Tensor.randmat(encoder.dModel(), 1, rng, 0.5);
    }

    public double[][] process(double[][] image) {
        double[][] patches = patchify(image);
        double[][] tokens = Tensor.matmul(patches, projIn);
        double[][] hidden = encoder.run(tokens);
        double[][] proj = Tensor.matmul(hidden, projOut);
        double[] raw = new double[proj.length];
        for (int i = 0; i < proj.length; i++) raw[i] = proj[i][0];
        // z-score across patches so the rendered image always keeps contrast
        double mean = 0.0;
        for (double v : raw) mean += v;
        mean /= raw.length;
        double var = 0.0;
        for (double v : raw) var += (v - mean) * (v - mean);
        double std = Math.sqrt(var / raw.length) + 1e-9;
        double[] outs = new double[raw.length];
        for (int i = 0; i < raw.length; i++) outs[i] = sigmoid((raw[i] - mean) / std);
        return unpatch(outs);
    }

    public static String ascii(double[][] gridVals) {
        String shades = " .:-=+*#%@";
        StringBuilder sb = new StringBuilder();
        for (int y = 0; y < gridVals.length; y++) {
            for (double v : gridVals[y]) {
                int idx = (int) Math.round(Math.max(0.0, Math.min(1.0, v)) * (shades.length() - 1));
                sb.append(shades.charAt(idx));
            }
            if (y < gridVals.length - 1) sb.append('\n');
        }
        return sb.toString();
    }

    private double[][] patchify(double[][] image) {
        double[][] rows = new double[perSide * perSide][patchDim];
        int r = 0;
        for (int py = 0; py < perSide; py++) {
            for (int px = 0; px < perSide; px++) {
                int c = 0;
                for (int dy = 0; dy < patch; dy++)
                    for (int dx = 0; dx < patch; dx++)
                        rows[r][c++] = image[py * patch + dy][px * patch + dx];
                r++;
            }
        }
        return rows;
    }

    private double[][] unpatch(double[] outs) {
        double[][] out = new double[grid][grid];
        int idx = 0;
        for (int py = 0; py < perSide; py++) {
            for (int px = 0; px < perSide; px++) {
                double val = outs[idx++];
                for (int dy = 0; dy < patch; dy++)
                    for (int dx = 0; dx < patch; dx++)
                        out[py * patch + dy][px * patch + dx] = val;
            }
        }
        return out;
    }

    private static double sigmoid(double x) { return 1.0 / (1.0 + Math.exp(-x)); }
}
