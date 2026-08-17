# frozen_string_literal: true

module Bada
  module QC
    # Logic — the *semiconductor* electronic-circuit simulation that drives the
    # classical control of the pseudo quantum computer.
    #
    # 「電子回路をシミュレーションで作って…半導体の…」——CMOS の MOSFET しきい値
    #   モデルから NAND を作り、NAND だけからインバータ／AND／OR／XOR と n-bit
    #   デコーダを組み上げます。CPU の命令デコードは、この*シミュレーション結果*で
    #   ワンホット選択を行います（＝半導体回路の結果を実際に使う）。
    #
    # Logic levels are volts on [0, VDD]; a MOSFET conducts above threshold VTH.
    module Logic
      module_function

      VDD = 1.0
      VTH = 0.5

      def high?(v)
        v >= VTH
      end

      def level(bit)
        bit == 1 || bit == true ? VDD : 0.0
      end

      # CMOS NAND: output low only when both inputs pull the series nFETs on.
      def nand(a, b)
        (high?(a) && high?(b)) ? 0.0 : VDD
      end

      # Inverter (NOT) = NAND with tied inputs.
      def inv(a)
        nand(a, a)
      end

      def and_(a, b)
        inv(nand(a, b))
      end

      def or_(a, b)
        nand(inv(a), inv(b))
      end

      def xor_(a, b)
        # xor = (a NAND (a NAND b)) NAND (b NAND (a NAND b))
        n = nand(a, b)
        nand(nand(a, n), nand(b, n))
      end

      # Read the k-th bit of value as a logic level.
      def bit_level(value, k)
        level((value >> k) & 1)
      end

      # An n-bit one-hot decoder built purely from NAND/INV gates. Returns an
      # array of 2**bits logic levels; exactly one is high (VDD). This is run by
      # the CPU to select which gate microcode to execute.
      def decode(value, bits)
        lines = (0...bits).map { |k| bit_level(value, k) }
        (0...(1 << bits)).map do |sel|
          # AND together each address line (or its complement) — an n-input AND
          # implemented as a NAND tree followed by an inverter.
          acc = VDD
          (0...bits).each do |k|
            want = (sel >> k) & 1
            line = want == 1 ? lines[k] : inv(lines[k])
            acc = and_(acc, line)
          end
          acc
        end
      end

      # Index of the (single) high output of the decoder — the decoded opcode.
      def decode_index(value, bits)
        decode(value, bits).index { |v| high?(v) } || 0
      end
    end
  end
end
