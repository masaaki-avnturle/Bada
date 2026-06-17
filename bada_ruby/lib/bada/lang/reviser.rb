# frozen_string_literal: true

require_relative "dialect"

module Bada
  module Lang
    # Reviser — forks a parent dialect into a new variant by applying revisions
    # (the language branching system). Revisions are expressed in a small DSL.
    #
    #   ja = Bada::Lang::Reviser.fork(name: "bada-ja") do
    #     rename :def,   "関数"
    #     rename :end,   "終"
    #     rename :print, "表示"
    #     rename :return,"返す"
    #     builtin("二乗") { |x| x * x }
    #   end
    module Reviser
      module_function

      # Fork a child dialect from `parent` (defaults to the base language).
      def fork(name:, parent: Dialect.base, &block)
        child = Dialect.new(name: name, parent: parent)
        RevisionDSL.new(child).instance_eval(&block) if block
        child
      end

      # Convenience: the language genealogy rooted at base.
      def tree
        Dialect.base
      end
    end

    # The revision DSL evaluated inside Reviser.fork { ... }.
    class RevisionDSL
      def initialize(dialect)
        @d = dialect
      end

      # alias an extra surface word to an existing role (keep the old one too)
      def keyword(surface, role)
        @d.alias_keyword(surface, role)
      end

      # rename a role: the new surface word replaces the old one(s)
      def rename(role, new_surface)
        @d.rename_keyword(role, new_surface)
      end

      # add or override a builtin available to programs in this dialect
      def builtin(name, &blk)
        @d.add_builtin(name, blk)
      end

      # prelude source (in THIS dialect's syntax) run before every program
      def prelude(src)
        @d.add_prelude(src)
      end

      def note(text)
        @d.note(text)
      end
    end
  end
end
