# frozen_string_literal: true

module Bada
  module Lang
    # AST node definitions for the Bada language.
    module AST
      Program  = Struct.new(:stmts)
      Num      = Struct.new(:value)
      Str      = Struct.new(:value)
      Bool     = Struct.new(:value)
      Nil_     = Struct.new(:dummy)
      Ident    = Struct.new(:name)
      ListLit  = Struct.new(:elems)
      Binary   = Struct.new(:op, :left, :right)
      Unary    = Struct.new(:op, :expr)
      Member   = Struct.new(:obj, :name)   # A.b
      Call     = Struct.new(:callee, :args)
      Assign   = Struct.new(:name, :expr)
      Def      = Struct.new(:name, :params, :body)
      Lambda   = Struct.new(:params, :body)        # def(params) ... end as a value
      Library  = Struct.new(:name, :defs)
      If       = Struct.new(:cond, :then_body, :elsifs, :else_body)
      While    = Struct.new(:cond, :body)
      Return   = Struct.new(:expr)
      Print    = Struct.new(:expr)
      Import   = Struct.new(:path)
      ExprStmt = Struct.new(:expr)
    end
  end
end
