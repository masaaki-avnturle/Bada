# frozen_string_literal: true

module Bada
  module QC
    # DiskMemory — the pseudo quantum computer's *disk-backed* main memory.
    #
    # 「PCのハードディスクの内部に電子回路をシミュレーションで作って、ディスクメモリの
    #   内蔵シミュレーションを利用した結果を使う」——量子状態ベクトルとプログラムを
    #   同一の線形メモリ（＝実ファイル／ハードディスク上）に置き、ノイマン型の
    #   ストアドプログラム方式で読み書きします。
    #
    # Memory is a flat array of 64-bit IEEE-754 words stored in a real file on the
    # disk. The state vector amplitudes and the program share this one address
    # space (von Neumann). Every gate application actually seeks/reads/writes the
    # disk, so the computation genuinely runs "inside the hard disk".
    class DiskMemory
      WORD = 8 # bytes per word (double)

      attr_reader :path, :words

      def initialize(path:, words:)
        @path = path
        @words = words
        @file = File.open(path, File::RDWR | File::CREAT | File::BINARY)
        # Force raw binary I/O so a process-wide Encoding.default_internal
        # (the CLI sets UTF-8) never transcodes the packed double bytes.
        @file.binmode
        @file.set_encoding(Encoding::BINARY, nil)
        @file.truncate(words * WORD)
      end

      # Raw word access (word-addressable disk memory).
      def write(index, float)
        raise "address #{index} out of range" if index.negative? || index >= @words
        @file.seek(index * WORD)
        @file.write([float.to_f].pack("E")) # little-endian double
      end

      def read(index)
        raise "address #{index} out of range" if index.negative? || index >= @words
        @file.seek(index * WORD)
        @file.read(WORD).unpack1("E")
      end

      # Complex amplitude = two consecutive words (re, im) at data_base + 2*i.
      def write_amp(base, i, complex)
        write(base + 2 * i,     complex.real)
        write(base + 2 * i + 1, complex.imaginary)
      end

      def read_amp(base, i)
        Complex(read(base + 2 * i), read(base + 2 * i + 1))
      end

      def flush
        @file.flush
      end

      def close
        @file.flush
        @file.close
      end

      # Bytes actually resident on disk for this memory image.
      def byte_size
        @words * WORD
      end
    end
  end
end
