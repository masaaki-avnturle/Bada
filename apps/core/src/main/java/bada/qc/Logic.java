package bada.qc;

/**
 * Logic — the semiconductor electronic-circuit simulation driving the classical
 * control: CMOS/MOSFET NAND, the gates derived from it, and a one-hot opcode
 * decoder used by the CPU. Java port of Bada::QC::Logic.
 */
public final class Logic {
    public static final double VDD = 1.0;
    public static final double VTH = 0.5;

    public static boolean high(double v) { return v >= VTH; }
    public static double level(int bit) { return bit == 1 ? VDD : 0.0; }

    public static double nand(double a, double b) {
        return (high(a) && high(b)) ? 0.0 : VDD;
    }

    public static double inv(double a) { return nand(a, a); }
    public static double and(double a, double b) { return inv(nand(a, b)); }
    public static double or(double a, double b) { return nand(inv(a), inv(b)); }

    public static double xor(double a, double b) {
        double n = nand(a, b);
        return nand(nand(a, n), nand(b, n));
    }

    public static double bitLevel(int value, int k) {
        return level((value >> k) & 1);
    }

    /** One-hot decoder from NAND/INV; returns 2^bits levels, exactly one high. */
    public static double[] decode(int value, int bits) {
        double[] lines = new double[bits];
        for (int k = 0; k < bits; k++) lines[k] = bitLevel(value, k);
        double[] out = new double[1 << bits];
        for (int sel = 0; sel < (1 << bits); sel++) {
            double acc = VDD;
            for (int k = 0; k < bits; k++) {
                int want = (sel >> k) & 1;
                double line = want == 1 ? lines[k] : inv(lines[k]);
                acc = and(acc, line);
            }
            out[sel] = acc;
        }
        return out;
    }

    public static int decodeIndex(int value, int bits) {
        double[] d = decode(value, bits);
        for (int i = 0; i < d.length; i++) if (high(d[i])) return i;
        return 0;
    }

    private Logic() { }
}
