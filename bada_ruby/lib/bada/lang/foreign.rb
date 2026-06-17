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

      # Global helper modules, always available:
      #   Ruby.eval("expr")
      #   Python.call("math", "isclose", [100, 101], [["rel_tol", 0.02]])  # kwargs
      #   C.call("c", "strlen", "int", ["string"], ["hello"])              # typed
      def install(interp)
        interp.register_module("Ruby", "eval" => ->(code) { to_bada(::Kernel.eval(code.to_s)) }) # rubocop:disable Security/Eval
        interp.register_module("Python",
          "call" => ->(mod, fn, args, kwargs = []) { python_call(mod, fn, args, kwargs) })
        interp.register_module("C",
          "call" => ->(lib, fn, ret, argtypes, args) { c_call(lib, fn, ret, argtypes, args) })
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
        kwargs = dict(p.get("kwargs", []))
        res = fn(*p["args"], **kwargs)
        sys.stdout.write(json.dumps([res]))
      PY

      def run_python(module_name, fn, args, kwargs)
        payload = JSON.generate("mod" => module_name.to_s, "fn" => fn.to_s,
                                "args" => from_bada(args), "kwargs" => from_bada(kwargs))
        out, err, st = Open3.capture3("python3", "-c", PY_DRIVER, stdin_data: payload)
        raise "Bada python error (#{module_name}.#{fn}): #{err.strip}" unless st.success?
        to_bada(JSON.parse(out).first)
      end

      def python_module(module_name)
        ->(method, args) { run_python(module_name, method, args, []) }
      end

      # Python.call with positional + keyword arguments ([[key, value], ...]).
      def python_call(module_name, fn, args, kwargs = [])
        run_python(module_name, fn, args, kwargs)
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
        @c_cache ||= {}
        return @c_cache[name] if @c_cache.key?(name)
        ["lib#{name}.so.6", "lib#{name}.so", "#{name}.so", name].each do |cand|
          begin
            return @c_cache[name] = Fiddle.dlopen(cand)
          rescue StandardError
            next
          end
        end
        raise "Bada: cannot open C library '#{name}'"
      end

      # Typed C call: C.call("c", "strlen", "int", ["string"], ["hello"]) -> 5.
      # Types: "double"/"float", "int"/"long", "string"/"char*", "void".
      def c_call(lib, fn, ret, argtypes, args)
        require "fiddle"
        handle = open_c_lib(lib.to_s)
        ftypes = argtypes.map { |t| fiddle_type(t) }
        f = Fiddle::Function.new(handle[fn.to_s], ftypes, fiddle_type(ret))
        cargs = args.each_with_index.map { |a, i| coerce_c_arg(a, argtypes[i]) }
        coerce_c_ret(f.call(*cargs), ret)
      end

      def fiddle_type(t)
        case t.to_s
        when "double", "float" then Fiddle::TYPE_DOUBLE
        when "int", "long" then Fiddle::TYPE_LONG
        when "string", "char*", "voidp" then Fiddle::TYPE_VOIDP
        when "void" then Fiddle::TYPE_VOID
        else raise "Bada: unknown C type '#{t}'"
        end
      end

      def coerce_c_arg(a, t)
        case t.to_s
        when "double", "float" then from_bada(a).to_f
        when "int", "long" then from_bada(a).to_i
        when "string", "char*", "voidp" then from_bada(a).to_s
        else from_bada(a)
        end
      end

      def coerce_c_ret(res, ret)
        case ret.to_s
        when "double", "float" then res.to_f
        when "int", "long" then res.to_i
        when "string", "char*"
          addr = res.respond_to?(:to_i) ? res.to_i : res
          addr.zero? ? nil : Fiddle::Pointer.new(addr).to_s.force_encoding("UTF-8")
        when "void" then nil
        else to_bada(res)
        end
      end
    end
  end
end
