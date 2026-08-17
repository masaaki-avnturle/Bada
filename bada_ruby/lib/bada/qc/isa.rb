# frozen_string_literal: true

module Bada
  module QC
    # ISA — the pseudo quantum computer's instruction set (BadaQASM) and its
    # von-Neumann encoding into disk words.
    #
    # Each instruction is a fixed 4-word record:  [opcode, a, b, theta]
    # so the *program* lives in the same disk memory as the *data* (state
    # vector) — a stored-program (von Neumann) machine.
    module ISA
      module_function

      RECORD_WORDS = 4

      # opcode table (4-bit, decoded by the simulated semiconductor decoder)
      OPCODES = {
        "NOP"     => 0,
        "H"       => 1,  # Hadamard on a
        "X"       => 2,  # Pauli-X on a
        "Y"       => 3,  # Pauli-Y on a
        "Z"       => 4,  # Pauli-Z on a
        "S"       => 5,  # phase S on a
        "T"       => 6,  # phase T on a
        "CX"      => 7,  # CNOT control a, target b
        "RX"      => 8,  # rotation about X by theta on a
        "RZ"      => 9,  # rotation about Z by theta on a
        "MEASURE" => 10, # collapse a (records classical bit)
        "HALT"    => 11
      }.freeze

      OPCODE_BITS = 4
      NAMES = OPCODES.invert.freeze

      # Parse BadaQASM source into an array of [opcode, a, b, theta] records.
      #
      #   # comment
      #   H 0
      #   CX 0 1
      #   RZ 1 0.7853981634
      #   MEASURE 0
      #   HALT
      def assemble(source)
        program = []
        source.each_line do |raw|
          line = raw.strip.sub(/#.*\z/, "").strip
          next if line.empty?
          tok = line.split(/\s+/)
          mnem = tok[0].upcase
          op = OPCODES.fetch(mnem) { raise "unknown instruction: #{mnem}" }
          a = tok[1] ? tok[1].to_i : 0
          b = tok[2] ? tok[2].to_i : 0
          theta =
            case mnem
            when "RX", "RZ" then (tok[2] || tok[1]).to_f # theta is last arg
            else 0.0
            end
          # For RX/RZ the form is "RX <qubit> <theta>", so b holds nothing useful:
          if %w[RX RZ].include?(mnem)
            a = tok[1].to_i
            theta = tok[2].to_f
            b = 0
          end
          program << [op, a, b, theta]
        end
        program
      end

      def mnemonic(opcode)
        NAMES[opcode] || "?"
      end
    end
  end
end
