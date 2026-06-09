# frozen_string_literal: true

module Bada
  module Penrose
    # A numeric tensor: a flat data array with a shape and named indices.
    # Penrose diagrams are evaluated by contracting these (Einstein summation),
    # which is what makes a drawn diagram "auto-compute".
    class Tensor
      attr_reader :name, :index_names, :shape, :data

      # index_names: Array<String> (one per leg); shape: Array<Integer>;
      # data: flat Array (row-major over shape).
      def initialize(name, index_names, shape, data)
        @name = name
        @index_names = index_names
        @shape = shape
        @data = data
        @strides = compute_strides(shape)
      end

      def rank
        @shape.length
      end

      def scalar?
        @shape.empty?
      end

      def value
        scalar? ? @data[0] : self
      end

      # Element at a hash assignment {index_name => i}.
      def at(assign)
        off = 0
        @index_names.each_with_index { |n, k| off += assign[n] * @strides[k] }
        @data[off]
      end

      # Build from a nested array (matrix/vector) with given index names.
      def self.from_nested(name, nested, index_names)
        shape = []
        probe = nested
        while probe.is_a?(Array)
          shape << probe.length
          probe = probe[0]
        end
        data = nested.flatten
        new(name, index_names, shape, data)
      end

      # Build a scalar.
      def self.scalar(name, v)
        new(name, [], [], [v])
      end

      def to_nested
        return @data[0] if scalar?
        build_nested(0, 0)
      end

      private

      def compute_strides(shape)
        strides = Array.new(shape.length, 1)
        (shape.length - 2).downto(0) { |k| strides[k] = strides[k + 1] * shape[k + 1] }
        strides
      end

      def build_nested(dim, base)
        if dim == @shape.length - 1
          (0...@shape[dim]).map { |i| @data[base + i * @strides[dim]] }
        else
          (0...@shape[dim]).map { |i| build_nested(dim + 1, base + i * @strides[dim]) }
        end
      end
    end

    # General Einstein summation over a set of named tensors.
    #   einsum([A, B], output: ["i","j"])
    # sums every index name that is NOT in `output` (the contracted/joined wires)
    # and keeps the output indices as the free legs of the diagram's result.
    module Einsum
      module_function

      def call(tensors, output:)
        dims = {}
        tensors.each do |t|
          t.index_names.each_with_index do |n, k|
            if dims.key?(n) && dims[n] != t.shape[k]
              raise "dimension mismatch on index #{n}: #{dims[n]} vs #{t.shape[k]}"
            end
            dims[n] = t.shape[k]
          end
        end
        all_names = dims.keys
        out_shape = output.map { |n| dims.fetch(n) { raise "free index #{n} not found" } }
        out_strides = strides_for(out_shape)
        result = Array.new(out_shape.reduce(1, :*), 0.0)

        each_assignment(all_names, dims) do |assign|
          prod = 1.0
          tensors.each { |t| prod *= t.at(assign) }
          next if prod.zero?
          off = 0
          output.each_with_index { |n, k| off += assign[n] * out_strides[k] }
          result[off] += prod
        end

        Tensor.new("result", output, out_shape, result)
      end

      def strides_for(shape)
        s = Array.new(shape.length, 1)
        (shape.length - 2).downto(0) { |k| s[k] = s[k + 1] * shape[k + 1] }
        s
      end

      # Iterate over every combination of index values for `names`.
      def each_assignment(names, dims, &block)
        return yield({}) if names.empty?
        ranges = names.map { |n| (0...dims[n]).to_a }
        first, *rest = ranges
        first.product(*rest).each do |combo|
          assign = {}
          names.each_with_index { |n, k| assign[n] = combo[k] }
          block.call(assign)
        end
      end
    end
  end
end
