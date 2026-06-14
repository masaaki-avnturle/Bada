# frozen_string_literal: true

require_relative "polynomial"

module Bada
  module Prover
    # A proof result. status is the honest verdict:
    #   :proved     - established by a sound, checkable method
    #   :disproved  - a concrete counterexample was found (also sound)
    #   :open       - not decided by our methods; computational evidence only
    Proof = Struct.new(:status, :method, :steps, :counterexample, :evidence, keyword_init: true) do
      def proved? = status == :proved
      def disproved? = status == :disproved
      def open? = status == :open

      def symbol
        { proved: "∎ 証明完了 (QED)", disproved: "✗ 反証（反例あり）",
          open: "? 未解決（経験的証拠のみ）" }[status]
      end
    end

    # Closed-form summation S(n) = Σ_{k=1}^n f(k) for a polynomial summand f,
    # with a *sound* induction certificate.
    module Summation
      module_function

      # Returns [closed_form_polynomial, verified_bool, step_residual_polynomial].
      def closed_form(f)
        deg = f.degree.clamp(0, Float::INFINITY).to_i
        npts = deg + 2 # S has degree deg+1; need deg+2 points
        pts = []
        acc = Rational(0)
        (0..npts).each do |m|
          acc += f.eval(m) if m >= 1
          pts << [m, acc]
        end
        c = Polynomial.interpolate(pts)
        # induction certificate: C(0)=0 and C(n) - C(n-1) - f(n) == 0
        base_ok = c.eval(0).zero?
        step = c - c.shift(-1) - f
        [c, base_ok && step.zero?, step]
      end
    end

    # Proves / disproves  Σ_{k=1}^n f(k) = R(n)  for polynomial f, R.
    module IdentityProver
      module_function

      def prove(f, rhs, var: "n")
        c, verified, step = Summation.closed_form(f)
        steps = []
        steps << "1. 和 S(n)=Σ_{k=1}^#{var} (#{f.to_s('k')}) の閉形式を有限差分で構成: S(#{var}) = #{c.to_s(var)}"
        steps << "2. 帰納法の基底: S(0) = #{c.eval(0)} = 0 ✓"
        steps << "3. 帰納法の段階: S(#{var}) - S(#{var}-1) - (#{f.to_s(var)}) = #{step.to_s(var)} ≡ 0 ✓"
        unless verified
          return Proof.new(status: :open, method: "induction",
                           steps: steps + ["閉形式の帰納検証に失敗（想定外）。"], evidence: nil)
        end
        if c == rhs
          steps << "4. 主張の右辺 R(#{var}) = #{rhs.to_s(var)} は閉形式 S(#{var}) と多項式として一致。"
          Proof.new(status: :proved, method: "閉形式 + 数学的帰納法", steps: steps)
        else
          n = first_counterexample(f, rhs)
          steps << "4. しかし R(#{var}) = #{rhs.to_s(var)} ≠ S(#{var})。反例 #{var}=#{n}。"
          Proof.new(status: :disproved, method: "閉形式比較", steps: steps,
                    counterexample: { n: n, lhs: c.eval(n), rhs: rhs.eval(n) })
        end
      end

      def first_counterexample(f, rhs)
        acc = Rational(0)
        (1..1000).each do |n|
          acc += f.eval(n)
          return n if acc != rhs.eval(n)
        end
        nil
      end
    end

    # Proves / disproves  m | E(n)  for all integers n, where E has integer
    # coefficients. Since E(n) mod m depends only on n mod m, exhaustive check
    # of residues 0..m-1 is a *complete, sound* proof.
    module DivisibilityProver
      module_function

      def prove(e, m, var: "n")
        unless e.integer_coeffs?
          return Proof.new(status: :open, method: "modular", steps: ["E は整数係数でない。"])
        end
        residues = (0...m).map { |r| [r, e.eval_int(r) % m] }
        bad = residues.find { |(_, v)| v != 0 }
        table = residues.map { |(r, v)| "E(#{r})≡#{v}" }.join(", ")
        steps = [
          "1. E(#{var}) = #{e.to_s(var)} の値は #{var} mod #{m} のみに依存する（整数係数多項式）。",
          "2. 剰余系を全数検査 (mod #{m}): #{table}"
        ]
        if bad.nil?
          steps << "3. すべての剰余で E≡0 (mod #{m}) ⇒ 任意の整数 #{var} で #{m} | E(#{var})。"
          Proof.new(status: :proved, method: "剰余系の全数検査 (完全)", steps: steps)
        else
          r = bad[0]
          steps << "3. E(#{r}) ≡ #{bad[1]} ≢ 0 (mod #{m})。反例 #{var}=#{r}。"
          Proof.new(status: :disproved, method: "剰余系の全数検査", steps: steps,
                    counterexample: { n: r, value: e.eval_int(r), mod: m })
        end
      end
    end

    # Exhaustively verifies a predicate over a finite domain (sound).
    module FiniteCaseProver
      module_function

      def prove(domain, description:, &predicate)
        bad = domain.find { |x| !predicate.call(x) }
        if bad.nil?
          Proof.new(status: :proved, method: "有限領域の全数検査",
                    steps: ["領域 #{description} の全 #{domain.size} 例で命題が成立。"])
        else
          Proof.new(status: :disproved, method: "有限領域の全数検査",
                    steps: ["領域 #{description} の x=#{bad} で命題が不成立。"],
                    counterexample: { x: bad })
        end
      end
    end

    # Empirical tester for statements our sound methods cannot decide. Finds
    # genuine counterexamples (sound disproof) but NEVER claims a proof; if no
    # counterexample is found it reports :open with the tested range as evidence.
    module EmpiricalTester
      module_function

      def test(domain, description:, &predicate)
        bad = domain.find { |x| !predicate.call(x) }
        if bad
          Proof.new(status: :disproved, method: "経験的探索",
                    steps: ["#{description} の x=#{bad} で反例を発見。"],
                    counterexample: { x: bad })
        else
          Proof.new(status: :open, method: "経験的検証（証明ではない）",
                    steps: ["#{description} の検証範囲では反例なし。これは証拠であって証明ではない。"],
                    evidence: { checked: domain.respond_to?(:size) ? domain.size : nil, range: description })
        end
      end
    end
  end
end
