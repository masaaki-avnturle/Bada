# frozen_string_literal: true

require_relative "isa"

module Bada
  module QC
    # Verilog — generates the *semiconductor source code* of the pseudo quantum
    # computer's classical control circuit (量子コンピューターの半導体のソース
    # コード). It emits synthesizable Verilog: a NAND primitive (the MOSFET
    # cell), a one-hot opcode decoder built from it, and a control sequencer whose
    # ROM holds the assembled program. This is the RTL that, on a real chip,
    # drives the qubit gate lines.
    module Verilog
      module_function

      def generate(program, n_qubits, module_name: "bada_qc_control")
        plen = program.length
        addr_bits = [1, Math.log2([plen, 2].max).ceil].max
        <<~V
          // #{module_name}.v — Bada 擬似量子コンピュータ 半導体制御回路 (auto-generated)
          // von Neumann stored-program control for #{n_qubits} qubits, #{plen} instructions.
          `default_nettype none

          // ---- MOSFET cell: 2-input CMOS NAND (the one semiconductor primitive) ----
          module nand2(input wire a, input wire b, output wire y);
            // pFETs in parallel (pull-up), nFETs in series (pull-down)
            assign y = ~(a & b);
          endmodule

          module inv(input wire a, output wire y);
            nand2 u(.a(a), .b(a), .y(y));   // inverter = NAND with tied inputs
          endmodule

          // ---- one-hot opcode decoder, 4-bit -> 16 lines, from NAND/INV only ----
          module opcode_decoder(input wire [3:0] op, output wire [15:0] sel);
            wire [3:0] n;
            inv i0(.a(op[0]), .y(n[0]));
            inv i1(.a(op[1]), .y(n[1]));
            inv i2(.a(op[2]), .y(n[2]));
            inv i3(.a(op[3]), .y(n[3]));
            genvar k;
            generate
              for (k = 0; k < 16; k = k + 1) begin : dec
                wire b0 = k[0] ? op[0] : n[0];
                wire b1 = k[1] ? op[1] : n[1];
                wire b2 = k[2] ? op[2] : n[2];
                wire b3 = k[3] ? op[3] : n[3];
                assign sel[k] = b0 & b1 & b2 & b3;   // AND tree (NAND+INV)
              end
            endgenerate
          endmodule

          // ---- control sequencer: PC walks the program ROM, decoder fires gates ----
          module #{module_name}(
              input  wire        clk,
              input  wire        rst,
              output reg  [#{addr_bits - 1}:0] pc,
              output wire [15:0] gate_sel,   // one-hot gate enable
              output reg  [#{[n_qubits - 1, 0].max}:0]  qubit_a,    // primary qubit line
              output reg  [#{[n_qubits - 1, 0].max}:0]  qubit_b,    // secondary (CX target)
              output reg  signed [31:0] theta_q,     // rotation angle (Q16.16)
              output wire        halt
          );
            // Program ROM (von Neumann: instruction memory image)
            reg [3:0]  rom_op   [0:#{[plen - 1, 0].max}];
            reg [7:0]  rom_a    [0:#{[plen - 1, 0].max}];
            reg [7:0]  rom_b    [0:#{[plen - 1, 0].max}];
            reg signed [31:0] rom_th [0:#{[plen - 1, 0].max}];

            initial begin
          #{rom_init(program)}
            end

            wire [3:0] op = rom_op[pc];
            opcode_decoder dec(.op(op), .sel(gate_sel));
            assign halt = gate_sel[#{ISA::OPCODES['HALT']}];   // HALT line

            always @(posedge clk or posedge rst) begin
              if (rst) begin
                pc <= 0; qubit_a <= 0; qubit_b <= 0; theta_q <= 0;
              end else if (!halt) begin
                qubit_a <= rom_a[pc][#{[n_qubits - 1, 0].max}:0];
                qubit_b <= rom_b[pc][#{[n_qubits - 1, 0].max}:0];
                theta_q <= rom_th[pc];
                pc      <= pc + 1'b1;
              end
            end
          endmodule
          `default_nettype wire
        V
      end

      def rom_init(program)
        program.each_with_index.map do |(op, a, b, theta), i|
          q = (theta * 65_536.0).round # Q16.16 fixed-point angle
          format("    rom_op[%d]=4'd%d; rom_a[%d]=8'd%d; rom_b[%d]=8'd%d; rom_th[%d]=32'sd%d; // %s",
                 i, op, i, a, i, b, i, q, ISA::mnemonic(op))
        end.join("\n")
      end
    end
  end
end
