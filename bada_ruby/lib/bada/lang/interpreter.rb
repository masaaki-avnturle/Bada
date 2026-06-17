# frozen_string_literal: true

require_relative "nodes"
require_relative "../special"
require_relative "../manifold"

module Bada
  module Lang
    # Lexical environment.
    class Env
      def initialize(parent = nil)
        @vars = {}
        @parent = parent
      end

      def define(name, value) = (@vars[name] = value)

      def set(name, value)
        e = self
        while e
          return e.instance_variable_get(:@vars)[name] = value if e.has?(name)
          e = e.instance_variable_get(:@parent)
        end
        @vars[name] = value
      end

      def has?(name) = @vars.key?(name)

      def lookup(name)
        e = self
        while e
          v = e.instance_variable_get(:@vars)
          return [true, v[name]] if v.key?(name)
          e = e.instance_variable_get(:@parent)
        end
        [false, nil]
      end
    end

    # A user-defined Bada function (closure).
    Function = Struct.new(:name, :params, :body, :closure)

    # A first-class native callable (a builtin or a bound foreign-module method),
    # so imported Ruby/Python/C functions can be passed directly as directive
    # branch / merge directives.
    NativeFn = Struct.new(:fn, :name) do
      def to_s = "<fn #{name}>"
    end

    # Non-local return.
    class ReturnSignal < StandardError
      attr_reader :value
      def initialize(value) = (@value = value; super("return"))
    end

    # A directive-oriented object: a flow carrying one or more "lanes". The
    # three Bada operators act on it:
    #   <-  代入 (assign)  : load a value into the object
    #   -<  分岐 (branch)  : split lanes through branch directives
    #   >-  合流 (merge)   : join lanes back into one
    class Directive
      attr_accessor :lanes
      def initialize(lanes) = (@lanes = lanes)
      def value = @lanes.length == 1 ? @lanes[0] : @lanes
      def to_s = "<| #{@lanes.join(', ')} |>"
    end

    # Tree-walking interpreter for the Bada language.
    class Interpreter
      include AST

      attr_reader :global, :modules, :output

      def initialize(loader: nil, out: $stdout)
        @global = Env.new
        @natives = {}     # global native functions: name -> proc
        @modules = {}     # module name -> { fn -> Function|proc }
        @loader = loader  # ->(path) returns source string
        @out = out
        @output = []
      end

      def register_native(name, &blk) = (@natives[name] = blk)

      def register_module(mod, fns)
        (@modules[mod] ||= {}).merge!(fns)
      end

      def run(ast)
        last = nil
        ast.stmts.each { |s| last = eval_node(s, @global) }
        last
      rescue ReturnSignal => e
        e.value
      end

      private

      def eval_node(node, env = @global)
        case node
        when Program  then node.stmts.map { |s| eval_node(s, env) }.last
        when Num      then node.value
        when Str      then node.value
        when Bool     then node.value
        when Nil_     then nil
        when ListLit  then node.elems.map { |e| eval_node(e, env) }
        when Ident    then resolve_ident(node.name, env)
        when Assign   then env.set(node.name, eval_node(node.expr, env))
        when Print    then v = eval_node(node.expr, env); line = display(v); @output << line; @out.puts(line); v
        when Return   then raise ReturnSignal.new(node.expr ? eval_node(node.expr, env) : nil)
        when Def      then define_function(node, env); nil
        when Lambda   then Function.new(nil, node.params, node.body, env)
        when Library  then define_library(node); nil
        when Import   then do_import(node.path); nil
        when If       then eval_if(node, env)
        when While    then eval_while(node, env)
        when Unary    then eval_unary(node, env)
        when Binary   then eval_binary(node, env)
        when Call     then eval_call(node, env)
        when Member   then eval_member_value(node, env)
        when ExprStmt then eval_node(node.expr, env)
        else raise "Bada eval error: unknown node #{node.class}"
        end
      end

      def resolve_ident(name, env)
        found, val = env.lookup(name)
        return val if found
        # builtins are first-class: a bare builtin name yields a callable value
        return NativeFn.new(@natives[name], name) if @natives.key?(name)
        raise "Bada: undefined variable '#{name}'"
      end

      def callable?(v) = v.is_a?(Function) || v.is_a?(NativeFn)

      def define_function(node, env)
        fn = Function.new(node.name, node.params, node.body, env)
        env.define(node.name, fn)
        fn
      end

      def define_library(node)
        # A per-library scope so functions can call their siblings by bare name.
        lib_env = Env.new(@global)
        fns = {}
        node.defs.each do |d|
          fn = Function.new(d.name, d.params, d.body, lib_env)
          lib_env.define(d.name, fn)
          fns[d.name] = fn
        end
        register_module(node.name, fns)
      end

      def eval_if(node, env)
        return eval_block(node.then_body, env) if truthy?(eval_node(node.cond, env))
        node.elsifs.each do |(c, b)|
          return eval_block(b, env) if truthy?(eval_node(c, env))
        end
        node.else_body ? eval_block(node.else_body, env) : nil
      end

      def eval_while(node, env)
        last = nil
        last = eval_block(node.body, env) while truthy?(eval_node(node.cond, env))
        last
      end

      def eval_block(stmts, env)
        last = nil
        stmts.each { |s| last = eval_node(s, env) }
        last
      end

      def eval_unary(node, env)
        v = eval_node(node.expr, env)
        case node.op
        when :not then !truthy?(v)
        when :minus then -v
        end
      end

      def eval_binary(node, env)
        return truthy?(eval_node(node.left, env)) ? eval_node(node.right, env) : false if node.op == :and
        return truthy?(eval_node(node.left, env)) || truthy?(eval_node(node.right, env)) if node.op == :or
        l = eval_node(node.left, env)
        r = eval_node(node.right, env)
        case node.op
        when :plus then l.is_a?(String) || r.is_a?(String) ? "#{display(l)}#{display(r)}" : l + r
        when :minus then l - r
        when :star then l * r
        when :slash then l / r
        when :eq then l == r
        when :neq then l != r
        when :lt then l < r
        when :le then l <= r
        when :gt then l > r
        when :ge then l >= r
        when :larrow then directive_assign(l, r)   # 代入オブジェクト
        when :integ  then directive_branch(l, r)    # 分岐オブジェクト
        when :rarrow then directive_merge(l, r)     # 合流オブジェクト
        else raise "Bada: bad operator #{node.op}"
        end
      end

      # ---- directive-oriented object operators ----
      def as_directive(v) = v.is_a?(Directive) ? v : Directive.new([v])

      # <-  代入: load the right value into a directive object (assignment).
      def directive_assign(l, r)
        if l.is_a?(Directive)
          l.lanes = [r]
          l
        else
          Directive.new([r])
        end
      end

      # -<  分岐: split each lane through the branch directive(s).
      #   d -< fn          map every lane through fn
      #   d -< [fn1, fn2]  fan each lane out through every fn (lanes multiply)
      #   d -< [v1, v2]    replace lanes with the explicit branch values
      #   d -< n           duplicate each lane n times
      def directive_branch(l, r)
        d = as_directive(l)
        lanes =
          if callable?(r) # function / builtin / foreign method
            d.lanes.map { |x| call_function(r, [x]) }
          elsif r.is_a?(Array) && !r.empty? && r.all? { |e| callable?(e) }
            d.lanes.flat_map { |x| r.map { |f| call_function(f, [x]) } }
          elsif r.is_a?(Array)
            r.dup
          elsif r.is_a?(Numeric)
            d.lanes.flat_map { |x| Array.new(r.to_i, x) }
          else
            d.lanes.map { |_| r }
          end
        Directive.new(lanes)
      end

      # >-  合流: merge the lanes back into one value via a 2-arg combiner.
      #   d >- fn   reduce lanes with fn(acc, lane); returns the merged value
      #   d >- nil  returns the lanes as a list
      def directive_merge(l, r)
        d = as_directive(l)
        return d.lanes.dup if r.nil?
        raise "Bada: >- needs a 2-arg merge directive" unless callable?(r)
        return nil if d.lanes.empty?
        d.lanes.reduce { |acc, x| call_function(r, [acc, x]) }
      end

      def eval_call(node, env)
        args = node.args.map { |a| eval_node(a, env) }
        callee = node.callee
        if callee.is_a?(Member) && callee.obj.is_a?(Ident) && @modules.key?(callee.obj.name)
          return call_module(callee.obj.name, callee.name, args)
        end
        if callee.is_a?(Ident)
          found, val = env.lookup(callee.name)
          return call_function(val, args) if found && callable?(val)
          return @natives[callee.name].call(*args) if @natives.key?(callee.name)
          raise "Bada: undefined function '#{callee.name}'"
        end
        fnval = eval_node(callee, env)
        return call_function(fnval, args) if callable?(fnval)
        raise "Bada: not callable"
      end

      def call_module(mod, fn, args)
        table = @modules[mod] or raise "Bada: unknown module #{mod}"
        target = table[fn]
        if target.nil?
          # dynamic module (foreign import): forward unknown members
          dyn = table["__call__"]
          return dyn.call(fn, args) if dyn
          raise "Bada: #{mod} has no member #{fn}"
        end
        target.is_a?(Function) ? call_function(target, args) : target.call(*args)
      end

      def call_function(fn, args)
        return fn.fn.call(*args) if fn.is_a?(NativeFn) # builtin / foreign method
        local = Env.new(fn.closure)
        fn.params.each_with_index { |p, i| local.define(p, args[i]) }
        result = nil
        begin
          fn.body.each { |s| result = eval_node(s, local) }
        rescue ReturnSignal => e
          return e.value
        end
        result
      end

      # `Mod.method` without a call yields a first-class bound callable, so an
      # imported foreign method can be used directly as a directive.
      def eval_member_value(node, _env)
        if node.obj.is_a?(Ident) && @modules.key?(node.obj.name)
          mod = node.obj.name
          meth = node.name
          return NativeFn.new(->(*args) { call_module(mod, meth, args) }, "#{mod}.#{meth}")
        end
        raise "Bada: '#{node.name}' on #{node.obj.inspect} is only valid as a call"
      end

      # ---- import ----
      def do_import(path)
        # foreign imports:  import "ruby:Math as M" / "python:math" / "c:m"
        if (m = path.match(/\A(ruby|python|c)\s*:\s*(.+)\z/m))
          scheme = m[1]
          target, al = m[2].split(/\s+as\s+/, 2)
          target = target.strip
          alias_name = (al || default_foreign_alias(target)).strip
          Foreign.import_into(self, scheme, target, alias_name)
          return
        end
        raise "Bada: no loader configured for import" unless @loader
        src = @loader.call(path)
        ast = Bada::Lang::Parser.parse(src)
        ast.stmts.each { |s| eval_node(s, @global) }
      end

      # default Bada alias for a foreign target ("math" -> "Math", "JSON" -> "JSON")
      def default_foreign_alias(target)
        base = target.split(/::|\./).last
        base[0].upcase + base[1..].to_s
      end

      # ---- helpers ----
      def truthy?(v) = !(v.nil? || v == false)

      def display(v)
        case v
        when Float then format_float(v)
        when Array then "[#{v.map { |x| display(x) }.join(', ')}]"
        when Directive then "<| #{v.lanes.map { |x| display(x) }.join(', ')} |>"
        when nil then "nil"
        else v.to_s
        end
      end

      def format_float(f)
        return f.to_s unless f.finite?
        (f == f.round && f.abs < 1e15) ? f.to_i.to_s : format("%.6g", f)
      end
    end

    # Bada operator semantics (shared meaning of <-, -<, >-).
    module Ops
      module_function

      def coerce(v) = v.is_a?(Numeric) ? v.to_f : Bada::Manifold.xi(v.to_s)

      # <-  left non-commutative act  π(χ,x) = [iπ, f(x)]
      def left_act(a, b)
        chi = coerce(b)
        x = coerce(a).abs + 1.0
        (Complex(0, Math::PI) * chi * Math.log(x)).abs
      end

      # -<  manifold integral  ∬ 1/(x log x)^2
      def manifold_integral(a, b)
        s = coerce(b)
        x = s.abs + 2.0
        Bada::Special.x_log_x(x) * Bada::Manifold.element(x) + Bada::Manifold.element(x)
      end

      # >-  quantum right act  e^{-x log x}
      def right_act(a, b)
        o = coerce(b)
        x = o.abs + 1e-6
        Math.exp(-Bada::Special.x_log_x(x))
      end
    end
  end
end
