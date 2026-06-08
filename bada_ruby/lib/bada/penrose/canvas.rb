# frozen_string_literal: true

require_relative "diagram"

module Bada
  module Penrose
    # Canvas: parse a *drawn* Penrose diagram (ASCII picture-symbols) into a
    # Diagram, and render a Diagram back to ASCII.
    #
    # Drawing convention (documented in the palette):
    #   * a tensor is a box  [X]  (single letter name)
    #   * a horizontal wire of '-' between two boxes contracts them
    #   * a vertical wire of '|' between two boxes (same column) contracts them
    #   * a label (letter/digit) at a wire end is a free (output) index
    #   * decorator tokens anywhere:  (D X m) ∇,  (d X m) ∂,  (I m) ∫,
    #       S{i j} symmetrise,  A{i j} antisymmetrise
    #
    #   example:  i-[A]-[B]-j   ⇒  A_{i k1} B_{k1 j} → R_{i j}
    module Canvas
      module_function

      Tok = Struct.new(:type, :name, :left, :right, :row, :col) # type: :box/:label

      def parse(drawing, values: {})
        d = Diagram.new
        text = extract_decorators(drawing.to_s, d)
        lines = text.split("\n")

        boxes = []          # all box tokens (for vertical wiring)
        connections = []    # [:cc, tokA, tokB] box-box ; [:cf, tok, label] box-free

        lines.each_with_index do |line, r|
          toks = tokenize(line, r)
          toks.select { |t| t.type == :box }.each { |b| boxes << b }
          # horizontal adjacency within the line
          toks.each_cons(2) do |a, b|
            next unless horizontally_wired?(line, a, b)
            connections << connect(a, b)
          end
        end

        # vertical wiring: '|' columns linking a box above to a box below
        vertical_connections(lines, boxes).each { |c| connections << c }

        build(d, connections, values)
        d
      end

      # ---- tokenisation ------------------------------------------------
      def tokenize(line, row)
        toks = []
        i = 0
        while i < line.length
          ch = line[i]
          if ch == "[" && i + 2 < line.length && line[i + 2] == "]"
            toks << Tok.new(:box, line[i + 1], i, i + 2, row, i + 1)
            i += 3
          elsif ch =~ /[A-Za-z0-9μνρσ]/
            j = i
            j += 1 while j < line.length && line[j] =~ /[A-Za-z0-9μνρσ]/
            toks << Tok.new(:label, line[i...j], i, j - 1, row, i)
            i = j
          else
            i += 1
          end
        end
        toks
      end

      # two tokens are wired if the cells strictly between them are all '-'
      def horizontally_wired?(line, a, b)
        gap = line[(a.right + 1)...b.left]
        return false if gap.nil? || gap.empty?
        gap.chars.all? { |c| c == "-" }
      end

      def connect(a, b)
        if a.type == :box && b.type == :box
          [:cc, a, b]
        elsif a.type == :box
          [:cf, a, b.name]
        else # label - box
          [:cf, b, a.name]
        end
      end

      def vertical_connections(lines, boxes)
        conns = []
        boxes.each do |top|
          # scan downward from just below the box centre for a '|' run to a box
          r = top.row + 1
          col = top.col
          seen_pipe = false
          while r < lines.length
            ch = lines[r] && lines[r][col]
            if ch == "|"
              seen_pipe = true
              r += 1
            else
              break
            end
          end
          next unless seen_pipe
          bottom = boxes.find { |b| b.row == r && b.col == col }
          conns << [:cc, top, bottom] if bottom
        end
        conns
      end

      # ---- build the diagram ------------------------------------------
      def build(diagram, connections, values)
        legcount = Hash.new(0)
        # first pass: count legs per box (each connection adds a leg to each box end)
        connections.each do |c|
          case c[0]
          when :cc then legcount[c[1].name] += 1; legcount[c[2].name] += 1
          when :cf then legcount[c[1].name] += 1
          end
        end
        legcount.each { |name, n| diagram.tensor(name, legs: n, value: values[name]) }

        nextleg = Hash.new(0)
        connections.each do |c|
          case c[0]
          when :cc
            a = c[1].name; b = c[2].name
            la = nextleg[a]; nextleg[a] += 1
            lb = nextleg[b]; nextleg[b] += 1
            diagram.contract([a, la], [b, lb])
          when :cf
            a = c[1].name; label = c[2]
            la = nextleg[a]; nextleg[a] += 1
            diagram.free([a, la], label)
          end
        end
      end

      # ---- decorators --------------------------------------------------
      def extract_decorators(text, diagram)
        t = text.dup
        t.gsub!(/\(D\s+(\w)\s+(\w+)\)/) { diagram.nabla($1, $2); "" }
        t.gsub!(/\(d\s+(\w)\s+(\w+)\)/) { diagram.partial($1, $2); "" }
        t.gsub!(/\(I\s+(\w+)\)/) { diagram.integral($1); "" }
        t.gsub!(/S\{([^}]*)\}/) { diagram.symmetrize(*$1.split(/[\s,]+/)); "" }
        t.gsub!(/A\{([^}]*)\}/) { diagram.antisymmetrize(*$1.split(/[\s,]+/)); "" }
        t
      end

      # ---- render Diagram -> ASCII ------------------------------------
      def render(diagram)
        r = diagram.resolve
        names = diagram.nodes.keys
        boxes = names.map { |n| "[#{n}]" }
        line = boxes.join("─")
        idx = names.map { |n| "#{n}:#{r[:assignment][n].join(',')}" }.join("  ")
        deco = diagram.decorators.map { |d| diagram.decorator_label(d) }
        out = []
        out << (deco.empty? ? line : "#{deco.join(' ')}  #{line}")
        out << "  添字: #{idx}"
        out << "  出力 (自由添字): #{r[:output].join(', ')}"
        out.join("\n")
      end
    end
  end
end
