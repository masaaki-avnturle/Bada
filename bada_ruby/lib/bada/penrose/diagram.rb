# frozen_string_literal: true

require_relative "tensor"

module Bada
  module Penrose
    # A Penrose diagram: tensor nodes whose legs are wired together (contraction)
    # or left free (output indices), plus decorators (∇, ∂, ∫, symmetrisation).
    #
    # The diagram is the data model behind both the drawn canvas and the DSL.
    # Evaluating it = contracting the tensors (Einstein summation).
    class Diagram
      Node = Struct.new(:name, :legs, :value) # legs: count; value: nested array or nil
      Wire = Struct.new(:a, :b)               # a,b = [node_name, leg_index]
      Free = Struct.new(:slot, :label)        # slot = [node_name, leg_index]
      Decorator = Struct.new(:type, :target, :label) # type: :nabla/:partial/:integral/:sym/:antisym

      attr_reader :nodes, :wires, :frees, :decorators

      def initialize
        @nodes = {}
        @wires = []
        @frees = []
        @decorators = []
      end

      # ---- Builder DSL -------------------------------------------------
      def self.build(&block)
        d = new
        d.instance_eval(&block)
        d
      end

      def tensor(name, legs:, value: nil)
        @nodes[name] = Node.new(name, legs, value)
      end

      def value(name, nested)
        @nodes[name].value = nested
      end

      def contract(slot_a, slot_b)
        @wires << Wire.new(slot_a, slot_b)
      end

      def free(slot, label)
        @frees << Free.new(slot, label)
      end

      def nabla(target, label) = @decorators << Decorator.new(:nabla, target, label)
      def partial(target, label) = @decorators << Decorator.new(:partial, target, label)
      def integral(label) = @decorators << Decorator.new(:integral, nil, label)
      def symmetrize(*labels) = @decorators << Decorator.new(:sym, labels, nil)
      def antisymmetrize(*labels) = @decorators << Decorator.new(:antisym, labels, nil)

      # ---- Index assignment -------------------------------------------
      # Returns { node_name => [index_name per leg] } and the ordered output
      # index names (free legs), resolving contractions to shared names.
      def resolve
        assign = {}
        @nodes.each { |n, node| assign[n] = Array.new(node.legs) }

        @wires.each_with_index do |w, i|
          shared = "k#{i + 1}"
          set(assign, w.a, shared)
          set(assign, w.b, shared)
        end

        output = []
        @frees.each do |f|
          set(assign, f.slot, f.label)
          output << f.label
        end

        # Any unwired, unfreed leg becomes an auto free index.
        auto = 0
        assign.each do |n, legs|
          legs.each_index do |k|
            next unless legs[k].nil?
            auto += 1
            name = "f#{auto}"
            legs[k] = name
            output << name
          end
        end

        # Integral indices are contracted (summed) against an implicit measure,
        # so remove them from the output if they appear there.
        integral_labels = @decorators.select { |d| d.type == :integral }.map(&:label)
        output -= integral_labels

        { assignment: assign, output: output, integral: integral_labels }
      end

      # Einstein-notation string, e.g. "A_{i k} B_{k j} → R_{i j}".
      def einsum_string
        r = resolve
        parts = @nodes.map do |name, _|
          idx = r[:assignment][name].join(" ")
          "#{name}_{#{idx}}"
        end
        deco = @decorators.map { |d| decorator_label(d) }.compact
        lhs = (deco + parts).join(" ")
        "#{lhs} → R_{#{r[:output].join(' ')}}"
      end

      def decorator_label(d)
        case d.type
        when :nabla    then "∇_#{d.label}"
        when :partial  then "∂_#{d.label}"
        when :integral then "∫·d#{d.label}"
        when :sym      then "Sym(#{Array(d.target).join(',')})"
        when :antisym  then "Asym(#{Array(d.target).join(',')})"
        end
      end

      private

      def set(assign, slot, name)
        node, leg = slot
        raise "unknown node #{node}" unless assign.key?(node)
        assign[node][leg] = name
      end
    end
  end
end
