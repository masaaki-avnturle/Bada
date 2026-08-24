# frozen_string_literal: true
#
# quantum_ext.rb — Bada 言語 量子プログラミング拡張
#
# bada_ruby の Bada::Interpreter を継承し、量子レジスタ(状態ベクトル
# シミュレータ)と silent-talk 思考入力パイプラインの命令を Bada 言語に
# 追加する。既存の演算子代数 (<- / -< / >- / Ω::) はそのまま使える。
#
# 追加された量子命令 (silent_talk.bada 参照):
#
#   qreg q = 5                     5 qubit レジスタ (2^5 = 32 振幅)
#   load sig = "file.txt"          数値列をロード
#   q <~ sig                       振幅符号化 (思考信号 → 量子状態)
#   q -< manifold                  大域的部分積分多様体 対角作用素
#   q >- hadamard                  全 qubit Hadamard (量子干渉 / transformer 混合)
#   q <- gamma 0.5                 Γ(s) 位相ゲート
#   q <- zeta 2.0                  ζ(s) 位相ゲート
#   entangle q                     CNOT 鎖 (もつれ)
#   measure q times 24 into syms   測定 → 思考記号列
#   markov syms into cert          マルコフ path certainty
#   jones sig into intent          Jones 多項式 熱意図性 V_K(e^{-1/kT})
#   confide cert intent into conf  信頼度統合 (silent-talk 超え判定)
#   gain conf                      ベースライン 0.62 との比較を出力
#   render q = "frame.pgm"         確率分布を映像化 (PGM フレーム)
#
# 依存: bada_ruby (Ruby 標準ライブラリのみ)。

require "bada"

module Bada
  module Quantum
    SILENT_TALK_BASELINE = 0.62

    # ------------------------------------------------------------------
    # QReg — 複素状態ベクトルによる n-qubit レジスタ
    # ------------------------------------------------------------------
    class QReg
      attr_reader :n, :amps

      def initialize(n)
        @n = n
        @amps = Array.new(1 << n) { Complex(0.0, 0.0) }
        @amps[0] = Complex(1.0, 0.0)
      end

      def dim = 1 << @n

      def normalize!
        norm = Math.sqrt(@amps.sum { |a| a.abs2 })
        return self if norm < 1e-12
        @amps.map! { |a| a / norm }
        self
      end

      # 振幅符号化: 実数列を状態ベクトルへ (思考信号の量子埋め込み)
      def encode!(series)
        d = dim
        @amps = Array.new(d) do |k|
          v = series[k % series.length] || 0.0
          Complex(v, 0.0)
        end
        normalize!
      end

      # 大域的部分積分多様体 対角作用素:
      #   |k⟩ → sqrt(1 + 1/(x_k (log x_k)^2)) |k⟩,  x_k = k + 2
      def manifold!
        @amps.each_index do |k|
          w = Math.sqrt(1.0 + Bada::Manifold.element(k + 2.0))
          @amps[k] *= w
        end
        normalize!
      end

      # Hadamard を単一 qubit に適用
      def h!(q)
        s = 1.0 / Math.sqrt(2.0)
        bit = 1 << q
        (0...dim).each do |k|
          next unless (k & bit).zero?
          a = @amps[k]
          b = @amps[k | bit]
          @amps[k]       = s * (a + b)
          @amps[k | bit] = s * (a - b)
        end
        self
      end

      def h_all!
        (0...@n).each { |q| h!(q) }
        self
      end

      # Γ(s) 位相ゲート: |k⟩ → e^{iθ_k}|k⟩, θ_k = π·s / Γ(1 + (k mod 8)·s/4)
      def gamma_phase!(s)
        @amps.each_index do |k|
          g = Bada::Special.gamma(1.0 + (k % 8) * s / 4.0)
          g = 1e-9 if g.abs < 1e-9
          theta = Math::PI * s / g
          @amps[k] *= Complex(Math.cos(theta), Math.sin(theta))
        end
        self
      end

      # ζ(s) 位相ゲート: |k⟩ → e^{iθ_k}|k⟩, θ_k = π / (k+1)^s (Dirichlet 項位相)
      def zeta_phase!(s)
        @amps.each_index do |k|
          theta = Math::PI / ((k + 1.0)**s)
          @amps[k] *= Complex(Math.cos(theta), Math.sin(theta))
        end
        self
      end

      # CNOT 鎖 (qubit i を制御, i+1 を標的) — もつれ生成
      def entangle!
        (0...(@n - 1)).each do |c|
          cbit = 1 << c
          tbit = 1 << (c + 1)
          (0...dim).each do |k|
            next if (k & cbit).zero? || (k & tbit) != 0
            j = k | tbit
            @amps[k], @amps[j] = @amps[j], @amps[k]
          end
        end
        self
      end

      def probabilities
        @amps.map(&:abs2)
      end

      # 測定 (非破壊コピーからのサンプル; seed 固定で再現的)
      def measure(times, vocab, seed: 0x1234abcd)
        rng = Random.new(seed)
        probs = probabilities
        out = []
        times.times do
          r = rng.rand
          acc = 0.0
          idx = 0
          probs.each_with_index do |p, k|
            acc += p
            if r <= acc
              idx = k
              break
            end
          end
          out << (idx % vocab)
        end
        out
      end
    end

    # ------------------------------------------------------------------
    # Interpreter — Bada 言語 + 量子命令
    # ------------------------------------------------------------------
    class Interpreter < Bada::Interpreter
      def initialize(db: Bada::TupleSpace.new, base_dir: Dir.pwd)
        super(db: db)
        @base_dir = base_dir
        @qregs    = {}
        @series   = {}
        @lists    = {}
        @scalars  = {}
        @manifold_mass = 0.0
      end

      private

      def exec_line(line)
        case line
        when /\Aqreg\s+(\w+)\s*=\s*(\d+)\z/
          @qregs[$1] = QReg.new($2.to_i)
        when /\Aload\s+(\w+)\s*=\s*"(.+)"\z/
          path = File.expand_path($2, @base_dir)
          @series[$1] = File.readlines(path).map(&:to_f)
        when /\A(\w+)\s*<~\s*(\w+)\z/
          qreg($1).encode!(series($2))
          @manifold_mass = manifold_mass(series($2).length)
        when /\A(\w+)\s*-<\s*manifold\z/
          qreg($1).manifold!
        when /\A(\w+)\s*>-\s*hadamard\z/
          qreg($1).h_all!
        when /\A(\w+)\s*<-\s*gamma\s+([-+]?\d+(?:\.\d+)?)\z/
          qreg($1).gamma_phase!($2.to_f)
        when /\A(\w+)\s*<-\s*zeta\s+([-+]?\d+(?:\.\d+)?)\z/
          qreg($1).zeta_phase!($2.to_f)
        when /\Aentangle\s+(\w+)\z/
          qreg($1).entangle!
        when /\Ameasure\s+(\w+)\s+times\s+(\d+)\s+into\s+(\w+)\z/
          syms = qreg($1).measure($2.to_i, 8)
          @lists[$3] = syms
          @output << "measure #{$1}: #{syms.join(' ')}"
        when /\Amarkov\s+(\w+)\s+into\s+(\w+)\z/
          @scalars[$2] = markov_path_certainty(list($1))
          @output << "markov path certainty = #{format('%.4f', @scalars[$2])}"
        when /\Ajones\s+(\w+)\s+into\s+(\w+)\z/
          @scalars[$2] = jones_thermal_intent(series($1), 0.5)
          @output << "jones thermal intent  = #{format('%.4f', @scalars[$2])}"
        when /\Aconfide\s+(\w+)\s+(\w+)\s+into\s+(\w+)\z/
          conf = confidence(scalar($1), scalar($2))
          @scalars[$3] = conf
          @env[$3] = Bada::BadaNode.new(conf)
          @output << "confidence = #{format('%.4f', conf)}"
        when /\Again\s+(\w+)\z/
          c = scalar($1)
          g = (c - SILENT_TALK_BASELINE) / SILENT_TALK_BASELINE * 100.0
          verdict = c > SILENT_TALK_BASELINE ? "EXCEEDS" : "below"
          @output << "silent-talk baseline #{SILENT_TALK_BASELINE} → gain #{format('%+.1f', g)}% (#{verdict})"
        when /\Arender\s+(\w+)\s*=\s*"(.+)"\z/
          write_pgm(qreg($1), File.expand_path($2, @base_dir))
        else
          super
        end
      end

      # ---- helpers ---------------------------------------------------

      def qreg(name)   = @qregs[name]  || raise("Bada quantum error: no qreg #{name}")
      def series(name) = @series[name] || raise("Bada quantum error: no series #{name}")
      def list(name)   = @lists[name]  || raise("Bada quantum error: no list #{name}")
      def scalar(name) = @scalars[name] || raise("Bada quantum error: no scalar #{name}")

      # M(2, 2+N) — lib/gamma_manifold.c の gpi_manifold と同じ構成
      def manifold_mass(n)
        a = 2.0
        b = 2.0 + n
        acc = 0.0
        h = (b - a) / n
        n.times do |i|
          x0 = a + h * i
          x1 = x0 + h
          xm = 0.5 * (x0 + x1)
          local = (h / 6.0) * (kern(x0) + 4.0 * kern(xm) + kern(x1))
          boundary = 1.0 / Math.log([x0, 1.000001].max) - 1.0 / Math.log(x1)
          acc += 0.5 * (local + boundary)
        end
        acc
      end

      def kern(x)
        return 0.0 if x <= 1.0 + 1e-12
        lx = Math.log(x)
        1.0 / (x * lx * lx)
      end

      # 1 次マルコフ連鎖 (ラプラス平滑化) の経路遷移確率平均
      def markov_path_certainty(seq)
        return 0.0 if seq.length < 2
        vocab = 8
        trans = Hash.new(1e-3)
        rowsum = Hash.new(1e-3 * vocab)
        seq.each_cons(2) do |a, b|
          trans[[a, b]] += 1.0
          rowsum[a] += 1.0
        end
        probs = seq.each_cons(2).map { |a, b| trans[[a, b]] / rowsum[a] }
        probs.sum / probs.length
      end

      # lib/jones_thermal.c の移植: 熱時系列 → Jones 係数 → V_K(e^{-1/kT})
      def jones_thermal_intent(temps, k_t)
        return 0.0 if temps.length < 2
        degree = temps.length - 1
        coeffs = Array.new(degree + 1, 0.0)
        coeffs[0] = 1.0
        (0...(temps.length - 1)).each do |i|
          d = temps[i + 1] - temps[i]
          sign = d >= 0.0 ? 1.0 : -1.0
          amp = 1.0 / (1.0 + d.abs)
          k = i + 1
          coeffs[k] += sign * amp
          coeffs[k - 1] += -sign * amp * 0.5
        end
        t = Math.exp(-1.0 / [k_t, 1e-6].max)
        v = 0.0
        tk = 1.0
        coeffs.each { |c| v += c * tk; tk *= t }
        v.abs / (1.0 + degree * 0.1)
      end

      # C 版 silent_decode の (G) 段と同じ重み
      def confidence(path_cert, intent)
        mnorm = 1.0 - Math.exp(-@manifold_mass.abs)
        lang  = @lists.values.last ? shannon_bits(@lists.values.last) : 0.0
        lnorm = lang / (lang + 1.0)
        c = 0.55 * path_cert + 0.20 * intent + 0.15 * mnorm + 0.10 * lnorm
        c.clamp(0.0, 1.0)
      end

      def shannon_bits(seq)
        counts = seq.tally
        total = seq.length.to_f
        -counts.values.sum { |c| p = c / total; p * Math.log2(p) }
      end

      # 確率分布の映像化 (64x64 PGM) — 映像化トランスフォーマーの Bada 版
      def write_pgm(reg, path)
        w = h = 64
        probs = reg.probabilities
        mx = probs.max
        mx = 1.0 if mx < 1e-12
        FileUtils.mkdir_p(File.dirname(path)) if defined?(FileUtils)
        data = (0...h).flat_map do |y|
          (0...w).map do |x|
            k = (x * probs.length / w + y * probs.length / h) % probs.length
            (probs[k] / mx * 255.0).round.clamp(0, 255)
          end
        end
        File.open(path, "wb") do |f|
          f.write("P5\n#{w} #{h}\n255\n")
          f.write(data.pack("C*"))
        end
        @output << "render → #{path} (#{w}x#{h} PGM)"
      end
    end
  end
end
