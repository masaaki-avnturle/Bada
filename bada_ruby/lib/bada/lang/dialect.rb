# frozen_string_literal: true

require_relative "lexer"
require_relative "../manifold"

module Bada
  module Lang
    # A Dialect is a *variant* (亜種) of the Bada language: a keyword-alias map,
    # a builtin overlay, and a prelude (Bada source run before any program).
    # Dialects form a branching genealogy (parent -> children) — the language
    # branching system. Each dialect also carries a manifold entropy invariant
    # of its spec, used as its branch identity ("trigger").
    class Dialect
      attr_reader :name, :parent, :keyword_map, :builtins, :prelude_parts,
                  :children, :revisions

      def initialize(name:, parent: nil)
        @name = name
        @parent = parent
        @keyword_map = parent ? parent.keyword_map.dup : Lexer.base_keyword_map
        @builtins = parent ? parent.builtins.dup : {}        # name -> proc overlay
        @prelude_parts = parent ? parent.prelude_parts.dup : []
        @revisions = parent ? parent.revisions.dup : []
        @children = []
        parent.children << self if parent
      end

      # The canonical base dialect (singleton).
      def self.base
        @base ||= new(name: "bada")
      end

      # --- revision operations (used by the Reviser) --------------------
      # Alias an extra surface word to a canonical role: keyword "関数", :def
      def alias_keyword(surface, role)
        @keyword_map[surface.to_s] = role.to_sym
        @revisions << "alias #{surface} -> #{role}"
        self
      end

      # Rename a role's primary surface word, removing the old surface(s).
      def rename_keyword(role, new_surface)
        role = role.to_sym
        @keyword_map.delete_if { |_, v| v == role }
        @keyword_map[new_surface.to_s] = role
        @revisions << "rename #{role} => #{new_surface}"
        self
      end

      def add_builtin(name, callable)
        @builtins[name.to_s] = callable
        @revisions << "builtin #{name}"
        self
      end

      def add_prelude(src)
        @prelude_parts << src
        @revisions << "prelude(+#{src.lines.count} lines)"
        self
      end

      def note(text)
        @revisions << text.to_s
        self
      end

      # --- spec / identity ----------------------------------------------
      def full_prelude
        @prelude_parts.join("\n")
      end

      def signature
        kws = @keyword_map.sort.map { |s, r| "#{s}:#{r}" }.join(",")
        "#{@name}|#{kws}|#{@builtins.keys.sort.join(',')}"
      end

      # Manifold entropy invariant of the spec = the branch's identity trigger.
      def invariant
        Bada::Manifold.xi(signature)
      end

      # --- genealogy / branch tree --------------------------------------
      def lineage
        chain = []
        d = self
        while d
          chain.unshift(d)
          d = d.parent
        end
        chain
      end

      def descendants
        @children.flat_map { |c| [c] + c.descendants }
      end

      def render_tree(indent = 0)
        line = "#{'  ' * indent}● #{@name}  (Ξ=#{format('%.4f', invariant)})"
        ([line] + @children.map { |c| c.render_tree(indent + 1) }).join("\n")
      end

      # surface word currently bound to a role (for diagnostics)
      def surface_for(role)
        @keyword_map.find { |_, v| v == role.to_sym }&.first
      end

      # What changed relative to the parent.
      def diff_from_parent
        return [] unless @parent
        @revisions - @parent.revisions
      end
    end
  end
end
