package bada.qc;

import bada.quantum.Complex;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.TreeMap;

/**
 * CPU — the von-Neumann control unit: fetch → (semiconductor) decode → execute
 * over a stored program, with all state on disk. Java port of Bada::QC::CPU.
 */
public final class Cpu {
    public static final int HEADER = 4;
    private static final double SQRT1_2 = 1.0 / Math.sqrt(2.0);

    private final DiskMemory mem;
    private final int n;
    private final long dim;
    private final int programLen;
    private final int progBase;
    private final long dataBase;
    private final Random rng;
    private final Map<Integer, Integer> classical = new TreeMap<>();
    private int steps = 0;

    public Cpu(DiskMemory mem, int n, int programLen, long seed) {
        this.mem = mem;
        this.n = n;
        this.dim = 1L << n;
        this.programLen = programLen;
        this.progBase = HEADER;
        this.dataBase = HEADER + (long) programLen * Isa.RECORD_WORDS;
        this.rng = new Random(seed);
    }

    public long dataBase() { return dataBase; }
    public int steps() { return steps; }
    public Map<Integer, Integer> classical() { return classical; }

    public void load(List<Isa.Instr> program) {
        mem.write(0, n);
        mem.write(1, programLen);
        mem.write(2, 0);
        mem.write(3, 0);
        for (int i = 0; i < program.size(); i++) {
            Isa.Instr ins = program.get(i);
            long base = progBase + (long) i * Isa.RECORD_WORDS;
            mem.write(base, ins.op);
            mem.write(base + 1, ins.a);
            mem.write(base + 2, ins.b);
            mem.write(base + 3, ins.theta);
        }
        resetState();
        mem.flush();
    }

    public void resetState() {
        for (long i = 0; i < dim; i++) mem.writeAmp(dataBase, i, new Complex(0, 0));
        mem.writeAmp(dataBase, 0, new Complex(1, 0));
    }

    public List<int[]> run() {
        List<int[]> trace = new ArrayList<>();
        while (true) {
            int pc = (int) mem.read(2);
            if (pc >= programLen) break;
            long base = progBase + (long) pc * Isa.RECORD_WORDS;
            int op = (int) mem.read(base);
            int a = (int) mem.read(base + 1);
            int b = (int) mem.read(base + 2);
            double theta = mem.read(base + 3);
            int decoded = Logic.decodeIndex(op, Isa.OPCODE_BITS); // semiconductor decode
            trace.add(new int[]{pc, decoded, a, b});
            if (decoded == Isa.OPCODES.get("HALT")) break;
            execute(decoded, a, b, theta);
            steps++;
            mem.write(2, pc + 1);
        }
        mem.flush();
        return trace;
    }

    public double[] probabilities() {
        double[] p = new double[(int) dim];
        for (int i = 0; i < dim; i++) p[i] = mem.readAmp(dataBase, i).abs2();
        return p;
    }

    private void execute(int op, int a, int b, double theta) {
        switch (Isa.NAMES.get(op)) {
            case "NOP" -> { }
            case "H" -> apply1(a, new Complex[][]{
                    {c(SQRT1_2), c(SQRT1_2)}, {c(SQRT1_2), c(-SQRT1_2)}});
            case "X" -> apply1(a, new Complex[][]{{c(0), c(1)}, {c(1), c(0)}});
            case "Y" -> apply1(a, new Complex[][]{{c(0), new Complex(0, -1)}, {new Complex(0, 1), c(0)}});
            case "Z" -> apply1(a, new Complex[][]{{c(1), c(0)}, {c(0), c(-1)}});
            case "S" -> apply1(a, new Complex[][]{{c(1), c(0)}, {c(0), new Complex(0, 1)}});
            case "T" -> apply1(a, new Complex[][]{{c(1), c(0)}, {c(0), expi(Math.PI / 4)}});
            case "RX" -> apply1(a, rx(theta));
            case "RZ" -> apply1(a, rz(theta));
            case "CX" -> applyCx(a, b);
            case "MEASURE" -> measure(a);
            default -> { }
        }
    }

    private static Complex c(double r) { return new Complex(r, 0); }
    private static Complex expi(double t) { return new Complex(Math.cos(t), Math.sin(t)); }

    private Complex[][] rx(double theta) {
        Complex cc = c(Math.cos(theta / 2.0));
        Complex ss = new Complex(0, -Math.sin(theta / 2.0));
        return new Complex[][]{{cc, ss}, {ss, cc}};
    }

    private Complex[][] rz(double theta) {
        return new Complex[][]{{expi(-theta / 2.0), c(0)}, {c(0), expi(theta / 2.0)}};
    }

    private void apply1(int q, Complex[][] m) {
        long step = 1L << q;
        for (long i = 0; i < dim; i++) {
            if ((i & step) != 0) continue;
            long j = i | step;
            Complex a0 = mem.readAmp(dataBase, i);
            Complex a1 = mem.readAmp(dataBase, j);
            mem.writeAmp(dataBase, i, m[0][0].mul(a0).add(m[0][1].mul(a1)));
            mem.writeAmp(dataBase, j, m[1][0].mul(a0).add(m[1][1].mul(a1)));
        }
    }

    private void applyCx(int control, int target) {
        long cbit = 1L << control;
        long tbit = 1L << target;
        for (long i = 0; i < dim; i++) {
            if ((i & cbit) == 0 || (i & tbit) != 0) continue;
            long j = i | tbit;
            Complex a0 = mem.readAmp(dataBase, i);
            Complex a1 = mem.readAmp(dataBase, j);
            mem.writeAmp(dataBase, i, a1);
            mem.writeAmp(dataBase, j, a0);
        }
    }

    private void measure(int q) {
        long bit = 1L << q;
        double p1 = 0.0;
        for (long i = 0; i < dim; i++) if ((i & bit) != 0) p1 += mem.readAmp(dataBase, i).abs2();
        int outcome = rng.nextDouble() < p1 ? 1 : 0;
        double norm = Math.sqrt(outcome == 1 ? p1 : (1.0 - p1));
        if (norm < 1e-12) norm = 1.0;
        for (long i = 0; i < dim; i++) {
            boolean keep = (((i & bit) != 0) ? 1 : 0) == outcome;
            Complex amp = keep ? mem.readAmp(dataBase, i).scale(1.0 / norm) : new Complex(0, 0);
            mem.writeAmp(dataBase, i, amp);
        }
        classical.put(q, outcome);
    }
}
