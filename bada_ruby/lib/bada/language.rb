# frozen_string_literal: true

require_relative "special"
require_relative "manifold"
require_relative "tuplespace"
require_relative "reviser"
require_relative "engine"
require_relative "quantum"

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

  # Line-oriented interpreter for Bada source, with reviser grammar extension.
  #
  # Core grammar (always available):
  #
  #   set g = 3.5            # bind a value
  #   x := qubit(2)          # bind a value (engine/quantum-friendly form)
  #   g <- "hello world"     # left act with a string (its manifold invariant)
  #   g -< 2.0               # manifold integral
  #   g >- g                 # quantum right act
  #   Omega::push g as node1 # write to the Akashic TupleSpace
  #   print g                # print a value
  #
  # Reviser grammar extension (the @reviser construct made into a grammar
  # transaction, per "Reviser-Extensible Grammars"):
  #
  #   @reviser : grammar {
  #     rule "hadamard" postfix [ 'H' '(' expr ')' ]      => phase_uniform(_1)
  #     rule "measure"  stmt    [ 'Measure' '(' expr ')' ] => commit_measurement(_1)
  #   }
  #   reg := qubit(1)        # |0>
  #   reg := H(reg)          # learned syntax -> phase_uniform(reg)
  #   Measure(reg)           # learned syntax -> commit_measurement(reg)
  #
  # Committed rules become append-only facts in Omega::DATABASE[grammar]; the
  # parser consults them (latest-priority-first, program-order scoped) before
  # its built-in alternatives. The denotation of a rule is an ordinary engine
  # call, so teaching Bada the word `Measure` and teaching it to commit a
  # measurement are the same act.
  #
  # Comments start with '#'. Strings use double quotes.
  class Interpreter
    attr_reader :env, :db, :output, :rules

    def initialize(db: TupleSpace.new, rules: nil)
      @env = {}
      @db = db
      @output = []
      @rules = rules || Reviser::RuleLedger.new(db: TupleSpace.new)
      @scope_seq = @rules.current_seq # rules in scope = committed at/before here
    end

    def run(source)
      lines = source.lines.map { |l| l.sub(/#.*/, "").rstrip }
      i = 0
      while i < lines.length
        raw = lines[i]
        if raw.strip.empty?
          i += 1
          next
        end
        if raw.strip =~ /\A@reviser\s*:\s*grammar\s*\{/
          i = run_reviser_block(lines, i)
        else
          exec_line(raw.strip)
          i += 1
        end
      end
      @output
    end

    private

    # ---- @reviser : grammar { … } -----------------------------------------

    def run_reviser_block(lines, start)
      depth = 0
      body = []
      i = start
      first = true
      while i < lines.length
        line = lines[i]
        if first
          line = line.sub(/\A.*?\{/, "")
          first = false
        end
        # track brace depth to find the matching close
        open = line.count("{")
        close = line.count("}")
        if close.positive? && depth + open - close < 0
          # closing brace is on this line; keep text before it
          body << line[0...line.rindex("}")]
          depth = -1
          i += 1
          break
        end
        depth += open - close
        body << line
        i += 1
        break if depth.negative?
      end
      committed = Reviser.parse_and_commit(body.join("\n"), @rules)
      @scope_seq = @rules.current_seq
      committed.each do |r|
        @output << "@reviser: learned rule '#{r.name}' (#{r.head}) => #{r.denotation}"
      end
      i
    end

    # ---- statements --------------------------------------------------------

    def exec_line(line)
      case line
      when /\Aset\s+(\w+)\s*=\s*(.+)\z/
        @env[$1] = node_for(eval_expr($2))
      when /\A(\w+)\s*:=\s*(.+)\z/
        @env[$1] = eval_expr($2)
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
      when /\Aprint\s*\((.*)\)\z/
        @output << split_args($1).map { |a| display(eval_expr(a)) }.join(" ")
      when /\Aprint\s+(.+)\z/
        @output << display(eval_expr($1))
      else
        # before failing, consult the rule ledger for an stmt-head extension.
        result = try_extended(line, %i[stmt])
        raise "Bada syntax error: #{line.inspect}" if result.equal?(NO_MATCH)
      end
    end

    NO_MATCH = Object.new

    # Try to parse `text` against committed rules of the given heads; on a
    # match, elaborate the rule's denotation and evaluate it.
    def try_extended(text, heads)
      toks = tokenize(text)
      heads.each do |head|
        @rules.rules_for(head, up_to_seq: @scope_seq).each do |rule|
          caps = match_pattern(rule.pattern, toks)
          next unless caps
          return eval_expr(rule.elaborate(caps))
        end
      end
      NO_MATCH
    end

    def nodef(name)
      v = @env[name]
      return v if v.is_a?(BadaNode)
      @env[name] = BadaNode.new
    end

    def node_for(v)
      v.is_a?(BadaNode) ? v : BadaNode.new(v.is_a?(Numeric) ? v.to_f : Manifold.xi(v.to_s))
    end

    def display(v)
      case v
      when BadaNode then v.value.to_s
      when Array then "[#{v.map { |e| e.is_a?(Float) ? format('%.5f', e) : e }.join(', ')}]"
      when Quantum::Register then "qubit(#{v.n}) a=#{display(v.probabilities)}"
      when Hash then v.to_s
      else v.to_s
      end
    end

    # ---- expression evaluation --------------------------------------------

    # string literal, number, identifier, builtin call, or learned (expr/
    # postfix) syntax.
    def eval_expr(src)
      s = src.strip
      if s =~ /\A"(.*)"\z/
        $1
      elsif s =~ /\A[-+]?\d+(?:\.\d+)?\z/
        s.include?(".") ? s.to_f : s.to_i
      elsif s =~ /\A(\w+)\s*\((.*)\)\z/ && balanced?($2)
        name = $1
        args = split_args($2).map { |a| eval_expr(a) }
        BUILTINS.include?(name) ? call_builtin(name, args) : extended_expr(s)
      elsif @env.key?(s)
        @env[s]
      else
        ext = try_extended(s, %i[expr postfix])
        ext.equal?(NO_MATCH) ? s : ext
      end
    end

    def extended_expr(s)
      ext = try_extended(s, %i[expr postfix])
      ext.equal?(NO_MATCH) ? s : ext
    end

    # The engine/quantum builtins that rule denotations elaborate to. The
    # surface words (H, CNOT, Measure, …) are NOT builtins: they only work once
    # a @reviser block has taught the grammar a rule whose denotation is one of
    # these calls. Teaching Bada `Measure` and teaching it to commit a
    # measurement are the same act.
    BUILTINS = %w[
      qubit phase_uniform hadamard pauli_x pauli_z cnot
      commit_measurement measure unknown_prior entropy
    ].freeze

    def call_builtin(name, args)
      case name
      when "qubit"
        Quantum.qubit(args[0] ? args[0].to_i : 1)
      when "phase_uniform", "hadamard"
        # H on qubit 0 (the paper's "uniform a + one phase module").
        reg = args[0]; reg.h(args[1] ? args[1].to_i : 0); reg
      when "pauli_x"
        reg = args[0]; reg.x(args[1] ? args[1].to_i : 0); reg
      when "pauli_z"
        reg = args[0]; reg.z(args[1] ? args[1].to_i : 0); reg
      when "cnot"
        reg = args[0]; reg.cnot(args[1] ? args[1].to_i : 0, args[2] ? args[2].to_i : 1); reg
      when "commit_measurement", "measure"
        r = Quantum.measure(args[0], ledger: @db)
        @output << "Measure -> P=#{display(r[:probabilities])} (committed #{r[:committed]} fact, forbidden=#{r[:forbidden].inspect})"
        r[:probabilities]
      when "unknown_prior"
        Engine.unknown_prior(args[0].to_i)
      when "entropy"
        Engine.entropy_of(args[0])
      end
    end

    # ---- tokenizer + pattern matcher (the "parser as rule reader") ---------

    def tokenize(text)
      text.scan(/"[^"]*"|[A-Za-z_]\w*|\d+(?:\.\d+)?|[()\[\],]|\S/)
    end

    # Match a rule pattern (array of {lit:}/{hole:}) against input tokens.
    # Returns the captured fragments (one per hole) or nil. An `expr` hole
    # captures balanced tokens up to the next literal in the pattern.
    def match_pattern(pattern, toks)
      caps = []
      ti = 0
      pi = 0
      while pi < pattern.length
        pat = pattern[pi]
        if pat[:lit]
          return nil if ti >= toks.length || toks[ti] != pat[:lit]
          ti += 1
        else # a hole: capture up to the next literal (balanced on parens)
          nextlit = pattern[pi + 1] && pattern[pi + 1][:lit]
          depth = 0
          frag = []
          while ti < toks.length
            tk = toks[ti]
            break if depth.zero? && nextlit && tk == nextlit
            depth += 1 if tk == "("
            depth -= 1 if tk == ")"
            frag << tk
            ti += 1
          end
          return nil if frag.empty?
          caps << join_tokens(frag)
        end
        pi += 1
      end
      ti == toks.length ? caps : nil
    end

    def join_tokens(toks)
      out = +""
      toks.each_with_index do |t, i|
        prev = toks[i - 1] if i.positive?
        sep = if i.zero?
                ""
              elsif %w[( ) , ].include?(t) || %w[(].include?(prev)
                ""
              elsif prev == ")" || t == "("
                ""
              else
                " "
              end
        out << sep << t
      end
      out.gsub(/\s*\(\s*/, "(").gsub(/\s*\)\s*/, ")").gsub(/\s*,\s*/, ", ").strip
    end

    def split_args(text)
      args = []
      depth = 0
      buf = +""
      text.each_char do |c|
        case c
        when "(", "[" then depth += 1; buf << c
        when ")", "]" then depth -= 1; buf << c
        when ","
          if depth.zero?
            args << buf.strip
            buf = +""
          else
            buf << c
          end
        else buf << c
        end
      end
      args << buf.strip unless buf.strip.empty?
      args
    end

    def balanced?(text)
      depth = 0
      text.each_char do |c|
        depth += 1 if c == "("
        depth -= 1 if c == ")"
        return false if depth.negative?
      end
      depth.zero?
    end
  end
end
