# frozen_string_literal: true

# Bada::Lang — the Bada scripting language: lexer + Pratt parser + tree-walking
# interpreter, with user functions, libraries (modules), `import`, and a native
# bridge (Kernel) to the underlying engines. The Bada *libraries* and the Bada
# *application* live in the bada/ directory as .bada source.
#
#   Bada::Lang.run_file("bada/app/unknown_engine.bada")

require_relative "lang/lexer"
require_relative "lang/nodes"
require_relative "lang/parser"
require_relative "lang/interpreter"
require_relative "lang/kernel"
require_relative "lang/foreign"
require_relative "lang/dialect"
require_relative "lang/reviser"

module Bada
  module Lang
    module_function

    # Default library search root (where the .bada libraries live).
    def library_root
      File.expand_path("../../bada", __dir__)
    end

    # Build an interpreter with the kernel installed and an import loader that
    # resolves paths relative to `base_dir` then the library root.
    def interpreter(base_dir: nil, out: $stdout)
      search = [base_dir, library_root].compact
      loader = lambda do |path|
        file = search.map { |d| File.expand_path(path, d) }.find { |f| File.file?(f) }
        file ||= File.expand_path(path, Dir.pwd)
        raise "Bada import: cannot find #{path}" unless File.file?(file)
        File.read(file, encoding: "UTF-8")
      end
      interp = Interpreter.new(loader: loader, out: out)
      Kernel.install(interp)
      Foreign.install(interp)
      interp
    end

    # Run a program in a given dialect (defaults to the base language). The
    # dialect supplies the keyword-alias map, a builtin overlay and a prelude,
    # so language variants run with their own syntax/semantics.
    def run(source, base_dir: nil, out: $stdout, dialect: Dialect.base)
      interp = interpreter(base_dir: base_dir, out: out)
      dialect.builtins.each { |name, callable| interp.register_native(name, &callable) }
      dialect.foreign.each { |scheme, target, al| Foreign.import_into(interp, scheme, target, al) }
      km = dialect.keyword_map
      pre = dialect.full_prelude
      interp.run(Parser.parse(pre, keyword_map: km)) unless pre.strip.empty?
      interp.run(Parser.parse(source, keyword_map: km))
      interp
    end

    def run_file(path, out: $stdout, dialect: Dialect.base)
      src = File.read(path, encoding: "UTF-8")
      run(src, base_dir: File.dirname(File.expand_path(path)), out: out, dialect: dialect)
    end

    # Fork a new language variant (亜種). See Bada::Lang::Reviser.
    def fork(name:, parent: Dialect.base, &block)
      Reviser.fork(name: name, parent: parent, &block)
    end
  end
end
