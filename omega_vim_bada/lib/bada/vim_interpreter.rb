# frozen_string_literal: true

require "bada"
require "bada/omega_vim"
require "bada/code_fix"

module Bada
  # VimInterpreter — the Bada language, extended with an editor sublanguage so
  # that the Ω-Vim editor is itself written *in a Bada program* (src/omega_vim.bada).
  #
  # It keeps every base Bada statement (set / <- / -< / >- / print / Omega::push)
  # and adds editor statements built in the same operator-algebra spirit:
  #
  #   keymap vim                       # load the classic vi/vim modal keymap
  #   bind normal "=" -> integrable_fix
  #   buffer main = open "file.py"     # load a buffer (Omega::arg = launch arg)
  #   buffer scratch = text "hello"
  #   main -< integrable_fix           # manifold-integral operator = close the
  #                                    #   delimiter rotation orbit (the code fix)
  #   fix main                         # same, as a statement
  #   Omega::vim main                  # launch the editor loop on a buffer
  #   Omega::push main as saved        # record buffer Ξ to the Akashic TupleSpace
  #
  # The `-<` operator is reused deliberately: the manifold integral is the
  # closed-orbit average of the complex rotational body, which is exactly what
  # the spinning-top code fix computes.
  class VimInterpreter < Interpreter
    attr_reader :buffers, :editor_config

    # opts:
    #   arg:       the file path passed on the command line (Omega::arg)
    #   headless:  run editors from a scripted key string instead of a TTY
    #   script:    the key script used when headless
    #   out:       output IO for the editor (defaults to $stdout)
    def initialize(arg: nil, headless: false, script: "", out: $stdout, **kw)
      super(**kw)
      @arg = arg
      @headless = headless
      @script = script
      @out = out
      @buffers = {}
      @editor_config = { keymap: :vim, binds: [] }
      @last_editor = nil
    end

    def last_editor
      @last_editor
    end

    def buffer(name)
      @buffers[name]
    end

    private

    # Override the line executor: try editor statements first, else fall back
    # to the base Bada interpreter.
    def exec_line(line)
      case line
      when /\Akeymap\s+(\w+)\z/
        @editor_config[:keymap] = $1.to_sym
        @output << "keymap: #{$1}"
      when /\Abind\s+(\w+)\s+"(.*)"\s*->\s*(\w+)\z/
        @editor_config[:binds] << { mode: $1.to_sym, key: unescape($2), action: $3.to_sym }
        @output << "bind #{$1} #{$2.inspect} -> #{$3}"
      when /\Abuffer\s+(\w+)\s*=\s*open\s+(.+)\z/
        path = resolve_path(eval_expr($2))
        @buffers[$1] = OmegaVim::Buffer.open(path)
        @output << "buffer #{$1} = open #{path} (#{@buffers[$1].lines.length} lines)"
      when /\Abuffer\s+(\w+)\s*=\s*text\s+(.+)\z/
        txt = eval_expr($2)
        txt = txt.value if txt.is_a?(BadaNode)
        @buffers[$1] = OmegaVim::Buffer.new(txt.to_s)
        @output << "buffer #{$1} = text (#{@buffers[$1].lines.length} lines)"
      when /\Afix\s+(\w+)\z/
        do_fix($1)
      when /\A(\w+)\s*-<\s*integrable_fix\z/
        # the manifold-integral operator, specialised to close the code orbit
        do_fix($1)
      when /\A(?:Omega|Ω)::vim\s+(\w+)\z/
        launch_editor($1)
      when /\A(?:Omega|Ω)::push\s+(\w+)\s+as\s+(\w+)\z/
        if (buf = @buffers[$1])
          xi = Manifold.xi(buf.text)
          @db.push(xi.to_s, key: $2)
          @output << "Ω::push #{$2} (buffer Ξ=#{format('%.4f', xi)})"
        else
          super
        end
      else
        super
      end
    end

    def do_fix(name)
      buf = @buffers[name] or (@output << "no such buffer: #{name}"; return)
      res = Bada::CodeFix.fix(buf.text, filename: buf.filename)
      buf.replace_source!(res[:source]) if res[:changed]
      if res[:changed]
        @output << "fix #{name}: ∮ orbit closed, #{res[:applied].length} change(s), " \
                   "Ξ #{res[:invariant_conserved] ? 'conserved' : 'DRIFT'} " \
                   "(#{format('%.4f', res[:certified_invariant])})"
        res[:applied].each { |a| @output << "  * #{a}" }
      else
        @output << "fix #{name}: orbit already closed (no structural errors)"
      end
      res
    end

    def launch_editor(name)
      buf = @buffers[name] or (@output << "no such buffer: #{name}"; return)
      ed = OmegaVim::Editor.new(buf, out: @out)
      # apply Bada-defined key bindings that map to editor actions
      apply_binds(ed)
      @last_editor = ed
      if @headless
        ed.run_script(@script)
        @output << "Ω::vim #{name} (headless: ran #{@script.length}-key script)"
        @output << "final buffer:\n#{buf.text}"
      else
        ed.run_interactive
        @output << "Ω::vim #{name} closed"
      end
      ed
    end

    # The Bada `bind` statements are advisory for the default vim keymap (which
    # the editor already implements); the one binding that matters — attaching
    # the integrable fix to '=' and ':fix' — is native. We surface any custom
    # bind that names integrable_fix so the program reads as the source of truth.
    def apply_binds(_ed)
      @editor_config[:binds].each do |b|
        next unless b[:action] == :integrable_fix
        # '=' and ':fix' already invoke CodeFix in the editor; nothing to patch.
      end
    end

    def resolve_path(v)
      v = v.value if v.is_a?(BadaNode)
      s = v.to_s
      s
    end

    def unescape(s)
      s.gsub("\\e", "\e").gsub("\\t", "\t").gsub("\\\\", "\\")
    end

    # Extend the base expression evaluator with Omega::arg.
    def eval_expr(src)
      s = src.strip
      return (@arg || "") if s == "Omega::arg" || s == "Ω::arg"
      super
    end
  end
end
