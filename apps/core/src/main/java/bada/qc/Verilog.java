package bada.qc;

import java.util.List;

/**
 * Verilog — emits the semiconductor (RTL) source code of the pseudo QC's
 * classical control circuit: a NAND MOSFET cell, a NAND-built opcode decoder,
 * and a program-ROM sequencer. Java port of Bada::QC::Verilog.
 */
public final class Verilog {

    public static String generate(List<Isa.Instr> program, int nQubits, String moduleName) {
        int plen = program.size();
        int addrBits = Math.max(1, (int) Math.ceil(Math.log(Math.max(plen, 2)) / Math.log(2)));
        int qh = Math.max(nQubits - 1, 0);
        int ph = Math.max(plen - 1, 0);

        StringBuilder sb = new StringBuilder();
        sb.append("// ").append(moduleName).append(".v — Bada 擬似量子コンピュータ 半導体制御回路 (auto-generated)\n");
        sb.append("// von Neumann stored-program control for ").append(nQubits)
          .append(" qubits, ").append(plen).append(" instructions.\n");
        sb.append("`default_nettype none\n\n");

        sb.append("// ---- MOSFET cell: 2-input CMOS NAND (the one semiconductor primitive) ----\n");
        sb.append("module nand2(input wire a, input wire b, output wire y);\n");
        sb.append("  // pFETs in parallel (pull-up), nFETs in series (pull-down)\n");
        sb.append("  assign y = ~(a & b);\n");
        sb.append("endmodule\n\n");

        sb.append("module inv(input wire a, output wire y);\n");
        sb.append("  nand2 u(.a(a), .b(a), .y(y));   // inverter = NAND with tied inputs\n");
        sb.append("endmodule\n\n");

        sb.append("// ---- one-hot opcode decoder, 4-bit -> 16 lines, from NAND/INV only ----\n");
        sb.append("module opcode_decoder(input wire [3:0] op, output wire [15:0] sel);\n");
        sb.append("  wire [3:0] n;\n");
        sb.append("  inv i0(.a(op[0]), .y(n[0]));\n");
        sb.append("  inv i1(.a(op[1]), .y(n[1]));\n");
        sb.append("  inv i2(.a(op[2]), .y(n[2]));\n");
        sb.append("  inv i3(.a(op[3]), .y(n[3]));\n");
        sb.append("  genvar k;\n");
        sb.append("  generate\n");
        sb.append("    for (k = 0; k < 16; k = k + 1) begin : dec\n");
        sb.append("      wire b0 = k[0] ? op[0] : n[0];\n");
        sb.append("      wire b1 = k[1] ? op[1] : n[1];\n");
        sb.append("      wire b2 = k[2] ? op[2] : n[2];\n");
        sb.append("      wire b3 = k[3] ? op[3] : n[3];\n");
        sb.append("      assign sel[k] = b0 & b1 & b2 & b3;   // AND tree (NAND+INV)\n");
        sb.append("    end\n");
        sb.append("  endgenerate\n");
        sb.append("endmodule\n\n");

        sb.append("// ---- control sequencer: PC walks the program ROM, decoder fires gates ----\n");
        sb.append("module ").append(moduleName).append("(\n");
        sb.append("    input  wire        clk,\n");
        sb.append("    input  wire        rst,\n");
        sb.append("    output reg  [").append(addrBits - 1).append(":0] pc,\n");
        sb.append("    output wire [15:0] gate_sel,   // one-hot gate enable\n");
        sb.append("    output reg  [").append(qh).append(":0]  qubit_a,\n");
        sb.append("    output reg  [").append(qh).append(":0]  qubit_b,\n");
        sb.append("    output reg  signed [31:0] theta_q,     // rotation angle (Q16.16)\n");
        sb.append("    output wire        halt\n");
        sb.append(");\n");
        sb.append("  reg [3:0]  rom_op   [0:").append(ph).append("];\n");
        sb.append("  reg [7:0]  rom_a    [0:").append(ph).append("];\n");
        sb.append("  reg [7:0]  rom_b    [0:").append(ph).append("];\n");
        sb.append("  reg signed [31:0] rom_th [0:").append(ph).append("];\n\n");

        sb.append("  initial begin\n");
        for (int i = 0; i < program.size(); i++) {
            Isa.Instr ins = program.get(i);
            long q = Math.round(ins.theta * 65_536.0);
            sb.append(String.format(
                "    rom_op[%d]=4'd%d; rom_a[%d]=8'd%d; rom_b[%d]=8'd%d; rom_th[%d]=32'sd%d; // %s%n",
                i, ins.op, i, ins.a, i, ins.b, i, q, Isa.mnemonic(ins.op)));
        }
        sb.append("  end\n\n");

        sb.append("  wire [3:0] op = rom_op[pc];\n");
        sb.append("  opcode_decoder dec(.op(op), .sel(gate_sel));\n");
        sb.append("  assign halt = gate_sel[").append(Isa.OPCODES.get("HALT")).append("];   // HALT line\n\n");

        sb.append("  always @(posedge clk or posedge rst) begin\n");
        sb.append("    if (rst) begin\n");
        sb.append("      pc <= 0; qubit_a <= 0; qubit_b <= 0; theta_q <= 0;\n");
        sb.append("    end else if (!halt) begin\n");
        sb.append("      qubit_a <= rom_a[pc][").append(qh).append(":0];\n");
        sb.append("      qubit_b <= rom_b[pc][").append(qh).append(":0];\n");
        sb.append("      theta_q <= rom_th[pc];\n");
        sb.append("      pc      <= pc + 1'b1;\n");
        sb.append("    end\n");
        sb.append("  end\n");
        sb.append("endmodule\n");
        sb.append("`default_nettype wire\n");
        return sb.toString();
    }

    private Verilog() { }
}
