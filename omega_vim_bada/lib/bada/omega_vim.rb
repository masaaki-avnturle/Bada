# frozen_string_literal: true

require "bada/code_fix"
require "bada/grammar"

module Bada
  # OmegaVim — a modal (vi/vim-style) text editor that is part of the Bada
  # language runtime. The editor itself is defined here (the host of the Bada
  # language is Ruby, exactly as Bada::NN / Bada::Penrose are); the *editor is
  # configured and launched from a Bada-language program* (see src/omega_vim.bada
  # and Bada::VimInterpreter).
  #
  # Its headline feature is `=` / `:fix` — source-code error correction for any
  # programming language via Bada::CodeFix, i.e. the complex-rotation
  # spinning-top integrable system of special relativity: it closes the
  # delimiter "rotation orbit" of the buffer while conserving the Ξ invariant.
  module OmegaVim
    # A text buffer: lines, cursor, filename, dirty flag.
    class Buffer
      attr_accessor :lines, :filename, :dirty, :row, :col

      def initialize(text = "", filename: nil)
        @lines = text.empty? ? [""] : text.split("\n", -1)
        @lines = [""] if @lines.empty?
        @filename = filename
        @dirty = false
        @row = 0
        @col = 0
      end

      def self.open(path)
        text = File.exist?(path) ? File.read(path) : ""
        buf = new(text, filename: path)
        buf.dirty = false
        buf
      end

      def text
        @lines.join("\n")
      end

      def line
        @lines[@row] || ""
      end

      def save(path = nil)
        path ||= @filename
        raise "no filename" unless path
        File.write(path, text)
        @filename = path
        @dirty = false
        path
      end

      def clamp!
        @row = 0 if @row < 0
        @row = @lines.length - 1 if @row > @lines.length - 1
        @col = 0 if @col < 0
        maxc = [line.length, 0].max
        @col = maxc if @col > maxc
      end

      # ---- editing primitives ----
      def insert_char(ch)
        l = line.dup
        l.insert(@col, ch)
        @lines[@row] = l
        @col += 1
        @dirty = true
      end

      def newline
        cur = line
        head = cur[0...@col]
        tail = cur[@col..] || ""
        @lines[@row] = head
        @lines.insert(@row + 1, tail)
        @row += 1
        @col = 0
        @dirty = true
      end

      def backspace
        if @col > 0
          l = line.dup
          l.slice!(@col - 1)
          @lines[@row] = l
          @col -= 1
          @dirty = true
        elsif @row > 0
          prev = @lines[@row - 1]
          @col = prev.length
          @lines[@row - 1] = prev + line
          @lines.delete_at(@row)
          @row -= 1
          @dirty = true
        end
      end

      def delete_char # 'x'
        l = line.dup
        return if l.empty?
        l.slice!(@col) if @col < l.length
        @lines[@row] = l
        @col = [@col, [l.length - 1, 0].max].min
        @dirty = true
      end

      def delete_line # 'dd'
        removed = @lines.delete_at(@row) || ""
        @lines = [""] if @lines.empty?
        @row = [@row, @lines.length - 1].min
        @col = 0
        @dirty = true
        removed
      end

      def open_below # 'o'
        @lines.insert(@row + 1, "")
        @row += 1
        @col = 0
        @dirty = true
      end

      def open_above # 'O'
        @lines.insert(@row, "")
        @col = 0
        @dirty = true
      end

      def join_lines # 'J'
        return if @row >= @lines.length - 1
        @col = line.length
        @lines[@row] = line + (@lines[@row + 1] || "")
        @lines.delete_at(@row + 1)
        @dirty = true
      end

      def replace_source!(new_text)
        @lines = new_text.split("\n", -1)
        @lines = [""] if @lines.empty?
        clamp!
        @dirty = true
      end
    end

    # The modal editor. Interactive by default; pass keys:/headless: for tests.
    class Editor
      MODES = %i[normal insert command].freeze

      attr_reader :buffer, :mode, :message, :lang

      def initialize(buffer, out: $stdout, rows: nil, cols: nil, lang: nil, indent: nil)
        @buffer = buffer
        @out = out
        @mode = :normal
        @message = "Ω-Vim — Bada language editor.  :help  :fix  :check  :indent  Tab=complete"
        @command = ""
        @pending = ""          # multi-key normal command (e.g. 'gg', 'dd')
        @quit = false
        @rows = rows
        @cols = cols
        @last_fix = nil
        @last_check = nil
        # grammar / indent configuration
        @lang = lang || Bada::Grammar.for_filename(buffer.filename)
        @indent_width = indent || Bada::Grammar.indent_width(@lang)
        @grammar_on = true
      end

      # accessors for tests / .bada reporting
      attr_reader :last_check, :indent_width
      def grammar_on?; @grammar_on; end
      def grammar!(on); @grammar_on = on; end
      def indent_width=(n); @indent_width = n; end
      def lang=(l); @lang = l; @indent_width = Bada::Grammar.indent_width(l); end

      # Run headlessly over a scripted key string (for tests / .bada demos).
      # Recognised escapes in the script: \e = ESC, \r or \n = Enter,
      # \b = Backspace, \t = Tab.
      def run_script(script)
        keys = tokenize_script(script)
        keys.each { |k| dispatch(k) }
        self
      end

      # Interactive run using the real terminal (raw mode).
      def run_interactive
        require "io/console"
        @out.print("\e[?1049h") # alternate screen
        begin
          $stdin.raw do
            render
            until @quit
              k = read_key
              dispatch(k)
              render
            end
          end
        ensure
          @out.print("\e[?1049l") # restore screen
          @out.flush
        end
        self
      end

      def quit?
        @quit
      end

      # ---- key dispatch ------------------------------------------------------
      def dispatch(key)
        case @mode
        when :normal  then normal_key(key)
        when :insert  then insert_key(key)
        when :command then command_key(key)
        end
      end

      private

      def normal_key(key)
        b = @buffer
        combo = @pending + key
        @pending = ""

        case combo
        when "h", :left  then b.col -= 1
        when "l", :right then b.col += 1
        when "j", :down  then b.row += 1
        when "k", :up    then b.row -= 1
        when "0"         then b.col = 0
        when "^"         then b.col = (b.line[/\A\s*/] || "").length
        when "$"         then b.col = [b.line.length - 1, 0].max
        when "w"         then move_word_forward
        when "b"         then move_word_back
        when "G"         then b.row = b.lines.length - 1; b.col = 0
        when "g"         then @pending = "g"; return
        when "gg"        then b.row = 0; b.col = 0
        when "x"         then b.delete_char
        when "d"         then @pending = "d"; return
        when "dd"        then b.delete_line
        when "J"         then b.join_lines
        when "i"         then enter_insert
        when "a"         then b.col += 1; enter_insert
        when "A"         then b.col = b.line.length; enter_insert
        when "I"         then b.col = (b.line[/\A\s*/] || "").length; enter_insert
        when "o"         then open_below_indented; enter_insert
        when "O"         then open_above_indented; enter_insert
        when "\t", :tab  then reindent_current_line   # indent completion (line)
        when ":"         then @mode = :command; @command = ""
        when "="         then integrable_fix(reindent: true) # fix + indent
        when "\x06"    then integrable_fix(reindent: true)  # Ctrl-F alias
        when :esc, "\e"  then @message = ""
        else
          # ignore unknown keys / partial combos
        end
        b.clamp!
      end

      def insert_key(key)
        b = @buffer
        case key
        when :esc, "\e"
          @mode = :normal
          b.col -= 1
          b.clamp!
        when :enter, "\r", "\n" then newline_indented
        when "\t", :tab then parser_complete   # parser/indent completion
        when :backspace, "\b", "\x7f" then b.backspace
        when :left  then b.col -= 1; b.clamp!
        when :right then b.col += 1; b.clamp!
        when :up    then b.row -= 1; b.clamp!
        when :down  then b.row += 1; b.clamp!
        when String
          b.insert_char(key) if key.length == 1 && key.ord >= 32
        end
      end

      def command_key(key)
        case key
        when :enter, "\r", "\n"
          run_command(@command)
          @command = ""
          @mode = :normal unless @quit
        when :esc, "\e"
          @command = ""
          @mode = :normal
        when :backspace, "\b", "\x7f"
          @command = @command[0...-1] || ""
          if @command.empty?
            @mode = :normal
          end
        when String
          @command += key if key.length == 1 && key.ord >= 32
        end
      end

      # ---- ex commands -------------------------------------------------------
      def run_command(cmd)
        cmd = cmd.strip
        case cmd
        when "w"  then do_save
        when "q"  then do_quit
        when "q!" then @quit = true
        when "wq", "x" then do_save && (@quit = true)
        when "fix", "correct" then integrable_fix(reindent: true)
        when "fix!" then integrable_fix(save: true, reindent: true)
        when "check", "grammar" then grammar_check
        when "indent", "reindent" then reindent_buffer
        when "complete", "comp" then show_completion
        when /\Aset\s+indent\s*=\s*(\d+)\z/ then @indent_width = $1.to_i; @message = "indent width = #{@indent_width}"
        when /\Aset\s+ft\s*=\s*(\w+)\z/, /\Aset\s+filetype\s*=\s*(\w+)\z/
          self.lang = $1.to_sym; @message = "filetype = #{@lang} (indent #{@indent_width})"
        when /\Aw\s+(.+)\z/ then do_save($1.strip)
        when /\Awq\s+(.+)\z/ then do_save($1.strip) && (@quit = true)
        when "help" then @message = "hjkl move · i/a/o insert · x/dd delete · = fix+indent · :check grammar · :indent · Tab complete · :w :q :wq"
        when "" then @message = ""
        else @message = "not an editor command: #{cmd}"
        end
      end

      def do_save(path = nil)
        p = @buffer.save(path)
        @message = "written: #{p} (#{@buffer.lines.length} lines)"
        true
      rescue => e
        @message = "save failed: #{e.message}"
        false
      end

      def do_quit
        if @buffer.dirty
          @message = "unsaved changes! use :q! to discard or :wq to save"
          false
        else
          @quit = true
        end
      end

      def enter_insert
        @mode = :insert
        @buffer.clamp!
      end

      # ---- THE spinning-top integrable-system code fix -----------------------
      def integrable_fix(save: false, reindent: false)
        res = Bada::CodeFix.fix(@buffer.text, filename: @buffer.filename)
        @last_fix = res
        if res[:changed]
          @buffer.replace_source!(res[:source])
          n = res[:applied].length
          consv = res[:invariant_conserved] ? "conserved" : "DRIFT"
          tail = ""
          if reindent && @grammar_on
            did = reindent_buffer(quiet: true)
            tail = did ? " · indent completed" : ""
          end
          @message = "∮ orbit closed: #{n} fix(es) · Ξ #{consv} " \
                     "(#{format('%.4f', res[:certified_invariant])}) · " \
                     "residual #{format('%.3e', res[:report][:rotation_residual])}#{tail}"
          do_save if save
        else
          ok = res[:report][:orbit_closed]
          if ok && reindent && @grammar_on && reindent_buffer(quiet: true)
            @message = "∮ orbit already closed — indent completed"
          else
            @message = ok ? "∮ orbit already closed — no structural errors" :
                            "no automatic fix found (winding=#{res[:report][:winding]})"
          end
        end
        res
      end

      # ---- grammar checker ---------------------------------------------------
      def grammar_check
        chk = Bada::Grammar.check(@buffer.text, lang: @lang, filename: @buffer.filename)
        @last_check = chk
        if chk[:ok]
          @message = "✓ grammar OK (#{@lang}) — orbit closed, Ξ #{format('%.4f', chk[:certified_invariant])}"
        else
          d = chk[:diagnostics].first
          more = chk[:diagnostics].length - 1
          @message = "✗ #{chk[:diagnostics].length} issue(s) [#{@lang}]  " \
                     "#{d[:line]}:#{d[:col]} #{d[:message]}" + (more > 0 ? "  (+#{more} more)" : "")
        end
        chk
      end

      # ---- indent completion: whole buffer -----------------------------------
      def reindent_buffer(quiet: false)
        before = @buffer.text
        after = Bada::Grammar.reindent(before, lang: @lang, width: @indent_width)
        changed = after != before
        if changed
          row, col = @buffer.row, @buffer.col
          @buffer.replace_source!(after)
          @buffer.row = [row, @buffer.lines.length - 1].min
          @buffer.col = col
          @buffer.clamp!
        end
        @message = changed ? "indent completed (#{@lang}, width #{@indent_width})" :
                             "indentation already normal (#{@lang})" unless quiet
        changed
      end

      # ---- indent completion: current line -----------------------------------
      def reindent_current_line
        row = @buffer.row
        after = Bada::Grammar.reindent(@buffer.text, lang: @lang, width: @indent_width)
        newlines = after.split("\n", -1)
        if newlines[row] && newlines[row] != @buffer.lines[row]
          @buffer.lines[row] = newlines[row]
          @buffer.col = (newlines[row][/\A\s*/] || "").length
          @buffer.dirty = true
          @message = "line indent completed"
        else
          @message = "line indent already normal"
        end
      end

      # ---- auto-indent on new lines ------------------------------------------
      def open_below_indented
        ref = @buffer.row
        @buffer.open_below
        apply_indent_from(ref)
      end

      def open_above_indented
        @buffer.open_above
        # base O on the line now below (the original current line): match it
        below = @buffer.lines[@buffer.row + 1] || ""
        ind = @grammar_on ? (below[/\A[ \t]*/] || "") : ""
        @buffer.lines[@buffer.row] = ind
        @buffer.col = ind.length
      end

      def newline_indented
        @buffer.newline
        return unless @grammar_on
        ref = @buffer.row - 1
        ind = Bada::Grammar.indent_for_new_line(@buffer.lines, ref, lang: @lang, width: @indent_width)
        tail = @buffer.line
        @buffer.lines[@buffer.row] = ind + tail.lstrip
        @buffer.col = ind.length
      end

      def apply_indent_from(ref_row)
        return unless @grammar_on
        ind = Bada::Grammar.indent_for_new_line(@buffer.lines, ref_row, lang: @lang, width: @indent_width)
        @buffer.lines[@buffer.row] = ind
        @buffer.col = ind.length
      end

      # ---- parser completion (Tab in insert mode) ----------------------------
      def parser_complete
        before = text_before_cursor
        res = Bada::Grammar.complete(before, lang: @lang, width: @indent_width)
        sug = res[:suggestion]
        cand = res[:candidates]
        if sug.nil?
          @indent_width.times { @buffer.insert_char(" ") }
          @message = "Tab: no parse expectation — inserted #{@indent_width}-space indent"
        elsif sug[:type] == :bracket
          @buffer.insert_char(sug[:text])
          @message = "parser completion → #{cand.join(' ')}"
        elsif sug[:type] == :indent
          sug[:text].each_char { |c| @buffer.insert_char(c) }
          @message = "indent completion (colon block)"
        elsif sug[:type] == :keyword
          @buffer.newline
          ind = sug[:indent] || ""
          @buffer.lines[@buffer.row] = ind + sug[:text]
          @buffer.col = (ind + sug[:text]).length
          @buffer.dirty = true
          @message = "parser completion → inserted '#{sug[:text]}'"
        end
      end

      def show_completion
        before = text_before_cursor
        res = Bada::Grammar.complete(before, lang: @lang, width: @indent_width)
        @message = res[:candidates].empty? ? "parser: nothing open (orbit closed)" :
                   "parser expects: #{res[:candidates].join(' ')}"
        res
      end

      def text_before_cursor
        b = @buffer
        (b.lines[0...b.row] + [b.line[0...b.col]]).join("\n")
      end

      # results for tests / .bada reporting
      public
      def last_fix; @last_fix; end
      def complete_at_cursor
        Bada::Grammar.complete(text_before_cursor, lang: @lang, width: @indent_width)
      end
      private

      # ---- word motions ------------------------------------------------------
      def move_word_forward
        b = @buffer
        s = b.line
        i = b.col
        i += 1 while i < s.length && word_char?(s[i])
        i += 1 while i < s.length && !word_char?(s[i])
        if i >= s.length && b.row < b.lines.length - 1
          b.row += 1; b.col = 0
        else
          b.col = i
        end
      end

      def move_word_back
        b = @buffer
        s = b.line
        i = b.col
        i -= 1 while i > 0 && !word_char?(s[i - 1])
        i -= 1 while i > 0 && word_char?(s[i - 1])
        b.col = i
      end

      def word_char?(c)
        !c.nil? && c =~ /[A-Za-z0-9_]/
      end

      # ---- rendering ---------------------------------------------------------
      def render
        rows = @rows || term_rows
        cols = @cols || term_cols
        text_rows = rows - 2
        top = [@buffer.row - text_rows + 1, 0].max
        top = scroll_top(text_rows)
        out = +"\e[H\e[2J"
        (0...text_rows).each do |i|
          li = top + i
          if li < @buffer.lines.length
            line = @buffer.lines[li]
            out << truncate(line, cols) << "\r\n"
          else
            out << "\e[38;5;60m~\e[0m\r\n"
          end
        end
        out << status_line(cols) << "\r\n"
        out << message_line(cols)
        # place cursor
        cr = @buffer.row - top + 1
        cc = @buffer.col + 1
        if @mode == :command
          cr = rows
          cc = @command.length + 2
        end
        out << "\e[#{cr};#{cc}H"
        @out.print(out)
        @out.flush
      end

      def scroll_top(text_rows)
        @top ||= 0
        @top = @buffer.row if @buffer.row < @top
        @top = @buffer.row - text_rows + 1 if @buffer.row >= @top + text_rows
        @top = 0 if @top < 0
        @top
      end

      def status_line(cols)
        name = @buffer.filename || "[No Name]"
        flag = @buffer.dirty ? " [+]" : ""
        left = " #{mode_label}  #{name}#{flag}"
        right = "#{@buffer.row + 1},#{@buffer.col + 1}  Ω-Vim "
        pad = cols - left.length - right.length
        pad = 1 if pad < 1
        "\e[7m#{left}#{" " * pad}#{right}\e[0m"
      end

      def message_line(cols)
        if @mode == :command
          truncate(":" + @command, cols)
        else
          truncate(@message, cols)
        end
      end

      def mode_label
        { normal: "NORMAL", insert: "INSERT", command: "COMMAND" }[@mode]
      end

      def truncate(s, cols)
        s = s.to_s
        s.length > cols ? s[0, cols] : s
      end

      def term_rows
        (ENV["LINES"] || (@out.respond_to?(:winsize) ? @out.winsize[0] : 24)).to_i
      rescue
        24
      end

      def term_cols
        (ENV["COLUMNS"] || (@out.respond_to?(:winsize) ? @out.winsize[1] : 80)).to_i
      rescue
        80
      end

      # ---- input -------------------------------------------------------------
      def read_key
        c = $stdin.getc
        return :esc if c.nil?
        if c == "\e"
          # try to read an escape sequence (arrows)
          if IO.select([$stdin], nil, nil, 0.005)
            a = $stdin.getc
            if a == "[" && IO.select([$stdin], nil, nil, 0.005)
              b = $stdin.getc
              return { "A" => :up, "B" => :down, "C" => :right, "D" => :left }[b] || :esc
            end
          end
          return :esc
        end
        return :enter if c == "\r" || c == "\n"
        return :backspace if c == "\x7f" || c == "\b"
        c
      end

      # Turn a script string into key tokens (with \e \r \b \t escapes).
      def tokenize_script(script)
        keys = []
        i = 0
        while i < script.length
          c = script[i]
          if c == "\\" && i + 1 < script.length
            nxt = script[i + 1]
            case nxt
            when "e" then keys << :esc
            when "r", "n" then keys << :enter
            when "b" then keys << :backspace
            when "t" then keys << "\t"
            when "\\" then keys << "\\"
            else keys << nxt
            end
            i += 2
          elsif c == "\e"
            keys << :esc; i += 1
          elsif c == "\n" || c == "\r"
            keys << :enter; i += 1
          else
            keys << c; i += 1
          end
        end
        keys
      end
    end
  end
end
