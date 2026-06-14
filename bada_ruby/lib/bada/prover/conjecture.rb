# frozen_string_literal: true

require_relative "polynomial"
require_relative "proof"
require_relative "../manifold"
require_relative "../entropy"

module Bada
  module Prover
    # Number-theory utilities for imagined problems.
    module NT
      module_function

      def prime?(n)
        return false if n < 2
        i = 2
        while i * i <= n
          return false if (n % i).zero?
          i += 1
        end
        true
      end

      def primes_upto(n)
        return [] if n < 2
        sieve = Array.new(n + 1, true)
        sieve[0] = sieve[1] = false
        (2..Integer.sqrt(n)).each { |i| (i * i..n).step(i) { |j| sieve[j] = false } if sieve[i] }
        (2..n).select { |i| sieve[i] }
      end

      def collatz_reaches_one?(n, cap: 100_000)
        steps = 0
        while n != 1
          n = n.even? ? n / 2 : 3 * n + 1
          steps += 1
          return false if steps > cap
        end
        true
      end

      def goldbach_holds?(even, prime_set)
        return true if even < 4 || even.odd?
        prime_set.any? { |p| p <= even - 2 && prime_set.include?(even - p) }
      end
    end

    # A single imagined statement plus a callable that returns a sound Proof.
    Conjecture = Struct.new(:id, :title, :statement, :latex, :kind, :prover, keyword_init: true) do
      def prove = prover.call
    end

    # ConjectureGenerator — the "imagination": invent unsolved-style statements
    # seeded by the question's manifold entropy invariant. The set deliberately
    # spans provable, disprovable, and genuinely-open classes so the engine can
    # demonstrate sound proof, sound disproof, and honest "open + evidence".
    module ConjectureGenerator
      module_function

      def imagine(question, count: 5)
        xi = Manifold.xi(question)
        h = Entropy.of(question)
        seed = ((xi.abs * 1e6).to_i + (h * 1000).to_i + question.to_s.bytes.sum)
        rng = Random.new(seed)
        cs = []
        cs << true_sum_identity(rng)
        cs << false_sum_identity(rng)
        cs << true_divisibility(rng)
        cs << false_divisibility(rng)
        cs << open_problem(rng)
        cs.first(count).each_with_index { |c, i| c.id = i + 1 }
        cs.first(count)
      end

      # ---- generators --------------------------------------------------
      def random_poly(rng, deg)
        Polynomial.from(Array.new(deg + 1) { rng.rand(1..4) })
      end

      def true_sum_identity(rng)
        f = random_poly(rng, rng.rand(1..2))
        c, = Summation.closed_form(f)
        Conjecture.new(
          title: "想像した和の恒等式（真）",
          statement: "Σ_{k=1}^n (#{f.to_s('k')}) = #{c.to_s('n')}",
          latex: "\\sum_{k=1}^{n}\\left(#{f.to_latex('k')}\\right) = #{c.to_latex('n')}",
          kind: :sum_identity,
          prover: -> { IdentityProver.prove(f, c) }
        )
      end

      def false_sum_identity(rng)
        f = random_poly(rng, rng.rand(1..2))
        c, = Summation.closed_form(f)
        wrong = c + Polynomial.from([0, 1]) # perturb by + n
        Conjecture.new(
          title: "想像した和の恒等式（要検証）",
          statement: "Σ_{k=1}^n (#{f.to_s('k')}) = #{wrong.to_s('n')}",
          latex: "\\sum_{k=1}^{n}\\left(#{f.to_latex('k')}\\right) = #{wrong.to_latex('n')}",
          kind: :sum_identity,
          prover: -> { IdentityProver.prove(f, wrong) }
        )
      end

      def true_divisibility(rng)
        a = [3, 5, 7].sample(random: rng) # prime exponent: Fermat little theorem
        e = Polynomial.from(Array.new(a + 1) { |i| i == a ? 1 : (i == 1 ? -1 : 0) }) # x^a - x
        Conjecture.new(
          title: "想像した整除性（フェルマーの小定理型）",
          statement: "すべての整数 n について #{a} | n^#{a} - n",
          latex: "#{a} \\mid n^{#{a}} - n \\quad \\forall n \\in \\mathbb{Z}",
          kind: :divisibility,
          prover: -> { DivisibilityProver.prove(e, a) }
        )
      end

      def false_divisibility(rng)
        m = [5, 7].sample(random: rng)
        e = Polynomial.from([0, -1, 1]) # x^2 - x
        Conjecture.new(
          title: "想像した整除性（要検証）",
          statement: "すべての整数 n について #{m} | n^2 - n",
          latex: "#{m} \\mid n^{2} - n \\quad \\forall n \\in \\mathbb{Z}",
          kind: :divisibility,
          prover: -> { DivisibilityProver.prove(e, m) }
        )
      end

      def open_problem(rng)
        if rng.rand < 0.5
          n = 300 + rng.rand(200)
          Conjecture.new(
            title: "想像した未解決問題（コラッツ型）",
            statement: "1 ≤ k ≤ #{n} のすべての k でコラッツ列は 1 に到達する",
            latex: "\\forall k\\in[1,#{n}]:\\; \\text{Collatz}(k)\\to 1",
            kind: :open,
            prover: lambda {
              EmpiricalTester.test((1..n), description: "コラッツ k∈[1,#{n}]") { |k| NT.collatz_reaches_one?(k) }
            }
          )
        else
          n = 200 + rng.rand(200)
          n += 1 if n.odd?
          Conjecture.new(
            title: "想像した未解決問題（ゴールドバッハ型）",
            statement: "4 ≤ 2m ≤ #{n} のすべての偶数は2素数の和で書ける",
            latex: "\\forall\\,\\text{even } e\\in[4,#{n}]:\\; e=p+q,\\ p,q\\ \\text{prime}",
            kind: :open,
            prover: lambda {
              primes = NT.primes_upto(n).to_set
              EmpiricalTester.test((4..n).step(2).to_a, description: "ゴールドバッハ e∈[4,#{n}]") do |e|
                NT.goldbach_holds?(e, primes)
              end
            }
          )
        end
      end
    end
  end
end
