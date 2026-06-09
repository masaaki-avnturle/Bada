# frozen_string_literal: true

require_relative "tensor"
require_relative "diagram"

module Bada
  module Penrose
    # Evaluate a Penrose diagram: build numeric tensors from the node values and
    # contract them (Einstein summation). Integral indices are summed against an
    # implicit unit measure; symmetrisation is applied to the result. ∇/∂ are
    # structural unless component values are supplied.
    module Evaluator
      module_function

      def evaluate(diagram)
        r = diagram.resolve
        notes = []
        symbolic = diagram.einsum_string

        deco_types = diagram.decorators.map(&:type)
        if deco_types.include?(:nabla) || deco_types.include?(:partial)
          notes << "∇/∂ は構造的に保持（成分値が無いため数値評価は記号のまま）。"
        end

        tensors = []
        numeric_ok = true
        diagram.nodes.each do |name, node|
          if node.value.nil?
            numeric_ok = false
            break
          end
          idx = r[:assignment][name]
          t = Tensor.from_nested(name, node.value, idx)
          unless t.rank == idx.length
            raise "node #{name}: value rank #{t.rank} != legs #{idx.length}"
          end
          tensors << t
        end

        result = nil
        nested = nil
        if numeric_ok && !tensors.empty?
          result = Einsum.call(tensors, output: r[:output])
          result = apply_symmetry(diagram, result, r[:output], notes)
          nested = result.to_nested
        else
          notes << "数値評価はテンソル値が未指定のためスキップ（記号式のみ）。" unless tensors.empty? && numeric_ok
        end

        {
          einsum: symbolic,
          output: r[:output],
          numeric: result,
          result: nested,
          scalar: (result && result.scalar? ? result.value : nil),
          notes: notes
        }
      end

      # Symmetrise / antisymmetrise the result over a pair of output indices.
      def apply_symmetry(diagram, tensor, output, notes)
        diagram.decorators.each do |d|
          next unless %i[sym antisym].include?(d.type)
          labels = Array(d.target)
          positions = labels.map { |l| output.index(l) }.compact
          if positions.length != 2
            notes << "#{d.type} は2つの出力添字にのみ対応（#{labels.join(',')}）。"
            next
          end
          tensor = swap_combine(tensor, positions[0], positions[1], d.type == :sym)
        end
        tensor
      end

      def swap_combine(tensor, p, q, plus)
        names = tensor.index_names
        swapped_names = names.dup
        swapped_names[p], swapped_names[q] = swapped_names[q], swapped_names[p]
        # build a tensor that is `tensor` with axes p,q swapped, same index names
        # so we can add elementwise.
        sw = Tensor.new(tensor.name, names, tensor.shape, Array.new(tensor.data.length, 0.0))
        Einsum.each_assignment(names, dim_map(tensor)) do |assign|
          a2 = assign.dup
          a2[names[p]], a2[names[q]] = assign[names[q]], assign[names[p]]
          off = offset(tensor, assign)
          sw.data[off] = tensor.at(a2)
        end
        combined = tensor.data.each_index.map do |i|
          plus ? 0.5 * (tensor.data[i] + sw.data[i]) : 0.5 * (tensor.data[i] - sw.data[i])
        end
        Tensor.new(tensor.name, names, tensor.shape, combined)
      end

      # Standalone numeric derivative for a scalar field sampled on a 1-D grid
      # (a concrete ∂ demonstration): central differences, spacing h.
      def derivative_1d(samples, h: 1.0)
        n = samples.length
        (0...n).map do |i|
          if i.zero?
            (samples[1] - samples[0]) / h
          elsif i == n - 1
            (samples[n - 1] - samples[n - 2]) / h
          else
            (samples[i + 1] - samples[i - 1]) / (2 * h)
          end
        end
      end

      def dim_map(t)
        m = {}
        t.index_names.each_with_index { |n, k| m[n] = t.shape[k] }
        m
      end

      def offset(t, assign)
        strides = Einsum.strides_for(t.shape)
        off = 0
        t.index_names.each_with_index { |n, k| off += assign[n] * strides[k] }
        off
      end
    end
  end
end
