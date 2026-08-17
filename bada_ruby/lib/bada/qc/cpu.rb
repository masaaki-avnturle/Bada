# frozen_string_literal: true

require_relative "disk_memory"
require_relative "logic"
require_relative "isa"

module Bada
  module QC
    # CPU — the von-Neumann control unit of the pseudo quantum computer.
    #
    # It runs the classic fetch → decode → execute cycle over a program stored in
    # the *same* disk memory as the quantum state (stored-program). Decoding uses
    # the simulated semiconductor decoder (Bada::QC::Logic), and every gate reads
    # and writes the state-vector amplitudes on disk (Bada::QC::DiskMemory).
    #
    # Memory layout (words), all on disk:
    #   [0] n_qubits   [1] program_len   [2] pc   [3] flags
    #   program:  base = 4,           program_len * 4 words (4-word records)
    #   data:     base = 4 + plen*4,  2 * 2**n words (complex amplitudes)
    class CPU
      HEADER = 4

      attr_reader :mem, :n, :dim, :prog_base, :data_base, :classical, :steps

      def initialize(mem:, n:, program_len:, rng: Random.new(0xBADA))
        @mem = mem
        @n = n
        @dim = 1 << n
        @program_len = program_len
        @prog_base = HEADER
        @data_base = HEADER + program_len * ISA::RECORD_WORDS
        @rng = rng
        @classical = {}
        @steps = 0
        @trace = []
      end

      # Write the header + program records to disk, then initialise |0...0>.
      def load!(program)
        @mem.write(0, @n)
        @mem.write(1, @program_len)
        @mem.write(2, 0)     # pc
        @mem.write(3, 0)     # flags
        program.each_with_index do |(op, a, b, theta), i|
          base = @prog_base + i * ISA::RECORD_WORDS
          @mem.write(base + 0, op)
          @mem.write(base + 1, a)
          @mem.write(base + 2, b)
          @mem.write(base + 3, theta)
        end
        reset_state!
        @mem.flush
      end

      def reset_state!
        (0...@dim).each { |i| @mem.write_amp(@data_base, i, Complex(0, 0)) }
        @mem.write_amp(@data_base, 0, Complex(1, 0))
      end

      # Full fetch-decode-execute loop. Returns the execution trace.
      def run
        loop do
          pc = @mem.read(2).to_i
          break if pc >= @program_len
          op, a, b, theta = fetch(pc)
          decoded = Logic.decode_index(op.to_i, ISA::OPCODE_BITS) # semiconductor decode
          @trace << [pc, ISA::mnemonic(decoded), a.to_i, b.to_i, theta]
          break if decoded == ISA::OPCODES["HALT"]
          execute(decoded, a.to_i, b.to_i, theta.to_f)
          @steps += 1
          @mem.write(2, pc + 1) # advance PC on disk
        end
        @mem.flush
        @trace
      end

      def fetch(pc)
        base = @prog_base + pc * ISA::RECORD_WORDS
        [@mem.read(base), @mem.read(base + 1), @mem.read(base + 2), @mem.read(base + 3)]
      end

      # Probabilities read straight back from the disk-resident state vector.
      def probabilities
        (0...@dim).map { |i| @mem.read_amp(@data_base, i).abs2 }
      end

      private

      def execute(op, a, b, theta)
        case ISA::NAMES[op]
        when "NOP" then nil
        when "H"   then apply1(a, hadamard)
        when "X"   then apply1(a, [[0, 1], [1, 0]])
        when "Y"   then apply1(a, [[0, Complex(0, -1)], [Complex(0, 1), 0]])
        when "Z"   then apply1(a, [[1, 0], [0, -1]])
        when "S"   then apply1(a, [[1, 0], [0, Complex(0, 1)]])
        when "T"   then apply1(a, [[1, 0], [0, expi(Math::PI / 4)]])
        when "RX"  then apply1(a, rx(theta))
        when "RZ"  then apply1(a, rz(theta))
        when "CX"  then apply_cx(a, b)
        when "MEASURE" then measure(a)
        end
      end

      SQRT1_2 = 1.0 / Math.sqrt(2.0)

      def hadamard
        [[SQRT1_2, SQRT1_2], [SQRT1_2, -SQRT1_2]]
      end

      def expi(t)
        Complex(Math.cos(t), Math.sin(t))
      end

      def rx(theta)
        c = Math.cos(theta / 2.0)
        s = Complex(0, -Math.sin(theta / 2.0))
        [[c, s], [s, c]]
      end

      def rz(theta)
        [[expi(-theta / 2.0), 0], [0, expi(theta / 2.0)]]
      end

      # Apply a 2x2 gate to qubit q, streaming amplitude pairs off/onto disk.
      def apply1(q, m)
        step = 1 << q
        m00 = to_c(m[0][0]); m01 = to_c(m[0][1])
        m10 = to_c(m[1][0]); m11 = to_c(m[1][1])
        (0...@dim).each do |i|
          next unless (i & step).zero?
          j = i | step
          a0 = @mem.read_amp(@data_base, i)
          a1 = @mem.read_amp(@data_base, j)
          @mem.write_amp(@data_base, i, m00 * a0 + m01 * a1)
          @mem.write_amp(@data_base, j, m10 * a0 + m11 * a1)
        end
      end

      def apply_cx(control, target)
        cbit = 1 << control
        tbit = 1 << target
        (0...@dim).each do |i|
          next unless (i & cbit) != 0 && (i & tbit).zero?
          j = i | tbit
          a0 = @mem.read_amp(@data_base, i)
          a1 = @mem.read_amp(@data_base, j)
          @mem.write_amp(@data_base, i, a1)
          @mem.write_amp(@data_base, j, a0)
        end
      end

      def measure(q)
        bit = 1 << q
        p1 = 0.0
        (0...@dim).each { |i| p1 += @mem.read_amp(@data_base, i).abs2 if (i & bit) != 0 }
        outcome = @rng.rand < p1 ? 1 : 0
        norm = Math.sqrt(outcome == 1 ? p1 : (1.0 - p1))
        norm = 1.0 if norm < 1e-12
        (0...@dim).each do |i|
          keep = ((i & bit) != 0 ? 1 : 0) == outcome
          amp = keep ? @mem.read_amp(@data_base, i) / norm : Complex(0, 0)
          @mem.write_amp(@data_base, i, amp)
        end
        @classical[q] = outcome
        outcome
      end

      def to_c(v)
        v.is_a?(Complex) ? v : Complex(v, 0)
      end
    end
  end
end
