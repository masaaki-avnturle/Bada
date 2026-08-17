package bada.qc;

import java.io.File;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Map;

/**
 * PseudoQC — the whole von-Neumann pseudo quantum computer as one facade, the
 * Java twin of Bada::QC::Machine. State + program live on a real disk file.
 *
 *   PseudoQC m = PseudoQC.bell();
 *   System.out.println(m.report());   // monitor projection + statevector
 *   System.out.println(m.verilog());  // semiconductor source code
 *   m.close();
 */
public final class PseudoQC implements AutoCloseable {
    private final int n;
    private final long seed;
    private List<Isa.Instr> program;
    private DiskMemory mem;
    private Cpu cpu;

    public PseudoQC(int nQubits, long seed) {
        this.n = nQubits;
        this.seed = seed;
    }

    public PseudoQC(int nQubits) { this(nQubits, 0xBADAL); }

    public PseudoQC load(String source) {
        program = Isa.assemble(source);
        long words = Cpu.HEADER + (long) program.size() * Isa.RECORD_WORDS + 2L * (1L << n);
        try {
            File f = File.createTempFile("bada_qc_", ".bin");
            f.deleteOnExit();
            mem = new DiskMemory(f.getAbsolutePath(), words);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        cpu = new Cpu(mem, n, program.size(), seed);
        cpu.load(program);
        return this;
    }

    public PseudoQC run() {
        cpu.run();
        return this;
    }

    public double[] probabilities() { return cpu.probabilities(); }
    public Map<Integer, Integer> classicalBits() { return cpu.classical(); }
    public long diskBytes() { return mem == null ? 0 : mem.byteSize(); }

    public String monitor() {
        return Monitor.project(program, n, diskBytes());
    }

    public String verilog() {
        return Verilog.generate(program, n, "bada_qc_control");
    }

    public String report() {
        StringBuilder sb = new StringBuilder();
        sb.append(monitor()).append("\n\n");
        sb.append("  program (BadaQASM, stored on disk):\n");
        for (int i = 0; i < program.size(); i++) {
            Isa.Instr ins = program.get(i);
            String name = Isa.NAMES.get(ins.op);
            String args;
            if ("CX".equals(name)) args = ins.a + "," + ins.b;
            else if ("RX".equals(name) || "RZ".equals(name)) args = ins.a + "," + String.format("%.4f", ins.theta);
            else args = String.valueOf(ins.a);
            sb.append(String.format("    %02d: %-7s %s%n", i, Isa.mnemonic(ins.op), args));
        }
        sb.append("\n  state vector (read back from disk memory):\n");
        double[] p = probabilities();
        for (int i = 0; i < p.length; i++) {
            if (p[i] < 1e-9) continue;
            String bits = pad(Integer.toBinaryString(i), n);
            sb.append(String.format("    |%s> : P = %.4f%n", bits, p[i]));
        }
        if (!classicalBits().isEmpty()) {
            sb.append("\n  classical register (measurements): ").append(classicalBits()).append("\n");
        }
        sb.append(String.format("%n  disk memory image: %d bytes, %d instructions, %d amplitudes",
                diskBytes(), program.size(), 1 << n));
        return sb.toString();
    }

    private static String pad(String s, int width) {
        StringBuilder z = new StringBuilder();
        for (int i = s.length(); i < width; i++) z.append('0');
        return z + s;
    }

    @Override
    public void close() {
        if (mem != null) mem.close();
    }

    public static PseudoQC bell() {
        return new PseudoQC(2).load("H 0\nCX 0 1\nHALT\n").run();
    }

    public static PseudoQC ghz() {
        return new PseudoQC(3).load("H 0\nCX 0 1\nCX 1 2\nHALT\n").run();
    }
}
