# frozen_string_literal: true

require_relative "special"
require_relative "manifold"
require_relative "tuplespace"

module Bada
  # The Bada language, rebuilt from scratch on top of Ruby.
  #
  # Bada is an operator-algebra language: programs are sequences of manifold
  # operators acting on values that live in Omega::DATABASE (a TupleSpace).
  # The three core operators come straight from the README / Bada1 report:
  #
  #   <-   left non-commutative act     π(χ,x) = [iπ, f(x)]
  #   -<   manifold integral            ∬ 1/(x log x)^2 dx_m
  #   >-   quantum right act            ⊕(iℏ∇)^⊕L = e^{-x log x}
  #   Ω::  / Omega::                    TupleSpace (Akashic) namespace
  #
  # A BadaNode is the runtime value the operators act on; Interpreter is a small
  # line-oriented evaluator for Bada source.
  class BadaNode
    attr_accessor :value, :history

    def initialize(value = 0.0)
      @value = value
      @history = []
    end

    # <-  left non-commutative act:  π(χ,x) = [iπ(χ,x), f(x)]
    # Implemented as the commutator magnitude of the imaginary generator iπ·χ
    # with f(x)=log x. For a string input χ is its entropy invariant.
    def left_act(input)
      chi = coerce(input)
      x = (@value.abs < 1e-9 ? 1.0 : @value.abs) + 1.0
      pi_chi = Complex(0, Math::PI) * chi
      commutator = (pi_chi * Math.log(x) - Math.log(x) * pi_chi) # = 0 for scalars...
      # non-commutative content carried by the rotation phase:
      result = (pi_chi * Math.log(x)).abs
      @history << [:left_act, input, result]
      @value = result
      self
    end

    # -<  manifold integral on the current state.
    def manifold_integral(state = nil)
      s = state.nil? ? @value : coerce(state)
      x = s.abs + 2.0
      result = Special.x_log_x(x) * Manifold.element(x) + Manifold.element(x)
      @history << [:manifold_integral, state, result]
      @value = result
      self
    end

    # >-  quantum right act:  e^{-x log x}.
    def right_act(output = nil)
      o = output.nil? ? @value : coerce(output)
      x = o.abs + 1e-6
      result = Math.exp(-Special.x_log_x(x))
      @history << [:right_act, output, result]
      @value = result
      self
    end

    def coerce(v)
      case v
      when Numeric then v.to_f
      when String  then Manifold.xi(v)
      when BadaNode then v.value
      else 0.0
      end
    end

    def to_s
      "#<BadaNode value=#{@value}>"
    end
  end

  # Line-oriented interpreter for Bada source.
  #
  #   set g = 3.5            # bind a value
  #   g <- "hello world"     # left act with a string (its manifold invariant)
  #   g -< 2.0               # manifold integral
  #   g >- g                 # quantum right act
  #   Omega::push g as node1 # write to the Akashic TupleSpace
  #   print g                # print a value
  #
  # Comments start with '#'. Strings use double quotes.
  class Interpreter
    attr_reader :env, :db, :output

    def initialize(db: TupleSpace.new)
      @env = {}
      @db = db
      @output = []
    end

    def run(source)
      source.each_line do |raw|
        line = raw.strip.sub(/#.*\z/, "").strip
        next if line.empty?
        exec_line(line)
      end
      @output
    end

    private

    def exec_line(line)
      case line
      when /\Aset\s+(\w+)\s*=\s*(.+)\z/
        @env[$1] = node_for(eval_expr($2))
      when /\A(\w+)\s*<-\s*(.+)\z/
        nodef($1).left_act(eval_expr($2))
      when /\A(\w+)\s*-<\s*(.+)\z/
        nodef($1).manifold_integral(eval_expr($2))
      when /\A(\w+)\s*>-\s*(.+)\z/
        nodef($1).right_act(eval_expr($2))
      when /\A(?:Omega|Ω)::push\s+(\w+)(?:\s+as\s+(\w+))?\z/
        n = nodef($1)
        key = $2
        t = @db.push(n.value.to_s, key: key)
        @output << "Ω::push #{key || t.key} (Xi=#{format('%.4f', n.value)})"
      when /\Aprint\s+(.+)\z/
        v = eval_expr($1)
        s = v.is_a?(BadaNode) ? v.value : v
        @output << s.to_s
      else
        raise "Bada syntax error: #{line.inspect}"
      end
    end

    def nodef(name)
      @env[name] ||= BadaNode.new
    end

    def node_for(v)
      v.is_a?(BadaNode) ? v : BadaNode.new(v.is_a?(Numeric) ? v.to_f : Manifold.xi(v.to_s))
    end

    # Minimal expression evaluator: string literal, number, or identifier.
    def eval_expr(src)
      s = src.strip
      if s =~ /\A"(.*)"\z/
        $1
      elsif s =~ /\A[-+]?\d+(?:\.\d+)?\z/
        s.include?(".") ? s.to_f : s.to_i
      elsif @env.key?(s)
        @env[s]
      else
        s # bare word -> treated as a string token
      end
    end
  end
end
