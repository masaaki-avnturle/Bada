# frozen_string_literal: true

require "json"
require_relative "palette"
require_relative "diagram"
require_relative "canvas"
require_relative "evaluator"
require_relative "latex"

module Bada
  module Penrose
    # Builder — the interactive Penrose 絵記号 application.
    #
    #   * a PALETTE of Roger Penrose's picture-symbols (tensor box, index wire,
    #     contraction, metric cup/cap, ∇, ∂, ∫, (anti)symmetriser),
    #   * a DIALOG BOX (a small command REPL) where you pick a symbol part and
    #     combine it into the drawing,
    #   * "combine" then generates the 清書した方程式 (fair-copy LaTeX + a
    #     Unicode form) and the 組み合わせによる計算した方程式 (Einstein-summation
    #     numeric result).
    #
    # The command surface is deliberately small and also usable programmatically
    # (so it is testable):
    #
    #   b = Builder.new
    #   b.place("A", legs: 2, value: [[1,2],[3,4]])
    #   b.place("B", legs: 2, value: [[5,6],[7,8]])
    #   b.wire("A.1", "B.0")           # contract A's 2nd leg with B's 1st
    #   b.free("A.0", "i"); b.free("B.1", "j")
    #   r = b.combine                  #=> { latex:, pretty:, result:, ... }
    #
    class Builder
      attr_reader :diagram, :values, :log

      def initialize
        reset
      end

      def reset
        @diagram = Diagram.new
        @values = {}
        @legs = Hash.new(0)   # declared leg count per node
        @log = []             # human-readable list of placed parts
        self
      end

      # ---- palette -----------------------------------------------------
      def palette
        Palette.glyphs
      end

      def palette_render
        Palette.render
      end

      # ---- placing parts (絵記号の部品を選ぶ) --------------------------
      # Place a tensor box. legs is the number of index wires; value is an
      # optional nested array of components (enables the numeric equation).
      def place(name, legs:, value: nil)
        raise ArgumentError, "part '#{name}' already placed" if @diagram.nodes.key?(name)

        @diagram.tensor(name, legs: legs, value: value)
        @legs[name] = legs
        @values[name] = value if value
        @log << "テンソル箱 [#{name}] を配置（脚#{legs}本#{value ? '・成分あり' : ''}）"
        self
      end

      # Convenience picks that map palette glyphs to a placed tensor.
      def metric(name = "g", value: nil)  = place(name, legs: 2, value: value)
      def epsilon(name = "ε", value: nil) = place(name, legs: value ? nil_rank(value) : 2, value: value)

      # Give (or replace) a placed part's components after the fact.
      def set_value(name, value)
        raise ArgumentError, "no such part '#{name}'" unless @diagram.nodes.key?(name)

        @diagram.value(name, value)
        @values[name] = value
        @log << "[#{name}] に成分を設定"
        self
      end

      # ---- wiring parts (組み合わせる) ---------------------------------
      # Contraction: join two legs (a shared line => Einstein sum).
      def wire(slot_a, slot_b)
        a = parse_slot(slot_a)
        b = parse_slot(slot_b)
        @diagram.contract(a, b)
        @log << "縮約線: #{a[0]}[#{a[1]}] ─ #{b[0]}[#{b[1]}]"
        self
      end

      # A free (output) index: a line that leaves the diagram with a label.
      def free(slot, label)
        s = parse_slot(slot)
        @diagram.free(s, label.to_s)
        @log << "自由添字: #{s[0]}[#{s[1]}] → #{label}"
        self
      end

      # ---- differential / integral parts ------------------------------
      def nabla(target, label)
        @diagram.nabla(target.to_s, label.to_s)
        @log << "共変微分 ∇_#{label}（対象 #{target}）"
        self
      end

      def partial(target, label)
        @diagram.partial(target.to_s, label.to_s)
        @log << "偏微分 ∂_#{label}（対象 #{target}）"
        self
      end

      def integral(label)
        @diagram.integral(label.to_s)
        @log << "積分 ∫ d#{label}"
        self
      end

      def symmetrize(*labels)
        @diagram.symmetrize(*labels.map(&:to_s))
        @log << "対称化 Sym(#{labels.join(',')})"
        self
      end

      def antisymmetrize(*labels)
        @diagram.antisymmetrize(*labels.map(&:to_s))
        @log << "反対称化 Asym(#{labels.join(',')})"
        self
      end

      # ---- combine (清書＋計算) ----------------------------------------
      # Produce both equations from the current combination of parts.
      def combine
        e = Evaluator.evaluate(@diagram)
        {
          einsum: e[:einsum],                    # raw index string
          latex: Latex.fair_copy(@diagram),      # 清書した方程式 (LaTeX)
          display: Latex.display(@diagram),      # $$...$$ ready block
          pretty: Latex.pretty(@diagram),        # Unicode terminal form
          output: e[:output],
          numeric: e[:numeric],
          result: e[:result],                    # 計算した方程式の値
          scalar: e[:scalar],
          notes: e[:notes],
          canvas: canvas
        }
      end

      # ASCII rendering of the current drawing (パレット上の絵).
      def canvas
        return "（まだ部品がありません）" if @diagram.nodes.empty?

        Canvas.render(@diagram)
      end

      # A one-shot pretty report of the combined equations.
      def combined_report
        r = combine
        out = []
        out << "──────── 絵記号（キャンバス）────────"
        out << r[:canvas]
        out << ""
        out << "──────── 清書した方程式（LaTeX）────────"
        out << r[:display]
        out << ""
        out << "──────── 清書した方程式（表示形）────────"
        out << "  #{r[:pretty]}"
        out << ""
        out << "──────── 組み合わせによる計算した方程式 ────────"
        out << "  #{numeric_line(r)}"
        r[:notes].each { |n| out << "  注: #{n}" }
        out.join("\n")
      end

      def numeric_line(r)
        if r[:scalar]
          "#{r[:pretty].split('=').first.strip} = #{format('%.6g', r[:scalar])}  （スカラー）"
        elsif r[:result]
          "#{r[:pretty].split('=').first.strip} = #{r[:result].inspect}"
        else
          "（成分値が未指定 — value で数値を与えると計算されます）"
        end
      end

      # =================================================================
      # Interactive dialog box (対話ループ)
      # =================================================================
      def run(input: $stdin, output: $stdout)
        @out = output
        banner
        loop do
          @out.print "penrose> "
          @out.flush
          line = input.gets
          break if line.nil?

          line = line.strip
          next if line.empty?
          break if %w[quit exit q bye].include?(line.downcase)

          begin
            dispatch(line)
          rescue StandardError => e
            @out.puts "  ! #{e.message}"
          end
        end
        @out.puts "終了しました。"
      end

      private

      def banner
        @out.puts "╔══════════════════════════════════════════════════════════════╗"
        @out.puts "║  ペンローズ絵記号スタジオ — パレット＋ダイアログ (Bada/Ruby)   ║"
        @out.puts "╚══════════════════════════════════════════════════════════════╝"
        @out.puts "コマンド: help でダイアログの使い方、palette でパレット一覧。"
        @out.puts "例: place A 2 [[1,2],[3,4]] / wire A.1 B.0 / free A.0 i / combine"
      end

      def dispatch(line)
        cmd, rest = line.split(/\s+/, 2)
        case cmd
        when "help"     then help
        when "palette"  then @out.puts palette_render
        when "place"    then cmd_place(rest)
        when "metric"   then cmd_metric(rest)
        when "value"    then cmd_value(rest)
        when "wire"     then cmd_wire(rest)
        when "free"     then cmd_free(rest)
        when "nabla"    then a, l = rest.split(/\s+/); nabla(a, l); echo_last
        when "partial"  then a, l = rest.split(/\s+/); partial(a, l); echo_last
        when "integral" then integral(rest.strip); echo_last
        when "sym"      then symmetrize(*rest.split(/\s+/)); echo_last
        when "antisym"  then antisymmetrize(*rest.split(/\s+/)); echo_last
        when "canvas"   then @out.puts canvas
        when "parts"    then @log.each_with_index { |l, i| @out.puts "  #{i + 1}. #{l}" }
        when "combine"  then @out.puts combined_report
        when "reset"    then reset; @out.puts "リセットしました。"
        else @out.puts "  ? 未知のコマンド: #{cmd}（help を参照）"
        end
      end

      def cmd_place(rest)
        name, legs, val = rest.to_s.split(/\s+/, 3)
        raise ArgumentError, "usage: place <名前> <脚数> [値JSON]" if name.nil? || legs.nil?

        value = val && !val.empty? ? JSON.parse(val) : nil
        place(name, legs: Integer(legs), value: value)
        echo_last
      end

      def cmd_metric(rest)
        name, val = rest.to_s.split(/\s+/, 2)
        name = "g" if name.nil? || name.empty?
        value = val && !val.empty? ? JSON.parse(val) : nil
        metric(name, value: value)
        echo_last
      end

      def cmd_value(rest)
        name, val = rest.to_s.split(/\s+/, 2)
        raise ArgumentError, "usage: value <名前> <値JSON>" if name.nil? || val.nil?

        set_value(name, JSON.parse(val))
        echo_last
      end

      def cmd_wire(rest)
        a, b = rest.to_s.split(/\s+/)
        raise ArgumentError, "usage: wire <A.脚> <B.脚>" if a.nil? || b.nil?

        wire(a, b)
        echo_last
      end

      def cmd_free(rest)
        slot, label = rest.to_s.split(/\s+/)
        raise ArgumentError, "usage: free <A.脚> <添字名>" if slot.nil? || label.nil?

        free(slot, label)
        echo_last
      end

      def echo_last
        @out.puts "  + #{@log.last}"
      end

      def help
        @out.puts <<~HELP
          ── ダイアログ・コマンド ──
            palette                     パレット（絵記号一覧）を表示
            place <名前> <脚数> [値]    テンソル箱を配置。例: place A 2 [[1,2],[3,4]]
            metric [名前] [値]          計量テンソル g を配置
            value <名前> <値JSON>       配置済み部品に成分を設定
            wire  <A.脚> <B.脚>         2本の線を縮約（つなぐ）。例: wire A.1 B.0
            free  <A.脚> <添字名>        自由添字（出力の脚）。例: free A.0 i
            nabla <対象> <添字>          共変微分 ∇ を付ける
            partial <対象> <添字>        偏微分 ∂ を付ける
            integral <添字>             積分 ∫ d<添字> を付ける
            sym <添字...>  / antisym ... 出力添字の(反)対称化
            canvas                      現在の絵を表示
            parts                       配置した部品の履歴
            combine                     清書方程式＋計算方程式を生成
            reset / quit
        HELP
      end

      # Parse "A.1" / "A:1" / "A 1" into [name, leg_index].
      def parse_slot(slot)
        return slot if slot.is_a?(Array)

        m = slot.to_s.match(/\A([^.:\s]+)[.:\s](\d+)\z/)
        raise ArgumentError, "脚の指定は 名前.番号 の形式で（例 A.0）: #{slot.inspect}" unless m

        name = m[1]
        leg = Integer(m[2])
        raise ArgumentError, "未配置の部品: #{name}" unless @diagram.nodes.key?(name)
        raise ArgumentError, "[#{name}] の脚は0..#{@legs[name] - 1}（指定 #{leg}）" if leg >= @legs[name]

        [name, leg]
      end

      def nil_rank(value)
        rank = 0
        probe = value
        while probe.is_a?(Array)
          rank += 1
          probe = probe[0]
        end
        rank
      end
    end
  end
end
