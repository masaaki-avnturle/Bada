# frozen_string_literal: true

require_relative "synth"

module Bada
  module Coder
    # Recipes — goal → complete program. Given a one-line goal ("fibonacci",
    # "FizzBuzz", "素数判定", "並べ替え"…) this builds a full working program as a
    # Synth AST, which the existing emitters turn into original source in any of
    # the six target languages. The programs are generated from the AST, not
    # pasted from language-specific templates.
    module Recipes
      module_function

      # --- AST builders ---
      def num(n) = [:num, n]
      def st(x)  = [:str, x]
      def var(n) = [:var, n]
      def bn(op, l, r) = [:bin, op, l, r]
      def cl(name, *a) = [:call, name, a]
      def ix(name, e)  = [:idx, name, e]
      def asg(n, e)    = [:assign, n, e]
      def adecl(n, elems) = [:arrdecl, n, elems]
      def iset(n, i, e)   = [:idxset, n, i, e]
      def pr(e)  = [:print, e]
      def ret(e) = [:return, e]
      def forr(v, a, b, *body) = [:for, v, a, b, body]
      def whl(c, *body) = [:while, c, body]
      def iff(c, thn, els = []) = [:if, c, thn, els]
      def func(name, params, *body) = [:func, name, params, body]

      def program(name, *items)
        prog = { name: name, items: items }
        Synth.resolve!(prog)
        Synth.asciify_names!(prog)
        prog
      end

      # Resolve a goal to a complete program, or nil if no recipe matches.
      def for(goal)
        g = goal.to_s
        gl = g.downcase
        nums = g.scan(/\d+/).map(&:to_i)

        return fizzbuzz(nums.first || 20)             if gl.match?(/fizz\s*buzz/) || g.match?(/フィズ\s*バズ|フィズバズ/)
        return fibonacci(nums.first || 10)            if gl.include?("fib") || g.match?(/フィボ/)
        return factorial(nums.first || 5)             if gl.include?("factorial") || g.match?(/階乗|ファクトリアル/)
        return prime(nums.first || 29)                if gl.match?(/\bprime\b|is[- ]?prime/) || g.match?(/素数/)
        return gcd(nums[0] || 48, nums[1] || 36)      if gl.match?(/\bgcd\b|greatest common/) || g.match?(/最大公約数/)
        return power(nums[0] || 2, nums[1] || 10)     if gl.match?(/\bpower\b|exponent/) || g.match?(/べき乗|累乗/)
        return mult_table(nums.first || 9)            if gl.match?(/multiplication table|times table/) || g.match?(/九九|掛け算表|かけ算表/)
        return bubble_sort(nums.length >= 2 ? nums : [5, 2, 9, 1, 7, 3]) if gl.match?(/\bsort\b|bubble/) || g.match?(/並べ替|並び替|ソート/)
        return sum_to_n(nums.first || 100)            if gl.match?(/\bsum\b/) || g.match?(/合計|総和/)

        nil
      end

      def names
        %w[fibonacci fizzbuzz factorial prime gcd power multiplication-table bubble-sort sum]
      end

      # --- the recipes (each returns a complete Synth program) ---

      def factorial(n)
        program("Factorial",
                func("factorial", ["n"],
                     asg("result", num(1)),
                     forr("i", num(1), var("n"), asg("result", bn("*", var("result"), var("i")))),
                     ret(var("result"))),
                pr(cl("factorial", num(n))))
      end

      def fibonacci(n)
        program("Fibonacci",
                func("fib", ["n"],
                     asg("a", num(0)),
                     asg("b", num(1)),
                     forr("i", num(1), var("n"),
                          pr(var("a")),
                          asg("t", bn("+", var("a"), var("b"))),
                          asg("a", var("b")),
                          asg("b", var("t")))),
                [:expr, cl("fib", num(n))])
      end

      def fizzbuzz(n)
        program("FizzBuzz",
                forr("i", num(1), num(n),
                     iff(bn("==", bn("%", var("i"), num(15)), num(0)),
                         [pr(st("FizzBuzz"))],
                         [iff(bn("==", bn("%", var("i"), num(3)), num(0)),
                              [pr(st("Fizz"))],
                              [iff(bn("==", bn("%", var("i"), num(5)), num(0)),
                                   [pr(st("Buzz"))],
                                   [pr(var("i"))])])])))
      end

      def prime(n)
        program("Prime",
                func("is_prime", ["n"],
                     iff(bn("<", var("n"), num(2)), [ret(num(0))]),
                     asg("i", num(2)),
                     whl(bn("<=", bn("*", var("i"), var("i")), var("n")),
                         iff(bn("==", bn("%", var("n"), var("i")), num(0)), [ret(num(0))]),
                         asg("i", bn("+", var("i"), num(1)))),
                     ret(num(1))),
                pr(cl("is_prime", num(n))))
      end

      def gcd(a, b)
        program("Gcd",
                func("gcd", %w[a b],
                     whl(bn("!=", var("b"), num(0)),
                         asg("t", var("b")),
                         asg("b", bn("%", var("a"), var("b"))),
                         asg("a", var("t"))),
                     ret(var("a"))),
                pr(cl("gcd", num(a), num(b))))
      end

      def power(base, exp)
        program("Power",
                func("power", %w[base exp],
                     asg("result", num(1)),
                     forr("i", num(1), var("exp"), asg("result", bn("*", var("result"), var("base")))),
                     ret(var("result"))),
                pr(cl("power", num(base), num(exp))))
      end

      def mult_table(n)
        program("MultiplicationTable",
                forr("i", num(1), num(n),
                     forr("j", num(1), num(n),
                          pr(bn("*", var("i"), var("j"))))))
      end

      def sum_to_n(n)
        program("Sum",
                func("sum_to", ["n"],
                     asg("total", num(0)),
                     forr("i", num(1), var("n"), asg("total", bn("+", var("total"), var("i")))),
                     ret(var("total"))),
                pr(cl("sum_to", num(n))))
      end

      def bubble_sort(list)
        list = list.first(64)
        n = list.length
        program("BubbleSort",
                adecl("a", list.map { |x| num(x) }),
                forr("i", num(0), num(n - 1),
                     forr("j", num(0), num(n - 2),
                          iff(bn(">", ix("a", var("j")), ix("a", bn("+", var("j"), num(1)))),
                              [asg("t", ix("a", var("j"))),
                               iset("a", var("j"), ix("a", bn("+", var("j"), num(1)))),
                               iset("a", bn("+", var("j"), num(1)), var("t"))]))),
                forr("k", num(0), num(n - 1), pr(ix("a", var("k")))))
      end
    end
  end
end
