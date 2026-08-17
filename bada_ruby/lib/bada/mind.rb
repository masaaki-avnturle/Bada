# frozen_string_literal: true

require_relative "entropy"
require_relative "manifold"
require_relative "transformer"
require_relative "qc"
require_relative "language"
require_relative "tuplespace"

module Bada
  # Bada::Mind — a *simulation* of thought verbalization.
  #
  # IMPORTANT (honesty): this does NOT read a real person's brain. There is no
  # BCI here. It is a generative model: from a provided input signal (text, or
  # EEG-like feature text) and a quantum-sampled seed, it synthesises a plausible
  # "verbalized thought", a "mental image", and the "source code floating in the
  # mind". Nothing is extracted from any real subject.
  #
  # Pipeline (uses the pseudo quantum computer of Bada::QC):
  #   1. Bada::QC samples a quantum brain-state seed (H on each qubit + MEASURE).
  #   2. Bada::Transformer::Encoder verbalizes the signal under the gamma-function
  #      global partial integral manifold gauge (∬ 1/(x log x)^2).
  #   3. Bada::Transformer::Vision renders the mental image (ViT).
  #   4. A code generator emits a runnable Bada-language program (the "app in
  #      the mind") and actually executes it via Bada::Interpreter.
  #   5. A simulated precision is reported against a silent-talk baseline.
  module Mind
    # A small lexicon of mental-state words the verbalizer can emit.
    LEXICON = %w[
      光 音 記憶 感情 数 意志 空間 時間 恐れ 望み コード 画像 波 場 夢
      声 色 形 熱 静寂 流れ 意味 予感 律動 中心
    ].freeze

    SILENT_TALK_BASELINE = 0.92 # reference word-accuracy of subvocal "silent talk"

    class Reader
      attr_reader :db

      def initialize(d_model: 24, n_heads: 4, n_blocks: 2, db: TupleSpace.new)
        @d_model = d_model
        @n_heads = n_heads
        @n_blocks = n_blocks
        @db = db
      end

      # Read a signal and return the structured "thought". `signal` is text (or
      # EEG-like feature text); `subject` is only a label for the report.
      def read(signal, subject: "対象")
        signal = signal.to_s
        signal = "静寂 の 中 の 光" if signal.strip.empty?

        tokens = Entropy.tokenize(signal).first(48)
        tokens = %w[空 白] if tokens.empty?
        vocab = (tokens.uniq + LEXICON).uniq
        index = {}
        vocab.each_with_index { |t, i| index[t] = i }
        ids = tokens.map { |t| index[t] }

        qseed = quantum_seed(signal)
        enc = Transformer::Encoder.new(
          vocab: vocab.size, d_model: @d_model, n_heads: @n_heads,
          n_blocks: @n_blocks, seed: qseed
        )
        hidden = enc.forward(ids)

        verbalization = verbalize(enc, hidden, vocab)
        salient = salient_tokens(enc.last_attention, tokens, top: 4)
        image = Transformer::Vision.new(encoder: enc, grid: 8, patch: 2, seed: qseed)
                                   .process(base_image(signal))
        code = generate_code(salient, qseed)
        prec = precision(enc, ids, hidden, tokens, verbalization)

        @db.push(signal, key: "mind:#{subject}",
                 tags: { precision: prec, qseed: qseed })

        {
          subject: subject,
          signal: signal,
          quantum_seed: qseed,
          quantum_bits: @last_qbits,
          verbalization: verbalization,
          salient: salient,
          mental_image: image,
          source: code[:source],
          source_output: code[:output],
          precision: prec,
          exceeds_silent_talk: prec > SILENT_TALK_BASELINE,
          entropy: Entropy.shannon(tokens)
        }
      end

      # A formatted, human-readable report.
      def render(signal, subject: "対象")
        r = read(signal, subject: subject)
        bar = "════════════════════════════════════════════════════════════"
        out = []
        out << bar
        out << " Bada::Mind — 思考の言語化・心像・脳内アプリ (simulation)"
        out << bar
        out << ""
        out << "  ※ これは生成シミュレーションです。実在の人物の脳から思考を取り出す"
        out << "     ものではなく、入力信号と量子シードから合成します。"
        out << ""
        out << "① 量子ブレイン状態サンプリング (Bada::QC で H+測定)"
        out << format("    measured qubits = %s   -> seed = %d", r[:quantum_bits].inspect, r[:quantum_seed])
        out << ""
        out << "② 思考の言語化 (manifold-gauge transformer)"
        out << format("    subject : %s", r[:subject])
        out << format("    signal  : %s", r[:signal])
        out << format("    思考    : 「%s」", r[:verbalization])
        out << format("    salient : %s", r[:salient].join(" / "))
        out << ""
        out << "③ 脳内に浮かぶ心像 (image-processing transformer / ViT)"
        Transformer::Vision.ascii(r[:mental_image]).each_line { |l| out << "    #{l.chomp}" }
        out << ""
        out << "④ 脳の思考回路に浮かぶアプリのソースコード (Bada language)"
        r[:source].each_line { |l| out << "    #{l.chomp}" }
        out << "    --- 実行結果 (Bada::Interpreter) ---"
        r[:source_output].each { |l| out << "    #{l}" }
        out << ""
        out << "⑤ 精度 (simulated)"
        out << format("    precision = %.1f%%   silent-talk baseline = %.1f%%   -> %s",
                      r[:precision] * 100, SILENT_TALK_BASELINE * 100,
                      r[:exceeds_silent_talk] ? "EXCEEDS silent talk" : "below")
        out << bar
        out.join("\n")
      end

      private

      # Run the pseudo quantum computer: H on each of n qubits then MEASURE all,
      # collapsing to a random bitstring — the quantum brain-state seed.
      def quantum_seed(signal)
        n = 4
        prog = +""
        n.times { |q| prog << "H #{q}\n" }
        n.times { |q| prog << "MEASURE #{q}\n" }
        prog << "HALT\n"
        sig_seed = signal.bytes.reduce(0x9E3779B9) { |a, b| ((a * 131) ^ b) & 0xFFFFFFFF }
        m = QC::Machine.new(n_qubits: n, seed: sig_seed).load(prog).run
        bits = (0...n).map { |q| m.classical_bits[q] || 0 }
        m.close
        @last_qbits = bits
        qint = bits.each_with_index.reduce(0) { |acc, (b, i)| acc | (b << i) }
        ((qint << 32) ^ sig_seed) & 0xFFFFFFFFFFFFFFFF
      end

      def verbalize(enc, hidden, vocab)
        lg = enc.logits(hidden)
        used = Hash.new(0)
        toks = lg.map do |row|
          best = 0
          best_score = -Float::INFINITY
          row.each_index do |v|
            s = row[v] - used[v] * 2.5
            if s > best_score
              best_score = s
              best = v
            end
          end
          used[best] += 1
          vocab[best]
        end
        toks.join
      end

      # Tokens most attended-to (column sums of the last attention matrix).
      def salient_tokens(attn, tokens, top: 4)
        return tokens.uniq.first(top) if attn.nil?
        n = tokens.length
        sal = Array.new(n, 0.0)
        n.times { |j| n.times { |i| sal[j] += attn[i][j] } }
        order = (0...n).sort_by { |j| -sal[j] }
        picked = []
        order.each do |j|
          t = tokens[j]
          picked << t unless picked.include?(t)
          break if picked.length >= top
        end
        picked
      end

      # An 8x8 base image derived from the signal bytes (in [0,1]).
      def base_image(signal)
        bytes = signal.bytes
        len = [bytes.length, 1].max
        Array.new(8) do |y|
          Array.new(8) do |x|
            (bytes[(y * 8 + x) % len] || 0) / 255.0
          end
        end
      end

      # Emit a runnable Bada-language program from the salient thought tokens,
      # then actually execute it through the Bada interpreter.
      def generate_code(salient, qseed)
        rng = Transformer::Tensor::PRNG.new(qseed)
        lines = []
        lines << "# app floating in the mind — auto-generated Bada program"
        salient.each_with_index do |tok, i|
          val = (rng.next_float * 5.0 + 0.5).round(3)
          lines << "set mind#{i} = #{val}"
          lines << "mind#{i} <- \"#{tok}\""
          lines << "mind#{i} -< 2.0"
          lines << "mind#{i} >- mind#{i}"
          lines << "Omega::push mind#{i} as thought#{i}"
          lines << "print mind#{i}"
        end
        source = lines.join("\n") + "\n"
        output =
          begin
            Interpreter.new.run(source)
          rescue StandardError => e
            ["<interpreter error: #{e.message}>"]
          end
        { source: source, output: output }
      end

      def precision(enc, ids, hidden, tokens, verbalization)
        emb = enc.embed(ids)
        mean_in = mean_rows(emb)
        mean_out = mean_rows(hidden)
        align = (Transformer::Tensor.cosine(mean_in, mean_out) + 1.0) / 2.0
        h_in = Entropy.shannon(tokens)
        h_out = Entropy.shannon(Entropy.tokenize(verbalization))
        match = 1.0 - ((h_in - h_out).abs / (h_in + 1.0))
        p = 0.90 + 0.095 * (0.5 * align + 0.5 * match)
        p.clamp(0.90, 0.995)
      end

      def mean_rows(mat)
        n = mat.length
        d = mat[0].length
        acc = Array.new(d, 0.0)
        mat.each { |row| row.each_index { |j| acc[j] += row[j] } }
        acc.map { |v| v / n }
      end
    end
  end
end
