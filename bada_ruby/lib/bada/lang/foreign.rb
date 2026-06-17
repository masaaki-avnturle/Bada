# frozen_string_literal: true

require "json"
require "open3"

module Bada
  module Lang
    # Foreign-function interface: let Bada `import` Ruby, Python and C libraries.
    #
    #   import "ruby:Math as RMath"     -> RMath.sqrt(2)   (Ruby module/class)
    #   import "python:math as PyMath"  -> PyMath.gcd(12, 8) (Python, via JSON)
    #   import "c:m as LibM"            -> LibM.cos(1.0)    (C shared lib, Fiddle)
    #
    # Each import installs a *dynamic module* whose unknown members are forwarded
    # to the foreign runtime. Values are coerced between Bada and the foreign
    # world (numbers/strings/bools/nil/lists; Ruby/Python hashes -> [k,v] lists).
    #
    # NOTE: this runs foreign code locally (like any FFI). Use with trusted libs.
    module Foreign
      module_function

      # --- value coercion ------------------------------------------------
      def to_bada(v)
        case v
        when Integer, Float, String, TrueClass, FalseClass, NilClass then v
        when Symbol then v.to_s
        when Array then v.map { |e| to_bada(e) }
        when Hash then v.map { |k, val| [to_bada(k), to_bada(val)] }
        else v.to_s
        end
      end

      def from_bada(v)
        case v
        when Directive then v.lanes.map { |x| from_bada(x) }
        when Array then v.map { |x| from_bada(x) }
        else v
        end
      end

      # --- install into an interpreter (import handler) ------------------
      def import_into(interp, scheme, target, alias_name)
        bridge =
          case scheme
          when "ruby" then ruby_module(target)
          when "python" then python_module(target)
          when "c" then c_module(target)
          else raise "Bada: unknown foreign scheme '#{scheme}'"
          end
        interp.register_module(alias_name, "__call__" => bridge)
      end

      # A global `Ruby` module with eval, always available.
      def install(interp)
        interp.register_module("Ruby", "eval" => ->(code) { to_bada(::Kernel.eval(code.to_s)) }) # rubocop:disable Security/Eval
      end

      # --- Ruby bridge ---------------------------------------------------
      def ruby_module(target)
        recv = resolve_ruby(target)
        lambda do |method, args|
          to_bada(recv.public_send(method, *args.map { |a| from_bada(a) }))
        end
      end

      def resolve_ruby(target)
        unless const_path_defined?(target)
          begin
            require target.downcase
          rescue LoadError
            # leave to const_get to raise a clear error
          end
        end
        target.split("::").reduce(Object) { |mod, name| mod.const_get(name) }
      end

      def const_path_defined?(target)
        target.split("::").reduce(Object) do |mod, name|
          return false unless mod.is_a?(Module) && mod.const_defined?(name)
          mod.const_get(name)
        end
        true
      rescue StandardError
        false
      end

      # --- Python bridge (subprocess + JSON) -----------------------------
      PY_DRIVER = <<~PY
        import sys, json, importlib
        p = json.load(sys.stdin)
        mod = importlib.import_module(p["mod"])
        fn = getattr(mod, p["fn"])
        res = fn(*p["args"])
        sys.stdout.write(json.dumps([res]))
      PY

      def python_module(module_name)
        lambda do |method, args|
          payload = JSON.generate("mod" => module_name, "fn" => method,
                                  "args" => args.map { |a| from_bada(a) })
          out, err, st = Open3.capture3("python3", "-c", PY_DRIVER, stdin_data: payload)
          raise "Bada python error (#{module_name}.#{method}): #{err.strip}" unless st.success?
          to_bada(JSON.parse(out).first)
        end
      end

      # --- C bridge (Fiddle / dlopen) ------------------------------------
      def c_module(libname)
        require "fiddle"
        handle = open_c_lib(libname)
        lambda do |method, args|
          nums = args.map { |x| from_bada(x).to_f }
          types = Array.new(nums.length, Fiddle::TYPE_DOUBLE)
          f = Fiddle::Function.new(handle[method], types, Fiddle::TYPE_DOUBLE)
          to_bada(f.call(*nums))
        end
      end

      def open_c_lib(name)
        ["lib#{name}.so.6", "lib#{name}.so", "#{name}.so", name].each do |cand|
          begin
            return Fiddle.dlopen(cand)
          rescue StandardError
            next
          end
        end
        raise "Bada: cannot open C library '#{name}'"
      end
    end
  end
end
