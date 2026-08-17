# frozen_string_literal: true

require_relative "isa"

module Bada
  module QC
    # Monitor — projects the pseudo quantum computer's *control circuit* onto the
    # screen (モニターに投射する機知): the von-Neumann datapath block diagram plus
    # an ASCII rendering of the quantum gate circuit running on it.
    module Monitor
      module_function

      CELL = 5 # column width per instruction

      # The whole projection: datapath schematic + gate-circuit timeline.
      def project(program, n_qubits, disk_bytes: nil)
        [datapath(disk_bytes), "", circuit(program, n_qubits)].join("\n")
      end

      # Von-Neumann datapath: PC -> disk memory -> semiconductor decoder -> gate
      # unit -> state vector (on disk), with the control bus feeding back.
      def datapath(disk_bytes = nil)
        size = disk_bytes ? "#{disk_bytes} bytes on HDD" : "on HDD"
        <<~ASCII
          ===== MONITOR :: 擬似量子コンピュータ 制御回路 (von Neumann) =====

              +------+   addr    +==================+   instr   +------------------+
              |  PC  | --------> |   DISK  MEMORY   | --------> |  SEMICONDUCTOR   |
              +------+           |  von Neumann:    |           |  DECODER         |
                 ^               |  program + state |           |  (NAND / MOSFET  |
                 | pc+1          |  vector share    |           |   simulation)    |
                 |               |  one address     |           +---------+--------+
                 |               |  space           |                     | ctrl
                 |               |  (#{format('%-16s', size)})|                     v
                 |               +========+=========+           +------------------+
                 |                        ^  read/write          |   GATE  UNIT     |
                 |                        |  amplitudes          |  H X Y Z S T     |
                 +------------------------+----------------------|  CX RX RZ MEAS   |
                                                                 +------------------+
        ASCII
      end

      # ASCII quantum-circuit timeline (gates over qubit wires).
      def circuit(program, n_qubits)
        rows = Array.new(n_qubits) { +"" }
        program.each do |op, a, b, _theta|
          name = ISA::NAMES[op]
          next if name.nil? || name == "HALT" || name == "NOP"
          (0...n_qubits).each do |q|
            rows[q] << cell_for(name, q, a, b)
          end
        end
        lines = (0...n_qubits).map do |q|
          format("q%d ─%s─", q, rows[q].empty? ? "─" * CELL : rows[q])
        end
        (["  quantum circuit (time →):"] + lines).join("\n")
      end

      def cell_for(name, q, a, b)
        token =
          if name == "CX"
            if q == a then "●"
            elsif q == b then "⊕"
            elsif q > [a, b].min && q < [a, b].max then "│"
            else "─"
            end
          elsif q == a
            "[#{name[0]}]"
          else
            "─"
          end
        token.center(CELL, "─")
      end
    end
  end
end
