# frozen_string_literal: true

require "tmpdir"
require_relative "disk_memory"
require_relative "isa"
require_relative "cpu"
require_relative "monitor"
require_relative "verilog"

module Bada
  module QC
    # Machine — the whole pseudo quantum computer as one facade.
    #
    #   m = Bada::QC::Machine.new(n_qubits: 2)
    #   m.load(<<~QASM)
    #     H 0
    #     CX 0 1
    #     HALT
    #   QASM
    #   m.run
    #   m.probabilities          # => Bell state [0.5, 0, 0, 0.5]
    #   puts m.monitor           # control circuit projected on the monitor
    #   puts m.verilog           # semiconductor (Verilog) source code
    #
    # The state vector and program live on a real disk file (von Neumann memory).
    class Machine
      attr_reader :n, :program, :cpu, :mem, :trace

      def initialize(n_qubits:, dir: nil, seed: 0xBADA)
        @n = n_qubits
        @dir = dir || Dir.mktmpdir("bada_qc")
        @seed = seed
        @program = []
      end

      def load(source)
        @program = source.is_a?(Array) ? source : ISA.assemble(source)
        words = CPU::HEADER + @program.length * ISA::RECORD_WORDS + 2 * (1 << @n)
        path = File.join(@dir, "qc_disk_memory.bin")
        @mem = DiskMemory.new(path: path, words: words)
        @cpu = CPU.new(mem: @mem, n: @n, program_len: @program.length, rng: Random.new(@seed))
        @cpu.load!(@program)
        self
      end

      def run
        @trace = @cpu.run
        self
      end

      def probabilities
        @cpu.probabilities
      end

      def classical_bits
        @cpu.classical
      end

      # The disk image size actually written on the HDD.
      def disk_bytes
        @mem&.byte_size
      end

      def monitor
        Monitor.project(@program, @n, disk_bytes: disk_bytes)
      end

      def verilog(module_name: "bada_qc_control")
        Verilog.generate(@program, @n, module_name: module_name)
      end

      # A full human-readable report (monitor + measured statevector + trace).
      def report
        lines = []
        lines << monitor
        lines << ""
        lines << "  program (BadaQASM, stored on disk):"
        @program.each_with_index do |(op, a, b, th), i|
          args = ISA::NAMES[op] == "CX" ? "#{a},#{b}" : (%w[RX RZ].include?(ISA::NAMES[op]) ? "#{a},#{format('%.4f', th)}" : a.to_s)
          lines << format("    %02d: %-7s %s", i, ISA::mnemonic(op), args)
        end
        lines << ""
        lines << "  state vector (read back from disk memory):"
        probabilities.each_with_index do |p, i|
          next if p < 1e-9
          lines << format("    |%s> : P = %.4f", i.to_s(2).rjust(@n, "0"), p)
        end
        unless classical_bits.empty?
          lines << ""
          lines << "  classical register (measurements): #{classical_bits.sort.to_h}"
        end
        lines << ""
        lines << format("  disk memory image: %d bytes, %d instructions, %d amplitudes",
                        disk_bytes.to_i, @program.length, 1 << @n)
        lines.join("\n")
      end

      def close
        @mem&.close
      end

      # A couple of ready-made demo programs.
      def self.bell
        new(n_qubits: 2).load("H 0\nCX 0 1\nHALT\n").run
      end

      def self.ghz
        new(n_qubits: 3).load("H 0\nCX 0 1\nCX 1 2\nHALT\n").run
      end
    end
  end
end
