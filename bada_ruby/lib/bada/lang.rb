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
      interp
    end

    def run(source, base_dir: nil, out: $stdout)
      interp = interpreter(base_dir: base_dir, out: out)
      interp.run(Parser.parse(source))
      interp
    end

    def run_file(path, out: $stdout)
      src = File.read(path, encoding: "UTF-8")
      run(src, base_dir: File.dirname(File.expand_path(path)), out: out)
    end
  end
end
