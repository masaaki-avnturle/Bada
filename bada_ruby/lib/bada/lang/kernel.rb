# frozen_string_literal: true

require_relative "../manifold"
require_relative "../entropy"
require_relative "../special"
require_relative "../info_engine"
require_relative "../prover"
require_relative "../basal"
require_relative "../penrose"
require_relative "../chat"
require_relative "llm"

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
        interp.register_native("keys") { |h| h.is_a?(Hash) ? h.keys : [] }
        interp.register_native("values") { |h| h.is_a?(Hash) ? h.values : [] }
        interp.register_native("contains") { |s, sub| s.to_s.include?(sub.to_s) }
        interp.register_native("upcase") { |s| s.to_s.upcase }
        # p(x): print-and-return alias (locals named `p` still shadow it)
        interp.register_native("p") { |x| interp.print_value(x) }
        interp.register_native("set_at") { |arr, i, v| arr[i.to_i] = v; arr }
        interp.register_native("fill") { |n, v| Array.new(n.to_i, v) }
        interp.register_native("abs") { |x| x.abs }
        interp.register_native("sqrt") { |x| Math.sqrt(x) }
        interp.register_native("log") { |x| Math.log(x) }
        interp.register_native("log2") { |x| Math.log2(x) }
        interp.register_native("exp") { |x| Math.exp(x) }
        interp.register_native("sin") { |x| Math.sin(x) }
        interp.register_native("cos") { |x| Math.cos(x) }
        interp.register_native("tan") { |x| Math.tan(x) }
        interp.register_native("acos") { |x| Math.acos(x.clamp(-1.0, 1.0)) }
        interp.register_native("atan") { |x| Math.atan(x) }
        interp.register_native("atan2") { |y, x| Math.atan2(y, x) }
        interp.register_native("write_file") { |path, content| File.write(path.to_s, content.to_s); true }
        interp.register_native("read_file") { |path| File.exist?(path.to_s) ? File.read(path.to_s, encoding: "UTF-8") : nil }
        interp.register_native("floor") { |x| x.floor }
        interp.register_native("ceil") { |x| x.ceil }
        interp.register_native("pow") { |a, b| a**b }
        interp.register_native("mod") { |a, b| a % b }
        interp.register_native("int") { |x| x.to_i }
        interp.register_native("pi") { Math::PI }
        interp.register_native("euler") { Math::E }
        # directive-oriented objects
        interp.register_native("directive") { |v| Bada::Lang::Directive.new([v]) }
        interp.register_native("lanes") { |d| d.is_a?(Bada::Lang::Directive) ? d.lanes : [d] }
        # the original manifold operator math, kept available as functions
        interp.register_native("left_act") { |a, b| Bada::Lang::Ops.left_act(a, b) }
        interp.register_native("right_act") { |a, b| Bada::Lang::Ops.right_act(a, b) }
        interp.register_native("manifold_integral") { |a, b| Bada::Lang::Ops.manifold_integral(a, b) }
      end

      def install_engine_modules(interp)
        # the ChatGPT branch (分派), reachable from Bada as Chat.ask / Chat.line
        chat = nil # lazily created, shared across calls
        interp.register_module("Chat",
          "ask" => lambda { |q|
            chat ||= Bada::OmegaChat.new
            r = chat.reply(q.to_s)
            "#{r[:theory][:theory]} (Ξ=#{format('%.4f', r[:question_invariant])})"
          },
          "line" => lambda { |q|
            chat ||= Bada::OmegaChat.new
            chat.reply(q.to_s)[:theory][:theory]
          },
          "equation" => lambda { |q|
            chat ||= Bada::OmegaChat.new
            chat.reply(q.to_s)[:equation][:equation]
          },
          "generate" => lambda { |q|
            chat ||= Bada::OmegaChat.new
            chat.reply(q.to_s)[:generated_text][:text]
          },
          # llm(q): reach a *real* LLM API when one is configured in the
          # environment (ANTHROPIC_API_KEY / OPENAI_API_KEY); otherwise fall
          # back gracefully to the local OmegaChat 分派. Always returns text.
          "llm" => lambda { |q|
            answer = Bada::Lang::LLM.ask(q.to_s)
            next answer if answer
            chat ||= Bada::OmegaChat.new
            r = chat.reply(q.to_s)
            "#{r[:theory][:theory]} (Ξ=#{format('%.4f', r[:question_invariant])})"
          },
          # backend(): which engine answers llm() — "anthropic"/"openai"/"local".
          "backend" => lambda { Bada::Lang::LLM.backend&.to_s || "local" },
          "live" => lambda { Bada::Lang::LLM.live? },
          # --- version ladder: downgrade / upgrade the ChatGPT version ----
          "codename" => lambda { Bada::Lang::LLM.codename },      # "Bada XP"
          "version" => lambda { Bada::Lang::LLM.version_label },  # e.g. "ムートス"
          "model" => lambda { Bada::Lang::LLM.current_model || "local" }, # e.g. "claude-opus-4-8"
          "versions" => lambda { Bada::Lang::LLM.ladder },        # the full ladder (ids)
          # downgrade([n]): step to a previous (less capable) version; returns label
          "downgrade" => lambda { |*n| Bada::Lang::LLM.downgrade(n.first || 1)[:label] },
          # upgrade([n]): step back to a newer version; returns label
          "upgrade" => lambda { |*n| Bada::Lang::LLM.upgrade(n.first || 1)[:label] },
          # use(id_or_label): pin a specific version; returns label or "?" if unknown
          "use" => lambda { |v| (e = Bada::Lang::LLM.use(v)) ? e[:label] : "?" },
          "reset" => lambda { Bada::Lang::LLM.reset![:label] },
          "history" => lambda { Bada::Lang::LLM.history },
          "xi" => ->(t) { Bada::Manifold.xi(t.to_s) })

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
        when Hash then "{#{x.map { |k, v| "#{stringify(k)}: #{stringify(v)}" }.join(', ')}}"
        when Bada::Lang::Directive then "<| #{x.lanes.map { |e| stringify(e) }.join(', ')} |>"
        when nil then "nil"
        else x.to_s
        end
      end
    end
  end
end
