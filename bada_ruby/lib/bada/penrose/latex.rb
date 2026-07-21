# frozen_string_literal: true

require_relative "diagram"

module Bada
  module Penrose
    # Latex — turn a drawn/combined Penrose diagram into a *fair copy* (清書)
    # equation. Two renderings are produced:
    #
    #   * LaTeX summation form  R_{ij} = \sum_{k} A_{ik} B_{kj}
    #   * a Unicode "pretty" form for the terminal  R[i j] = Σ_k A[i k] B[k j]
    #
    # This is the "清書した方程式" side of the app: the combination of picture-
    # symbols chosen on the palette becomes a properly typeset equation. The
    # numeric "計算した方程式" comes from Evaluator (Einstein summation).
    module Latex
      module_function

      # Unicode subscript digits, for k1 -> k₁ style dummy names.
      SUBDIGITS = { "0" => "₀", "1" => "₁", "2" => "₂", "3" => "₃", "4" => "₄",
                    "5" => "₅", "6" => "₆", "7" => "₇", "8" => "₈", "9" => "₉" }.freeze

      # ---- LaTeX ------------------------------------------------------
      # Fully typeset equation as a LaTeX string (display math body, no $$).
      def fair_copy(diagram)
        r = diagram.resolve
        dummies = dummy_indices(diagram, r)

        factors = diagram.nodes.map do |name, _node|
          "#{tex_name(name)}_{#{r[:assignment][name].map { |i| tex_index(i) }.join}}"
        end
        body = decorate_tex(diagram, factors.join(" \\, "))

        lhs = result_symbol_tex(diagram, r)
        sum = dummies.empty? ? "" : "\\sum_{#{dummies.map { |d| tex_index(d) }.join}} "
        "#{lhs} \\;=\\; #{sum}#{body}"
      end

      # A ready-to-compile display-math block ($$ ... $$).
      def display(diagram)
        "$$#{fair_copy(diagram)}$$"
      end

      # ---- Unicode pretty (terminal) ----------------------------------
      def pretty(diagram)
        r = diagram.resolve
        dummies = dummy_indices(diagram, r)

        factors = diagram.nodes.map do |name, _node|
          "#{name}[#{r[:assignment][name].map { |i| uni_index(i) }.join(' ')}]"
        end
        body = decorate_uni(diagram, factors.join(" · "))

        lhs = result_symbol_uni(diagram, r)
        sum = dummies.empty? ? "" : "Σ_#{dummies.map { |d| uni_index(d) }.join(',')} "
        "#{lhs} = #{sum}#{body}"
      end

      # ---- helpers ----------------------------------------------------

      # Contracted (dummy) indices: names appearing on more than one leg, plus
      # integral measure indices (both are summed over).
      def dummy_indices(diagram, resolved)
        counts = Hash.new(0)
        resolved[:assignment].each_value { |legs| legs.each { |n| counts[n] += 1 } }
        dummies = counts.select { |_n, c| c > 1 }.keys
        (dummies | resolved[:integral]).uniq
      end

      def result_symbol_tex(diagram, resolved)
        idx = resolved[:output].map { |i| tex_index(i) }.join
        wrap = symmetry_wrap(diagram)
        return "R" if idx.empty? && wrap.nil?
        case wrap
        when :sym    then "R_{(#{idx})}"
        when :antisym then "R_{[#{idx}]}"
        else "R_{#{idx}}"
        end
      end

      def result_symbol_uni(diagram, resolved)
        idx = resolved[:output].map { |i| uni_index(i) }.join(" ")
        wrap = symmetry_wrap(diagram)
        return "R" if idx.empty? && wrap.nil?
        case wrap
        when :sym    then "R[(#{idx})]"
        when :antisym then "R[#{idx}]⁻"
        else "R[#{idx}]"
        end
      end

      def symmetry_wrap(diagram)
        d = diagram.decorators.find { |x| %i[sym antisym].include?(x.type) }
        d&.type
      end

      # Wrap the product with the ∇/∂/∫ operators the diagram carries.
      def decorate_tex(diagram, body)
        pre = ""
        post = ""
        diagram.decorators.each do |d|
          case d.type
          when :nabla   then pre = "\\nabla_{#{tex_index(d.label)}} #{pre}"
          when :partial then pre = "\\partial_{#{tex_index(d.label)}} #{pre}"
          when :integral
            pre = "\\int #{pre}"
            post += " \\, d#{tex_index(d.label)}"
          end
        end
        "#{pre}#{body}#{post}"
      end

      def decorate_uni(diagram, body)
        pre = ""
        post = ""
        diagram.decorators.each do |d|
          case d.type
          when :nabla   then pre = "∇_#{uni_index(d.label)} #{pre}"
          when :partial then pre = "∂_#{uni_index(d.label)} #{pre}"
          when :integral
            pre = "∫ #{pre}"
            post += " d#{uni_index(d.label)}"
          end
        end
        "#{pre}#{body}#{post}"
      end

      # Index token -> LaTeX.  "k1" -> "k_{1}" style dummy, greek stays literal.
      def tex_index(tok)
        s = tok.to_s
        if s =~ /\A([A-Za-z])(\d+)\z/
          "#{$1}_{#{$2}}"
        else
          s
        end
      end

      def tex_name(name)
        case name
        when "ε", "E" then "\\varepsilon"
        when "∇" then "\\nabla"
        else name
        end
      end

      # Index token -> Unicode, mapping trailing digits to subscripts.
      def uni_index(tok)
        s = tok.to_s
        if s =~ /\A([A-Za-z])(\d+)\z/
          $1 + $2.chars.map { |c| SUBDIGITS[c] || c }.join
        else
          s
        end
      end
    end
  end
end
