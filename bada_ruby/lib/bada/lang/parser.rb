# frozen_string_literal: true

require_relative "lexer"
require_relative "nodes"

module Bada
  module Lang
    # Recursive-descent + Pratt parser for the Bada language.
    class Parser
      include AST

      def self.parse(source, keyword_map: nil)
        new(Lexer.new(source, keyword_map: keyword_map).tokenize).parse_program
      end

      def initialize(tokens)
        @toks = tokens
        @p = 0
      end

      def parse_program
        stmts = []
        skip_newlines
        until at?(:eof)
          stmts << statement
          skip_terminators
        end
        Program.new(stmts)
      end

      private

      # ---- token helpers ----
      def peek = @toks[@p]
      def kind = peek.type
      def at?(t) = kind == t
      def advance = (@toks[@p].tap { @p += 1 })
      def accept(t) = (at?(t) ? advance : nil)

      def expect(t)
        return advance if at?(t)
        raise "Bada parse error: expected #{t}, got #{kind} (#{peek.value.inspect}) line #{peek.line}"
      end

      def skip_newlines = (advance while at?(:newline))
      def skip_terminators = (advance while at?(:newline))

      # ---- statements ----
      def statement
        case kind
        when :let then parse_let
        when :def then parse_def
        when :library then parse_library
        when :if then parse_if
        when :while then parse_while
        when :return then advance; Return.new(end_of_stmt? ? nil : expression)
        when :print then advance; Print.new(expression)
        when :import then advance; Import.new(expect(:string).value)
        else
          expr = expression
          # assignment without `let`:  name = expr
          if expr.is_a?(Ident) && at?(:assign)
            advance
            return Assign.new(expr.name, expression)
          end
          ExprStmt.new(expr)
        end
      end

      def end_of_stmt? = at?(:newline) || at?(:eof) || at?(:end)

      def parse_let
        advance
        name = expect(:ident).value
        expect(:assign)
        Assign.new(name, expression)
      end

      def parse_def
        advance
        name = expect(:ident).value
        params = parse_params
        body = block(%i[end])
        expect(:end)
        Def.new(name, params, body)
      end

      def parse_params
        expect(:lparen)
        params = []
        until at?(:rparen)
          params << expect(:ident).value
          break unless accept(:comma)
        end
        expect(:rparen)
        params
      end

      def parse_library
        advance
        name = expect(:ident).value
        skip_newlines
        defs = []
        until at?(:end)
          defs << parse_def
          skip_newlines
        end
        expect(:end)
        Library.new(name, defs)
      end

      def parse_if
        advance
        cond = expression
        then_body = block(%i[elsif else end])
        elsifs = []
        while at?(:elsif)
          advance
          c = expression
          b = block(%i[elsif else end])
          elsifs << [c, b]
        end
        else_body = nil
        if accept(:else)
          else_body = block(%i[end])
        end
        expect(:end)
        If.new(cond, then_body, elsifs, else_body)
      end

      def parse_while
        advance
        cond = expression
        body = block(%i[end])
        expect(:end)
        While.new(cond, body)
      end

      # Parse statements until one of `terminators` keyword tokens is seen.
      def block(terminators)
        stmts = []
        skip_newlines
        until terminators.include?(kind) || at?(:eof)
          stmts << statement
          skip_terminators
        end
        stmts
      end

      # ---- expressions (Pratt) ----
      def expression = parse_or

      def parse_or
        left = parse_and
        while at?(:or)
          advance
          left = Binary.new(:or, left, parse_and)
        end
        left
      end

      def parse_and
        left = parse_equality
        while at?(:and)
          advance
          left = Binary.new(:and, left, parse_equality)
        end
        left
      end

      def parse_equality
        left = parse_comparison
        while at?(:eq) || at?(:neq)
          op = advance.type
          left = Binary.new(op, left, parse_comparison)
        end
        left
      end

      def parse_comparison
        left = parse_bada_ops
        while %i[lt le gt ge].include?(kind)
          op = advance.type
          left = Binary.new(op, left, parse_bada_ops)
        end
        left
      end

      # The Bada operators  <-  -<  >-
      def parse_bada_ops
        left = parse_additive
        while %i[larrow integ rarrow].include?(kind)
          op = advance.type
          left = Binary.new(op, left, parse_additive)
        end
        left
      end

      def parse_additive
        left = parse_multiplicative
        while at?(:plus) || at?(:minus)
          op = advance.type
          left = Binary.new(op, left, parse_multiplicative)
        end
        left
      end

      def parse_multiplicative
        left = parse_unary
        while at?(:star) || at?(:slash)
          op = advance.type
          left = Binary.new(op, left, parse_unary)
        end
        left
      end

      def parse_unary
        if at?(:not) || at?(:minus)
          op = advance.type
          return Unary.new(op, parse_unary)
        end
        parse_postfix
      end

      # calls and member access
      def parse_postfix
        expr = parse_primary
        loop do
          if accept(:dot)
            name = expect(:ident).value
            expr = Member.new(expr, name)
          elsif at?(:lparen)
            expr = Call.new(expr, parse_args)
          else
            break
          end
        end
        expr
      end

      def parse_args
        expect(:lparen)
        args = []
        until at?(:rparen)
          args << expression
          break unless accept(:comma)
        end
        expect(:rparen)
        args
      end

      def parse_primary
        case kind
        when :def       # anonymous function (directive):  def(params) ... end
          advance
          params = parse_params
          body = block(%i[end])
          expect(:end)
          Lambda.new(params, body)
        when :number then Num.new(advance.value)
        when :string then Str.new(advance.value)
        when :true then advance; Bool.new(true)
        when :false then advance; Bool.new(false)
        when :nil then advance; Nil_.new(nil)
        when :ident then Ident.new(advance.value)
        when :lparen
          advance
          e = expression
          expect(:rparen)
          e
        when :lbracket
          advance
          elems = []
          until at?(:rbracket)
            elems << expression
            break unless accept(:comma)
          end
          expect(:rbracket)
          ListLit.new(elems)
        else
          raise "Bada parse error: unexpected #{kind} (#{peek.value.inspect}) line #{peek.line}"
        end
      end
    end
  end
end
