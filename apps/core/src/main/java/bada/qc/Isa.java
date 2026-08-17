package bada.qc;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * ISA — BadaQASM instruction set and its von-Neumann encoding into disk words.
 * Each instruction is a 4-word record [opcode, a, b, theta]. Java port of
 * Bada::QC::ISA.
 */
public final class Isa {
    public static final int RECORD_WORDS = 4;
    public static final int OPCODE_BITS = 4;

    public static final Map<String, Integer> OPCODES = new LinkedHashMap<>();
    public static final Map<Integer, String> NAMES = new LinkedHashMap<>();
    static {
        String[] mn = {"NOP", "H", "X", "Y", "Z", "S", "T", "CX", "RX", "RZ", "MEASURE", "HALT"};
        for (int i = 0; i < mn.length; i++) {
            OPCODES.put(mn[i], i);
            NAMES.put(i, mn[i]);
        }
    }

    /** An assembled instruction record. */
    public static final class Instr {
        public final int op, a, b;
        public final double theta;
        public Instr(int op, int a, int b, double theta) {
            this.op = op; this.a = a; this.b = b; this.theta = theta;
        }
    }

    /** Parse BadaQASM source into records. */
    public static List<Instr> assemble(String source) {
        List<Instr> program = new ArrayList<>();
        for (String raw : source.split("\n")) {
            String line = raw.replaceAll("#.*$", "").trim();
            if (line.isEmpty()) continue;
            String[] tok = line.split("\\s+");
            String mnem = tok[0].toUpperCase();
            Integer op = OPCODES.get(mnem);
            if (op == null) throw new IllegalArgumentException("unknown instruction: " + mnem);
            int a = tok.length > 1 ? (int) parseNum(tok[1]) : 0;
            int b = tok.length > 2 ? (int) parseNum(tok[2]) : 0;
            double theta = 0.0;
            if (mnem.equals("RX") || mnem.equals("RZ")) {
                a = tok.length > 1 ? (int) parseNum(tok[1]) : 0;
                theta = tok.length > 2 ? parseNum(tok[2]) : 0.0;
                b = 0;
            }
            program.add(new Instr(op, a, b, theta));
        }
        return program;
    }

    private static double parseNum(String s) {
        try { return Double.parseDouble(s); } catch (NumberFormatException e) { return 0.0; }
    }

    public static String mnemonic(int opcode) {
        return NAMES.getOrDefault(opcode, "?");
    }

    private Isa() { }
}
