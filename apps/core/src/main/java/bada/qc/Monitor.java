package bada.qc;

import java.util.List;

/**
 * Monitor — projects the pseudo QC control circuit onto the screen: the
 * von-Neumann datapath schematic plus an ASCII quantum-circuit timeline. Java
 * port of Bada::QC::Monitor.
 */
public final class Monitor {
    public static final int CELL = 5;

    public static String project(List<Isa.Instr> program, int nQubits, long diskBytes) {
        return datapath(diskBytes) + "\n\n" + circuit(program, nQubits);
    }

    public static String datapath(long diskBytes) {
        String size = diskBytes > 0 ? diskBytes + " bytes on HDD" : "on HDD";
        String pad = String.format("%-16s", size);
        return "===== MONITOR :: 擬似量子コンピュータ 制御回路 (von Neumann) =====\n\n"
            + "    +------+   addr    +==================+   instr   +------------------+\n"
            + "    |  PC  | --------> |   DISK  MEMORY   | --------> |  SEMICONDUCTOR   |\n"
            + "    +------+           |  von Neumann:    |           |  DECODER         |\n"
            + "       ^               |  program + state |           |  (NAND / MOSFET  |\n"
            + "       | pc+1          |  vector share    |           |   simulation)    |\n"
            + "       |               |  one address     |           +---------+--------+\n"
            + "       |               |  space           |                     | ctrl\n"
            + "       |               |  (" + pad + ")|                     v\n"
            + "       |               +========+=========+           +------------------+\n"
            + "       |                        ^  read/write          |   GATE  UNIT     |\n"
            + "       |                        |  amplitudes          |  H X Y Z S T     |\n"
            + "       +------------------------+----------------------|  CX RX RZ MEAS   |\n"
            + "                                                       +------------------+";
    }

    public static String circuit(List<Isa.Instr> program, int nQubits) {
        StringBuilder[] rows = new StringBuilder[nQubits];
        for (int q = 0; q < nQubits; q++) rows[q] = new StringBuilder();
        for (Isa.Instr ins : program) {
            String name = Isa.NAMES.get(ins.op);
            if (name == null || name.equals("HALT") || name.equals("NOP")) continue;
            for (int q = 0; q < nQubits; q++) rows[q].append(cellFor(name, q, ins.a, ins.b));
        }
        StringBuilder sb = new StringBuilder("  quantum circuit (time ->):\n");
        for (int q = 0; q < nQubits; q++) {
            String body = rows[q].length() == 0 ? repeat("─", CELL) : rows[q].toString();
            sb.append(String.format("q%d ─%s─%n", q, body));
        }
        return sb.toString().stripTrailing();
    }

    private static String cellFor(String name, int q, int a, int b) {
        String token;
        if (name.equals("CX")) {
            int lo = Math.min(a, b), hi = Math.max(a, b);
            if (q == a) token = "●";
            else if (q == b) token = "⊕";
            else if (q > lo && q < hi) token = "│";
            else token = "─";
        } else if (q == a) {
            token = "[" + name.charAt(0) + "]";
        } else {
            token = "─";
        }
        return center(token, CELL, "─");
    }

    private static String center(String s, int width, String fill) {
        int len = s.codePointCount(0, s.length());
        if (len >= width) return s;
        int total = width - len;
        int left = total / 2;
        int right = total - left;
        return repeat(fill, left) + s + repeat(fill, right);
    }

    private static String repeat(String s, int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) sb.append(s);
        return sb.toString();
    }

    private Monitor() { }
}
