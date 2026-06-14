# frozen_string_literal: true

require_relative "../manifold"
require_relative "../entropy"
require_relative "../special"
require_relative "../info_engine"
require_relative "../prover"
require_relative "../basal"
require_relative "../penrose"

module Bada
  module Lang
    # Kernel: registers the native (Ruby) bridge into a Bada interpreter so Bada
    # libraries can reach the underlying engines. This is the foreign-function
    # layer the .bada libraries are built on.
    module Kernel
      module_function

      def install(interp)
        install_globals(interp)
        install_engine_modules(interp)
        interp
      end

      def install_globals(interp)
        interp.register_native("str") { |x| stringify(x) }
        interp.register_native("len") { |x| x.respond_to?(:length) ? x.length : 0 }
        interp.register_native("round") { |x, n = 0| n.to_i.zero? ? x.round : x.round(n.to_i) }
        interp.register_native("range") { |n| (0...n.to_i).to_a }
        interp.register_native("push") { |arr, x| arr << x; arr }
        interp.register_native("at") { |arr, i| arr[i.to_i] }
        interp.register_native("abs") { |x| x.abs }
        interp.register_native("sqrt") { |x| Math.sqrt(x) }
        interp.register_native("log") { |x| Math.log(x) }
      end

      def install_engine_modules(interp)
        interp.register_module("Manifold",
          "xi" => ->(t) { Bada::Manifold.xi(t.to_s) },
          "entropy" => ->(t) { Bada::Entropy.of(t.to_s) },
          "perelman" => ->(t) { Bada::Manifold.invariant(t.to_s)[:manifold_integral] })

        interp.register_module("Entropy",
          "of" => ->(t) { Bada::Entropy.of(t.to_s) })

        interp.register_module("Special",
          "gamma" => ->(x) { Bada::Special.gamma(x) },
          "beta" => ->(p, q) { Bada::Special.beta(p, q) },
          "zeta_gauge" => ->(p, q, x) { Bada::Special.zeta_gauge(p, q, x) })

        interp.register_module("Info",
          "render" => ->(q) { Bada::InfoEngine.new.render(q.to_s) })

        interp.register_module("Prover",
          "render" => ->(q, n = 5) { Bada::Prover::Engine.new.render(q.to_s, count: n.to_i) },
          "count" => ->(q, n = 5) { Bada::Prover::Engine.new.imagine(q.to_s, count: n.to_i).length })

        interp.register_module("Basal",
          "deliberate" => ->(q, n = 5) { Bada::Basal::AprioriEngine.new(seed: 42).render(q.to_s, count: n.to_i) },
          "select" => lambda { |*sal|
            sys = Bada::Basal::BodyNeuralSystem.new(channels: sal.length, gate: :argmax)
            sys.select(sal.each_with_index.map { |s, i| [i, s] })
          })

        interp.register_module("Penrose",
          "compute" => lambda { |drawing|
            d = Bada::Penrose::Canvas.parse(drawing.to_s)
            Bada::Penrose::Evaluator.evaluate(d)[:einsum]
          })
      end

      def stringify(x)
        case x
        when Float then (x == x.round && x.abs < 1e15) ? x.to_i.to_s : format("%.6g", x)
        when Array then "[#{x.map { |e| stringify(e) }.join(', ')}]"
        when nil then "nil"
        else x.to_s
        end
      end
    end
  end
end
