# frozen_string_literal: true

module Bada
  module Lang
    Token = Struct.new(:type, :value, :line)

    # Lexer for the Bada scripting language. Produces a flat token stream;
    # NEWLINE tokens act as statement separators (multiple/blank lines collapse).
    class Lexer
      KEYWORDS = %w[let def end if elsif else while return print import library true false and or not nil].freeze

      def initialize(source)
        @s = source
        @i = 0
        @line = 1
        @tokens = []
      end

      def tokenize
        until eof?
          c = cur
          case
          when c == "#"
            skip_to_eol
          when c == "\n"
            push(:newline, "\n"); @line += 1; advance
          when c == " " || c == "\t" || c == "\r"
            advance
          when c == '"'
            string
          when digit?(c)
            number
          when ident_start?(c)
            identifier
          else
            operator
          end
        end
        push(:eof, nil)
        @tokens
      end

      private

      def eof? = @i >= @s.length
      def cur = @s[@i]
      def nxt = @s[@i + 1]
      def advance = (@i += 1)
      def push(t, v) = (@tokens << Token.new(t, v, @line))
      def digit?(c) = c =~ /[0-9]/
      def ident_start?(c) = c =~ /[A-Za-z_]/
      def ident_char?(c) = c =~ /[A-Za-z0-9_]/

      def skip_to_eol
        advance until eof? || cur == "\n"
      end

      def string
        advance # opening quote
        buf = +""
        until eof? || cur == '"'
          if cur == "\\"
            advance
            buf << escape(cur)
          else
            buf << cur
          end
          advance
        end
        advance # closing quote
        push(:string, buf)
      end

      def escape(c)
        { "n" => "\n", "t" => "\t", '"' => '"', "\\" => "\\" }.fetch(c, c)
      end

      def number
        buf = +""
        while !eof? && (digit?(cur) || cur == ".")
          buf << cur
          advance
        end
        # scientific notation: e / E with optional sign
        if !eof? && (cur == "e" || cur == "E") && (digit?(nxt) || nxt == "+" || nxt == "-")
          buf << cur; advance
          if cur == "+" || cur == "-"
            buf << cur; advance
          end
          while !eof? && digit?(cur)
            buf << cur
            advance
          end
          push(:number, buf.to_f)
          return
        end
        push(:number, buf.include?(".") ? buf.to_f : buf.to_i)
      end

      def identifier
        buf = +""
        while !eof? && ident_char?(cur)
          buf << cur
          advance
        end
        if KEYWORDS.include?(buf)
          push(buf.to_sym, buf)
        else
          push(:ident, buf)
        end
      end

      MULTI = { "<-" => :larrow, "-<" => :integ, ">-" => :rarrow,
                "==" => :eq, "!=" => :neq, "<=" => :le, ">=" => :ge,
                "::" => :colcol }.freeze
      SINGLE = { "+" => :plus, "-" => :minus, "*" => :star, "/" => :slash,
                 "(" => :lparen, ")" => :rparen, "[" => :lbracket, "]" => :rbracket,
                 "," => :comma, "." => :dot, "=" => :assign, "<" => :lt, ">" => :gt }.freeze

      def operator
        two = "#{cur}#{nxt}"
        if MULTI.key?(two)
          push(MULTI[two], two); advance; advance
          return
        end
        if SINGLE.key?(cur)
          push(SINGLE[cur], cur); advance
          return
        end
        raise "Bada lex error: unexpected #{cur.inspect} on line #{@line}"
      end
    end
  end
end
